#!/usr/bin/env python3
"""
brain.py — the ʻOhana Bot mind, wired for the VIRTUAL totem (totem-web).

It does NOT re-implement the bot. It imports the real bridge from
/shared/ohana-bot/bridge/router.py and uses its:
    * FACES / wake-word matcher
    * load_persona()      -> persona .md + domain pack .md -> system prompt
    * VisitorMemory       -> memory.json, fsync'd, survives power cycles
    * sanitize_reply()    -> the pre-TTS scrub (Tessera's rules)
    * Router.handle()     -> the whole turn, unchanged

Two shims are installed in sys.modules BEFORE router's lazy imports can run:

  llm         -> our pluggable responder (mock | openrouter). router.handle()
                 calls `from llm import chat`, so this is the whole brain switch.
  taurus_sync -> a hard no-op. THE LAW: zero Taurus credentials, zero Taurus
                 calls, anywhere near the venue machine. Not "unconfigured" —
                 structurally impossible.
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_bridge() -> Path:
    """The bridge lives in /shared on the ʻohana machines and NEXT TO US in the
    laptop bundle (bundle.sh copies bridge/ + personas/ + packs/ in). Env wins."""
    env = os.environ.get("OHANA_BRIDGE")
    cands = [Path(env)] if env else []
    cands += [HERE / "bridge", Path("/shared/ohana-bot/bridge")]
    for c in cands:
        if (c / "router.py").is_file():
            return c
    raise SystemExit("router.py not found — set OHANA_BRIDGE to the bridge/ directory")


BRIDGE = _find_bridge()
os.environ["OHANA_BRIDGE"] = str(BRIDGE)       # canned.py reads the same answer

# memory.json lives with the virtual totem, not in /shared
os.environ.setdefault("OHANA_MEMORY", str(HERE / "memory.json"))

if str(BRIDGE) not in sys.path:
    sys.path.insert(0, str(BRIDGE))

import canned  # noqa: E402  (our mock responder; reads the persona files)
import ladder  # noqa: E402  (the 3-layer brain: free -> paid -> MOCK)

# --------------------------------------------------------------- llm shim
CURRENT_FACE = "shaka"          # set by ask() right before router.handle()
LAST_ERROR = ""

# THE 3-LAYER LADDER (see ladder.py):
#   free :free OpenRouter model  ->  paid claude-haiku-4.5 ($5 airbag)  ->  MOCK.
# One OHANA_LLM_KEY powers both network lanes; no key = pure MOCK, no sockets.
LADDER = ladder.Ladder()


def mode() -> str:
    """'mock' | 'free:<model>' | 'paid:<model>' — short, badge-sized."""
    return LADDER.mode()


def _chat(system: str, history: list, user: str, **kw) -> str:
    """The pluggable lane. Climbs the ladder; MOCK catches everything."""
    global LAST_ERROR
    if LADDER.enabled:
        try:
            text, lane = LADDER.complete(system, history, user)
            return text
        except Exception as e:                      # quota, GFW, dead key, bench…
            LAST_ERROR = f"{type(e).__name__}: {e}"
            print(f"[brain] ladder exhausted ({LAST_ERROR[:160]}) -> canned persona line",
                  flush=True)
    return canned.answer(CURRENT_FACE, user, history)


_llm_shim = types.ModuleType("llm")
_llm_shim.chat = _chat
sys.modules["llm"] = _llm_shim

# -------------------------------------------------------- taurus_sync shim
_ts = types.ModuleType("taurus_sync")


def _mirror_async(*a, **k):      # noqa: D401 - deliberately does nothing
    """NO-OP. Zero Taurus credentials on the venue machine (TESSERA-FINDINGS)."""
    return None


_ts.mirror_async = _mirror_async
sys.modules["taurus_sync"] = _ts

# ------------------------------------------------------------- the router
import router  # noqa: E402

FACES = router.FACES
FACE_BY_KEY = router.FACE_BY_KEY
MEMORY_PATH = router.MEMORY_PATH

_R: "router.Router | None" = None


def get_router() -> "router.Router":
    global _R
    if _R is None:
        _R = router.Router()
    return _R


def face_table() -> list:
    out = []
    for f in FACES:
        out.append({
            "k": f.key, "nm": f.name, "em": f.emoji, "col": f.color,
            "wake": f.wake_words, "pack": f.pack, "led": f.led_index,
            "greeting": canned.greeting(f.key),
        })
    return out


def ask(text: str, face: str | None = None, visitor: str | None = None) -> dict:
    """One visitor utterance -> one reply, through the REAL router path."""
    global CURRENT_FACE
    r = get_router()
    if visitor:
        r.mem.data.setdefault("visitor", {})["name"] = visitor.strip()[:40]
        r.mem.flush()
    else:
        # 中文 name capture ("我叫小明") — router.note_name only knows the EN form
        zh_nm = canned.ZH_NAME_RE.search(text or "")
        if zh_nm and not (r.mem.data.get("visitor") or {}).get("name"):
            r.mem.data.setdefault("visitor", {})["name"] = zh_nm.group(1).strip()[:40]
            r.mem.flush()
    if face and face in FACE_BY_KEY:
        r.switch_face(face)
    CURRENT_FACE = r.active                     # mock responder needs the face
    woke = router.match_wake_word(text)
    if woke:
        CURRENT_FACE = woke                     # handle() will switch too
    reply = r.handle(text)                      # untouched bridge logic
    f = FACE_BY_KEY[r.active]
    return {
        "face": r.active, "name": f.name, "emoji": f.emoji, "color": f.color,
        "reply": reply, "mode": mode(), "woke": woke,
        "visitor": r.mem.data.get("visitor", {}).get("name") or "",
        "handoff": canned.handoff_target(reply, r.active),
    }


def memory_snapshot() -> dict:
    r = get_router()
    d = r.mem.data
    hist = {k: len(v) for k, v in (d.get("history") or {}).items()}
    return {
        "visitor": d.get("visitor", {}),
        "active_face": d.get("active_face", router.DEFAULT_FACE),
        "last_thought": d.get("last_thought", ""),
        "turns": hist,
        "updated": d.get("updated", 0),
        "path": str(MEMORY_PATH),
        "exists": MEMORY_PATH.exists(),
    }


def resume() -> dict:
    """THE PARTY TRICK. Called on every page load: if memory.json carries a
    name and an unfinished thought, the totem greets by name and resumes."""
    r = get_router()
    name = (r.mem.data.get("visitor") or {}).get("name") or ""
    thought = r.mem.data.get("last_thought") or ""
    face = r.mem.data.get("active_face") or router.DEFAULT_FACE
    f = FACE_BY_KEY.get(face, FACE_BY_KEY[router.DEFAULT_FACE])
    cold = not (name or thought)
    text = canned.greeting(face) if cold else canned.resume_line(face, name, thought)
    return {
        "face": face, "name": f.name, "emoji": f.emoji, "color": f.color,
        "reply": router.sanitize_reply(text, face),
        "cold": cold, "visitor": name, "resumed": bool(thought),
        "mode": mode(),
    }


def forget() -> dict:
    """Wipe memory.json (between judges / rehearsals)."""
    r = get_router()
    r.mem.data = {"visitor": {}, "active_face": router.DEFAULT_FACE,
                  "last_thought": "", "history": {}, "updated": 0}
    r.mem.flush()
    r.active = router.DEFAULT_FACE
    return memory_snapshot()


if __name__ == "__main__":
    get_router()
    print("mode:", mode(), "| memory:", MEMORY_PATH)
    print("resume:", resume()["reply"])
    for q, fk in [("my name is Jordan", None), ("what are you?", None),
                  ("what does ZK mean?", "crops"), ("teach me a chord", "kala")]:
        out = ask(q, fk)
        print(f"  [{out['face']}] {out['reply'][:120]}")
