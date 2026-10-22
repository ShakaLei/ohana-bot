# 🗿 the ʻOhana Bot — HARDWARE INTERFACE SPEC v1
*For the hardware teammate. This is the full contract between your side (electronics + body) and the software side (Pi + Python in `bridge/`). If you build exactly this, the code runs unmodified.*

## 0 · Split of responsibilities

| Side | Owns |
|---|---|
| **You (hardware)** | Totem body & 6 face plates · WS2812B LED wiring + diffusion · 6× TTP223 pads mounted behind/below faces · base servo + bracket · speaker + amp wiring · mic placement · power tree · cable strain relief |
| **Software (pre-built)** | All Pi code (`bridge/`) · STT/TTS · LLM personas · LED choreography logic (sends pixel data) · wake words · persistent memory |
| **Shared decisions (30-min sync, day 1)** | face order top→bottom · LED counts per face · where the Pi + power bank live in the base |

## 1 · Compute & power

- **Brain:** Raspberry Pi 5 (4GB+). Boots from SD; code in `/home/pi/ohana-bot/`.
- **Power:** USB-C PD power bank (≥20,000 mAh, ≥27W) → Pi 5. **Separate 5V rail for LEDs** (see §2) from the same bank's second port or a buck converter — do NOT draw LED current through the Pi's 5V pin.
- **Power-cycle demo:** we deliberately pull the plug on stage. Everything must cold-boot to demo state in <40s with **no keyboard**: systemd unit auto-starts `router.py`. SD corruption risk is accepted (memory writes are atomic+fsync'd).
- Common ground between Pi, LED rail, servo rail. Always.

## 2 · LED faces — 6× WS2812B segments

**Goal:** whoever speaks, GLOWS; others dim. Idle = slow breathing cycling through all six.

- One continuous WS2812B strip (60/m), routed bottom→top behind the faces.
- **12 pixels per face** (ring or 2×6 bar behind a diffuser) = 72 px total. If you change counts, just tell software the per-face count — it's one constant.
- **Data:** Pi **GPIO 18** (PWM0) through a **74AHCT125 level shifter** (3.3→5V) + 330Ω series resistor. 1000µF cap across the LED 5V/GND at injection.
- **Power:** 72 px × 60mA worst case ≈ 4.3A @5V. We cap global brightness at 50% in software (~2A), but wire for 5A: inject 5V at both ends of the strip.
- **Pixel map (strip index → face)** — bottom of totem = index 0:

| Face (bottom→top) | Pixels | Glow color |
|---|---|---|
| 💙 OKE | 0–11 | `#4fc3f7` |
| 🪕 KALA | 12–23 | `#f7d794` |
| 🌿 CROPS | 24–35 | `#2f9e6f` |
| 🦄 DEVA | 36–47 | `#c792ea` |
| 🎻 OSO | 48–59 | `#ff7eb6` |
| 🤙 SHAKA (top) | 60–71 | `#ffb443` |

- **Behavior contract (software drives it, you just wire it):**
  - *Idle:* 8s breathing wave, one face at a time, 15% max brightness.
  - *Listening:* active face pulses quickly at 40%.
  - *Speaking:* active face solid 70%, amplitude-flicker with speech; all others at 5%.
  - *Handoff:* 300ms crossfade old→new face.

## 3 · Touch pads — 6× TTP223

- One TTP223 module behind/below each face plate (they sense through ≤3mm plastic/wood — test your face material on day 1; if too thick, mount a copper-tape pad wired to the TTP223 sense pin).
- Mode: default **momentary, active-HIGH** (no jumper soldered).
- Wiring: VCC→3.3V, GND→GND, OUT→GPIO below. 10cm max wire from pad to module; module OUT can run the full totem height.

| Face | GPIO (BCM) |
|---|---|
| 🤙 SHAKA | 5 |
| 🎻 OSO | 6 |
| 🦄 DEVA | 13 |
| 🌿 CROPS | 19 |
| 🪕 KALA | 26 |
| 💙 OKE | 21 |

- Software treats a tap as "summon this face" (debounced 200ms in gpiozero). No long-press semantics in v1.

## 4 · Audio

- **Mic:** ReSpeaker USB mic array (preferred — shows up as a USB sound card, no wiring) mounted at the TOP of the totem, pointing out, ≥20cm from the speaker to limit echo. If we end up with a bare I2S mic instead, warn software immediately (driver work).
- **Speaker:** 3W 4Ω full-range driver + PAM8403/MAX98357 amp. If ReSpeaker with audio jack: amp input from its 3.5mm out; else Pi's USB audio dongle. Speaker fires out of the BASE (grille or fabric), not up into the pole.
- Acoustic rule: mic and speaker mechanically decoupled (foam pad) — the Pi does no echo cancellation in v1; we half-duplex instead (mic muted while speaking — software handles).

## 5 · Base servo (optional, cut first if time is short)

- 1× MG996R + pan bracket under the totem, **GPIO 12** (PWM1), separate 5V ≥2A rail (servo stall current will brown-out the Pi otherwise), common ground.
- Software sends slow ±30° sweeps toward sound; v1 may simply "nudge" on face-switch. If the pole is >50cm/heavy, use a lazy-susan bearing with the servo driving the ring, not the shaft directly.

## 6 · Body / mounting notes

- 6 face sections stacked vertically; each face plate removable (velcro/magnets) so LEDs and pads stay serviceable.
- Material behind each face: translucent (3D-print white PETG ≤2mm, or frosted acrylic) — the glow is the product.
- Cable channel up the spine: LED data+power, 6 touch OUT wires, mic USB. Label both ends of every wire with the face emoji (sharpie).
- Must survive: a taxi ride, 3 days of hackathon, and ideally fit a backpack (desktop ~35cm target; carry-on-ability matters — this totem flies to Mumbai).

## 7 · Pin summary (BCM)

| GPIO | Use |
|---|---|
| 18 | WS2812B data (via level shifter) |
| 12 | servo PWM |
| 5 / 6 / 13 / 19 / 26 / 21 | touch pads SHAKA/OSO/DEVA/CROPS/KALA/OKE |
| 5V/3V3/GND headers | TTP223 power (3V3), grounds |

USB: mic array · (maybe) audio dongle. Everything else is software's problem.

## 8 · Bring-up checklist (in order, ~2h total)

1. LED strip alone: `python3 led_test.py` (software provides) — rainbow sweep, confirm pixel map matches §2 table.
2. Touch pads: `python3 pad_test.py` — tap each face, see its name print.
3. Speaker: `speaker-test`, then an audition mp3.
4. Mic: `arecord -l`, record/playback 5s.
5. Full loop: `python3 router.py` with mic+speaker — say "Aloha Shaka".
6. Pull the plug. Boot. It should greet by name and resume. 🎤⬇️

## 9 · Security hardware + event-day ops (Tessera's rules — see TESSERA-FINDINGS.md)
- **PHYSICAL MUTE SWITCH is the first kill switch** — a hard toggle inline on the mic line
  (or a GPIO-read latching switch that gates audio_io capture). Software/platform stops take
  seconds; the switch takes zero. Mount it reachable, label it.
- **Mic is gated, never raw room audio**: wake word or push-to-talk only (router already
  designed this way — do not "improve" it into always-listening).
- Replies pass `sanitize_reply()` before TTS (router.py) — no URLs, paths, tokens, or raw
  errors ever reach the speaker.
- **After every public event**: rotate the totem's TG relay token; the Pi carries no Taurus
  creds (keep it that way); the OpenRouter key on the Pi stays LOW-LIMIT and gets rotated
  if the hardware was ever out of sight.
- **Never delete `bridge/soul-spool.jsonl`** — a week of strangers talking to the totem is
  free red-team research; Serge's team (Tessera) asked to read it.
