# TradingAgents-Lite

A small multi-agent LLM trading-desk framework, inspired by the TradingAgents project.
Specialist agents analyse a market, a bull and a bear debate it, a trader proposes a plan,
a risk team challenges it, and a portfolio manager issues the final decision.

Default instrument is gold (`XAUUSD`, mapped to `GC=F` on Yahoo Finance), but any
Yahoo Finance ticker works (`BTC-USD`, `AAPL`, `EURUSD=X`, ...).

> **Research and paper-trading only. Not financial advice.** LLM output can be wrong.
> Never connect this to a live account without your own testing and risk controls.

## How it works

```
Technical analyst ─┐
Macro analyst ─────┼─> Bull vs Bear debate ─> Research manager ─> Trader
Sentiment analyst ─┘                                                 │
                                                                     v
                              Portfolio manager <─ Risk team (aggressive / neutral / conservative)
                                       │
                                       v
                          JSON decision + Markdown report
```

| File | Purpose |
|---|---|
| `main.py` | Command-line entry point |
| `config.py` | Settings (model, symbol map, debate rounds) |
| `llm.py` | Thin wrapper around the Anthropic API |
| `data.py` | Prices, indicators, macro and news snapshots |
| `agents.py` | All agents and the decision pipeline |
| `tests/test_data.py` | Offline tests for the indicator maths |

## Setup

```bash
git clone <your-repo-url>
cd tradingagents-lite
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
```

## Usage

```bash
python main.py                       # XAUUSD, 1 debate round
python main.py --symbol BTC-USD --rounds 2
python main.py --symbol XAUUSD --interval 1h --days 30
```

Each run prints the decision and saves a full report to `reports/`.

Example decision:

```json
{
  "action": "HOLD",
  "confidence": 0.55,
  "entry": null,
  "stop_loss": null,
  "take_profit": null,
  "rationale": "Mixed signals; wait for a break of the 20-day range."
}
```

## Configuration

Set in `.env` or the environment:

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your API key |
| `TA_MODEL` | `claude-sonnet-5-5` | Model used by every agent |
| `TA_DEBATE_ROUNDS` | `1` | Bull/bear rounds |

## Tests

```bash
pip install pytest
pytest
```

## Extending

- Add an analyst: write a prompt in `agents.py` and add it to `run_analysts`.
- Add a data source: add a function in `data.py` that returns a text snapshot.
- Execution (e.g. MetaTrader 5) is intentionally not included. Feed the JSON decision to
  your own paper-trading layer.

## License

MIT
