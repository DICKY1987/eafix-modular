# Technical Specification Git-TUI (Multi_Document Versioning Automation TUI)

## 1. System Overview

**Purpose**: PowerShell-based Terminal UI tool for executing all GitHub CLI commands with managed credentials, repository context, and parameter validation.

**Design Principles**:
- Zero-touch credential management via `gh auth` and PS SecretStore
- Deterministic execution with full audit trail
- Modular plugin architecture for command families
- Graceful degradation on missing dependencies

**Target Platform**: Windows 11, PowerShell 7.4+, with Linux/macOS compatibility path via `gum` UI primitives

---

## 2. Architecture Components

### 2.1 Directory Structure

```
mdva-tui/
├── bin/
│   └── gum.exe                    # Charm gum binary (Windows x64)
├── commands/
│   ├── gh-commands.json           # Parsed command tree
│   └── param-schemas.json         # Parameter definitions per command
├── lib/
│   ├── Core.psm1                  # Entry point, orchestration
│   ├── UI.psm1                    # gum wrappers, rendering
│   ├── GH-Executor.psm1           # Command execution, output capture
│   ├── GH-Repo.psm1               # repo family commands
│   ├── GH-Project.psm1            # project family commands
│   ├── GH-PR.psm1                 # pr family commands
│   ├── GH-Issue.psm1              # issue family commands
│   ├── GH-Workflow.psm1           # workflow family commands
│   ├── Auth.psm1                  # SecretStore, gh auth integration
│   ├── Config.psm1                # Profile management
│   └── Validator.psm1             # Input validation, schema checks
├── config/
│   └── profiles.json              # User profiles (last repo, dirs)
├── logs/
│   └── execution.log              # Audit trail
└── mdva-tui.ps1                   # Entry script
```

### 2.2 Data Flow

```
User Input → UI.psm1 (gum dropdowns/inputs)
          → Validator.psm1 (schema check)
          → GH-Executor.psm1 (spawn gh CLI)
          → Capture stdout/stderr/exit code
          → Display formatted output
          → Log to execution.log
```

---

## 3. Data Structures & Schemas

### 3.1 Command Tree Schema (`commands/gh-commands.json`)

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "repo": {
      "type": "object",
      "properties": {
        "create": {
          "params": [
            {"name": "name", "type": "string", "required": true},
            {"name": "description", "type": "string", "required": false},
            {"name": "private", "type": "boolean", "default": false}
          ],
          "flags": ["--public", "--private", "--enable-issues"],
          "description": "Create a new repository"
        },
        "clone": {
          "params": [
            {"name": "repository", "type": "repo", "required": true}
          ],
          "requiresLocalDir": true
        }
      }
    },
    "project": {
      "type": "object",
      "properties": {
        "item-add": {
          "params": [
            {"name": "project-url", "type": "url", "required": true},
            {"name": "content-id", "type": "string", "required": true}
          ]
        }
      }
    }
  }
}
```

**Generation Strategy**: Parse `GH_Commands.txt` + augment with parameter metadata from `gh <command> --help` scraping during build phase.

### 3.2 Profile Schema (`config/profiles.json`)

```json
{
  "version": "1.0",
  "lastUsed": {
    "repo": "DICKY1987/Multi-Document-Versioning-Automation",
    "localDir": "C:\\Users\\richg\\MOD\\Multi-Document Versioning Automation",
    "profile": "default"
  },
  "profiles": {
    "default": {
      "defaultRepo": "DICKY1987/Multi-Document-Versioning-Automation",
      "defaultDir": "C:\\Users\\richg\\MOD\\Multi-Document Versioning Automation",
      "defaultBranch": "main",
      "secrets": {
        "useVault": true,
        "vaultName": "mdva-tui"
      }
    }
  }
}
```

### 3.3 Execution Log Schema

```json
{
  "timestamp": "2025-11-11T14:23:01Z",
  "command": "gh repo create",
  "args": ["test-repo", "--public"],
  "workdir": "C:\\projects",
  "exitCode": 0,
  "duration": 2.34,
  "output": "✓ Created repository DICKY1987/test-repo"
}
```

---

## 4. Module Specifications

### 4.1 Core.psm1

**Responsibility**: Application lifecycle, module loading, main loop.

```powershell
# Pseudo-implementation
function Start-MdvaTui {
    [CmdletBinding()]
    param()
    
    # Prerequisites check
    Assert-Prerequisites  # gh, gum, PS 7+
    
    # Load configuration
    $config = Get-MdvaConfig
    
    # Auth check
    if (-not (Test-GhAuth)) {
        Write-Host "GitHub CLI not authenticated" -ForegroundColor Yellow
        gh auth login
    }
    
    # Main loop
    while ($true) {
        $ctx = Get-UserContext  # repo, dir from profile or prompt
        $command = Select-GhCommand  # UI dropdown
        if (-not $command) { break }
        
        $params = Get-CommandParams -Command $command  # Dynamic form
        Invoke-GhCommand -Command $command -Params $params -Context $ctx
        
        if (-not (Read-YesNo "Run another command?")) { break }
    }
}
```

### 4.2 UI.psm1

**Responsibility**: Abstraction over `gum` CLI for forms, dropdowns, confirmations.

```powershell
function Invoke-Dropdown {
    param(
        [string[]]$Items,
        [string]$Prompt = "Select:",
        [int]$Height = 15
    )
    
    $selected = & gum choose $Items --header $Prompt --height $Height
    if ($LASTEXITCODE -ne 0) { return $null }
    return $selected
}

