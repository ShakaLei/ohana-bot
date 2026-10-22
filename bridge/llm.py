#!/usr/bin/env python3
"""
llm.py — the fast-path brain call for the ʻOhana Bot.

OpenRouter-style chat completion. Any OpenAI-compatible endpoint works:
set env vars on the Pi (e.g. in /etc/ohana.env, loaded by the systemd unit):

    OHANA_LLM_BASE=https://openrouter.ai/api/v1
    OHANA_LLM_KEY=sk-or-...          # provision a LOW-LIMIT key for the demo
    OHANA_LLM_MODEL=anthropic/claude-haiku-4.5   # fast + cheap; swap freely

Latency notes (fast voice loop):
  * stream=True and feed tokens straight into audio_io.speak_stream()
  * personas+packs are ~3-9KB each — fine as a single system message
  * keep history short (router trims to 12 turns/face)
"""

from __future__ import annotations
import json
import os
import urllib.request

BASE = os.environ.get("OHANA_LLM_BASE", "https://openrouter.ai/api/v1")
KEY = os.environ.get("OHANA_LLM_KEY", "")
MODEL = os.environ.get("OHANA_LLM_MODEL", "anthropic/claude-haiku-4.5")


def _request(payload: dict) -> urllib.request.Request:
    return urllib.request.Request(
        BASE.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            # OpenRouter attribution headers (optional, polite):
            "HTTP-Referer": "https://opensourceorchestra.org",
            # ASCII only — urllib encodes headers latin-1; an ʻokina here
            # raises UnicodeEncodeError on EVERY request (found 2026-10-20 by
            # ohana-totem/test_ladder.py against a mock endpoint)
            "X-Title": "the Ohana Bot",
        },
    )


def chat(system: str, history: list[dict], user: str,
         max_tokens: int = 300, temperature: float = 0.8) -> str:
    """Blocking completion. Returns the reply text."""
    if not KEY:
        return ("(dev mode — no OHANA_LLM_KEY set) I heard you say: " + user)
    messages = ([{"role": "system", "content": system}]
                + history + [{"role": "user", "content": user}])
    body = {"model": MODEL, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature}
    with urllib.request.urlopen(_request(body), timeout=30) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"].strip()


def chat_stream(system: str, history: list[dict], user: str,
                max_tokens: int = 300, temperature: float = 0.8):
    """Generator of token strings (SSE). Feed directly into
    audio_io.speak_stream() for the <1.5s-to-first-word target."""
    if not KEY:
        yield "(dev mode — no key) "
        yield "You said: " + user
        return
    messages = ([{"role": "system", "content": system}]
                + history + [{"role": "user", "content": user}])
    body = {"model": MODEL, "messages": messages, "stream": True,
            "max_tokens": max_tokens, "temperature": temperature}
    with urllib.request.urlopen(_request(body), timeout=60) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                delta = json.loads(chunk)["choices"][0]["delta"]
                if "content" in delta and delta["content"]:
                    yield delta["content"]
            except (KeyError, json.JSONDecodeError, IndexError):
                continue
