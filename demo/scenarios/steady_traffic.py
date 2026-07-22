"""Scenario: Steady baseline traffic (topic A queries)."""

from __future__ import annotations

import argparse
import random
import time
import urllib.request

QUERIES = [
    "what is opentelemetry?",
    "how does signoz export metrics?",
    "what port does OTLP use?",
    "explain token usage attributes",
    "how does quality drift detection work?",
]


def send_query(url: str, prompt: str) -> None:
    req = urllib.request.Request(
        url,
        data=f'{{"prompt": "{prompt}"}}'.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            resp.read()
    except Exception as e:
        print(f"Error sending query '{prompt}': {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send steady baseline query traffic")
    parser.add_argument("--url", default="http://localhost:8000/chat", help="RAG app URL")
    parser.add_argument("--rate", type=float, default=2.0, help="Queries per second")
    parser.add_argument("--count", type=int, default=50, help="Total queries to send")
    args = parser.parse_args()

    interval = 1.0 / args.rate if args.rate > 0 else 0.5
    print(f"Sending {args.count} steady baseline queries to {args.url}...")

    for i in range(args.count):
        q = random.choice(QUERIES)
        send_query(args.url, q)
        if (i + 1) % 10 == 0:
            print(f"Sent {i + 1}/{args.count} queries")
        time.sleep(interval)

    print("Steady traffic generation complete.")


if __name__ == "__main__":
    main()