function Invoke-Input {
    param(
        [string]$Placeholder,
        [string]$DefaultValue,
        [ValidateSet("text","password")]$Type = "text"
    )
    
    $args = @("input", "--placeholder", $Placeholder)
    if ($DefaultValue) { $args += @("--value", $DefaultValue) }
    if ($Type -eq "password") { $args += "--password" }
    
    $result = & gum @args
    if ($LASTEXITCODE -ne 0) { return $null }
    return $result
}

function Show-Form {
    param(
        [Parameter(Mandatory)]
        [PSCustomObject[]]$Fields  # [{name, type, required, default}]
    )
    
    $result = @{}
    foreach ($field in $Fields) {
        $value = Invoke-Input -Placeholder $field.name -DefaultValue $field.default
        if ($field.required -and [string]::IsNullOrEmpty($value)) {
            throw "Required field: $($field.name)"
        }
        $result[$field.name] = $value
    }
    return $result
}
```

### 4.3 GH-Executor.psm1

**Responsibility**: Spawn `gh` processes, capture output, handle errors.

```powershell
function Invoke-GhCommand {
    [CmdletBinding()]
    param(
        [string]$Command,
        [hashtable]$Params,
        [hashtable]$Context  # {repo, localDir}
    )
    
    # Build argument list
    $cmdParts = $Command -split ' '  # e.g., "repo create" → ["repo", "create"]
    $args = @($cmdParts)
    
    foreach ($key in $Params.Keys) {
        if ($Params[$key] -is [bool] -and $Params[$key]) {
            $args += "--$key"
        } else {
            $args += @("--$key", $Params[$key])
        }
    }
    
    # Set working directory
    Push-Location $Context.localDir
    
    try {
        # Execute with output capture
        $startTime = Get-Date
        $output = & gh @args 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
        $duration = (Get-Date) - $startTime
        
        # Log execution
        Add-ExecutionLog -Command "gh $Command" -Args $args -ExitCode $exitCode `
                         -Duration $duration.TotalSeconds -Output $output
        
        # Display result
        if ($exitCode -eq 0) {
            Write-Host "`n✓ Success`n" -ForegroundColor Green
            Write-Host $output
        } else {
            Write-Host "`n✗ Command failed (exit $exitCode)`n" -ForegroundColor Red
            Write-Host $output -ForegroundColor DarkRed
        }
        
        return @{
            Success = ($exitCode -eq 0)
            ExitCode = $exitCode
            Output = $output
        }
    }
    finally {
        Pop-Location
    }
}
```

### 4.4 Auth.psm1

**Responsibility**: Integrate with `gh auth` and PowerShell SecretStore.

```powershell
function Test-GhAuth {
    $result = gh auth status 2>&1
    return $LASTEXITCODE -eq 0
}

function Initialize-SecretVault {
    param([string]$VaultName = "mdva-tui")
    
    if (-not (Get-SecretVault -Name $VaultName -ErrorAction SilentlyContinue)) {
        Register-SecretVault -Name $VaultName -ModuleName Microsoft.PowerShell.SecretStore
        # Set vault password (prompt once, store in DPAPI)
        Set-SecretStoreConfiguration -Scope CurrentUser -Authentication Password `
                                      -PasswordTimeout 3600 -Interaction None
    }
}

