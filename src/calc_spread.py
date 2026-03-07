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


def _compute_ae_ic_d1_d2(merged: pd.DataFrame, delivery_col: str = "fut_dlv_dt_first") -> pd.DataFrame:
    """Add Ae, Ic, d1, d2 for the implied repo formula."""
    df = merged.copy()
    df[delivery_col] = pd.to_datetime(df[delivery_col])
    df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()

    # Coupon per period (semiannual per 100 par)
    freq = df.get("coupon_frequency", 2)
    df["coupon_cash_per_period"] = df["coupon_rate"] / freq

    # Ae: accrued interest at delivery
    next_cpn = pd.to_datetime(df["next_coupon_date"])
    prev_cpn = pd.to_datetime(df["prev_coupon_date"])
    period_days = (next_cpn - prev_cpn).dt.days
    accrued_days_end = (df[delivery_col] - prev_cpn).dt.days
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
) -> pd.DataFrame:
    """
    Compute implied repo for one tenor using first deferred contract and positive volume.

    Delivery date: use fut_dlv_dt_first when implied repo > bond coupon rate (deliver
    early), fut_dlv_dt_last when implied repo < bond coupon rate (deliver late).
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

    # Delivery date: first if implied repo > bond coupon (deliver early), last if repo < coupon (deliver late).
    merged_first = _compute_ae_ic_d1_d2(merged.copy(), delivery_col="fut_dlv_dt_first")
    merged_last = _compute_ae_ic_d1_d2(merged.copy(), delivery_col="fut_dlv_dt_last")

    P = merged["clean_price"]
    Ab = merged["accrued_interest_begin"]
    F = merged["px_last"]
    CF = merged["fut_cnvs_factor"]
    coupon_rate = merged["coupon_rate"]

    def _irr_from_comp( m: pd.DataFrame ) -> pd.Series:
        d1, d2 = m["d1"], m["d2"]
        Ae, Ic = m["Ae"], m["Ic"]
        denom = (d1 * (P + Ab)) - (Ic * d2)
        valid = (denom > 0) & d1.notna() & (d1 > 0)
        out = pd.Series(index=merged.index, dtype=float)
        out.loc[valid] = (
            ((F * CF) + Ae + Ic - (P + Ab)).loc[valid] * 10_000 / denom.loc[valid] #10_000 for decimals -> bps
        )
        return out

    irr_first = _irr_from_comp(merged_first)
    irr_last = _irr_from_comp(merged_last)

    # Use first delivery when repo > coupon, else last delivery.
    irr_pct = irr_first.where(irr_first > coupon_rate, irr_last)

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
        one = calc_implied_repo_per_tenor(bbg_df, irr_df, tenor, ticker)
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


if __name__ == "__main__":
    main()
