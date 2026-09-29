"""
indicators.py
All calculations here are fully vectorized across the entire stock universe
at once using pandas — there is no per-stock Python loop for the maths.
Columns = stocks, rows = time. Every rolling/resample op below runs on every
column (stock) simultaneously.
"""

import pandas as pd

from config import SQUEEZE_LOOKBACK, SQUEEZE_PERCENTILE, BB_WINDOW, BB_STD


def to_monthly(fields: dict) -> dict:
    """Vectorized daily -> monthly resample, applied to every stock column at once."""
    return {
        "Open": fields["Open"].resample("ME").first(),
        "High": fields["High"].resample("ME").max(),
        "Low": fields["Low"].resample("ME").min(),
        "Close": fields["Close"].resample("ME").last(),
    }


def monthly_bollinger_bands(monthly_close: pd.DataFrame, window: int = BB_WINDOW, num_std: float = BB_STD):
    """Vectorized monthly Bollinger Bands for every stock column simultaneously."""
    mid = monthly_close.rolling(window).mean()
    std = monthly_close.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    width_pct = (upper - lower) / mid * 100
    return mid, upper, lower, width_pct


def _consecutive_true_streak(bool_df: pd.DataFrame) -> pd.DataFrame:
    """
    Length of the run of consecutive True values ending at each row, per column.
    Uses the standard cumsum-of-negation groupby trick. The only per-column
    loop here is over the ~500-900 tickers (via DataFrame.apply), not over
    rows/time — with a few hundred columns and a few dozen monthly rows this
    is effectively instant, and keeps the actual streak logic vectorized
    per-column via groupby/cumcount rather than a manual row-by-row scan.
    """
    def _streak(col: pd.Series) -> pd.Series:
        filled = col.fillna(False)
        reset_at = (~filled).cumsum()
        streak = filled.groupby(reset_at).cumcount() + 1
        return streak.where(filled, 0)

    return bool_df.apply(_streak, axis=0)


def detect_squeeze(width_pct: pd.DataFrame, lookback: int = SQUEEZE_LOOKBACK, percentile: float = SQUEEZE_PERCENTILE):
    """
    Flags months where the band is unusually tight ("consolidation") relative
    to its own trailing history — a rolling percentile computed per stock.
    """
    squeeze_cutoff = width_pct.rolling(lookback).quantile(percentile)
    in_squeeze = width_pct <= squeeze_cutoff
    squeeze_streak = _consecutive_true_streak(in_squeeze)
    return in_squeeze, squeeze_streak
