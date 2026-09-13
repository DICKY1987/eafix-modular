import json
import sys

from doc_id_subsystem.validation import validate_doc_id_coverage, validate_doc_id_uniqueness


def test_validate_doc_id_coverage_rejects_invalid_baseline(tmp_path, monkeypatch, capsys) -> None:
    baseline_file = tmp_path / "doc_id_coverage_baseline.json"
    baseline_file.write_text(json.dumps({"tracked_files": 10}), encoding="utf-8")

    monkeypatch.setattr(validate_doc_id_coverage, "BASELINE_FILE", baseline_file)
    monkeypatch.setattr(sys, "argv", ["validate_doc_id_coverage.py"])

    assert validate_doc_id_coverage.main() == 2
    assert "invalid coverage baseline" in capsys.readouterr().err


def test_validate_doc_id_uniqueness_rejects_invalid_baseline(tmp_path, monkeypatch, capsys) -> None:
    known_file = tmp_path / "known_duplicates.json"
    known_file.write_text(json.dumps({"duplicates": []}), encoding="utf-8")

    monkeypatch.setattr(validate_doc_id_uniqueness, "KNOWN_FILE", known_file)
    monkeypatch.setattr(sys, "argv", ["validate_doc_id_uniqueness.py"])

    assert validate_doc_id_uniqueness.main() == 2
    assert "invalid duplicate baseline" in capsys.readouterr().err
