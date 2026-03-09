# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Project Tour: Treasury Spot-Futures Arbitrage Spreads
#
# **Summary**
#
# This notebook gives a brief tour of the cleaned data and the main analysis
# pipeline in this project. The end goal is to replicate the paper-style figure
# of arbitrage spreads over time for Treasury futures tenors.
#
# **Learning Outcomes**
#
# 1. Understand how cleaned input files are organized for futures, bonds,
#    implied repo, and spreads.
# 2. See how `pull_bloomberg.py` and `pull_CRSP.py` feed the analysis.
# 3. Understand how `calc_spread.py` transforms raw inputs into implied repo and
#    arbitrage spread outputs.
# 4. Recreate a core chart of arbitrage spreads over time by tenor.
#
# **Game Plan**
#
# 1. Load key parquet files.
# 2. Tour schemas and key columns.
# 3. Show selected code snippets from pull and analysis modules.
# 4. Plot and summarize arbitrage spreads.

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")

# %% [markdown]
# ## Step 1. Load Cleaned Inputs and Outputs
#
# The project commonly uses `_data/` (pipeline outputs) and `data_manual/`
# (versioned manual cache). This helper prefers `_data/` and falls back to
# `data_manual/`.

# %%
BASE_DIR = Path.cwd().resolve().parent if Path.cwd().name == "src" else Path.cwd().resolve()
DATA_DIR = BASE_DIR / "_data"
MANUAL_DIR = BASE_DIR / "data_manual"


def resolve_data_file(filename: str) -> Path:
    for folder in [DATA_DIR, MANUAL_DIR]:
        candidate = folder / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {filename} in {DATA_DIR} or {MANUAL_DIR}")


paths = {
    "bloomberg": resolve_data_file("bloomberg.parquet"),
    "tfz_irr": resolve_data_file("TFZ_IRR.parquet"),
    "implied_repo": resolve_data_file("implied_repo_first_deferred.parquet"),
    "arbitrage_spreads": resolve_data_file("arbitrage_spreads.parquet"),
}
paths

# %%
bbg = pd.read_parquet(paths["bloomberg"])
tfz = pd.read_parquet(paths["tfz_irr"])
implied_repo = pd.read_parquet(paths["implied_repo"])
spreads = pd.read_parquet(paths["arbitrage_spreads"])

if "Date" in implied_repo.columns:
    implied_repo = implied_repo.set_index("Date")
if "Date" in spreads.columns:
    spreads = spreads.set_index("Date")

implied_repo.index = pd.to_datetime(implied_repo.index)
spreads.index = pd.to_datetime(spreads.index)

print(f"Bloomberg shape: {bbg.shape}")
print(f"TFZ_IRR shape: {tfz.shape}")
print(f"Implied repo shape: {implied_repo.shape}")
print(f"Arbitrage spreads shape: {spreads.shape}")
print(f"Spread date range: {spreads.index.min().date()} to {spreads.index.max().date()}")

# %% [markdown]
# ## Step 2. Brief Tour of the Cleaned Data

# %%
# Bloomberg file is typically wide with MultiIndex columns: (ticker, field)
print(type(bbg.columns))
print("First 10 columns:")
print(list(bbg.columns[:10]))

if isinstance(bbg.columns, pd.MultiIndex):
    tickers = sorted(set(bbg.columns.get_level_values(0)))
    fields = sorted(set(bbg.columns.get_level_values(1)))
    print(f"Unique tickers: {len(tickers)}")
    print(f"Unique fields: {len(fields)}")

# %%
important_tfz_cols = [
    "tcusip",
    "caldt",
    "clean_price",
    "accrued_interest_begin",
    "coupon_rate",
    "coupon_frequency",
    "prev_coupon_date",
    "next_coupon_date",
]
existing_cols = [c for c in important_tfz_cols if c in tfz.columns]
tfz[existing_cols].head()

# %%
tenors = [c for c in ["2Y", "5Y", "10Y", "20Y", "30Y"] if c in spreads.columns]
spreads[tenors].describe().T

# %% [markdown]
# ## Step 3. How the Code Works (Selected Snippets)
#
# The analysis pipeline is:
#
# 1. `pull_bloomberg.py` builds futures + OIS panel data.
# 2. `pull_CRSP.py` builds bond-level inputs for implied repo math.
# 3. `calc_spread.py` computes implied repo and arbitrage spreads by tenor.

# %%
SRC_DIR = BASE_DIR / "src"


def snippet_around(path: Path, needle: str, before: int = 3, after: int = 18) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        if needle in line:
            lo = max(1, i - before)
            hi = min(len(lines), i + after)
            return "\n".join(f"{j:4d}: {lines[j-1]}" for j in range(lo, hi + 1))
    return f"Pattern {needle!r} not found in {path.name}."


print("=== pull_bloomberg.py / pull_bbg_data ===")
print(snippet_around(SRC_DIR / "pull_bloomberg.py", "def pull_bbg_data"))

print("\n=== pull_CRSP.py / pull_CRSP_treasury_for_irr ===")
print(snippet_around(SRC_DIR / "pull_CRSP.py", "def pull_CRSP_treasury_for_irr"))

print("\n=== calc_spread.py / calc_irr ===")
print(snippet_around(SRC_DIR / "calc_spread.py", "def calc_irr"))

print("\n=== calc_spread.py / calc_arbitrage_spread ===")
print(snippet_around(SRC_DIR / "calc_spread.py", "def calc_arbitrage_spread"))

# %% [markdown]
# ## Step 4. Replicate the Core Figure: Arbitrage Spreads Over Time

# %%
fig, ax = plt.subplots(figsize=(12, 6))
for tenor in tenors:
    series = spreads[tenor].dropna()
    if not series.empty:
        ax.plot(series.index, series.values, linewidth=1.2, label=tenor)

ax.axhline(0.0, color="black", linewidth=1.0, linestyle="--", alpha=0.8)
ax.set_title("Treasury Spot-Futures Arbitrage Spreads by Tenor")
ax.set_xlabel("Date")
ax.set_ylabel("Spread (bps)")
ax.legend(title="Tenor")
fig.tight_layout()
plt.show()

# %% [markdown]
# ## Step 5. Quick Consistency Checks

# %%
common_idx = implied_repo.index.intersection(spreads.index)
print(f"Common dates between implied repo and spreads: {len(common_idx):,}")

missing_share = spreads[tenors].isna().mean().sort_index()
pd.DataFrame({"missing_share": missing_share})

# %% [markdown]
# ## Wrap-Up
#
# This notebook maps cleaned inputs (`bloomberg.parquet`, `TFZ_IRR.parquet`)
# to final spread output (`arbitrage_spreads.parquet`) and is intended as a
# quick orientation for readers before they dive into the source modules.
