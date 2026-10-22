#!/usr/bin/env python3
"""
smoke.py — prove the totem works, in ~30 seconds, before you walk on stage.

    python3 smoke.py            # starts its own bridge on port 8799, kills it, restarts it

Checks: the page builds and is CDN-free · the six faces load · the mock brain
answers in persona · wake words route · the name lands in memory.json ·
SIGKILL + restart resumes by name · demo audio is on disk · TTS (if reachable).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("SMOKE_PORT", 8799))
BASE = f"http://127.0.0.1:{PORT}"
MEM = HERE / "smoke-memory.json"
ok_n, fail_n = 0, 0


def chk(name, cond, detail=""):
    global ok_n, fail_n
    if cond:
        ok_n += 1
        print(f"  ✓ {name}" + (f" — {detail}" if detail else ""))
    else:
        fail_n += 1
        print(f"  ✗ {name} — {detail}")


def get(path, body=None, timeout=30):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def start():
    env = dict(os.environ, OHANA_MEMORY=str(MEM))
    # Deterministic MOCK brain, always: the persona/中文/handoff checks assert
    # the CANNED tables. A key leaked in from the parent shell turns them into
    # live-model roulette (happened 2026-10-20 — 6 false fails). Live-lane
    # round-trips are proven separately (test_ladder.py + manual key test).
    env.pop("OHANA_LLM_KEY", None)
    p = subprocess.Popen([sys.executable, "serve.py", "--port", str(PORT)],
                         cwd=HERE, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(0.25)
        try:
            get("/health", timeout=3)
            return p
        except Exception:
            continue
    raise SystemExit("bridge never came up")


print("🗿 totem-web smoke test\n")

# ---- the page
page = (HERE / "dist" / "index.html")
chk("dist/index.html exists", page.exists(), f"{page.stat().st_size if page.exists() else 0} bytes")
html = page.read_text(encoding="utf-8") if page.exists() else ""
chk("no runtime CDN refs (GFW law)", "https://" not in html,
    f"{html.count('https://')} occurrences")
chk("three.js vendored next to it", (HERE / "dist" / "three.module.js").exists())
chk("chat lane is in the page", 'id="chatLog"' in html and "OhanaTotem" in html)
chk("static mirror speaks 中文 too", "STATIC_LINES_ZH" in html and "静态镜像" in html)

# ---- the brain ladder (unit-tested against a mock endpoint, no key, no net)
r = subprocess.run([sys.executable, "test_ladder.py"], cwd=HERE,
                   capture_output=True, text=True)
tally = (r.stdout.strip().splitlines() or ["?"])[-1]
chk("brain ladder unit tests (free→paid→MOCK, benching, no-key=no-net)",
    r.returncode == 0, tally)

MEM.unlink(missing_ok=True)
proc = start()
try:
    h = get("/health")
    chk("bridge healthy", h.get("ok") is True, f"brain={h.get('mode')}, prerendered={h.get('prerendered')}")
    chk("zero Taurus credentials", "none" in h.get("taurus_credentials", ""))
    lad = h.get("ladder") or {}
    chk("ladder reported on /health (mock when no key)",
        lad.get("enabled") is False and h.get("mode") == "mock"
        and "free" in lad and "paid" in lad,
        f"free={lad.get('free', {}).get('model')} paid={lad.get('paid', {}).get('model')}")
    faces = get("/faces")
    chk("six faces", len(faces) == 6, ", ".join(f["nm"] for f in faces))

    r = get("/chat", {"text": "my name is Judge", "face": "shaka"})
    chk("SHAKA answers + remembers the name", r["face"] == "shaka" and "Judge" in r["reply"],
        r["reply"][:60])

    r = get("/chat", {"text": "hey deva, when and where is devcon?"})
    chk("wake word routes to DEVA", r["face"] == "deva", r["reply"][:60])
    chk("DEVA has the real facts", "November 3rd to 6th" in r["reply"] and "Jio World" in r["reply"])

    r = get("/chat", {"text": "what is the mandate?", "face": "crops"})
    chk("CROPS recites the mandate", "Censorship-resistant" in r["reply"], r["reply"][:60])

    r = get("/chat", {"text": "teach me a chord", "face": "oso"})
    chk("cross-domain handoff lights a sibling", r.get("handoff") == "kala", r["reply"][:60])

    r = get("/chat", {"text": "start a song", "face": "oke"})
    chk("OKE runs the singalong", "Susanna" in r["reply"], r["reply"][:60])

    # ---- the 中文 lane (CJK in -> CJK out, facts preserved)
    import re as _re
    _cjk = lambda s: bool(_re.search(r"[一-鿿]", s or ""))
    r = get("/chat", {"text": "你好！你是什么东西？", "face": "shaka"})
    chk("SHAKA answers in 中文", r["face"] == "shaka" and _cjk(r["reply"])
        and "六个灵魂" in r["reply"], r["reply"][:40])
    r = get("/chat", {"text": "Devcon 什么时候、在哪里举行？", "face": "deva"})
    chk("DEVA 中文 facts exact (11月3日至6日 · Jio World · 孟买)",
        _cjk(r["reply"]) and "11月3日至6日" in r["reply"]
        and "Jio World" in r["reply"] and "孟买" in r["reply"], r["reply"][:50])
    r = get("/chat", {"text": "教我弹尤克里里", "face": "deva"})
    chk("中文 cross-face handoff lights a sibling", r.get("handoff") == "kala"
        and _cjk(r["reply"]), r["reply"][:40])
    import tts as _tts
    chk("中文 never read by an English voice",
        _tts.voice_for("deva", "zh") == "zh-CN-XiaoxiaoNeural"
        and (_tts.voice_for("shaka", "zh").startswith("zh-") or _tts.is_fish(_tts.voice_for("shaka", "zh"))),
        f"deva_zh→{_tts.voice_for('deva', 'zh')}")

    mem = get("/memory")
    chk("memory.json on disk", mem["exists"] and mem["visitor"].get("name") == "Judge",
        f"turns={mem['turns']}")

    # ---- THE PARTY TRICK
    print("\n  ⚡ pulling the plug (SIGKILL) …")
    proc.send_signal(signal.SIGKILL)
    proc.wait(timeout=10)
    dead = False
    try:
        get("/health", timeout=2)
    except Exception:
        dead = True
    chk("bridge is dead", dead)
    t0 = time.time()
    proc = start()
    boot = time.time() - t0
    res = get("/resume")
    chk("resumes by name after a power cycle",
        res.get("visitor") == "Judge" and res.get("resumed") is True,
        f"boot {boot:.1f}s · {res['emoji']} {res['name']}: {res['reply'][:70]}…")

    # ---- offline-proof demo
    sc = get("/script")
    chk("6 beats scripted", len(sc["beats"]) == 6)
    chk("demo audio pre-rendered on disk", sc["prerendered"] == 6,
        f"{sc['prerendered']}/6 — run prerender.py on good wifi")

    # ---- voice (allowed to fail: that is the whole point of pre-rendering)
    try:
        t = get("/tts", {"face": "shaka", "text": "voice check, one two."}, timeout=40)
        chk("live TTS reachable", bool(t.get("url")), t.get("url") or t.get("error", "")[:60])
    except urllib.error.HTTPError as e:
        chk("live TTS reachable (optional)", False,
            "edge-tts unreachable — demo still runs from disk")
finally:
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        pass
    MEM.unlink(missing_ok=True)

print(f"\n{ok_n} passed, {fail_n} failed")
sys.exit(1 if fail_n else 0)
