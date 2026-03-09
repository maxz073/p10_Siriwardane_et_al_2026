from pathlib import Path

import pandas as pd
import pytest

from plot_spreads import load_spreads, select_tenors


def test_load_spreads_sets_date_index_and_sorts(tmp_path: Path):
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
    df = pd.DataFrame(columns=["10Y", "2Y", "UNUSED"])
    assert select_tenors(df) == ["2Y", "10Y"]

    with pytest.raises(ValueError, match="No tenor columns found"):
        select_tenors(pd.DataFrame(columns=["UNUSED"]))
