"""Run everything: prices -> strategies -> backtests -> risk metrics -> robustness -> report."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd  # noqa: E402

import backtest as B  # noqa: E402
import charts  # noqa: E402
import config as C  # noqa: E402
import data  # noqa: E402
import metrics as M  # noqa: E402
from strategies import STRATEGIES, momentum  # noqa: E402

MARK = "<!-- COMMENTARY -->"


def md(df):
    h = "| " + " | ".join(map(str, df.columns)) + " |"
    return "\n".join([h, "| " + " | ".join("---" for _ in df.columns) + " |"]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)])


def kept(path):
    d = "_Write 4-6 sentences in your own words: which strategy did best on a risk-adjusted basis, whether it beat the benchmark after costs, how robust it was, and what the risk numbers mean._"
    if path.exists():
        p = path.read_text(encoding="utf-8").split(MARK)
        if len(p) == 3:
            return p[1].strip()
    return d


def main():
    print("Data")
    px = data.load()
    rf = (px[C.RISK_FREE] / 100 / 252).fillna(0.0)
    print(f"  {len(px):,} trading days, {px.index[0]:%Y-%m-%d} to {px.index[-1]:%Y-%m-%d}")

    runs = {name: B.run(px, rule) for name, rule in STRATEGIES.items()}
    start = max(r.index[0] for r in runs.values())                    # common start for a fair comparison
    runs = {k: v.loc[start:] for k, v in runs.items()}
    runs["SPY"] = B.buy_and_hold(px, C.BENCHMARK, start)
    end = min(r.index[-1] for r in runs.values())
    runs = {k: v.loc[:end] for k, v in runs.items()}
    bench = runs["SPY"]["ret"]

    rows = []
    for name, df in runs.items():
        s = M.summary(df["ret"], rf, bench, df["turnover"])
        if name != "equal_weight":
            s["excess_vs_equal_wt"], s["t_stat_vs_equal_wt"] = M.excess_t_stat(df["ret"], runs["equal_weight"]["ret"])
        rows.append({"strategy": name, **s})
    perf = pd.DataFrame(rows)

    sub = []
    for label, a, b in C.SUBPERIODS:
        for name, df in runs.items():
            r = df["ret"].loc[a:b]
            if len(r) > 252:
                s = M.summary(r, rf, bench.loc[a:b])
                sub.append({"period": label, "strategy": name, "cagr": s["cagr"], "sharpe": s["sharpe"], "max_drawdown": s["max_drawdown"]})
    sub = pd.DataFrame(sub)

    cost = []
    for c in C.COST_GRID:
        for name in ["momentum", "low_volatility", "inverse_vol", "equal_weight"]:
            r = B.run(px, STRATEGIES[name], cost_bps=c)["ret"].loc[start:end]
            s = M.summary(r, rf, bench)
            cost.append({"strategy": name, "cost_bps": c, "cagr": s["cagr"], "sharpe": s["sharpe"]})
    cost = pd.DataFrame(cost)

    look = []
    for lb in C.LOOKBACK_GRID:
        r = B.run(px, momentum, lookback=lb)["ret"].loc[start:end]
        s = M.summary(r, rf, bench)
        look.append({"lookback_months": lb, "cagr": s["cagr"], "sharpe": s["sharpe"], "max_drawdown": s["max_drawdown"]})
    look = pd.DataFrame(look)

    C.OUTPUTS.mkdir(exist_ok=True)
    perf.round(4).to_csv(C.OUTPUTS / "performance.csv", index=False)
    sub.round(4).to_csv(C.OUTPUTS / "subperiods.csv", index=False)
    cost.round(4).to_csv(C.OUTPUTS / "cost_sensitivity.csv", index=False)
    look.round(4).to_csv(C.OUTPUTS / "momentum_lookbacks.csv", index=False)
    pd.DataFrame({k: v["ret"] for k, v in runs.items()}).to_csv(C.OUTPUTS / "daily_returns.csv")
    series = {k: v["ret"] for k, v in runs.items()}
    charts.wealth(series); charts.drawdowns(series); charts.cost_sensitivity(cost)

    P = perf.set_index("strategy")
    best = P.drop(index="SPY")["sharpe"].idxmax()
    pct = lambda x: f"{100 * x:.1f}%"
    facts = [f"Backtest {start:%Y-%m-%d} to {end:%Y-%m-%d} ({len(bench) / 252:.1f} years), monthly rebalance, {C.COST_BPS} bp trading cost per unit of turnover."]
    for name in ["SPY", "equal_weight", "momentum", "low_volatility", "inverse_vol"]:
        p = P.loc[name]
        facts.append(f"{name}: CAGR {pct(p['cagr'])}, volatility {pct(p['volatility'])}, Sharpe {p['sharpe']:.2f}, max drawdown {pct(p['max_drawdown'])}, beta {p['beta_vs_spy']:.2f}"
                     + (f", turnover {p['turnover_per_year']:.1f}x/yr" if name != "SPY" else ""))
    facts.append(f"Best risk-adjusted: {best}; vs equal weight its excess return is {pct(P.loc[best, 'excess_vs_equal_wt'])}/yr with t = {P.loc[best, 't_stat_vs_equal_wt']:.2f}.")
    facts.append(f"Daily 95% VaR / expected shortfall: SPY {pct(P.loc['SPY', 'var95_daily'])} / {pct(P.loc['SPY', 'es95_daily'])}, {best} {pct(P.loc[best, 'var95_daily'])} / {pct(P.loc[best, 'es95_daily'])}.")
    mc = cost[cost.strategy == "momentum"].set_index("cost_bps")["sharpe"]
    facts.append(f"Momentum Sharpe by cost: " + ", ".join(f"{c} bp → {v:.2f}" for c, v in mc.items())
                 + "; by lookback: " + ", ".join(f"{int(r.lookback_months)}m → {r.sharpe:.2f}" for r in look.itertuples()) + ".")

    out = C.REPORTS / "backtest_report.md"
    cols = ["strategy", "cagr", "volatility", "sharpe", "max_drawdown", "calmar", "beta_vs_spy", "alpha_annual",
            "info_ratio", "var95_daily", "es95_daily", "worst_month", "turnover_per_year"]
    text = "# Sector Rotation & Portfolio Risk Backtest\n\n## 1. Key findings\n" + "\n".join(f"- {f}" for f in facts) + f"""

