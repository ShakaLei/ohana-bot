#!/usr/bin/env python3
"""
ladder.py — the 3-layer brain ladder for the virtual ʻohana totem.

    layer 1  FREE   a :free OpenRouter model            — primary, ¥0
    layer 2  PAID   anthropic/claude-haiku-4.5          — the $5 airbag
    layer 3  MOCK   canned.py (handled by the CALLER)   — never fails, offline

One key powers both network lanes:

    OHANA_LLM_KEY=sk-or-...  python3 serve.py

No key -> this module never opens a socket; the caller (brain._chat) answers
from canned.py exactly as before. That is asserted by test_ladder.py.

Env contract (all optional except the key):
    OHANA_LLM_KEY           the OpenRouter key. Absent = pure MOCK.
    OHANA_LLM_MODEL_FREE    default minimax/minimax-m3.1-flash:free
                            (best free model on OpenRouter as of 2026-10-20:
                             quality-ranked #1 of 18 :free models, "flash"
                             latency, 1M ctx; swap freely when the list moves)
    OHANA_LLM_MODEL_PAID    default anthropic/claude-haiku-4.5
    OHANA_LLM_BASE          default https://openrouter.ai/api/v1
    OHANA_LLM_TIMEOUT       per-attempt hard timeout, default 12 (seconds)
    OHANA_LLM_REASONING     reasoning effort for the FREE lane only, default
                            "low". minimax-m3.1 is a MANDATORY-reasoning model:
                            without this its thinking eats the whole max_tokens
                            budget and content comes back EMPTY or cut mid-word
                            (found live 2026-10-20 with the real key; reasoning
                            cannot be disabled, 400). "none" omits the param.
                            The PAID lane (claude-haiku) never gets it — a
                            thinking budget changes Anthropic temperature rules.

Failover rules (per request):
    * try FREE: hard timeout ~12s, 1 retry (2 attempts total)
    * any timeout / 429 / 5xx / invalid-json / empty reply -> try PAID (same rules)
    * PAID fails too -> raise LadderExhausted -> caller answers from MOCK
    * 3 consecutive failed REQUESTS on a lane -> bench it for 5 minutes
      (a dead lane must not burn 24s of stage time on every question)
    * a success un-benches and clears the lane

NEVER put the key in a file. It lives in the environment of the serve.py
process and nowhere else. Errors reported via state() are trimmed and the
Authorization header is never logged.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_FREE = "minimax/minimax-m3.1-flash:free"
DEFAULT_PAID = "anthropic/claude-haiku-4.5"
DEFAULT_BASE = "https://openrouter.ai/api/v1"

BENCH_SECONDS = 300          # 5 min on the bench after…
STRIKES_TO_BENCH = 3         # …3 consecutive failed requests
ATTEMPTS = 2                 # 1 try + 1 retry per lane per request


class LadderExhausted(Exception):
    """Both network lanes failed or are benched — fall to MOCK."""


def _short(model: str) -> str:
    """'minimax/minimax-m3.1-flash:free' -> 'minimax-m3.1-flash' (badge-sized)."""
    m = model.rsplit("/", 1)[-1]
    if m.endswith(":free"):
        m = m[:-5]
    return m[:28]


class Lane:
    def __init__(self, name: str, model: str, extra: dict | None = None):
        self.name = name                 # "free" | "paid"
        self.model = model
        self.extra = extra or {}         # extra body params (e.g. reasoning)
        self.strikes = 0                 # consecutive failed requests
        self.benched_until = 0.0
        self.last_error = ""
        self.ok_count = 0
        self.fail_count = 0

    def benched(self) -> bool:
        return time.time() < self.benched_until

    def strike(self, err: str):
        self.last_error = (err or "")[:160]
        self.strikes += 1
        self.fail_count += 1
        if self.strikes >= STRIKES_TO_BENCH:
            self.benched_until = time.time() + BENCH_SECONDS
            self.strikes = 0             # fresh chances when the bench expires

    def clear(self):
        self.strikes = 0
        self.benched_until = 0.0
        self.ok_count += 1

    def state(self) -> dict:
        b = max(0, int(self.benched_until - time.time()))
        return {"model": self.model, "strikes": self.strikes,
                "benched_s": b, "ok": self.ok_count, "fail": self.fail_count,
                "last_error": self.last_error}


class Ladder:
    def __init__(self, key: str | None = None, base: str | None = None,
                 model_free: str | None = None, model_paid: str | None = None,
                 timeout: float | None = None):
        env = os.environ
        self.key = key if key is not None else env.get("OHANA_LLM_KEY", "")
        self.base = (base or env.get("OHANA_LLM_BASE", DEFAULT_BASE)).rstrip("/")
        self.timeout = float(timeout if timeout is not None
                             else env.get("OHANA_LLM_TIMEOUT", "12"))
        effort = env.get("OHANA_LLM_REASONING", "low")
        free_extra = {} if effort == "none" else {"reasoning": {"effort": effort}}
        self.free = Lane("free", model_free or env.get("OHANA_LLM_MODEL_FREE", DEFAULT_FREE),
                         extra=free_extra)
        self.paid = Lane("paid", model_paid or env.get("OHANA_LLM_MODEL_PAID", DEFAULT_PAID))
        self.last_lane = ""              # lane that answered the last request

    # ------------------------------------------------------------- reporting
    @property
    def enabled(self) -> bool:
        return bool(self.key)

    def mode(self) -> str:
        """Short badge string. 'mock' | 'free:<model>' | 'paid:<model>'."""
        if not self.enabled:
            return "mock"
        if not self.free.benched():
            return f"free:{_short(self.free.model)}"
        if not self.paid.benched():
            return f"paid:{_short(self.paid.model)}"
        return "mock"                    # both lanes benched — canned answers

    def state(self) -> dict:
        return {"enabled": self.enabled, "mode": self.mode(),
                "last_lane": self.last_lane,
                "free": self.free.state(), "paid": self.paid.state()}

    # ------------------------------------------------------------- the climb
    def complete(self, system: str, history: list, user: str,
                 max_tokens: int = 900, temperature: float = 0.8) -> tuple[str, str]:
        # 900 not 300: on reasoning models max_tokens INCLUDES the thinking
        # tokens (~80-150 at effort low); 300 left zero room for the answer.
        """Returns (reply_text, lane_name). Raises LadderExhausted -> MOCK."""
        if not self.enabled:
            raise LadderExhausted("no OHANA_LLM_KEY — mock only (no socket opened)")
        errs = []
        for lane in (self.free, self.paid):
            if lane.benched():
                errs.append(f"{lane.name}: benched {int(lane.benched_until - time.time())}s")
                continue
            try:
                text = self._lane_call(lane, system, history, user, max_tokens, temperature)
                lane.clear()
                self.last_lane = lane.name
                return text, lane.name
            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                lane.strike(msg)
                errs.append(f"{lane.name}: {msg[:90]}")
        raise LadderExhausted(" | ".join(errs))

    def _lane_call(self, lane: Lane, system, history, user, max_tokens, temperature) -> str:
        last: Exception | None = None
        for _ in range(ATTEMPTS):
            try:
                return self._once(lane, system, history, user, max_tokens, temperature)
            except Exception as e:                      # timeout/429/5xx/bad json…
                last = e
        raise last if last else RuntimeError("unreachable")

    def _once(self, lane: Lane, system, history, user, max_tokens, temperature) -> str:
        messages = ([{"role": "system", "content": system}]
                    + list(history or []) + [{"role": "user", "content": user}])
        payload = {"model": lane.model, "messages": messages,
                   "max_tokens": max_tokens, "temperature": temperature}
        payload.update(lane.extra)
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.base + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://opensourceorchestra.org",
                     # ASCII only: urllib encodes headers latin-1, an ʻokina
                     # here kills EVERY request (found by test_ladder.py; the
                     # same bug sits in the bridge's llm.py X-Title)
                     "X-Title": "the Ohana Bot totem"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read())
        # OpenRouter sometimes 200s with {"error": {...}} (e.g. rate-limited free lane)
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"api error: {str(data['error'])[:80]}")
        choice = data["choices"][0]
        text = (choice["message"]["content"] or "").strip()
        if not text:
            raise ValueError("empty completion")
        # finish_reason "length" = cut mid-sentence (reasoning burned the
        # budget, or a runaway). Never vocalize a half-thought — fail the lane.
        if choice.get("finish_reason") == "length":
            raise ValueError("truncated completion (finish_reason=length)")
        return text


if __name__ == "__main__":
    L = Ladder()
    print("enabled:", L.enabled, "| mode:", L.mode())
    print(json.dumps(L.state(), indent=1))
