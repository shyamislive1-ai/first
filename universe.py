"""
universe.py
Fetches and caches the constituent lists for NIFTY 500, Nifty Midcap 150,
and Nifty Smallcap 250 directly from NSE's public index archives.

NSE blocks bare requests without a browser-like User-Agent and sometimes
without a prior "warm-up" hit to the homepage to pick up cookies. This
module handles both, and falls back to a locally cached CSV if NSE is
unreachable (e.g. no internet, NSE rate-limiting you).
"""

import os
import io
import requests
import pandas as pd

from config import INDEX_URLS, NSE_REQUEST_HEADERS, CACHE_DIR


def _get_nse_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(NSE_REQUEST_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except requests.RequestException:
        pass  # best-effort warm-up; continue regardless
    return session


def _cache_path(index_name: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{index_name}.csv")


def get_index_constituents(index_name: str, use_cache_on_failure: bool = True) -> pd.DataFrame:
    """
    Returns a DataFrame with a 'Symbol' column for the given index.
    index_name must be a key in config.INDEX_URLS.
    """
    if index_name not in INDEX_URLS:
        raise ValueError(f"Unknown index '{index_name}'. Choose from {list(INDEX_URLS)}")

    url = INDEX_URLS[index_name]
    session = _get_nse_session()
    cache_file = _cache_path(index_name)

    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df.to_csv(cache_file, index=False)  # refresh cache on success
        return df
    except Exception as exc:
        if use_cache_on_failure and os.path.exists(cache_file):
            print(f"[universe] Live fetch failed for {index_name} ({exc}); using cached copy.")
            return pd.read_csv(cache_file)
        raise RuntimeError(
            f"Could not fetch {index_name} constituents from NSE and no cache exists. "
            f"Download the CSV manually from {url} and save it to {cache_file}."
        ) from exc


def get_universe(selected_indices: list) -> list:
    """
    Combine one or more indices into a single de-duplicated list of
    Yahoo-Finance-ready tickers (NSE symbols suffixed with '.NS').
    """
    symbols = set()
    for idx in selected_indices:
        df = get_index_constituents(idx)
        col = "Symbol" if "Symbol" in df.columns else df.columns[0]
        symbols.update(df[col].astype(str).str.strip().tolist())
    return sorted(f"{s}.NS" for s in symbols if s and s.lower() != "nan")
