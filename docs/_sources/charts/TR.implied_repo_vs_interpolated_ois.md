---
date: 2026-03-09 00:14:26
tags: Bloomberg Terminal
category: Treasury Futures, Arbitrage, Ois, Implied Repo
---

# Chart: Implied Repo vs Interpolated OIS by Tenor
Comparison of implied repo rates and interpolated OIS financing benchmark across tenors.

## Chart
```{raw} html
<iframe src="../_static/TR/implied_repo_vs_interpolated_ois.html" height="500px" width="100%"></iframe>

<p style="text-align: center;">Sources: Bloomberg Terminal</p>
```
[Full Screen Chart](../download_chart/TR/implied_repo_vs_interpolated_ois.html)





**Description:** This chart compares implied repo and interpolated OIS financing benchmarks by tenor over time.

**Relevance for Financial Markets:** It displays the two legs that define the arbitrage spread and helps identify whether spread moves are driven by futures/bond implied repo changes or by financing-rate moves.

**Direction of Risk:** A widening gap between implied repo and interpolated OIS indicates richer basis opportunities; narrowing gaps indicate reduced dislocation.

**Formulas Used:** Interpolated OIS is matched to tenor-specific holding period and compared directly with implied repo in bps.

**Data Cleaning Information:** Both series are aligned to common dates and computed from staged Bloomberg/CRSP-derived outputs.

**Relation to a chart in an OFR public monitor:** N/A

**What does this add that other charts might not?** It provides decomposition-level transparency for the spread rather than only the net result.



## Chart Specs

| Chart Name             | Implied Repo vs Interpolated OIS by Tenor                                             |
|------------------------|------------------------------------------------------------|
| Chart ID               | implied_repo_vs_interpolated_ois                                               |
| Topic Tags             | Treasury Futures, Arbitrage, Ois, Implied Repo                                |
| Data Series Start Date | 2010-01-01                                 |
| Data Frequency         | Daily                                         |
| Observation Period     | Weekday                                     |
| Lag in Data Release    | One day                                    |
| Data Release Timing    |                                     |
| Seasonal Adjustment    | None                                    |
| Units                  | Basis Points                                                  |
| Data Series            | I, m, p, l, i, e, d,  , r, e, p, o,  , a, n, d,  , i, n, t, e, r, p, o, l, a, t, e, d,  , O, I, S,  , b, y,  , t, e, n, o, r                                            |
| HTML Chart             | [HTML](../download_chart/TR/implied_repo_vs_interpolated_ois.html)    |


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
| Date of Last Code Update        | 2026-03-09 00:14:26           |
| OS Compatibility                |  |
| Linked Dataframes               |  [TR:bloomberg](../dataframes/TR/bloomberg.md)<br>  |

