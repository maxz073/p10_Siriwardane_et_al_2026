"""
Test: Pull only the most recent Bloomberg snapshot for each security.

- Uses bdp() (point-in-time) instead of bdh() (time series).
- Pulls futures + OIS snapshots.
- Tries to resolve CTD bonds from futures and pulls bond snapshots too.

You must have a Bloomberg Terminal running and xbbg installed.
"""

from pathlib import Path

import pandas as pd

from settings import config

DATA_DIR = Path(r"C:\Users\maxz\bbg_run\p10_Siriwardane_et_al_2026")

# Treasury futures contracts
FUTURES_CONTRACTS = [
    "TY1 Comdty",
    "FV1 Comdty",
    "TU1 Comdty",
    "US1 Comdty",
    "WN1 Comdty",
    "TY2 Comdty",
    "FV2 Comdty",
    "TU2 Comdty",
    "US2 Comdty",
    "WN2 Comdty",
]

# OIS contracts
OIS_CONTRACTS = [
    "USSO1Z CMPN Curncy",
    "USSOA CMPN Curncy",
    "USSOB CMPN Curncy",
    "USSOC CMPN Curncy",
    "USSOF CMPN Curncy",
    "USSO1 CMPN Curncy",
    "USSO2 CMPN Curncy",
    "USSO3 CMPN Curncy",
    "USSO4 CMPN Curncy",
]

# Futures snapshot fields
FUTURES_FIELDS_LATEST = [
    "PX_LAST",
    "PX_VOLUME",
    "CURRENT_CONTRACT_MONTH_YR",
    "FUT_IMPLIED_REPO_RT",
    "FUT_DLV_DT_FIRST",
    "FUT_DLV_DT_LAST",
    "FUT_CONT_SIZE",
    "FUT_TICK_SIZE",
    "FUT_VAL_PT",
    "FUT_CTD_ISIN",
    "FUT_CTD_CUSIP",
    "FUT_CTD_ID_BB_GLOBAL",
]

# OIS snapshot fields
OIS_FIELDS_LATEST = [
    "PX_LAST",
]

# Bond snapshot fields (for CTDs if resolved)
BOND_FIELDS_LATEST = [
    "PX_LAST",
    "ACCRUED_INT",
    "CPN",
    "CPN_FREQ",
    "DAY_CNT_DES",
    "NXT_CPN_DT",
    "PRV_CPN_DT",
    "MATURITY",
    "ISSUE_DT",
]


def _coerce_bdp(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    xbbg blp.bdp(ticker, fields) returns a DataFrame indexed by field,
    with one column named by ticker.
    Convert to a 1-row DataFrame with MultiIndex columns: (ticker, field).
    """
    if df is None or df.empty:
        cols = pd.MultiIndex.from_product([[ticker], []])
        return pd.DataFrame(index=[0], columns=cols)

    # Ensure one column exists; xbbg usually uses the ticker as the column label
    col = df.columns[0]
    s = df[col]
    out = pd.DataFrame([s.to_dict()])
    out.columns = pd.MultiIndex.from_product([[ticker], out.columns.tolist()])
    return out


def pull_latest_snapshots() -> pd.DataFrame:
    from xbbg import blp

    frames = []

    # ---- Futures snapshots ----
    for fut in FUTURES_CONTRACTS:
        snap = blp.bdp(fut, FUTURES_FIELDS_LATEST)
        frames.append(_coerce_bdp(snap, fut))

    # ---- OIS snapshots ----
    for ois in OIS_CONTRACTS:
        snap = blp.bdp(ois, OIS_FIELDS_LATEST)
        frames.append(_coerce_bdp(snap, ois))

    # ---- Resolve CTD bonds and pull bond snapshots ----
    ctd_id_map = {}
    for fut in FUTURES_CONTRACTS:
        try:
            ctd = blp.bdp(fut, ["FUT_CTD_ID_BB_GLOBAL", "FUT_CTD_ISIN", "FUT_CTD_CUSIP"])
            # indexed by field, one column
            col = ctd.columns[0]
            ctd_global = ctd.loc["FUT_CTD_ID_BB_GLOBAL", col] if "FUT_CTD_ID_BB_GLOBAL" in ctd.index else None
            ctd_isin = ctd.loc["FUT_CTD_ISIN", col] if "FUT_CTD_ISIN" in ctd.index else None
            ctd_cusip = ctd.loc["FUT_CTD_CUSIP", col] if "FUT_CTD_CUSIP" in ctd.index else None

            chosen = ctd_global
            if pd.isna(chosen) or chosen is None or str(chosen).strip() == "":
                chosen = ctd_isin
            if pd.isna(chosen) or chosen is None or str(chosen).strip() == "":
                chosen = ctd_cusip

            if chosen is not None and pd.notna(chosen) and str(chosen).strip() != "":
                ctd_id_map[fut] = str(chosen).strip()
        except Exception:
            continue

    # Convert identifiers to bond tickers (heuristic: "<ID> Govt")
    ctd_bonds = sorted({f"{ident} Govt" for ident in ctd_id_map.values()})

    for bond in ctd_bonds:
        try:
            snap = blp.bdp(bond, BOND_FIELDS_LATEST)
            frames.append(_coerce_bdp(snap, bond))
        except Exception:
            # If a heuristic ticker fails, skip
            continue

    # ---- Combine into one row ----
    out = pd.concat(frames, axis=1)
    out.index = ["LATEST"]  # single-row label
    return out


if __name__ == "__main__":
    df_latest = pull_latest_snapshots()

    # Write snapshot to parquet + csv for quick inspection
    out_csv = DATA_DIR / "bloomberg_latest_snapshot.csv"

    df_latest.to_csv(out_csv)

    print(f"Wrote: {out_csv}")
    print(df_latest.iloc[:, :10])  # small preview