"""
This module loads Treasury futures data from Bloomberg.

You must have a Bloomberg terminal open on this computer to run. You must
first install xbbg
"""

from pathlib import Path
import pandas as pd
from settings import config

DATA_DIR = config("DATA_DIR")
START_DATE = "2010-01-01"
END_DATE = "2026-02-28"

FUTURES_CONTRACTS = [
    #"TY1 Comdty", "FV1 Comdty", "TU1 Comdty", "US1 Comdty", "WN1 Comdty",
    "TY2 Comdty", "FV2 Comdty", "TU2 Comdty", "US2 Comdty", "WN2 Comdty",
]

# Time-series fields (bdh)
FUTURES_FIELDS_BDH = [
    "FUT_IMPLIED_REPO_RT",
    "PX_VOLUME",
    "CURRENT_CONTRACT_MONTH_YR",
    "PX_LAST",                 # <- use consistent uppercase
    "FUT_CTD_CUSIP",           # this one DOES come through historically for you
    "FUT_CNVS_FACTOR",         # conversion factor (historical via bdh)
    #"FUT_DLV_DT_FIRST", # If this doesn't come through, we'll just take the first & last delivery dates as the first & last weekdays of the month.
    #"FUT_DLV_DT_LAST",
    #"FUT_CONT_SIZE",
    #"FUT_TICK_SIZE",
    #"FUT_VAL_PT",
    #"FUT_CTD_ISIN",
    #"FUT_CTD_ID_BB_GLOBAL",
]

# Reference/static-ish fields (bdp)
FUTURES_FIELDS_BDP = [
    #"FUT_DLV_DT_FIRST",
    #"FUT_DLV_DT_LAST",
    #"FUT_CONT_SIZE",
    #"FUT_TICK_SIZE",
    #"FUT_VAL_PT",
    #"FUT_CTD_ISIN",
    #"FUT_CTD_ID_BB_GLOBAL",
    # keep CUSIP too, for cross-checking snapshot vs time-series
    #"FUT_CTD_CUSIP",
    #"FUT_CNVS_FACTOR"
]

OIS_CONTRACTS = [
    "USSOB CMPN Curncy", "USSOC CMPN Curncy", "USSOD CMPN Curncy",
    "USSOE CMPN Curncy", "USSOF CMPN Curncy", "USSOI CMPN Curncy",
]
OIS_FIELDS = ["PX_LAST"]

