# Safe Merge Strategy with Execution Patterns

**Created**: 2025-11-26T14:23:00Z  
**Status**: Ready for Execution  
**Risk Level**: LOW → MEDIUM (Has unstaged changes to address)  
**Pattern**: EXEC-005 (Safe Git Merge with Validation)

---

## Executive Summary

This strategy provides a **safe, repeatable pattern** for merging outstanding work while preserving current unstaged changes and maintaining repository integrity.

**Current State**:
- ✅ 4 copilot branches already analyzed (SAFE_MERGE_PLAN.md)
- ⚠️ 3 unstaged changes in working directory
- ✅ Clean main branch (up to date with origin)
- ✅ No active PRs (all previous branches merged)

**Strategy**: Stash → Merge → Validate → Restore → Commit

---

## Phase 0: Current State Analysis

### Unstaged Changes (Must Preserve)

```
Modified:
  - aider/templates/prompts/workstream_v1.1_codex.txt.j2 (24 lines changed)
  - ccpm (submodule, modified content)
  - legacy/AI_MANGER_archived_2025-11-22 (submodule, modified content + untracked)

Untracked:
  - ToDo_Task/Folder Purpose Descriptions.md
  - ToDo_Task/READMEALL/ (multiple files)
  - docs/reference/tools/CODEX.md
```

### Risk Assessment

| Risk Factor | Status | Mitigation |
|-------------|--------|------------|
| **Lose unstaged work** | 🟡 MEDIUM | Stash before merge |
| **Merge conflicts** | 🟢 LOW | Branches verified clean |
| **Submodule conflicts** | 🟡 MEDIUM | Update submodules after merge |
| **Breaking changes** | 🟢 LOW | All branches are docs/structure only |

---

## Execution Pattern: EXEC-005 (Safe Merge with State Preservation)

### Pattern Overview

**Input**: N branches to merge, M unstaged changes  
**Output**: All branches merged, all changes preserved, clean state  
**Time**: 20-30 minutes  
**Complexity**: Medium (submodules + unstaged changes)

### Pattern Steps

```
1. SAVE_STATE    → Stash all changes (staged + unstaged)
2. VERIFY_CLEAN  → Confirm working directory clean
3. MERGE_BRANCH  → Merge one branch (--no-ff)
4. VALIDATE      → Quick validation (compile check)
5. COMMIT        → Push to origin
6. REPEAT 3-5    → For each remaining branch
7. RESTORE_STATE → Pop stash
8. VERIFY_FINAL  → Confirm all changes present
```

---

## Phase 1: Pre-Merge Preparation (5 minutes)

### Step 1.1: Backup Current State

```powershell
# Create safety snapshot
git add -A
git stash push -u -m "Pre-merge snapshot $(Get-Date -Format 'yyyy-MM-dd-HHmm')"

# Verify stash created
git stash list
# Expected: stash@{0}: On main: Pre-merge snapshot 2025-11-26-1423
```

**Success Criteria**: Stash shows 3 modified files + 3 untracked files

---

### Step 1.2: Verify Clean State

```powershell
# Confirm working directory clean
git status

# Expected output:
# On branch main
# Your branch is up to date with 'origin/main'.
# nothing to commit, working tree clean
```

**Guard**: If NOT clean, abort and investigate

---

### Step 1.3: Fetch Latest Remote State

```powershell
# Get latest refs from origin
git fetch --all --prune

# List available branches
git branch -r | Select-String "copilot/"
```

**Expected**: 0 copilot branches (all already merged based on git log)

---

## Phase 2: Outstanding Branches Analysis

### Reality Check ✅

Based on git log analysis, **all 4 copilot branches were already merged**:

```
Commits found in main:
- 15fb92f: merge: Add comprehensive specification documentation
- 94450dc: merge: Add AIM module structure documentation
- (Earlier merges for other 2 branches)
```

**Conclusion**: No outstanding branches to merge! 🎉

---

## Phase 3: Alternative Actions (Since No PRs Outstanding)

### Option A: Commit Unstaged Work (Recommended) ⭐

Since there are no PRs to merge, focus on committing current work:

```powershell
# Restore stashed changes
git stash pop

# Review changes
git status
git diff aider/templates/prompts/workstream_v1.1_codex.txt.j2

# Stage specific changes
git add aider/templates/prompts/workstream_v1.1_codex.txt.j2
git add docs/reference/tools/CODEX.md
git add "ToDo_Task/Folder Purpose Descriptions.md"
git add ToDo_Task/READMEALL/

# Create descriptive commit
git commit -m "docs: Update Codex documentation and folder descriptions

- Enhanced workstream v1.1 Codex template prompts
- Added CODEX tool reference documentation
- Added folder purpose descriptions for task organization
- Generated comprehensive README files for all project directories"

# Push to origin
git push origin main
```

