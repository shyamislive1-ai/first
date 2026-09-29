"""
screener.py
Combines universe selection, data fetch, and vectorized indicator maths into
a single daily-runnable screener that flags Bollinger Band consolidation
breakouts on the MONTHLY timeframe, checked against TODAY's live price.

Run standalone:  python screener.py
"""

import pandas as pd

from config import MIN_SQUEEZE_MONTHS
from universe import get_universe
from data_fetch import fetch_daily_ohlc
from indicators import to_monthly, monthly_bollinger_bands, detect_squeeze


def run_screener(selected_indices: list, min_squeeze_months: int = MIN_SQUEEZE_MONTHS) -> pd.DataFrame:
    tickers = get_universe(selected_indices)
    daily = fetch_daily_ohlc(tickers)
    monthly = to_monthly(daily)

    mid, upper, lower, width_pct = monthly_bollinger_bands(monthly["Close"])
    in_squeeze, squeeze_streak = detect_squeeze(width_pct)

    # Most recent COMPLETED month's band values
    last_upper = upper.iloc[-1]
    last_lower = lower.iloc[-1]
    last_mid = mid.iloc[-1]
    last_width = width_pct.iloc[-1]

    # Squeeze streak as of the month BEFORE the latest completed one — i.e.
    # "was it already consolidating going into the month we're now checking"
    prior_streak = squeeze_streak.iloc[-2] if len(squeeze_streak) > 1 else squeeze_streak.iloc[-1] * 0

    latest_close = daily["Close"].ffill().iloc[-1]     # today's live/last traded price
    latest_date = daily["Close"].index[-1]

    breakout_up = (latest_close > last_upper) & (prior_streak >= min_squeeze_months)
    breakout_down = (latest_close < last_lower) & (prior_streak >= min_squeeze_months)

    result = pd.DataFrame({
        "Symbol": last_upper.index.str.replace(".NS", "", regex=False),
        "LTP": latest_close.values,
        "Monthly_Upper_BB": last_upper.values,
        "Monthly_Mid_BB": last_mid.values,
        "Monthly_Lower_BB": last_lower.values,
        "BB_Width_%": last_width.values,
        "Squeeze_Months_Prior": prior_streak.values,
        "Breakout": [
            "Bullish" if u else ("Bearish" if d else "-")
            for u, d in zip(breakout_up.values, breakout_down.values)
        ],
    })

    result = result.dropna(subset=["Monthly_Upper_BB"])  # not enough history yet
    result["As_Of"] = latest_date.strftime("%Y-%m-%d")
    return result.sort_values(
        ["Breakout", "Squeeze_Months_Prior"], ascending=[True, False]
    ).reset_index(drop=True)


if __name__ == "__main__":
    df = run_screener(["NIFTY500", "MIDCAP150", "SMALLCAP250"])
    breakouts = df[df["Breakout"] != "-"]
    print(f"\n{len(breakouts)} breakout(s) found out of {len(df)} stocks screened.\n")
    print(breakouts.to_string(index=False))
    df.to_csv("screener_output.csv", index=False)
    print("\nFull results saved to screener_output.csv")
