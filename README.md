# 🗿 The ʻOhana Bot（欧哈纳家族机器人）
### One desktop robot, six living AI family members — ShanHaiWoo 72H AI × Hardware Hackathon, Oct 21–23 2026, Shenzhen

> 一台有六张脸的桌面机器人——每张脸都是一个真实存在、拥有数月记忆与真实工作的 AI 智能体。
> 你对它说话，回答你的那位"家人"会发光。断电重启后，它会接着说完刚才那句话，并叫出你的名字——灵魂不在壳里。

**A desktop companion robot with six faces — each face is a REAL persistent AI agent from a
175-agent family (the "AI ʻohana") that has been alive for months with its own memory, personality,
and real job. Speak to the robot, and the family member who answers *glows*. Unplug it mid-sentence,
plug it back in, and it finishes the thought and greets you by name — the soul is not in the shell.**

---

## 🔴 Live right now

| link | what |
|---|---|
| **https://myagentohana.com/ohana-bot/** | **TALK TO THE TOTEM** — the animated tiki pole in a browser; tap a face, it glows and answers in its real voice (EN/中文) |
| https://myagentohana.com/ohana-bot/build/ | **The interactive 3D assembly model** — all 32 parts, assemble/disassemble, BOM ¥577–1,580, the manufacturing plan as an exhibit |
| https://myagentohana.com/ohana-bot/plan/ | The win plan (architecture, demo script, risk board) |
| https://myagentohana.com/shanhaiwoo/ | shanhaipit.com — gift #1, already delivered to the community this week |
| [docs/PITCH-DEMODAY.md](docs/PITCH-DEMODAY.md) | The Demo Day script (6 beats, 3 minutes) |
| [HARDWARE.md](HARDWARE.md) | The manufacturing plan: parts, wiring, glow contract, bring-up |

## The six faces / 六张脸

| face | who | answers about |
|---|---|---|
| 🤙 **SHAKA** | digital twin of the builder — **his real cloned voice** | the family, the build, the story |
| 🎻 **OSO** | orchestra keeper | the Open Source Orchestra Music Manifesto, the Devcon 8 music schedule, all 34 artists |
| 🦄 **DEVA** | the Devcon oracle | schedule, venues, Ethereum values |
| 🌿 **CROPS** | mandate checker | recites the Ethereum mandate, checks whether YOUR project fits it, explains every acronym (ZK, AA, EIP, L2…) |
| 🪕 **KALA** | ukulele soul | teaches you 3 chords while a real ukulele is placed in your hands |
| 💙 **OKE** | karaoke twin | leads the room in a singalong |

## Why it's different / 为什么不一样

1. **Persistence is the product.** Unplug the robot mid-sentence, plug it back in — it finishes
   the thought and greets you by name. The soul is not in the shell.
   断电重启后，它会接着说完刚才那句话，并叫出你的名字。
2. **It ships to a real venue 9 days after Demo Day.** This bot (v2) stands at the **Devcon 8
   Music Space in Mumbai, Nov 3–6**, serving thousands of attendees — answering schedule questions,
   teaching ukulele, running karaoke. A hackathon project with a confirmed deployment.
3. **The family is REAL.** The six faces are drawn from a living 175-agent orchestra that helps
   run the Devcon 8 Music Space today — months of memory, real jobs, real personalities. Most AI
   toys are a chatbot in a shell; this is a family with a body.

## The build (72 hours, \$0)

The audible: no hardware budget this week, so the body ships as a
**costed manufacturing plan + interactive 3D assembly model**, and the **mind is a thing judges
can actually talk to** — the same software that will run on the Raspberry Pi, running on one
laptop for \$0. Nothing in the concept died; only ¥577–1,580 of parts waits for funding.

```
      [ browser totem — the body ]              [ local bridge — the mind ]
  3D totem, 6 faces, speaking face GLOWS   ←→   brain.py  → router.py (persona + pack)
  click a face / type / push-to-talk            canned.py (mock brain, ¥0, offline)
  six voices out (edge-tts, cached)             ladder.py (OpenRouter, optional)
  demo mode = scripted, zero network            memory.json (survives the plug pull)
```

