---
date: 2026-03-09 13:01:28
tags: Bloomberg Terminal
category: Treasury Futures, Fixed Income, Prices
---

# Chart: Underlying Treasury Futures Prices by Tenor
Second-deferred Treasury futures prices for 2Y, 5Y, 10Y, 20Y, and 30Y contracts.

## Chart
```{raw} html
<iframe src="../_static/TR/underlying_futures_prices.html" height="500px" width="100%"></iframe>

<p style="text-align: center;">Sources: Bloomberg Terminal</p>
```
[Full Screen Chart](../download_chart/TR/underlying_futures_prices.html)





**Description:** This chart shows the underlying second-deferred Treasury futures prices used in implied repo construction for 2Y, 5Y, 10Y, 20Y, and 30Y tenors.

**Relevance for Financial Markets:** These series are the direct futures-leg inputs to the arbitrage spread calculation and provide context for cross-tenor market behavior.

**Direction of Risk:** This is an input-level chart; it is mainly descriptive and does not by itself indicate arbitrage sign.

**Formulas Used:** N/A. Direct Bloomberg futures prices (`PX_LAST`) by tenor.

**Data Cleaning Information:** Series are extracted from the Bloomberg parquet and plotted on a common date index.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It shows the exact futures price inputs underlying the spread and helps verify data coverage and continuity by tenor.



## Chart Specs

| Chart Name             | Underlying Treasury Futures Prices by Tenor                                             |
|------------------------|------------------------------------------------------------|
| Chart ID               | underlying_futures_prices                                               |
| Topic Tags             | Treasury Futures, Fixed Income, Prices                                |
| Data Series Start Date | 2010-01-01                                 |
| Data Frequency         | Daily                                         |
| Observation Period     | Weekday                                     |
| Lag in Data Release    | One day                                    |
| Data Release Timing    |                                     |
| Seasonal Adjustment    | None                                    |
| Units                  | Price                                                  |
| Data Series            | 2, Y, ,,  , 5, Y, ,,  , 1, 0, Y, ,,  , 2, 0, Y, ,,  , 3, 0, Y,  , f, u, t, u, r, e, s,  , p, r, i, c, e, s                                            |
| HTML Chart             | [HTML](../download_chart/TR/underlying_futures_prices.html)    |


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
| Dataframe Path                 | /Users/maxzhalilo/Finm/Finm-329/p10_Siriwardane_et_al_2026/_data/bloomberg.parquet                                                   |
| Download Data as Parquet       | [Parquet](../../download_dataframe/TR/bloomberg.parquet)         |
| Download Data as Excel         | [Excel](../../download_dataframe/TR/bloomberg.xlsx)              |
| Linked Charts                  |   [TR:treasury_futures_prices](../../charts/TR.treasury_futures_prices.md)<br>  [TR:underlying_futures_prices](../../charts/TR.underlying_futures_prices.md)<br>  [TR:ois_input_rates](../../charts/TR.ois_input_rates.md)<br>  [TR:holding_period_days](../../charts/TR.holding_period_days.md)<br>  [TR:implied_repo_vs_interpolated_ois](../../charts/TR.implied_repo_vs_interpolated_ois.md)<br>   |

## Pipeline Manifest

| Pipeline Name                   | Treasury Spot-Futures                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [TR](../index.md)              |
| Lead Pipeline Developer         | George Lord, Max Zhalilo             |
| Contributors                    | George Lord, Max Zhalilo           |
| Git Repo URL                    |                         |
| Pipeline Web Page               | <a href="file:///Users/maxzhalilo/Finm/Finm-329/p10_Siriwardane_et_al_2026/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-03-09 13:01:28           |
| OS Compatibility                |  |
| Linked Dataframes               |  [TR:bloomberg](../dataframes/TR/bloomberg.md)<br>  |

