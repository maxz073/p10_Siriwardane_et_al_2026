# Dataframe: `TR:bloomberg` - Bloomberg Treasury Futures and OIS Data


## Description

This dataframe contains Treasury futures contracts data and Overnight Index Swap (OIS) rates pulled from Bloomberg Terminal. The dataset includes first and second generic futures contracts across multiple maturities (2-year, 5-year, 10-year, 30-year, and Ultra 10-year Treasury notes/bonds), along with various OIS rates.

The data provides key pricing information, trading volumes, implied repo rates, and contract expiration details that are essential for analyzing Treasury futures markets and interest rate dynamics.

## Data Dictionary

### Treasury Futures Contracts
- **TY1 Comdty**: 10-Year Note First Generic Contract
- **FV1 Comdty**: 5-Year Note First Generic Contract
- **TU1 Comdty**: 2-Year Note First Generic Contract
- **US1 Comdty**: 30-Year Bond First Generic Contract
- **WN1 Comdty**: Ultra 10-Year Note First Generic Contract
- **TY2 Comdty**: 10-Year Note Second Generic Contract
- **FV2 Comdty**: 5-Year Note Second Generic Contract
- **TU2 Comdty**: 2-Year Note Second Generic Contract
- **US2 Comdty**: 30-Year Bond Second Generic Contract
- **WN2 Comdty**: Ultra 10-Year Note Second Generic Contract

### Fields per Contract
- **FUT_IMPLIED_REPO_RT**: `float64` - The implied repo rate embedded in the futures contract
- **PX_VOLUME**: `float64` - Trading volume for the contract
- **CURRENT_CONTRACT_MONTH_YR**: `object` - The expiration month and year of the current contract
- **PX_Last**: `float64` - Last traded price of the futures contract

### OIS Contracts
- **USSO1Z CMPN Curncy**: Overnight OIS
- **USSOA CMPN Curncy**: 1-Week OIS
- **USSOB CMPN Curncy**: 2-Week OIS
- **USSOC CMPN Curncy**: 3-Week OIS
- **USSOF CMPN Curncy**: 1-Month OIS
- **USSO1 CMPN Curncy**: 1-Year OIS
- **USSO2 CMPN Curncy**: 2-Year OIS
- **USSO3 CMPN Curncy**: 3-Year OIS
- **USSO4 CMPN Curncy**: 4-Year OIS

### OIS Fields
- **PX_Last**: `float64` - Last traded OIS rate

## Data Source

Data is pulled from Bloomberg Terminal using the `xbbg` Python package via the `blp.bdh()` function for historical data downloads.



## DataFrame Glimpse

```
Rows: 521
Columns: 50
$ ('TY1 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('TY1 Comdty', 'px_volume')                  <f64> None
$ ('TY1 Comdty', 'current_contract_month_yr')  <str> None
$ ('TY1 Comdty', 'px_last')                    <f64> None
$ ('FV1 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('FV1 Comdty', 'px_volume')                  <f64> None
$ ('FV1 Comdty', 'current_contract_month_yr')  <str> None
$ ('FV1 Comdty', 'px_last')                    <f64> None
$ ('TU1 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('TU1 Comdty', 'px_volume')                  <f64> None
$ ('TU1 Comdty', 'current_contract_month_yr')  <str> None
$ ('TU1 Comdty', 'px_last')                    <f64> None
$ ('US1 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('US1 Comdty', 'px_volume')                  <f64> None
$ ('US1 Comdty', 'current_contract_month_yr')  <str> None
$ ('US1 Comdty', 'px_last')                    <f64> None
$ ('WN1 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('WN1 Comdty', 'px_volume')                  <f64> None
$ ('WN1 Comdty', 'current_contract_month_yr')  <str> None
$ ('WN1 Comdty', 'px_last')                    <f64> None
$ ('TY2 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('TY2 Comdty', 'px_volume')                  <f64> None
$ ('TY2 Comdty', 'current_contract_month_yr')  <str> None
$ ('TY2 Comdty', 'px_last')                    <f64> None
$ ('FV2 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('FV2 Comdty', 'current_contract_month_yr')  <str> None
$ ('FV2 Comdty', 'px_last')                    <f64> None
$ ('FV2 Comdty', 'px_volume')                  <f64> None
$ ('TU2 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('TU2 Comdty', 'current_contract_month_yr')  <str> None
$ ('TU2 Comdty', 'px_last')                    <f64> None
$ ('TU2 Comdty', 'px_volume')                  <f64> None
$ ('US2 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('US2 Comdty', 'px_volume')                  <f64> None
$ ('US2 Comdty', 'current_contract_month_yr')  <str> None
$ ('US2 Comdty', 'px_last')                    <f64> None
$ ('WN2 Comdty', 'fut_implied_repo_rt')        <f64> None
$ ('WN2 Comdty', 'current_contract_month_yr')  <str> None
$ ('WN2 Comdty', 'px_last')                    <f64> None
$ ('WN2 Comdty', 'px_volume')                  <f64> None
$ ('USSO1Z CMPN Curncy', 'px_last')            <f64> None
$ ('USSOA CMPN Curncy', 'px_last')             <f64> 0.113
$ ('USSOB CMPN Curncy', 'px_last')             <f64> 0.115
$ ('USSOC CMPN Curncy', 'px_last')             <f64> 0.124
$ ('USSOF CMPN Curncy', 'px_last')             <f64> 0.148
$ ('USSO1 CMPN Curncy', 'px_last')             <f64> 0.226
$ ('USSO2 CMPN Curncy', 'px_last')             <f64> 0.634
$ ('USSO3 CMPN Curncy', 'px_last')             <f64> 1.172
$ ('USSO4 CMPN Curncy', 'px_last')             <f64> 1.638
$ Date                                        <date> 2011-04-22


```

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
| Data available up to (min)     | 2011-12-30 00:00:00                                                             |
| Data available up to (max)     | 2011-12-30 00:00:00                                                             |
| Dataframe Path                 | /Users/maxzhalilo/Finm/Finm-329/p10_Siriwardane_et_al_2026/treasury_spot_futures/_data/bloomberg.parquet                                                   |
| Download Data as Parquet       | [Parquet](../../download_dataframe/TR/bloomberg.parquet)         |
| Download Data as Excel         | [Excel](../../download_dataframe/TR/bloomberg.xlsx)              |
| Linked Charts                  |   [TR:treasury_futures_prices](../../charts/TR.treasury_futures_prices.md)<br>   |

## Pipeline Manifest

| Pipeline Name                   | Treasury Spot-Futures                       |
|---------------------------------|--------------------------------------------------------|
| Pipeline ID                     | [TR](../index.md)              |
| Lead Pipeline Developer         | George Lord, Max Zhalilo             |
| Contributors                    | George Lord, Max Zhalilo           |
| Git Repo URL                    |                         |
| Pipeline Web Page               | <a href="file:///Users/maxzhalilo/Finm/Finm-329/p10_Siriwardane_et_al_2026/treasury_spot_futures/docs/index.html">Pipeline Web Page      |
| Date of Last Code Update        | 2026-02-05 20:09:42           |
| OS Compatibility                |  |
| Linked Dataframes               |  [TR:bloomberg](../dataframes/TR/bloomberg.md)<br>  |


