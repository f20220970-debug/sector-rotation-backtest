"""Performance and risk measures, all from daily returns (252 trading days a year)."""
import numpy as np
import pandas as pd
from scipy import stats

import config as C

DAYS = 252


def wealth(r: pd.Series) -> pd.Series:
    return (1 + r).cumprod()


def cagr(r: pd.Series) -> float:
    years = len(r) / DAYS
    return float(wealth(r).iloc[-1] ** (1 / years) - 1)


def max_drawdown(r: pd.Series) -> float:
    w = wealth(r)
    return float((w / w.cummax() - 1).min())


def drawdown_series(r: pd.Series) -> pd.Series:
    w = wealth(r)
    return w / w.cummax() - 1


def summary(r: pd.Series, rf: pd.Series, bench: pd.Series, turnover: pd.Series = None) -> dict:
    rf = rf.reindex(r.index).fillna(0.0)
    b = bench.reindex(r.index).fillna(0.0)
    ex = r - rf
    vol = float(r.std() * np.sqrt(DAYS))
    beta = float(np.cov(r, b)[0, 1] / np.var(b, ddof=1))
    alpha = float((ex.mean() - beta * (b - rf).mean()) * DAYS)
    te = float((r - b).std() * np.sqrt(DAYS))
    monthly = (1 + r).groupby(r.index.to_period("M")).prod() - 1
    q = 1 - C.VAR_LEVEL
    var_hist = float(-np.quantile(r, q))
    es = float(-r[r <= -var_hist].mean())
    var_param = float(-(r.mean() + stats.norm.ppf(q) * r.std()))
    years = len(r) / DAYS
    return {
        "cagr": cagr(r), "volatility": vol, "sharpe": float(ex.mean() / r.std() * np.sqrt(DAYS)),
        "max_drawdown": max_drawdown(r), "calmar": cagr(r) / abs(max_drawdown(r)),
        "beta_vs_spy": beta, "alpha_annual": alpha,
        "info_ratio": float((r - b).mean() * DAYS / te) if te > 0 else np.nan,
        "var95_daily": var_hist, "es95_daily": es, "var95_normal": var_param,
        "worst_month": float(monthly.min()), "pct_positive_months": float((monthly > 0).mean()),
        "turnover_per_year": float(turnover.sum() / years) if turnover is not None else 0.0,
    }


def excess_t_stat(r: pd.Series, base: pd.Series) -> tuple:
    """t-stat of the average monthly return difference versus a baseline strategy."""
    m = lambda x: (1 + x).groupby(x.index.to_period("M")).prod() - 1
    d = (m(r) - m(base.reindex(r.index).fillna(0))).dropna()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    return float(d.mean() * 12), float(t)
