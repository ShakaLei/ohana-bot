# 🌙 CHANGELOG — overnight build, 20 Oct 2026 (12:4x–13:0x UTC)

---

## ⚡ 14:1x UTC UPDATE — THE KEY LANDED, LADDER IS LIVE (and a stage-killer found)

Shaka pasted the OpenRouter key (vaulted at `/workspace/vault/openrouter-key`,
0600, never /shared, never git, never the bundle) and loaded **\$10** —
`is_free_tier: false`, free lane cap **1000 req/day** (was 50), haiku airbag
funded. First real round-trips: FREE 0.77s, PAID ok, DEVA/KALA answered live
through the bridge, 中文 included.

**🐛 STAGE-KILLER #2 FOUND LIVE: minimax-m3.1-flash is a MANDATORY-reasoning
model.** Its thinking silently ate the whole `max_tokens: 300` budget —
`finish_reason: length`, content EMPTY or cut mid-word ("…third metal fret**,
then"). Disabling reasoning = 400 ("mandatory"). Fix in `ladder.py`:
- FREE lane sends `reasoning: {"effort": "low"}` (env `OHANA_LLM_REASONING`,
  "none" omits); **PAID lane never gets it** (a thinking budget changes
  Anthropic temperature rules)
- default `max_tokens` 300 → **900** (the budget INCLUDES thinking tokens)
- `finish_reason == "length"` now fails the lane → failover — never vocalize
  a half-thought
- `smoke.py` quarantines `OHANA_LLM_KEY` from its bridge: the persona/中文
  checks assert the deterministic CANNED tables (a leaked key turned them into
  live-model roulette — 6 false fails)

Tests 18 → **22** (reasoning contract per lane · max_tokens floor · truncated
reply fails over). Smoke **26/26**. Bundle rebuilt 14:18 (4.1 MB, fix inside).
Post-fix live proof: KALA full C-major lesson (237 chars, pack-accurate), DEVA
中文 facts exact, badge `free:minimax-m3.1-flash`.
⚠️ `/shared/ohana-bot/bridge/llm.py` (the Pi-path, unused by totem-web) still
sends bare max_tokens=300 — same burn if ever pointed at a reasoning model.

*Smoke: **26/26 green** (was 19/19 — all 19 originals kept, 7 new checks added).
Build gates (node --check + GFW + py_compile) green. Laptop bundle rebuilt (4.1 MB).
Nothing deployed — `/shared/public` and gh-pages untouched, your call as always.*

---

## ① THE 3-LAYER BRAIN LADDER — new `ladder.py`, wired through `brain.py`

```
layer 1  FREE   minimax/minimax-m3.1-flash:free   ¥0  (best :free model on OpenRouter 2026-10-20:
                                                       quality #1 of 18, flash latency, 1M ctx)
layer 2  PAID   anthropic/claude-haiku-4.5        your $5 airbag
layer 3  MOCK   canned.py                         ¥0, offline, never fails
```

**Run it with the key (the whole contract):**
```bash
OHANA_LLM_KEY=sk-or-…  python3 serve.py
```
One key powers both network lanes. No key → pure MOCK, **zero sockets opened** (proved by test).

**How it behaves, per request:** try FREE with a hard 12s timeout + 1 retry →
any timeout/429/5xx/invalid-json/empty reply → try PAID (same rules) → PAID fails
too → MOCK answers in persona. **3 consecutive failed requests bench a lane for
5 minutes** so a dead lane can't burn 24s of stage time on every question; a
success un-benches and clears it. The reply still flows through the REAL
`router.handle()` → `sanitize_reply()` — the ladder replaced only the completion
call, nothing else.

**Overrides:** `OHANA_LLM_MODEL_FREE` · `OHANA_LLM_MODEL_PAID` · `OHANA_LLM_BASE` · `OHANA_LLM_TIMEOUT`.
If minimax's free lane feels weak on stage, next picks from today's list:
`nvidia/nemotron-3.5-super-vl:free`, `thinkingmachines/inkling-small:free`.
Free-tier limits: 20 req/min, 200 req/day — plenty for a demo room; the bench + airbag absorb the rest.

**Visibility:** `/health` now carries the full ladder state (models, strikes,
bench countdown, ok/fail counts, last error); the chat badge shows
`free:minimax-m3.1-flash` / `paid:claude-haiku-4.5` / `mock brain · ¥0`; the
startup banner prints the whole ladder.

**Proof without a real key** — `test_ladder.py`, 18 checks against a local mock
endpoint (fake key `test-key-not-real`): free answers · 429→paid failover ·
bad-json→paid · both-dead→MOCK · benching + benched-lane-skipped · bench
survives a paid success · timeout failover is bounded · **no key = zero network
calls** · badge strings stay short. Plus a full E2E through the real serve.py
process: free→paid→MOCK cascade and `/health` reporting all verified live.
`smoke.py` runs the suite as one of its checks.

**🐛 Real bug found & fixed by these tests:** the `X-Title: the ʻOhana Bot`
header — urllib encodes headers **latin-1**, so the ʻokina raised
`UnicodeEncodeError` on EVERY request. Every real-key call would have died on
stage. Fixed in `ladder.py` AND in `/shared/ohana-bot/bridge/llm.py` (same bug,
inherited from there; that file had never been run with a key).

## ② 中文 ANSWER LANE — the mock brain now speaks Chinese

Any CJK character in the visitor's message flips the whole mock path to new
中文 tables in `canned.py`: **~50 translated answers** across all six faces
(every EN keyword entry has a zh twin), zh greetings (pulled from the 中文
lines already in the persona files), zh handoffs (names stay latin → the
face-glow handoff detector keeps working), zh nudges, and zh name capture
(`我叫小明` — deliberately not `我是`, too many false positives) which **lands in
memory.json via brain.ask**, so the power-cycle trick works for a Chinese judge too.

Facts preserved exactly: Devcon 8 = **2026年11月3日至6日 · 孟买 BKC 的 Jio World
会展中心**; CROPS = **抗审查/开源/隐私/安全** with the EN terms glossed; ticket
numbers, both OSO day-schedules, the KALA C-major lesson (无名指·最下弦·第三品),
OKE's five public-domain songs.

**Voices:** `/tts` auto-detects CJK → zh lane; faces without a `<face>_zh` pick
in voices.json fall back to `zh-CN-XiaoxiaoNeural` so **Chinese text is never
read by an English voice** (SHAKA keeps his `zh-CN-YunxiNeural`). Offline, the
existing text-only degradation covers it as before.

**Static mirror too:** `chat.js` got `STATIC_LINES_ZH` — a typed 中文 message on
the no-bridge public mirror gets an honest in-persona 中文 line, same CJK test.

Verified in a real browser against the live bridge: DEVA answered
`Devcon 什么时候、在哪里举行？` with the exact zh facts, glow + handoff intact.

## ③ Housekeeping

- `build.sh` syntax-gates `ladder.py` + `test_ladder.py` too; README rewritten
  (ladder table, env contract, 中文 lane); dev bridge on :8777 restarted on the
  new code; laptop bundle rebuilt → `/shared/ohana-bot/totem-web.tar.gz` (4.1 MB,
  carries the fixed bridge llm.py).
- Laws re-verified: 3D source untouched · 0 CDN refs in the shipped page ·
  zero Taurus credentials (taurus_sync still a structural no-op) · **no key
  string anywhere in the tree** (swept) · static mirror can't hang on THINKING.

## New smoke checks (19 → 26)

1. static mirror speaks 中文 (`STATIC_LINES_ZH` + 静态镜像 in the page)
2. brain ladder unit tests — 18 sub-checks, mock endpoint
3. ladder reported on /health (mock when no key)
4. SHAKA answers in 中文
5. DEVA 中文 facts exact (11月3日至6日 · Jio World · 孟买)
6. 中文 cross-face handoff lights a sibling
7. 中文 never read by an English voice (zh voice fallback)

## What I could NOT test without a real key

- An actual OpenRouter round-trip (both lanes are only proven against the mock
  endpoint and E2E through serve.py with a scripted server). First thing to run
  when the key lands:
  ```bash
  cd /workspace/ohana-totem
  OHANA_LLM_KEY=sk-or-… python3 serve.py     # banner must say LADDER …
  # then in the page: ask anything → badge "free:minimax-m3.1-flash";
  # curl -s localhost:8777/health | python3 -m json.tool   → ladder.free.ok ≥ 1
  ```
- Whether minimax-m3.1-flash's free tier is reachable/fast from inside the GFW
  at the venue (if it stalls, the 12s timeout + bench route around it — but
  consider pinning `OHANA_LLM_MODEL_FREE` after one on-site test).
- Real zh TTS audio quality for the 5 Xiaoxiao-fallback faces (edge-tts was
  reachable here and the zh cache path works, but no human listened yet).