### Analyst commentary
{MARK}
{kept(out)}
{MARK}

## 2. Performance and risk (after costs)
{md(perf[cols].round(3))}

![Wealth](../outputs/charts/wealth.png)
![Drawdowns](../outputs/charts/drawdowns.png)

## 3. Robustness
### Sub-periods
{md(sub.round(3))}

### Trading costs
{md(cost.round(3))}

![Cost sensitivity](../outputs/charts/cost_sensitivity.png)

### Momentum lookback
{md(look.round(3))}

## 4. Method notes
- Universe: nine SPDR sector ETFs (adjusted for dividends); benchmark SPY; risk-free rate from 13-week T-bill yields.
- Signals use only prices up to each month end; trades happen at that close and returns start the next day (tested in `tests/`).
- Weights drift with prices during the month; turnover = sum of absolute weight changes at rebalance; cost charged on turnover.
- Sharpe uses excess return over T-bills; VaR and expected shortfall are historical, daily, 95%; a normal-distribution VaR is reported for comparison.
- Limits: four strategies were compared, so the best result is partly selection; ETFs have short histories relative to market cycles; taxes and bid-ask spreads beyond the cost assumption are ignored.
"""
    out.write_text(text, encoding="utf-8")
    print("Analysis")
    for f in facts:
        print("  -", f)


if __name__ == "__main__":
    main()
