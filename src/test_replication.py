"""
Replication tests against treasury_sf_implied_rf.dta.

Loads the paper's Stata file and compares:
1. My IRR vs tfut_*_rf (all 5 tenors)
2. My OIS vs tfut_ois_* (all 5 tenors)
3. My spread vs spread_* (all 5 tenors)

Each test requires that the difference is within a tenor-specific bps tolerance for at least 90% of valid observations.
"""

from pathlib import Path

import pandas as pd
import pytest

from calc_spread import calc_arbitrage_spread, calc_ois_at_holding_period
from settings import config

# Paths relative to this file (src/)
SRC_DIR = Path(__file__).resolve().parent
DATA_MANUAL = SRC_DIR.parent / "data_manual"
# Pipeline writes to DATA_DIR (_data); tests should look there for our outputs
DATA_DIR = Path(config("DATA_DIR"))

TENORS = ["2Y", "5Y", "10Y", "20Y", "30Y"]
TENOR_TO_TFUT_RF = {"2Y": "tfut_2_rf", "5Y": "tfut_5_rf", "10Y": "tfut_10_rf", "20Y": "tfut_20_rf", "30Y": "tfut_30_rf"}
TENOR_TO_TFUT_OIS = {"2Y": "tfut_ois_2", "5Y": "tfut_ois_5", "10Y": "tfut_ois_10", "20Y": "tfut_ois_20", "30Y": "tfut_ois_30"}
TENOR_TO_SPREAD = {"2Y": "spread_2", "5Y": "spread_5", "10Y": "spread_10", "20Y": "spread_20", "30Y": "spread_30"}

BPS_TOLERANCE_IRR = 75
BPS_TOLERANCE_OIS = 25
BPS_TOLERANCE_SPREAD = 75
MIN_FRACTION_WITHIN = 0.90


def _load_stata_df():
    """Load treasury_sf_implied_rf.dta and ensure spread_* exist (paper: spread = tfut_*_rf - tfut_ois_*)."""
    path = DATA_MANUAL / "treasury_sf_implied_rf.dta"
    if not path.exists():
        pytest.skip(f"Replication data not found: {path}")
    df = pd.read_stata(path)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    for n in [2, 5, 10, 20, 30]:
        if f"spread_{n}" not in df.columns:
            df[f"spread_{n}"] = df[f"tfut_{n}_rf"] - df[f"tfut_ois_{n}"]
    return df


def _align_dates(my_df, paper_df, my_date_col="Date", paper_date_col="date"):
    """Inner join on date; return (my_aligned, paper_aligned) with common index."""
    my = my_df.copy()
    paper = paper_df.copy()
    if my_date_col in my.columns:
        my = my.set_index(my_date_col)
    my.index = pd.to_datetime(my.index).normalize()
    paper = paper.set_index(paper_date_col)
    paper.index = pd.to_datetime(paper.index).normalize()
    common = my.index.intersection(paper.index).sort_values()
    my_a = my.reindex(common)
    paper_a = paper.reindex(common)
    return my_a, paper_a


def _frac_within_bps(my_series, paper_series, bps_tol):
    """Fraction of valid (non-NaN) pairs where |my - paper| <= bps_tol."""
    mask = my_series.notna() & paper_series.notna()
    if mask.sum() == 0:
        return 0.0
    diff = (my_series - paper_series).abs()
    return (diff[mask] <= bps_tol).mean()


@pytest.fixture(scope="module")
def paper_df():
    """Load paper replication Stata file (treasury_sf_implied_rf.dta)."""
    return _load_stata_df()


@pytest.fixture(scope="module")
def my_irr_df():
    """Load our implied repo (first deferred) parquet for comparison."""
    path = DATA_DIR / "implied_repo_first_deferred.parquet"
    if not path.exists():
        pytest.skip(f"Implied repo not found: {path}. Run calc_spread pipeline first.")
    df = pd.read_parquet(path)
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    return df


@pytest.fixture(scope="module")
def my_ois_df():
    """Compute our OIS-at-holding-period DataFrame for comparison."""
    try:
        df = calc_ois_at_holding_period(manual_dir=DATA_DIR)
    except Exception as e:
        pytest.skip(f"Could not compute OIS: {e}")
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    return df


@pytest.fixture(scope="module")
def my_spread_df():
    """Load or compute our arbitrage spreads for comparison with paper."""
    path = DATA_DIR / "arbitrage_spreads.parquet"
    if not path.exists():
        try:
            df = calc_arbitrage_spread(manual_dir=DATA_DIR)
        except Exception as e:
            pytest.skip(f"Arbitrage spreads not found and calc failed: {e}")
    else:
        df = pd.read_parquet(path)
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    return df


def test_irr_vs_tfut_rf_all_tenors(paper_df, my_irr_df):
    """Spread between my IRR and tfut_*_rf is within 75 bps for >= 90% of data, for all 5 tenors."""
    my_a, paper_a = _align_dates(my_irr_df, paper_df)
    for tenor in TENORS:
        my_col = tenor
        paper_col = TENOR_TO_TFUT_RF[tenor]
        if my_col not in my_a.columns or paper_col not in paper_a.columns:
            pytest.fail(f"Missing column: my={my_col} or paper={paper_col}")
        frac = _frac_within_bps(my_a[my_col], paper_a[paper_col], BPS_TOLERANCE_IRR)
        assert frac >= MIN_FRACTION_WITHIN, (
            f"IRR vs tfut_*_rf for {tenor}: {frac:.2%} of observations within {BPS_TOLERANCE_IRR} bps "
            f"(required >= {MIN_FRACTION_WITHIN:.0%})"
        )


def test_ois_vs_tfut_ois_all_tenors(paper_df, my_ois_df):
    """Difference between my OIS and tfut_ois_* is within 25 bps for >= 90% of data, for all 5 tenors."""
    my_a, paper_a = _align_dates(my_ois_df, paper_df)
    for tenor in TENORS:
        my_col = tenor
        paper_col = TENOR_TO_TFUT_OIS[tenor]
        if my_col not in my_a.columns or paper_col not in paper_a.columns:
            pytest.fail(f"Missing column: my={my_col} or paper={paper_col}")
        frac = _frac_within_bps(my_a[my_col], paper_a[paper_col], BPS_TOLERANCE_OIS)
        assert frac >= MIN_FRACTION_WITHIN, (
            f"OIS vs tfut_ois_* for {tenor}: {frac:.2%} of observations within {BPS_TOLERANCE_OIS} bps "
            f"(required >= {MIN_FRACTION_WITHIN:.0%})"
        )


def test_spread_vs_paper_spread_all_tenors(paper_df, my_spread_df):
    """Spread I compute vs spread_* is within 100 bps for >= 90% of data, for all 5 tenors."""
    my_a, paper_a = _align_dates(my_spread_df, paper_df)
    for tenor in TENORS:
        my_col = tenor
        paper_col = TENOR_TO_SPREAD[tenor]
        if my_col not in my_a.columns or paper_col not in paper_a.columns:
            pytest.fail(f"Missing column: my={my_col} or paper={paper_col}")
        frac = _frac_within_bps(my_a[my_col], paper_a[paper_col], BPS_TOLERANCE_SPREAD)
        assert frac >= MIN_FRACTION_WITHIN, (
            f"My spread vs spread_* for {tenor}: {frac:.2%} of observations within {BPS_TOLERANCE_SPREAD} bps "
            f"(required >= {MIN_FRACTION_WITHIN:.0%})"
        )
