"""Scenario 1 — the cost hook. Hammer the RAG app to simulate a runaway agent loop;
vitals.cost.velocity (USD/min) spikes and the token-velocity alert fires in minutes.

    python demo/scenarios/runaway_loop.py --rate 20 --duration 120

Every number is reproducible: a judge runs this and watches the Vitals dashboard.
"""

from __future__ import annotations

import argparse
import time
import urllib.parse
import urllib.request

QUERIES = [
    "what is opentelemetry?",
    "how does signoz store data?",
    "what port does otlp use?",
    "what are gen_ai semantic conventions?",
    "how do agent loops burn money?",
]


def _fire(base_url: str, query: str) -> None:
    url = f"{base_url}/ask?query={urllib.parse.quote(query)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        print(f"  request failed: {e}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--rate", type=int, default=20, help="requests per second")
    p.add_argument("--duration", type=int, default=120, help="seconds")
    args = p.parse_args()

    interval = 1.0 / max(args.rate, 1)
    end = time.time() + args.duration
    n = 0
    print(f"runaway loop: {args.rate} req/s for {args.duration}s -> {args.url}")
    while time.time() < end:
        _fire(args.url, QUERIES[n % len(QUERIES)])
        n += 1
        if n % args.rate == 0:
            print(f"  {n} requests fired ({int(end - time.time())}s left)")
        time.sleep(interval)
    print(f"done: {n} requests. Watch vitals.cost.velocity on the Vitals dashboard.")


if __name__ == "__main__":
    main()
