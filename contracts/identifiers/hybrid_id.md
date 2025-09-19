# Hybrid ID Format Specification

## Overview
Hybrid IDs provide a standardized way to encode trading context including outcome, duration, proximity, calendar impact, and direction for re-entry decision making.

## Format Structure
```
{OUTCOME}_{DURATION}_{PROXIMITY}_{CALENDAR_IMPACT}_{DIRECTION}_{SUFFIX}
```

### Components

#### 1. Outcome Buckets
| Token | Rank | Description |
|-------|------|-------------|
| `W2` | 2 | Strong win / exceeded high threshold |
| `W1` | 1 | Win / hit target |
| `BE` | 0 | Break-even |
| `L1` | -1 | Loss / small adverse move |
| `L2` | -2 | Strong loss / large adverse move |

#### 2. Duration Buckets
| Token | Max Minutes | ISO Limit | Description |
|-------|-------------|-----------|-------------|
| `FLASH` | 5 | PT5M | Very short burst; spike handling; ≤ 5 minutes |
| `QUICK` | 30 | PT30M | Short move; ≤ 30 minutes |
| `LONG` | 240 | PT4H | Sustained move; ≤ 4 hours |
| `EXTENDED` | null | null | Prolonged; > 4 hours |

#### 3. Proximity Buckets
| Token | Window (minutes) | Description |
|-------|------------------|-------------|
| `PRE_1H` | [-60, 0] | In anticipation window before scheduled event time |
| `AT_EVENT` | [0, 5] | At the event print and immediate aftershock window |
| `POST_30M` | [1, 30] | Post-event stabilization window (1-30m after T0) |

#### 4. Calendar Impact
| Token | Description |
|-------|-------------|
| `CAL8` | High-impact 8-character calendar identifier |
| `CAL5` | Medium-impact 5-character calendar identifier |
| `NONE` | No significant calendar event |

#### 5. Direction
| Token | Description |
|-------|-------------|
| `LONG` | Buy position |
| `SHORT` | Sell position |
| `ANY` | Direction-neutral |

#### 6. Suffix
- **Generation Range**: 1-3 (represents re-entry generation: O→R1→R2)
- **Comment Suffix**: Short deterministic hash for trade comment uniqueness

## Examples

### Basic Hybrid IDs
```
W1_QUICK_AT_EVENT_CAL8_LONG_1    # Win, quick duration, at event, high impact calendar, long position, generation 1
L1_EXTENDED_PRE_1H_CAL5_SHORT_2  # Loss, extended duration, pre-event, medium impact calendar, short position, generation 2
BE_FLASH_POST_30M_NONE_LONG_1    # Break-even, flash duration, post-event, no calendar, long position, generation 1
```

### With Comment Suffix
```
W1_QUICK_AT_EVENT_CAL8_LONG_1_abc123   # Includes 6-char deterministic hash
```

## Validation Rules

### 1. Format Validation
- Must contain exactly 5 or 6 components separated by underscores
- Each component must be from valid vocabulary
- Generation must be 1, 2, or 3
- Comment suffix (if present) must be 6 alphanumeric characters

### 2. Logical Validation
- Proximity and calendar impact should be consistent
- Duration should align with market conditions
- Generation sequence must follow O(1)→R1(2)→R2(3) progression

### 3. Chain Enforcement
- Original trade (O) has generation 1
- First re-entry (R1) has generation 2, can only follow O
- Second re-entry (R2) has generation 3, can only follow R1
- Maximum one R1 and one R2 per original trade

## Implementation Functions

### Required Functions
```python
def compose(outcome: str, duration: str, proximity: str, calendar: str, direction: str, generation: int) -> str:
    """Compose a hybrid ID from components."""
    
def parse(hybrid_id: str) -> dict:
    """Parse a hybrid ID into components."""
    
def validate_key(hybrid_id: str) -> bool:
    """Validate hybrid ID format and vocabulary."""
    
def comment_suffix_hash(hybrid_id: str) -> str:
    """Generate deterministic 6-character suffix for trade comments."""
```

## Cross-Language Parity
- Python implementation in `shared/reentry/hybrid_id.py`
- MQL4 implementation in `ReentryHelpers.mq4`
- Both implementations must produce identical results for same inputs
- Comment suffix hash must be deterministic across languages