from pathlib import Path

from doc_id_subsystem.core.doc_id_scanner import scan_paths


def test_scan_paths_classifies_supported_prefixes(tmp_path: Path) -> None:
    result = scan_paths(
        tmp_path,
        [
            "1299900011260118_doc_id_validation.yml",
            "nested/P_2099900005260118_eafix_cli.py",
            "README.md",
        ],
    )

    assert result.total_files == 3
    assert [item.doc_id for item in result.prefixed_files] == [
        "1299900011260118",
        "2099900005260118",
    ]
    assert result.unprefixed_files == ["README.md"]
    assert result.coverage_ratio == 2 / 3


def test_scan_paths_reports_duplicate_ids_deterministically(tmp_path: Path) -> None:
    result = scan_paths(
        tmp_path,
        [
            "z/1199900011260118_schema.json",
            "a/1199900011260118_fixture.json",
            "a/1199900012260118_other.json",
        ],
    )

    assert result.duplicate_ids == {
        "1199900011260118": [
            "a/1199900011260118_fixture.json",
            "z/1199900011260118_schema.json",
        ]
    }
    assert result.duplicate_count == 2


def test_empty_path_set_has_full_coverage(tmp_path: Path) -> None:
    result = scan_paths(tmp_path, [])

    assert result.total_files == 0
    assert result.coverage_ratio == 1.0
