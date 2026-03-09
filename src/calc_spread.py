"""
This module calculates the implied repo rate for Treasury futures and
the arbitrage spread between the implied repo rate and the OIS rate.

Data Inputs: data_manual/bloomberg.parquet, data_manual/TFZ_IRR.parquet.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from settings import config

MANUAL_DATA_DIR = config("MANUAL_DATA_DIR")
FUTURES_TIDY_FILE = "futures_inputs_tidy.parquet"
OIS_TIDY_FILE = "ois_inputs_tidy.parquet"
CRSP_TIDY_FILE = "crsp_inputs_tidy.parquet"

TENOR_CONTRACTS = {
    "2Y": "TU2 Comdty",
    "5Y": "FV2 Comdty",
    "10Y": "TY2 Comdty",
    "20Y": "WN2 Comdty",
    "30Y": "US2 Comdty",
}

# OIS by month tenor (2M–9M) for interpolation by holding period.
# Tickers must match those pulled in pull_bloomberg (OIS_MONTH_CONTRACTS).
OIS_MONTH_TENORS = [2, 3, 4, 5, 6, 9]  # months
OIS_MONTH_TICKERS = {
    2: "USSOB CMPN Curncy",
    3: "USSOC CMPN Curncy",
    4: "USSOD CMPN Curncy",
    5: "USSOE CMPN Curncy",
    6: "USSOF CMPN Curncy",
    9: "USSOI CMPN Curncy",
}

FIELDS_NEEDED = [
    "px_last", "px_volume", "fut_ctd_cusip", "fut_cnvs_factor",
    "current_contract_month_yr",
]

# Month abbreviation -> month number (for parsing "MAR 25" style)
_MONTH_ABBR = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _first_weekday_of_month(year: int, month: int) -> pd.Timestamp:
    """First weekday (business day) of the given month."""
    d = pd.Timestamp(year=year, month=month, day=1)
    if d.weekday() == 5:  # Saturday -> Monday
        d += pd.Timedelta(days=2)
    elif d.weekday() == 6:  # Sunday -> Monday
        d += pd.Timedelta(days=1)
    return d


def _last_weekday_of_month(year: int, month: int) -> pd.Timestamp:
    """Last weekday (business day) of the given month."""
    d = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    if d.weekday() == 5:  # Saturday -> Friday
        d -= pd.Timedelta(days=1)
    elif d.weekday() == 6:  # Sunday -> Friday
        d -= pd.Timedelta(days=2)
    return d


def _parse_contract_month_yr(s: str) -> tuple[int, int] | None:
    """Parse 'MAR 25' or 'JUN 25' -> (year, month). Returns None if invalid."""
    if pd.isna(s) or not isinstance(s, str):
        return None
    s = str(s).strip().strip('"').strip()
    parts = s.upper().split()
    if len(parts) != 2:
        return None
    abbr, yr = parts[0], parts[1]
    if abbr not in _MONTH_ABBR:
        return None
    try:
        y = int(yr)
        year = 2000 + y if y < 100 else y
        return (year, _MONTH_ABBR[abbr])
    except (ValueError, TypeError):
        return None


def _delivery_dates_from_contract_month(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Compute fut_dlv_dt_first (first weekday of contract month) and
    fut_dlv_dt_last (last weekday of contract month) from current_contract_month_yr.
    """
    raw = raw.copy()
    first_dates = []
    last_dates = []
    for val in raw["current_contract_month_yr"]:
        parsed = _parse_contract_month_yr(val)
        if parsed is None:
            first_dates.append(pd.NaT)
            last_dates.append(pd.NaT)
        else:
            year, month = parsed
            first_dates.append(_first_weekday_of_month(year, month))
            last_dates.append(_last_weekday_of_month(year, month))
    raw["fut_dlv_dt_first"] = first_dates
    raw["fut_dlv_dt_last"] = last_dates
    return raw


def _col(bbg_df: pd.DataFrame, ticker: str, field: str):
    if isinstance(bbg_df.columns, pd.MultiIndex):
        if (ticker, field) in bbg_df.columns:
            return bbg_df[(ticker, field)]
        for c in bbg_df.columns:
            if c[0] == ticker and c[1].lower() == field.lower():
                return bbg_df[c]
        return None
    for c in bbg_df.columns:
        if isinstance(c, str) and ticker in c and field in c:
            return bbg_df[c]
    return None


