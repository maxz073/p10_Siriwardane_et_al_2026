"""
Calculate implied repo rate for Treasury futures using the first deferred contract.

Uses data from data_manual/bloomberg.parquet and data_manual/FTZ_IRR.parquet
(also tries TFZ_IRR.parquet if FTZ_IRR is not found). Only includes observations
with positive trading volume. Does not use the nearby contract (1) because delivery
options during the delivery month confound nearby prices; we use the first
deferred (contract 2) so that within a quarter the implied riskless rate tenor
starts at about six months and declines to about three months.

Tenors: 2-year (TU), 5-year (FV), 10-year (TY), 20-year (WN/Ultra 10), 30-year (US).
"""

from pathlib import Path

import pandas as pd

from settings import config

# Data paths: bloomberg and bond-level (CRSP-style) data from data_manual
MANUAL_DATA_DIR = config("MANUAL_DATA_DIR")

# First deferred contract tickers (we do not use nearby 1)
# Mapping: 2Y=TU, 5Y=FV, 10Y=TY, 20Y=WN, 30Y=US

TENOR_CONTRACTS = {
    "2Y": "TU2 Comdty",
    "5Y": "FV2 Comdty",
    "10Y": "TY2 Comdty",
    "20Y": "WN2 Comdty",
    "30Y": "US2 Comdty",
}

# Maturity-matched OIS: Bloomberg has 1Y–4Y (USSO1–USSO4). We use closest available.
# 5Y/10Y/20Y/30Y use 4Y OIS as proxy when longer OIS are not in the pull.
OIS_TENOR_MAP = {
    "2Y": "USSO2 CMPN Curncy",
    "5Y": "USSO4 CMPN Curncy",
    "10Y": "USSO4 CMPN Curncy",
    "20Y": "USSO4 CMPN Curncy",
    "30Y": "USSO4 CMPN Curncy",
}

FIELDS_NEEDED = [
    "px_last",
    "px_volume",
    "fut_ctd_cusip",
    "fut_cnvs_factor",
    "fut_dlv_dt_first",
    "fut_dlv_dt_last",
]


def implied_repo(F, CF, P, Ab, Ae, Ic, d1, d2):
    """Implied repo rate (annualized, simple, 360-day basis).

    Parameters
    ----------
    F : float
        Futures price.
    CF : float
        Conversion factor.
    P : float
        Clean price of CTD bond.
    Ab : float
        Accrued interest at beginning (quote date).
    Ae : float
        Accrued interest at delivery.
    Ic : float
        Coupon income received between quote date and delivery (if any).
    d1 : float
        Day count from quote date to delivery (fraction of year, e.g. Act/360).
    d2 : float
        Day count from interim coupon date to delivery (fraction of year), when
        next coupon is before delivery; else 0.

    Returns
    -------
    float
        Implied repo rate in percent (e.g. 4.5 for 4.5%). Uses 360-day
        annualization; denominator must be in years (e.g. Act/360).
    """
    numerator = (F * CF) + Ae + Ic - (P + Ab)
    denominator = (d1 * (P + Ab)) - (Ic * d2)
    if denominator is None or denominator <= 0:
        return None
    irr = numerator / denominator
    return irr


def _col(bbg_df: pd.DataFrame, ticker: str, field: str):
    """Get a single column from Bloomberg df with MultiIndex or string columns."""
    if isinstance(bbg_df.columns, pd.MultiIndex):
        if (ticker, field) in bbg_df.columns:
            return bbg_df[(ticker, field)]
        # try lowercase field (parquet may store lowercase)
        for c in bbg_df.columns:
            if c[0] == ticker and c[1].lower() == field.lower():
                return bbg_df[c]
        return None
    # Flattened string columns e.g. "('TY2 Comdty', 'px_last')"
    for c in bbg_df.columns:
        if isinstance(c, str) and ticker in c and field in c:
            return bbg_df[c]
    return None


