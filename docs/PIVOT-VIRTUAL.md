# 🗿💻 THE AUDIBLE — THE ʻOHANA BOT GOES VIRTUAL
*Shaka, 20 Oct 2026 09:39 UTC (17:39 Shenzhen), T-15h to the hackathon:*
> "we need to audible… I only have \$200 to my name and we can't afford to build the hackathon
> project… I think we should do a completely virtual totem pole that works the exact same but
> interfaces through the computer… We can finish what we started at ETH Global and refine the
> whole project making sure that everything we set out to do works… we include the hardware plan
> and 3D build model as well as the working demo… but unfortunately because of lack of funds
> everything will have to be virtual."

**Ruling: accepted. Nothing in the concept dies — only the ¥577–1,580 of plastic and silicon.**
The software was always the project; the Pi was only a body. We ship the body as a 3D model and
a full manufacturing plan, and we ship the *mind* as a thing judges can actually talk to.

## What changes and what does not

| | before (hardware) | now (virtual) |
|---|---|---|
| Body | Pi 5 + LED rings + touch pads + servo, ¥577–1,580 | the **3D totem already live** at myagentohana.com/ohana-bot/build/ — same 32 parts, same glow contract |
| Faces | 6 LED-lit face plates | 6 faces in the 3D totem; **the speaking face glows, the others dim** (identical contract, already coded in DEMO MODE) |
| Summon | wake word + tap a face (TTP223) | wake word (mic) + **click a face** + type |
| Voice | ReSpeaker mic → speaker | laptop mic → browser → same six voices |
| Brain | `bridge/` on the Pi | **the same `bridge/`**, unchanged, on the laptop |
| Memory | `memory.json` on the SD card | `memory.json` on disk — same file, same power-cycle trick (close the lid / kill the process → reopen → it resumes and greets you by name) |
| Cost | ¥577–1,580 he does not have | **\$0** |

**Zero new dependencies, zero cloud bills.** Domains, hosting (GitHub Pages), TTS (edge-tts) and
the agents themselves are already paid for. The only spend is a handful of LLM cents, and even
that is optional — the demo script runs from pre-rendered audio if the network dies.

## Why this is a stronger submission, not a weaker one

1. **It actually works.** A 72-hour hardware build usually demos half-dead. Ours will be finished,
   rehearsed and bug-free — "finish what we started at ETHGlobal and make sure everything we set
   out to do works" is the whole brief.
2. **The hardware isn't missing — it's specified.** Judges get: the interactive 3D assembly model
   (32 parts, assemble/disassemble, tap a part for GPIO + price), `HARDWARE.md` (the embedded
   contract), the live BOM at ¥577–1,580, and the bring-up sequence. That is a *manufacturing
   plan*, which most hackathon toys never produce.
3. **It is honest, and the honesty is the story.** A Hawaiian musician with \$200 to his name built
   a six-voiced AI ʻohana anyway, because the gift doesn't require a budget. That is the
   ShanHaiWoo spirit in one sentence.
4. **It travels.** A laptop clears customs. The virtual totem flies to Devcon 8 Mumbai (Nov 3–6)
   and runs at the Music Space with no checked bag, no 220V, no broken LED on arrival.
5. **Funding turns it physical later.** DRK Lab grant (¥4,200, sent 20 Oct) and the parts-sponsor
   ask stay open and stay honest: the plan is costed, the software is done, the money builds the
   body. Nothing we said becomes untrue.

## The build (what "works the exact same" means concretely)

```
      [ browser totem — the body ]            [ local bridge — the mind ]
  3D totem, 6 faces, speaking face glows   ←→   router.py   (persona + pack → prompt)
  click a face / hold-to-talk / type            llm.py      (OpenRouter, low-limit key)
  six voices out                                audio_io.py (edge-tts; Fish later)
  demo mode = scripted, no network needed       memory.json (survives restarts)
```

- **Same six faces:** SHAKA 🤙 · OSO 🎻 · DEVA 🦄 · CROPS 🌿 · KALA 🪕 · OKE 💙 — each one distilled
  from a *real* persistent agent's own system prompt, with its domain pack.
- **Same party trick:** kill the process mid-sentence, restart, it resumes and greets the judge by
  name — now provable in front of the room in 3 seconds instead of 30.
- **Offline-proof:** every demo line is pre-rendered to mp3 and every face has canned in-persona
  answers, so GFW, venue wifi or a dead API can never kill the stage.

## 72-hour plan (Oct 21 09:00 → Oct 23 18:30)

- **Tonight (T-15h):** totem-web v0.1 — the 3D body wired to the bridge, click-a-face → it answers
  and glows, memory persists. *(building now)*
- **Day 1 (Tue):** voice in (push-to-talk + wake word), six voices out, the six domain packs
  answering real questions, offline fallbacks.
- **Day 2 (Wed):** the demo script end-to-end, karaoke finale (OKE), KALA's 3-chord lesson,
  judge-name memory, rehearsal with the projector; polish the 3D body (it is the visual).
- **Day 3 (Thu, Demo Day):** freeze by noon, rehearse ×3, submit; the deck = working demo →
  3D model → hardware plan → Mumbai deployment date.

## Open decisions for Shaka
1. **Voice picks** — the audition page is still unanswered; I will default to the A-takes and he can
   swap any face in one click. (Fish Audio real-voice clone for SHAKA stays a \$15 "if funded" item.)
2. **Mic lane** — browser speech recognition needs the network (and the GFW tunnel). Default:
   push-to-talk with type-to-talk always available, wake word as the demo flourish.
3. **Teammates** — a solo build is fine now that there is no soldering. Still want a teammate?
4. **The asks stay open** — Woocon/DRK parts sponsorship is no longer blocking; if it lands, the
   body gets built for the Maker Festival (Oct 24) or Mumbai instead.
