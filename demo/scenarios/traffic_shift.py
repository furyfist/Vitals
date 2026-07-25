"""Scenario: Input shift traffic (topic B database queries)."""

from __future__ import annotations

import argparse
import random
import time
import urllib.request

QUERIES_TOPIC_B = [
    "what is write ahead logging?",
    "how do b-tree indices work?",
    "explain multiversion concurrency control",
    "what is dirty read in database isolation?",
    "how does deadlock detection resolve graph cycles?",
]


def send_query(url: str, prompt: str) -> None:
    req = urllib.request.Request(
        url,
        data=f'{{"query": "{prompt}"}}'.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            resp.read()
    except Exception as e:
        print(f"Error sending query '{prompt}': {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send topic B input shift traffic")
    parser.add_argument("--url", default="http://localhost:8002/ask", help="RAG app URL")
    parser.add_argument("--rate", type=float, default=2.0, help="Queries per second")
    parser.add_argument("--count", type=int, default=50, help="Total queries to send")
    args = parser.parse_args()

    interval = 1.0 / args.rate if args.rate > 0 else 0.5
    print(f"Sending {args.count} topic B input-shifted queries to {args.url}...")

    for i in range(args.count):
        q = random.choice(QUERIES_TOPIC_B)
        send_query(args.url, q)
        if (i + 1) % 10 == 0:
            print(f"Sent {i + 1}/{args.count} queries")
        time.sleep(interval)

    print("Traffic shift generation complete.")


if __name__ == "__main__":
    main()
