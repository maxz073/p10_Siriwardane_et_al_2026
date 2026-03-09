---
date: 2026-03-09 15:25:06
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

- [TR:underlying_futures_prices](../../charts/TR.underlying_futures_prices.md)

- [TR:ois_input_rates](../../charts/TR.ois_input_rates.md)

- [TR:holding_period_days](../../charts/TR.holding_period_days.md)

- [TR:implied_repo_vs_interpolated_ois](../../charts/TR.implied_repo_vs_interpolated_ois.md)



## Pipeline Manifest

| Pipeline Name                   | Treasury Spot-Futures                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [TR](../index.md)              |
| Lead Pipeline Developer         | George Lord, Max Zhalilo             |
| Contributors                    | George Lord, Max Zhalilo           |
| Git Repo URL                    |                         |
| Pipeline Web Page               | <a href="file:///mnt/c/Users/George/Documents/GitHub/p10_Siriwardane_et_al_2026/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-03-09 15:25:06           |
| OS Compatibility                |  |
| Linked Dataframes               |  [TR:bloomberg](../dataframes/TR/bloomberg.md)<br>  |

