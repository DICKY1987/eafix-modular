---
title: 16-Digit ID Structure - Complete Breakdown
date: 2026-01-21
audience: System Understanding
---

# 16-Digit ID Structure - What Each Part Means

## Example Filename

```
0199900095260118_README.md
^^^^^^^^^^^^^^^^ ^^^^^^^^^
16-digit ID      filename
```

## Breaking Down the 16 Digits

```
01 999 00095 260118
│  │   │     └────────── SCOPE (6 digits)
│  │   └──────────────── SEQ (5 digits)
│  └──────────────────── NS (3 digits)
└─────────────────────── TYPE (2 digits)

Position:  1-2  3-5  6-10   11-16
Segment:   TYPE NS   SEQ    SCOPE
```

## Detailed Explanation of Each Segment

### 1️⃣ TYPE (Positions 1-2) - File Type Code

**What it means:** What kind of file this is (2 digits)

**Example from above:** `01` = Markdown file

| Code | File Type | Extensions | Example |
|------|-----------|------------|---------|
| **01** | Markdown | .md | `01`999000952601118_README.md |
| **02** | Text | .txt | `02`999000012601118_notes.txt |
| **10** | CSV Data | .csv | `10`110000012601118_data.csv |
| **11** | JSON | .json | `11`110000022601118_config.json |
| **12** | YAML | .yaml, .yml | `12`999000792601118_config.yaml |
| **20** | Python | .py | `20`999000012601119_script.py |
| **21** | PowerShell | .ps1 | `21`201000012601118_deploy.ps1 |
| **30** | Database | .db | `30`300000012601118_app.db |
| **00** | Unknown/Other | * | `00`999000012601118_file |

**Why it exists:** So you can instantly tell what type of file it is just from the ID.

---

### 2️⃣ NS (Positions 3-5) - Namespace Code

**What it means:** Which folder/category this file belongs to (3 digits)

**Example from above:** `999` = Uncategorized (fallback)

