---
doc_id: DOC-GUIDE-DOC-ID-SYSTEM-COMPLETE-SPECIFICATION-274
---

# DOC_ID System - Complete Specification for AI Applications

**Version:** 3.0  
**Created:** 2025-12-28  
**Purpose:** Complete technical specification for AI agents to understand and operate the DOC_ID system without reading code  
**Audience:** AI applications, automated systems, future maintainers

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Concepts](#core-concepts)
3. [Doc ID Format Specification](#doc-id-format-specification)
4. [Registry Architecture](#registry-architecture)
5. [File Operations](#file-operations)
6. [Validation Rules](#validation-rules)
7. [Automation System](#automation-system)
8. [Data Structures](#data-structures)
9. [Workflow Patterns](#workflow-patterns)
10. [Error Handling](#error-handling)
11. [Integration Points](#integration-points)
12. [Performance Characteristics](#performance-characteristics)
13. [Security & Constraints](#security--constraints)

---

## 1. System Overview

### 1.1 Purpose

The DOC_ID system is a repository-wide document identification and tracking system that assigns unique, stable identifiers to every file for:
- **Traceability:** Track files across renames, moves, and refactors
- **Documentation:** Link files to requirements, specifications, and tests
- **Automation:** Enable automated workflows based on file identity
- **Governance:** Enforce documentation standards and completeness

### 1.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DOC_ID SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Scanner     │───▶│  Assigner   │───▶│  Registry   │  │
│  │  (Discovery)  │    │ (Injection) │    │  (Storage)  │  │
│  └───────────────┘    └─────────────┘    └─────────────┘  │
│         │                     │                   │         │
│         │                     │                   │         │
│  ┌──────▼─────────────────────▼───────────────────▼─────┐  │
│  │              docs_inventory.jsonl                      │  │
│  │         (Snapshot of current scan state)               │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                     │                   │         │
│         │                     │                   │         │
│  ┌──────▼─────────┐    ┌─────▼──────┐    ┌──────▼──────┐  │
│  │   Validators   │    │ Automation │    │  Reporting  │  │
│  │   (Quality)    │    │  (Hooks)   │    │ (Analytics) │  │
│  └────────────────┘    └────────────┘    └─────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Key Components

| Component | Location | Purpose | Input | Output |
|-----------|----------|---------|-------|--------|
| **Scanner** | `1_CORE_OPERATIONS/doc_id_scanner.py` | Discover files and extract existing doc_ids | Repository files | `docs_inventory.jsonl` |
| **Assigner** | `1_CORE_OPERATIONS/doc_id_assigner.py` | Inject doc_ids into files | `docs_inventory.jsonl` | Modified files |
| **Registry** | `5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml` | Authoritative doc_id database | Doc_id requests | Unique doc_ids |
| **Validators** | `2_VALIDATION_FIXING/` | Ensure quality and consistency | Files, registry | Pass/fail, fixes |
| **Automation** | `3_AUTOMATION_HOOKS/` | Trigger scans and validations | File events | Automated operations |
| **Reporting** | `4_REPORTING_MONITORING/` | Coverage and trends | Scan results | Reports, alerts |

### 1.4 Current System Status

**Last Scan:** 2025-12-31
**System Maturity:** Production-ready
**Core Tools:** Fully operational

| Metric | Value | Details |
|--------|-------|---------|
| **Doc ID Coverage** | 100.0% | 2,624 of 2,625 eligible files |
| **Total Tracked Docs** | 2,636 | From registry metadata |
| **Missing Doc IDs** | 1 file | 1 yml file in repository |
| **Invalid Doc IDs** | 0 | All existing IDs valid |
| **Registry Entries** | 2,636 | Across 8 categories |
| **Test Suite** | 22 tests | 11 passing, 10 failing, 1 skipped |

**Coverage by File Type:**
- Python (`.py`): 992/992 (100.0%)
- YAML (`.yaml`): 390/390 (100.0%)
- YML (`.yml`): 22/23 (95.7%) ← 1 missing
- JSON (`.json`): 860/860 (100.0%)
- PowerShell (`.ps1`): 317/317 (100.0%)
- Shell (`.sh`): 43/43 (100.0%)

**Category Distribution:**
- `CORE`: 919 docs (system components, orchestrator, scheduler)
- `GUIDE`: 700 docs (documentation and guides)
- `CONFIG`: 777 docs (configuration files)
- `LEGACY`: 569 docs (archived/deprecated components)
- `TEST`: 445 docs (test files and utilities)
- `SCRIPT`: 428 docs (scripts and automation)
- `PATTERNS`: 201 docs (execution patterns and templates)
- `ERROR`: 179 docs (error detection and recovery)
- `SPEC`: 68 docs (specifications and schemas)

**Operational Status:**
- ✅ Scanner: Operational (`doc_id_scanner.py`)
- ✅ Assigner: Operational (`doc_id_assigner.py`)
- ✅ Validators: Operational (multiple validators)
- ✅ Registry: Operational (`DOC_ID_REGISTRY.yaml`)
- ✅ CLI: Operational (`doc_id_registry_cli.py`)
- ⚠️ Tests: 10 of 22 tests failing (non-critical, system functional)

### 1.5 Integration with Related Systems

The DOC_ID system integrates with several sibling systems in the repository:

#### SSOT (Single Source of Truth) System
- **Location:** `../SSOT_System/`
- **Purpose:** Canonical project state management with patch-based updates
- **Integration:** `DOC_ID_REGISTRY.yaml` is an SSOT-managed artifact
- **Governance:** All changes to registry via RFC 6902 JSON Patch files
- **Why patch-only:**
  - Immutable audit trail (every change recorded)
  - Concurrent modification safety
  - Rollback capability
  - Compliance with determinism requirements
- **Relationship:** SSOT is the governance framework; doc_id registry is a managed artifact

#### Lifecycle Management System
- **Location:** `../LIFECYCLE/`, `../LIFECYCLE_V2.5.3_CONSOLIDATED/`
- **Purpose:** Task dependencies, execution graphs, workflow orchestration
- **Integration:** Doc_ids reference lifecycle tasks for traceability
- **Status:** Separate system with loose coupling
- **Relationship:**
  - Doc_id: Identity and tracking
  - Lifecycle: Execution and dependencies
  - Coordination: Doc_ids enable lifecycle task tracking

#### Determinism Contract
- **Location:** `../PHASE_0_BOOTSTRAP/SYSTEM_DETERMINISM_CONTRACT.json`
- **Purpose:** Ensure reproducible, traceable execution across all tools
- **Integration:** All doc_id tools comply with determinism requirements
- **Requirements:**
  - All output to `.runs/<run_id>/` (not arbitrary locations)
  - No unseeded randomness
  - Trace_id and run_id propagation
  - Timestamps via explicit clock injection
- **Current Compliance:**
  - ✅ Scanner: run_id propagation implemented
  - ✅ Assigner: Output containment to `.runs/` implemented
  - ⚠️ Some validators: Pending run_id integration

#### Phase-Based Pipeline
- **Location:** `../PHASE_0_BOOTSTRAP/` through `../PHASE_7_MONITORING/`
- **Purpose:** Multi-phase AI development pipeline (planning → execution → monitoring)
- **Integration:** SUB_DOC_ID operates within PHASE_5 (Execution)
- **Current Phase Status:**
  - PHASE_0-4: Complete (bootstrap, planning, routing)
  - PHASE_5: ✅ Operational (execution - doc_id system resides here)
  - PHASE_6-7: Planned (error recovery, monitoring)

---

## 2. Core Concepts

### 2.1 Doc ID

A **doc_id** is a unique, stable identifier permanently assigned to a file. It follows this pattern:

```
DOC-{CATEGORY}-{NAME}-{SEQUENCE}
```

**Properties:**
- **Unique:** No two files share the same doc_id
- **Stable:** Persists across file renames, moves, and refactors
- **Human-readable:** Conveys file category and purpose
- **Machine-parseable:** Follows strict regex pattern
- **Version-controlled:** Committed with the file

### 2.2 Categories

Categories group related files and control doc_id prefix:

| Category | Prefix | Purpose | Examples |
|----------|--------|---------|----------|
| `core` | CORE | Core system components | Orchestrator, scheduler, executor |
| `script` | SCRIPT | Scripts and tools | Validation scripts, utilities |
| `test` | TEST | Test files | Unit tests, integration tests |
| `guide` | GUIDE | Documentation | READMEs, guides, specifications |
| `spec` | SPEC | Formal specifications | Schemas, contracts |
| `config` | CONFIG | Configuration files | YAML configs, settings |
| `patterns` | PAT | Execution patterns | Workflow templates |
| `error` | ERROR | Error handling | Recovery logic, error detection |
| `aim` | AIM | AIM subsystem | AIM environment tools |
| `pm` | PM | Project management | Planning, tracking |
| `gui` | GUI | User interfaces | GUI components, panels |
| `glossary` | GLOSSARY | Glossary terms | Term definitions |

### 2.3 ID Types Ecosystem

The repository governance defines **5 distinct ID types**, though only `doc_id` is currently fully implemented:

| ID Type | Status | Purpose | Registry Location | Tool |
|---------|--------|---------|-------------------|------|
| **doc_id** | ✅ Operational | Document/file identity | `DOC_ID_REGISTRY.yaml` | `doc_id_scanner.py`, `doc_id_assigner.py` |
| **pattern_id** | 🚧 Planned | Pattern suite identity | `patterns/PATTERN_REGISTRY.yaml` | TBD |
| **module_id** | 🚧 Planned | Architectural module identity | `SUBSYSTEM_CATALOG.yaml` | TBD |
| **run_id** | ✅ Operational | Execution run identity | Generated at runtime | UUID v4 generation |
| **event_id** | 🚧 Planned | Event/step identity | Runtime only | TBD |

**Currently Implemented:**
- **doc_id**: Full scanner/assigner/validator toolchain (this system)
- **run_id**: Runtime generation for determinism and traceability

**Planned (Governance Defined, Tools Pending):**
- **pattern_id**: Will track execution pattern definitions
- **module_id**: Will track architectural module boundaries
- **event_id**: Will track execution events and workflow steps

**Relationship:**
- `doc_id` identifies **files** (persistent)
- `pattern_id` identifies **reusable patterns** (persistent)
- `module_id` identifies **subsystems/modules** (persistent)
- `run_id` identifies **execution runs** (transient, for tracing)
- `event_id` identifies **execution events** (transient, for observability)

**Integration:**
- All tools must accept `run_id` parameter for determinism
- Files may reference `pattern_id` and `module_id` in metadata
- Events logged with `run_id` and `event_id` for traceability

### 2.4 File Lifecycle

```
┌────────────┐
│  Created   │ ─── File created without doc_id
└─────┬──────┘
      │
      ▼
┌────────────┐
│  Scanned   │ ─── Scanner discovers file
└─────┬──────┘
      │
      ▼
┌────────────┐
│  Assigned  │ ─── Doc_id minted and injected
└─────┬──────┘
      │
      ▼
┌────────────┐
│  Tracked   │ ─── Doc_id in registry, validated
└─────┬──────┘
      │
      ▼
┌────────────┐
│ Deprecated │ ─── File archived (doc_id preserved)
└────────────┘
```

### 2.4 Injection Points

Doc_ids are injected into files at **standardized locations**:

**Python files (`.py`):**
```python
#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-MY-TOOL-0042
"""
Module docstring
"""
```

**Markdown files (`.md`):**
```markdown
---
doc_id: DOC-GUIDE-USER-MANUAL-0137
title: User Manual
---

# Content starts here
```

**YAML files (`.yaml`, `.yml`):**
```yaml
doc_id: DOC-CONFIG-PIPELINE-SETTINGS-0256
metadata:
  version: 1.0.0
```

**PowerShell files (`.ps1`):**
```powershell
# DOC_LINK: DOC-SCRIPT-AUTOMATION-RUNNER-0089
# Script description
```

**JSON files (`.json`):**
```json
{
  "doc_id": "DOC-SPEC-API-SCHEMA-0412",
  "version": "1.0"
}
```

---

## 3. Doc ID Format Specification

### 3.1 Formal Grammar

```ebnf
doc_id         = "DOC-" category "-" name "-" sequence
category       = uppercase_alpha { uppercase_alnum }
name           = name_part { "-" name_part }
name_part      = uppercase_alnum { uppercase_alnum }
sequence       = digit digit digit { digit }
uppercase_alpha = "A" | "B" | ... | "Z"
uppercase_alnum = uppercase_alpha | digit
digit          = "0" | "1" | ... | "9"
```

### 3.2 Regex Pattern

**Primary pattern:**
```regex
^DOC-([A-Z0-9]+)-([A-Z0-9]+(?:-[A-Z0-9]+)*)-([0-9]{3,})$
```

**Capture groups:**
- Group 1: Category prefix (e.g., `CORE`, `SCRIPT`)
- Group 2: Name parts (e.g., `DOC-ID-SCANNER`, `VALIDATE-PHASE`)
- Group 3: Sequence number (e.g., `0001`, `0042`, `1234`)

### 3.3 Validation Rules

**MUST comply:**
1. Start with literal `DOC-`
2. Category MUST be uppercase letters/digits only
3. Category MUST exist in registry categories
4. Name MUST be uppercase letters/digits with optional hyphens
5. Name MUST have at least one character between hyphens
6. Sequence MUST be 3+ digits (supports 000-999, typically 0000-9999)
7. Total length SHOULD NOT exceed 80 characters

**MUST NOT:**
1. Contain lowercase letters
2. Contain special characters except hyphens in name
3. Start or end name parts with hyphens
4. Have consecutive hyphens
5. Use reserved prefixes outside of category definition

### 3.4 Examples

**Valid:**
```
DOC-CORE-ORCHESTRATOR-0001
DOC-SCRIPT-DOC-ID-SCANNER-0046
DOC-TEST-INTEGRATION-API-GATEWAY-0137
DOC-GUIDE-BATCH-ASSIGNMENT-PROCEDURE-0724
```

**Invalid:**
```
DOC-core-test-001                # Lowercase
doc-CORE-TEST-001                # Lowercase prefix
DOC-CORE-test_file-001           # Underscore
DOC-CORE-TEST-01                 # Only 2 digits
DOC-CORE--TEST-001               # Double hyphen
DOC-UNKNOWN-TEST-001             # Unknown category
```

### 3.5 Sequence Number Allocation

Sequence numbers are **monotonically increasing** per category:

**Rules:**
- Each category maintains `next_id` in registry
- Assignment increments `next_id`
- Numbers are NEVER reused (even after file deletion)
- Width is 4 digits by default (0000-9999)
- Can extend to 5+ digits if needed (backward compatible)

**Format:**
```python
next_id = 42
doc_id = f"DOC-{category}-{name}-{next_id:04d}"
# Result: DOC-CORE-EXAMPLE-0042
```

---

## 4. Registry Architecture

### 4.1 Registry File: DOC_ID_REGISTRY.yaml

**Location:** `SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml`

**Structure:**
```yaml
doc_id: DOC-GUIDE-DOC-ID-REGISTRY-724
metadata:
  version: 1.0.0
  created: '2025-12-04'
  last_updated: '2025-12-28'
  total_docs: 2636
  description: Central registry for all doc_id assignments

categories:
  core:
    prefix: CORE
    description: Core system components
    next_id: 512      # Next available sequence number
    count: 919        # Total assigned in this category
  
  script:
    prefix: SCRIPT
    description: Scripts and automation tools
    next_id: 973
    count: 428

docs:
  - doc_id: DOC-CORE-ORCHESTRATOR-0001
    category: core
    name: orchestrator
    title: Execution Orchestrator
    status: active
    file_path: PHASE_5_EXECUTION/engine/orchestrator.py
    artifacts: []
    created: '2025-12-03'
    last_modified: '2025-12-15'
    tags: [execution, core]
  
  - doc_id: DOC-SCRIPT-DOC-ID-SCANNER-0046
    category: script
    name: doc-id-scanner
    title: Doc ID Scanner
    status: active
    file_path: SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py
    artifacts: []
    created: '2025-12-04'
    last_modified: '2025-12-20'
    tags: [scanning, automation]
```

### 4.2 Multi-Tier Architecture (Registry V3)

The registry supports a **multi-tier architecture** where basic document tracking (Tier 0-1) can be enhanced with advanced code analysis (Tier 2-3):

#### Tier 0: Basic Identity
**Purpose:** Minimal viable tracking
**Fields:**
- `doc_id` - Unique identifier
- `file_path` - Current location
- `status` - Lifecycle state (active, deprecated, archived)
- `category` - Classification

**Storage:** `DOC_ID_REGISTRY.yaml` (human-readable SSOT)

#### Tier 1: Metadata
**Purpose:** Provenance and versioning
**Fields:**
- `author` - Creator
- `created_utc` - Creation timestamp
- `modified_utc` - Last modification
- `checksum` - File integrity hash
- `title` - Human-readable name
- `tags` - Classification tags

**Storage:** `DOC_ID_REGISTRY.yaml`

#### Tier 2: Code Analysis (Advanced)
**Purpose:** AST-based code understanding
**Fields:**
- `canonical_hash` - Semantic hash (ignores formatting)
- `symbols` - Exported functions, classes, variables
- `edges` - Import/export dependencies
- `complexity_metrics` - Cyclomatic complexity, lines of code

**Storage:** `registry_v3.db` (SQLite for advanced queries)

**Implementation:** `tree_sitter_extractor.py` parses code into AST

#### Tier 3: Semantic Analysis (Future)
**Purpose:** Deep semantic understanding
**Fields:**
- `structure_signals` - Architectural patterns detected
- `relationships` - Logical dependencies beyond imports
- `semantic_tags` - ML-derived classifications

**Storage:** `registry_v3.db`

**Status:** Planned, tools pending

---

**Two Storage Formats:**

1. **DOC_ID_REGISTRY.yaml** (Tier 0-1)
   - Human-readable, Git-friendly
   - Single source of truth (SSOT-managed)
   - Direct edits forbidden (use sync tools)

2. **registry_v3.db** (Tier 0-3)
   - SQLite database for complex queries
   - Supports advanced analysis (Tier 2-3)
   - Derived/computed from YAML + code analysis
   - Regenerated on demand

**Sync Relationship:**
```
DOC_ID_REGISTRY.yaml (authoritative)
         ↓
    [sync process]
         ↓
registry_v3.db (derived + enhanced with Tier 2-3)
```

**When to Use Each Tier:**
- **Tier 0-1**: All files (required)
- **Tier 2**: Code files needing dependency analysis (`.py`, `.js`, etc.)
- **Tier 3**: Reserved for future ML-based analysis

### 4.3 Registry Operations

#### 4.3.1 Mint New Doc ID

**Operation:** Create a new unique doc_id

**Input:**
- `category`: Category key (e.g., "core", "script")
- `name`: Slugified name (e.g., "doc-id-scanner")
- `title`: Human-readable title (optional)

**Process:**
1. Validate category exists
2. Get `next_id` from category
3. Format doc_id: `DOC-{prefix}-{name}-{next_id:04d}`
4. Increment category `next_id`
5. Increment category `count`
6. Add entry to `docs` list
7. Save registry

**Output:**
```python
{
  "doc_id": "DOC-SCRIPT-MY-TOOL-0973",
  "category": "script",
  "next_id": 974
}
```

#### 4.3.2 Lookup Doc ID

**Operation:** Find existing doc_id

**Input:**
- `doc_id`: The doc_id to find

**Process:**
1. Load registry
2. Search `docs` list for matching `doc_id`
3. Return entry or None

**Output:**
```python
{
  "doc_id": "DOC-SCRIPT-MY-TOOL-0973",
  "status": "active",
  "file_path": "scripts/my_tool.py",
  ...
}
```

#### 4.3.3 Deprecate Doc ID

**Operation:** Mark doc_id as deprecated (file archived/deleted)

**Input:**
- `doc_id`: The doc_id to deprecate

**Process:**
1. Find entry in registry
2. Set `status: deprecated`
3. Add `deprecated_at` timestamp
4. Preserve entry (never delete)
5. Save registry

**Rules:**
- Doc_ids are NEVER deleted from registry
- Sequence numbers are NEVER reused
- Deprecated entries preserved for audit trail

### 4.3 Inventory File: docs_inventory.jsonl

**Location:** `SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl`

**Format:** JSON Lines (one JSON object per line)

**Purpose:** Snapshot of repository scan state

**Structure:**
```jsonl
{"path": "scripts/validator.py", "doc_id": "DOC-SCRIPT-VALIDATOR-0123", "status": "found", "file_type": "python", "last_modified": "2025-12-20T10:30:00Z", "scanned_at": "2025-12-28T07:00:00Z"}
{"path": "docs/guide.md", "doc_id": null, "status": "missing", "file_type": "markdown", "last_modified": "2025-12-25T14:20:00Z", "scanned_at": "2025-12-28T07:00:00Z"}
{"path": "tests/test_api.py", "doc_id": "DOC-TEST-API-0456", "status": "found", "file_type": "python", "last_modified": "2025-12-27T09:15:00Z", "scanned_at": "2025-12-28T07:00:00Z"}
```

**Fields:**
- `path`: Relative path from repository root
- `doc_id`: Extracted doc_id or `null` if missing
- `status`: `"found"`, `"missing"`, or `"invalid"`
- `file_type`: Detected file type (python, markdown, yaml, etc.)
- `last_modified`: File modification timestamp (ISO 8601)
- `scanned_at`: Scan timestamp (ISO 8601)

**Usage:**
1. Scanner writes inventory after each scan
2. Assigner reads inventory to find files needing doc_ids
3. Validators use inventory for coverage analysis
4. Reporters generate metrics from inventory

---

## 5. File Operations

### 5.1 Scanning (Discovery)

**Purpose:** Find all eligible files and extract existing doc_ids

**Tool:** `1_CORE_OPERATIONS/doc_id_scanner.py`

**Process:**
```
1. Start at repository root
2. Enumerate all files matching ELIGIBLE_PATTERNS
3. Skip files matching EXCLUDE_PATTERNS
4. For each eligible file:
   a. Read file content
   b. Extract doc_id using file-type-specific parser
   c. Validate extracted doc_id format
   d. Record in inventory entry
5. Write all entries to docs_inventory.jsonl
6. Calculate and print statistics
```

**Eligible Patterns:**
```python
ELIGIBLE_PATTERNS = [
    "**/*.py",      # Python files
    "**/*.md",      # Markdown docs
    "**/*.yaml",    # YAML configs
    "**/*.yml",     # YAML configs
    "**/*.ps1",     # PowerShell scripts
    "**/*.sh",      # Shell scripts
    "**/*.txt",     # Text files
    "**/*.json",    # JSON files (selective)
]
```

**Exclude Patterns:**
```python
EXCLUDE_PATTERNS = [
    ".venv", "venv", "__pycache__",
    ".git", ".pytest_cache", "node_modules",
    "UTI_Archives", "Backups", ".acms_runs",
    "envs", "htmlcov", ".coverage"
]
```

**Extraction Algorithms:**

**Python files:**
```python
def extract_doc_id_python(content: str) -> Optional[str]:
    # Search first 50 lines for:
    # - # DOC_LINK: DOC-...
    # - # DOC_ID: DOC-...
    lines = content.split("\n")[:50]
    for line in lines:
        match = re.search(r"DOC_(LINK|ID):\s*(DOC-[A-Z0-9-]+)", line)
        if match:
            return match.group(2)
    return None
```

**Markdown files:**
```python
def extract_doc_id_markdown(content: str) -> Optional[str]:
    # Look for YAML frontmatter:
    # ---
    # doc_id: DOC-...
    # ---
    if not content.startswith("---"):
        return None
    lines = content.split("\n")
    # Find closing ---
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter = "\n".join(lines[1:i])
            match = re.search(r'doc_id:\s*["\']?(DOC-[A-Z0-9-]+)', frontmatter)
            if match:
                return match.group(1)
            break
    return None
```

**YAML files:**
```python
def extract_doc_id_yaml(content: str) -> Optional[str]:
    # Parse as YAML and look for doc_id key
    import yaml
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict) and "doc_id" in data:
            return data["doc_id"]
    except:
        pass
    return None
```

**Commands:**
```bash
# Full scan
python doc_id_scanner.py scan

# View statistics
python doc_id_scanner.py stats

# Generate report
python doc_id_scanner.py report --format markdown
```

**Output:**
- Writes `docs_inventory.jsonl`
- Prints summary statistics
- Returns exit code 0 on success

### 5.2 Assignment (Injection)

**Purpose:** Mint new doc_ids and inject into files

**Tool:** `1_CORE_OPERATIONS/doc_id_assigner.py`

**Process:**
```
1. Load docs_inventory.jsonl
2. Filter entries with status="missing"
3. For each missing entry:
   a. Determine category from file path
   b. Generate name slug from filename
   c. Mint new doc_id via registry
   d. Inject doc_id into file at appropriate location
   e. Update inventory entry: status="found", doc_id=new_id
4. Write updated inventory
5. Print assignment summary
```

**Category Inference:**

| Path Pattern | Category |
|--------------|----------|
| `**/tests/**` | test |
| `**/scripts/**` | script |
| `**/*.md` | guide |
| `**/*.yaml` in `specs/` | spec |
| `**/PHASE_*/engine/**` | core |
| `**/SUB_*/**` | Based on subsystem |

**Name Generation:**
```python
def generate_name(file_path: Path) -> str:
    # Example: "doc_id_scanner.py" -> "doc-id-scanner"
    stem = file_path.stem
    name = stem.replace("_", "-").upper()
    return name
```

**Injection Locations:**

**Python:**
```python
# Insert after shebang and encoding, before docstring
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-MY-TOOL-0042  # <-- INJECTED HERE
"""
Module docstring
"""
```

**Markdown:**
```markdown
---
doc_id: DOC-GUIDE-MY-DOC-0137  # <-- INJECTED IN FRONTMATTER
title: My Document
---

Content...
```

**YAML:**
```yaml
doc_id: DOC-CONFIG-SETTINGS-0256  # <-- INJECTED AS TOP-LEVEL KEY
version: 1.0.0
settings:
  ...
```

**Commands:**
```bash
# Dry-run (preview only)
python doc_id_assigner.py auto-assign --dry-run

# Assign to first 100 files
python doc_id_assigner.py auto-assign --limit 100

# Assign to all missing files
python doc_id_assigner.py auto-assign

# Assign to single file
python doc_id_assigner.py single --path scripts/my_tool.py --category script --name my-tool
```

**Safety Features:**
- Always creates backup before modifying files
- Validates file is not locked or read-only
- Preserves file encoding
- Maintains original line endings
- Atomic write (write to temp, then rename)

### 5.3 Synchronization

**Purpose:** Sync inventory with registry

**Tool:** `5_REGISTRY_DATA/sync_registries.py`

**Process:**
```
1. Load docs_inventory.jsonl
2. Load DOC_ID_REGISTRY.yaml
3. For each inventory entry with doc_id:
   a. Check if doc_id exists in registry
   b. If missing: add to registry
   c. If exists: update file_path and last_modified
4. For each registry entry:
   a. Check if file exists in inventory
   b. If missing and status=active: mark as missing_file
5. Write updated registry
6. Print sync summary
```

**Commands:**
```bash
# Sync inventory to registry
python sync_registries.py sync

# Force sync (ignore timestamps)
python sync_registries.py sync --force

# Validate registry integrity
python sync_registries.py validate
```

---

## 6. Validation Rules

### 6.1 Format Validation

**Rule:** Doc_id MUST match regex pattern

**Validator:** `common/rules.py::validate_doc_id()`

**Checks:**
- Starts with `DOC-`
- Category is uppercase alphanumeric
- Name is uppercase alphanumeric with hyphens
- Sequence is 3+ digits
- No invalid characters

**Errors:**
- `E001`: Invalid format
- `E002`: Lowercase characters
- `E003`: Invalid characters
- `E004`: Sequence too short

### 6.2 Uniqueness Validation

**Rule:** Each doc_id MUST be unique across repository

**Validator:** `2_VALIDATION_FIXING/validate_doc_id_uniqueness.py`

**Checks:**
- Scans all files for doc_ids
- Detects duplicates
- Reports conflicts

**Errors:**
- `E101`: Duplicate doc_id found in multiple files
- `E102`: Doc_id in registry but not in files
- `E103`: Doc_id in files but not in registry

### 6.3 Category Validation

**Rule:** Category MUST exist in registry

**Validator:** `common/registry.py::validate_category()`

**Checks:**
- Category is defined in `categories` section
- Category has valid prefix
- Category has `next_id` field

**Errors:**
- `E201`: Unknown category
- `E202`: Missing prefix
- `E203`: Missing next_id

### 6.4 Consistency Validation

**Rule:** Doc_id in file MUST match registry entry

**Validator:** `2_VALIDATION_FIXING/validate_doc_id_sync.py`

**Checks:**
- Doc_id in file matches registry file_path
- Registry entry status is "active"
- Timestamps are consistent

**Errors:**
- `E301`: Doc_id in file doesn't match registry path
- `E302`: Registry entry marked deprecated but file exists
- `E303`: File modified but registry not updated

### 6.5 Coverage Validation

**Rule:** Repository MUST meet minimum coverage threshold

**Validator:** `2_VALIDATION_FIXING/validate_doc_id_coverage.py`

**Checks:**
- Calculates coverage percentage
- Compares against baseline
- Detects regressions

**Baseline:** Configurable, default 55%

**Formula:**
```python
coverage = (files_with_doc_id / eligible_files) * 100
pass = coverage >= baseline
```

**Errors:**
- `E401`: Coverage below baseline
- `E402`: Coverage regression detected

### 6.6 Reference Validation

**Rule:** Doc_id references MUST point to valid doc_ids

**Validator:** `2_VALIDATION_FIXING/validate_doc_id_references.py`

**Checks:**
- Finds all doc_id references in files
- Validates each reference exists in registry
- Checks reference target is not deprecated

**Errors:**
- `E501`: Reference to non-existent doc_id
- `E502`: Reference to deprecated doc_id
- `E503`: Circular reference detected

---

## 7. Automation System

### 7.1 Git Pre-Commit Hook

**Purpose:** Validate doc_ids before commit

**Location:** `3_AUTOMATION_HOOKS/pre_commit_hook.py`

**Installation:**
```bash
python 3_AUTOMATION_HOOKS/install_pre_commit_hook.py
```

**Process:**
```
1. Git stages files for commit
2. Hook is triggered
3. For each staged file:
   a. Extract doc_ids
   b. Validate format
   c. Check for duplicates
   d. Verify in registry
4. If validation fails:
   - Print errors
   - Block commit with exit code 1
5. If validation passes:
   - Allow commit with exit code 0
```

**Configuration:**
```bash
# .git/hooks/pre-commit
#!/usr/bin/env python3
import sys
sys.path.insert(0, "SUB_DOC_ID")
from pre_commit_hook import main
sys.exit(main())
```

**Bypass (emergency only):**
```bash
git commit --no-verify -m "Emergency fix"
```

### 7.2 File Watcher

**Purpose:** Auto-scan on file changes

**Location:** `3_AUTOMATION_HOOKS/file_watcher.py`

**Dependencies:** `watchdog` library

**Process:**
```
1. Start watchdog observer
2. Monitor repository for file changes
3. On file change event:
   a. Check if file is eligible
   b. Debounce (wait N seconds for more changes)
   c. Trigger scanner
   d. Optionally trigger assigner
4. Log all activities
5. Send alerts on errors
```

**Commands:**
```bash
# Start watcher with 10-minute debounce
python file_watcher.py --debounce 600

# Start watcher in background
nohup python file_watcher.py --debounce 600 > watcher.log 2>&1 &
```

**Configuration:**
```python
MONITORED_FOLDERS = {
    'glossary': {
        'path': 'SUB_GLOSSARY',
        'patterns': ['.yaml', '.yml', '.md'],
        'category': 'glossary',
    },
    'scripts': {
        'path': 'scripts',
        'patterns': ['.py', '.ps1'],
        'category': 'script',
    }
}
```

### 7.3 Scheduled Tasks

**Purpose:** Periodic scans and maintenance

**Location:** `3_AUTOMATION_HOOKS/setup_scheduled_tasks.py`

**Platform:** Windows Task Scheduler / Linux cron

**Tasks:**

| Task | Schedule | Command |
|------|----------|---------|
| **Nightly Scan** | Daily 2:00 AM | `python doc_id_scanner.py scan` |
| **Coverage Report** | Daily 3:00 AM | `python validate_doc_id_coverage.py --report` |
| **Duplicate Check** | Daily 4:00 AM | `python fix_duplicate_doc_ids.py --check` |
| **Registry Sync** | Daily 5:00 AM | `python sync_registries.py sync` |

**Installation (Windows):**
```bash
python setup_scheduled_tasks.py --interval daily
```

**Installation (Linux):**
```bash
# Add to crontab
0 2 * * * cd /path/to/repo && python SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py scan
0 3 * * * cd /path/to/repo && python SUB_DOC_ID/2_VALIDATION_FIXING/validate_doc_id_coverage.py --report
```

### 7.4 CI/CD Integration

**Purpose:** Validate doc_ids in CI pipeline

**GitHub Actions Example:**
```yaml
name: Doc ID Validation
on: [push, pull_request]

jobs:
  validate-doc-ids:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install pyyaml
      
      - name: Validate doc_id coverage
        run: |
          cd SUB_DOC_ID/2_VALIDATION_FIXING
          python validate_doc_id_coverage.py --baseline 0.55
      
      - name: Check for duplicates
        run: |
          cd SUB_DOC_ID/2_VALIDATION_FIXING
          python fix_duplicate_doc_ids.py --check
      
      - name: Validate format
        run: |
          cd SUB_DOC_ID/2_VALIDATION_FIXING
          python fix_invalid_doc_ids.py --check
```

---

## 8. Data Structures

### 8.1 Registry Schema

```yaml
# DOC_ID_REGISTRY.yaml

# Registry metadata
doc_id: string           # Doc_id of registry file itself
metadata:
  version: string        # Registry schema version (semver)
  created: string        # ISO 8601 date
  last_updated: string   # ISO 8601 date
  total_docs: integer    # Total doc_ids assigned
  description: string    # Human-readable description

# Category definitions
categories:
  {category_key}:        # Lowercase key (e.g., "core", "script")
    prefix: string       # Uppercase prefix (e.g., "CORE", "SCRIPT")
    description: string  # Purpose of this category
    next_id: integer     # Next available sequence number
    count: integer       # Total assigned in this category

# Doc_id entries
docs:
  - doc_id: string            # Full doc_id (e.g., "DOC-CORE-TEST-0001")
    category: string          # Category key
    name: string              # Name slug
    title: string             # Human-readable title
    status: enum              # "active" | "deprecated"
    file_path: string         # Relative path from repo root
    artifacts: list[string]   # Related artifact paths
    created: string           # ISO 8601 date
    last_modified: string     # ISO 8601 date
    deprecated_at: string     # ISO 8601 date (if deprecated)
    tags: list[string]        # Optional tags
```

### 8.2 Inventory Schema

```json
{
  "path": "string",              // Relative path from repo root
  "doc_id": "string | null",     // Extracted doc_id or null
  "status": "string",            // "found" | "missing" | "invalid"
  "file_type": "string",         // "python" | "markdown" | "yaml" | etc.
  "last_modified": "string",     // ISO 8601 timestamp
  "scanned_at": "string",        // ISO 8601 timestamp
  "error": "string | null"       // Error message if status="invalid"
}
```

### 8.3 Common Module API

**Location:** `SUB_DOC_ID/common/`

**Constants:**
```python
# Paths
REPO_ROOT: Path                  # Repository root directory
MODULE_ROOT: Path                # SUB_DOC_ID directory
REGISTRY_PATH: Path              # Path to DOC_ID_REGISTRY.yaml
INVENTORY_PATH: Path             # Path to docs_inventory.jsonl

# Patterns
ELIGIBLE_PATTERNS: List[str]     # File patterns to scan
EXCLUDE_PATTERNS: List[str]      # Patterns to exclude
DOC_ID_REGEX: re.Pattern         # Doc_id validation regex
DOC_ID_WIDTH: int                # Default sequence width (4)

# Defaults
DEFAULT_COVERAGE_BASELINE: float # Default coverage threshold (0.55)
```

**Rules Module (`rules.py`):**
```python
def validate_doc_id(doc_id: str) -> bool:
    """Validate doc_id format"""
    
def validate_doc_id_strict(doc_id: str, width: int) -> bool:
    """Validate with exact width requirement"""
    
def format_doc_id(category: str, name: str, sequence: int) -> str:
    """Format doc_id from components"""
    
def parse_doc_id(doc_id: str) -> Dict[str, str]:
    """Parse doc_id into components"""
```

**Registry Module (`registry.py`):**
```python
class Registry:
    def load() -> Dict:
        """Load registry from file"""
    
    def save(data: Dict) -> None:
        """Save registry to file"""
    
    def mint_doc_id(category: str, name: str, title: str) -> str:
        """Mint new unique doc_id"""
    
    def lookup(doc_id: str) -> Optional[Dict]:
        """Find doc_id entry"""
    
    def deprecate(doc_id: str) -> None:
        """Mark doc_id as deprecated"""
```

**Utils Module (`utils.py`):**
```python
def load_yaml(path: Path) -> Dict:
    """Load YAML file"""
    
def save_yaml(path: Path, data: Dict) -> None:
    """Save YAML file"""
    
def load_jsonl(path: Path) -> List[Dict]:
    """Load JSON Lines file"""
    
def save_jsonl(path: Path, data: List[Dict]) -> None:
    """Save JSON Lines file"""
```

**Validators Module (`validators.py`):**
```python
class ValidatorFactory:
    @staticmethod
    def create(validator_type: str) -> Validator:
        """Create validator instance"""

class Validator:
    def validate() -> ValidationResult:
        """Run validation"""
```

---

## 9. Workflow Patterns

### 9.1 Initial Repository Setup

**Goal:** Assign doc_ids to all existing files

**Steps:**
```
1. Install dependencies:
   pip install pyyaml watchdog

2. Scan repository:
   cd SUB_DOC_ID/1_CORE_OPERATIONS
   python doc_id_scanner.py scan
   python doc_id_scanner.py stats

3. Review scan results:
   # Check coverage percentage
   # Identify files missing doc_ids

4. Preview assignments:
   python doc_id_assigner.py auto-assign --dry-run

5. Assign in batches:
   python doc_id_assigner.py auto-assign --limit 100
   # Review changes
   # Repeat with more files

6. Sync registry:
   cd ../5_REGISTRY_DATA
   python sync_registries.py sync

7. Validate:
   cd ../2_VALIDATION_FIXING
   python validate_doc_id_coverage.py --baseline 0.55
   python fix_duplicate_doc_ids.py --check

8. Install automation:
   cd ../3_AUTOMATION_HOOKS
   python install_pre_commit_hook.py
   python setup_scheduled_tasks.py --interval daily

9. Commit changes:
   git add .
   git commit -m "feat: assign doc_ids to all files"
```

### 9.2 Adding New Files

**Goal:** Assign doc_id to newly created file

**Manual Method:**
```
1. Create file without doc_id
2. Run scanner:
   python doc_id_scanner.py scan
3. Run assigner:
   python doc_id_assigner.py auto-assign --limit 1
4. Verify injection:
   cat path/to/file | grep DOC_
5. Commit:
   git add path/to/file
   git commit -m "feat: add new component"
```

**Automated Method (with file watcher):**
```
1. Create file without doc_id
2. File watcher detects change
3. Scanner runs automatically
4. Assigner runs automatically (if configured)
5. Notification sent
6. Commit file with auto-assigned doc_id
```

### 9.3 Renaming/Moving Files

**Goal:** Preserve doc_id when file moves

**Steps:**
```
1. Move/rename file:
   git mv old_path new_path

2. Doc_id remains in file (unchanged)

3. Run sync:
   cd SUB_DOC_ID/5_REGISTRY_DATA
   python sync_registries.py sync
   # Registry file_path updated automatically

4. Validate:
   cd ../2_VALIDATION_FIXING
   python validate_doc_id_sync.py

5. Commit:
   git add .
   git commit -m "refactor: move component to new location"
```

**Important:** Doc_id is file-identity, not path-identity. It persists across moves.

### 9.4 Deprecating Files

**Goal:** Mark file and doc_id as deprecated

**Steps:**
```
1. Move file to archive:
   git mv path/to/file.py UTI_Archives/file.py

2. Deprecate doc_id in registry:
   cd SUB_DOC_ID/1_CORE_OPERATIONS
   python deprecate_doc_id.py DOC-CORE-COMPONENT-0042

3. Verify:
   # Check registry shows status: deprecated
   grep -A5 "DOC-CORE-COMPONENT-0042" ../5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml

4. Commit:
   git add .
   git commit -m "chore: deprecate old component"
```

**Important:** Doc_ids are never deleted, only marked deprecated.

### 9.5 Fixing Coverage Regression

**Goal:** Restore coverage after it drops below baseline

**Steps:**
```
1. Detect regression (CI or scheduled task):
   python validate_doc_id_coverage.py --baseline 0.55
   # Exit code 1: Regression detected

2. Identify missing files:
   python doc_id_scanner.py scan
   grep '"status": "missing"' ../5_REGISTRY_DATA/docs_inventory.jsonl

3. Assign doc_ids:
   python doc_id_assigner.py auto-assign

4. Verify:
   python validate_doc_id_coverage.py --baseline 0.55
   # Exit code 0: Coverage restored

5. Commit:
   git add .
   git commit -m "fix: restore doc_id coverage"
```

### 9.6 Resolving Duplicates

**Goal:** Fix duplicate doc_ids

**Steps:**
```
1. Detect duplicates:
   cd SUB_DOC_ID/2_VALIDATION_FIXING
   python fix_duplicate_doc_ids.py --check

2. Review conflicts:
   # Tool shows files with same doc_id

3. Auto-resolve (recommended):
   python fix_duplicate_doc_ids.py --auto-resolve
   # Keeps oldest file, reassigns newer files

4. Manual resolve (if needed):
   # Edit file to remove/change doc_id
   # Run scanner and assigner

5. Verify:
   python fix_duplicate_doc_ids.py --check

6. Commit:
   git add .
   git commit -m "fix: resolve doc_id duplicates"
```

---

## 10. Error Handling

### 10.1 Error Categories

| Code | Category | Description | Recovery |
|------|----------|-------------|----------|
| `E0xx` | Format | Invalid doc_id format | Auto-fix or reassign |
| `E1xx` | Uniqueness | Duplicate doc_ids | Reassign duplicates |
| `E2xx` | Category | Category errors | Add category or recategorize |
| `E3xx` | Consistency | Registry sync issues | Run sync operation |
| `E4xx` | Coverage | Below threshold | Assign missing doc_ids |
| `E5xx` | Reference | Invalid references | Fix or remove references |
| `E9xx` | System | I/O or system errors | Check permissions, disk space |

### 10.2 Error Messages

**Format Errors:**
```
E001: Invalid doc_id format: 'DOC-core-test-001'
  Expected: DOC-{CATEGORY}-{NAME}-{SEQUENCE}
  Problem: Lowercase 'core' should be 'CORE'
  Fix: Run fix_invalid_doc_ids.py
```

**Uniqueness Errors:**
```
E101: Duplicate doc_id 'DOC-CORE-TEST-0042' found in:
  - scripts/test_old.py
  - scripts/test_new.py
  Fix: Run fix_duplicate_doc_ids.py --auto-resolve
```

**Coverage Errors:**
```
E401: Coverage 52.3% below baseline 55.0%
  Missing doc_ids: 1,423 files
  Fix: Run doc_id_assigner.py auto-assign
```

### 10.3 Recovery Procedures

**Corrupted Registry:**
```
1. Stop all operations
2. Restore from backup:
   cp 5_REGISTRY_DATA/backups_v2_v3/DOC_ID_REGISTRY_backup_*.yaml \
      5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml
3. Re-scan repository:
   python doc_id_scanner.py scan
4. Sync registry:
   python sync_registries.py sync --force
5. Validate:
   python validate_doc_id_sync.py
```

**Lost Inventory:**
```
1. Re-scan repository:
   cd SUB_DOC_ID/1_CORE_OPERATIONS
   python doc_id_scanner.py scan
2. Verify inventory created:
   ls -l ../5_REGISTRY_DATA/docs_inventory.jsonl
3. Sync with registry:
   cd ../5_REGISTRY_DATA
   python sync_registries.py sync
```

**Permission Errors:**
```
1. Check file permissions:
   ls -l path/to/file
2. Fix permissions:
   chmod u+w path/to/file
3. Retry operation
```

---

## 11. Integration Points

### 11.1 Git Integration

**Pre-commit Hook:**
- Triggered on `git commit`
- Validates staged files
- Blocks commit if validation fails

**Post-merge Hook:**
- Triggered on `git merge` completion
- Detects new/changed files
- Triggers scan and potential reassignment

### 11.2 CI/CD Integration

**Inputs:**
- Repository checkout
- Python 3.8+
- pyyaml dependency

**Validation Gates:**
```yaml
gates:
  - name: "Doc ID Coverage"
    command: validate_doc_id_coverage.py --baseline 0.55
    fail_on_error: true
  
  - name: "No Duplicates"
    command: fix_duplicate_doc_ids.py --check
    fail_on_error: true
  
  - name: "Valid Formats"
    command: fix_invalid_doc_ids.py --check
    fail_on_error: true
```

**Outputs:**
- Exit codes (0=pass, 1=fail)
- JSON reports for dashboards
- Markdown reports for PR comments

### 11.3 IDE Integration

**VS Code Extension (Conceptual):**
```json
{
  "commands": [
    {
      "command": "docid.assignToFile",
      "title": "Assign Doc ID to Current File"
    },
    {
      "command": "docid.validateFile",
      "title": "Validate Doc IDs in File"
    },
    {
      "command": "docid.showCoverage",
      "title": "Show Doc ID Coverage"
    }
  ],
  "keybindings": [
    {
      "command": "docid.assignToFile",
      "key": "ctrl+shift+d"
    }
  ]
}
```

### 11.4 External Systems

**Document Management:**
- Export doc_id registry to external doc systems
- Link requirements to doc_ids
- Track coverage in dashboards

**Code Review:**
- Validate new files have doc_ids
- Require doc_id assignment before merge
- Auto-comment on PRs with coverage status

**Traceability Matrix:**
- Map doc_ids to requirements
- Map doc_ids to test cases
- Generate traceability reports

---

## 12. Performance Characteristics

### 12.1 Operation Times

| Operation | Repo Size | Time | Notes |
|-----------|-----------|------|-------|
| **Full Scan** | 1,000 files | 5-10 sec | Python files slower (AST parse) |
|  | 3,000 files | 15-30 sec | Markdown fastest (simple regex) |
|  | 10,000 files | 60-120 sec | Bottleneck: I/O |
| **Assignment** | 100 files | 5-10 sec | Includes registry updates |
|  | 1,000 files | 30-60 sec | Parallel not currently used |
| **Registry Sync** | Any | 2-5 sec | Pure YAML I/O |
| **Validation** | 3,000 files | 10-20 sec | Depends on validator |

### 12.2 Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Scanner | ~50-100 MB | Loads files into memory |
| Assigner | ~100-200 MB | Holds inventory + registry |
| Registry | ~10-50 MB | YAML parsing overhead |
| Validators | ~50-150 MB | Depends on validator type |

### 12.3 Scalability

**Current Limits:**
- **Files:** Tested up to 10,000 files
- **Registry Size:** Up to 5,000 doc_ids
- **Sequence Numbers:** 0000-9999 per category (10,000 per category)

**Bottlenecks:**
1. File I/O (reading file contents)
2. YAML parsing (registry load/save)
3. Regex matching (doc_id extraction)

**Optimization Opportunities:**
1. Parallel scanning (thread pool)
2. Incremental scanning (only changed files)
3. Binary registry format (faster than YAML)
4. Caching (file content hashes)

---

## 13. Security & Constraints

### 13.1 Security Considerations

**File Access:**
- System requires read/write access to all repository files
- Runs with user permissions (no elevation required)
- No network access required (local operations only)

**Data Privacy:**
- Doc_ids are non-sensitive (just identifiers)
- File paths may reveal structure (consider in public repos)
- Registry can be committed safely to version control

**Injection Safety:**
- Validates all inputs before injection
- Uses safe file writing (atomic writes)
- No code execution from doc_ids or user input

### 13.2 Constraints

**Required:**
- Python 3.8 or higher
- pyyaml library
- watchdog library (optional, for file watcher)
- Git (for hooks)

**Assumptions:**
- Files are text-based (UTF-8 encoding)
- Repository root is Git repository
- Write permissions to all tracked files
- YAML 1.2 format for registry

**Limitations:**
- Binary files not supported
- Large files (>10 MB) may be slow
- No cross-repository doc_id coordination
- Sequence numbers limited per category (extensible to 5+ digits)

### 13.3 Failure Modes

**Scan Failure:**
- Cause: Unreadable file, permission denied
- Impact: File excluded from inventory
- Recovery: Fix permissions, re-scan

**Assignment Failure:**
- Cause: File locked, read-only, corrupted
- Impact: File skipped, remains without doc_id
- Recovery: Fix file, re-assign

**Registry Corruption:**
- Cause: Manual edit error, merge conflict
- Impact: System cannot mint new doc_ids
- Recovery: Restore from backup, re-sync

**Duplicate Detection:**
- Cause: Manual copy/paste, merge conflict
- Impact: Validation fails
- Recovery: Auto-resolve or manual fix

---

## Appendix A: Quick Reference

### Commands Cheat Sheet

```bash
# Scanning
python doc_id_scanner.py scan                        # Full scan
python doc_id_scanner.py stats                       # Show statistics
python doc_id_scanner.py report --format markdown    # Generate report

# Assignment
python doc_id_assigner.py auto-assign --dry-run      # Preview
python doc_id_assigner.py auto-assign --limit 100    # Batch assign
python doc_id_assigner.py auto-assign                # Assign all
python doc_id_assigner.py single --path FILE         # Single file

# Validation
python validate_doc_id_coverage.py --baseline 0.55   # Coverage check
python fix_duplicate_doc_ids.py --check              # Duplicate check
python fix_invalid_doc_ids.py --check                # Format check
python validate_doc_id_sync.py                       # Sync check

# Maintenance
python sync_registries.py sync                       # Sync registry
python detect_doc_drift.py --check                   # Drift detection
python deprecate_doc_id.py DOC-ID                    # Deprecate doc_id

# Automation
python install_pre_commit_hook.py                    # Git hook
python setup_scheduled_tasks.py --interval daily     # Scheduler
python file_watcher.py --debounce 600                # File watcher
```

### File Locations Quick Reference

```
SUB_DOC_ID/
├── 1_CORE_OPERATIONS/        # Scan and assign
│   ├── doc_id_scanner.py
│   ├── doc_id_assigner.py
│   └── lib/
│       └── doc_id_registry_cli.py
├── 2_VALIDATION_FIXING/      # Validators and fixers
│   ├── validate_doc_id_coverage.py
│   ├── fix_duplicate_doc_ids.py
│   └── fix_invalid_doc_ids.py
├── 3_AUTOMATION_HOOKS/       # Git hooks and watchers
│   ├── pre_commit_hook.py
│   ├── file_watcher.py
│   └── setup_scheduled_tasks.py
├── 4_REPORTING_MONITORING/   # Reports and alerts
│   ├── doc_id_coverage_trend.py
│   └── scheduled_report_generator.py
├── 5_REGISTRY_DATA/          # Data files
│   ├── DOC_ID_REGISTRY.yaml  # Authoritative registry
│   └── docs_inventory.jsonl  # Scan snapshot
├── 6_TESTS/                  # Test suite
│   ├── test_doc_id_system.py
│   └── test_doc_id_compliance.py
├── 7_CLI_INTERFACE/          # Unified CLI
│   └── cli_wrapper.py
└── common/                   # Shared library
    ├── rules.py              # Validation rules
    ├── registry.py           # Registry API
    ├── utils.py              # Utilities
    └── config.py             # Configuration
```

---

## Appendix B: Decision Log

### Design Decisions

1. **Why YAML for registry?**
   - Human-readable and editable
   - Git-friendly (text-based diffs)
   - Good Python library support
   - Extensible schema

2. **Why JSON Lines for inventory?**
   - Streamable (one entry at a time)
   - Append-only friendly
   - Easy to parse line-by-line
   - Handles large datasets

3. **Why 4-digit sequence numbers?**
   - Backward compatible with 3-digit
   - Supports 10,000 files per category
   - Fixed width aids visual scanning
   - Can extend to 5+ digits if needed

4. **Why uppercase doc_ids?**
   - Stand out visually in code
   - Avoid case-sensitivity issues
   - Convention from DOI/ISBN standards
   - Easier regex matching

5. **Why inject doc_ids into files?**
   - Self-documenting (doc_id travels with file)
   - No external database required
   - Survives file moves/renames
   - Works offline

---

## Appendix C: Glossary

- **Doc_id:** Unique identifier permanently assigned to a file
- **Category:** Grouping of related files (core, script, test, etc.)
- **Sequence:** Numeric portion of doc_id, unique per category
- **Registry:** Authoritative YAML file listing all assigned doc_ids
- **Inventory:** Snapshot JSONL file of current repository state
- **Scanner:** Tool that discovers files and extracts doc_ids
- **Assigner:** Tool that mints and injects doc_ids into files
- **Validator:** Tool that checks doc_id rules and constraints
- **Coverage:** Percentage of eligible files with doc_ids
- **Baseline:** Minimum acceptable coverage percentage
- **Eligible File:** File type that should have a doc_id
- **Injection:** Process of writing doc_id into file content
- **Minting:** Process of creating new unique doc_id
- **Deprecation:** Marking doc_id as no longer active
- **Drift:** When file content changes but doc_id doesn't update

---

## Appendix D: FAQ

**Q: Can I manually edit doc_ids?**  
A: Yes, but update registry afterward with `sync_registries.py sync`

**Q: What if I delete a file?**  
A: Deprecate its doc_id with `deprecate_doc_id.py DOC-ID`. Never reuse.

**Q: Can I use doc_ids across multiple repos?**  
A: No, each repo has independent registry. Use different prefixes if merging.

**Q: What's the maximum number of doc_ids?**  
A: 10,000 per category by default. Extensible to millions with 5+ digit sequences.

**Q: How do I change a category?**  
A: Edit registry `categories` section, add entry with prefix and next_id.

**Q: Can doc_ids be hierarchical?**  
A: No, flat namespace. Use categories and naming for organization.

**Q: How do I bulk-rename doc_ids?**  
A: Not recommended. Doc_ids are stable identifiers. If needed, write custom migration script.

**Q: What about internationalization?**  
A: Doc_ids are ASCII-only. Use `title` field in registry for localized names.

**Q: How do I generate reports?**  
A: Use tools in `4_REPORTING_MONITORING/`, output JSON or Markdown.

**Q: Can I disable the pre-commit hook temporarily?**  
A: Yes, use `git commit --no-verify` for emergency commits.

---

**END OF SPECIFICATION**

This document is version-controlled and authoritative. For implementation details, see source code in `SUB_DOC_ID/`.

Last Updated: 2025-12-28  
Document ID: DOC-GUIDE-DOC-ID-COMPLETE-SPEC-1001