def _extract_contract_series(bbg_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Extract one contract’s series (F, CF, volume, CTD CUSIP, delivery date)."""
    out = pd.DataFrame(index=bbg_df.index)
    out.index.name = "Date"
    for f in FIELDS_NEEDED:
        s = _col(bbg_df, ticker, f)
        if s is not None:
            out[f] = s
    return out


def _load_irr_bonds(manual_dir: Path) -> pd.DataFrame:
    """Load bond-level data (TFZ_IRR.parquet) from data_manual."""
    path = manual_dir / "TFZ_IRR.parquet"
    if not path.exists():
        raise FileNotFoundError(f"TFZ_IRR.parquet not found in {manual_dir}")
    df = pd.read_parquet(path)
    if "caldt" in df.columns:
        df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()
    return df


def _compute_ae_ic_d1_d2(merged: pd.DataFrame, delivery_col: str) -> pd.DataFrame:
    """Add Ae, Ic, d1, d2 for the implied repo formula."""
    df = merged.copy()
    df[delivery_col] = pd.to_datetime(df[delivery_col])
    df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()

    # Coupon per period (semiannual per 100 par)
    freq = df.get("coupon_frequency", 2)
    df["coupon_cash_per_period"] = df["coupon_rate"] / freq

    # Ae: accrued interest at delivery = interest from last coupon payment (before delivery) until delivery date.
    # prev/next_coupon are relative to quote date; we need the coupon date that is immediately before delivery.
    next_cpn = pd.to_datetime(df["next_coupon_date"])
    prev_cpn = pd.to_datetime(df["prev_coupon_date"])
    delivery = df[delivery_col]
    # If delivery is before next_coupon, last coupon before delivery = prev_cpn; else = next_cpn (delivery in next period).
    last_cpn_before_delivery = prev_cpn.where(delivery < next_cpn, next_cpn)
    # End of accrual period: next_cpn when in first period, or next_cpn + 6 months when in second.
    period_end = next_cpn.where(delivery < next_cpn, next_cpn + pd.DateOffset(months=6))
    period_days = (period_end - last_cpn_before_delivery).dt.days
    accrued_days_end = (delivery - last_cpn_before_delivery).dt.days
    df["Ae"] = df["coupon_cash_per_period"] * accrued_days_end / period_days.replace(0, 1)

    # Ic: coupon received between caldt and delivery (only if next_coupon in between)
    df["Ic"] = 0.0
    mask_cpn_before_delivery = (next_cpn > df["caldt"]) & (next_cpn <= df[delivery_col])
    df.loc[mask_cpn_before_delivery, "Ic"] = df.loc[mask_cpn_before_delivery, "coupon_cash_per_period"]

    # d1: days from quote to delivery / 360
    df["d1"] = (df[delivery_col] - df["caldt"]).dt.days / 360.0

    # d2: days from interim coupon date to delivery / 360 when next coupon <= delivery, else 0
    df["d2"] = 0.0
    mask = (next_cpn > df["caldt"]) & (next_cpn <= df[delivery_col])
    df.loc[mask, "d2"] = (df.loc[mask, delivery_col] - next_cpn.loc[mask]).dt.days / 360.0

    return df


def load_bloomberg(manual_dir: Path) -> pd.DataFrame:
    """Load Bloomberg parquet; ensure Date index."""
    path = manual_dir / "bloomberg.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Bloomberg data not found: {path}")
    df = pd.read_parquet(path)
    if "Date" in df.columns and df.index.name != "Date":
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index).normalize()
    return df


def calc_implied_repo_per_tenor(
    bbg_df: pd.DataFrame,
    irr_df: pd.DataFrame,
    tenor: str,
    ticker: str,
    ois_series: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Compute implied repo for one tenor using first deferred contract and positive volume.

    Delivery date: use fut_dlv_dt_first when OIS rate > bond coupon rate (deliver
    early), fut_dlv_dt_last when OIS rate < bond coupon rate (deliver late).
    Uses the true risk-free (OIS) rate for this choice, not the implied repo.
    """
    raw = _extract_contract_series(bbg_df, ticker)
    if raw.empty or "px_last" not in raw.columns:
        return pd.DataFrame()

    raw = raw[raw["px_volume"] > 0].copy()
    raw = raw.dropna(
        subset=["px_last", "fut_cnvs_factor", "fut_ctd_cusip", "fut_dlv_dt_first", "fut_dlv_dt_last"]
    )
    if raw.empty:
        return pd.DataFrame()

    raw = raw.reset_index()
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()

    # Merge with bond data on date and CTD CUSIP
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

    P = merged["clean_price"]
    Ab = merged["accrued_interest_begin"]
    F = merged["px_last"]
    CF = merged["fut_cnvs_factor"]
    coupon_rate = merged["coupon_rate"]

    # Choose delivery date from rule: first when OIS > coupon, last when OIS <= coupon. Default first when OIS missing.
    if ois_series is not None:
        ois_series = ois_series.copy()
        ois_series.index = pd.to_datetime(ois_series.index).normalize()
        ois_rate = merged["Date"].map(ois_series)
        use_first = ois_rate > coupon_rate
    else:
        use_first = pd.Series(True, index=merged.index)

    # Compute Ae, Ic, d1, d2 using the chosen delivery date per row (first or last by rule).
    merged_first = _compute_ae_ic_d1_d2(merged.copy(), delivery_col="fut_dlv_dt_first")
    merged_last = _compute_ae_ic_d1_d2(merged.copy(), delivery_col="fut_dlv_dt_last")
    merged_computed = merged.copy()
    for col in ("Ae", "Ic", "d1", "d2"):
        merged_computed[col] = merged_first[col].where(use_first.values, merged_last[col].values)

    d1, d2 = merged_computed["d1"], merged_computed["d2"]
    Ae, Ic = merged_computed["Ae"], merged_computed["Ic"]
    denom = (d1 * (P + Ab)) - (Ic * d2)
    valid = (denom > 0) & d1.notna() & (d1 > 0)
    irr_pct = pd.Series(index=merged.index, dtype=float)
    irr_pct.loc[valid] = (
        ((F * CF) + Ae + Ic - (P + Ab)).loc[valid] * 10_000 / denom.loc[valid]
    )

    result = merged[["Date"]].copy()
    result["tenor"] = tenor
    result["implied_repo_pct"] = irr_pct
    result["px_last"] = merged["px_last"]
    result["px_volume"] = merged["px_volume"]
    result["fut_ctd_cusip"] = merged["fut_ctd_cusip"]
    return result.drop_duplicates(subset=["Date"]).set_index("Date").sort_index()


def calc_irr(
    bloomberg_path: Path | None = None,
    irr_path: Path | None = None,
) -> pd.DataFrame:
    """
    Calculate implied repo rate for 2Y, 5Y, 10Y, 20Y, and 30Y Treasury futures.

    Uses the first deferred contract and only observations with positive volume.
    Merges Bloomberg futures data with bond-level data (FTZ_IRR / TFZ_IRR) on
    date and CTD CUSIP, then applies the implied repo formula.

    Parameters
    ----------
    bloomberg_path : Path, optional
        Path to bloomberg.parquet. Default: MANUAL_DATA_DIR / "bloomberg.parquet".
    irr_path : Path, optional
        Directory to look for FTZ_IRR.parquet / TFZ_IRR.parquet. Default: MANUAL_DATA_DIR.

    Returns
    -------
    pd.DataFrame
        Index: Date. Columns: one column per tenor (e.g. '2Y', '5Y', ...) with
        implied repo rate in percent. Rows are dates where we had valid data
        for at least one tenor.
    """
    manual_dir = irr_path or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")

    if Path(bbg_path).is_file():
        bbg_df = pd.read_parquet(bbg_path)
    else:
        bbg_df = load_bloomberg(manual_dir)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    irr_df = _load_irr_bonds(manual_dir)

    frames = []
    for tenor, ticker in TENOR_CONTRACTS.items():
        ois_series = _extract_ois_series(bbg_df, OIS_TENOR_MAP[tenor])
        if ois_series.empty or ois_series.notna().sum() == 0:
            ois_series = None
        else:
            if ois_series.max() < 10:
                ois_series = ois_series * 100
        one = calc_implied_repo_per_tenor(bbg_df, irr_df, tenor, ticker, ois_series=ois_series)
        if not one.empty:
            one = one[["implied_repo_pct"]].rename(columns={"implied_repo_pct": tenor})
            frames.append(one)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, axis=1).sort_index()


