import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import data  # noqa: E402
from agents import _parse_json  # noqa: E402


def _fake_prices(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    close = 2000 + np.cumsum(rng.normal(0, 5, n))
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 3,
            "Low": close - 3,
            "Close": close,
            "Volume": 1000,
        },
        index=pd.date_range("2026-01-01", periods=n, freq="D"),
    )


def test_rsi_is_bounded():
    rsi = data.rsi(_fake_prices()["Close"]).dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()


def test_indicators_columns_and_atr_positive():
    out = data.add_indicators(_fake_prices())
    for col in ("sma20", "sma50", "macd", "macd_signal", "rsi14", "atr14", "bb_upper", "bb_lower"):
        assert col in out.columns
    assert (out["atr14"].dropna() > 0).all()
    last = out.iloc[-1]
    assert last["bb_lower"] < last["sma20"] < last["bb_upper"]


def test_parse_json_extracts_object():
    assert _parse_json('Here: {"action": "BUY", "confidence": 0.7}')["action"] == "BUY"


def test_parse_json_falls_back_to_hold():
    assert _parse_json("no json here")["action"] == "HOLD"
