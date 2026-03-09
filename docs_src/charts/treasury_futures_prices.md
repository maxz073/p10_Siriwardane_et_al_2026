
**Description:** This chart shows the replicated Treasury spot-futures arbitrage spread in basis points for the 2Y, 5Y, 10Y, 20Y, and 30Y tenors. The spread is defined as implied repo minus interpolated OIS at the tenor-specific holding period.

**Relevance for Financial Markets:** The spread measures relative-value dislocations between Treasury cash and futures markets. It is useful for:
- Tracking arbitrage pressure across maturities
- Comparing mispricing intensity across tenors
- Studying market segmentation and funding stress
- Monitoring how financing conditions map into futures basis

**Direction of Risk:** A higher spread means implied repo is richer than the matched OIS financing benchmark; a lower or negative spread indicates less attractive (or reversed) basis opportunities.

**Formulas Used:** Spread \(=\) Implied Repo \(-\) Interpolated OIS (both in bps).

**Data Cleaning Information:** Input rows require positive futures volume and non-missing futures/CTD fields. Delivery windows are inferred from contract month, implied repo is computed for first and last delivery, and the maximum is retained before subtracting interpolated OIS.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It is the final replication deliverable and directly summarizes the arbitrage signal across the full tenor curve in one panel.