function Get-MdvaSecret {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [string]$VaultName = "mdva-tui"
    )
    
    return Get-Secret -Name $Name -Vault $VaultName -AsPlainText -ErrorAction Stop
}

function Set-MdvaSecret {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [Parameter(Mandatory)]
        [SecureString]$Value,
        [string]$VaultName = "mdva-tui"
    )
    
    Set-Secret -Name $Name -Secret $Value -Vault $VaultName
}
```

### 4.5 Config.psm1

**Responsibility**: Load/save user profiles.

```powershell
function Get-MdvaConfig {
    $configPath = Join-Path $env:APPDATA "mdva-tui\profiles.json"
    
    if (-not (Test-Path $configPath)) {
        $default = @{
            version = "1.0"
            lastUsed = @{}
            profiles = @{
                default = @{
                    defaultRepo = ""
                    defaultDir = (Get-Location).Path
                }
            }
        }
        $default | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8
    }
    
    return Get-Content $configPath | ConvertFrom-Json
}

function Update-MdvaConfig {
    param(
        [Parameter(Mandatory)]
        [PSCustomObject]$Config
    )
    
    $configPath = Join-Path $env:APPDATA "mdva-tui\profiles.json"
    $Config | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8
}
```

### 4.6 Validator.psm1

**Responsibility**: Validate inputs against parameter schemas.

```powershell
function Test-CommandParams {
    param(
        [string]$Command,
        [hashtable]$Params,
        [PSCustomObject]$Schema
    )
    
    $definition = $Schema.$Command
    if (-not $definition) {
        throw "No schema found for command: $Command"
    }
    
    foreach ($param in $definition.params) {
        if ($param.required -and -not $Params.ContainsKey($param.name)) {
            throw "Missing required parameter: $($param.name)"
        }
        
        if ($Params.ContainsKey($param.name)) {
            switch ($param.type) {
                "repo" {
                    if ($Params[$param.name] -notmatch '^[^/]+/[^/]+$') {
                        throw "Invalid repo format: $($Params[$param.name]). Expected: owner/name"
                    }
                }
                "url" {
                    if ($Params[$param.name] -notmatch '^https?://') {
                        throw "Invalid URL: $($Params[$param.name])"
                    }
                }
            }
        }
    }
}
```

---

## 5. Execution Flow

### 5.1 Startup Sequence

```
1. Load Core.psm1 → import all modules
2. Check prerequisites:
   - PowerShell 7+
   - gh CLI installed & in PATH
   - gum.exe in bin/
3. Load config/profiles.json
4. Test gh auth status
   - If not authed: run gh auth login
5. Initialize SecretVault (if first run)
6. Enter main loop
```

### 5.2 Command Execution Lifecycle

```
1. User Context Phase
   - Prompt for repo (default from profile)
   - Prompt for local dir (default from profile)
   - Save as lastUsed in profile

2. Command Selection Phase
   - Load commands/gh-commands.json
   - Build category list (repo, pr, issue, project, workflow, etc.)
   - User selects category → dropdown of commands
   - User selects command

3. Parameter Collection Phase
   - Load param-schemas.json for selected command
   - Build dynamic form via Show-Form
   - Validate inputs via Test-CommandParams

4. Execution Phase
   - Push to local dir
   - Spawn gh CLI with args
   - Stream output to console
   - Capture exit code + duration
   - Pop location

5. Post-Execution Phase
   - Log to logs/execution.log
   - Display formatted result
   - Prompt: "Run another command?"
```

---

## 6. Security Model

### 6.1 Credential Storage

**GitHub Token**:
- **Primary**: Use `gh auth login` → token stored in OS credential manager
- **Read**: Tool reads via `gh auth status`, never touches token directly
- **Fallback**: If `GITHUB_TOKEN` env var present, `gh` uses it automatically

**Non-GitHub Secrets**:
- **Storage**: PowerShell SecretStore vault (DPAPI-encrypted on Windows)
- **Access**: `Get-MdvaSecret -Name "webhook-key"`
- **First-run**: Prompt for vault password, timeout 1 hour

### 6.2 Input Sanitization

```powershell
function Test-SafePath {
    param([string]$Path)
    
    # Prevent directory traversal
    if ($Path -match '\.\.[/\\]') {
        throw "Path contains directory traversal: $Path"
    }
    
    # Ensure absolute path
    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        throw "Path must be absolute: $Path"
    }
    
    return $true
}

