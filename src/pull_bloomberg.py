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

# Fields to pull
FUTURES_FIELDS = [
    "FUT_IMPLIED_REPO_RT",
    "PX_VOLUME",
    "CURRENT_CONTRACT_MONTH_YR",
    "PX_Last",
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

OIS_FIELDS = [
    "PX_Last",
]


def pull_bbg_data(end_date=END_DATE):
    """
    Pull Bloomberg data for Treasury futures contracts.
    
    Returns a DataFrame with MultiIndex columns (contract, field).
    """
    data_frames = []
    
    for contract in FUTURES_CONTRACTS:
        # Pull all fields for this contract
        contract_data = blp.bdh(contract, FUTURES_FIELDS, START_DATE, end_date)
        data_frames.append(contract_data)

    for contract in OIS_CONTRACTS:
        # Pull all fields for this contract
        contract_data = blp.bdh(contract, OIS_FIELDS, START_DATE, end_date)
        data_frames.append(contract_data)
    
    # Concatenate all data along columns
    bbg_df = pd.concat(data_frames, axis=1)
    bbg_df.index.name = "Date"
    
    return bbg_df


if __name__ == "__main__":
    from xbbg import blp

    df = pull_bbg_data(end_date=END_DATE)
    path = Path(DATA_DIR) / "bloomberg.parquet"
    df.to_parquet(path)
