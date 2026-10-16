import numpy as np
import pandas as pd

import backtest as B
import config as C
import metrics as M
from strategies import STRATEGIES, momentum


def fake_prices(days=900, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=days)
    cols = list(C.SECTORS) + [C.BENCHMARK]
    r = rng.normal(0.0003, 0.01, (days, len(cols))) + np.linspace(-0.0004, 0.0004, len(cols))
    px = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=idx, columns=cols)
    px[C.RISK_FREE] = 2.0
    return px


def test_metrics_known_values():
    r = pd.Series([0.1, -0.5, 0.2])
    assert abs(M.max_drawdown(r) - (-0.5)) < 1e-9
    assert abs(M.wealth(r).iloc[-1] - 1.1 * 0.5 * 1.2) < 1e-9


def test_weights_valid():
    px = fake_prices()
    d = px.index[-1]
    for name, rule in STRATEGIES.items():
        w = rule(px, d)
        assert abs(w.sum() - 1) < 1e-9 and (w >= 0).all(), name
    assert len(momentum(px, d)) == C.TOP_N


def test_no_lookahead():
    px = fake_prices()
    d = px.index[600]
    before = {n: rule(px, d) for n, rule in STRATEGIES.items()}
    shocked = px.copy()
    shocked.loc[shocked.index > d, list(C.SECTORS)] *= np.linspace(0.2, 5, len(C.SECTORS))   # change the future
    for n, rule in STRATEGIES.items():
        assert before[n].equals(rule(shocked, d)), n


def test_costs_reduce_returns():
    px = fake_prices()
    a = B.run(px, momentum, cost_bps=0)["ret"]
    b = B.run(px, momentum, cost_bps=50)["ret"]
    assert M.wealth(b).iloc[-1] < M.wealth(a).iloc[-1]


def test_equal_weight_matches_manual_first_month():
    px = fake_prices()
    res = B.run(px, STRATEGIES["equal_weight"], cost_bps=0)
    first = res.index[0]
    me = B.month_ends(px.index)
    nxt = me[me > first][0]
    period = px.loc[(px.index >= first) & (px.index <= nxt), list(C.SECTORS)]
    start_px = px.loc[px.index < first, list(C.SECTORS)].iloc[-1]
    manual = (period.iloc[-1] / start_px).mean() - 1
    got = (1 + res.loc[first:nxt, "ret"]).prod() - 1
    assert abs(manual - got) < 1e-9