def _extract_contract_series(bbg_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    out = pd.DataFrame(index=bbg_df.index)
    out.index.name = "Date"
    for f in FIELDS_NEEDED:
        s = _col(bbg_df, ticker, f)
        if s is not None:
            out[f] = s
    return out


def _load_irr_bonds(manual_dir: Path) -> pd.DataFrame:
    tidy_path = manual_dir / CRSP_TIDY_FILE
    path = tidy_path if tidy_path.exists() else (manual_dir / "TFZ_IRR.parquet")
    if not path.exists():
        raise FileNotFoundError(
            f"CRSP input not found in {manual_dir}. Expected {CRSP_TIDY_FILE} or TFZ_IRR.parquet."
        )
    df = pd.read_parquet(path)
    if "caldt" in df.columns:
        df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()
    if "tcusip" in df.columns:
        df["tcusip"] = df["tcusip"].astype(str).str.strip().str.strip('"')
    return df


def _compute_ae_ic_d1_d2(merged: pd.DataFrame, delivery_col: str) -> pd.DataFrame:
    df = merged.copy()
    df[delivery_col] = pd.to_datetime(df[delivery_col])
    df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()
    freq = df.get("coupon_frequency", 2)
    df["coupon_cash_per_period"] = df["coupon_rate"] / freq

    next_cpn = pd.to_datetime(df["next_coupon_date"])
    prev_cpn = pd.to_datetime(df["prev_coupon_date"])
    delivery = df[delivery_col]
    last_cpn_before_delivery = prev_cpn.where(delivery < next_cpn, next_cpn)
    period_end = next_cpn.where(delivery < next_cpn, next_cpn + pd.DateOffset(months=6))
    period_days = (period_end - last_cpn_before_delivery).dt.days
    accrued_days_end = (delivery - last_cpn_before_delivery).dt.days
    df["Ae"] = df["coupon_cash_per_period"] * accrued_days_end / period_days.replace(0, 1)

    # Settlement: T+1 business day (carry starts on settlement, not trade date)
    settlement_date = df["caldt"] + pd.offsets.BDay(1)

    # Ab = accrued interest at settlement (not at caldt), so carry uses correct dirty price
    last_cpn_before_settlement = prev_cpn.where(settlement_date < next_cpn, next_cpn)
    period_end_settlement = next_cpn.where(
        settlement_date < next_cpn, next_cpn + pd.DateOffset(months=6)
    )
    period_days_settlement = (period_end_settlement - last_cpn_before_settlement).dt.days
    accrued_days_settlement = (settlement_date - last_cpn_before_settlement).dt.days
    df["Ab"] = (
        df["coupon_cash_per_period"]
        * accrued_days_settlement
        / period_days_settlement.replace(0, 1)
    )

    # Ex-coupon: coupon is included in price if caldt < ex_coupon_date <= delivery
    ex_coupon_date = next_cpn - pd.offsets.BDay(1)
    df["Ic"] = 0.0
    mask_cpn = (df["caldt"] < ex_coupon_date) & (next_cpn <= delivery)
    df.loc[mask_cpn, "Ic"] = df.loc[mask_cpn, "coupon_cash_per_period"]

    # d1 = holding period from settlement to delivery (Act/360)
    df["d1"] = (delivery - settlement_date).dt.days / 360.0
    df["d2"] = 0.0
    df.loc[mask_cpn, "d2"] = (df.loc[mask_cpn, delivery_col] - next_cpn.loc[mask_cpn]).dt.days / 360.0
    return df


def _irr_series(merged: pd.DataFrame, m: pd.DataFrame, P: pd.Series, Ab: pd.Series, F: pd.Series, CF: pd.Series) -> pd.Series:
    num = (F * CF) + m["Ae"] + m["Ic"] - (P + Ab)
    denom = (m["d1"] * (P + Ab)) - (m["Ic"] * m["d2"])
    valid = (denom > 0) & m["d1"].notna() & (m["d1"] > 0)
    out = pd.Series(index=merged.index, dtype=float)
    out.loc[valid] = num.loc[valid] * 10_000 / denom.loc[valid]
    return out


def load_bloomberg(manual_dir: Path) -> pd.DataFrame:
    path = manual_dir / "bloomberg.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Bloomberg data not found: {path}")
    df = pd.read_parquet(path)
    if "Date" in df.columns and df.index.name != "Date":
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    return df


