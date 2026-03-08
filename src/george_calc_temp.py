







def calculate_implied_repo_rate(F, Cf, Ae, Ab, Ic, d1, d2, P):
    """
    Fabozzi's Fixed Income Handbook defines a formula for implied repo rate.
    It is defined as the return received by going long the basis (buying the cash bond, financed w/ repo rate to term)
    and going short the futures. The exact return is defined as

    [(F * CF + Ae + Ic - (P + Ab)) * 360] / ((d1 * (P + Ab)) - (Ic * d2))

    where

    - F = futures price
    - CF = conversion factor
    - Ae = accrued interest of the bond at the end
    - Ab = accrued interest of the bond at the beginning
    - Ic = interim coupons
    - d1 = number of days between settlement and delivery
    - d2 = number of days between interim coupon date and delivery
    - P = clean price of the bond

    Source: https://quant.stackexchange.com/questions/51415/implied-repo-rate-calculation-from-fabozzi
    """

    return ((F * Cf + Ae + Ic - (P + Ab)) * 360) / ((d1 * (P + Ab)) - (Ic * d2))

def determine_delivery_date(repo_rate, coupon_rate, fut_dlv_dt_first, fut_dlv_dt_last):
    """
    The delivery date is determined as follows:

    - If the cost to borrow the bond (repo rate) is higher than the bond coupon rate, then deliver ASAP (first delivery date).
    - If the cost to borrow the bond (repo rate) is lower than the bond coupon rate, then deliver at the end of the delivery period (last delivery date).
    
    Based on this, we either return "fut_dlv_dt_first" or "fut_dlv_dt_last", the string column name for the first and last delivery date, respectively, from the bloomberg data.

    Input map:
    - repo_rate: sourced from 
    """