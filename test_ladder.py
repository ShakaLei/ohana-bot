#!/usr/bin/env python3
"""
test_ladder.py — prove the 3-layer brain ladder WITHOUT a real key or network.

Stands up a mock OpenAI-compatible endpoint on 127.0.0.1 and scripts its
behavior per model. Proves:
  1. free lane success          -> free answers, one call
  2. free 429                   -> paid answers (failover), free struck once
  3. free bad-json              -> paid answers
  4. free + paid both 500       -> LadderExhausted (caller falls to MOCK)
  5. 3 strikes                  -> free benched; next request skips it entirely
  6. timeout on free            -> paid answers (1s timeout, 2s stall)
  7. NO KEY                     -> no socket is ever opened (call counter = 0)
  8. mode strings               -> "mock" / "free:…" / "paid:…", badge-sized

The key used here is a plain fake ("test-key-not-real") — never a real-looking
sk-or token. Nothing here talks to openrouter.ai.

    python3 test_ladder.py        # exit 0 = all green
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import ladder

FAKE_KEY = "test-key-not-real"

# ------------------------------------------------------------ the mock server
CALLS = []          # model names, in arrival order
BODIES = []         # full request bodies, in arrival order
SCRIPT = {}         # model -> list of behaviors, popped per call; empty = ok
LOCK = threading.Lock()


def _behavior(model, body=None):
    with LOCK:
        CALLS.append(model)
        BODIES.append(body or {})
        q = SCRIPT.get(model)
        return q.pop(0) if q else ("ok", None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # silence
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass    # the stall test's client times out mid-write — expected

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        kind, arg = _behavior(body.get("model", "?"), body)
        if kind == "status":
            self.send_response(arg)
            self.end_headers()
            self.wfile.write(b'{"error":"scripted failure"}')
            return
        if kind == "badjson":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html>not json at all")
            return
        if kind == "stall":
            time.sleep(arg)
        # ok (kind "truncated" = 200 with finish_reason length, mid-word cut)
        reply = {"choices": [{"finish_reason": "length" if kind == "truncated" else "stop",
                              "message": {"content": "half a thou" if kind == "truncated"
                                          else f"echo({body['model']}): "
                                          + body["messages"][-1]["content"]}}]}
        out = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)


def start_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


# ------------------------------------------------------------------ harness
PASS, FAIL = 0, 0


def chk(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  ✗ {name} — {detail}")


def fresh(base, timeout=5.0):
    with LOCK:
        CALLS.clear()
        BODIES.clear()
        SCRIPT.clear()
    return ladder.Ladder(key=FAKE_KEY, base=base,
                         model_free="fake/free-model:free",
                         model_paid="fake/paid-model", timeout=timeout)


def main():
    srv, base = start_server()
    S, H, U = "sys", [], "hello totem"

    # 1. free lane success
    L = fresh(base)
    text, lane = L.complete(S, H, U)
    chk("free lane answers", lane == "free" and "echo(fake/free-model:free)" in text,
        f"lane={lane}")
    chk("one call only", CALLS == ["fake/free-model:free"], str(CALLS))
    chk("mode is free:…", L.mode() == "free:free-model", L.mode())

    # 2. free 429 -> paid
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("status", 429), ("status", 429)]
    text, lane = L.complete(S, H, U)
    chk("429 on free -> paid answers", lane == "paid" and "paid-model" in text,
        f"lane={lane}")
    chk("free retried once then paid", CALLS == ["fake/free-model:free"] * 2 + ["fake/paid-model"],
        str(CALLS))
    chk("free struck once (per request)", L.free.strikes == 1, f"strikes={L.free.strikes}")

    # 3. invalid json on free -> paid
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("badjson", None), ("badjson", None)]
    text, lane = L.complete(S, H, U)
    chk("bad json on free -> paid answers", lane == "paid", f"lane={lane}")

    # 4. both lanes dead -> LadderExhausted (caller then answers from MOCK)
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("status", 500)] * 2
    SCRIPT["fake/paid-model"] = [("status", 500)] * 2
    try:
        L.complete(S, H, U)
        chk("both dead raises LadderExhausted", False, "no exception")
    except ladder.LadderExhausted as e:
        chk("both dead raises LadderExhausted", True, str(e)[:60])

    # 5. benching: 3 failed requests on free -> benched; request 4 skips it
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("status", 503)] * 6     # 3 requests × 2 attempts
    for _ in range(3):
        L.complete(S, H, U)                                     # paid catches each
    chk("free benched after 3 strikes", L.free.benched(),
        f"benched_s={L.free.state()['benched_s']}")
    chk("mode flips to paid:…", L.mode() == "paid:paid-model", L.mode())
    n_free = CALLS.count("fake/free-model:free")
    text, lane = L.complete(S, H, U)
    chk("benched lane is skipped", lane == "paid" and CALLS.count("fake/free-model:free") == n_free,
        f"free calls still {n_free}")
    # a paid success never un-benches free; the bench expires on its own clock
    chk("bench survives paid success", L.free.benched())

    # 6. timeout on free -> paid (1s timeout vs 2s stall)
    L = fresh(base, timeout=1.0)
    SCRIPT["fake/free-model:free"] = [("stall", 2.0), ("stall", 2.0)]
    t0 = time.time()
    text, lane = L.complete(S, H, U)
    dt = time.time() - t0
    chk("timeout on free -> paid answers", lane == "paid", f"lane={lane} in {dt:.1f}s")
    chk("timeout is bounded (<6s for 2×1s + paid)", dt < 6, f"{dt:.1f}s")

    # 7. NO KEY -> zero sockets, LadderExhausted immediately
    with LOCK:
        CALLS.clear()
        SCRIPT.clear()
    L = ladder.Ladder(key="", base=base)
    chk("no key -> disabled + mode mock", not L.enabled and L.mode() == "mock")
    try:
        L.complete(S, H, U)
        chk("no key raises (caller -> MOCK)", False, "no exception")
    except ladder.LadderExhausted:
        chk("no key raises (caller -> MOCK)", True)
    chk("no key -> ZERO network calls", CALLS == [], str(CALLS))

    # 9. reasoning contract: FREE lane sends effort low, PAID never does
    #    (minimax m3.1 = mandatory-reasoning: without it, thinking eats the
    #    whole max_tokens and the content is empty/cut — found live 2026-10-20)
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("status", 429)] * 2      # force paid too
    L.complete(S, H, U)
    free_bodies = [b for m, b in zip(CALLS, BODIES) if m.endswith(":free")]
    paid_bodies = [b for m, b in zip(CALLS, BODIES) if not m.endswith(":free")]
    chk("free lane sends reasoning effort low",
        all(b.get("reasoning") == {"effort": "low"} for b in free_bodies) and free_bodies,
        str(free_bodies[0].get("reasoning") if free_bodies else None))
    chk("paid lane sends NO reasoning param",
        all("reasoning" not in b for b in paid_bodies) and paid_bodies,
        f"{len(paid_bodies)} paid bodies clean")
    chk("default max_tokens leaves room for thinking (>=900)",
        all(b.get("max_tokens", 0) >= 900 for b in BODIES), str(BODIES[0].get("max_tokens")))

    # 10. finish_reason=length (mid-word cut) fails the lane -> paid answers
    L = fresh(base)
    SCRIPT["fake/free-model:free"] = [("truncated", None)] * 2
    text, lane = L.complete(S, H, U)
    chk("truncated free reply -> paid answers (never vocalize a half-thought)",
        lane == "paid" and "half a thou" not in text, f"lane={lane}")

    # 8. badge strings stay short
    chk("mode strings badge-sized",
        all(len(m) <= 34 for m in ("mock", f"free:{ladder._short(ladder.DEFAULT_FREE)}",
                                   f"paid:{ladder._short(ladder.DEFAULT_PAID)}")),
        f"free:{ladder._short(ladder.DEFAULT_FREE)} · paid:{ladder._short(ladder.DEFAULT_PAID)}")

    srv.shutdown()
    print(f"\nladder tests: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
