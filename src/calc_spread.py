"""
Implied repo rate for Treasury futures (first deferred contract, volume > 0).
IRR = max(IRR using first delivery date, IRR using last delivery date).
Data: data_manual/bloomberg.parquet, data_manual/TFZ_IRR.parquet.
"""

from pathlib import Path

import pandas as pd

from settings import config

MANUAL_DATA_DIR = config("MANUAL_DATA_DIR")

TENOR_CONTRACTS = {
    "2Y": "TU2 Comdty",
    "5Y": "FV2 Comdty",
    "10Y": "TY2 Comdty",
    "20Y": "WN2 Comdty",
    "30Y": "US2 Comdty",
}

OIS_TENOR_MAP = {
    "2Y": "USSO2 CMPN Curncy",
    "5Y": "USSO4 CMPN Curncy",
    "10Y": "USSO4 CMPN Curncy",
    "20Y": "USSO4 CMPN Curncy",
    "30Y": "USSO4 CMPN Curncy",
}

FIELDS_NEEDED = [
    "px_last", "px_volume", "fut_ctd_cusip", "fut_cnvs_factor",
    "fut_dlv_dt_first", "fut_dlv_dt_last",
]


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
    path = manual_dir / "TFZ_IRR.parquet"
    if not path.exists():
        raise FileNotFoundError(f"TFZ_IRR.parquet not found in {manual_dir}")
    df = pd.read_parquet(path)
    if "caldt" in df.columns:
        df["caldt"] = pd.to_datetime(df["caldt"]).dt.normalize()
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

    df["Ic"] = 0.0
    mask_cpn = (next_cpn > df["caldt"]) & (next_cpn <= df[delivery_col])
    df.loc[mask_cpn, "Ic"] = df.loc[mask_cpn, "coupon_cash_per_period"]

    df["d1"] = (df[delivery_col] - df["caldt"]).dt.days / 360.0
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


def calc_implied_repo_per_tenor(
    bbg_df: pd.DataFrame,
    irr_df: pd.DataFrame,
    tenor: str,
    ticker: str,
) -> pd.DataFrame:
    """IRR per date for one tenor; result = max(IRR first delivery, IRR last delivery)."""
    raw = _extract_contract_series(bbg_df, ticker)
    if raw.empty or "px_last" not in raw.columns:
        return pd.DataFrame()

    raw = raw[raw["px_volume"] > 0].copy()
    raw = raw.dropna(subset=["px_last", "fut_cnvs_factor", "fut_ctd_cusip", "fut_dlv_dt_first", "fut_dlv_dt_last"])
    if raw.empty:
        return pd.DataFrame()

    raw = raw.reset_index()
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()
    irr = irr_df.copy()
    irr["tcusip"] = irr["tcusip"].astype(str).str.strip().str.strip('"')
    raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')
    merged = raw.merge(irr, left_on=["Date", "fut_ctd_cusip"], right_on=["caldt", "tcusip"], how="inner")
    if merged.empty:
        return pd.DataFrame()

    P, Ab = merged["clean_price"], merged["accrued_interest_begin"]
    F, CF = merged["px_last"], merged["fut_cnvs_factor"]
    m_first = _compute_ae_ic_d1_d2(merged.copy(), "fut_dlv_dt_first")
    m_last = _compute_ae_ic_d1_d2(merged.copy(), "fut_dlv_dt_last")
    irr_first = _irr_series(merged, m_first, P, Ab, F, CF)
    irr_last = _irr_series(merged, m_last, P, Ab, F, CF)
    irr_pct = pd.concat([irr_first, irr_last], axis=1).max(axis=1)

    result = merged[["Date"]].copy()
    result["tenor"] = tenor
    result["implied_repo_pct"] = irr_pct
    result["px_last"] = merged["px_last"]
    result["px_volume"] = merged["px_volume"]
    result["fut_ctd_cusip"] = merged["fut_ctd_cusip"]
    return result.drop_duplicates(subset=["Date"]).set_index("Date").sort_index()


def calc_irr(bloomberg_path: Path | None = None, irr_path: Path | None = None) -> pd.DataFrame:
    """Implied repo for 2Y, 5Y, 10Y, 20Y, 30Y. Index=Date, columns=tenor (bps)."""
    manual_dir = irr_path or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")
    bbg_df = pd.read_parquet(bbg_path) if Path(bbg_path).is_file() else load_bloomberg(manual_dir)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()
    irr_df = _load_irr_bonds(manual_dir)

    frames = []
    for tenor, ticker in TENOR_CONTRACTS.items():
        one = calc_implied_repo_per_tenor(bbg_df, irr_df, tenor, ticker)
        if not one.empty:
            frames.append(one[["implied_repo_pct"]].rename(columns={"implied_repo_pct": tenor}))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index()


def _extract_ois_series(bbg_df: pd.DataFrame, ois_ticker: str) -> pd.Series:
    s = _col(bbg_df, ois_ticker, "px_last")
    if s is None:
        return pd.Series(dtype=float)
    return s.astype(float)


def calc_arbitrage_spread(
    implied_repo_df: pd.DataFrame | None = None,
    bloomberg_path: Path | None = None,
    manual_dir: Path | None = None,
) -> pd.DataFrame:
    """Spread = implied repo - OIS (percent). Index=Date, columns=tenor."""
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

    if not Path(bbg_path).is_file():
        raise FileNotFoundError(f"Bloomberg data not found: {bbg_path}")
    bbg_df = pd.read_parquet(bbg_path)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    ois_df = pd.DataFrame(index=bbg_df.index)
    for tenor, ois_ticker in OIS_TENOR_MAP.items():
        ois_df[tenor] = _extract_ois_series(bbg_df, ois_ticker)
    ois_df = ois_df.reindex(columns=list(TENOR_CONTRACTS.keys()))
    ois_bps = ois_df * 100  # percent -> bps (implied_repo is in bps)

    irr_aligned, ois_aligned = implied_repo_df.align(ois_bps, join="inner", axis=0)
    return (irr_aligned - ois_aligned).sort_index()


def main():
    manual_dir = MANUAL_DATA_DIR
    print(f"Data directory: {manual_dir}")
    try:
        result = calc_irr(bloomberg_path=manual_dir / "bloomberg.parquet", irr_path=manual_dir)
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
    try:
        spreads = calc_arbitrage_spread(implied_repo_df=result, bloomberg_path=manual_dir / "bloomberg.parquet", manual_dir=manual_dir)
        if not spreads.empty:
            print(spreads.tail(10).to_string())
            spreads.to_parquet(manual_dir / "arbitrage_spreads.parquet")
            print(f"Saved: {manual_dir / 'arbitrage_spreads.parquet'}")
    except FileNotFoundError as e:
        print(f"Arbitrage spreads skipped: {e}")


if __name__ == "__main__":
    main()
