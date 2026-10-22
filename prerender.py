#!/usr/bin/env python3
"""
prerender.py — bake every demo line to mp3 on disk.

Run this ONCE on good wifi (hotel, hostel, anywhere) before the hackathon:

    python3 prerender.py

After that, DEMO MODE is a local-file slideshow: zero network, zero API, zero
cost. If the venue wifi is hostile or the GFW eats the TTS endpoint, the stage
does not notice.

    python3 prerender.py --check     # just report what is missing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import demo_script
import tts

HERE = Path(__file__).resolve().parent
DEMO = HERE / "audio" / "demo"
MANIFEST = DEMO / "manifest.json"


def run(check_only: bool = False) -> dict:
    DEMO.mkdir(parents=True, exist_ok=True)
    tts.ensure_voices_json()
    man = {}
    missing, made = [], []
    for lid, face, text in demo_script.all_lines():
        voice = tts.voice_for(face)
        out = DEMO / f"{lid}.mp3"
        ok = out.exists() and out.stat().st_size > 400
        if not ok and not check_only:
            try:
                tts.synth(text, face, out=out)
                ok = True
                made.append(lid)
                print(f"  ✓ {lid:16} {face:6} {voice:22} {out.stat().st_size:>7} bytes")
            except Exception as e:
                print(f"  ✗ {lid:16} {face:6} FAILED: {type(e).__name__}: {e}")
        elif ok:
            print(f"  · {lid:16} cached ({out.stat().st_size} bytes)")
        if not ok:
            missing.append(lid)
        man[lid] = {"face": face, "voice": voice,
                    "file": f"audio/demo/{lid}.mp3" if ok else None,
                    "bytes": out.stat().st_size if ok else 0,
                    "text": text}
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(man)-len(missing)}/{len(man)} lines on disk; manifest -> {MANIFEST}")
    if missing:
        print("MISSING (demo mode will show text with no voice for these):", ", ".join(missing))
    return man


if __name__ == "__main__":
    run("--check" in sys.argv)