def _load_tidy_futures_inputs(manual_dir: Path) -> pd.DataFrame:
    path = manual_dir / FUTURES_TIDY_FILE
    if not path.exists():
        raise FileNotFoundError(f"Tidy futures inputs not found: {path}")
    df = pd.read_parquet(path)
    if "Date" not in df.columns:
        raise ValueError(f"Tidy futures inputs missing required Date column: {path}")
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    return df


def _load_tidy_ois_inputs(manual_dir: Path) -> pd.DataFrame:
    path = manual_dir / OIS_TIDY_FILE
    if not path.exists():
        raise FileNotFoundError(f"Tidy OIS inputs not found: {path}")
    df = pd.read_parquet(path)
    if "Date" not in df.columns:
        raise ValueError(f"Tidy OIS inputs missing required Date column: {path}")
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    return df

def _delivery_candidate_dates(first_dlv: pd.Timestamp, last_dlv: pd.Timestamp, next_coupon_date) -> list:
    """
    Candidate delivery dates for max-IRR: first delivery, ex-coupon (1 BDay before coupon),
    coupon date, and last delivery. Only dates within [first_dlv, last_dlv] are returned.
    """
    first_dlv = pd.Timestamp(first_dlv).normalize()
    last_dlv = pd.Timestamp(last_dlv).normalize()
    candidates = [first_dlv, last_dlv]
    next_cpn = pd.to_datetime(next_coupon_date)
    if pd.notna(next_cpn):
        next_cpn = pd.Timestamp(next_cpn).normalize()
        ex_coupon = (next_cpn - pd.offsets.BDay(1)).normalize()
        for d in (ex_coupon, next_cpn):
            if first_dlv <= d <= last_dlv:
                candidates.append(d)
    # Unique, sorted for reproducibility
    seen = set()
    out = []
    for d in candidates:
        key = (d.year, d.month, d.day)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return sorted(out)


