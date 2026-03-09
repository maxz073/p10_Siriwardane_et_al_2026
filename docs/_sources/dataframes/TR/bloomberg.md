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
Rows: 4216
Columns: 388
$ ('TY2 Comdty', 'fut_implied_repo_rt')        <f64> null
$ ('TY2 Comdty', 'px_volume')                  <f64> null
$ ('TY2 Comdty', 'current_contract_month_yr')  <str> null
$ ('TY2 Comdty', 'px_last')                    <f64> null
$ ('TY2 Comdty', 'fut_ctd_cusip')              <str> null
$ ('TY2 Comdty', 'fut_cnvs_factor')            <f64> null
$ ('FV2 Comdty', 'fut_implied_repo_rt')        <f64> null
$ ('FV2 Comdty', 'current_contract_month_yr')  <str> null
$ ('FV2 Comdty', 'px_last')                    <f64> null
$ ('FV2 Comdty', 'fut_ctd_cusip')              <str> null
$ ('FV2 Comdty', 'fut_cnvs_factor')            <f64> null
$ ('FV2 Comdty', 'px_volume')                  <f64> null
$ ('TU2 Comdty', 'fut_implied_repo_rt')        <f64> null
$ ('TU2 Comdty', 'current_contract_month_yr')  <str> null
$ ('TU2 Comdty', 'px_last')                    <f64> null
$ ('TU2 Comdty', 'fut_ctd_cusip')              <str> null
$ ('TU2 Comdty', 'fut_cnvs_factor')            <f64> null
$ ('TU2 Comdty', 'px_volume')                  <f64> null
$ ('US2 Comdty', 'fut_implied_repo_rt')        <f64> null
$ ('US2 Comdty', 'px_volume')                  <f64> null
$ ('US2 Comdty', 'current_contract_month_yr')  <str> null
$ ('US2 Comdty', 'px_last')                    <f64> null
$ ('US2 Comdty', 'fut_ctd_cusip')              <str> null
$ ('US2 Comdty', 'fut_cnvs_factor')            <f64> null
$ ('WN2 Comdty', 'fut_implied_repo_rt')        <f64> null
$ ('WN2 Comdty', 'current_contract_month_yr')  <str> null
$ ('WN2 Comdty', 'px_last')                    <f64> null
$ ('WN2 Comdty', 'fut_ctd_cusip')              <str> null
$ ('WN2 Comdty', 'fut_cnvs_factor')            <f64> null
$ ('WN2 Comdty', 'px_volume')                  <f64> null
$ ('USSOB CMPN Curncy', 'px_last')             <f64> null
$ ('USSOC CMPN Curncy', 'px_last')             <f64> null
$ ('USSOD CMPN Curncy', 'px_last')             <f64> null
$ ('USSOE CMPN Curncy', 'px_last')             <f64> null
$ ('USSOF CMPN Curncy', 'px_last')             <f64> null
$ ('USSOI CMPN Curncy', 'px_last')             <f64> null
$ ('912810EV Govt', 'px_last')                 <f64> null
$ ('912810EW Govt', 'px_last')                 <f64> 100.302734375
$ ('912810EX Govt', 'px_last')                 <f64> 101.955078125
$ ('912810EY Govt', 'px_last')                 <f64> 102.67578125
$ ('912810EZ Govt', 'px_last')                 <f64> 103.583984375
$ ('912810FA Govt', 'px_last')                 <f64> 104.533203125
$ ('912810FB Govt', 'px_last')                 <f64> 104.7578125
$ ('912810FE Govt', 'px_last')                 <f64> 104.9140625
$ ('912810FF Govt', 'px_last')                 <f64> 104.62890625
$ ('912810FJ Govt', 'px_last')                 <f64> 108.46875
$ ('912810FM Govt', 'px_last')                 <f64> 110.265625
$ ('912810FT Govt', 'px_last')                 <f64> 103.3203125
$ ('912810PT Govt', 'px_last')                 <f64> 104.875
$ ('912810PU Govt', 'px_last')                 <f64> 107.1640625
$ ('912810PW Govt', 'px_last')                 <f64> 101.0234375
$ ('912810PX Govt', 'px_last')                 <f64> 102.0859375
$ ('912810QB Govt', 'px_last')                 <f64> 98.09375
$ ('912810QC Govt', 'px_last')                 <f64> 100.3203125
$ ('912810QE Govt', 'px_last')                 <f64> 101.2421875
$ ('912810QH Govt', 'px_last')                 <f64> 98.46875
$ ('912810QL Govt', 'px_last')                 <f64> 96.6484375
$ ('912810QN Govt', 'px_last')                 <f64> 101.9609375
$ ('912810QQ Govt', 'px_last')                 <f64> 97.5859375
$ ('912810QS Govt', 'px_last')                 <f64> 90.2890625
$ ('912810QT Govt', 'px_last')                 <f64> 82.8359375
$ ('912810QU Govt', 'px_last')                 <f64> 82.4140625
$ ('912810RC Govt', 'px_last')                 <f64> 86.484375
$ ('912810RD Govt', 'px_last')                 <f64> 87.7890625
$ ('912810RE Govt', 'px_last')                 <f64> 86.0078125
$ ('912810RG Govt', 'px_last')                 <f64> 82.6875
$ ('912810RH Govt', 'px_last')                 <f64> 79.3125
$ ('912810RJ Govt', 'px_last')                 <f64> 77.4921875
$ ('912810RM Govt', 'px_last')                 <f64> 77.09375
$ ('912810RN Govt', 'px_last')                 <f64> 75.140625
$ ('912810RP Govt', 'px_last')                 <f64> 76.53125
$ ('912810RV Govt', 'px_last')                 <f64> 75.4140625
$ ('912810RX Govt', 'px_last')                 <f64> 75.21875
$ ('912810RY Govt', 'px_last')                 <f64> 71.5703125
$ ('912810SA Govt', 'px_last')                 <f64> 74.5625
$ ('912810SC Govt', 'px_last')                 <f64> 76.1171875
$ ('912810SE Govt', 'px_last')                 <f64> 79.2734375
$ ('912810SF Govt', 'px_last')                 <f64> 73.828125
$ ('912810SH Govt', 'px_last')                 <f64> 71.8984375
$ ('912810SJ Govt', 'px_last')                 <f64> 62.875
$ ('912810SK Govt', 'px_last')                 <f64> 64.375
$ ('912810TL Govt', 'px_last')                 <f64> 86.8984375
$ ('912810TV Govt', 'px_last')                 <f64> 98.34375
$ ('912810TW Govt', 'px_last')                 <f64> 100.15625
$ ('912810TZ Govt', 'px_last')                 <f64> 96.8984375
$ ('912810UB Govt', 'px_last')                 <f64> 98.3359375
$ ('912810UJ Govt', 'px_last')                 <f64> 99.6328125
$ ('912810UL Govt', 'px_last')                 <f64> 102.8046875
$ ('9128282A Govt', 'px_last')                 <f64> 98.75
$ ('9128282F Govt', 'px_last')                 <f64> null
$ ('9128282R Govt', 'px_last')                 <f64> 98.068359375
$ ('9128282S Govt', 'px_last')                 <f64> null
$ ('9128282V Govt', 'px_last')                 <f64> null
$ ('9128283F Govt', 'px_last')                 <f64> 97.794921875
$ ('9128283L Govt', 'px_last')                 <f64> null
$ ('9128283N Govt', 'px_last')                 <f64> null
$ ('9128283P Govt', 'px_last')                 <f64> null
$ ('9128283V Govt', 'px_last')                 <f64> null
$ ('9128283W Govt', 'px_last')                 <f64> 98.5078125
$ ('9128283Z Govt', 'px_last')                 <f64> null
$ ('9128284A Govt', 'px_last')                 <f64> null
$ ('9128284B Govt', 'px_last')                 <f64> null
$ ('9128284D Govt', 'px_last')                 <f64> null
$ ('9128284F Govt', 'px_last')                 <f64> null
$ ('9128284M Govt', 'px_last')                 <f64> null
$ ('9128284N Govt', 'px_last')                 <f64> 98.59375
$ ('9128284R Govt', 'px_last')                 <f64> null
$ ('9128284S Govt', 'px_last')                 <f64> null
$ ('9128284T Govt', 'px_last')                 <f64> null
$ ('9128284U Govt', 'px_last')                 <f64> null
$ ('9128284V Govt', 'px_last')                 <f64> 98.4140625
$ ('9128284X Govt', 'px_last')                 <f64> null
$ ('9128284Z Govt', 'px_last')                 <f64> null
$ ('9128285A Govt', 'px_last')                 <f64> null
$ ('9128285B Govt', 'px_last')                 <f64> null
$ ('9128285C Govt', 'px_last')                 <f64> null
$ ('9128285D Govt', 'px_last')                 <f64> null
$ ('9128285J Govt', 'px_last')                 <f64> null
$ ('9128285M Govt', 'px_last')                 <f64> 98.890625
$ ('9128285P Govt', 'px_last')                 <f64> null
$ ('9128285R Govt', 'px_last')                 <f64> null
$ ('9128285S Govt', 'px_last')                 <f64> null
$ ('9128285T Govt', 'px_last')                 <f64> null
$ ('9128285U Govt', 'px_last')                 <f64> null
$ ('9128286A Govt', 'px_last')                 <f64> 99.900390625
$ ('9128286B Govt', 'px_last')                 <f64> 97.24609375
$ ('9128286G Govt', 'px_last')                 <f64> null
$ ('9128286H Govt', 'px_last')                 <f64> null
$ ('9128286L Govt', 'px_last')                 <f64> 99.685546875
$ ('9128286S Govt', 'px_last')                 <f64> 99.642578125
$ ('9128286T Govt', 'px_last')                 <f64> 96.18359375
$ ('9128286Y Govt', 'px_last')                 <f64> null
$ ('9128286Z Govt', 'px_last')                 <f64> null
$ ('9128287B Govt', 'px_last')                 <f64> 99.208984375
$ ('912828A3 Govt', 'px_last')                 <f64> null
$ ('912828A4 Govt', 'px_last')                 <f64> null
$ ('912828A7 Govt', 'px_last')                 <f64> null
$ ('912828B6 Govt', 'px_last')                 <f64> null
$ ('912828C2 Govt', 'px_last')                 <f64> null
$ ('912828C6 Govt', 'px_last')                 <f64> null
$ ('912828D5 Govt', 'px_last')                 <f64> null
$ ('912828D8 Govt', 'px_last')                 <f64> null
$ ('912828D9 Govt', 'px_last')                 <f64> null
$ ('912828F2 Govt', 'px_last')                 <f64> null
$ ('912828F3 Govt', 'px_last')                 <f64> null
$ ('912828F9 Govt', 'px_last')                 <f64> null
$ ('912828G3 Govt', 'px_last')                 <f64> null
$ ('912828G6 Govt', 'px_last')                 <f64> null
$ ('912828G7 Govt', 'px_last')                 <f64> null
$ ('912828G8 Govt', 'px_last')                 <f64> null
$ ('912828G9 Govt', 'px_last')                 <f64> null
$ ('912828GH Govt', 'px_last')                 <f64> null
$ ('912828GM Govt', 'px_last')                 <f64> null
$ ('912828GS Govt', 'px_last')                 <f64> null
$ ('912828GW Govt', 'px_last')                 <f64> null
$ ('912828HA Govt', 'px_last')                 <f64> null
$ ('912828HE Govt', 'px_last')                 <f64> null
$ ('912828HH Govt', 'px_last')                 <f64> null
$ ('912828HM Govt', 'px_last')                 <f64> null
$ ('912828HR Govt', 'px_last')                 <f64> null
$ ('912828HV Govt', 'px_last')                 <f64> null
$ ('912828HZ Govt', 'px_last')                 <f64> null
$ ('912828J2 Govt', 'px_last')                 <f64> null
$ ('912828J5 Govt', 'px_last')                 <f64> null
$ ('912828J6 Govt', 'px_last')                 <f64> null
$ ('912828J7 Govt', 'px_last')                 <f64> null
$ ('912828J8 Govt', 'px_last')                 <f64> null
$ ('912828JD Govt', 'px_last')                 <f64> null
$ ('912828JH Govt', 'px_last')                 <f64> null
$ ('912828JM Govt', 'px_last')                 <f64> null
$ ('912828JR Govt', 'px_last')                 <f64> null
$ ('912828JW Govt', 'px_last')                 <f64> null
$ ('912828K7 Govt', 'px_last')                 <f64> null
$ ('912828KD Govt', 'px_last')                 <f64> null
$ ('912828KJ Govt', 'px_last')                 <f64> null
$ ('912828KQ Govt', 'px_last')                 <f64> null
$ ('912828KY Govt', 'px_last')                 <f64> null
$ ('912828L2 Govt', 'px_last')                 <f64> null
$ ('912828L3 Govt', 'px_last')                 <f64> null
$ ('912828L4 Govt', 'px_last')                 <f64> null
$ ('912828L5 Govt', 'px_last')                 <f64> null
$ ('912828L6 Govt', 'px_last')                 <f64> null
$ ('912828LJ Govt', 'px_last')                 <f64> null
$ ('912828LK Govt', 'px_last')                 <f64> null
$ ('912828LQ Govt', 'px_last')                 <f64> null
$ ('912828LY Govt', 'px_last')                 <f64> null
$ ('912828LZ Govt', 'px_last')                 <f64> null
$ ('912828M4 Govt', 'px_last')                 <f64> null
$ ('912828M5 Govt', 'px_last')                 <f64> null
$ ('912828M8 Govt', 'px_last')                 <f64> null
$ ('912828M9 Govt', 'px_last')                 <f64> null
$ ('912828MB Govt', 'px_last')                 <f64> null
$ ('912828ME Govt', 'px_last')                 <f64> null
$ ('912828MP Govt', 'px_last')                 <f64> null
$ ('912828MR Govt', 'px_last')                 <f64> null
$ ('912828MS Govt', 'px_last')                 <f64> null
$ ('912828MT Govt', 'px_last')                 <f64> null
$ ('912828MV Govt', 'px_last')                 <f64> null
$ ('912828MW Govt', 'px_last')                 <f64> null
$ ('912828N2 Govt', 'px_last')                 <f64> null
$ ('912828N3 Govt', 'px_last')                 <f64> null
$ ('912828N4 Govt', 'px_last')                 <f64> null
$ ('912828NA Govt', 'px_last')                 <f64> null
$ ('912828ND Govt', 'px_last')                 <f64> null
$ ('912828NF Govt', 'px_last')                 <f64> null
$ ('912828NG Govt', 'px_last')                 <f64> null
$ ('912828NL Govt', 'px_last')                 <f64> null
$ ('912828NT Govt', 'px_last')                 <f64> null
$ ('912828NV Govt', 'px_last')                 <f64> null
$ ('912828NZ Govt', 'px_last')                 <f64> null
$ ('912828P4 Govt', 'px_last')                 <f64> 99.74609375
$ ('912828P8 Govt', 'px_last')                 <f64> null
$ ('912828PC Govt', 'px_last')                 <f64> null
$ ('912828PJ Govt', 'px_last')                 <f64> null
$ ('912828PL Govt', 'px_last')                 <f64> null
$ ('912828PM Govt', 'px_last')                 <f64> null
$ ('912828PX Govt', 'px_last')                 <f64> null
$ ('912828PY Govt', 'px_last')                 <f64> null
$ ('912828PZ Govt', 'px_last')                 <f64> null
$ ('912828QA Govt', 'px_last')                 <f64> null
$ ('912828QJ Govt', 'px_last')                 <f64> null
$ ('912828QN Govt', 'px_last')                 <f64> null
$ ('912828QP Govt', 'px_last')                 <f64> null
$ ('912828QR Govt', 'px_last')                 <f64> null
$ ('912828R3 Govt', 'px_last')                 <f64> 99.30859375
$ ('912828R6 Govt', 'px_last')                 <f64> null
$ ('912828R7 Govt', 'px_last')                 <f64> null
$ ('912828RC Govt', 'px_last')                 <f64> null
$ ('912828RE Govt', 'px_last')                 <f64> null
$ ('912828RF Govt', 'px_last')                 <f64> null
$ ('912828RH Govt', 'px_last')                 <f64> null
$ ('912828RJ Govt', 'px_last')                 <f64> null
$ ('912828RR Govt', 'px_last')                 <f64> null
$ ('912828RU Govt', 'px_last')                 <f64> null
$ ('912828RX Govt', 'px_last')                 <f64> null
$ ('912828SF Govt', 'px_last')                 <f64> null
$ ('912828SJ Govt', 'px_last')                 <f64> null
$ ('912828SM Govt', 'px_last')                 <f64> null
$ ('912828SV Govt', 'px_last')                 <f64> null
$ ('912828SY Govt', 'px_last')                 <f64> null
$ ('912828TB Govt', 'px_last')                 <f64> null
$ ('912828TJ Govt', 'px_last')                 <f64> null
$ ('912828TM Govt', 'px_last')                 <f64> null
$ ('912828TS Govt', 'px_last')                 <f64> null
$ ('912828TY Govt', 'px_last')                 <f64> null
$ ('912828U2 Govt', 'px_last')                 <f64> 98.6953125
$ ('912828U6 Govt', 'px_last')                 <f64> null
$ ('912828UA Govt', 'px_last')                 <f64> null
$ ('912828UE Govt', 'px_last')                 <f64> null
$ ('912828UN Govt', 'px_last')                 <f64> null
$ ('912828UR Govt', 'px_last')                 <f64> null
$ ('912828UU Govt', 'px_last')                 <f64> null
$ ('912828V9 Govt', 'px_last')                 <f64> 98.619140625
$ ('912828VB Govt', 'px_last')                 <f64> null
$ ('912828VE Govt', 'px_last')                 <f64> null
$ ('912828VK Govt', 'px_last')                 <f64> null
$ ('912828VS Govt', 'px_last')                 <f64> null
$ ('912828VV Govt', 'px_last')                 <f64> null
$ ('912828W5 Govt', 'px_last')                 <f64> null
$ ('912828W6 Govt', 'px_last')                 <f64> null
$ ('912828W7 Govt', 'px_last')                 <f64> null
$ ('912828W8 Govt', 'px_last')                 <f64> null
$ ('912828WE Govt', 'px_last')                 <f64> null
$ ('912828WJ Govt', 'px_last')                 <f64> null
$ ('912828WL Govt', 'px_last')                 <f64> null
$ ('912828WP Govt', 'px_last')                 <f64> null
$ ('912828WS Govt', 'px_last')                 <f64> null
$ ('912828WY Govt', 'px_last')                 <f64> null
$ ('912828WZ Govt', 'px_last')                 <f64> null
$ ('912828X8 Govt', 'px_last')                 <f64> 98.5
$ ('912828XB Govt', 'px_last')                 <f64> null
$ ('912828XD Govt', 'px_last')                 <f64> null
$ ('912828XE Govt', 'px_last')                 <f64> null
$ ('912828XF Govt', 'px_last')                 <f64> null
$ ('912828XG Govt', 'px_last')                 <f64> null
$ ('912828XH Govt', 'px_last')                 <f64> null
$ ('912828XQ Govt', 'px_last')                 <f64> null
$ ('912828XR Govt', 'px_last')                 <f64> null
$ ('912828XT Govt', 'px_last')                 <f64> null
$ ('912828XY Govt', 'px_last')                 <f64> null
$ ('912828XZ Govt', 'px_last')                 <f64> null
$ ('912828Y7 Govt', 'px_last')                 <f64> null
$ ('912828Y9 Govt', 'px_last')                 <f64> 99.060546875
$ ('912828YB Govt', 'px_last')                 <f64> 93.37890625
$ ('912828YE Govt', 'px_last')                 <f64> null
$ ('912828YF Govt', 'px_last')                 <f64> null
$ ('912828YH Govt', 'px_last')                 <f64> null
$ ('912828YS Govt', 'px_last')                 <f64> 93.40234375
$ ('912828YV Govt', 'px_last')                 <f64> null
$ ('912828YW Govt', 'px_last')                 <f64> null
$ ('912828YX Govt', 'px_last')                 <f64> 98.283203125
$ ('912828YY Govt', 'px_last')                 <f64> null
$ ('912828Z9 Govt', 'px_last')                 <f64> 91.87109375
$ ('912828ZC Govt', 'px_last')                 <f64> null
$ ('912828ZF Govt', 'px_last')                 <f64> null
$ ('912828ZQ Govt', 'px_last')                 <f64> 87.78515625
$ ('912828ZT Govt', 'px_last')                 <f64> null
$ ('91282CAE Govt', 'px_last')                 <f64> 87.0390625
$ ('91282CAJ Govt', 'px_last')                 <f64> null
$ ('91282CAV Govt', 'px_last')                 <f64> 87.44140625
$ ('91282CAZ Govt', 'px_last')                 <f64> null
$ ('91282CBQ Govt', 'px_last')                 <f64> 99.4921875
$ ('91282CCB Govt', 'px_last')                 <f64> 89.6171875
$ ('91282CCF Govt', 'px_last')                 <f64> 98.865234375
$ ('91282CCS Govt', 'px_last')                 <f64> 87.15234375
$ ('91282CCW Govt', 'px_last')                 <f64> 98.185546875
$ ('91282CDJ Govt', 'px_last')                 <f64> 87.14453125
$ ('91282CDK Govt', 'px_last')                 <f64> 97.958984375
$ ('91282CDY Govt', 'px_last')                 <f64> 89.234375
$ ('91282CEC Govt', 'px_last')                 <f64> 98.16015625
$ ('91282CED Govt', 'px_last')                 <f64> null
$ ('91282CEE Govt', 'px_last')                 <f64> 96.359375
$ ('91282CEF Govt', 'px_last')                 <f64> 98.783203125
$ ('91282CEG Govt', 'px_last')                 <f64> null
$ ('91282CEM Govt', 'px_last')                 <f64> 97.8046875
$ ('91282CEP Govt', 'px_last')                 <f64> 94.328125
$ ('91282CET Govt', 'px_last')                 <f64> 98.8125
$ ('91282CEU Govt', 'px_last')                 <f64> null
$ ('91282CEV Govt', 'px_last')                 <f64> 98.8828125
$ ('91282CEW Govt', 'px_last')                 <f64> 99.669921875
$ ('91282CEX Govt', 'px_last')                 <f64> null
$ ('91282CFF Govt', 'px_last')                 <f64> 93.265625
$ ('91282CFK Govt', 'px_last')                 <f64> null
$ ('91282CFL Govt', 'px_last')                 <f64> 100.86328125
$ ('91282CFM Govt', 'px_last')                 <f64> 101.078125
$ ('91282CFN Govt', 'px_last')                 <f64> null
$ ('91282CFT Govt', 'px_last')                 <f64> 101.32421875
$ ('91282CFV Govt', 'px_last')                 <f64> 101.1953125
$ ('91282CFZ Govt', 'px_last')                 <f64> 100.720703125
$ ('91282CGA Govt', 'px_last')                 <f64> null
$ ('91282CGB Govt', 'px_last')                 <f64> 100.859375
$ ('91282CGD Govt', 'px_last')                 <f64> null
$ ('91282CGM Govt', 'px_last')                 <f64> 97.2265625
$ ('91282CGP Govt', 'px_last')                 <f64> 101.0546875
$ ('91282CGQ Govt', 'px_last')                 <f64> 101.28515625
$ ('91282CGR Govt', 'px_last')                 <f64> 100.201171875
$ ('91282CGS Govt', 'px_last')                 <f64> 99.828125
$ ('91282CGT Govt', 'px_last')                 <f64> 100.28515625
$ ('91282CGU Govt', 'px_last')                 <f64> null
$ ('91282CHE Govt', 'px_last')                 <f64> 100.2734375
$ ('91282CHF Govt', 'px_last')                 <f64> 100.265625
$ ('91282CHH Govt', 'px_last')                 <f64> 100.29296875
$ ('91282CHJ Govt', 'px_last')                 <f64> 100.265625
$ ('91282CHK Govt', 'px_last')                 <f64> 101.17578125
$ ('91282CHL Govt', 'px_last')                 <f64> null
$ ('91282CHR Govt', 'px_last')                 <f64> 101.2890625
$ ('91282CHW Govt', 'px_last')                 <f64> 101.77734375
$ ('91282CHX Govt', 'px_last')                 <f64> 102.125
$ ('91282CHY Govt', 'px_last')                 <f64> 100.75
$ ('91282CHZ Govt', 'px_last')                 <f64> 103.9453125
$ ('91282CJB Govt', 'px_last')                 <f64> null
$ ('91282CJG Govt', 'px_last')                 <f64> 105.078125
$ ('91282CJN Govt', 'px_last')                 <f64> 102.27734375
$ ('91282CJP Govt', 'px_last')                 <f64> 100.791015625
$ ('91282CJQ Govt', 'px_last')                 <f64> 100.08203125
$ ('91282CJS Govt', 'px_last')                 <f64> null
$ ('91282CJX Govt', 'px_last')                 <f64> 101.19140625
$ ('91282CKC Govt', 'px_last')                 <f64> 102.328125
$ ('91282CKD Govt', 'px_last')                 <f64> 102.046875
$ ('91282CKE Govt', 'px_last')                 <f64> 100.85546875
$ ('91282CKF Govt', 'px_last')                 <f64> 101.73046875
$ ('91282CKN Govt', 'px_last')                 <f64> 104.12109375
$ ('91282CKT Govt', 'px_last')                 <f64> 102.890625
$ ('91282CKU Govt', 'px_last')                 <f64> 104.125
$ ('91282CKV Govt', 'px_last')                 <f64> 101.607421875
$ ('91282CKW Govt', 'px_last')                 <f64> 102.3046875
$ ('91282CKY Govt', 'px_last')                 <f64> 100.529296875
$ ('91282CLK Govt', 'px_last')                 <f64> 100.0078125
$ ('91282CLM Govt', 'px_last')                 <f64> 99.0390625
$ ('91282CLU Govt', 'px_last')                 <f64> 101.578125
$ ('91282CLZ Govt', 'px_last')                 <f64> 101.546875
$ ('91282CMA Govt', 'px_last')                 <f64> 101.734375
$ ('91282CMB Govt', 'px_last')                 <f64> 100.98046875
$ ('91282CMC Govt', 'px_last')                 <f64> 103.53125
$ ('91282CME Govt', 'px_last')                 <f64> 100.705078125
$ ('91282CMK Govt', 'px_last')                 <f64> 102.828125
$ ('91282CMS Govt', 'px_last')                 <f64> 100.8125
$ ('91282CMT Govt', 'px_last')                 <f64> 101.421875
$ ('91282CNA Govt', 'px_last')                 <f64> 100.69921875
$ ('91282CNF Govt', 'px_last')                 <f64> 101.36328125
$ ('91282CNG Govt', 'px_last')                 <f64> 101.2890625
$ ('91282CNJ Govt', 'px_last')                 <f64> 100.63671875
$ ('91282CNR Govt', 'px_last')                 <f64> 100.578125
$ ('91282CNW Govt', 'px_last')                 <f64> 99.7890625
$ ('91282CNX Govt', 'px_last')                 <f64> 99.6640625
$ ('91282CPQ Govt', 'px_last')                 <f64> 99.6015625
$ ('91282CPY Govt', 'px_last')                 <f64> null
$ Date                                        <date> 2026-01-01


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
| Data available up to (min)     | 2012-03-30 00:00:00                                                             |
| Data available up to (max)     | 2026-02-27 00:00:00                                                             |
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


