"""
This module loads Treasury futures data from Bloomberg.

You must have a Bloomberg terminal open on this computer to run. You must
first install xbbg
"""

from pathlib import Path

import pandas as pd

from settings import config

DATA_DIR = config("DATA_DIR")
START_DATE = config("START_DATE")
END_DATE = config("END_DATE")

# Treasury futures contracts
FUTURES_CONTRACTS = [
    "TY1 Comdty",  # 10-year Note First Generic
    "FV1 Comdty",  # 5-year Note First Generic
    "TU1 Comdty",  # 2-year Note First Generic
    "US1 Comdty",  # 30-year Bond First Generic
    "WN1 Comdty",  # Ultra 10-year Note First Generic
    "TY2 Comdty",  # 10-year Note Second Generic
    "FV2 Comdty",  # 5-year Note Second Generic
    "TU2 Comdty",  # 2-year Note Second Generic
    "US2 Comdty",  # 30-year Bond Second Generic
    "WN2 Comdty",  # Ultra 10-year Note Second Generic
]

# Fields to pull (futures)
# Note: Some fields may not be populated for all generics/contracts; that's OK.
FUTURES_FIELDS = [
    # Already pulling
    "FUT_IMPLIED_REPO_RT",
    "PX_VOLUME",
    "CURRENT_CONTRACT_MONTH_YR",
    "PX_LAST",

    # Delivery / settlement inputs (used later to compute d1, etc.)
    "FUT_DLV_DT_FIRST",
    "FUT_DLV_DT_LAST",

    # Useful contract mechanics / diagnostics
    "FUT_CONT_SIZE",
    "FUT_TICK_SIZE",
    "FUT_VAL_PT",

    # CTD / delivery basket identifiers (used later to pull bond-level vars)
    # Availability varies by contract and by generic vs specific.
    "FUT_CTD_ISIN",
    "FUT_CTD_CUSIP",
    "FUT_CTD_ID_BB_GLOBAL",
]

# If you'd like basket-level IDs later, this is where you'd add:
# "FUT_DELIV_BASKET" (often better accessed via DES/CTD screens than bdh)

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

OIS_FIELDS = [
    "PX_LAST",
]

# Bond fields (for CTD bonds if we can resolve them)
# These are the "raw ingredients" for Ab, Ae (later), Ic (later), and coupon timing.
BOND_FIELDS = [
    "PX_LAST",        # Clean price P
    "ACCRUED_INT",    # Accrued interest today Ab
    "CPN",            # Coupon rate
    "CPN_FREQ",       # Coupon frequency
    "DAY_CNT_DES",    # Day count convention descriptor
    "NXT_CPN_DT",     # Next coupon date
    "PRV_CPN_DT",     # Previous coupon date
    "MATURITY",       # Maturity date
    "ISSUE_DT",       # Issue date (optional but useful)
]


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure columns are a proper MultiIndex of (ticker, field).
    xbbg bdh typically already returns MultiIndex columns; this is defensive.
    """
    if isinstance(df.columns, pd.MultiIndex):
        return df
    # If it's single-index, promote to multiindex using a placeholder ticker.
    df.columns = pd.MultiIndex.from_product([["UNKNOWN"], df.columns])
    return df


def pull_bbg_data(end_date=END_DATE):
    """
    Pull Bloomberg data for Treasury futures + OIS.
    Additionally pulls CTD bond fields when CTD identifiers are available.

    Returns a DataFrame with MultiIndex columns: (ticker, field).
    """
    from xbbg import blp  # keep import here so module import doesn't require Bloomberg

    data_frames = []

    # ---- Futures pulls ----
    for contract in FUTURES_CONTRACTS:
        contract_data = blp.bdh(contract, FUTURES_FIELDS, START_DATE, end_date)
        contract_data = _flatten_columns(contract_data)
        data_frames.append(contract_data)

    # ---- OIS pulls ----
    for contract in OIS_CONTRACTS:
        contract_data = blp.bdh(contract, OIS_FIELDS, START_DATE, end_date)
        contract_data = _flatten_columns(contract_data)
        data_frames.append(contract_data)

    # ---- Try to resolve CTD bonds and pull bond-level fields ----
    # We first query CTD identifiers as of "end_date" using bdp (point-in-time),
    # because CTD may not be stable and bdh for CTD id fields can be sparse on generics.
    ctd_ids = {}
    for fut in FUTURES_CONTRACTS:
        try:
            ctd = blp.bdp(
                fut,
                [
                    "FUT_CTD_ISIN",
                    "FUT_CTD_CUSIP",
                    "FUT_CTD_ID_BB_GLOBAL",
                ],
            )
            # bdp returns a DataFrame indexed by field name
            # Prefer BBG GLOBAL, then ISIN, then CUSIP (format varies)
            ctd_global = None
            ctd_isin = None
            ctd_cusip = None

            if "FUT_CTD_ID_BB_GLOBAL" in ctd.index:
                ctd_global = ctd.loc["FUT_CTD_ID_BB_GLOBAL"].values[0]
            if "FUT_CTD_ISIN" in ctd.index:
                ctd_isin = ctd.loc["FUT_CTD_ISIN"].values[0]
            if "FUT_CTD_CUSIP" in ctd.index:
                ctd_cusip = ctd.loc["FUT_CTD_CUSIP"].values[0]

            chosen = ctd_global or ctd_isin or ctd_cusip
            if pd.notna(chosen) and str(chosen).strip() != "":
                ctd_ids[fut] = chosen
        except Exception:
            # If Bloomberg can't resolve CTD for this contract, skip silently
            continue

    # Pull bond-level timeseries for any CTDs we resolved.
    # We map IDs to Bloomberg bond tickers where possible:
    # - ISIN/CUSIP can often be used directly with "Govt"
    # - BBG Global ID sometimes needs a suffix; if it fails, user can adjust later.
    ctd_bond_tickers = []
    for fut, ident in ctd_ids.items():
        s = str(ident).strip()

        # Heuristics:
        # - ISIN typically starts with 'US' and length 12
        # - CUSIP length 9
        # We'll attempt the common Bloomberg format "<identifier> Govt"
        if len(s) in (9, 12) or s.startswith("US"):
            ctd_bond_tickers.append(f"{s} Govt")
        else:
            # fallback attempt: still try "<id> Govt"
            ctd_bond_tickers.append(f"{s} Govt")

    ctd_bond_tickers = sorted(set(ctd_bond_tickers))

    if ctd_bond_tickers:
        try:
            bond_df = blp.bdh(ctd_bond_tickers, BOND_FIELDS, START_DATE, end_date)
            bond_df = _flatten_columns(bond_df)
            data_frames.append(bond_df)
        except Exception:
            # If the heuristic tickers fail, we still return futures/OIS pulls.
            pass

    # ---- Concatenate all data along columns ----
    bbg_df = pd.concat(data_frames, axis=1)
    bbg_df.index.name = "Date"
    return bbg_df


if __name__ == "__main__":
    df = pull_bbg_data(end_date=END_DATE)
    path = Path(DATA_DIR) / "bloomberg.parquet"
    df.to_parquet(path)
