# Nifty Monthly Bollinger Band Consolidation-Breakout Screener

Screens **Nifty 500 + Nifty Midcap 150 + Nifty Smallcap 250** for stocks that
were consolidating tightly (Bollinger Band "squeeze") on the **monthly**
timeframe and have now broken out, checked using **today's live price** —
runnable once a day.

## How it works

1. **`universe.py`** pulls the live constituent CSVs straight from NSE's
   index archives (cached locally as a fallback).
2. **`data_fetch.py`** downloads daily OHLC for the *entire* universe in a
   single batched `yfinance` call — no per-stock loop.
3. **`indicators.py`** resamples daily → monthly and computes Bollinger
   Bands (default: 20-month SMA ± 2σ) for **all stocks simultaneously** as
   wide DataFrames (columns = stocks). This is the "vectorized" part: every
   rolling mean/std/percentile is one pandas call across every ticker.
4. It also flags **squeeze months** — months where the band width (as % of
   price) sits in the bottom 20% of that stock's own trailing 24-month
   history — and counts consecutive squeeze months per stock.
5. **`screener.py`** compares each stock's *current live price* against the
   *last completed month's* band. A "Bullish" breakout = price above the
   upper band **and** it had at least `MIN_SQUEEZE_MONTHS` of prior
   consolidation (filters out noise / random band touches). "Bearish" is
   the mirror case on the lower band.
6. **`app.py`** wraps all of this in a Streamlit dashboard so you don't
   have to touch code day-to-day.

## Setup

```bash
pip install -r requirements.txt
```

## Run it

**Dashboard (recommended):**
```bash
streamlit run app.py
```
Opens in your browser. Pick your universe, tweak BB window / squeeze
sensitivity in the sidebar, hit "Run Screener". Three tabs: confirmed
breakouts, stocks currently squeezing (your watchlist), and the full table.
Download results as CSV.

**Command line (for scheduling):**
```bash
python screener.py
```
Prints today's breakouts and saves the full table to `screener_output.csv`.

## Running it daily automatically

- **Windows**: Task Scheduler → daily trigger → run
  `python C:\path\to\screener.py` after market close (e.g. 4:00 PM IST).
- **Mac/Linux**: cron —
  `30 16 * * 1-5 cd /path/to/nifty_bb_screener && python3 screener.py`
- Point the CSV output at a Google Sheet / email step if you want it pushed
  to your phone instead of pulled.

## Tuning knobs (all in `config.py` or the sidebar)

| Setting | Default | What it does |
|---|---|---|
| `BB_WINDOW` | 20 months | SMA/STD lookback for the bands |
| `BB_STD` | 2 | Band width in standard deviations |
| `SQUEEZE_PERCENTILE` | 0.20 | How tight = "consolidating" (bottom 20% of width history) |
| `SQUEEZE_LOOKBACK` | 24 months | History used to judge what "tight" means for that stock |
| `MIN_SQUEEZE_MONTHS` | 2 | Minimum consecutive squeeze months before a breakout counts |

## Notes & caveats

- NSE's archive site sometimes rate-limits scripted requests — the code
  retries with browser-like headers and falls back to the last successful
  cache under `cache/`. If it ever fully fails, grab the CSV manually from
  the URLs in `config.py` and drop it in `cache/`.
- Yahoo Finance data for small/micro caps can have gaps or bad ticks;
  treat this as a first-pass filter, not gospel — sanity-check any signal
  before acting on it.
- This is a technical screening tool, not investment advice.
