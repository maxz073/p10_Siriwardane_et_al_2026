"""
Single-date walkthrough: print inputs and steps for IRR (max of first/last delivery).
Run: python walkthrough.py [DATE]
"""

from pathlib import Path

import pandas as pd

from calc_spread import (
    MANUAL_DATA_DIR,
    TENOR_CONTRACTS,
    _compute_ae_ic_d1_d2,
    _extract_contract_series,
    _load_irr_bonds,
    load_bloomberg,
)


def walkthrough_one_date(
    date=None,
    bloomberg_path: Path | None = None,
    irr_path: Path | None = None,
) -> None:
    """For one date, print inputs and intermediate steps for each tenor. If date is None, use first date with valid data."""
    manual_dir = irr_path or MANUAL_DATA_DIR
    bbg_path = bloomberg_path or (manual_dir / "bloomberg.parquet")
    bbg_df = pd.read_parquet(bbg_path) if Path(bbg_path).is_file() else load_bloomberg(manual_dir)
    if "Date" in bbg_df.columns:
        bbg_df = bbg_df.set_index("Date")
    bbg_df.index = pd.to_datetime(bbg_df.index).normalize()

    irr_df = _load_irr_bonds(manual_dir)
    irr_df["tcusip"] = irr_df["tcusip"].astype(str).str.strip().str.strip('"')

    if date is not None:
        walk_date = pd.Timestamp(date).normalize()
    else:
        walk_date = None
        for d in bbg_df.index:
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
            if walk_date is not None:
                break
        if walk_date is None:
            print("No date with valid data found.")
            return
        walk_date = pd.Timestamp(walk_date).normalize()

    print("=" * 70)
    print(f"WALKTHROUGH: {walk_date.date()}")
    print("=" * 70)
    print("\nIRR = (F*CF + Ae + Ic - (P+Ab)) / (d1*(P+Ab) - Ic*d2)  →  bps (×10_000)")
    print("Delivery: max(IRR with first delivery date, IRR with last delivery date).\n")

    for tenor, ticker in TENOR_CONTRACTS.items():
        print("-" * 70)
        print(f"TENOR: {tenor}  ({ticker})")
        print("-" * 70)

        raw = _extract_contract_series(bbg_df, ticker)
        if raw.empty or "px_last" not in raw.columns:
            print("  [No data]\n")
            continue
        raw = raw[raw["px_volume"] > 0].dropna(
            subset=["px_last", "fut_cnvs_factor", "fut_ctd_cusip", "fut_dlv_dt_first", "fut_dlv_dt_last"]
        )
        if raw.empty:
            print("  [No data]\n")
            continue
        raw = raw.reset_index()
        raw["Date"] = pd.to_datetime(raw["Date"]).dt.normalize()
        raw["fut_ctd_cusip"] = raw["fut_ctd_cusip"].astype(str).str.strip().str.strip('"')
        if (raw["Date"] == walk_date).sum() == 0:
            print(f"  [No data for {walk_date.date()}]\n")
            continue
        merged = raw.merge(irr_df, left_on=["Date", "fut_ctd_cusip"], right_on=["caldt", "tcusip"], how="inner")
        merged_one = merged[merged["Date"] == walk_date]
        if merged_one.empty:
            print("  [No bond match]\n")
            continue
        row = merged_one.iloc[0]

        F = float(row["px_last"])
        CF = float(row["fut_cnvs_factor"])
        P = float(row["clean_price"])
        Ab = float(row["accrued_interest_begin"])
        print(f"  F={F}, CF={CF}, P={P}, Ab={Ab}, CTD={row['fut_ctd_cusip']}")
        print(f"  fut_dlv_dt_first={row['fut_dlv_dt_first']}, fut_dlv_dt_last={row['fut_dlv_dt_last']}")

        one = row.to_frame().T.reset_index(drop=True)
        m_first = _compute_ae_ic_d1_d2(one.copy(), "fut_dlv_dt_first").iloc[0]
        m_last = _compute_ae_ic_d1_d2(one.copy(), "fut_dlv_dt_last").iloc[0]

        for label, m in [("First delivery", m_first), ("Last delivery", m_last)]:
            Ae, Ic, d1, d2 = float(m["Ae"]), float(m["Ic"]), float(m["d1"]), float(m["d2"])
            num = (F * CF) + Ae + Ic - (P + Ab)
            denom = (d1 * (P + Ab)) - (Ic * d2)
            bps = (num * 10_000 / denom) if denom > 0 else None
            print(f"  {label}: Ae={Ae:.4f}, Ic={Ic:.4f}, d1={d1:.4f}, d2={d2:.4f} → IRR={bps:.2f} bps" if bps else f"  {label}: denom<=0")

        denom_first = (m_first["d1"] * (P + Ab)) - (m_first["Ic"] * m_first["d2"])
        denom_last = (m_last["d1"] * (P + Ab)) - (m_last["Ic"] * m_last["d2"])
        irr_first = ((F * CF) + m_first["Ae"] + m_first["Ic"] - (P + Ab)) * 10_000 / denom_first if denom_first > 0 else None
        irr_last = ((F * CF) + m_last["Ae"] + m_last["Ic"] - (P + Ab)) * 10_000 / denom_last if denom_last > 0 else None
        vals = [v for v in (irr_first, irr_last) if v is not None]
        final = max(vals) if vals else None
        print(f"  → max(first, last) = {final:.2f} bps\n" if final else "  → invalid\n")

    print("=" * 70)


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    walkthrough_one_date(date=date_arg)
