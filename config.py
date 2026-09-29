"""
Central configuration for the Nifty BB Consolidation-Breakout Screener.
Tweak these values to change screener behaviour without touching logic
elsewhere in the codebase.
"""

BB_WINDOW = 20              # months used for Bollinger Band SMA/STD (monthly candles)
BB_STD = 2                  # number of standard deviations for the bands

SQUEEZE_LOOKBACK = 24       # months of history used to rank "how tight" the band currently is
SQUEEZE_PERCENTILE = 0.20   # bottom 20% of band-width readings = "squeeze" (consolidation)
MIN_SQUEEZE_MONTHS = 2      # require at least this many consecutive squeeze months before a breakout counts

DAILY_HISTORY_PERIOD = "5y"  # daily history to download (must cover BB_WINDOW + SQUEEZE_LOOKBACK months)

INDEX_URLS = {
    "NIFTY500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "MIDCAP150": "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "SMALLCAP250": "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
}

NSE_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/csv,*/*",
}

CACHE_DIR = "cache"
