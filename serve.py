#!/usr/bin/env python3
"""
serve.py — the local bridge for the VIRTUAL ʻohana totem (totem-web).

    python3 serve.py              # http://127.0.0.1:8777/
    python3 serve.py --port 9000 --host 0.0.0.0

It serves the totem page and the mind behind it:

    GET  /                 the 3D totem + chat lane (dist/index.html)
    GET  /health           {ok, mode, memory, prerendered}
    GET  /faces            the six faces (from router.py's FACES table)
    GET  /resume           THE PARTY TRICK — greet by name from memory.json
    POST /chat             {face, text, visitor} -> {face, reply, ...}
    GET  /memory           the live memory.json snapshot
    POST /forget           wipe memory (between judges / rehearsals)
    POST /tts              {face, text} -> {url} (cached mp3 on disk)
    GET  /script           the 6-beat demo script + prerendered audio urls
    GET  /audio/<...>      the mp3s
    GET  /voices           the voice table (edit voices.json to change picks)

LAWS OBEYED HERE:
  * ZERO Taurus credentials. brain.py installs a no-op taurus_sync shim, so
    there is no code path that could talk to the platform even by accident.
  * ZERO runtime CDN fetches in the page (three.js is vendored next to it).
  * The LLM lane is pluggable and defaults to MOCK (free, offline, in-persona).
"""
from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import brain
import demo_script
import tts

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
AUDIO = HERE / "audio"

app = Flask(__name__, static_folder=None)


# ----------------------------------------------------------------- the page
@app.after_request
def _nocache(resp):
    if resp.mimetype in ("text/html", "application/json"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/")
def index():
    if not (DIST / "index.html").exists():
        return ("<pre>dist/index.html is missing — run ./build.sh first.</pre>", 503)
    return send_from_directory(DIST, "index.html")


@app.get("/<path:fname>")
def dist_file(fname):
    # only ever serves files that exist in dist/ (three.module.js, OrbitControls.js, …)
    p = (DIST / fname)
    if p.is_file():
        return send_from_directory(DIST, fname)
    return ("not found", 404)


@app.get("/audio/<path:fname>")
def audio(fname):
    p = AUDIO / fname
    if p.is_file():
        return send_from_directory(AUDIO, fname, mimetype="audio/mpeg")
    return ("no audio", 404)


# ----------------------------------------------------------------- the mind
@app.get("/health")
def health():
    man = AUDIO / "demo" / "manifest.json"
    pre = 0
    if man.exists():
        try:
            pre = sum(1 for v in json.loads(man.read_text()).values() if v.get("file"))
        except Exception:
            pre = 0
    return jsonify({
        "ok": True, "mode": brain.mode(), "faces": len(brain.FACES),
        "ladder": brain.LADDER.state(),
        "memory": brain.memory_snapshot(), "prerendered": pre,
        "taurus_credentials": "none (taurus_sync is a no-op shim)",
    })


@app.get("/faces")
def faces():
    return jsonify(brain.face_table())


@app.get("/voices")
def voices():
    return jsonify(tts.voices())


@app.get("/resume")
def resume():
    return jsonify(brain.resume())


@app.post("/chat")
def chat():
    d = request.get_json(silent=True) or {}
    text = (d.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty text"}), 400
    out = brain.ask(text[:2000], face=d.get("face"), visitor=d.get("visitor"))
    return jsonify(out)


@app.get("/memory")
def memory():
    return jsonify(brain.memory_snapshot())


@app.post("/forget")
def forget():
    return jsonify(brain.forget())


@app.post("/tts")
def speak():
    d = request.get_json(silent=True) or {}
    text = (d.get("text") or "").strip()
    face = d.get("face") or "shaka"
    # 中文 replies must never be read by an English voice: auto-detect CJK
    lang = d.get("lang") or ("zh" if brain.canned.is_zh(text) else "en")
    if not text:
        return jsonify({"error": "empty text"}), 400
    path = tts.cached_path(face, text, lang)
    if path.exists() and path.stat().st_size > 400:
        return jsonify({"url": f"/audio/cache/{path.name}", "cached": True,
                        "voice": tts.voice_for(face, lang)})
    try:
        p = tts.synth(text[:1200], face, lang)
        return jsonify({"url": f"/audio/cache/{p.name}", "cached": False,
                        "voice": tts.voice_for(face, lang)})
    except Exception as e:
        # no voice is survivable; the text is already on screen
        return jsonify({"error": f"{type(e).__name__}: {e}", "url": None}), 503


@app.get("/script")
def script():
    man = {}
    p = AUDIO / "demo" / "manifest.json"
    if p.exists():
        try:
            man = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            man = {}
    beats = []
    for b in demo_script.BEATS:
        e = dict(b)
        m = man.get(f"beat{b['id']}") or {}
        e["audio"] = ("/" + m["file"]) if m.get("file") else None
        beats.append(e)
    extra = {}
    for x in demo_script.EXTRA:
        m = man.get(x["id"]) or {}
        extra[x["id"]] = {"text": x["text"], "face": x["face"],
                          "audio": ("/" + m["file"]) if m.get("file") else None}
    return jsonify({"beats": beats, "extra": extra,
                    "prerendered": sum(1 for b in beats if b["audio"])})


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("OHANA_PORT", 8777)))
    ap.add_argument("--host", default=os.environ.get("OHANA_HOST", "127.0.0.1"))
    a = ap.parse_args()

    brain.get_router()
    tts.ensure_voices_json()
    mem = brain.memory_snapshot()
    name = (mem["visitor"] or {}).get("name") or "—"
    pre = 0
    p = AUDIO / "demo" / "manifest.json"
    if p.exists():
        try:
            pre = sum(1 for v in json.loads(p.read_text()).values() if v.get("file"))
        except Exception:
            pass

    print("")
    print("  🗿  the ʻOhana Bot — virtual totem (totem-web)")
    print(f"      open:        http://127.0.0.1:{a.port}/")
    if a.host == "0.0.0.0":
        print(f"      on the LAN:  http://{_lan_ip()}:{a.port}/   (phones, judges, projector)")
    print(f"      demo mode:   http://127.0.0.1:{a.port}/?demo=1")
    m = brain.mode()
    if m == "mock":
        print("      brain:       MOCK  (no OHANA_LLM_KEY set — canned in-persona lines, ¥0)")
    else:
        L = brain.LADDER
        print(f"      brain:       LADDER  {L.free.model} (free) → {L.paid.model} ($5 airbag) → MOCK")
    print(f"      memory:      {mem['path']}  visitor: {name}"
          + ("  · resumes a thought" if mem["last_thought"] else ""))
    print(f"      voices:      {HERE / 'voices.json'}  ·  prerendered demo lines: {pre}")
    print("      taurus:      no credentials, no calls (taurus_sync is a no-op shim)")
    print("")
    app.run(host=a.host, port=a.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
