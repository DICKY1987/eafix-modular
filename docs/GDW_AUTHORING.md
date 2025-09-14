GDW Authoring Guide (Draft)

- Spec schema: see `schema/gdw.spec.schema.json` (draft-07)
- Place new workflows under `gdw/<id>/v<semver>/spec.json`
- Update catalogs in `catalog/index.json` and domain files
- Validate with: `python -m schema.validators.python.gdw_validator <spec.json>`
- CLI usage:
  - `cli-multi-rapid gdw list`
  - `cli-multi-rapid gdw validate gdw/<id>/v1.0.0/spec.json`
  - `cli-multi-rapid gdw run <id> --dry-run`
  - `cli-multi-rapid gdw chain examples/<file>.json --dry-run`

