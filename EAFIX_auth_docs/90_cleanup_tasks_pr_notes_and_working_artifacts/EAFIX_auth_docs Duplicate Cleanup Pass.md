# EAFIX_auth_docs Duplicate Cleanup Pass  
## Objective  
Perform a duplicate-file cleanup pass within the EAFIX_auth_docs directory.  
The goal is to remove obsolete duplicate files while preserving the newest and most authoritative version of each document.  
Do NOT perform broad consolidation.  
Do NOT merge content.  
Do NOT rewrite documents.  
This task is limited to identifying duplicate files and deleting older copies when the duplication is confirmed.  
   
⸻  
   
## Safety Rules  
Before deleting any file:  
1. Verify duplication using file content comparison, not filename similarity.  
2. Prefer SHA256 comparison when available.  
3. If content differs in any meaningful way:    
    * DO NOT DELETE.  
    * Mark as a merge candidate.  
4. Produce a deletion report before making changes.  
5. Do not delete any file referenced as canonical by doc_authority.json.  
6. Do not delete any file unless the replacement file is present in the repository.  
7. Preserve git history through normal git deletion operations.  
   
⸻  
   
## Confirmed Duplicate Sets  
**Duplicate Set 1**  
Keep:  
```
eafix_project_knowledge_reference_routing_instructions.json

```
Delete:  
Any duplicate copy whose SHA256 matches exactly.  
Known finding:  
The file exists both:  
* at repository root  
* in EAFIX_auth_docs  
* in EAFIX_auth_docs  
Action:  
Determine which location should be canonical.  
Keep only one copy.  
Update references if necessary.  
   
⸻  
   
**Duplicate Set 2**  
Keep:  
```
module system as a versioned governance system.txt

```
Delete:  
```
Mod_refactor_plan.txt

```
Reason:  
SHA256 confirmed identical.  
No content loss.  
   
⸻  
   
**Duplicate Set 3**  
Keep:  
```
schema_version_ module_governance_glossary.txt

```
Delete:  
```
Schema_module_governance_glossary.txt

```
Reason:  
SHA256 confirmed identical.  
No content loss.  
   
⸻  
   
## Newer-Version Supersession Review  
These are NOT automatic deletions.  
Verify first.  
**Governance Glossary Family**  
Files:  
* module governance glossary.json  
* Y_module governance glossary.json  
Known finding:  
```
Y_module governance glossary.json

```
appears to be a newer revision.  
Tasks:  
1. Diff both files.  
2. Verify that Y contains all information from the base file.  
3. Verify no unique content exists only in the older file.  
4. If verified:  
Keep:  
```
Y_module governance glossary.json

```
Delete:  
```
module governance glossary.json

```
Otherwise:  
Mark for manual review.  
   
⸻  
   
**Bulk Terms Family**  
Files:  
* module governance glossary bulk terms.json  
* x_module governance glossary bulk terms.json  
Known finding:  
```
x_module governance glossary bulk terms.json

```
appears newer and contains additional governance decisions.  
Tasks:  
1. Diff files.  
2. Confirm all original terms exist in x version.  
3. Confirm no data loss.  
4. If verified:  
Keep:  
```
x_module governance glossary bulk terms.json

```
Delete:  
```
module governance glossary bulk terms.json

```
Otherwise:  
Mark for manual review.  
   
⸻  
   
## Required Output  
Produce:  
**1. Duplicate Cleanup Report**  
For each file:  
```
{
  "file": "",
  "action": "keep|delete|manual_review",
  "reason": "",
  "evidence": ""
}

```
**2. Deletion Summary**  
```
{
  "deleted_files": [],
  "kept_files": [],
  "manual_review_required": []
}

```
**3. Git Change Summary**  
List:  
* files deleted  
* references updated  
* authority documents affected  
   
⸻  
   
## Success Criteria  
Success means:  
* Exact duplicates removed.  
* Newest verified revisions retained.  
* No information loss.  
* No unresolved references.  
* No speculative deletions.  
* All deletions justified with evidence.  