**Time**: 5 minutes  
**Risk**: 🟢 LOW (documentation only)

---

### Option B: Handle Submodule Changes

The submodules show modifications. Determine the action:

```powershell
# Check submodule status
git submodule status

# Update submodules to latest
git submodule update --remote --merge

# Or commit submodule pointer updates
git add ccpm
git add legacy/AI_MANGER_archived_2025-11-22
git commit -m "chore: Update submodule references"
git push origin main
```

**Decision Point**: Do you want to:
1. Update submodules to latest upstream? → `git submodule update --remote`
2. Commit current submodule state? → `git add <submodule> && git commit`
3. Ignore submodule changes? → `git submodule update --init`

---

## Phase 4: Validation Pattern (Post-Commit)

### Validation Checklist

```powershell
# 1. Verify git status clean
git status
# Expected: "nothing to commit, working tree clean"

# 2. Verify all files present
Test-Path "docs\reference\tools\CODEX.md"
Test-Path "ToDo_Task\Folder Purpose Descriptions.md"

# 3. Verify Python imports still work
python -m compileall core/ error/ aim/ -q
# Expected: Exit code 0 (no syntax errors)

# 4. Verify commit pushed
git log --oneline -1
git log origin/main --oneline -1
# Expected: Both show same commit hash

# 5. Quick smoke test (optional)
python -c "from core.state import db; print('✓ Core imports OK')"
python -c "from error.engine import error_engine; print('✓ Error imports OK')"
```

**Success Criteria**: All checks pass ✅

---

## Phase 5: Rollback Plan (If Needed)

### If Issues During Commit

```powershell
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Or discard commit and changes
git reset --hard HEAD~1

# Restore from stash
git stash pop
```

### If Issues After Push

```powershell
# Revert the commit (creates new commit)
git revert HEAD
git push origin main

# Or force rollback (destructive - use with caution)
git reset --hard HEAD~1
git push --force origin main
```

### Emergency Recovery

```powershell
# Find your stash (even if popped)
git fsck --lost-found
git reflog

# Restore from specific stash
git stash apply stash@{0}

# Or restore from reflog
git reset --hard HEAD@{1}
```

---

## Execution Pattern Library

### EXEC-005.1: Simple File Commit

**When**: No merge needed, just commit changes  
**Time**: 5 min  
**Risk**: LOW

```powershell
git add <files>
git commit -m "<type>: <description>"
git push origin main
```

---

### EXEC-005.2: Stash + Merge + Restore

**When**: Have unstaged changes + need to merge branch  
**Time**: 15 min  
**Risk**: MEDIUM

```powershell
# Save state
git stash push -u -m "Backup before merge"

# Merge
git merge --no-ff <branch>
git push origin main

# Restore
git stash pop

# Resolve any conflicts
git add <resolved-files>
git commit -m "merge: Resolved conflicts after stash pop"
```

---

### EXEC-005.3: Submodule Safe Update

**When**: Submodules show modifications  
**Time**: 10 min  
**Risk**: MEDIUM

```powershell
# Check submodule status
git submodule status
git diff --submodule

# Update to latest
git submodule update --remote --merge

# Verify submodule state
cd <submodule-path>
git status
git log -1
cd ..

# Commit pointer update
git add <submodule>
git commit -m "chore: Update <submodule> to latest"
git push origin main
```

---

### EXEC-005.4: Multi-Branch Sequential Merge

**When**: N branches to merge, no local changes  
**Time**: 3-5 min per branch  
**Risk**: LOW (if verified clean)

```powershell
# For each branch:
$branches = @(
    "origin/branch1",
    "origin/branch2",
    "origin/branch3"
)

foreach ($branch in $branches) {
    Write-Host "Merging $branch..." -ForegroundColor Cyan
    
    # Merge
    git merge --no-ff $branch -m "merge: $(git log -1 --pretty=%s $branch)"
    
    # Quick validation
    $result = git status --porcelain
    if ($result) {
        Write-Host "⚠️ Unexpected changes after merge!" -ForegroundColor Yellow
        git status
        break
    }
    
    # Push
    git push origin main
    Write-Host "✓ $branch merged successfully" -ForegroundColor Green
}
```

---

## Anti-Patterns to Avoid ❌

