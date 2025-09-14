from __future__ import annotations

from pathlib import Path

from schema.validators.python.gdw_validator import validate_spec


def test_gdw_specs_validate():
    roots = [
        Path("gdw/git.commit_push.main/v1.0.0/spec.json"),
        Path("gdw/build.container.sign/v1.0.0/spec.json"),
        Path("gdw/security.scan.trivy/v1.0.0/spec.json"),
        Path("gdw/k8s.deploy.rolling/v1.0.0/spec.json"),
        Path("gdw/version.bump.semver/v1.0.0/spec.json"),
    ]
    for spec in roots:
        ok, msg = validate_spec(spec)
        assert ok, (spec, msg)


def test_gdw_spec_invalid(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    ok, msg = validate_spec(bad)
    assert not ok
