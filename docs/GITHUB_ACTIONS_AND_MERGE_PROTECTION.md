# GitHub Actions and merge protection: what they are

**Repository:** `DICKY1987/eafix-modular`  
**Inventory checked:** 2026-10-06

This report explains the difference between GitHub Actions workflows and
merge-protection checks, inventories the workflow definitions currently in this
checkout, and describes what suspending or removing them would mean. It does
not disable or delete anything.

## In brief

- **A GitHub Actions workflow** is automation described by a YAML file under
  `.github/workflows/`. It runs when its configured events happen, such as a
  push, pull request, tag, schedule, or manual dispatch.
- **A merge-protection rule** is a repository setting (branch protection or a
  ruleset) that determines whether a pull request may be merged. It can require
  passing status checks, reviews, resolved conversations, or other conditions.
- A workflow is **not automatically a merge blocker** just because it exists
  or reports failure. Its check must be required by applicable merge rules, or
  some other policy must prevent merging.
- Deleting/disabling a workflow and removing a required-check rule are separate
  actions. Removing a workflow while leaving its check required can leave a PR
  waiting for a check that will never report.

## What exists in this repository

There are **27 `.yml` workflow definitions** in `.github/workflows/`. The
`.github/workflows/0099900014260118_ci-original.yml.backup` file is a backup,
not a workflow definition GitHub Actions normally runs.

### CI, quality, and validation

| Workflow file | Purpose / trigger scope |
| --- | --- |
| `ci.yml` | Quality checks and root pytest on pull requests and pushes to `main`; then runs a sample workflow and cost-report jobs. |
| `1299900007260118_ci.yml` | Older/enhanced service CI and deployment pipeline for pull requests to `master` and pushes to `master` or `rel/**`; contains service tests, contract tests, Docker builds, and integration checks. Some test and type-check failures are explicitly non-blocking. |
| `1299900013260118_reentry_ci.yml` | Root pytest and other checks for all branches and pull requests. |
| `1299900017260118_services-ci.yml` | Service test matrix for changes under `services/**`, on push and pull request. |
| `agentic-validators.yml` | Static analysis, dependency/license checks, formatting/linting, and an 85% coverage test gate for pull requests targeting `main`. |
| `gui-terminal.yml` | GUI core and parity tests for pushes and pull requests targeting `main`. |
| `validate-module-structure.yml` | Module structure validation when module manifests/readmes/agent instructions or the validator change. |
| `compliance-gate.yml` | Compliance script on pushes and pull requests targeting `main`. |
| `pr-title-lint.yml` | Checks pull request titles; accepts Conventional Commit titles or a sentence-style fallback. |
| `1299900018260118_smoke-e2e.yml` | Build-and-smoke job on pull requests and manual dispatch. |

### Contracts, registries, and repository metadata

| Workflow file | Purpose / trigger scope |
| --- | --- |
| `1299900008260118_contract-tests.yml` | Consumer/provider, scenario, property, coverage, and smoke contract jobs for relevant `master`/`develop` changes. |
| `1299900009260118_contracts-ci.yml` | Schema, CSV, and re-entry validation on relevant contract/re-entry changes. Some re-entry checks use `continue-on-error`. |
| `1299900010260118_contracts-compat.yml` | Contract schema compatibility for `contracts/**` pull requests and `master` pushes. |
| `1299900011260118_doc_id_validation.yml` | Document-ID coverage and uniqueness validation for `master`/`develop` pushes and pull requests. |
| `registry-validation.yml` | Registry unit tests and report-only registry validation for relevant `master`/`develop` changes. |

### Security and performance

| Workflow file | Purpose / trigger scope |
| --- | --- |
| `1299900016260118_security.yml` | Bandit, Safety dependency checks, and Semgrep on pushes and pull requests. |
| `codeql.yml` | CodeQL analysis on `main` pushes, pull requests, and scheduled runs. |
| `1299900015260118_scorecards.yml` | OpenSSF Scorecards on schedule, selected `master` changes, or manual dispatch. It contains threshold-reporting logic. |
| `scorecards.yml` | Another scorecard workflow, scheduled and push-triggered. |
| `1299900012260118_perf-smoke.yml` | Manually dispatched k6 and Locust performance smoke tests; both load steps are configured as non-blocking. |