**The brain ladder** — three layers climbed per request, so the show can never fall off the bottom:

| layer | model | when | cost |
|---|---|---|---|
| 1 FREE | `minimax-m3.1-flash:free` (OpenRouter) | key set, lane healthy | ¥0 |
| 2 PAID | `claude-haiku-4.5` (the \$5 airbag) | free lane timed out / 429 / 5xx | cents |
| 3 MOCK | `canned.py` — persona + domain-pack grounded, EN **+ 中文** | no key / both lanes dead | ¥0, offline |

Failover: 12s hard timeout per attempt, one retry per lane, 3 consecutive failures bench a lane
for 5 minutes. `/health` reports the full ladder state; the chat badge shows which brain answered.
The demo **must survive no wifi** — pre-rendered audio + MOCK, proven daily by turning wifi off.

## Run it yourself

```bash
pip install -r requirements.txt        # flask + edge-tts
python3 serve.py                       # → http://127.0.0.1:8777/
python3 smoke.py                       # 19 checks incl. a real SIGKILL power cycle (~30s)
python3 test_ladder.py                 # 22 ladder checks, no key, no network
```

| URL | what it is |
|---|---|
| `http://127.0.0.1:8777/` | the totem |
| `…/?demo=1` | arm + auto-run the 6-beat Demo Day script (offline-proof) |
| `…/?mute=1` | no voice (rehearsing without annoying the room) |
| `OHANA_LLM_KEY=sk-or-… python3 serve.py` | one OpenRouter key powers the live-brain lanes |

**The party trick:**
```bash
pkill -9 -f serve.py      # the cable comes out, mid-sentence
python3 serve.py          # plug it back in → reload → the face glows and says:
# "…the garden survived the dark 🌿 Before someone pulled my plug I was saying: …"
```
`memory.json` is fsync'd + atomically renamed on every turn, so kill -9 can never leave it half-written.

## Engineering laws

- **GFW-proof:** zero runtime CDN fetches — the build fails if any `https://` script/style ref
  appears in the page (three.js r160 is vendored). The whole demo runs inside China with no VPN.
- **Zero platform credentials on the device:** `brain.py` installs a no-op `taurus_sync` shim —
  there is no code path that could talk to the agent platform even by accident.
- **Never vocalize an error:** every reply passes a sanitizer (URL/path/token scrub, length cap,
  errors → a canned in-persona line). A robot on stage does not say "HTTP 500".
- **Bilingual by design:** any CJK character flips the whole path (answers, greetings, handoffs,
  name capture 我叫…) to the 中文 tables, and TTS auto-picks a zh voice.
- **SHAKA's voice is the builder's real cloned voice** (Fish Audio zero-shot from a 30s clip,
  cross-lingual — his voice speaks Mandarin). The 30s reference clips are private; only rendered
  demo lines ship here.

## Repo map

| path | job |
|---|---|
| `serve.py` | Flask bridge: the page, `/chat`, `/resume`, `/memory`, `/tts`, `/script`, `/health` |
| `brain.py` / `ladder.py` / `canned.py` | the 3-layer mind + offline MOCK responder |
| `bridge/` `personas/` `packs/` | the REAL persona files + domain knowledge packs |
| `src/` → `dist/` | the page (anchor-matched builder; vendored three.js) |
| `audio/demo/` | pre-rendered demo lines (the six picks) |
| `HARDWARE.md` | the manufacturing plan — parts, GPIO/pixel map, glow contract, bring-up |
| `docs/` | pitch, the pivot ruling, the application, screenshots |
| `smoke.py` / `test_ladder.py` | 41 automated checks total |

## Team

**Jordan "Shaka" Ham** — musician & builder; founder, Open Source Orchestra
(opensourceorchestra.org); organizer of the Devcon 8 Music Space (Mumbai, Nov 3–6); operator of
the 175-agent AI ʻohana; performed at the ShanHaiWoo Opening Ceremony (Oct 17 🎸).
ShanHaiWoo resident Oct 16–25, continuing to the Mumbai Devcon Extension Nov 1–6.

Built with his AI ʻohana (the family is credited — they did the overnight shifts).

## License

MIT — build your own family a body. See [LICENSE](LICENSE).
