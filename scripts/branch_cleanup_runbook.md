# Branch Cleanup Runbook

> **Context:** This runbook was generated because the Copilot sandbox cannot push directly to the `master`
> protected branch or call the GitHub API with admin privileges.
> Execute these steps from a terminal with push access to `DICKY1987/eafix-modular`, or follow the
> GitHub UI steps where noted.

---

## Prerequisites

```bash
# Clone (or update) the repo
git clone https://github.com/DICKY1987/eafix-modular.git
cd eafix-modular

# Fetch all remote refs
git fetch --all --prune
```

---

## Part 1 — Merge unmerged branches into `master`

Two branches are not yet merged into `master`:

| Branch | Description |
|---|---|
| `copilot/create-archived-auth-doc-folder` | Creates `EAFIX_auth_docs/Archived_Auth_Doc/` and moves legacy files into it |
| `copilot/resolve-conflict-in-pr-29` | Resolves conflicts from PR #29 CI-retarget workflow |

### Option A — GitHub UI (recommended, no local steps)

1. Open: <https://github.com/DICKY1987/eafix-modular/compare/master...copilot/create-archived-auth-doc-folder>
   - Click **Create pull request** → fill title → **Create pull request**
   - If GitHub shows conflicts, use **Resolve conflicts** in-UI:
     - For every file under `EAFIX_auth_docs/Archived_Auth_Doc/` accept the **incoming (head branch)** version
     - Mark as resolved → **Commit merge**
   - Click **Merge pull request** → **Confirm merge**

2. Open: <https://github.com/DICKY1987/eafix-modular/compare/master...copilot/resolve-conflict-in-pr-29>
   - Click **Create pull request** → fill title → **Create pull request**
   - No conflicts expected — click **Merge pull request** → **Confirm merge**

### Option B — Local merge + push (requires admin / bypass branch protection)

```bash
git checkout master
git pull origin master

# --- Branch 1: create-archived-auth-doc-folder ---
git merge --no-ff origin/copilot/create-archived-auth-doc-folder \
  -m "Merge branch 'copilot/create-archived-auth-doc-folder' into master"

# If conflict (rename/delete on Archived_Auth_Doc files):
#   Accept the incoming (branch) version — keep the archived files
git checkout --theirs \
  EAFIX_auth_docs/Archived_Auth_Doc/VSCODE_INTEGRATION.md \
  EAFIX_auth_docs/Archived_Auth_Doc/VSCODE_SETUP.md \
  EAFIX_auth_docs/Archived_Auth_Doc/decomposition_model.docx \
  EAFIX_auth_docs/Archived_Auth_Doc/decomposition_model.json \
  EAFIX_auth_docs/Archived_Auth_Doc/decomposition_plan_ph1_ph2.json \
  EAFIX_auth_docs/Archived_Auth_Doc/decomposition_plan_ph3_ph4.json
git add EAFIX_auth_docs/Archived_Auth_Doc/
git commit --no-edit

# --- Branch 2: resolve-conflict-in-pr-29 ---
git merge --no-ff origin/copilot/resolve-conflict-in-pr-29 \
  -m "Merge branch 'copilot/resolve-conflict-in-pr-29' into master"
# No conflicts expected; commit is automatic

git push origin master
```

---

## Part 2 — Delete stale merged remote branches

After Part 1 is complete, all of the following branches will be fully merged into `master`
and can be safely deleted.

### Option A — GitHub UI

Go to <https://github.com/DICKY1987/eafix-modular/branches> and delete each branch listed below.

### Option B — Single `git push` command

```bash
git push origin --delete \
  copilot/ac7e5e30b9efe5bd46112f61ea3c9ccecd6000c5 \
  copilot/check-individual-manifest-schemes \
  copilot/copiloteafix-auth-docs-consolidation \
  copilot/create-archived-auth-doc-folder \
  copilot/create-evidence-inventory \
  copilot/delete-merged-branches \
  copilot/delete-old-branches \
  copilot/describe-conflicts-in-pr-31 \
  copilot/documentation-module-connections \
  copilot/fixglossary-filename-remediation \
  copilot/identify-34-modules \
  copilot/identify-new-architecture-modules \
  copilot/identify-number-of-pull-requests \
  copilot/reduce-number-of-branches \
  copilot/resolve-conflict-in-pr-29 \
  copilot/resolve-pr-31-conflicts
```

> **Note:** `main` is an alias tracking `master` — do **not** delete it unless you intend to
> remove the `main` branch entirely.

### Option C — `gh` CLI (one-liner)

```bash
gh auth login   # if not already authenticated

for branch in \
  copilot/ac7e5e30b9efe5bd46112f61ea3c9ccecd6000c5 \
  copilot/check-individual-manifest-schemes \
  copilot/copiloteafix-auth-docs-consolidation \
  copilot/create-archived-auth-doc-folder \
  copilot/create-evidence-inventory \
  copilot/delete-merged-branches \
  copilot/delete-old-branches \
  copilot/describe-conflicts-in-pr-31 \
  copilot/documentation-module-connections \
  copilot/fixglossary-filename-remediation \
  copilot/identify-34-modules \
  copilot/identify-new-architecture-modules \
  copilot/identify-number-of-pull-requests \
  copilot/reduce-number-of-branches \
  copilot/resolve-conflict-in-pr-29 \
  copilot/resolve-pr-31-conflicts; do
  gh api repos/DICKY1987/eafix-modular/git/refs/heads/"$branch" -X DELETE && echo "Deleted $branch"
done
```

---

## Part 3 — Verify clean state

```bash
git fetch --all --prune

echo "=== Remote branches merged into master ==="
git branch -r --merged origin/master | grep -v 'origin/master\|origin/main\|origin/HEAD'

echo "=== Remote branches NOT merged into master ==="
git branch -r --no-merged origin/master | grep -v 'origin/HEAD'
```

Expected output after all steps:
- **Merged list:** empty (or only `origin/main` if kept as alias)
- **Not-merged list:** empty

---

## Why these instructions exist

The Copilot sandbox runs with a scoped token that:
- Cannot push to `master` (protected branch rule)
- Cannot call the GitHub REST/GraphQL API directly
- Cannot run `gh pr merge` with admin bypass

All git work was completed locally in the sandbox (merges resolved, commits created), but
the final `git push origin master` was rejected. Running the commands above from your own
authenticated terminal or GitHub UI will complete the task.
