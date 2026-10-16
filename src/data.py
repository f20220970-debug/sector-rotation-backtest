"""Download daily adjusted prices (dividends reinvested) from Yahoo Finance, once.

The CSV is saved to data/processed/prices.csv and committed, so later runs (and CI)
reuse it instead of downloading again. Delete it to refresh.
"""
import pandas as pd

import config as C


def download() -> pd.DataFrame:
    import yfinance as yf
    tickers = list(C.SECTORS) + [C.BENCHMARK, C.RISK_FREE]
    print(f"  downloading {len(tickers)} series from Yahoo Finance ...")
    raw = yf.download(tickers, start=C.START, auto_adjust=True, progress=False)["Close"]
    return raw[tickers].dropna(how="all")


def load() -> pd.DataFrame:
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    if C.PRICES.exists():
        px = pd.read_csv(C.PRICES, index_col=0, parse_dates=True)
        print(f"  using saved prices: {C.PRICES.name}")
    else:
        px = download()
        px.to_csv(C.PRICES)
    assets = list(C.SECTORS) + [C.BENCHMARK]
    missing = [t for t in assets if t not in px.columns or px[t].dropna().empty]
    if missing:
        raise SystemExit(f"Missing price data for {missing}; delete {C.PRICES} and retry")
    px = px.sort_index()
    px[C.RISK_FREE] = px[C.RISK_FREE].ffill()
    return px.dropna(subset=assets)
