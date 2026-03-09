**Description:** This chart shows the OIS input rates used in spread construction (2M, 3M, and 6M tenors).

**Relevance for Financial Markets:** OIS serves as the financing benchmark in the spread decomposition, so these rates are critical for interpreting level shifts in the arbitrage spread.

**Direction of Risk:** Higher OIS rates raise the financing benchmark and mechanically reduce implied-repo-minus-OIS spreads, all else equal.

**Formulas Used:** OIS inputs are linearly interpolated to tenor-specific holding periods before conversion to bps.

**Data Cleaning Information:** The chart uses Bloomberg `PX_LAST` OIS series and aligns them on the normalized date index.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It isolates the financing leg of the spread and makes interpolation inputs transparent.
