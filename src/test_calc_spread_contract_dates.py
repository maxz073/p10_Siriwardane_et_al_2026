import pandas as pd

from calc_spread import (
    _delivery_dates_from_contract_month,
    _first_weekday_of_month,
    _last_weekday_of_month,
    _parse_contract_month_yr,
)


def test_parse_contract_month_yr_valid_and_invalid_inputs():
    assert _parse_contract_month_yr("MAR 25") == (2025, 3)
    assert _parse_contract_month_yr('"jun 2030"') == (2030, 6)
    assert _parse_contract_month_yr("BAD 25") is None
    assert _parse_contract_month_yr(None) is None


def test_first_and_last_weekday_handles_weekend_boundaries():
    # 2025-11-01 is Saturday, so first weekday should be Monday 2025-11-03.
    assert _first_weekday_of_month(2025, 11) == pd.Timestamp("2025-11-03")
    # 2025-11-30 is Sunday, so last weekday should be Friday 2025-11-28.
    assert _last_weekday_of_month(2025, 11) == pd.Timestamp("2025-11-28")


def test_delivery_dates_from_contract_month_maps_to_expected_columns():
    raw = pd.DataFrame(
        {"current_contract_month_yr": ["MAR 25", "NOV 25", "BAD 25"]}
    )
    out = _delivery_dates_from_contract_month(raw)

    assert out.loc[0, "fut_dlv_dt_first"] == pd.Timestamp("2025-03-03")
    assert out.loc[0, "fut_dlv_dt_last"] == pd.Timestamp("2025-03-31")
    assert out.loc[1, "fut_dlv_dt_first"] == pd.Timestamp("2025-11-03")
    assert out.loc[1, "fut_dlv_dt_last"] == pd.Timestamp("2025-11-28")
    assert pd.isna(out.loc[2, "fut_dlv_dt_first"])
    assert pd.isna(out.loc[2, "fut_dlv_dt_last"])