def _extract_ois_series(bbg_df: pd.DataFrame, ois_ticker: str) -> pd.Series:
    """Extract OIS rate (px_last) for one ticker from Bloomberg df."""
    s = _col(bbg_df, ois_ticker, "px_last")
    if s is None:
        return pd.Series(dtype=float)
    return s.astype(float)


def calc_arbitrage_spread(
    implied_repo_df: pd.DataFrame | None = None,
    bloomberg_path: Path | None = None,
    manual_dir: Path | None = None,
) -> pd.DataFrame:
    """
    Compute arbitrage spreads: futures-implied riskless rate minus maturity-matched OIS.

    Spread = implied_repo (from first deferred contract) - OIS rate. Returns a
    DataFrame of spreads over time, one column per tenor (2Y, 5Y, 10Y, 20Y, 30Y).

    Parameters
    ----------
    implied_repo_df : pd.DataFrame, optional
        Implied repo rates (index=Date, columns=2Y, 5Y, ...). If None, loads from
        implied_repo_first_deferred.parquet (run calc_spread first).
    bloomberg_path : Path, optional
        Path to bloomberg.parquet for OIS. Default: manual_dir / "bloomberg.parquet".
    manual_dir : Path, optional
        data_manual directory. Default: MANUAL_DATA_DIR.

    Returns
    -------
    pd.DataFrame
        Index: Date. Columns: 2Y, 5Y, 10Y, 20Y, 30Y (spread in percent).
    """
    manual_dir = manual_dir or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")

    if implied_repo_df is None:
        ir_path = manual_dir / "implied_repo_first_deferred.parquet"
        if not ir_path.exists():
            raise FileNotFoundError(
                f"Implied repo not found: {ir_path}. Run calc_spread() first."
            )
        implied_repo_df = pd.read_parquet(ir_path)
    if "Date" in implied_repo_df.columns:
        implied_repo_df = implied_repo_df.set_index("Date")
    implied_repo_df.index = pd.to_datetime(implied_repo_df.index).normalize()

    if not Path(bbg_path).is_file():
        raise FileNotFoundError(f"Bloomberg data not found: {bbg_path}")
    bbg_df = pd.read_parquet(bbg_path)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    # Build OIS panel: one column per tenor (same column names as implied_repo)
    ois_df = pd.DataFrame(index=bbg_df.index)
    for tenor, ois_ticker in OIS_TENOR_MAP.items():
        ois_df[tenor] = _extract_ois_series(bbg_df, ois_ticker)
    ois_df = ois_df.reindex(columns=list(TENOR_CONTRACTS.keys()))

    # Align dates: inner join so we only have dates with both implied repo and OIS
    common = implied_repo_df.align(ois_df, join="inner", axis=0)
    irr_aligned = common[0]
    ois_aligned = common[1] * 100 #100 for decimals -> bps. DONT FORGET TO MOVE TO NEXT STEP

    # Spread = implied riskless rate - OIS (both in percent)
    spread_df = irr_aligned - ois_aligned
    return spread_df.sort_index()


