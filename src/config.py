"""Settings for the sector rotation and portfolio risk backtest."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
CHARTS = OUTPUTS / "charts"
REPORTS = ROOT / "reports"
PRICES = PROCESSED / "prices.csv"        # daily adjusted closes, committed so CI needs no download

# The nine original SPDR sector ETFs (all trading since Dec 1998) and the S&P 500 benchmark
SECTORS = {"XLB": "Materials", "XLE": "Energy", "XLF": "Financials", "XLI": "Industrials", "XLK": "Technology",
           "XLP": "Consumer Staples", "XLU": "Utilities", "XLV": "Health Care", "XLY": "Consumer Discretionary"}
BENCHMARK = "SPY"
RISK_FREE = "^IRX"                       # 13-week US T-bill yield (annual %, quoted)
START = "1999-01-01"

TOP_N = 3                  # sectors held by momentum and low-volatility strategies
MOM_LOOKBACK = 12          # months of past return used for momentum ...
MOM_SKIP = 1               # ... skipping the most recent month (short-term reversal)
VOL_LOOKBACK_DAYS = 126    # ~6 months of daily returns for volatility
COST_BPS = 10              # trading cost per 1.0 of turnover, in basis points
COST_GRID = [0, 10, 25, 50]
LOOKBACK_GRID = [6, 9, 12]
VAR_LEVEL = 0.95
SUBPERIODS = [("1999-2009", "1999-01-01", "2009-12-31"), ("2010-2019", "2010-01-01", "2019-12-31"),
              ("2020-now", "2020-01-01", "2100-01-01")]
