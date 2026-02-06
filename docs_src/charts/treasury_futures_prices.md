
**Description:** This chart visualizes the price movements of Treasury futures contracts across different maturities over time. It includes both first generic (most actively traded near-month) and second generic contracts for 2-year, 5-year, 10-year, 30-year Treasury notes/bonds, and Ultra 10-year notes. The interactive chart allows users to compare price trends across different maturities and contract series.

**Relevance for Financial Markets:** Treasury futures prices reflect market expectations about future interest rates and economic conditions. Price movements in these contracts are crucial for:
- Hedging interest rate risk
- Speculating on interest rate movements
- Understanding yield curve dynamics
- Assessing market sentiment about future Fed policy

**Direction of Risk:** Rising futures prices indicate falling expected yields (positive market sentiment), while falling prices indicate rising expected yields (negative sentiment or expectations of Fed tightening).

**Formulas Used:** N/A - Direct price data from Bloomberg Terminal.

**Data Cleaning Information:** The chart uses the `PX_Last` field from Bloomberg, which represents the last traded price for each futures contract. Data is filtered to remove NaN values before plotting.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** This chart provides a comprehensive view across multiple maturities and contract series simultaneously, allowing for:
1. Cross-maturity comparisons to understand yield curve shifts
2. Roll dynamics by comparing first vs second generic contracts
3. Identification of relative value opportunities across the curve
4. Assessment of market liquidity and trading patterns
