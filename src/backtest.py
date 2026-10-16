"""Monthly-rebalanced backtest with drifting weights and trading costs.

On the last trading day of each month the strategy sets new target weights using data up
to that day. The portfolio holds them from the next day; weights drift with prices during
the month. Turnover = sum of |new weight - drifted old weight|; cost = turnover × COST_BPS,
charged on the first day of the new holding period.
"""
import numpy as np
import pandas as pd

import config as C


def month_ends(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    s = pd.Series(index, index=index)
    return pd.DatetimeIndex(s.groupby(index.to_period("M")).max().values)


def run(px: pd.DataFrame, rule, cost_bps: float = C.COST_BPS, **kw) -> pd.DataFrame:
    assets = list(C.SECTORS)
    rets = px[assets].pct_change().fillna(0.0)
    dates = month_ends(px.index)[:-1]                       # last month end has no holding period yet
    out, w_prev, started = [], pd.Series(0.0, index=assets), False
    for i, d in enumerate(dates):
        target = rule(px, d, **kw).reindex(assets).fillna(0.0)
        if target.sum() == 0:
            continue
        nxt = dates[i + 1] if i + 1 < len(dates) else px.index[-1]
        period = rets.loc[(rets.index > d) & (rets.index <= nxt)]
        if period.empty:
            continue
        turnover = float((target - w_prev).abs().sum()) if started else float(target.sum())
        growth = (1 + period).cumprod()
        value = (growth * target).sum(axis=1)               # portfolio value path, start = 1
        daily = value / value.shift(1).fillna(1.0) - 1
        daily.iloc[0] -= turnover * cost_bps / 1e4
        out.append(pd.DataFrame({"ret": daily, "turnover": 0.0}))
        out[-1].iloc[0, 1] = turnover
        w_prev = (growth.iloc[-1] * target) / value.iloc[-1]   # drifted weights at period end
        started = True
    return pd.concat(out)


def buy_and_hold(px: pd.DataFrame, ticker: str, start) -> pd.DataFrame:
    r = px[ticker].pct_change().loc[lambda s: s.index >= start]
    return pd.DataFrame({"ret": r, "turnover": 0.0})
