"""Market data: prices, indicators, macro context and news headlines."""
import numpy as np
import pandas as pd
import yfinance as yf

import config


def get_prices(ticker: str, days: int = 120, interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV data. Intraday intervals are limited by Yahoo (about 60 days)."""
    df = yf.download(
        ticker,
        period=f"{days}d",
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if df is None or df.empty:
        raise ValueError(f"No price data returned for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["Close"].shift()
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    c = out["Close"]
    out["sma20"] = c.rolling(20).mean()
    out["sma50"] = c.rolling(50).mean()
    out["ema12"] = c.ewm(span=12, adjust=False).mean()
    out["ema26"] = c.ewm(span=26, adjust=False).mean()
    out["macd"] = out["ema12"] - out["ema26"]
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["rsi14"] = rsi(c)
    out["atr14"] = atr(out)
    std20 = c.rolling(20).std()
    out["bb_upper"] = out["sma20"] + 2 * std20
    out["bb_lower"] = out["sma20"] - 2 * std20
    return out


def technical_snapshot(ticker: str, days: int = 120, interval: str = "1d") -> str:
    df = add_indicators(get_prices(ticker, days, interval))
    last = df.iloc[-1]
    recent = df.tail(20)
    lines = [
        f"Ticker: {ticker} | interval: {interval} | last bar: {df.index[-1]}",
        f"Close: {last['Close']:.2f} | High/Low (last 20 bars): "
        f"{recent['High'].max():.2f} / {recent['Low'].min():.2f}",
        f"SMA20: {last['sma20']:.2f} | SMA50: {last['sma50']:.2f}",
        f"MACD: {last['macd']:.3f} | Signal: {last['macd_signal']:.3f}",
        f"RSI14: {last['rsi14']:.1f} | ATR14: {last['atr14']:.2f}",
        f"Bollinger bands: {last['bb_lower']:.2f} - {last['bb_upper']:.2f}",
        "Last 5 closes: " + ", ".join(f"{x:.2f}" for x in df["Close"].tail(5)),
    ]
    return "\n".join(lines)


def macro_snapshot() -> str:
    lines = []
    for name, ticker in config.MACRO_TICKERS.items():
        try:
            df = get_prices(ticker, days=15)
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-6]) if len(df) > 5 else float(df["Close"].iloc[0])
            change = (last / prev - 1) * 100
            lines.append(f"{name}: {last:.2f} ({change:+.2f}% over 5 sessions)")
        except Exception as exc:  # network or ticker problems should not stop a run
            lines.append(f"{name}: unavailable ({exc})")
    return "\n".join(lines)


def news_snapshot(ticker: str, limit: int = 10) -> str:
    try:
        items = yf.Ticker(ticker).news or []
    except Exception as exc:
        return f"News unavailable ({exc})"
    titles = []
    for item in items[:limit]:
        title = item.get("title") or (item.get("content") or {}).get("title")
        if title:
            titles.append(f"- {title}")
    return "\n".join(titles) if titles else "No recent headlines found."
