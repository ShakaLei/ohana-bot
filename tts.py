#!/usr/bin/env python3
"""
tts.py — six voices out, cached on disk.

edge-tts (the same voices as the audition page). Every utterance is cached by
sha1(voice|text) so a line is only ever synthesized once; the demo lines are
pre-rendered by prerender.py and therefore need no network at all on stage.

Voice picks live in ONE file: voices.json. When Shaka picks his winners from
the audition page, edit that file — nothing else changes.

FISH LANE (2026-10-22, his picks): a voice value of "fish:clone" means
"Shaka's REAL voice" — Fish Audio zero-shot clone (model s2.1-pro-free, $0)
from the 30 s reference in audio/ref/shaka.{wav,txt}, sent as msgpack
(JSON+base64 references are rejected). Cross-lingual, so the same lane speaks
中文 and ʻŌlelo. Key: env OHANA_FISH_KEY, else file OHANA_FISH_KEY_FILE
(default /workspace/vault/fish-audio-key). NEVER inside the bundle.
Any failure (no key, GFW, timeout, tiny blob) -> the edge-tts fallback voice
<face>_fallback, so the stage never goes silent. Demo lines are pre-rendered
in the clone, so Fish is not needed on stage at all.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "audio" / "cache"
DEMO = HERE / "audio" / "demo"
VOICES_JSON = HERE / "voices.json"

DEFAULT_VOICES = {
    # Shaka's picks, 2026-10-22 07:41 CST ("shaka clone is the best cuz it
    # sounds just like me; deva A Sonia, oke B William, kala B Natasha,
    # oso B Brian, crops B Liam")
    "shaka": "fish:clone",
    "shaka_zh": "fish:clone",
    "shaka_fallback": "en-US-AndrewNeural",      # audition A, if Fish is down
    "shaka_zh_fallback": "zh-CN-YunxiNeural",
    "oso": "en-US-BrianNeural",
    "deva": "en-GB-SoniaNeural",
    "crops": "en-CA-LiamNeural",
    "kala": "en-AU-NatashaNeural",
    "oke": "en-AU-WilliamNeural",
}

FISH_URL = "https://api.fish.audio/v1/tts"
FISH_MODEL = os.environ.get("OHANA_FISH_MODEL", "s2.1-pro-free")
FISH_REF = HERE / "audio" / "ref" / "shaka"      # .wav + .txt
FISH_TIMEOUT = float(os.environ.get("OHANA_FISH_TIMEOUT", "45"))

# small per-face delivery tweaks (edge-tts prosody) — OKE shouts, CROPS is calm
RATE = {"oke": "+12%", "crops": "-6%", "kala": "-4%", "shaka": "+2%",
        "oso": "+0%", "deva": "+0%"}


def voices() -> dict:
    if VOICES_JSON.exists():
        try:
            v = dict(DEFAULT_VOICES)
            v.update(json.loads(VOICES_JSON.read_text(encoding="utf-8")))
            return v
        except Exception as e:
            print(f"[tts] voices.json unreadable ({e}) — using defaults")
    return dict(DEFAULT_VOICES)


def voice_for(face: str, lang: str = "en") -> str:
    v = voices()
    if lang.startswith("zh"):
        # Chinese text must NEVER be read by an English voice: faces without
        # their own <face>_zh pick fall back to a neutral zh voice.
        # ("fish:clone" is cross-lingual, so it counts as a zh voice.)
        return v.get(f"{face}_zh") or "zh-CN-XiaoxiaoNeural"
    return v.get(face, v.get("shaka_fallback", "en-US-AndrewNeural"))


def fallback_voice(face: str, lang: str = "en") -> str:
    """edge-tts voice used when the fish lane fails for this face."""
    v = voices()
    if lang.startswith("zh"):
        return v.get(f"{face}_zh_fallback") or "zh-CN-XiaoxiaoNeural"
    return v.get(f"{face}_fallback") or "en-US-AndrewNeural"


def is_fish(voice: str) -> bool:
    return voice.startswith("fish:")


def fish_key() -> str:
    k = os.environ.get("OHANA_FISH_KEY", "").strip()
    if k:
        return k
    f = os.environ.get("OHANA_FISH_KEY_FILE", "/workspace/vault/fish-audio-key")
    try:
        return Path(f).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _synth_fish(text: str, out: Path):
    """Zero-shot clone of Shaka's voice. Raises on any failure."""
    import urllib.request
    import msgpack
    key = fish_key()
    if not key:
        raise RuntimeError("no Fish key (OHANA_FISH_KEY / OHANA_FISH_KEY_FILE)")
    ref_wav = FISH_REF.with_suffix(".wav")
    ref_txt = FISH_REF.with_suffix(".txt")
    if not (ref_wav.exists() and ref_txt.exists()):
        raise RuntimeError(f"no voice reference at {ref_wav}")
    body = msgpack.packb({
        "text": text, "format": "mp3",
        "references": [{"audio": ref_wav.read_bytes(),
                        "text": ref_txt.read_text(encoding="utf-8").strip()}],
    }, use_bin_type=True)
    req = urllib.request.Request(FISH_URL, data=body, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/msgpack",
        "model": FISH_MODEL,
    })
    with urllib.request.urlopen(req, timeout=FISH_TIMEOUT) as r:
        data = r.read()
    if len(data) < 2000:
        raise RuntimeError(f"fish returned {len(data)} bytes")
    tmp = out.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(out)


def key_for(face: str, text: str, lang: str = "en") -> str:
    voice = voice_for(face, lang)
    h = hashlib.sha1(f"{voice}|{RATE.get(face,'+0%')}|{text}".encode("utf-8")).hexdigest()[:20]
    return h


def cached_path(face: str, text: str, lang: str = "en") -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / (key_for(face, text, lang) + ".mp3")


async def _synth(text: str, voice: str, out: Path, rate: str = "+0%"):
    import edge_tts
    tmp = out.with_suffix(".part")
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(str(tmp))
    if tmp.stat().st_size < 400:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("edge-tts returned an empty stream")
    tmp.replace(out)


def synth(text: str, face: str, lang: str = "en", out: Path | None = None) -> Path:
    """Returns a path to an mp3. Raises on failure (callers degrade to silence)."""
    out = out or cached_path(face, text, lang)
    if out.exists() and out.stat().st_size > 400:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    voice = voice_for(face, lang)
    if is_fish(voice):
        try:
            _synth_fish(text, out)
            return out
        except Exception as e:
            fb = fallback_voice(face, lang)
            print(f"[tts] fish lane failed ({type(e).__name__}: {e}) -> edge {fb}")
            voice = fb
    asyncio.run(_synth(text, voice, out, RATE.get(face, "+0%")))
    return out


def ensure_voices_json():
    if not VOICES_JSON.exists():
        VOICES_JSON.write_text(json.dumps(DEFAULT_VOICES, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ensure_voices_json()
    p = synth("Aloha! This is the voice check.", "shaka")
    print("wrote", p, os.path.getsize(p), "bytes")