### Build, release, and repository automation

| Workflow file | Purpose / trigger scope |
| --- | --- |
| `1299900006260118_build-publish.yml` | Build/publish pipeline for tags and manual dispatch. |
| `build-publish.yml` | Builds a Python distribution and SBOM on version tags. |
| `1299900014260118_release.yml` | Creates a release for version tags or manual dispatch. |
| `release.yml` | Another release workflow for version tags or manual dispatch. |
| `automerge.yml` | Enables squash auto-merge for non-draft PRs with the `automerge` label or Dependabot PRs. This does not itself waive required checks. |
| `branch_cleanup.yml` | Scheduled/manual cleanup of merged branches. |
| `budget_check.yml` | Scheduled/manual cost budget reporting. |

Some workflows overlap in purpose (for example, there are two build/publish,
two release, and two scorecard definitions). That may be intentional or legacy
duplication; the filenames alone do not prove which checks are required.

## Merge protection in plain terms

When a workflow runs, GitHub reports one or more check runs/statuses on the
commit or pull request. Repository administrators can separately configure
rules to require selected checks before merging. Common merge rules include:

- required status checks;
- one or more approving reviews, possibly from code owners;
- all review conversations resolved;
- branch must be up to date with its base;
- restrictions on who may push or merge;
- signed commits or linear history.

The rules are configured in GitHub repository settings or rulesets; they are
not defined by adding a `required: true` field to a workflow. In workflow YAML,
`required: true` can instead describe an input to a manually started workflow.
Likewise, a `CODEOWNERS` file names owners, but it does not by itself require
their approval; an applicable review rule must enforce that.

### What could be verified here

The GitHub branch listing reported `master` with `protected: false` when
checked. This indicates no classic branch-protection setting was reported for
that branch by the listing. This checkout does **not** reveal whether a
repository ruleset, organization-level rule, or other GitHub-side policy
applies. Therefore, this report cannot certify that no merge-protection
requirements exist or identify the repository's actual required-check names.
Those must be checked in the repository's **Settings → Rules → Rulesets** and
**Settings → Branches** (and, if applicable, organization rulesets).

## What “suspend” and “remove” mean

### Suspend Actions

Disabling GitHub Actions for the repository, or disabling selected workflows,
stops future workflow runs without deleting their YAML history. This also stops
automation unrelated to PR gating, such as releases, security scans, scheduled
budget checks, and branch cleanup. Existing run records remain available.

### Remove workflow files

Deleting workflow YAML files from the repository prevents those definitions
from running on future events after the deletion is merged. It does not
automatically remove branch-protection rules, past run records, or checks
required in repository/ruleset settings.

### Remove merge-protection checks

Changing required status checks, approvals, or other merge conditions must be
done in GitHub repository or organization settings/rulesets. This is independent
of deleting workflow YAML. If a required check is deleted or renamed without
updating the rule, affected pull requests may remain blocked while waiting for
the old check.

## Practical cautions

1. First determine which checks are actually required on `master` and which
   protections are enforced by repository or organization rulesets.
2. Distinguish required merge gates from informational, scheduled, release,
   and non-blocking workflows. The `continue-on-error` setting makes individual
   steps non-blocking, but does not necessarily make the whole workflow
   non-required.
3. Before disabling or deleting a required workflow, update the corresponding
   ruleset/branch-protection check list in the same change window.
4. Prefer disabling only the specific workflow that is unwanted rather than
   turning off all Actions, unless the intent is to stop all automation.
5. Treat required reviews and other repository rules separately from CI status
   checks; removing workflows does not remove those review requirements.

No workflow or merge-protection setting was changed as part of preparing this
report.
