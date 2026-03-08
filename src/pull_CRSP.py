"""Pull and load CRSP Treasury Data from WRDS for Treasury futures IRR work.

Reference:
    CRSP US TREASURY DATABASE GUIDE
    https://www.crsp.org/wp-content/uploads/guides/CRSP_US_Treasury_Database_Guide_for_SAS_ASCII_EXCEL_R.pdf

Purpose:
    Pull the bond-side inputs needed for Treasury futures implied repo rate (IRR):
    - clean price of the bond
    - accrued interest at the beginning (quote date)
    - coupon rate
    - coupon frequency
    - previous coupon date
    - next coupon date
    - day count basis / accrual basis

Notes:
    - CRSP does NOT explicitly provide coupon frequency or coupon date schedule fields
      in tfz_dly / tfz_iss. For Treasury notes and bonds, we assume:
          coupon_frequency = 2
          day_count_basis = "ACT/ACT"
    - Accrued interest at the end (delivery date) is NOT directly stored in CRSP.
      It must be computed later once you merge in the futures delivery date from Bloomberg.
"""

from pathlib import Path

import pandas as pd
import wrds
from pandas.tseries.offsets import DateOffset

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
WRDS_USERNAME = config("WRDS_USERNAME")
END_DATE = pd.Timestamp(config("END_DATE"))