# Bond fields for CTDs (bdh)
BOND_FIELDS_BDH = [
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


def _ensure_columns_ticker_field(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure MultiIndex columns are (ticker, field), i.e. [Future Name], [Field].
    If xbbg returns (field, ticker), swap levels so ticker is first.
    """
    if not isinstance(df.columns, pd.MultiIndex) or df.columns.nlevels != 2:
        return df
    lev0 = df.columns.get_level_values(0).astype(str)
    lev1 = df.columns.get_level_values(1).astype(str)
    # Ticker-like: contains " Comdty", " Curncy", or " Govt"
    def looks_like_ticker(arr):
        return any(
            " Comdty" in v or " Curncy" in v or " Govt" in v
            for v in arr[: min(3, len(arr))]  # sample first few
        )
    if looks_like_ticker(lev0):
        return df  # already (ticker, field)
    if looks_like_ticker(lev1):
        df = df.reorder_levels([1, 0], axis=1)
        df.columns.names = ["ticker", "field"]
        return df
    return df


def _bdp_to_row_multiindex(bdp_df: pd.DataFrame) -> pd.DataFrame:
    """
    xbbg blp.bdp(list_of_tickers, list_of_fields) returns a DataFrame
    indexed by field with columns=tickers.
    Convert to 1-row DataFrame with MultiIndex columns (ticker, field).
    """
    # bdp_df: index=fields, cols=tickers
    out = bdp_df.T  # index=tickers, columns=fields
    out.columns.name = "field"
    out.index.name = "ticker"
    out = out.stack().to_frame().T  # single row, columns MultiIndex (ticker, field) #It's dropping nas rn.
    out.columns = pd.MultiIndex.from_tuples(out.columns, names=["ticker", "field"])
    out.index = ["LATEST_REF"]
    return out


def _broadcast_row_to_index(row_df: pd.DataFrame, index: pd.Index) -> pd.DataFrame:
    """
    Take a 1-row DataFrame and broadcast values across a new date index.
    """
    broadcast = pd.DataFrame(
        [row_df.iloc[0].values] * len(index),
        index=index,
        columns=row_df.columns,
    )
    return broadcast


def pull_bbg_data(end_date=END_DATE, pull_ctd_bonds=True):
    """
    Pull Bloomberg data for Treasury futures contracts + OIS.
    Adds missing futures reference fields via bdp and broadcasts across dates.
    Optionally pulls CTD bond fields using historical FUT_CTD_CUSIP.
    """
    from xbbg import blp

    data_frames = []

    # ---- Futures bdh (time series) ----
    fut_bdh_frames = []
    for fut in FUTURES_CONTRACTS:
        fut_df = blp.bdh(fut, FUTURES_FIELDS_BDH, START_DATE, end_date)
        fut_bdh_frames.append(fut_df)
    fut_bdh = pd.concat(fut_bdh_frames, axis=1)
    fut_bdh = _ensure_columns_ticker_field(fut_bdh)
    data_frames.append(fut_bdh)

    # ---- Futures bdp (reference fields), broadcast across time index ----
    fut_bdp = blp.bdp(FUTURES_CONTRACTS, FUTURES_FIELDS_BDP)
    fut_bdp_row = _bdp_to_row_multiindex(fut_bdp)
    fut_bdp_broadcast = _broadcast_row_to_index(fut_bdp_row, fut_bdh.index)
    fut_bdp_broadcast = _ensure_columns_ticker_field(fut_bdp_broadcast)
    data_frames.append(fut_bdp_broadcast)

    # ---- OIS bdh ----
    ois_frames = []
    for ois in OIS_CONTRACTS:
        ois_df = blp.bdh(ois, OIS_FIELDS, START_DATE, end_date)
        ois_frames.append(ois_df)
    ois_bdh = pd.concat(ois_frames, axis=1)
    ois_bdh = _ensure_columns_ticker_field(ois_bdh)
    data_frames.append(ois_bdh)

    # ---- CTD bond pulls (optional) ----
    if pull_ctd_bonds:
        # Collect unique CUSIPs observed historically in FUT_CTD_CUSIP columns
        ctd_cols = [c for c in fut_bdh.columns if isinstance(c, tuple) and c[1].upper() == "FUT_CTD_CUSIP"]
        if ctd_cols:
            stacked = fut_bdh[ctd_cols].stack()
            # stack() can return DataFrame when multiple columns; ensure Series for .str
            if isinstance(stacked, pd.DataFrame):
                stacked = stacked.stack()
            cusips = (
                stacked.astype(str)
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA})
                .dropna()
                .unique()
                .tolist()
            )
            # Heuristic bond ticker format
            bond_tickers = sorted({f"{cusip} Govt" for cusip in cusips})

            if bond_tickers:
                bond_df = blp.bdh(bond_tickers, BOND_FIELDS_BDH, START_DATE, end_date)
                bond_df = _ensure_columns_ticker_field(bond_df)
                data_frames.append(bond_df)

    bbg_df = pd.concat(data_frames, axis=1)
    bbg_df = _ensure_columns_ticker_field(bbg_df)
    bbg_df.index.name = "Date"
    return bbg_df


if __name__ == "__main__":
    from xbbg import blp  # noqa: F401

    df = pull_bbg_data(end_date=END_DATE, pull_ctd_bonds=True)
    path = Path(DATA_DIR) / "bloomberg.parquet"
    df.to_parquet(path)
    df.to_csv(Path(DATA_DIR) / "bloomberg.csv")