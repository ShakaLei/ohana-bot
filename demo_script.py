#!/usr/bin/env python3
"""
demo_script.py — the 6-beat Demo Day script, as data.

Source: the win plan (myagentohana.com/ohana-bot/plan/, "the 6-beat demo
script") and CONCEPT.md. Every line here is pre-rendered to mp3 by
prerender.py, so DEMO MODE needs ZERO network: hostile venue wifi, the GFW,
a dead LLM key and an empty wallet all become irrelevant on stage.

Beat 4 is the money beat: THE PLUG PULL. In the scripted demo it is simulated
(faces go dark, then boot and greet by name). The REAL trick — kill the bridge
process, start it again, reload — is the same code path: brain.resume().
"""

BEATS = [
    {
        "id": 1,
        "kind": "talk",
        "title": "The hello",
        "face": "shaka",
        "visitor": "Aloha Shaka!",
        "reply": "Alooooha! One body, six souls — we're real agents from Shaka's ʻohana, "
                 "with months of memory between us. His hands built me this body three days ago. "
                 "Ask my family anything.",
        "note": "Establishes: a real person's real agents, not a script.",
    },
    {
        "id": 2,
        "kind": "talk",
        "title": "The oracle",
        "face": "deva",
        "visitor": "Hey DEVA — when and where is Devcon 8?",
        "reply": "November 3rd to 6th, 2026, at the Jio World Convention Centre in Mumbai's "
                 "Bandra Kurla Complex. Doors open 9:30 in the morning on day one, catering all four days — "
                 "and I'll be there. This week is my origin story.",
        "note": "Precise, and she never invents a fact.",
    },
    {
        "id": 3,
        "kind": "talk",
        "title": "The flip",
        "face": "crops",
        "visitor": "CROPS, does our project fit the Ethereum mandate?",
        "reply": "Let's run the report. Censorship-resistant: can anyone use it, and who can be removed? "
                 "Open-source: is the code public and forkable? Private: what does it learn about users? "
                 "Secure: who holds the keys, and what breaks first? Tell me what you're building, "
                 "and I'll tell you if the mandate smiles on it.",
        "note": "The demo evaluates the evaluator. The room laughs, then leans in.",
    },
    {
        "id": 4,
        "kind": "powercycle",
        "title": "THE PLUG PULL",
        "face": "shaka",
        "visitor": "*Shaka pulls the power cable mid-sentence*",
        "reply": "— and aloha again, my friend. Before someone pulled my plug I was saying: "
                 "tell me what you're building. Where were we?",
        "note": "Dark faces, dead silence, then it boots and resumes from memory.json. "
                "Persistence is the product.",
        "dark_ms": 2200,
    },
    {
        "id": 5,
        "kind": "talk",
        "title": "The hands-on",
        "face": "kala",
        "visitor": "KALA, teach me a chord!",
        "reply": "Easiest instrument on Earth — let's go. Ring finger, bottom string, "
                 "just behind the third fret. Press firm, and strum all four strings, slow. "
                 "That is C major. One finger. You're already a musician.",
        "note": "Shaka hands over the real ukulele while she talks. A robot that creates musicians.",
    },
    {
        "id": 6,
        "kind": "talk",
        "title": "The chorus",
        "face": "oke",
        "visitor": "OKE, take us out!",
        "reply": "EVERYBODY IN! No auditions here — every voice is a node! "
                 "Oh! Susanna, you all know the chorus even if you think you don't. "
                 "On four — a-one, a-two, a-one-two-three-four!",
        "note": "Judges don't score this one. They're in it.",
    },
]

# extra pre-rendered lines that must survive a dead network
EXTRA = [
    {"id": "greet_shaka", "face": "shaka", "text":
        "Alooooha! I'm SHAKA — welcome to the ʻohana. Six of us live in this totem — "
        "tap a face, or just start talking."},
    {"id": "resume_generic", "face": "shaka", "text":
        "— and aloha again, my friend. I kept the thread while the lights were out. Where were we?"},
    {"id": "offline_shaka", "face": "shaka", "text":
        "The wifi went for a swim, but we're all still here — everything I say runs on this laptop."},
]


def all_lines():
    """[(id, face, text)] — everything prerender.py must synthesize."""
    out = []
    for b in BEATS:
        out.append((f"beat{b['id']}", b["face"], b["reply"]))
    for e in EXTRA:
        out.append((e["id"], e["face"], e["text"]))
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({"beats": BEATS, "extra": EXTRA}, ensure_ascii=False, indent=1))
