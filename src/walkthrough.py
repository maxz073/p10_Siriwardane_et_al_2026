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
    _delivery_dates_from_contract_month,
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
                raw = _delivery_dates_from_contract_month(raw)
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
        raw = _delivery_dates_from_contract_month(raw)
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

        # ----- Beginning input values -----
        print("  BEGINNING INPUTS")
        print("  (from Bloomberg)")
        F = float(row["px_last"])
        CF = float(row["fut_cnvs_factor"])
        print(f"    px_last (F) = {F}")
        print(f"    fut_cnvs_factor (CF) = {CF}")
        print(f"    fut_ctd_cusip (CTD) = {row['fut_ctd_cusip']}")
        print(f"    current_contract_month_yr = {row.get('current_contract_month_yr', 'N/A')}")
        print(f"    fut_dlv_dt_first = {row['fut_dlv_dt_first']}")
        print(f"    fut_dlv_dt_last = {row['fut_dlv_dt_last']}")
        print("  (from bond / CRSP)")
        P = float(row["clean_price"])
        print(f"    clean_price (P) = {P}")
        print(f"    accrued_interest_begin (from bond) = {float(row['accrued_interest_begin'])}  [Ab used in IRR is computed at settlement T+1 below]")
        print(f"    coupon_rate = {row['coupon_rate']}")
        print(f"    coupon_frequency = {row.get('coupon_frequency', 2)}")
        print(f"    next_coupon_date = {row['next_coupon_date']}")
        print(f"    prev_coupon_date = {row['prev_coupon_date']}")
        print(f"    Date (caldt) = {walk_date}")

        one = row.to_frame().T.reset_index(drop=True)
        m_first = _compute_ae_ic_d1_d2(one.copy(), "fut_dlv_dt_first").iloc[0]
        m_last = _compute_ae_ic_d1_d2(one.copy(), "fut_dlv_dt_last").iloc[0]

        def print_intermediates_for_delivery(label: str, m: pd.Series, delivery_col: str) -> float | None:
            """Print intermediates for one delivery date; return IRR in bps or None. Matches calc_spread._compute_ae_ic_d1_d2 and _irr_series."""
            freq = int(row.get("coupon_frequency", 2))
            coupon_cash = float(row["coupon_rate"]) / freq
            caldt = pd.Timestamp(walk_date).normalize()
            delivery = pd.Timestamp(m[delivery_col])
            next_cpn = pd.Timestamp(row["next_coupon_date"])
            prev_cpn = pd.Timestamp(row["prev_coupon_date"])
            # Settlement T+1 business day (carry starts on settlement)
            settlement_date = caldt + pd.offsets.BDay(1)
            # Ab = accrued at settlement (computed in _compute_ae_ic_d1_d2)
            Ab_settle = float(m["Ab"])
            last_cpn = prev_cpn if delivery < next_cpn else next_cpn
            period_end = next_cpn if delivery < next_cpn else next_cpn + pd.DateOffset(months=6)
            period_days = (period_end - last_cpn).days
            accrued_days_end = (delivery - last_cpn).days
            Ae = float(m["Ae"])
            Ic = float(m["Ic"])
            d1 = float(m["d1"])  # (delivery - settlement_date).days / 360
            d2 = float(m["d2"])
            ex_coupon_date = next_cpn - pd.offsets.BDay(1)
            mask_cpn = (caldt < ex_coupon_date) and (ex_coupon_date <= delivery)

            print(f"  INTERMEDIATES — {label}")
            print(f"    coupon_cash_per_period = coupon_rate / freq = {row['coupon_rate']} / {freq} = {coupon_cash:.6f}")
            print(f"    settlement_date = caldt + BDay(1) = {settlement_date.date()}")
            print(f"    Ab (accrued at settlement) = {Ab_settle:.6f}")
            print(f"    next_coupon_date = {next_cpn.date()}, prev_coupon_date = {prev_cpn.date()}, delivery = {delivery.date()}")
            print(f"    last_cpn_before_delivery = {last_cpn.date()}, period_end = {period_end.date()}")
            print(f"    period_days = {period_days}, accrued_days_end = {accrued_days_end}")
            print(f"    Ae = coupon_cash * accrued_days_end / period_days = {Ae:.6f}")
            print(f"    ex_coupon_date = next_cpn - BDay(1) = {ex_coupon_date.date()}")
            print(f"    mask_cpn (caldt < ex_coupon <= delivery): {mask_cpn}")
            print(f"    Ic = {Ic:.6f}, d1 = (delivery - settlement).days/360 = {d1:.6f}, d2 = {d2:.6f}")
            P_Ab = P + Ab_settle
            num = (F * CF) + Ae + Ic - P_Ab
            denom = (d1 * P_Ab) - (Ic * d2)
            print(f"    numerator = F*CF + Ae + Ic - (P+Ab) = {F}*{CF} + {Ae:.4f} + {Ic:.4f} - {P_Ab:.4f} = {num:.6f}")
            print(f"    denominator = d1*(P+Ab) - Ic*d2 = {d1:.6f}*{P_Ab:.4f} - {Ic:.6f}*{d2:.6f} = {denom:.6f}")
            bps = (num * 10_000 / denom) if denom > 0 else None
            if bps is not None:
                print(f"    IRR_bps = numerator * 10_000 / denominator = {bps:.2f} bps")
            else:
                print(f"    IRR_bps = (invalid, denom <= 0)")
            return bps

        irr_first = print_intermediates_for_delivery("First delivery", m_first, "fut_dlv_dt_first")
        print("")
        irr_last = print_intermediates_for_delivery("Last delivery", m_last, "fut_dlv_dt_last")

        vals = [v for v in (irr_first, irr_last) if v is not None]
        final = max(vals) if vals else None
        print("  FINAL")
        print(f"    max(IRR_first, IRR_last) = {final:.2f} bps\n" if final else "    (invalid)\n")

    print("=" * 70)


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    walkthrough_one_date(date=date_arg)
