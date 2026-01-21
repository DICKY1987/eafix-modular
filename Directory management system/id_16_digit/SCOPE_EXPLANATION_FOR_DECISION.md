---
title: SCOPE Value - Simple Explanation for Decision Making
date: 2026-01-21
audience: Non-Technical Decision Maker
---

# What is SCOPE? Simple Explanation

## The Problem in Plain English

Your files have 16-digit ID numbers in their names, like this:

```
2099900001260119_apply_ids_to_filenames.py
^^^^^^^^^^^^^^^^
16-digit ID number
```

These 16 digits are divided into 4 parts:

```
20 999 00001 260119
│  │   │     └─────── SCOPE (6 digits) ← THIS IS THE PROBLEM
│  │   └──────────── SEQ (sequence number)
│  └──────────────── NS (namespace - which folder type)
└─────────────────── TYPE (file type - .py, .md, etc.)
```

## What is SCOPE?

**SCOPE is like a "project ID number"** - it's meant to ensure your files never conflict with files from other projects.

Think of it like:
- Your phone number has an area code (SCOPE) so it doesn't conflict with someone else's number
- Your license plate has a state code (SCOPE) so plates in different states can have same number

## The Current Problem

**Your system has THREE different SCOPE values in use:**

### Option 1: **260118**
- Used by: 15 older files
- Looks like: `0199900095260118_README.md`
- Meaning: Probably date **2026-01-18** (January 18, 2026)
- This appears to be when the project started

### Option 2: **260119**
- Used by: 5 newer files  
- Looks like: `0199900006260119_CLAUDE.md`
- Meaning: Probably date **2026-01-19** (January 19, 2026)
- This appears to be a day later (maybe a migration attempt)

### Option 3: **720066**
- Used by: 0 files currently
- Only exists in: Configuration file (IDENTITY_CONFIG.yaml)
- Meaning: **Unknown - you'll need to decide what this represents**
- This is what the config file says to use NOW

## The Question You Need to Answer

**"Which single number should ALL your files use as their SCOPE?"**

### Choice A: Use **260118** (go back to original)
- ✅ Matches 15 existing files (most files)
- ✅ Clear meaning: project start date Jan 18, 2026
- ❌ Need to update config file
- ❌ Need to rename 5 files that use 260119
- ❌ Ignores the 720066 someone put in config

### Choice B: Use **260119** (use the middle one)
- ✅ Matches 5 recent files
- ⚠️ Unclear why 260119 was chosen (one day after start?)
- ❌ Need to rename 15 older files
- ❌ Need to update config file from 720066

### Choice C: Use **720066** (use what's in config now) ✅ RECOMMENDED
- ✅ Fresh start - no files conflict yet
- ✅ Config file already set to this
- ✅ Can assign it a clear meaning (see suggestions below)
- ❌ Need to rename ALL 20 existing files (15+5)
- ⚠️ Someone configured this but we don't know why

## What Should 720066 Mean?

Since nobody knows what 720066 represents, **you can decide its meaning**:

### Suggestion 1: **Make it meaningful**
- `720066` could be a permanent project code
- Example: "Project 720066" or "EAFIX System ID: 720066"
- Advantage: Won't change over time (dates keep incrementing)

### Suggestion 2: **Convert to a date**
- Maybe it's supposed to be: 2026-07-20 (July 20, 2026)?
- Or: 2066-07-20 (far future placeholder)?
- Or: Something else entirely?

### Suggestion 3: **Revert to date-based**
- Change config back to: 260118 (Jan 18, 2026) or 260121 (today)
- Clear meaning: files created in this project on this date
- Consistent with what system was using before

## My Recommendation

**Use 260118** - Here's why:

1. ✅ It's what most files already use (15 out of 20)
2. ✅ Clear meaning: January 18, 2026 (project start)
3. ✅ Less work: only 5 files to rename instead of 20
4. ✅ If you ever copy files to another project, the date tells you where they came from

**Action needed:**
- Change config file from `scope: "720066"` to `scope: "260118"`
- Rename 5 files from 260119 → 260118
- Update documentation to explain SCOPE=260118 means "EAFIX project, created Jan 18, 2026"

---

# Question 2: Counter Format

This is simpler - it's just **how we write the counter key in the database**.

## Current Situation

When tracking which sequence number to use next, the system needs a "key" made from 3 parts:
- SCOPE (project)
- NS (folder type)
- TYPE (file type)

**Two different formats are in use:**

### Format A: `SCOPE:NS:TYPE` (in specification document)
```
Example: "260118:200:20"
Meaning: SCOPE=260118, NS=200, TYPE=20
```

### Format B: `NS_TYPE_SCOPE` (in actual code)
```
Example: "999_20_260118"
Meaning: NS=999, TYPE=20, SCOPE=260118
```

## Which One to Use?

**Use Format A: `SCOPE:NS:TYPE`** ✅ RECOMMENDED

Why:
1. ✅ Matches the order in the file ID: TYPE-NS-SEQ-SCOPE
2. ✅ Written in the official specification document
3. ✅ Standard format (colon separators, SCOPE first)
4. ✅ If you ever have multiple projects, it groups them correctly

**Action needed:**
- Change one line of code in `registry_store.py`
- Update the database keys from `999_20_260118` to `260118:999:20`

---

# Summary: My Recommendations

## Decision 1: SCOPE Value
**Use: 260118**
- Document it as: "EAFIX ID System - Project Start Date: January 18, 2026"
- Never change it (files keep this SCOPE forever)

## Decision 2: Counter Format  
**Use: `SCOPE:NS:TYPE`** (colon separator, SCOPE first)
- Matches specification
- Standard format
- Future-proof

## What Happens Next

Once you approve these decisions, I will:
1. Update config file: `scope: "260118"`
2. Update code: counter format to `SCOPE:NS:TYPE`
3. Document what 260118 means
4. Create migration plan for the 5 files using 260119
5. Update all documentation to be consistent

**Do you approve these recommendations?**
- [ ] Yes, use SCOPE=260118
- [ ] Yes, use Format=SCOPE:NS:TYPE
- [ ] No, I want to discuss alternatives

---

**Need help deciding?** Ask yourself:
- "What date did this project start?" → That's probably your SCOPE
- "Will I ever have multiple projects?" → If yes, use SCOPE-first format
