"""
Create tidy input datasets for spread analysis.

This file is intentionally limited to cleaning/reshaping staged raw inputs.
No spread analysis is performed here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from calc_spread import (
    OIS_MONTH_TICKERS,
    TENOR_CONTRACTS,
    _col,
    _delivery_dates_from_contract_month,
)
from settings import config

DATA_DIR = Path(config("DATA_DIR"))

FUTURES_TIDY_PATH = DATA_DIR / "futures_inputs_tidy.parquet"
OIS_TIDY_PATH = DATA_DIR / "ois_inputs_tidy.parquet"
CRSP_TIDY_PATH = DATA_DIR / "crsp_inputs_tidy.parquet"


def _load_bloomberg_raw(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Bloomberg raw input not found: {path}")
    df = pd.read_parquet(path)
    if "Date" in df.columns and df.index.name != "Date":
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    df.index.name = "Date"
    return df


def tidy_futures_inputs(bbg_df: pd.DataFrame) -> pd.DataFrame:
    """Create tidy futures input rows used by implied repo calculations."""
    rows: list[pd.DataFrame] = []
    output_cols = [
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
    required_fields = [
        "px_last",
        "px_volume",
        "fut_ctd_cusip",
        "fut_cnvs_factor",
        "current_contract_month_yr",
    ]

    for tenor, ticker in TENOR_CONTRACTS.items():
        one = pd.DataFrame(index=bbg_df.index)
        one.index.name = "Date"
        for field in required_fields:
            s = _col(bbg_df, ticker, field)
            one[field] = s if s is not None else pd.NA
        if one["px_last"].isna().all() and one["px_volume"].isna().all():
            continue

        one = _delivery_dates_from_contract_month(one)
        one = one.reset_index()
        if "Date" not in one.columns and "index" in one.columns:
            one = one.rename(columns={"index": "Date"})
        one["Date"] = pd.to_datetime(one["Date"]).dt.normalize()
        one["tenor"] = tenor
        one["ticker"] = ticker
        one["px_last"] = pd.to_numeric(one["px_last"], errors="coerce")
        one["px_volume"] = pd.to_numeric(one["px_volume"], errors="coerce")
        one["fut_cnvs_factor"] = pd.to_numeric(one["fut_cnvs_factor"], errors="coerce")
        one["fut_ctd_cusip"] = (
            one["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')
        )
        one.loc[
            one["fut_ctd_cusip"].isin(["", "nan", "None", "NaN"]),
            "fut_ctd_cusip",
        ] = pd.NA

        rows.append(
            one[output_cols]
        )

    if not rows:
        return pd.DataFrame(columns=output_cols)
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["Date", "tenor"]).reset_index(drop=True)


def tidy_ois_inputs(bbg_df: pd.DataFrame) -> pd.DataFrame:
    """Create tidy OIS input rows used for interpolation."""
    rows: list[pd.DataFrame] = []
    for month, ticker in OIS_MONTH_TICKERS.items():
        s = _col(bbg_df, ticker, "px_last")
        if s is None:
            continue
        s = s.copy()
        s.index.name = "Date"
        one = s.rename("ois_rate_pct").to_frame().reset_index()
        if "Date" not in one.columns and "index" in one.columns:
            one = one.rename(columns={"index": "Date"})
        one["Date"] = pd.to_datetime(one["Date"]).dt.normalize()
        one["ois_month"] = month
        one["ticker"] = ticker
        one["ois_rate_pct"] = pd.to_numeric(one["ois_rate_pct"], errors="coerce")
        rows.append(one[["Date", "ois_month", "ticker", "ois_rate_pct"]])

    if not rows:
        return pd.DataFrame(columns=["Date", "ois_month", "ticker", "ois_rate_pct"])
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["Date", "ois_month"]).reset_index(drop=True)


def tidy_crsp_inputs(path: Path) -> pd.DataFrame:
    """Clean/normalize CRSP bond inputs used by implied repo calculations."""
    if not path.exists():
        raise FileNotFoundError(f"CRSP raw input not found: {path}")
    df = pd.read_parquet(path).copy()

    if "caldt" in df.columns:
        df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()
    for col in ["prev_coupon_date", "next_coupon_date", "tdatdt", "tmatdt"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    if "tcusip" in df.columns:
        df["tcusip"] = df["tcusip"].astype(str).str.strip().str.strip('"')
        df.loc[df["tcusip"].isin(["", "nan", "None", "NaN"]), "tcusip"] = pd.NA

    sort_cols = [col for col in ["tcusip", "caldt"] if col in df.columns]
    if sort_cols:
        return df.sort_values(sort_cols).reset_index(drop=True)
    return df.reset_index(drop=True)


def main():
    bloomberg_raw_path = DATA_DIR / "bloomberg.parquet"
    crsp_raw_path = DATA_DIR / "TFZ_IRR.parquet"

    bbg_raw = _load_bloomberg_raw(bloomberg_raw_path)
    futures_tidy = tidy_futures_inputs(bbg_raw)
    ois_tidy = tidy_ois_inputs(bbg_raw)
    crsp_tidy = tidy_crsp_inputs(crsp_raw_path)

    FUTURES_TIDY_PATH.parent.mkdir(parents=True, exist_ok=True)
    futures_tidy.to_parquet(FUTURES_TIDY_PATH, index=False)
    ois_tidy.to_parquet(OIS_TIDY_PATH, index=False)
    crsp_tidy.to_parquet(CRSP_TIDY_PATH, index=False)

    print(f"Wrote {FUTURES_TIDY_PATH}")
    print(f"Wrote {OIS_TIDY_PATH}")
    print(f"Wrote {CRSP_TIDY_PATH}")


if __name__ == "__main__":
    main()
