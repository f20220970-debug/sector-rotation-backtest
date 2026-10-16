import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config as C
import metrics as M


def _save(fig, name):
    C.CHARTS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(C.CHARTS / name, dpi=120); plt.close(fig)


def wealth(series):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for name, r in series.items():
        ax.plot(M.wealth(r), label=name, lw=1.4 if name != "SPY" else 2)
    ax.set_yscale("log"); ax.set_ylabel("Growth of $1 (log scale)"); ax.legend()
    ax.set_title("Cumulative performance after trading costs")
    _save(fig, "wealth.png")


def drawdowns(series):
    fig, ax = plt.subplots(figsize=(11, 3.8))
    for name, r in series.items():
        ax.plot(100 * M.drawdown_series(r), label=name, lw=1)
    ax.set_ylabel("Drawdown (%)"); ax.legend(ncol=5, fontsize=8); ax.set_title("Drawdowns: fall from previous peak")
    _save(fig, "drawdowns.png")


def cost_sensitivity(tbl):
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for strat, g in tbl.groupby("strategy"):
        ax.plot(g["cost_bps"], g["sharpe"], marker="o", label=strat)
    ax.set_xlabel("Trading cost (basis points per unit turnover)"); ax.set_ylabel("Sharpe ratio"); ax.legend()
    ax.set_title("How trading costs erode each strategy")
    _save(fig, "cost_sensitivity.png")
