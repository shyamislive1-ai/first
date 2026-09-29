"""
data_fetch.py
Bulk, vectorized OHLC download for the whole stock universe in ONE call
(no per-stock loop) using yfinance's multi-ticker download.
"""

import pandas as pd
import yfinance as yf

from config import DAILY_HISTORY_PERIOD


def fetch_daily_ohlc(tickers: list) -> dict:
    """
    Downloads daily OHLC for ALL tickers in a single vectorized batch call.
    Returns a dict of wide DataFrames, one per OHLC field:
        {'Open': df, 'High': df, 'Low': df, 'Close': df}
    Each df has Date as index and one column per ticker.
    """
    raw = yf.download(
        tickers=tickers,
        period=DAILY_HISTORY_PERIOD,
        interval="1d",
        group_by="column",   # -> columns MultiIndex: (Field, Ticker)
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    if raw.empty:
        raise RuntimeError("yfinance returned no data — check tickers/network.")

    fields = {}
    for field in ("Open", "High", "Low", "Close"):
        if field in raw.columns.get_level_values(0):
            fields[field] = raw[field].copy()
        else:
            raise RuntimeError(f"Expected field '{field}' missing from download.")

    # Drop tickers that came back all-NaN (delisted / wrong symbol / no data)
    valid_cols = fields["Close"].dropna(axis=1, how="all").columns
    for field in fields:
        fields[field] = fields[field][valid_cols]

    return fields