function Test-SafeRepoName {
    param([string]$Repo)
    
    if ($Repo -notmatch '^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$') {
        throw "Invalid repository name: $Repo"
    }
    
    return $true
}
```

---

## 7. Error Handling Strategy

### 7.1 Levels

| Level | Handler | Action |
|-------|---------|--------|
| **Fatal** | Prerequisites missing | Exit with code 1, display install instructions |
| **Command** | `gh` exit code ≠ 0 | Display stderr, log, prompt retry |
| **Validation** | Invalid input | Re-prompt with error message |
| **Network** | Timeout, DNS failure | Retry 3x with exponential backoff |

### 7.2 Implementation Pattern

```powershell
function Invoke-WithRetry {
    param(
        [ScriptBlock]$Action,
        [int]$MaxRetries = 3,
        [int]$BaseDelay = 1
    )
    
    $attempt = 0
    while ($attempt -lt $MaxRetries) {
        try {
            return & $Action
        }
        catch {
            $attempt++
            if ($attempt -ge $MaxRetries) { throw }
            
            $delay = [Math]::Pow(2, $attempt - 1) * $BaseDelay
            Write-Warning "Attempt $attempt failed, retrying in $delay seconds..."
            Start-Sleep -Seconds $delay
        }
    }
}
```

### 7.3 Audit Trail

Every command execution writes to `logs/execution.log`:

```json
{
  "timestamp": "2025-11-11T14:23:01Z",
  "user": "richg",
  "command": "gh repo create",
  "args": ["test-repo", "--public"],
  "workdir": "C:\\projects",
  "exitCode": 0,
  "duration": 2.34,
  "output": "✓ Created repository DICKY1987/test-repo",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 8. Configuration Management

### 8.1 Profile Switching

```powershell
function Switch-MdvaProfile {
    param([string]$ProfileName)
    
    $config = Get-MdvaConfig
    if (-not $config.profiles.ContainsKey($ProfileName)) {
        throw "Profile not found: $ProfileName"
    }
    
    $config.lastUsed.profile = $ProfileName
    Update-MdvaConfig -Config $config
}
```

### 8.2 Environment Variables

Support override via env vars:

```powershell
$repo = $env:MDVA_DEFAULT_REPO ?? $config.profiles.default.defaultRepo
$dir = $env:MDVA_DEFAULT_DIR ?? $config.profiles.default.defaultDir
```

---

## 9. Testing Requirements

### 9.1 Unit Tests (Pester)

```powershell
Describe "Validator" {
    It "Rejects invalid repo names" {
        { Test-SafeRepoName -Repo "not a repo" } | Should -Throw
    }
    
    It "Accepts valid repo names" {
        { Test-SafeRepoName -Repo "owner/repo" } | Should -Not -Throw
    }
}

Describe "GH-Executor" {
    Mock gh { return "mocked output" }
    
    It "Executes command with correct args" {
        Invoke-GhCommand -Command "repo list" -Params @{} -Context @{localDir = "C:\temp"}
        Assert-MockCalled gh -ParameterFilter { $args -contains "repo" -and $args -contains "list" }
    }
}
```

### 9.2 Integration Tests

```powershell
# Test against real gh CLI in isolated test repo
Describe "End-to-End" {
    BeforeAll {
        # Setup test repo
        gh repo create test-mdva-tui --private
    }
    
    It "Creates issue in test repo" {
        $result = Invoke-GhCommand -Command "issue create" `
                                   -Params @{title="Test";body="Test issue"} `
                                   -Context @{repo="DICKY1987/test-mdva-tui"}
        $result.Success | Should -Be $true
    }
    
    AfterAll {
        # Cleanup
        gh repo delete test-mdva-tui --yes
    }
}
```

---

## 10. Dependencies & Prerequisites

### 10.1 Required

| Component | Version | Purpose | Install Method |
|-----------|---------|---------|----------------|
| PowerShell | 7.4+ | Runtime | `winget install Microsoft.PowerShell` |
| GitHub CLI | 2.40+ | Command backend | `winget install GitHub.cli` |
| gum | 0.13+ | TUI primitives | `winget install charmbracelet.gum` |
| SecretManagement | 1.1+ | Vault API | `Install-Module -Name Microsoft.PowerShell.SecretManagement` |
| SecretStore | 1.0+ | DPAPI vault | `Install-Module -Name Microsoft.PowerShell.SecretStore` |

### 10.2 Optional

- **Pester** 5.5+ - Unit testing framework
- **PSScriptAnalyzer** - Linting

### 10.3 Verification Script

```powershell
function Assert-Prerequisites {
    $checks = @(
        @{Name="PowerShell"; Test={$PSVersionTable.PSVersion.Major -ge 7}},
        @{Name="gh CLI"; Test={Get-Command gh -ErrorAction SilentlyContinue}},
        @{Name="gum"; Test={Test-Path "$PSScriptRoot\bin\gum.exe"}},
        @{Name="SecretManagement"; Test={Get-Module -ListAvailable Microsoft.PowerShell.SecretManagement}}
    )
    
    $failed = @()
    foreach ($check in $checks) {
        if (-not (& $check.Test)) {
            $failed += $check.Name
        }
    }
    
    if ($failed) {
        throw "Missing prerequisites: $($failed -join ', ')"
    }
}
```

---

## 11. Build & Distribution

### 11.1 Build Script

```powershell
# build.ps1
param([switch]$IncludeBinaries)

# Generate command metadata
& .\scripts\Parse-GhCommands.ps1 -InputFile .\GH_Commands.txt `
                                  -OutputJson .\commands\gh-commands.json

# Generate parameter schemas (scrape gh --help)
& .\scripts\Generate-ParamSchemas.ps1

# Bundle dependencies
if ($IncludeBinaries) {
    # Download gum.exe for Windows
    Invoke-WebRequest "https://github.com/charmbracelet/gum/releases/download/v0.13.0/gum_0.13.0_Windows_x86_64.zip" `
                      -OutFile gum.zip
    Expand-Archive gum.zip -DestinationPath .\bin\
}

# Package as module
New-ModuleManifest -Path .\mdva-tui.psd1 `
                   -ModuleVersion "1.0.0" `
                   -Author "DICKY1987" `
                   -Description "GitHub CLI TUI Orchestrator" `
                   -PowerShellVersion "7.4" `
                   -RequiredModules @("Microsoft.PowerShell.SecretManagement")
```

---

## 12. AI Implementation Guidance

### 12.1 Implementation Order

1. **Phase 1: Core Infrastructure**
   - Implement UI.psm1 (gum wrappers)
   - Implement Config.psm1 (profile loading)
   - Implement Auth.psm1 (gh auth checks)

2. **Phase 2: Command Execution**
   - Implement GH-Executor.psm1
   - Create gh-commands.json parser
   - Implement Validator.psm1

3. **Phase 3: Command Families**
   - Implement GH-Repo.psm1 (highest priority)
   - Implement GH-Project.psm1
   - Implement remaining families as needed

4. **Phase 4: Main Loop**
   - Implement Core.psm1
   - Wire up execution flow
   - Add error handling

5. **Phase 5: Polish**
   - Add logging
   - Add retry logic
   - Create tests

### 12.2 Critical Implementation Notes

- **Do not hardcode** `gh` command syntax; always read from `gh-commands.json`
- **Always validate** paths with `Test-SafePath` before `Push-Location`
- **Never store** plain-text credentials; use `gh auth` or SecretStore exclusively
- **Log every execution** with correlation ID for debugging
- **Handle CTRL+C** gracefully; clean up temp files and restore location

### 12.3 Extension Points

Future enhancements should add:
- Custom command aliases (stored in profiles.json)
- Batch execution (queue multiple commands)
- Webhook integration (trigger commands on events)
- Rich output parsing (convert JSON to tables via Spectre.Console)

---

**End of Specification**

This document contains all architectural decisions, data structures, code patterns, and implementation guidance needed to build MDVA-TUI. All code snippets are pseudocode for context; the implementing agent must write production-quality, error-handled implementations based on these patterns.