| Code | Namespace | Folder Pattern | Example |
|------|-----------|----------------|---------|
| **100** | Documentation | docs/**/* | 01`100`000012601118_guide.md |
| **110** | Data Files | data/**/* | 10`110`000012601118_export.csv |
| **200** | Python Scripts | scripts/python/**/* | 20`200`000012601118_main.py |
| **201** | PowerShell Scripts | scripts/powershell/**/* | 21`201`000012601118_deploy.ps1 |
| **300** | Storage | storage/**/* | 30`300`000012601118_cache.db |
| **400** | Assets | assets/**/* | 41`400`000012601118_logo.png |
| **410** | Logs | logs/**/* | 42`410`000012601118_app.log |
| **420** | Reports | reports/**/* | 43`420`000012601118_summary.html |
| **999** | Uncategorized | **/* (any) | 01`999`000952601118_README.md |

**Why it exists:** Groups files by their purpose/location in the project.

---

### 3️⃣ SEQ (Positions 6-10) - Sequence Number

**What it means:** Which number file this is in its category (5 digits)

**Example from above:** `00095` = This is the 95th file of this type+namespace combination

| SEQ | Meaning | Example |
|-----|---------|---------|
| **00001** | First file | 0199900`00001`260118_first.md |
| **00002** | Second file | 0199900`00002`260118_second.md |
| **00095** | 95th file | 0199900`00095`260118_README.md |
| **00495** | 495th file | 2099900`00495`260118_script.py |
| **99999** | Max possible | 0199900`99999`260118_last.md |

**Why it exists:** 
- Ensures every file gets a unique number
- Prevents ID collisions
- Counter goes up by 1 each time a new file is created
- Each TYPE+NS+SCOPE combination has its own counter

**Important:** The counter is **per combination** of TYPE+NS+SCOPE. So:
- Markdown files (01) in docs (100) have their own counter: 01-100-00001, 01-100-00002...
- Python files (20) in scripts (200) have their own counter: 20-200-00001, 20-200-00002...

---

### 4️⃣ SCOPE (Positions 11-16) - Project Identifier

**What it means:** Which project/system this file belongs to (6 digits)

**Example from above:** `260118` = This project, started January 18, 2026

| SCOPE | Meaning | Used By |
|-------|---------|---------|
| **260118** | EAFIX Project (Jan 18, 2026) | 15 files |
| **260119** | EAFIX Project (Jan 19, 2026) | 5 files |
| **720066** | Unknown project code | 0 files (in config) |

**Why it exists:**
- Prevents conflicts if you copy files between projects
- Acts like a "project stamp"
- Should never change once set
- Usually based on project start date

---

## Complete Examples

### Example 1: README file
```
0199900095260118_README.md
│││││  │││└─────── SCOPE: 260118 (project Jan 18, 2026)
│││││  ││└──────── SEQ: 00095 (95th file of this type)
││││└──┴┴───────── 
│││└────────────── NS: 999 (uncategorized folder)
││└─────────────── 
│└──────────────── TYPE: 01 (markdown file)

Translation: "This is the 95th markdown file in uncategorized 
folders for the EAFIX project that started Jan 18, 2026"
```

### Example 2: Python script
```
2099900001260119_apply_ids_to_filenames.py
│││││  │││└─────── SCOPE: 260119 (project Jan 19, 2026)
│││││  ││└──────── SEQ: 00001 (first file of this type)
││││└──┴┴───────── 
│││└────────────── NS: 999 (uncategorized folder)
││└─────────────── 
│└──────────────── TYPE: 20 (python file)

Translation: "This is the 1st python file in uncategorized 
folders for the EAFIX project"
```

### Example 3: Config file
```
1299900079260118_IDENTITY_CONFIG.yaml
│││││  │││└─────── SCOPE: 260118 (project Jan 18, 2026)
│││││  ││└──────── SEQ: 00079 (79th file of this type)
││││└──┴┴───────── 
│││└────────────── NS: 999 (uncategorized folder)
││└─────────────── 
│└──────────────── TYPE: 12 (yaml file)

Translation: "This is the 79th YAML file in uncategorized 
folders for the EAFIX project"
```

---

## Visual Summary

```
┌─────────────── 16-DIGIT FILE ID ───────────────┐
│                                                 │
│  ┌──┐ ┌───┐ ┌──────┐ ┌─────────┐              │
│  │01│ │999│ │00095 │ │ 260118  │              │
│  └──┘ └───┘ └──────┘ └─────────┘              │
│   │     │      │          │                    │
│   │     │      │          └──► Project ID      │
│   │     │      └─────────────► Sequence #      │
│   │     └────────────────────► Folder Type     │
│   └──────────────────────────► File Type       │
│                                                 │
└─────────────────────────────────────────────────┘

RESULT: 0199900095260118_README.md
        └──────┬──────┘ └───┬──┘
         Unique ID      Original name
```

---

## Why This System?

### Problem it solves:
Without IDs, files named `README.md` or `config.yaml` conflict when you copy between folders.

### How IDs help:
- **Uniqueness**: Every file gets a different number
- **Traceability**: You can find files even if renamed
- **Organization**: Groups files by type and purpose
- **Project isolation**: SCOPE prevents conflicts between projects

---

## The Current Problem (Why You Need to Decide)

Looking at your files:

```
15 files use SCOPE: 260118  ← Original
 5 files use SCOPE: 260119  ← Migration attempt?
 0 files use SCOPE: 720066  ← What config says now

Example files:
0199900095260118_README.md        ← Uses 260118
0199900006260119_CLAUDE.md        ← Uses 260119
Config says: scope: "720066"      ← Not used anywhere!
```

**The question:** Should all files use:
- **260118** (what most files use)
- **260119** (what some files use)
- **720066** (what config says but nobody uses)

---

## My Recommendation

**Use SCOPE = 260118** because:
1. Most files (15 of 20) already use it
2. Clear meaning: Project started January 18, 2026
3. Less work to standardize everything

**Do you agree with using 260118?**

If yes, I'll:
- Update config from 720066 → 260118
- Document what 260118 means
- Plan to rename the 5 files using 260119
- Make all specs consistent

---

**Simple Question:** 
Do you want to use **260118** (Jan 18, 2026) as your permanent project SCOPE?
- [ ] Yes, use 260118
- [ ] No, use something else (tell me what)
