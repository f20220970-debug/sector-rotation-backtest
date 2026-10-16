"""Portfolio rules. Each function returns target weights on a rebalance date using ONLY
prices up to and including that date (no look-ahead).

  equal_weight   - 1/9 in every sector
  momentum       - top 3 sectors by return from 12 months ago to 1 month ago
  low_volatility - 3 sectors with the lowest daily volatility over ~6 months
  inverse_vol    - every sector, weighted by 1 / volatility (calmer sectors get more)
"""
import numpy as np
import pandas as pd

import config as C


def equal_weight(px: pd.DataFrame, date) -> pd.Series:
    n = len(C.SECTORS)
    return pd.Series(1 / n, index=list(C.SECTORS))


def momentum(px: pd.DataFrame, date, lookback: int = C.MOM_LOOKBACK, skip: int = C.MOM_SKIP) -> pd.Series:
    hist = px.loc[:date, list(C.SECTORS)]
    me = hist.groupby(hist.index.to_period("M")).tail(1)          # month-end prices
    if len(me) <= lookback:
        return pd.Series(dtype=float)
    ret = me.iloc[-1 - skip] / me.iloc[-1 - lookback] - 1
    top = ret.nlargest(C.TOP_N).index
    return pd.Series(1 / C.TOP_N, index=top)


def _vol(px, date):
    r = px.loc[:date, list(C.SECTORS)].pct_change().iloc[-C.VOL_LOOKBACK_DAYS:]
    return r.std() if len(r) >= C.VOL_LOOKBACK_DAYS else None


def low_volatility(px: pd.DataFrame, date) -> pd.Series:
    v = _vol(px, date)
    if v is None:
        return pd.Series(dtype=float)
    return pd.Series(1 / C.TOP_N, index=v.nsmallest(C.TOP_N).index)


def inverse_vol(px: pd.DataFrame, date) -> pd.Series:
    v = _vol(px, date)
    if v is None:
        return pd.Series(dtype=float)
    w = 1 / v
    return w / w.sum()


STRATEGIES = {"equal_weight": equal_weight, "momentum": momentum,
              "low_volatility": low_volatility, "inverse_vol": inverse_vol}
