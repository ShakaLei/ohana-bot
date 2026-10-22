#!/usr/bin/env python3
"""
router.py — the ʻOhana Bot persona router (Raspberry Pi reference).

Responsibilities:
  * wake-word table  -> which face answers
  * touch-pad switch -> tap a face to summon it (GPIO events from 6x TTP223)
  * persona loader   -> persona .md + domain pack .md -> system prompt
  * per-visitor persistent memory (memory.json) -> survives power cycles
    THIS is the demo trick: pull the plug mid-conversation, boot, and the
    totem resumes the thought and greets the visitor by name.

No external deps except what llm.py / audio_io.py need. Run on Pi:
    python3 router.py            # console chat loop (no audio) for testing
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # /shared/ohana-bot or repo root
PERSONA_DIR = ROOT / "personas"
PACK_DIR = ROOT / "packs"
MEMORY_PATH = Path(os.environ.get("OHANA_MEMORY", str(ROOT / "bridge" / "memory.json")))

# ---------------------------------------------------------------- wake words

@dataclass
class Face:
    key: str                 # persona/pack file stem
    name: str
    emoji: str
    led_index: int           # which LED segment glows (see HARDWARE.md)
    color: str               # hex glow color (matches audition page)
    wake_words: list = field(default_factory=list)
    pack: str | None = None  # pack file stem, None = persona only

FACES = [
    Face("shaka", "SHAKA", "🤙", 0, "#ffb443",
         ["aloha shaka", "hey shaka", "shaka", "阿罗哈"], None),
    Face("oso",   "OSO",   "🎻", 1, "#ff7eb6",
         ["oso", "hey oso", "orchestra"], "oso-pack"),
    Face("deva",  "DEVA",  "🦄", 2, "#c792ea",
         ["hey deva", "deva", "devcon"], "deva-pack"),
    Face("crops", "CROPS", "🌿", 3, "#2f9e6f",
         ["hey crops", "crops", "steward"], "crops-pack"),
    Face("kala",  "KALA",  "🪕", 4, "#f7d794",
         ["kala", "hey kala", "ukulele"], "kala-pack"),
    Face("oke",   "OKE",   "💙", 5, "#4fc3f7",
         ["oke", "hey oke", "karaoke"], "oke-pack"),
]
FACE_BY_KEY = {f.key: f for f in FACES}
DEFAULT_FACE = "shaka"

def match_wake_word(text: str) -> str | None:
    """Return face key if the transcript starts with / contains a wake word.
    Checked longest-first so 'aloha shaka' wins over 'shaka'."""
    t = re.sub(r"[^\w\s一-鿿]", "", text.lower()).strip()
    pairs = [(w, f.key) for f in FACES for w in f.wake_words]
    for w, key in sorted(pairs, key=lambda p: -len(p[0])):
        if t.startswith(w) or f" {w} " in f" {t} ":
            return key
    return None

# ------------------------------------------------------------- touch switch

def setup_touch_pads(on_tap):
    """6x TTP223 touch pads -> GPIO. See HARDWARE.md for the pin map.
    on_tap(face_key) is called from the GPIO thread.
    Stub: replaced with real gpiozero wiring on the Pi."""
    try:
        from gpiozero import Button  # type: ignore
    except ImportError:
        print("[touch] gpiozero not available — touch pads disabled (dev mode)")
        return None
    # Pin map must match HARDWARE.md exactly:
    PAD_PINS = {"shaka": 5, "oso": 6, "deva": 13, "crops": 19, "kala": 26, "oke": 21}
    pads = {}
    for key, pin in PAD_PINS.items():
        b = Button(pin, pull_up=False)         # TTP223 default: active-high momentary
        b.when_pressed = (lambda k=key: on_tap(k))
        pads[key] = b
    return pads

# --------------------------------------------------------------- LED + servo

def set_glow(active_key: str | None):
    """Tell the LED controller which face glows. Stub — the real
    implementation speaks the serial/neopixel protocol in HARDWARE.md."""
    print(f"[led] glow -> {active_key or 'idle breathing (all faces)'}")

def face_servo_nudge():
    """Optional: slow pan toward the speaker. Stub (one MG996R on GPIO 18)."""
    pass

# ------------------------------------------------------------ persona loader

def load_persona(face_key: str) -> str:
    face = FACE_BY_KEY[face_key]
    parts = [(PERSONA_DIR / f"{face.key}.md").read_text(encoding="utf-8")]
    if face.pack:
        parts.append((PACK_DIR / f"{face.pack}.md").read_text(encoding="utf-8"))
    rules = (
        "\n## TOTEM RULES (always)\n"
        "- You are ONE face of a six-face robot. Keep spoken replies SHORT: "
        "1–3 sentences unless teaching or storytelling is explicitly wanted.\n"
        "- If the question belongs to a sibling, answer in one line and hand off "
        "by saying their name (the router lights their face).\n"
        "- If visitor_memory below contains a name or an unfinished thought, "
        "greet them by name and pick up where you left off.\n"
        "- Never read URLs out loud character by character; say 'the schedule page' etc.\n"
    )
    return "\n\n".join(parts) + rules

# ------------------------------------------------- persistent visitor memory

class VisitorMemory:
    """Tiny persistent store. Survives power cycles because every update is
    flushed to disk (fsync). Schema:
    {
      "visitor": {"name": "...", "lang": "en"},
      "active_face": "shaka",
      "last_thought": "one-line summary of what we were saying",
      "history": {face_key: [{"role": "...", "content": "..."}], ...},
      "updated": 1760000000
    }
    """
    MAX_TURNS = 12  # per face, keeps the fast path fast

    def __init__(self, path: Path = MEMORY_PATH):
        self.path = path
        self.data = {"visitor": {}, "active_face": DEFAULT_FACE,
                     "last_thought": "", "history": {}, "updated": 0}
        if path.exists():
            try:
                self.data.update(json.loads(path.read_text(encoding="utf-8")))
            except Exception as e:
                print(f"[memory] corrupt memory.json ({e}) — starting fresh")

    def flush(self):
        self.data["updated"] = int(time.time())
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(self.path)          # atomic — a power cut never half-writes

    def remember_turn(self, face_key: str, role: str, content: str):
        h = self.data["history"].setdefault(face_key, [])
        h.append({"role": role, "content": content})
        del h[:-2 * self.MAX_TURNS]
        self.flush()

    def note_name(self, transcript: str):
        """Cheap name capture: 'my name is X' / \"I'm X\". The LLM also updates
        last_thought via router after each reply."""
        m = re.search(r"\b(?:my name is|i am|i'm|call me)\s+([A-Z][a-zA-Z\-]{1,20})",
                      transcript, re.IGNORECASE)
        if m:
            self.data["visitor"]["name"] = m.group(1).strip().title()
            self.flush()

    def resume_blurb(self) -> str:
        v = self.data["visitor"]
        bits = []
        if v.get("name"):
            bits.append(f"The visitor's name is {v['name']}.")
        if self.data.get("last_thought"):
            bits.append(f"Before the last shutdown you were saying: "
                        f"{self.data['last_thought']!r} — resume it naturally.")
        return " ".join(bits)

# ----------------------------------------------- reply sanitizer (pre-TTS)
# Tessera's relay-side rules (TESSERA-FINDINGS.md): a public room is untrusted
# input and the speaker is a public output. Before anything reaches TTS:
#   * length cap (a totem face speaks in breaths, not essays)
#   * strip anything URL-, path- or token-shaped (never leak, never vocalize)
#   * never vocalize raw errors — fail in persona instead

MAX_SPOKEN_CHARS = 700
_SCRUB_PATTERNS = [
    re.compile(r"https?://\S+", re.I),                    # URLs
    re.compile(r"\b[\w.-]+\.(?:com|org|net|io|ai|link|me)\b\S*", re.I),  # bare domains
    re.compile(r"(?:/[\w.-]+){2,}"),                      # unix-y paths
    re.compile(r"\b(?:sk|gh[pos]|xox[bap]|ey[JA])[A-Za-z0-9_\-\.]{16,}\b"),  # token-shaped
    re.compile(r"\b[A-Fa-f0-9]{24,}\b"),                  # long hex blobs
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b"),         # telegram bot tokens
]

CANNED_FAIL = {
    "shaka": "Hoo, the wind took that one 🤙 — ask me again?",
    "oso":   "The orchestra dropped a beat — one more time?",
    "deva":  "My crystal ball flickered ✨ — say that again?",
    "crops": "The garden line went quiet — once more, friend?",
    "kala":  "My string slipped 🪕 — play that question again?",
    "oke":   "The mic cut out 💙 — one more time for me?",
}

_ERRORISH = re.compile(r"^\s*(error|exception|traceback)\b|HTTPSConnection|urlopen|\bstatus\s+\d{3}\b", re.I)

def sanitize_reply(text: str, face_key: str) -> str:
    if _ERRORISH.search(text or ""):
        return CANNED_FAIL.get(face_key, "Say that again for me? 🌺")
    out = text
    for pat in _SCRUB_PATTERNS:
        out = pat.sub("", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    if len(out) > MAX_SPOKEN_CHARS:
        cut = out[:MAX_SPOKEN_CHARS]
        out = cut[:max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), 200) + 1]
    if not out:
        out = CANNED_FAIL.get(face_key, "Say that again for me? 🌺")
    return out

# --------------------------------------------------------------- the router

class Router:
    def __init__(self):
        self.mem = VisitorMemory()
        self.active = self.mem.data.get("active_face", DEFAULT_FACE)
        self.pads = setup_touch_pads(self.switch_face)
        set_glow(self.active if self.mem.data.get("last_thought") else None)

    def switch_face(self, face_key: str):
        if face_key == self.active:
            return
        print(f"[router] switch {self.active} -> {face_key}")
        self.active = face_key
        self.mem.data["active_face"] = face_key
        self.mem.flush()
        set_glow(face_key)

    def handle(self, transcript: str) -> str:
        """One visitor utterance in, one spoken reply out."""
        woke = match_wake_word(transcript)
        if woke:
            self.switch_face(woke)
        self.mem.note_name(transcript)

        from llm import chat  # local module, see llm.py
        face = FACE_BY_KEY[self.active]
        system = load_persona(self.active)
        memory_note = self.mem.resume_blurb()
        if memory_note:
            system += f"\n## visitor_memory\n{memory_note}\n"

        history = self.mem.data["history"].get(self.active, [])
        self.mem.remember_turn(self.active, "user", transcript)
        set_glow(self.active)

        try:
            reply = chat(system=system, history=history, user=transcript)
        except Exception as e:
            print(f"[llm] FAIL ({e}) — canned in-persona fallback, never vocalized")
            reply = CANNED_FAIL.get(self.active, "Say that again for me? 🌺")
        reply = sanitize_reply(reply, self.active)

        self.mem.remember_turn(self.active, "assistant", reply)
        # keep a one-line resume hook for the power-cycle trick
        self.mem.data["last_thought"] = reply[-160:]
        self.mem.flush()

        # fire-and-forget mirror to the real Taurus agents (slow soul path)
        try:
            from taurus_sync import mirror_async
            mirror_async(self.active, transcript, reply)
        except Exception:
            pass
        return reply

# --------------------------------------------------------------- dev console

if __name__ == "__main__":
    r = Router()
    name = r.mem.data["visitor"].get("name")
    print(f"🗿 ʻOhana Bot router — active face: {r.active}"
          + (f" — welcome back, {name}!" if name else ""))
    print("   wake words:", {f.key: f.wake_words[0] for f in FACES})
    while True:
        try:
            line = input(f"[{r.active}] you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\naloha 🌺")
            break
        if not line:
            continue
        print(f"[{r.active}] bot> {r.handle(line)}")
