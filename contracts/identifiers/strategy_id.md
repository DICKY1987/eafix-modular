# strategy_id

## Definition

`strategy_id` is semantically equivalent to `calendar_id`.

They represent the same concept: the economic event identity that drives the trading strategy (e.g., `CAL8_USD_NFP_H` for US Non-Farm Payrolls, high-impact).

## Carry-through Path

The `calendar_id` / `strategy_id` value flows through the process in these steps:

| Step | Location | Role |
|------|----------|------|
| S4   | calendar-ingestor | Origin — assigned when event is classified |
| S6   | ActiveCalendarSignal CSV | Carried as `calendar_id` |
| S11  | Signal@1.0 | Carried as `calendar_id` |
| S12  | OrderIntent@1.2 | Carried as `calendar_id` |
| S13  | ExecutionReport | Carried as `calendar_id` |
| S24  | ReentryDecision CSV | Carried as part of `hybrid_id` component 4 |

## Values

Format: `{IMPACT_PREFIX}_{CURRENCY}_{EVENT_CODE}_{TIMEFRAME}`

Examples:
- `CAL8_USD_NFP_H` — US Non-Farm Payrolls, high-impact
- `CAL8_GBP_BOE_H` — Bank of England rate decision
- `CAL5_EUR_PMI_H` — Euro PMI (medium priority)
- `NONE` — No associated calendar event

## Notes

- `strategy_id` is NOT a separate field in any schema; use `calendar_id` consistently
- GAP-48 closed by this definition