def _calc_implied_repo_per_tenor_from_tidy(
    futures_tidy_df: pd.DataFrame,
    irr_df: pd.DataFrame,
    tenor: str,
) -> pd.DataFrame:
    """IRR per date for one tenor, using pre-cleaned tidy futures inputs."""
    raw = futures_tidy_df[futures_tidy_df["tenor"] == tenor].copy()
    if raw.empty:
        return pd.DataFrame()

    raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()
    raw = raw[raw["px_volume"] > 0].copy()
    raw = raw.dropna(
        subset=[
            "px_last",
            "fut_cnvs_factor",
            "fut_ctd_cusip",
            "fut_dlv_dt_first",
            "fut_dlv_dt_last",
        ]
    )
    if raw.empty:
        return pd.DataFrame()

    irr = irr_df.copy()
    irr["tcusip"] = irr["tcusip"].astype(str).str.strip().str.strip('"')
    raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')

    merged = raw.merge(
        irr,
        left_on=["Date", "fut_ctd_cusip"],
        right_on=["caldt", "tcusip"],
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()

    out_rows = []
    last_printed_year = None

    for _, row in merged.iterrows():
        row_year = pd.Timestamp(row["Date"]).year
        if row_year != last_printed_year:
            print(f"Computing IRR for {tenor}: {row_year}")
            last_printed_year = row_year

        first_dlv = pd.to_datetime(row["fut_dlv_dt_first"])
        last_dlv = pd.to_datetime(row["fut_dlv_dt_last"])
        candidates = _delivery_candidate_dates(first_dlv, last_dlv, row.get("next_coupon_date"))

        best_irr = np.nan
        best_dlv = pd.NaT

        row_df = pd.DataFrame([row])
        P = row_df["clean_price"]
        F = row_df["px_last"]
        CF = row_df["fut_cnvs_factor"]

        for dlv in candidates:
            temp = row_df.copy()
            temp["candidate_delivery"] = dlv

            m = _compute_ae_ic_d1_d2(temp, "candidate_delivery")
            irr_val = _irr_series(temp, m, P, m["Ab"], F, CF).iloc[0]

            if pd.notna(irr_val) and (pd.isna(best_irr) or irr_val > best_irr):
                best_irr = irr_val
                best_dlv = dlv

        out_rows.append(
            {
                "Date": row["Date"],
                "tenor": tenor,
                "implied_repo_pct": best_irr,  # bps (pipeline expects this column name)
                "optimal_delivery_date": best_dlv,
                "holding_period_days": (
                    (best_dlv - (row["caldt"] + pd.offsets.BDay(1))).days
                    if pd.notna(best_dlv)
                    else np.nan
                ),
                "px_last": row["px_last"],
                "px_volume": row["px_volume"],
                "fut_ctd_cusip": row["fut_ctd_cusip"],
            }
        )

    return (
        pd.DataFrame(out_rows)
        .drop_duplicates(subset=["Date"])
        .set_index("Date")
        .sort_index()
    )


def calc_implied_repo_per_tenor(
    bbg_df: pd.DataFrame,
    irr_df: pd.DataFrame,
    tenor: str,
    ticker: str,
) -> pd.DataFrame:
    raw = _extract_contract_series(bbg_df, ticker)
    if raw.empty or "px_last" not in raw.columns:
        return pd.DataFrame()

    raw = _delivery_dates_from_contract_month(raw)
    raw = raw[raw["px_volume"] > 0].copy()
    raw = raw.dropna(
        subset=[
            "px_last", "fut_cnvs_factor", "fut_ctd_cusip",
            "fut_dlv_dt_first", "fut_dlv_dt_last"
        ]
    )
    if raw.empty:
        return pd.DataFrame()

    raw = raw.reset_index()
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()

    irr = irr_df.copy()
    irr["tcusip"] = irr["tcusip"].astype(str).str.strip().str.strip('"')
    raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')

    merged = raw.merge(
        irr,
        left_on=["Date", "fut_ctd_cusip"],
        right_on=["caldt", "tcusip"],
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()

    out_rows = []
    last_printed_year = None

    for _, row in merged.iterrows():
        row_year = pd.Timestamp(row["Date"]).year
        if row_year != last_printed_year:
            print(f"Computing IRR for {tenor}: {row_year}")
            last_printed_year = row_year

        first_dlv = pd.to_datetime(row["fut_dlv_dt_first"])
        last_dlv = pd.to_datetime(row["fut_dlv_dt_last"])
        candidates = _delivery_candidate_dates(first_dlv, last_dlv, row.get("next_coupon_date"))

        best_irr = np.nan
        best_dlv = pd.NaT

        row_df = pd.DataFrame([row])
        P = row_df["clean_price"]
        F = row_df["px_last"]
        CF = row_df["fut_cnvs_factor"]

        for dlv in candidates:
            temp = row_df.copy()
            temp["candidate_delivery"] = dlv

            m = _compute_ae_ic_d1_d2(temp, "candidate_delivery")
            irr_val = _irr_series(temp, m, P, m["Ab"], F, CF).iloc[0]

            if pd.notna(irr_val) and (pd.isna(best_irr) or irr_val > best_irr):
                best_irr = irr_val
                best_dlv = dlv

        out_rows.append({
            "Date": row["Date"],
            "tenor": tenor,
            "implied_repo_pct": best_irr,  # bps (pipeline expects this column name)
            "optimal_delivery_date": best_dlv,
            "holding_period_days": (best_dlv - (row["caldt"] + pd.offsets.BDay(1))).days if pd.notna(best_dlv) else np.nan,
            "px_last": row["px_last"],
            "px_volume": row["px_volume"],
            "fut_ctd_cusip": row["fut_ctd_cusip"],
        })

    return pd.DataFrame(out_rows).drop_duplicates(subset=["Date"]).set_index("Date").sort_index()


def calc_irr(bloomberg_path: Path | None = None, irr_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Implied repo for 2Y, 5Y, 10Y, 20Y, 30Y. Returns (implied_repo_df, holding_period_df).
    Each has Index=Date, columns=tenor. implied_repo in bps; holding_period in days."""
    manual_dir = irr_path or MANUAL_DATA_DIR
    futures_tidy_path = manual_dir / FUTURES_TIDY_FILE
    futures_tidy_df = _load_tidy_futures_inputs(manual_dir) if futures_tidy_path.exists() else None

    bbg_df = None
    if futures_tidy_df is None:
        bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")
        bbg_df = pd.read_parquet(bbg_path) if Path(bbg_path).is_file() else load_bloomberg(manual_dir)
        if "Date" in bbg_df.columns:
            bbg_df = bbg_df.set_index("Date")
        bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    irr_df = _load_irr_bonds(manual_dir)

    repo_frames = []
    holding_frames = []
    for tenor, ticker in TENOR_CONTRACTS.items():
        if futures_tidy_df is not None:
            one = _calc_implied_repo_per_tenor_from_tidy(futures_tidy_df, irr_df, tenor)
        else:
            one = calc_implied_repo_per_tenor(bbg_df, irr_df, tenor, ticker)
        if not one.empty:
            repo_frames.append(one[["implied_repo_pct"]].rename(columns={"implied_repo_pct": tenor}))
            holding_frames.append(one[["holding_period_days"]].rename(columns={"holding_period_days": tenor}))
    if not repo_frames:
        return pd.DataFrame(), pd.DataFrame()
    implied_repo_df = pd.concat(repo_frames, axis=1).sort_index()
    holding_period_df = pd.concat(holding_frames, axis=1).sort_index()
    return implied_repo_df, holding_period_df


def _extract_ois_series(bbg_df: pd.DataFrame, ois_ticker: str) -> pd.Series:
    s = _col(bbg_df, ois_ticker, "px_last")
    if s is None:
        return pd.Series(dtype=float)
    return s.astype(float)


def _interpolate_ois_at_holding_period(
    holding_period_months: np.ndarray,
    ois_rates_pct_row: np.ndarray,
    tenors_months: list[int],
) -> np.ndarray:
    """Interpolate OIS rate at holding_period_months using OIS at tenors_months.
    ois_rates_pct_row: 1d of length len(tenors_months). Returns rate in percent (caller converts to bps)."""
    tenors = np.array(tenors_months, dtype=float)
    return np.interp(
        np.clip(holding_period_months, tenors.min(), tenors.max()),
        tenors,
        ois_rates_pct_row,
    )


def calc_arbitrage_spread(
    implied_repo_df: pd.DataFrame | None = None,
    holding_period_df: pd.DataFrame | None = None,
    bloomberg_path: Path | None = None,
    manual_dir: Path | None = None,
) -> pd.DataFrame:
    """Spread = implied repo - OIS (bps). OIS is interpolated from 2/3/4/5/6/9M OIS using holding period (days)."""
    manual_dir = manual_dir or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")
    if implied_repo_df is None:
        ir_path = manual_dir / "implied_repo_first_deferred.parquet"
        if not ir_path.exists():
            raise FileNotFoundError(f"Implied repo not found: {ir_path}. Run main() first.")
        implied_repo_df = pd.read_parquet(ir_path)
    if "Date" in implied_repo_df.columns:
        implied_repo_df = implied_repo_df.set_index("Date")
    implied_repo_df.index = pd.to_datetime(implied_repo_df.index).normalize()

    if holding_period_df is None:
        hp_path = manual_dir / "holding_period_days.parquet"
        if not hp_path.exists():
            raise FileNotFoundError(
                f"Holding period not found: {hp_path}. Run main() to generate implied repo and holding period."
            )
        holding_period_df = pd.read_parquet(hp_path)
    if "Date" in holding_period_df.columns:
        holding_period_df = holding_period_df.set_index("Date")
    holding_period_df.index = pd.to_datetime(holding_period_df.index).normalize()

    ois_by_month: dict[int, pd.Series] = {}
    ois_tidy_path = manual_dir / OIS_TIDY_FILE
    if ois_tidy_path.exists():
        ois_tidy = _load_tidy_ois_inputs(manual_dir)
        ois_wide = ois_tidy.pivot_table(
            index="Date",
            columns="ois_month",
            values="ois_rate_pct",
            aggfunc="first",
        )
        for m in OIS_MONTH_TENORS:
            if m in ois_wide.columns:
                ois_by_month[m] = ois_wide[m].astype(float)
    else:
        if not Path(bbg_path).is_file():
            raise FileNotFoundError(f"Bloomberg data not found: {bbg_path}")
        bbg_df = pd.read_parquet(bbg_path)
        if "Date" in bbg_df.columns:
            bbg_df = bbg_df.set_index("Date")
        bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

        for m in OIS_MONTH_TENORS:
            ticker = OIS_MONTH_TICKERS.get(m)
            if ticker is None:
                continue
            s = _extract_ois_series(bbg_df, ticker)
            if s is not None and not s.empty:
                ois_by_month[m] = s

    if len(ois_by_month) != len(OIS_MONTH_TENORS):
        missing = set(OIS_MONTH_TENORS) - set(ois_by_month.keys())
        raise FileNotFoundError(
            f"OIS data missing for month tenors: {missing}. "
            "Ensure tidy_inputs or pull_bloomberg includes OIS month contracts (2M-9M)."
        )

    # Align to common index (dates present in implied repo, holding period, and OIS inputs)
    common_idx = implied_repo_df.index.intersection(holding_period_df.index)
    common_idx = common_idx.sort_values()
    implied_repo_df = implied_repo_df.reindex(common_idx)
    holding_period_df = holding_period_df.reindex(common_idx)
    for m in ois_by_month:
        ois_by_month[m] = ois_by_month[m].reindex(common_idx)

    tenors = list(TENOR_CONTRACTS.keys())
    # Holding period in months (Act/365 then * 12)
    holding_months = holding_period_df[tenors].astype(float) / (365.0 / 12.0)

    ois_row = np.array([ois_by_month[m].values for m in OIS_MONTH_TENORS])
    # For each date: interpolate OIS at holding_months[date, tenor] for each tenor
    n_dates = len(common_idx)
    ois_interp_bps = np.full((n_dates, len(tenors)), np.nan)
    for i in range(n_dates):
        ois_pct_row = ois_row[:, i]
        if np.any(np.isnan(ois_pct_row)):
            continue
        for j, tn in enumerate(tenors):
            months_j = holding_months.iloc[i, j]
            if np.isnan(months_j):
                continue
            rate_pct = _interpolate_ois_at_holding_period(
                np.array([months_j]), ois_pct_row, OIS_MONTH_TENORS
            )[0]
            ois_interp_bps[i, j] = rate_pct * 100.0  # percent -> bps

    ois_df = pd.DataFrame(ois_interp_bps, index=common_idx, columns=tenors)
    irr_aligned, ois_aligned = implied_repo_df[tenors].align(ois_df, join="inner", axis=0)
    return (irr_aligned - ois_aligned).sort_index()


def main():
    manual_dir = MANUAL_DATA_DIR
    print(f"Data directory: {manual_dir}")
    try:
        result, holding_period_df = calc_irr(bloomberg_path=manual_dir / "bloomberg.parquet", irr_path=manual_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    if result.empty:
        print("No implied repo produced.")
        return
    print(result.tail(10).to_string())
    out_path = manual_dir / "implied_repo_first_deferred.parquet"
    result.to_parquet(out_path)
    print(f"Saved: {out_path}")
    holding_path = manual_dir / "holding_period_days.parquet"
    holding_period_df.to_parquet(holding_path)
    print(f"Saved: {holding_path}")
    try:
        spreads = calc_arbitrage_spread(
            implied_repo_df=result,
            holding_period_df=holding_period_df,
            bloomberg_path=manual_dir / "bloomberg.parquet",
            manual_dir=manual_dir,
        )
        if not spreads.empty:
            print(spreads.tail(10).to_string())
            spreads.to_parquet(manual_dir / "arbitrage_spreads.parquet")
            print(f"Saved: {manual_dir / 'arbitrage_spreads.parquet'}")
    except FileNotFoundError as e:
        print(f"Arbitrage spreads skipped: {e}")


if __name__ == "__main__":
    main()

