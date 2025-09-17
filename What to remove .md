What to remove (GDW/GWU-specific)

The entire gdw/ tree. 
GitHub

Any files whose path or filename contains gdw/GWU (schemas, specs, docs, sample data, UI bits, etc.).

Any GUI tabs/panels that were for GDW (inside gui_terminal/, if present). 
GitHub

Docs that pitch GDW/GWU (look under docs/, specs/, and root *.md). 
GitHub

Any capability/config entries tied to GDW (under capabilities/, config/, schema/). 
GitHub

What to keep (execution tool)

Core CLI and commands: src/cli_multi_rapid (greet/sum/run-job), plus tests. 
GitHub

Workflow runner & phases: workflows/ (if you still want light orchestration). 
GitHub

Tool registry + health probe: config/, scripts/ipt_tools_ping.py, state/. 
GitHub

Event bus service (optional but useful glue): services/event_bus/. 
GitHub

CI, hooks, Docs that discuss general execution: .github/, scripts/, README*.md. 
GitHub

10-minute cleanup (copy/paste)
1) Make a branch (safe sandbox)
git checkout -b chore/remove-gdw

2) List all GDW/GWU hits (content + paths)
# If you have ripgrep:
rg -n --hidden -S -e '\bGDW\b|\bGWU\b|gdw\.|Brick Builder|gdw\.lock|chain\.spec' -g '!*.png' -g '!*.jpg'

# Fallback with git grep:
git grep -nI -E 'GDW|GWU|gdw\.|Brick Builder|gdw\.lock|chain\.spec'

3) Delete GDW/GWU directories & files
# Remove the dedicated folder (if present)
test -d gdw && git rm -r gdw

# Remove any file whose *path* contains '/gdw/' (case-insensitive)
git ls-files | awk 'BEGIN{IGNORECASE=1}/(^|\/)gdw(\/|$)/{print}' | xargs -r git rm

# Remove filenames that *contain* gdw (schemas/specs/docs)
git ls-files | awk 'BEGIN{IGNORECASE=1}/gdw.*\.(json|yaml|yml|md|py|ts)$/ {print}' | xargs -r git rm


If you use PowerShell on Windows:

# Folder
if (Test-Path gdw) { git rm -r gdw }

# Paths containing \gdw\
git ls-files | Where-Object { $_ -match '(?i)(^|/|\\)gdw(\\|/|$)' } | % { git rm $_ }

# Filenames containing gdw.*
git ls-files | Where-Object { $_ -match '(?i)gdw.*\.(json|ya?ml|md|py|ts)$' } | % { git rm $_ }

4) Sanitize remaining files (remove/neutralize wording)

Choose one approach:

A. Replace “GDW/GWU” with neutral execution terms

git grep -l -I -E 'GDW|GWU' \
| xargs -r sed -i.bak -E 's/\bGDW\b|\\bGWU\\b/execution pipeline/g'


B. Hard-remove any paragraphs that mention GDW/GWU

# Simple line-level removal:
git grep -l -I -E 'GDW|GWU' \
| xargs -r sed -i.bak -E '/GDW|GWU/d'


Then delete the backup files:

find . -name '*.bak' -delete

5) GUI: remove GDW tabs/panels (if any)

Search inside gui_terminal/ for the same tokens and delete the components/routes that are GDW-only, plus any menu entries that point to them. 
GitHub

6) Capabilities/config/schema scrub

Open capabilities/ and config/ and delete entries whose value or id references GDW/GWU.

