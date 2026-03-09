**Description:** This chart shows the underlying second-deferred Treasury futures prices used in implied repo construction for 2Y, 5Y, 10Y, 20Y, and 30Y tenors.

**Relevance for Financial Markets:** These series are the direct futures-leg inputs to the arbitrage spread calculation and provide context for cross-tenor market behavior.

**Direction of Risk:** This is an input-level chart; it is mainly descriptive and does not by itself indicate arbitrage sign.

**Formulas Used:** N/A. Direct Bloomberg futures prices (`PX_LAST`) by tenor.

**Data Cleaning Information:** Series are extracted from the Bloomberg parquet and plotted on a common date index.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It shows the exact futures price inputs underlying the spread and helps verify data coverage and continuity by tenor.
