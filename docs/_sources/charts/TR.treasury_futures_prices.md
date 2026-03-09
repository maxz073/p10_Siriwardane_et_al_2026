---
date: 2026-03-08 22:13:16
tags: Bloomberg Terminal
category: Treasury Futures, Arbitrage, Fixed Income, Spreads
---

# Chart: Arbitrage Spreads by Tenor
Time series of Treasury spot-futures arbitrage spreads for 2Y, 5Y, 10Y, 20Y, and 30Y tenors.

## Chart
```{raw} html
<iframe src="../_static/TR/treasury_futures_prices.html" height="500px" width="100%"></iframe>

<p style="text-align: center;">Sources: Bloomberg Terminal</p>
```
[Full Screen Chart](../download_chart/TR/treasury_futures_prices.html)






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



## Chart Specs

| Chart Name             | Arbitrage Spreads by Tenor                                             |
|------------------------|------------------------------------------------------------|
| Chart ID               | treasury_futures_prices                                               |
| Topic Tags             | Treasury Futures, Arbitrage, Fixed Income, Spreads                                |
| Data Series Start Date | 2010-01-01                                 |
| Data Frequency         | Daily                                         |
| Observation Period     | Weekday                                     |
| Lag in Data Release    | One day                                    |
| Data Release Timing    |                                     |
| Seasonal Adjustment    | None                                    |
| Units                  | Basis Points                                                  |
| Data Series            | 2, Y, ,,  , 5, Y, ,,  , 1, 0, Y, ,,  , 2, 0, Y, ,,  , 3, 0, Y,  , a, r, b, i, t, r, a, g, e,  , s, p, r, e, a, d, s                                            |
| HTML Chart             | [HTML](../download_chart/TR/treasury_futures_prices.html)    |


## Dataframe Manifest

| Dataframe Name                 | Bloomberg Treasury Futures and OIS Data                                                   |
|--------------------------------|--------------------------------------------------------------------------------------|
| Dataframe ID                   | [bloomberg](../dataframes/TR/bloomberg.md)                                       |
| Data Sources                   | Bloomberg Terminal                                        |
| Data Providers                 | Bloomberg L.P.                                      |
| Links to Providers             | https://www.bloomberg.com/professional/solution/bloomberg-terminal/                             |
| Topic Tags                     | Treasury Futures, Interest Rate Swaps, Ois, Fixed Income                                          |
| Type of Data Access            | P,r,o,p,r,i,e,t,a,r,y                                  |
| How is data pulled?            | Bloomberg Terminal API via Python (xbbg package)                                                    |
| Data available up to (min)     |                                                              |
| Data available up to (max)     |                                                              |
| Dataframe Path                 | /mnt/c/Users/George/Documents/GitHub/p10_Siriwardane_et_al_2026/_data/bloomberg.parquet                                                   |


**Linked Charts:**


- [TR:treasury_futures_prices](../../charts/TR.treasury_futures_prices.md)



## Pipeline Manifest

| Pipeline Name                   | Treasury Spot-Futures                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [TR](../index.md)              |
| Lead Pipeline Developer         | George Lord, Max Zhalilo             |
| Contributors                    | George Lord, Max Zhalilo           |
| Git Repo URL                    |                         |
| Pipeline Web Page               | <a href="file:///mnt/c/Users/George/Documents/GitHub/p10_Siriwardane_et_al_2026/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-03-08 22:13:16           |
| OS Compatibility                |  |
| Linked Dataframes               |  [TR:bloomberg](../dataframes/TR/bloomberg.md)<br>  |

