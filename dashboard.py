#!/usr/bin/env python3
"""
Price History Dashboard — renders a terminal chart of tracked prices.
Run after you've accumulated a few data points.

Usage: python dashboard.py
"""

import json
from pathlib import Path

HISTORY_FILE = Path("price_history.json")


def load_history():
    if not HISTORY_FILE.exists():
        return []
    return json.loads(HISTORY_FILE.read_text())


def terminal_chart(history: list):
    """Draw a simple ASCII price chart in the terminal."""
    if not history:
        print("No data yet. Run tracker.py a few times first.")
        return

    prices = [h["best_price"] for h in history]
    dates = [h["checked_at"][:10] for h in history]
    lo, hi = min(prices), max(prices)
    spread = hi - lo if hi != lo else 1
    width = 40

    print(f"\n  {'─'*56}")
    print(f"  PVD → RDU  ·  Price Trend  ·  {len(history)} checks")
    print(f"  {'─'*56}\n")

    for i, (d, p) in enumerate(zip(dates, prices)):
        bar_len = int(((p - lo) / spread) * width) if spread > 0 else width // 2
        bar = "█" * max(bar_len, 1)

        # Highlight the lowest price
        marker = " ◀ LOW" if p == lo else ""
        print(f"  {d}  ${p:>7.2f}  {bar}{marker}")

    print()
    avg = sum(prices) / len(prices)
    print(f"  Low: ${lo:.2f}  ·  High: ${hi:.2f}  ·  Avg: ${avg:.2f}")

    # Trend arrow
    if len(prices) >= 2:
        diff = prices[-1] - prices[-2]
        arrow = "↓" if diff < 0 else "↑" if diff > 0 else "→"
        print(f"  Last change: {arrow} ${abs(diff):.2f}")

    print()


if __name__ == "__main__":
    terminal_chart(load_history())
