**Description:** This chart shows holding period days by tenor, where holding period is determined by the delivery date (first vs last delivery window) that maximizes implied repo.

**Relevance for Financial Markets:** Holding period length determines which point of the OIS curve is relevant for financing and therefore directly affects spread measurement.

**Direction of Risk:** Longer holding periods typically map to longer-tenor OIS inputs; spread sensitivity can shift as holding periods change through time.

**Formulas Used:** Holding period days are computed from settlement (T+1 business day) to the selected delivery date.

**Data Cleaning Information:** Tenor-level series come from the implied repo computation step and are plotted after date alignment.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It explains a key mechanical channel behind spread movements that is not visible in price-only charts.
