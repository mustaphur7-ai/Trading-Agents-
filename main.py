"""Command-line entry point.

Examples:
    python main.py
    python main.py --symbol BTC-USD --rounds 2
    python main.py --symbol XAUUSD --interval 1h --days 30
"""
import argparse
import json
import os

import config
from agents import run_pipeline, to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent LLM trading desk")
    parser.add_argument("--symbol", default=config.DEFAULT_SYMBOL, help="e.g. XAUUSD, BTC-USD, AAPL")
    parser.add_argument("--interval", default="1d", help="Yahoo interval: 1d, 1h, 15m ...")
    parser.add_argument("--days", type=int, default=120, help="History length in days")
    parser.add_argument("--rounds", type=int, default=None, help="Bull/bear debate rounds")
    parser.add_argument("--out", default="reports", help="Folder for saved reports")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")

    result = run_pipeline(args.symbol, args.interval, args.days, args.rounds)

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"{args.symbol}_{result['date']}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_markdown(result))

    print(json.dumps(result["decision"], indent=2))
    print(f"\nFull report saved to {path}")


if __name__ == "__main__":
    main()
