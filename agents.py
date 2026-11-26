"""The trading-desk agents and the pipeline that connects them."""
import json
import re
from datetime import date

import config
import data
from llm import ask

ANALYST_RULES = (
    "Use only the data provided; do not invent numbers. Be concise (max 180 words). "
    "End with a line: Stance: BULLISH, BEARISH or NEUTRAL."
)


def run_analysts(ticker: str, interval: str, days: int) -> dict:
    """Three specialist analysts, each looking at a different data slice."""
    tech_data = data.technical_snapshot(ticker, days, interval)
    macro_data = data.macro_snapshot()
    news_data = data.news_snapshot(ticker)

    return {
        "data": {"technical": tech_data, "macro": macro_data, "news": news_data},
        "technical": ask(
            f"You are a technical analyst on a trading desk. {ANALYST_RULES}",
            f"Analyse trend, momentum, volatility and key levels.\n\n{tech_data}",
        ),
        "macro": ask(
            f"You are a macro analyst on a trading desk. {ANALYST_RULES}",
            f"Assess how these cross-market moves affect {ticker}.\n\n{macro_data}",
        ),
        "sentiment": ask(
            f"You are a news and sentiment analyst on a trading desk. {ANALYST_RULES}",
            f"Judge the tone of these headlines for {ticker}.\n\n{news_data}",
        ),
    }


def _brief(reports: dict) -> str:
    return (
        f"TECHNICAL:\n{reports['technical']}\n\n"
        f"MACRO:\n{reports['macro']}\n\n"
        f"SENTIMENT:\n{reports['sentiment']}"
    )


def run_debate(ticker: str, reports: dict, rounds: int) -> dict:
    """Bull and bear argue; a research manager picks a side."""
    brief = _brief(reports)
    transcript = []
    last_bear = ""
    last_bull = ""

    for i in range(1, rounds + 1):
        bull = ask(
            "You are the bull researcher. Make the strongest evidence-based case to BUY. "
            "Rebut the bear's last point if there is one. Max 150 words.",
            f"Ticker: {ticker}\n\n{brief}\n\nBear's last argument:\n{last_bear or 'none yet'}",
        )
        last_bull = bull
        bear = ask(
            "You are the bear researcher. Make the strongest evidence-based case to SELL or "
            "stay out. Rebut the bull's last point. Max 150 words.",
            f"Ticker: {ticker}\n\n{brief}\n\nBull's last argument:\n{last_bull}",
        )
        last_bear = bear
        transcript.append(f"Round {i} - Bull:\n{bull}\n\nRound {i} - Bear:\n{bear}")

    debate_text = "\n\n".join(transcript)
    verdict = ask(
        "You are the research manager. Weigh the debate and the analyst reports. "
        "Say which side is more convincing and why, and list the 2 biggest risks. Max 150 words.",
        f"Ticker: {ticker}\n\n{brief}\n\nDEBATE:\n{debate_text}",
    )
    return {"transcript": debate_text, "verdict": verdict}


def run_trader(ticker: str, reports: dict, verdict: str) -> str:
    return ask(
        "You are the trader. Turn the research verdict into a concrete plan: direction "
        "(BUY, SELL or HOLD), entry zone, stop loss, take profit, and position-size idea as a "
        "percent of risk. Base levels on the ATR and levels in the data. Max 150 words.",
        f"Ticker: {ticker}\n\nTechnical data:\n{reports['data']['technical']}\n\n"
        f"Research verdict:\n{verdict}",
    )


def run_risk_team(ticker: str, plan: str) -> str:
    views = []
    for name, stance in (
        ("Aggressive", "favour taking the trade and a larger size"),
        ("Neutral", "weigh reward against risk evenly"),
        ("Conservative", "prioritise capital protection and smaller size"),
    ):
        views.append(
            f"{name} risk view:\n"
            + ask(
                f"You are the {name.lower()} risk analyst. You {stance}. "
                "Critique the trade plan in max 80 words.",
                f"Ticker: {ticker}\n\nTrade plan:\n{plan}",
                max_tokens=400,
            )
        )
    return "\n\n".join(views)


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {
        "action": "HOLD",
        "confidence": 0.0,
        "entry": None,
        "stop_loss": None,
        "take_profit": None,
        "rationale": "Could not parse the portfolio manager's reply; defaulting to HOLD.",
    }


def run_portfolio_manager(ticker: str, plan: str, risk: str) -> dict:
    reply = ask(
        "You are the portfolio manager and make the final call. Reply with ONLY a JSON object "
        'with keys: "action" (BUY, SELL or HOLD), "confidence" (0 to 1), "entry", '
        '"stop_loss", "take_profit" (numbers or null), "rationale" (one or two sentences). '
        "No other text.",
        f"Ticker: {ticker}\n\nTrader plan:\n{plan}\n\nRisk team:\n{risk}",
        max_tokens=500,
    )
    decision = _parse_json(reply)
    decision["action"] = str(decision.get("action", "HOLD")).upper()
    if decision["action"] not in {"BUY", "SELL", "HOLD"}:
        decision["action"] = "HOLD"
    return decision


def run_pipeline(symbol: str, interval: str = "1d", days: int = 120, rounds: int | None = None) -> dict:
    """Run the full desk and return all intermediate outputs plus the final decision."""
    ticker = config.resolve_symbol(symbol)
    rounds = config.DEBATE_ROUNDS if rounds is None else rounds

    reports = run_analysts(ticker, interval, days)
    debate = run_debate(ticker, reports, rounds)
    plan = run_trader(ticker, reports, debate["verdict"])
    risk = run_risk_team(ticker, plan)
    decision = run_portfolio_manager(ticker, plan, risk)

    return {
        "symbol": symbol,
        "ticker": ticker,
        "date": date.today().isoformat(),
        "reports": reports,
        "debate": debate,
        "plan": plan,
        "risk": risk,
        "decision": decision,
    }


def to_markdown(result: dict) -> str:
    r = result
    return (
        f"# {r['symbol']} ({r['ticker']}) - {r['date']}\n\n"
        f"## Final decision\n```json\n{json.dumps(r['decision'], indent=2)}\n```\n\n"
        f"## Technical analyst\n{r['reports']['technical']}\n\n"
        f"## Macro analyst\n{r['reports']['macro']}\n\n"
        f"## Sentiment analyst\n{r['reports']['sentiment']}\n\n"
        f"## Bull vs bear debate\n{r['debate']['transcript']}\n\n"
        f"## Research manager verdict\n{r['debate']['verdict']}\n\n"
        f"## Trader plan\n{r['plan']}\n\n"
        f"## Risk team\n{r['risk']}\n\n"
        "---\n*Research only. Not financial advice.*\n"
    )