### ❌ Don't: Merge Without Stashing

```powershell
# BAD: Merge with unstaged changes
git merge origin/branch  # ❌ May cause conflicts with local changes
```

**Why**: Local changes can conflict with merge, creating messy state

---

### ❌ Don't: Force Push Without Backup

```powershell
# BAD: Force push without verification
git push --force origin main  # ❌ Can lose work
```

**Why**: Destructive and irreversible without reflog

---

### ❌ Don't: Ignore Submodule State

```powershell
# BAD: Commit without checking submodules
git add .
git commit -m "stuff"  # ❌ Submodule pointers may be broken
```

**Why**: Submodules may point to invalid commits

---

### ❌ Don't: Merge Without Pull

```powershell
# BAD: Merge without fetching latest
git merge origin/branch  # ❌ May merge stale refs
```

**Why**: Origin refs may be outdated

---

## Guard Checklist (Before Each Commit)

From `ANTI_PATTERN_GUARDS.md`:

- [ ] **No silent failures**: All commands checked for exit code
- [ ] **No hardcoded paths**: Use relative or config-based paths
- [ ] **Submodules verified**: `git submodule status` shows expected state
- [ ] **Clean imports**: `python -m compileall` exits 0
- [ ] **Commit message descriptive**: Type + scope + description
- [ ] **Changes staged correctly**: `git diff --staged` shows intended changes
- [ ] **No TODOs in committed code**: Search for `# TODO` before commit

---

## Recommended Action Plan

Based on current state analysis:

### ✅ Immediate Actions (Next 10 minutes)

1. **Restore stashed changes** (if stashed earlier)
2. **Review changes** in `aider/templates/prompts/workstream_v1.1_codex.txt.j2`
3. **Decide on submodules**: Update or commit current state
4. **Stage and commit** documentation changes
5. **Push to origin**
6. **Validate** with smoke tests

### 📋 Commands to Execute

```powershell
# 1. Restore work (if stashed)
git stash pop

# 2. Review changes
git status
git diff

# 3. Stage documentation files
git add aider/templates/prompts/workstream_v1.1_codex.txt.j2
git add docs/reference/tools/CODEX.md
git add "ToDo_Task/Folder Purpose Descriptions.md"
git add ToDo_Task/READMEALL/

# 4. Commit with descriptive message
git commit -m "docs: Update Codex documentation and folder descriptions

- Enhanced workstream v1.1 Codex template prompts (24 lines)
- Added CODEX tool reference documentation
- Added folder purpose descriptions for task organization
- Generated comprehensive README files for all project directories
- Supports improved AI agent context and navigation"

# 5. Handle submodules (choose one):
# Option A: Update to latest
git submodule update --remote --merge
git add ccpm legacy/AI_MANGER_archived_2025-11-22
git commit -m "chore: Update submodule references to latest"

# Option B: Reset to clean state
git submodule update --init

# 6. Push
git push origin main

# 7. Verify
git status
python -m compileall core/ -q
```

---

## Success Criteria

### Immediate Success ✅
- [ ] All documentation changes committed
- [ ] Submodule state clean
- [ ] No merge conflicts
- [ ] Changes pushed to origin
- [ ] Working directory clean

### Validation Success ✅
- [ ] Python imports still work (`compileall` exits 0)
- [ ] Git status shows clean tree
- [ ] Origin/main matches local main
- [ ] No lost work (all files present)

---

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Pre-merge prep | 5 min | 5 min |
| Commit changes | 5 min | 10 min |
| Handle submodules | 5 min | 15 min |
| Validation | 5 min | 20 min |
| **Total** | **20 min** | - |

---

## Notes

1. **No Outstanding PRs**: All 4 copilot branches were already merged in previous sessions
2. **Focus on Current Work**: Primary action is committing unstaged documentation changes
3. **Submodule Decision**: Determine whether to update or reset submodules
4. **Safe Pattern**: Stash → Work → Commit → Validate pattern ensures no data loss

---

## Reference Documents

- `SAFE_MERGE_PLAN.md` - Previous merge plan (already executed)
- `ANTI_PATTERN_GUARDS.md` - Guard checklist
- `HYBRID_IMPORT_EXECUTION_PATTERN.md` - Import fix pattern
- `.github/copilot-instructions.md` - Repository standards

---

**Status**: Ready for Execution ✅  
**Next Action**: Execute "Immediate Actions" section  
**Risk Level**: 🟢 LOW (documentation changes only)  
**Approval**: Awaiting user confirmation to proceed