def _add_coupon_schedule_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Treasury coupon schedule fields needed for IRR work.

    Assumptions for U.S. Treasury notes/bonds:
    - Semiannual coupons
    - ACT/ACT accrual basis
    """
    df = df.copy()

    # Treasury notes/bonds pay semiannual coupons
    df["coupon_frequency"] = 2
    df["coupon_interval_months"] = 6
    df["day_count_basis"] = "ACT/ACT"

    # Compute previous and next coupon dates from maturity date
    # Coupon schedule runs backward from maturity in 6M steps.
    prev_coupon_dates = []
    next_coupon_dates = []

    for _, row in df.iterrows():
        caldt = row["caldt"]
        maturity = row["tmatdt"]

        if pd.isna(caldt) or pd.isna(maturity):
            prev_coupon_dates.append(pd.NaT)
            next_coupon_dates.append(pd.NaT)
            continue

        coupon_date = maturity

        # Step backward until coupon_date <= caldt
        while coupon_date > caldt:
            next_cd = coupon_date
            coupon_date = coupon_date - DateOffset(months=6)

        prev_cd = coupon_date
        next_cd = prev_cd + DateOffset(months=6)

        prev_coupon_dates.append(prev_cd)
        next_coupon_dates.append(next_cd)

    df["prev_coupon_date"] = pd.to_datetime(prev_coupon_dates)
    df["next_coupon_date"] = pd.to_datetime(next_coupon_dates)

    return df


def pull_CRSP_treasury_for_irr(
    start_date="1970-01-01",
    end_date="2025-12-31",
    wrds_username=WRDS_USERNAME,
    cusips=None,
):
    """
    Pull CRSP Treasury bond-side fields needed for implied repo calculations.

    Parameters
    ----------
    start_date : str
        Start date for CRSP quote dates.
    end_date : str
        End date for CRSP quote dates.
    wrds_username : str
        WRDS username.
    cusips : list[str] or None
        Optional list of Treasury CUSIPs to restrict the pull to CTD bonds only.

    Returns
    -------
    pd.DataFrame
        Daily bond-side data with:
        - tcusip
        - caldt
        - clean_price
        - accrued_interest_begin
        - dirty_price
        - coupon_rate
        - coupon_frequency
        - prev_coupon_date
        - next_coupon_date
        - day_count_basis
        - tdatdt
        - tmatdt
    """
    cusip_filter = ""
    if cusips:
        cusip_list = ", ".join([f"'{c}'" for c in cusips])
        cusip_filter = f"AND iss.tcusip IN ({cusip_list})"

    query = f"""
    SELECT
        -- identifiers
        tfz.kytreasno,
        tfz.kycrspid,
        iss.tcusip,

        -- dates
        tfz.caldt,
        iss.tdatdt,
        iss.tmatdt,

        -- raw CRSP pricing fields
        tfz.tdbid,
        tfz.tdask,
        tfz.tdaccint,
        tfz.tdyld,

        -- coupon info
        iss.tcouprt,
        iss.itype,

        -- derived prices
        ((tfz.tdbid + tfz.tdask) / 2.0) AS clean_price,
        (((tfz.tdbid + tfz.tdask) / 2.0) + tfz.tdaccint) AS dirty_price

    FROM
        crspm.tfz_dly AS tfz
    LEFT JOIN
        crspm.tfz_iss AS iss
    ON
        tfz.kytreasno = iss.kytreasno
        AND tfz.kycrspid = iss.kycrspid
    WHERE
        tfz.caldt BETWEEN '{start_date}' AND '{end_date}'
        AND iss.itype IN (1, 2)
        {cusip_filter}
    """

    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(query, date_cols=["caldt", "tdatdt", "tmatdt"])
    db.close()

    df = df.rename(
        columns={
            "tdaccint": "accrued_interest_begin",
            "tcouprt": "coupon_rate",
        }
    )

    df = _add_coupon_schedule_fields(df)

    # Reorder columns for readability
    ordered_cols = [
        "kytreasno",
        "kycrspid",
        "tcusip",
        "caldt",
        "tdatdt",
        "tmatdt",
        "clean_price",
        "accrued_interest_begin",
        "dirty_price",
        "coupon_rate",
        "coupon_frequency",
        "prev_coupon_date",
        "next_coupon_date",
        "day_count_basis",
        "tdbid",
        "tdask",
        "tdyld",
        "itype",
    ]
    df = df[ordered_cols].sort_values(["tcusip", "caldt"]).reset_index(drop=True)

    return df


def compute_accrued_interest_end(
    df: pd.DataFrame,
    delivery_date_col: str = "delivery_date",
) -> pd.DataFrame:
    """
    Compute accrued interest at the futures delivery date.

    This function expects the CRSP bond-side dataframe to already be merged with
    a delivery date from Bloomberg.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - coupon_rate
        - prev_coupon_date
        - next_coupon_date
        - delivery_date_col
    delivery_date_col : str
        Column name holding the chosen futures delivery date.

    Returns
    -------
    pd.DataFrame
        Original dataframe plus:
        - accrued_interest_end
        - coupon_cash_per_period
        - coupon_period_days
        - accrued_days_end
    """
    out = df.copy()

    # Treasury coupon per period, per 100 par
    out["coupon_cash_per_period"] = out["coupon_rate"] / out["coupon_frequency"]

    out["coupon_period_days"] = (
        pd.to_datetime(out["next_coupon_date"]) - pd.to_datetime(out["prev_coupon_date"])
    ).dt.days

    out["accrued_days_end"] = (
        pd.to_datetime(out[delivery_date_col]) - pd.to_datetime(out["prev_coupon_date"])
    ).dt.days

    out["accrued_interest_end"] = (
        out["coupon_cash_per_period"] * out["accrued_days_end"] / out["coupon_period_days"]
    )

    return out


def load_CRSP_treasury_for_irr(data_dir=DATA_DIR):
    path = data_dir / "TFZ_IRR.parquet"
    df = pd.read_parquet(path)
    df = df[df["caldt"] <= END_DATE]
    return df


if __name__ == "__main__":
    # Optional: restrict to your Bloomberg CTD cusips later
    df = pull_CRSP_treasury_for_irr(
        start_date="2025-01-01",
        end_date="2025-12-31",
        wrds_username=WRDS_USERNAME,
        cusips=None,
    )

    path = DATA_DIR / "TFZ_IRR.parquet"
    df.to_parquet(path)

    csv_path = DATA_DIR / "TFZ_IRR.csv"
    df.to_csv(csv_path, index=False)

    print(f"Wrote: {path}")
    print(f"Wrote: {csv_path}")
    print(df.head())