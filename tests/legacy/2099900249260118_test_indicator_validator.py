# doc_id: DOC-TEST-0046
# DOC_ID: DOC-TEST-0006
\
import os, sys, json, tempfile
sys.path.insert(0, os.path.abspath("."))

from reentry_helpers.indicator_validator import validate_records

def test_indicator_validator_minimal_schema_and_record():
    schema = {
        "type":"object",
        "additionalProperties": False,
        "required":["Id","Name","OutputType"],
        "properties": {
            "Id":{"type":"string"},
            "Name":{"type":"string"},
            "OutputType":{"type":"string","enum":["zscore","band","percent_change"]}
        }
    }
    good = {"Id":"VIX_Z","Name":"VIX Z-Score","OutputType":"zscore"}
    bad  = {"Id":"BAD","Name":"Bad","OutputType":"wat"}
    valids, invalids = validate_records([good,bad], {"type":"array","items":schema}) if False else validate_records([good,bad],[schema])  # keep API simple
    # Our helper expects list + schema for a single record; call validator per record
    from reentry_helpers.indicator_validator import _validate_with_jsonschema
    assert _validate_with_jsonschema(good, schema) == []
    assert _validate_with_jsonschema(bad, schema) != []
