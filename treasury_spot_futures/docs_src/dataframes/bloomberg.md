
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
