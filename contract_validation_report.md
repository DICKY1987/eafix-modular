# Contract Validation Report
Generated at: "2025-09-10 09:04:32.739212"

## Schema Loading Status
Loaded schemas: 4
- LOADED: hybrid_id.schema
- LOADED: indicator_record.schema
- LOADED: orders_in.schema
- LOADED: orders_out.schema

## Fixture Validation Results
Total fixtures: 4
Valid fixtures: 1
Invalid fixtures: 3

### FAIL: hybrid_id_valid.json
  - Path : Additional properties are not allowed ('calendar', 'direction', 'duration', 'outcome', 'proximity', 'suffix' were unexpected)
  - Path : 'signal_id' is a required property
  - Path : 'time_bucket' is a required property
  - Path : 'outcome_bucket' is a required property
  - Path : 'proximity_bucket' is a required property
  - Path : 'reentry_key' is a required property
  - Path : 'comment_suffix' is a required property

### PASS: indicator_record_valid.json

### FAIL: orders_in_valid.json
  - Path reentry_key: 'W1_QUICK_AT_EVENT_CAL8_USD_NFP_H~1' does not match '^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$'
  - 1 validation error for OrderIn
reentry_key
  String should match pattern '^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$' [type=string_pattern_mismatch, input_value='W1_QUICK_AT_EVENT_CAL8_USD_NFP_H~1', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_pattern_mismatch

### FAIL: orders_out_valid.json
  - Path reentry_key: 'W1_QUICK_AT_EVENT_CAL8_USD_NFP_H~1' does not match '^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$'
  - Path comment_suffix: 'ABC123' does not match '^[A-Z2-7]{4,10}$'
  - 2 validation errors for OrderOut
reentry_key
  String should match pattern '^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$' [type=string_pattern_mismatch, input_value='W1_QUICK_AT_EVENT_CAL8_USD_NFP_H~1', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_pattern_mismatch
comment_suffix
  String should match pattern '^[A-Z2-7]{4,10}$' [type=string_pattern_mismatch, input_value='ABC123', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_pattern_mismatch
