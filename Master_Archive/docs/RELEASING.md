Release Guide

Version bump

- Patch: `python scripts/bump_version.py`
- Minor: `python scripts/bump_version.py minor`
- Major: `python scripts/bump_version.py major`

Commit and tag

```bash
git add pyproject.toml
git commit -m "chore(release): bump version"
git tag v$(python scripts/bump_version.py) # if you want to tag the bumped version automatically
git push origin main --tags
```

CI release

- On tag push (`v*`), the `release` workflow builds artifacts, generates a CycloneDX SBOM, and publishes a GitHub Release with assets.

