# Safe Merge Plan - Feature Branches to Main
**Generated**: 2025-11-28 05:39 UTC  
**Current Branch**: feature/safe-merge-patterns-complete  
**Target**: main

---

## Pre-Merge Status

### Branches to Merge
1. ✅ **feature/tui-panel-framework-v1** - Already merged via PR #44
2. ✅ **fix/test-collection-errors** - Already merged 18h ago
3. ⏳ **chore/add-untracked-files** - Needs merge (13h old, 6 commits)
4. ⏳ **feature/safe-merge-patterns-complete** - Needs merge (current, 1 commit)

### Branches to Keep
- ✅ **rollback/pre-main-merge-20251127-030912** - Tagged safety snapshot

### Safety Measures
- ✅ Pre-merge snapshot exists: `pre-merge-snapshot-20251127-030912`
- ✅ All feature branches pushed to origin
- ✅ Main is up-to-date with origin/main

---

## Execution Plan

### Phase 1: Prepare Current Branch (feature/safe-merge-patterns-complete)

#### Step 1.1: Stage and commit all changes
```bash
# Review what's being added
git status

# Add all changes (deleted files will be staged as deletions, new files added)
git add -A

# Commit with descriptive message
git commit -m "feat: consolidate safe merge patterns and reorganize documentation

- Move diagrams from assets/ to docs/diagrams/
- Relocate execution patterns to UETF structure
- Add pipeline tree utilities and validation
- Organize GUI/TUI documentation in gui/ module
- Update path configs and migration scripts"
```

#### Step 1.2: Push to origin
```bash
git push origin feature/safe-merge-patterns-complete
```

---

### Phase 2: Merge Outstanding Branches

#### Step 2.1: Switch to main and update
```bash
git checkout main
git pull origin main
```

#### Step 2.2: Create safety snapshot (optional but recommended)
```bash
# Tag current main for safety
git tag -a pre-multi-merge-$(date +%Y%m%d-%H%M%S) -m "Safety snapshot before merging feature branches"
git push origin --tags
```

#### Step 2.3: Merge chore/add-untracked-files
```bash
# Merge the chore branch
git merge chore/add-untracked-files --no-ff -m "Merge chore/add-untracked-files: Add autonomous doc generation"

# If conflicts occur:
# 1. Review conflicts: git status
# 2. Resolve manually or use: git mergetool
# 3. After resolving: git add <resolved-files>
# 4. Continue: git commit
```

#### Step 2.4: Merge feature/safe-merge-patterns-complete
```bash
# Merge the feature branch
git merge feature/safe-merge-patterns-complete --no-ff -m "Merge feature/safe-merge-patterns-complete: Consolidate merge patterns and docs"

# If conflicts occur:
# 1. Review conflicts: git status
# 2. Prioritize keeping the reorganized structure (docs/diagrams/, gui/, etc.)
# 3. Resolve: git mergetool or manual edit
# 4. Stage: git add <resolved-files>
# 5. Complete: git commit
```

---

### Phase 3: Validation

#### Step 3.1: Run quality gates
```bash
# Validate ACS conformance
python scripts/validate_acs_conformance.py

# Check deprecated paths (CI gate)
python scripts/paths_index_cli.py gate --db refactor_paths.db

# Validate workstreams
python scripts/validate_workstreams.py

# Run tests
pytest tests/ -q
```

#### Step 3.2: Review merge result
```bash
# Check status
git status

# Review recent commits
git log --oneline -10

# Verify no unexpected changes
git diff origin/main
```

---

### Phase 4: Push to Remote

#### Step 4.1: Push main
```bash
git push origin main
```

#### Step 4.2: Verify push succeeded
```bash
# Check remote status
git fetch origin
git status

# Verify main is synced
git log origin/main --oneline -5
```

---

### Phase 5: Cleanup

#### Step 5.1: Delete merged local branches
```bash
# Delete already-merged branches
git branch -d fix/test-collection-errors
git branch -d feature/tui-panel-framework-v1
git branch -d chore/add-untracked-files
git branch -d feature/safe-merge-patterns-complete
```

#### Step 5.2: Delete merged remote branches (optional)
```bash
# Only delete if confirmed merged and no longer needed
git push origin --delete fix/test-collection-errors
git push origin --delete feature/tui-panel-framework-v1
git push origin --delete chore/add-untracked-files
git push origin --delete feature/safe-merge-patterns-complete
```

