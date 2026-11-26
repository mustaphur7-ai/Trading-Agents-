"""Central settings. Values can be overridden with environment variables or a .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("TA_MODEL", "claude-sonnet-5-5")
DEBATE_ROUNDS = int(os.getenv("TA_DEBATE_ROUNDS", "1"))
DEFAULT_SYMBOL = "XAUUSD"

# Friendly names -> Yahoo Finance tickers
SYMBOL_MAP = {
    "XAUUSD": "GC=F",
    "GOLD": "GC=F",
    "XAGUSD": "SI=F",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "US100": "^NDX",
    "US500": "^GSPC",
}

# Context markets shown to the macro analyst
MACRO_TICKERS = {
    "US Dollar Index": "DX-Y.NYB",
    "US 10Y yield": "^TNX",
    "S&P 500": "^GSPC",
    "VIX": "^VIX",
}


def resolve_symbol(symbol: str) -> str:
    """Map a friendly symbol (e.g. XAUUSD) to a Yahoo Finance ticker."""
    return SYMBOL_MAP.get(symbol.upper(), symbol)
