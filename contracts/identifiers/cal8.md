# CAL8 Calendar Identifier Specification

## Overview
CAL8 identifiers provide standardized 8-character codes for high-impact economic calendar events.

## Format Structure
```
CAL8_{CURRENCY}_{EVENT}_{IMPACT}
```

### Components

#### 1. Currency (3 characters)
ISO 4217 currency codes for major trading currencies:
- `USD` - US Dollar
- `EUR` - Euro  
- `GBP` - British Pound
- `JPY` - Japanese Yen
- `CHF` - Swiss Franc
- `AUD` - Australian Dollar
- `CAD` - Canadian Dollar
- `NZD` - New Zealand Dollar

#### 2. Event Code (3-4 characters)
Abbreviated names for major economic events:

**US Events:**
- `NFP` - Non-Farm Payrolls
- `CPI` - Consumer Price Index
- `FOMC` - Federal Open Market Committee Meeting
- `GDP` - Gross Domestic Product
- `PPI` - Producer Price Index
- `ISM` - ISM Manufacturing PMI
- `RET` - Retail Sales
- `UNE` - Unemployment Rate

**European Events:**
- `ECB` - European Central Bank Meeting
- `CPI` - Consumer Price Index (HICP)
- `GDP` - Gross Domestic Product
- `PMI` - Purchasing Managers Index
- `IFO` - IFO Business Climate (Germany)

**UK Events:**
- `BOE` - Bank of England Meeting
- `CPI` - Consumer Price Index
- `GDP` - Gross Domestic Product
- `PMI` - Purchasing Managers Index
- `RET` - Retail Sales

**Japan Events:**
- `BOJ` - Bank of Japan Meeting
- `CPI` - Consumer Price Index
- `GDP` - Gross Domestic Product
- `TAN` - Tankan Survey

#### 3. Impact Level (1 character)
- `H` - High impact (market-moving events)
- `M` - Medium impact (moderate market reaction expected)

## Examples

### High-Impact Events
```
CAL8_USD_NFP_H      # US Non-Farm Payrolls (High Impact)
CAL8_USD_FOMC_H     # FOMC Meeting (High Impact)
CAL8_EUR_ECB_H      # ECB Meeting (High Impact)
CAL8_GBP_BOE_H      # Bank of England Meeting (High Impact)
CAL8_JPY_BOJ_H      # Bank of Japan Meeting (High Impact)
```

### Medium-Impact Events
```
CAL8_USD_CPI_M      # US CPI (Medium Impact)
CAL8_EUR_GDP_M      # Eurozone GDP (Medium Impact)
CAL8_GBP_PMI_M      # UK PMI (Medium Impact)
```

## Event Priority Classification

### Tier 1 (Highest Priority - Always High Impact)
- Central Bank Meetings (FOMC, ECB, BOE, BOJ)
- Non-Farm Payrolls (NFP)
- GDP releases (major economies)

### Tier 2 (High to Medium Impact)
- CPI/Inflation data
- Employment data (excluding NFP)
- PMI data
- Retail sales

### Tier 3 (Medium Impact)
- Producer Price Index (PPI)
- Trade balance
- Industrial production
- Consumer confidence

## Mapping Rules

### Impact Level Assignment
1. **High Impact (`H`)**: Events that typically move markets >50 pips in major pairs
2. **Medium Impact (`M`)**: Events that typically move markets 20-50 pips in major pairs

### Currency Assignment
- Use the currency of the country releasing the data
- For Eurozone events, use `EUR`
- For UK events, use `GBP`

## Validation Rules

### Format Validation
- Must be exactly 8 characters plus `CAL8_` prefix
- Currency must be valid ISO 4217 code from supported list
- Event code must be from approved list
- Impact level must be `H` or `M`

### Logical Validation
- Currency and event must be logically consistent (e.g., `NFP` only with `USD`)
- Impact level must align with event significance

## Usage in Trading System

### Calendar Signal Generation
```python
# Example usage
calendar_id = "CAL8_USD_NFP_H"
symbol = "EURUSD"  # Will be affected by USD NFP
proximity_state = "PRE_1H"  # One hour before event
```

### Re-entry Context
CAL8 identifiers are used in Hybrid IDs to provide calendar context for re-entry decisions:
```
W1_QUICK_PRE_1H_CAL8_USD_NFP_H_LONG_1
```

This indicates a winning quick trade during the pre-event window of a high-impact US NFP release.