#!/usr/bin/env python3
"""
audio_io.py — STT/TTS interface for the ʻOhana Bot.

Design: the router never cares HOW audio happens. It calls:
    listen()                  -> transcript string (blocking until utterance ends)
    speak(text, face_key)     -> plays audio on the speaker, returns when done
    speak_stream(tokens, key) -> incremental TTS for low latency (<1.5s to first word)

Decide ON THE PI (both paths sketched below, pick at the parts bench):

STT options
  A) faster-whisper, model "base" or "small", int8 on Pi 5         [offline, ~1-2s]
     TODO: pip install faster-whisper; needs ~1GB RAM for "small".
     Pair with webrtcvad or silero-vad for end-of-utterance detection.
  B) cloud STT (OpenAI whisper API / Deepgram / Volc for zh)        [fast, needs wifi]
     TODO: pick by venue wifi reliability. Hackathon hall wifi is a gamble —
     having (A) as fallback is the honest move.

TTS options
  A) edge-tts (same voices as the audition page!)                    [needs wifi]
     Voice table below mirrors the audition winners — update after Shaka picks.
  B) piper (rhasspy) fully offline, ~10 voices, fast on Pi 5        [offline fallback]
     TODO: download .onnx voices at the bench; map faces -> closest piper voice.

Wake words: handled in router.py on the TRANSCRIPT (simple + robust in noise
when paired with touch pads). If always-on hotword is wanted instead,
openWakeWord or porcupine go HERE, upstream of listen().
"""

from __future__ import annotations
import asyncio
import subprocess
import tempfile

# face -> edge-tts voice. Shaka's picks 2026-10-22 (deva A Sonia · oke B
# William · kala B Natasha · oso B Brian · crops B Liam). SHAKA = his REAL
# voice via the Fish clone lane in ohana-totem/tts.py ("fish:clone"); on this
# edge-only Pi path Andrew (audition A) is the stand-in/fallback.
EDGE_VOICES = {
    "shaka": "en-US-AndrewNeural",
    "oso":   "en-US-BrianNeural",
    "deva":  "en-GB-SoniaNeural",
    "crops": "en-CA-LiamNeural",
    "kala":  "en-AU-NatashaNeural",
    "oke":   "en-AU-WilliamNeural",
    "shaka_zh": "zh-CN-YunxiNeural",   # 中文 greetings / zh replies
}

# ----------------------------------------------------------------------- STT

def listen(timeout_s: float = 15.0) -> str:
    """Block until one utterance is captured and transcribed.

    TODO (bench): implement with
      1. sounddevice / arecord capture from the ReSpeaker (see HARDWARE.md),
      2. VAD to find end of speech (silero-vad: ~1 line),
      3. faster-whisper transcribe (language autodetect covers en+zh).
    Dev fallback: keyboard input so the whole stack runs without a mic.
    """
    try:
        return input("🎤 (type to simulate speech)> ").strip()
    except EOFError:
        return ""

# ----------------------------------------------------------------------- TTS

def speak(text: str, face_key: str = "shaka"):
    """Synthesize + play one utterance. Blocking. edge-tts implementation
    works today in dev; swap internals for piper when offline."""
    voice = EDGE_VOICES.get(face_key, EDGE_VOICES["shaka"])
    try:
        import edge_tts
    except ImportError:
        print(f"[tts/{voice}] {text}")
        return
    async def _run():
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        await edge_tts.Communicate(text, voice).save(path)
        # mpg123 is tiny and reliable on Pi; TODO: apt install mpg123
        subprocess.run(["mpg123", "-q", path], check=False)
    asyncio.run(_run())

def speak_stream(token_iter, face_key: str = "shaka"):
    """Low-latency path: buffer LLM tokens into clauses (split on .,!?;:\n)
    and synthesize clause-by-clause while the LLM is still generating.
    Target: first audio <1.5s after end of user speech.

    TODO (bench): run synthesis in a worker thread with a playback queue so
    clause N plays while clause N+1 synthesizes. Keep a sentence buffer of 1.
    """
    buf = ""
    for tok in token_iter:
        buf += tok
        while any(c in buf for c in ".!?;\n"):
            cut = max(buf.rfind(c) for c in ".!?;\n")
            clause, buf = buf[:cut + 1].strip(), buf[cut + 1:]
            if clause:
                speak(clause, face_key)
    if buf.strip():
        speak(buf.strip(), face_key)
