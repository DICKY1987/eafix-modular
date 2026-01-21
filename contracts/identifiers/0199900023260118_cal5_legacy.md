---
doc_id: DOC-CONTRACT-0030
---

# CAL5 Legacy Calendar Identifier Specification

## Overview
CAL5 identifiers provide 5-character codes for medium-impact economic calendar events and legacy event identification.

## Format Structure
```
CAL5_{EVENT_CODE}
```

### Components

#### Event Code (5 characters)
Abbreviated names for medium-impact economic events:

**Cross-Currency Events:**
- `GDPQ1` - GDP Q1 releases
- `GDPQ2` - GDP Q2 releases  
- `GDPQ3` - GDP Q3 releases
- `GDPQ4` - GDP Q4 releases
- `CPIM1` - CPI Month-over-Month
- `CPIY1` - CPI Year-over-Year
- `PMIM1` - PMI Manufacturing
- `PMIS1` - PMI Services
- `RETM1` - Retail Sales Monthly

**US Specific:**
- `ISMM1` - ISM Manufacturing Monthly
- `ISMS1` - ISM Services Monthly
- `JOLTS` - Job Openings and Labor Turnover
- `CLAIMS` - Initial Jobless Claims
- `DURAB` - Durable Goods Orders

**European Specific:**
- `IFOM1` - IFO Business Climate Monthly
- `ZEWM1` - ZEW Economic Sentiment Monthly
- `HICPM` - HICP Monthly (Eurozone CPI)

**UK Specific:**
- `CLIOM` - Claimant Count Change Monthly
- `AVGEM` - Average Earnings Monthly

**Japan Specific:**
- `TANKQ` - Tankan Survey Quarterly
- `BOJA1` - BOJ Meeting Minutes/Statements

## Examples

### Medium-Impact Events
```
CAL5_GDPQ1     # Q1 GDP Release
CAL5_CPIM1     # Monthly CPI Release
CAL5_PMIM1     # Manufacturing PMI
CAL5_RETM1     # Monthly Retail Sales
CAL5_JOLTS     # US JOLTS Report
CAL5_IFOM1     # German IFO Business Climate
```

## Event Classification

### Tier 1 (Medium-High Impact)
- Quarterly GDP releases
- Monthly CPI data
- Manufacturing PMI

### Tier 2 (Medium Impact)  
- Services PMI
- Retail sales
- Employment data (non-NFP)

### Tier 3 (Medium-Low Impact)
- Sentiment surveys
- Secondary economic indicators
- Regional data

## Mapping Rules

### When to Use CAL5 vs CAL8
- **CAL8**: Use for high-impact, market-moving events
- **CAL5**: Use for medium-impact events that may influence but not dominate market movements

### Legacy Support
CAL5 identifiers provide backward compatibility for:
- Historical trade analysis
- Existing re-entry parameter sets
- Legacy indicator configurations

## Validation Rules

### Format Validation
- Must be exactly 5 characters plus `CAL5_` prefix
- Event code must be from approved list
- All characters must be alphanumeric (A-Z, 0-9)

### Usage Guidelines
- Prefer CAL8 for new high-impact events
- Use CAL5 for medium-impact events
- Maintain CAL5 support for legacy data

## Usage in Trading System

### Calendar Signal Generation
```python
# Example usage
calendar_id = "CAL5_GDPQ1"
symbol = "EURUSD"  # May be affected by Eurozone GDP
proximity_state = "POST_30M"  # Post-event stabilization
```

### Re-entry Context
CAL5 identifiers in Hybrid IDs indicate medium-impact calendar context:
```
L1_EXTENDED_POST_30M_CAL5_GDPQ1_SHORT_2
```

This indicates a losing extended trade during the post-event window of a medium-impact GDP release.

## Migration Path

### From CAL5 to CAL8
For events that become higher impact:
1. Create new CAL8 identifier
2. Update event classification
3. Maintain CAL5 for historical data
4. Document mapping in migration log

### Deprecation Process
1. Mark CAL5 event as deprecated
2. Provide CAL8 alternative
3. Update documentation
4. Maintain backward compatibility for 2 major releases