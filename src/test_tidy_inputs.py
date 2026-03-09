import pandas as pd

from tidy_inputs import tidy_futures_inputs, tidy_ois_inputs


def test_tidy_futures_inputs_extracts_long_rows_for_available_tenors():
    idx = pd.to_datetime(["2025-01-02", "2025-01-03"])
    cols = pd.MultiIndex.from_tuples(
        [
            ("TU2 Comdty", "PX_LAST"),
            ("TU2 Comdty", "PX_VOLUME"),
            ("TU2 Comdty", "FUT_CTD_CUSIP"),
            ("TU2 Comdty", "FUT_CNVS_FACTOR"),
            ("TU2 Comdty", "CURRENT_CONTRACT_MONTH_YR"),
        ]
    )
    bbg_df = pd.DataFrame(
        [
            [111.0, 1000, "123456AB", 0.95, "MAR 25"],
            [112.0, 1200, "123456AB", 0.96, "APR 25"],
        ],
        index=idx,
        columns=cols,
    )

    out = tidy_futures_inputs(bbg_df)

    assert out["tenor"].unique().tolist() == ["2Y"]
    assert out["ticker"].unique().tolist() == ["TU2 Comdty"]
    assert out.shape[0] == 2
    assert out.loc[0, "fut_dlv_dt_first"] == pd.Timestamp("2025-03-03")
    assert out.loc[0, "fut_dlv_dt_last"] == pd.Timestamp("2025-03-31")


def test_tidy_ois_inputs_extracts_month_tagged_series():
    idx = pd.to_datetime(["2025-01-02", "2025-01-03"])
    cols = pd.MultiIndex.from_tuples(
        [
            ("USSOB CMPN Curncy", "PX_LAST"),
            ("USSOC CMPN Curncy", "PX_LAST"),
        ]
    )
    bbg_df = pd.DataFrame(
        [
            [4.10, 4.20],
            [4.11, 4.21],
        ],
        index=idx,
        columns=cols,
    )

    out = tidy_ois_inputs(bbg_df)

    assert set(out["ois_month"].unique().tolist()) == {2, 3}
    first_2m = out[(out["Date"] == pd.Timestamp("2025-01-02")) & (out["ois_month"] == 2)]
    assert first_2m["ois_rate_pct"].iloc[0] == 4.10


def test_tidy_futures_inputs_returns_empty_when_no_supported_contracts():
    idx = pd.to_datetime(["2025-01-02"])
    cols = pd.MultiIndex.from_tuples([("UNRELATED TICKER", "PX_LAST")])
    bbg_df = pd.DataFrame([[100.0]], index=idx, columns=cols)

    out = tidy_futures_inputs(bbg_df)

    assert out.empty
    assert out.columns.tolist() == [
        "Date",
        "tenor",
        "ticker",
        "px_last",
        "px_volume",
        "fut_ctd_cusip",
        "fut_cnvs_factor",
        "current_contract_month_yr",
        "fut_dlv_dt_first",
        "fut_dlv_dt_last",
    ]