def main():
    """Run implied repo and arbitrage spread calculation; print summary and save."""
    manual_dir = MANUAL_DATA_DIR
    print(f"Data directory: {manual_dir}")

    try:
        result = calc_irr(
            bloomberg_path=manual_dir / "bloomberg.parquet",
            irr_path=manual_dir,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    if result.empty:
        print("No implied repo series produced (check data and filters).")
        return

    print("\nImplied repo (%), first deferred, volume > 0:")
    print(result.tail(10).to_string())
    print(f"\nShape: {result.shape}")
    out_path = manual_dir / "implied_repo_first_deferred.parquet"
    result.to_parquet(out_path)
    print(f"Saved: {out_path}")

    # Arbitrage spreads: implied riskless rate - maturity-matched OIS
    try:
        spreads = calc_arbitrage_spread(
            implied_repo_df=result,
            bloomberg_path=manual_dir / "bloomberg.parquet",
            manual_dir=manual_dir,
        )
        if not spreads.empty:
            print("\nArbitrage spread (implied repo - OIS), %:")
            print(spreads.tail(10).to_string())
            print(f"\nShape: {spreads.shape}")
            spread_path = manual_dir / "arbitrage_spreads.parquet"
            spreads.to_parquet(spread_path)
            print(f"Saved: {spread_path}")
    except FileNotFoundError as e:
        print(f"\nArbitrage spreads skipped: {e}")


def walkthrough_one_date(
    date=None,
    bloomberg_path: Path | None = None,
    irr_path: Path | None = None,
) -> None:
    """
    For one date, print all inputs and intermediate steps to get IRR for each tenor.
    Useful to trace the full calculation. If date is None, uses the first date
    that has valid data for at least one tenor.
    """
    manual_dir = irr_path or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")
    if Path(bbg_path).is_file():
        bbg_df = pd.read_parquet(bbg_path)
    else:
        bbg_df = load_bloomberg(manual_dir)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    irr_df = _load_irr_bonds(manual_dir)
    irr_df["tcusip"] = irr_df["tcusip"].astype(str).str.strip().str.strip('"')

    # If no date given, find first date with at least one valid tenor
    if date is not None:
        walk_date = pd.Timestamp(date).normalize()
    else:
        for _, row in bbg_df.iterrows():
            d = row.name
            for tenor, ticker in TENOR_CONTRACTS.items():
                raw = _extract_contract_series(bbg_df.loc[[d]], ticker)
                if raw.empty or "px_last" not in raw.columns:
                    continue
                raw = raw[raw["px_volume"] > 0].dropna(
                    subset=["px_last", "fut_cnvs_factor", "fut_ctd_cusip", "fut_dlv_dt_first", "fut_dlv_dt_last"]
                )
                if raw.empty:
                    continue
                raw = raw.reset_index()
                raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()
                raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')
                merged = raw.merge(irr_df, left_on=["Date", "fut_ctd_cusip"], right_on=["caldt", "tcusip"], how="inner")
                if not merged.empty:
                    walk_date = d
                    break
            else:
                continue
            break
        else:
            print("No date with valid data found.")
            return
        walk_date = pd.Timestamp(walk_date).normalize()

    print("=" * 70)
    print(f"WALKTHROUGH: Single date = {walk_date.date()}")
    print("=" * 70)
    print("\nData sources:")
    print("  - Bloomberg (futures): px_last, px_volume, fut_ctd_cusip, fut_cnvs_factor, fut_dlv_dt_first, fut_dlv_dt_last")
    print("  - Bond file (TFZ_IRR): caldt, tcusip, clean_price, accrued_interest_begin, coupon_rate, next_coupon_date, prev_coupon_date")
    print("\nIRR formula (Act/360, simple):")
    print("  numerator   = (F*CF) + Ae + Ic - (P + Ab)")
    print("  denominator = d1*(P+Ab) - Ic*d2")
    print("  IRR (decimal) = numerator / denominator   →  stored as basis points (× 10_000)")
    print("  Delivery: use FIRST date if IRR > coupon (deliver early), else LAST date.")
    print()

    for tenor, ticker in TENOR_CONTRACTS.items():
        print("-" * 70)
        print(f"TENOR: {tenor}  (contract: {ticker})")
        print("-" * 70)

        raw = _extract_contract_series(bbg_df, ticker)
        if raw.empty or "px_last" not in raw.columns:
            print("  [No Bloomberg series for this ticker]\n")
            continue
        raw = raw[raw["px_volume"] > 0].copy()
        raw = raw.dropna(
            subset=["px_last", "fut_cnvs_factor", "fut_ctd_cusip", "fut_dlv_dt_first", "fut_dlv_dt_last"]
        )
        if raw.empty:
            print("  [No rows with positive volume and full fields]\n")
            continue
        raw = raw.reset_index()
        raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()
        raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')
        row_date = raw["Date"] == walk_date
        if not row_date.any():
            print(f"  [No data for date {walk_date.date()}]\n")
            continue
        raw_one = raw.loc[row_date].iloc[0]
        merged = raw.merge(irr_df, left_on=["Date", "fut_ctd_cusip"], right_on=["caldt", "tcusip"], how="inner")
        merged_one = merged[(merged["Date"] == walk_date)]
        if merged_one.empty:
            print(f"  [No bond match for CTD CUSIP on this date]\n")
            continue
        merged_one = merged_one.iloc[0]

        # Inputs from Bloomberg
        F = float(merged_one["px_last"])
        CF = float(merged_one["fut_cnvs_factor"])
        cusip = merged_one["fut_ctd_cusip"]
        dlv_first = merged_one["fut_dlv_dt_first"]
        dlv_last = merged_one["fut_dlv_dt_last"]
        vol = merged_one["px_volume"]
        print("  INPUTS (Bloomberg, first deferred):")
        print(f"    F (futures price)     = {F}")
        print(f"    CF (conversion factor)= {CF}")
        print(f"    CTD CUSIP             = {cusip}")
        print(f"    fut_dlv_dt_first      = {dlv_first}")
        print(f"    fut_dlv_dt_last       = {dlv_last}")
        print(f"    px_volume             = {vol}")

        P = float(merged_one["clean_price"])
        Ab = float(merged_one["accrued_interest_begin"])
        coupon_rate = float(merged_one["coupon_rate"])
        next_cpn = merged_one["next_coupon_date"]
        prev_cpn = merged_one["prev_coupon_date"]
        print("  INPUTS (Bond file, matched on date + CUSIP):")
        print(f"    P (clean price)       = {P}")
        print(f"    Ab (accrued @ begin)  = {Ab}")
        print(f"    coupon_rate           = {coupon_rate}")
        print(f"    next_coupon_date      = {next_cpn}")
        print(f"    prev_coupon_date      = {prev_cpn}")
        print(f"    P + Ab (dirty price)  = {P + Ab}")

        one_row = merged_one.to_frame().T.reset_index(drop=True)
        merged_first = _compute_ae_ic_d1_d2(one_row.copy(), delivery_col="fut_dlv_dt_first").iloc[0]
        merged_last = _compute_ae_ic_d1_d2(one_row.copy(), delivery_col="fut_dlv_dt_last").iloc[0]

        for label, m in [("First delivery (early)", merged_first), ("Last delivery (late)", merged_last)]:
            Ae = float(m["Ae"])
            Ic = float(m["Ic"])
            d1 = float(m["d1"])
            d2 = float(m["d2"])
            num = (F * CF) + Ae + Ic - (P + Ab)
            denom = (d1 * (P + Ab)) - (Ic * d2)
            irr_decimal = num / denom if denom > 0 else None
            irr_bps = (num * 10_000 / denom) if denom > 0 else None
            print(f"  {label}:")
            print(f"    Ae = {Ae:.6f},  Ic = {Ic:.6f},  d1 = {d1:.6f},  d2 = {d2:.6f}")
            print(f"    numerator   = (F*CF)+Ae+Ic-(P+Ab) = {num:.6f}")
            print(f"    denominator = d1*(P+Ab)-Ic*d2   = {denom:.6f}")
            print(f"    IRR (decimal) = {irr_decimal:.6f}" if irr_decimal is not None else "    IRR = invalid (denom <= 0)")
            if irr_bps is not None:
                print(f"    IRR (bps)    = {irr_bps:.2f}")

        irr_first_bps = (merged_first["d1"] * (P + Ab) - merged_first["Ic"] * merged_first["d2"])
        if irr_first_bps > 0:
            irr_first_val = ((F * CF) + merged_first["Ae"] + merged_first["Ic"] - (P + Ab)) * 10_000 / irr_first_bps
        else:
            irr_first_val = None
        irr_last_denom = (merged_last["d1"] * (P + Ab) - merged_last["Ic"] * merged_last["d2"])
        if irr_last_denom > 0:
            irr_last_val = ((F * CF) + merged_last["Ae"] + merged_last["Ic"] - (P + Ab)) * 10_000 / irr_last_denom
        else:
            irr_last_val = None

        # Same rule as in calc_implied_repo_per_tenor: use OIS (true repo) vs coupon for delivery choice
        ois_ticker = OIS_TENOR_MAP.get(tenor)
        ois_val = None
        if ois_ticker is not None:
            ois_series = _extract_ois_series(bbg_df, ois_ticker)
            if not ois_series.empty and walk_date in ois_series.index:
                ois_val = float(ois_series.loc[walk_date])
                if ois_val is not None and ois_val < 10:
                    ois_val = ois_val * 100
        if ois_val is not None and ois_val > coupon_rate:
            chosen = "first (early)"
            final_bps = irr_first_val
        elif ois_val is not None and ois_val <= coupon_rate:
            chosen = "last (late)"
            final_bps = irr_last_val
        elif ois_val is None and irr_last_val is not None:
            chosen = "last (late)"
            final_bps = irr_last_val
        elif irr_first_val is not None:
            chosen = "first (early)"
            final_bps = irr_first_val
        else:
            chosen = "N/A"
            final_bps = None
        ois_msg = f"OIS = {ois_val:.2f}%" if ois_val is not None else "OIS = N/A"
        print(f"  Coupon rate = {coupon_rate}  ({ois_msg})  →  use {chosen}  (OIS > coupon ⇒ early).")
        print(f"  FINAL implied_repo for {tenor}: {final_bps:.2f} bps" if final_bps is not None else f"  FINAL: invalid")
        print()

    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "walkthrough":
        date_arg = sys.argv[2] if len(sys.argv) > 2 else None
        walkthrough_one_date(date=date_arg)
    else:
        main()
