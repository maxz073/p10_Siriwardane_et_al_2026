import numpy as np
import pandas as pd

from calc_spread import _col, _extract_contract_series, _interpolate_ois_at_holding_period


def test_col_multiindex_lookup_is_case_insensitive_for_field():
    idx = pd.to_datetime(["2025-01-02", "2025-01-03"])
    cols = pd.MultiIndex.from_tuples(
        [
            ("TU2 Comdty", "PX_LAST"),
            ("TU2 Comdty", "px_volume"),
        ]
    )
    df = pd.DataFrame([[111.0, 1000], [112.0, 1200]], index=idx, columns=cols)

    px_last = _col(df, "TU2 Comdty", "px_last")
    px_volume = _col(df, "TU2 Comdty", "PX_VOLUME")

    assert list(px_last.values) == [111.0, 112.0]
    assert list(px_volume.values) == [1000, 1200]


def test_extract_contract_series_keeps_only_required_fields_for_ticker():
    idx = pd.to_datetime(["2025-01-02"])
    cols = pd.MultiIndex.from_tuples(
        [
            ("TU2 Comdty", "PX_LAST"),
            ("TU2 Comdty", "PX_VOLUME"),
            ("TU2 Comdty", "FUT_CTD_CUSIP"),
            ("TU2 Comdty", "FUT_CNVS_FACTOR"),
            ("TU2 Comdty", "CURRENT_CONTRACT_MONTH_YR"),
            ("TU2 Comdty", "UNUSED_FIELD"),
            ("OTHER TICKER", "PX_LAST"),
        ]
    )
    df = pd.DataFrame(
        [[111.0, 1000, "123456AB", 0.88, "MAR 25", 999, 77.0]],
        index=idx,
        columns=cols,
    )

    out = _extract_contract_series(df, "TU2 Comdty")

    assert out.columns.tolist() == [
        "px_last",
        "px_volume",
        "fut_ctd_cusip",
        "fut_cnvs_factor",
        "current_contract_month_yr",
    ]
    assert out.loc[idx[0], "px_last"] == 111.0
    assert out.loc[idx[0], "fut_ctd_cusip"] == "123456AB"


def test_interpolate_ois_clips_to_bounds_and_interpolates_interior():
    hold_months = np.array([1.0, 2.5, 7.0, 10.0])
    ois_curve = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 8.0])  # 2M,3M,4M,5M,6M,9M

    out = _interpolate_ois_at_holding_period(
        holding_period_months=hold_months,
        ois_rates_pct_row=ois_curve,
        tenors_months=[2, 3, 4, 5, 6, 9],
    )

    np.testing.assert_allclose(out, np.array([1.0, 1.5, 6.0, 8.0]))