#### Step 5.3: Keep safety branches
```bash
# DO NOT delete these:
# - rollback/pre-main-merge-20251127-030912 (tagged snapshot)
# - Any new snapshot tags created in Step 2.2
```

---

## Conflict Resolution Strategy

### Expected Conflicts

1. **Documentation reorganization**
   - Files moved from `assets/diagrams/` → `docs/diagrams/`
   - Files moved from root → `gui/`
   - **Resolution**: Accept incoming changes (new structure)

2. **Config file updates**
   - `config/path_index.yaml`, `config/section_map.yaml`
   - **Resolution**: Merge both changes, prioritize new paths

3. **Script modifications**
   - `scripts/migrate_imports.py`, `scripts/check_deprecated_usage.py`
   - **Resolution**: Review diffs, keep functional improvements

### Conflict Resolution Commands

```bash
# If merge conflicts occur:
# 1. List conflicts
git status | grep "both modified"

# 2. For each conflict, choose strategy:
# - Keep incoming: git checkout --theirs <file>
# - Keep current: git checkout --ours <file>
# - Manual merge: edit file, remove conflict markers

# 3. Stage resolved files
git add <resolved-files>

# 4. Complete merge
git commit
```

---

## Rollback Procedures

### If merge fails catastrophically

```bash
# Abort merge in progress
git merge --abort

# Return to tagged state
git reset --hard pre-multi-merge-<timestamp>

# Or use the existing rollback branch
git reset --hard rollback/pre-main-merge-20251127-030912
```

### If issues discovered after merge

```bash
# Create new branch from problematic main
git checkout -b hotfix/post-merge-issues

# Revert specific commits
git revert <commit-hash>

# Or reset to before merge (destructive)
git reset --hard <pre-merge-commit>
git push origin main --force  # DANGER: Only if no one else has pulled
```

---

## Post-Merge Verification Checklist

- [ ] All branches merged successfully
- [ ] No merge conflicts remaining
- [ ] `pytest tests/ -q` passes
- [ ] `python scripts/validate_acs_conformance.py` passes
- [ ] `python scripts/paths_index_cli.py gate --db refactor_paths.db` passes
- [ ] `git status` shows clean working directory
- [ ] `origin/main` is up-to-date
- [ ] Old feature branches deleted locally
- [ ] Remote feature branches deleted (optional)
- [ ] Safety tags/branches preserved
- [ ] Documentation reflects new structure

---

## Timeline Estimate

- Phase 1 (Prepare): **5 minutes**
- Phase 2 (Merge): **10-15 minutes** (20-30 if conflicts)
- Phase 3 (Validate): **5-10 minutes**
- Phase 4 (Push): **2 minutes**
- Phase 5 (Cleanup): **3 minutes**

**Total**: ~25-35 minutes (assuming minimal conflicts)

---

## Notes

1. **Current working directory has changes** - Must commit before switching branches
2. **File reorganization is significant** - Many files moved to new locations
3. **Two branches ready to merge** - chore/add-untracked-files + feature/safe-merge-patterns-complete
4. **CI gates exist** - Must pass path standards and ACS conformance
5. **Safety net exists** - Tagged rollback point available

---

## Quick Execution (Copy-Paste Script)

```bash
# Phase 1: Prepare current branch
git add -A
git commit -m "feat: consolidate safe merge patterns and reorganize documentation"
git push origin feature/safe-merge-patterns-complete

# Phase 2: Merge to main
git checkout main
git pull origin main
git tag -a pre-multi-merge-$(date +%Y%m%d-%H%M%S) -m "Safety snapshot"
git merge chore/add-untracked-files --no-ff -m "Merge chore/add-untracked-files"
git merge feature/safe-merge-patterns-complete --no-ff -m "Merge feature/safe-merge-patterns-complete"

# Phase 3: Validate
python scripts/validate_acs_conformance.py
python scripts/paths_index_cli.py gate --db refactor_paths.db
pytest tests/ -q

# Phase 4: Push
git push origin main

# Phase 5: Cleanup
git branch -d fix/test-collection-errors feature/tui-panel-framework-v1 chore/add-untracked-files feature/safe-merge-patterns-complete
```

**⚠️ Review output at each step before proceeding!**
