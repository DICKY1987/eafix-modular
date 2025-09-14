from __future__ import annotations

from pathlib import Path

from src.cli_multi_rapid.commands.gdw.list import discover_gdws


def test_discover_gdws_catalog():
    root = Path(".").resolve()
    items = discover_gdws(root)
    ids = {i.get("id") for i in items}
    # Expect at least our seeded workflows
    assert "git.commit_push.main" in ids
    assert "build.container.sign" in ids
    assert "security.scan.trivy" in ids
    assert "k8s.deploy.rolling" in ids
    assert "version.bump.semver" in ids
    assert len(items) >= 5
