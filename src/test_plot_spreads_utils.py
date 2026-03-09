"""
Unit tests for plot_spreads utilities: load_spreads and select_tenors.

Checks date index handling, sorting, and tenor column selection/ordering.
"""

from pathlib import Path

import pandas as pd
import pytest

from plot_spreads import load_spreads, select_tenors


def test_load_spreads_sets_date_index_and_sorts(tmp_path: Path):
    """load_spreads sets Date as index and sorts by date."""
    df = pd.DataFrame(
        {
            "Date": ["2025-01-03", "2025-01-02"],
            "2Y": [1.0, 2.0],
            "5Y": [3.0, 4.0],
        }
    )
    path = tmp_path / "arbitrage_spreads.parquet"
    df.to_parquet(path)

    out = load_spreads(path)

    assert out.index.tolist() == [
        pd.Timestamp("2025-01-02"),
        pd.Timestamp("2025-01-03"),
    ]
    assert "Date" not in out.columns


def test_select_tenors_returns_stable_order_and_rejects_missing_tenors():
    """select_tenors returns TENOR_ORDER subset and raises when no tenor columns exist."""
    df = pd.DataFrame(columns=["10Y", "2Y", "UNUSED"])
    assert select_tenors(df) == ["2Y", "10Y"]

    with pytest.raises(ValueError, match="No tenor columns found"):
        select_tenors(pd.DataFrame(columns=["UNUSED"]))