In schema/, remove any gdw.* or *chain.spec*/*gdw.lock* schemas; then run a full-repo search to ensure nothing imports them. 
GitHub

7) Docs refresh (minimal edits)

Update or trim these to reflect “execution tool” only:

README.md (remove GDW pitch/sections). 
GitHub

INTERFACE_GUIDE.md (state that Python GUI Terminal is for launching jobs/tools, not GDW). 
GitHub

Any GDW pages under docs/ / specs/. 
GitHub

Quick one-liner to nuke entire GDW doc leafs:

git ls-files 'docs/**' 'specs/**' | grep -i gdw | xargs -r git rm

8) Dependency/CI check

Open pyproject.toml and requirements.txt → remove any GDW-only deps (keep generic ones). 
GitHub

Run tests & hooks:

pre-commit run -a || true
pytest -q || python -m unittest discover -s tests -v

9) Verify no leftovers
git grep -nI -E 'GDW|GWU|gdw\.|Brick Builder|gdw\.lock|chain\.spec' || echo "✅ No GDW/GWU references found."

10) Commit
git add -A
git commit -m "chore: remove GDW/GWU and sanitize repo to execution-only tool"

What this leaves you with (clean core)

CLI executor (src/cli_multi_rapid) with run-job for tasks.json / agent_jobs.yaml. 
GitHub

Optional workflow runner (workflows/) if you still want phase sequencing. 
GitHub

Tool registry + health probe (config/, scripts/ipt_tools_ping.py). 
GitHub

Event bus for lightweight orchestration (services/event_bus/). 
GitHub

If you want, I can draft a single PowerShell script (repo_sanitize_gdw.ps1) that runs all of the above with safety checks and a dry-run mode.

You said:
n draft a single PowerShell script (repo_sanitize_gdw.ps1) that runs all of the above with safety checks and a dry-run mode
ChatGPT said:
Thought for 1m 28s

Here’s a ready-to-use PowerShell script you can drop in your repo as repo_sanitize_gdw.ps1. It creates a safety branch, finds and removes GDW/GWU files, sanitizes remaining text, and shows a clear summary. It defaults to dry-run (no changes) so you can see exactly what would happen.

<#  repo_sanitize_gdw.ps1
    Purpose: Remove GDW/GWU artifacts and sanitize remaining files to return the repo
             to a clean "execution-only" tool. Safe by default (DryRun).

    Usage (dry run / preview):
      pwsh ./repo_sanitize_gdw.ps1

    Apply changes:
      pwsh ./repo_sanitize_gdw.ps1 -DryRun:$false

    Aggressive doc cleanup (remove GDW lines from docs):
      pwsh ./repo_sanitize_gdw.ps1 -DryRun:$false -SanitizeMode Remove

    Skip branch creation, allow dirty tree, and commit at the end:
      pwsh ./repo_sanitize_gdw.ps1 -DryRun:$false -SkipBranch -AllowDirty
#>

[CmdletBinding()]
param(
  [switch]$DryRun = $true,
  [string]$BranchName = "chore/remove-gdw",
  [switch]$AllowDirty,
  [ValidateSet("Replace","Remove")]
  [string]$SanitizeMode = "Replace",
  [string]$Replacement = "execution pipeline",
  [switch]$IncludeUntracked,
  [switch]$SkipBranch,
  [switch]$NoCommit,
  [string]$CommitMessage = "chore: remove GDW/GWU and sanitize repo to execution-only tool"
)

function Write-Note($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Do($msg)   { Write-Host "[DO]    $msg" -ForegroundColor Green }
function Write-Dry($msg)  { Write-Host "[DRY]   $msg" -ForegroundColor DarkGray }
function Fail($msg){ Write-Host "[ERR]   $msg" -ForegroundColor Red; exit 1 }

# Ensure Git is present
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Fail "Git not found in PATH."
}

# Ensure we're in a repo
$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { Fail "Not inside a Git repository." }
Set-Location $repoRoot
Write-Note "Repo root: $repoRoot"

# Optionally ensure clean working tree
if (-not $AllowDirty) {
  $status = (& git status --porcelain)
  if ($status) {
    Write-Warn "Working tree is not clean. Use -AllowDirty to proceed anyway."
    Fail   "Aborting to avoid accidental data loss."
  }
}

# Create safety branch
if (-not $SkipBranch) {
  $currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
  if ($currentBranch -ne $BranchName) {
    if ($DryRun) {
      Write-Dry "Would create and switch to branch: $BranchName"
    } else {
      Write-Do  "Creating branch: $BranchName"
      git checkout -b $BranchName | Out-Null
    }
  } else {
    Write-Note "Already on branch: $BranchName"
  }
} else {
  Write-Note "Skipping branch creation per -SkipBranch."
}

# Collect tracked files (and optionally untracked)
$tracked = (& git ls-files -z) -split "`0" | Where-Object { $_ }
$allFiles = @($tracked)
if ($IncludeUntracked) {
  $untracked = (& git ls-files --others --exclude-standard -z) -split "`0" | Where-Object { $_ }
  $allFiles += $untracked
  Write-Note "Including untracked files for scanning."
}

# Define patterns
$dirKillRegex   = '(?i)(^|[\\/])gdw([\\/]|$)'  # any dir path containing /gdw/
$fileNameKill   = '(?i)gdw.*\.(json|ya?ml|md|py|ts)$'
$schemaKill     = '(?i)(^|[\\/])schema[\\/].*(gdw|chain\.spec|gdw\.lock)'
$docLeafKill    = '(?i)(^|[\\/])(docs|specs)[\\/].*gdw'
$guiGdwPath     = '(?i)(^|[\\/])gui_terminal[\\/].*gdw'

# Tokens to scan in content
$tokens = @('GDW','GWU','gdw.lock','Brick Builder','chain.spec')

# PHASE 1: Identify paths to delete
$toDelete = New-Object System.Collections.Generic.List[string]
foreach ($p in $allFiles) {
  if ($p -match $dirKillRegex) { $toDelete.Add($p); continue }
  if ($p -match $fileNameKill) { $toDelete.Add($p); continue }
  if ($p -match $schemaKill)   { $toDelete.Add($p); continue }
  if ($p -match $docLeafKill)  { $toDelete.Add($p); continue }
  if ($p -match $guiGdwPath)   { $toDelete.Add($p); continue }
}
$toDelete = $toDelete | Sort-Object -Unique

# Special-case whole "gdw" directory if present and tracked
if (Test-Path "$repoRoot/gdw") {
  # Confirm at least one tracked file within gdw/
  $gdwTracked = $tracked | Where-Object { $_ -match '(?i)(^|[\\/])gdw([\\/]|$)' }
  if ($gdwTracked.Count -gt 0) {
    $toDelete = @("gdw") + ($toDelete | Where-Object { $_ -ne "gdw" })
  }
}

# PHASE 2: Sanitize content in-place
# We only modify text-like files; binary likely to break. Define a conservative set of extensions.
$textExt = @(
  '.md','.rst','.txt','.py','.ps1','.psm1','.psd1','.ts','.tsx','.js','.jsx',
  '.json','.yml','.yaml','.toml','.ini','.cfg','.pyi','.css','.html','.xml'
)

$sanitizedPlans = @()  # records of planned or actual changes
function IsTextFile($path) {
  $ext = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
  return $textExt -contains $ext
}
function ContainsAnyToken($path, $patterns) {
  try {
    return Select-String -Path $path -Pattern $patterns -SimpleMatch -Quiet -ErrorAction Stop
  } catch { return $false }
}

# Build a set of files to consider for sanitizing (exclude those slated for deletion)
$deleteSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$toDelete | ForEach-Object { [void]$deleteSet.Add($_) }

$sanitizeTargets = @()
foreach ($p in $allFiles) {
  if (-not (Test-Path $p)) { continue }
  if ($deleteSet.Contains($p)) { continue }
  if (-not (IsTextFile $p)) { continue }
  if (ContainsAnyToken $p $tokens) { $sanitizeTargets += $p }
}

# Helper for safe write
function Set-FileContent([string]$path, [string]$text) {
  $enc = New-Object System.Text.UTF8Encoding($false) # no BOM
  [System.IO.File]::WriteAllText($path, $text, $enc)
}

# Perform sanitization plan
foreach ($file in $sanitizeTargets) {
  $raw = Get-Content -LiteralPath $file -Raw
  $orig = $raw

  $changes = 0

  # Mode: Replace → replace "GDW"/"GWU" tokens with a neutral term
  if ($SanitizeMode -eq 'Replace') {
    $raw = $raw -replace '\bGDW\b', [System.Text.RegularExpressions.Regex]::Escape($Replacement)
    $raw = $raw -replace '\bGWU\b', [System.Text.RegularExpressions.Regex]::Escape($Replacement)
    # Light neutralization (strings that can remain as labels, not schema keys)
    $raw = $raw -replace 'gdw\.lock','artifact.lock'
    $raw = $raw -replace 'chain\.spec','chain.contract'
    if ($raw -ne $orig) { $changes++ }
  }

  # Mode: Remove → delete lines mentioning GDW/GWU in docs only (avoid breaking JSON/YAML)
  if ($SanitizeMode -eq 'Remove') {
    $ext = [IO.Path]::GetExtension($file).ToLowerInvariant()
    $docExt = @('.md','.rst','.txt')
    if ($docExt -contains $ext) {
      $lines = $orig -split "(`r`n|`n)"
      $kept  = $lines | Where-Object {
        ($_ -notmatch '\bGDW\b') -and
        ($_ -notmatch '\bGWU\b') -and
        ($_ -notmatch 'gdw\.lock') -and
        ($_ -notmatch 'Brick Builder') -and
        ($_ -notmatch 'chain\.spec')
      }
      $raw = ($kept -join "`r`n")
      if ($raw -ne $orig) { $changes++ }
    } else {
      # For non-docs, fall back to Replace to avoid breaking syntax
      $raw = $raw -replace '\bGDW\b', [System.Text.RegularExpressions.Regex]::Escape($Replacement)
      $raw = $raw -replace '\bGWU\b', [System.Text.RegularExpressions.Regex]::Escape($Replacement)
      $raw = $raw -replace 'gdw\.lock','artifact.lock'
      $raw = $raw -replace 'chain\.spec','chain.contract'
      if ($raw -ne $orig) { $changes++ }
    }
  }

  if ($changes -gt 0) {
    if ($DryRun) {
      Write-Dry "Would sanitize: $file"
    } else {
      Write-Do  "Sanitizing: $file"
      # Save .bak for safety
      Copy-Item -LiteralPath $file -Destination "$file.bak" -Force
      Set-FileContent -path $file -text $raw
    }
    $sanitizedPlans += [pscustomobject]@{ File=$file; Mode=$SanitizeMode }
  }
}

# PHASE 3: Delete files/dirs
if ($toDelete.Count -gt 0) {
  Write-Note "Targets to delete: $($toDelete.Count)"
  foreach ($p in $toDelete) {
    if ($DryRun) {
      Write-Dry "Would git rm: $p"
    } else {
      Write-Do  "git rm: $p"
      # If "gdw" directory marker, do recursive remove, else remove the path
      if ($p -ieq 'gdw' -and (Test-Path "$repoRoot/gdw")) {
        & git rm -r -- "gdw" | Out-Null
      } else {
        & git rm -- "$p" | Out-Null
      }
    }
  }
} else {
  Write-Note "No files matched deletion rules."
}

# PHASE 4: Cleanup .bak (only if not DryRun)
if (-not $DryRun) {
  $baks = Get-ChildItem -Recurse -Filter *.bak -File -ErrorAction SilentlyContinue
  foreach ($b in $baks) {
    # Keep a backup; comment next two lines if you prefer to retain .bak files
    # Write-Do "Removing backup: $($b.FullName)"
    # Remove-Item -LiteralPath $b.FullName -Force
    Write-Note "Backup created: $($b.FullName)"
  }
}

# PHASE 5: Residual scan
Write-Note "Residual scan for GDW/GWU tokens…"
$grep = & git grep -nI -E 'GDW|GWU|gdw\.lock|Brick Builder|chain\.spec' 2>$null
if ($grep) {
  Write-Warn "References still present (manual review recommended):`n$grep"
} else {
  Write-Note "No remaining matches for GDW/GWU token set."
}

# PHASE 6: Commit
if ($NoCommit) {
  Write-Note "Skipping commit per -NoCommit."
} else {
  if ($DryRun) {
    Write-Dry "Would git add -A && git commit -m '$CommitMessage'"
  } else {
    Write-Do  "Committing changes"
    git add -A
    # Only commit if there is something to commit
    $needsCommit = (& git status --porcelain)
    if ($needsCommit) {
      git commit -m $CommitMessage | Out-Null
      Write-Note "Commit created."
    } else {
      Write-Note "Nothing to commit."
    }
  }
}

# Summary
Write-Host ""
Write-Host "========== SUMMARY ==========" -ForegroundColor Cyan
Write-Host ("Mode:         {0}" -f ($(if($DryRun){"DRY RUN (no changes)"}else{"APPLIED"})))
Write-Host ("Branch:       {0}" -f $BranchName)
Write-Host ("Deleted:      {0}" -f $toDelete.Count)
Write-Host ("Sanitized:    {0}" -f $sanitizedPlans.Count)
Write-Host ("SanitizeMode: {0}" -f $SanitizeMode)
Write-Host "=============================" -ForegroundColor Cyan

What it does

Creates a safety branch (unless -SkipBranch).

Finds and removes GDW/GWU folders, schema/doc leafs, and filenames (gdw*, gdw.lock, chain.spec, etc.).

Sanitizes remaining files:

Replace mode (default): swaps GDW/GWU → “execution pipeline” and neutralizes gdw.lock → artifact.lock, chain.spec → chain.contract.

Remove mode: deletes lines mentioning GDW/GWU in docs (.md/.rst/.txt), uses Replace for code/config to avoid breaking structure.

Shows any residual references via git grep so you know what to review manually.

Commits the changes (unless -NoCommit), with .bak backups left in place for anything edited.