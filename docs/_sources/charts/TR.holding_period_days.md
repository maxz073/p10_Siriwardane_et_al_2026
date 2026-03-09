---
date: 2026-03-09 13:01:28
tags: Bloomberg Terminal
category: Treasury Futures, Arbitrage, Holding Period
---

# Chart: Holding Period Days by Tenor
Tenor-specific holding period in days implied by winning delivery choice in IRR construction.

## Chart
```{raw} html
<iframe src="../_static/TR/holding_period_days.html" height="500px" width="100%"></iframe>

<p style="text-align: center;">Sources: Bloomberg Terminal</p>
```
[Full Screen Chart](../download_chart/TR/holding_period_days.html)





**Description:** This chart shows holding period days by tenor, where holding period is determined by the delivery date (first vs last delivery window) that maximizes implied repo.

**Relevance for Financial Markets:** Holding period length determines which point of the OIS curve is relevant for financing and therefore directly affects spread measurement.

**Direction of Risk:** Longer holding periods typically map to longer-tenor OIS inputs; spread sensitivity can shift as holding periods change through time.

**Formulas Used:** Holding period days are computed from settlement (T+1 business day) to the selected delivery date.

**Data Cleaning Information:** Tenor-level series come from the implied repo computation step and are plotted after date alignment.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It explains a key mechanical channel behind spread movements that is not visible in price-only charts.



## Chart Specs

| Chart Name             | Holding Period Days by Tenor                                             |
|------------------------|------------------------------------------------------------|
| Chart ID               | holding_period_days                                               |
| Topic Tags             | Treasury Futures, Arbitrage, Holding Period                                |
| Data Series Start Date | 2010-01-01                                 |
| Data Frequency         | Daily                                         |
| Observation Period     | Weekday                                     |
| Lag in Data Release    | One day                                    |
| Data Release Timing    |                                     |
| Seasonal Adjustment    | None                                    |
| Units                  | Days                                                  |
| Data Series            | 2, Y, ,,  , 5, Y, ,,  , 1, 0, Y, ,,  , 2, 0, Y, ,,  , 3, 0, Y,  , h, o, l, d, i, n, g,  , p, e, r, i, o, d,  , d, a, y, s                                            |
| HTML Chart             | [HTML](../download_chart/TR/holding_period_days.html)    |


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

