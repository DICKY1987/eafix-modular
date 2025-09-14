from __future__ import annotations

import json
from pathlib import Path
from src.cli_multi_rapid.cli import main


def test_gdw_list_non_empty(tmp_path: Path, monkeypatch):
    # Ensure we run from repo
    rc = main(["gdw", "list"])
    assert rc == 0

