#!/usr/bin/env python3
"""EAFIX Process Consolidation Verifier v1.1.0.

Fail-closed, standard-library-only verifier for the hardened process consolidation
runbook. This version fixes the v1.0 gate defects by adding:
  * gate-aware source checks;
  * manifest structure validation;
  * authority-lineage and human-ballot gates;
  * exact baseline registry hash binding;
  * per-record/per-field gap validation;
  * base-ref mutation-scope validation;
  * material-process conflict filtering;
  * stage-aware source relocation checks;
  * projection parity, Markdown coverage, and generator no-op detection.

Exit codes: 0 pass, 1 gate failure, 2 verifier could not run.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

REG_JSONL = "EAFIX_auth_docs/01_canonical_registries/process_registry.jsonl"
STEP_CATALOG = "EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json"
CONFLICT_QUEUE = "EAFIX_auth_docs/01_canonical_registries/registry_conflict_queue.jsonl"
PROJECTION = "EAFIX_auth_docs/generated/registries/process_registry.current.json"
MARKDOWN_PROJECTION = "EAFIX_auth_docs/generated/registries/process_catalog.generated.md"
BUILD_MANIFEST = "EAFIX_auth_docs/generated/registries/registry_build_manifest.json"
COMPLETENESS = "EAFIX_auth_docs/generated/registries/registry_completeness_report.json"
SOURCE_MANIFEST = "EAFIX_auth_docs/process_consolidation_source_manifest_v1_1_0.json"
AUTHORITY_DECISION = "EAFIX_auth_docs/process_consolidation/PROCESS_AUTHORITY_LINEAGE_DECISION.json"
FIELD_BALLOT = "EAFIX_auth_docs/process_consolidation/HD-PC-01_field_adjudication.json"
BUILD_SCRIPT = "tools/registries/build_registries.py"
EXPECTED_RECORD_COUNT = 26
EXPECTED_STEP_CODES = [f"S{n:02d}" for n in range(1, 27)]
RECORD_ID_PREFIX = "600000000000000000"
IMMUTABLE_FIELDS = {"record_id","step_id","step_code","step_number","process_order","owner_module_id"}
GATES = ["AUTH-00","AUTH-01","STEP-00","STEP-01","STEP-02","STEP-03","STEP-04","STEP-05","STEP-06","STEP-07","STEP-08","STEP-09"]

class Results:
    def __init__(self): self.checks=[]; self.failed=0
    def add(self,cid,ok,detail,severity="FAIL"):
        status="PASS" if ok else severity
        self.checks.append({"check_id":cid,"status":status,"detail":detail})
        if not ok and severity=="FAIL": self.failed+=1
        return ok

def abort(msg):
    print(f"VERIFIER-ABORT: {msg}",file=sys.stderr); raise SystemExit(2)

def read_json(path):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError: abort(f"missing {path}")
    except json.JSONDecodeError as e: abort(f"invalid JSON {path}: {e}")

def read_jsonl(path):
    out=[]
    try:
        for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
            if line.strip():
                try: out.append(json.loads(line))
                except json.JSONDecodeError as e: abort(f"invalid JSONL {path}:{n}: {e}")
    except FileNotFoundError: abort(f"missing {path}")
    return out

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(65536),b""): h.update(chunk)
    return h.hexdigest()

def filled(v): return not (v is None or v=="" or v==[] or v=={})
def stage_at_least(gate,target): return GATES.index(gate)>=GATES.index(target)
def field_resolution(record, field): return (record.get("field_resolution") or {}).get(field) or {}
def field_resolution_status(record, field): return field_resolution(record, field).get("status")

def git_show(root,ref,path):
    cp=subprocess.run(["git","-C",str(root),"show",f"{ref}:{path}"],capture_output=True)
    if cp.returncode: abort(f"git show {ref}:{path} failed: {cp.stderr.decode(errors='replace')}")
    return cp.stdout

def parse_jsonl_bytes(data,label):
    out=[]
    for n,line in enumerate(data.decode("utf-8").splitlines(),1):
        if line.strip():
            try: out.append(json.loads(line))
            except json.JSONDecodeError as e: abort(f"invalid JSONL in {label}:{n}: {e}")
    return out

def check_spine(root,records,res):
    res.add("SPINE-01-record-count",len(records)==26,f"expected 26, found {len(records)}")
    codes=[r.get("step_code") for r in records]
    res.add("SPINE-02-step-codes",sorted(c for c in codes if c)==EXPECTED_STEP_CODES,f"codes={codes}")
    res.add("SPINE-03-unique-codes",len(codes)==len(set(codes)),"duplicate step_code values detected" if len(codes)!=len(set(codes)) else "unique")
    ids=[r.get("record_id") for r in records]
    res.add("SPINE-04-unique-record-ids",len(ids)==len(set(ids)),"duplicate record IDs detected" if len(ids)!=len(set(ids)) else "unique")
    bad=[]
    for r in records:
        code=r.get("step_code") or ""
        exp=RECORD_ID_PREFIX+(code[1:].zfill(2) if code.startswith("S") else "??")
        if r.get("record_id")!=exp or r.get("step_id")!=exp: bad.append((code,r.get("record_id"),r.get("step_id"),exp))
    res.add("SPINE-05-id-binding",not bad,f"violations={bad}")
    orders=sorted(r.get("process_order") for r in records if isinstance(r.get("process_order"),int))
    res.add("SPINE-06-process-order",orders==list(range(1,27)),f"orders={orders}")
    cat=read_json(root/STEP_CATALOG)
    cmap={x.get("step_code"):x.get("module_id") for x in cat.get("steps",[])}
    drift=[(r.get("step_code"),r.get("owner_module_id"),cmap.get(r.get("step_code"))) for r in records if r.get("owner_module_id")!=cmap.get(r.get("step_code"))]
    res.add("SPINE-07-module-binding-parity",not drift,f"drift={drift}")

def check_authority(root,res,gate):
    if not stage_at_least(gate,"AUTH-01"): return
    p=root/AUTHORITY_DECISION
    if not p.exists(): res.add("AUTHROOT-01-decision-present",False,f"missing {AUTHORITY_DECISION}"); return
    d=read_json(p)
    approved=d.get("status") in {"APPROVED","approved"} and bool(d.get("approved_by"))
    res.add("AUTHROOT-01-decision-approved",approved,f"status={d.get('status')} approved_by={d.get('approved_by')}")
    res.add("AUTHROOT-02-option-selected",d.get("selected_option_id") in {"P1-A","P1-B","P1-C"},f"selected={d.get('selected_option_id')}")
    s25=d.get("s25_disposition",{})
    res.add("AUTHROOT-03-s25-resolved",s25.get("status")=="RESOLVED" and s25.get("classification") in {"approved_ownership_decision","projection_normalization","unsupported_inference"},f"s25={s25}")
    res.add("AUTHROOT-04-artifact-roles",isinstance(d.get("artifact_roles"),list) and len(d.get("artifact_roles"))>0,"artifact_roles must classify every process artifact")
    res.add("AUTHROOT-05-cutover-mode",d.get("ssot_cutover_mode") in {"independent_process_cutover","staged_multi_registry_cutover","defer_until_full_registry_cutover"},f"mode={d.get('ssot_cutover_mode')}")

def validate_manifest_structure(m,res):
    srcs=m.get("frozen_sources",[]); count=m.get("source_count")
    res.add("MAN-01-source-count",count==len(srcs)==m.get("manifest_validation",{}).get("expected_source_count",11),f"declared={count} actual={len(srcs)}")
    ids=[x.get("source_id") for x in srcs]; paths=[x.get("active_path") for x in srcs]; ex=[x.get("extraction_artifact") for x in srcs]; orders=[x.get("merge_order") for x in srcs]
    res.add("MAN-02-unique-ids",len(ids)==len(set(ids)) and all(re.fullmatch(r"PCSRC-[0-9]{2}",x or "") for x in ids),f"ids={ids}")
    res.add("MAN-03-unique-paths",len(paths)==len(set(paths)),"active paths must be unique")
    res.add("MAN-04-unique-extractions",len(ex)==len(set(ex)),"extraction paths must be unique")
    res.add("MAN-05-contiguous-order",sorted(orders)==list(range(1,len(srcs)+1)),f"orders={orders}")
    badhash=[x.get("source_id") for x in srcs if not re.fullmatch(r"[0-9a-f]{64}",x.get("sha256") or "")]
    res.add("MAN-06-valid-hashes",not badhash,f"invalid={badhash}")
    badsize=[x.get("source_id") for x in srcs if not isinstance(x.get("byte_size"),int) or x.get("byte_size")<=0]
    res.add("MAN-07-valid-sizes",not badsize,f"invalid={badsize}")
    facts=set(m.get("fact_classes",[])); badfacts=[]
    for x in srcs:
        if set(x.get("authority_by_fact_class",{}))!=facts: badfacts.append(x.get("source_id"))
    res.add("MAN-08-fact-class-completeness",not badfacts,f"incomplete={badfacts}")

def load_manifest(root,res,gate):
    if not stage_at_least(gate,"AUTH-00"): return None
    p=root/SOURCE_MANIFEST
    if not p.exists(): res.add("MAN-00-present",False,f"missing {SOURCE_MANIFEST}"); return None
    m=read_json(p); res.add("MAN-00-present",True,SOURCE_MANIFEST); validate_manifest_structure(m,res)
    base=m.get("merge_target_baseline",{})
    bound=base.get("binding_status")=="BOUND" and re.fullmatch(r"[0-9a-f]{64}",base.get("sha256") or "") and isinstance(base.get("byte_size"),int)
    res.add("BASE-01-bound",bool(bound),f"binding_status={base.get('binding_status')} sha={base.get('sha256')} size={base.get('byte_size')}")
    return m

def check_baseline(root,m,res,gate):
    if not m: return
    base=m["merge_target_baseline"]; reg=root/base["path"]
    if stage_at_least(gate,"AUTH-00") and GATES.index(gate)<=GATES.index("STEP-03"):
        actual=sha256(reg)
        res.add("BASE-02-registry-unchanged",actual==base.get("sha256"),f"expected={base.get('sha256')} actual={actual}")
        res.add("BASE-03-registry-size",reg.stat().st_size==base.get("byte_size"),f"expected={base.get('byte_size')} actual={reg.stat().st_size}")

def check_sources(root,m,res,gate):
    if not m or not stage_at_least(gate,"STEP-02"): return
    post=stage_at_least(gate,"STEP-08")
    missing=[]; drift=[]; wrong_location=[]
    for s in m.get("frozen_sources",[]):
        use_archive=post and s.get("retirement_policy")=="archive_after_verified_cutover"
        rel=s.get("archive_path") if use_archive else s.get("active_path")
        if not rel: wrong_location.append((s.get("source_id"),"no expected path")); continue
        p=root/rel
        if not p.exists(): missing.append(rel); continue
        actual=sha256(p)
        if actual!=s.get("sha256") or p.stat().st_size!=s.get("byte_size"): drift.append((s.get("source_id"),rel,s.get("sha256"),actual,p.stat().st_size))
        if use_archive and (root/s.get("active_path")).exists(): wrong_location.append((s.get("source_id"),"active copy remains after cutover"))
    res.add("SRC-01-present-at-stage-location",not missing,f"missing={missing}")
    res.add("SRC-02-hash-and-size",not drift,f"drift={drift}")
    res.add("SRC-03-location-policy",not wrong_location,f"violations={wrong_location}")

def check_ballot(root,res,gate):
    if not stage_at_least(gate,"STEP-01"): return None
    p=root/FIELD_BALLOT
    if not p.exists(): res.add("BALLOT-01-present",False,f"missing {FIELD_BALLOT}"); return None
    b=read_json(p); approved=b.get("status") in {"APPROVED","approved"} and bool(b.get("approved_by"))
    res.add("BALLOT-01-approved",approved,f"status={b.get('status')} approved_by={b.get('approved_by')}")
    allowed=set(b.get("allowed_dispositions",[])); bad=[x.get("field") for x in b.get("fields",[]) if x.get("selected_disposition") not in allowed]
    res.add("BALLOT-02-complete",not bad,f"unresolved={bad}")
    resolution_statuses=b.get("required_field_resolution_statuses",[])
    if resolution_statuses:
        expected={"populated","confirmed_none","not_applicable","deferred_gap","lifecycle_not_triggered","derived"}
        res.add("BALLOT-03-resolution-statuses",set(resolution_statuses)==expected,f"statuses={resolution_statuses}")
    return b

def gap_id(step,field): return f"GAP::PROCESS::{step}::{field.upper()}"
def check_cell_completeness(records,ballot,res,gate):
    if not ballot or not stage_at_least(gate,"STEP-06"): return
    violations=[]; required_missing=[]; removed_present=[]; derived_missing=[]; cutover_missing=[]; applicability_missing=[]; lifecycle_bad=[]
    for pol in ballot.get("fields",[]):
        field=pol.get("field"); disp=pol.get("selected_disposition"); overrides={x.get("step_code"):x.get("disposition") for x in pol.get("record_overrides",[])}
        for r in records:
            step=r.get("step_code"); d=overrides.get(step,disp); value=r.get(field); status=field_resolution_status(r, field)
            if d=="required_for_baseline" and not filled(value): required_missing.append((step,field))
            elif d=="deferred_with_gap_id" and not filled(value) and gap_id(step,field) not in (r.get("gap_ids") or []): violations.append((step,field,gap_id(step,field)))
            elif d=="required_when_applicable" and not filled(value) and status not in {"confirmed_none","not_applicable"}: applicability_missing.append((step,field,status))
            elif d=="derived_at_build" and status != "derived": derived_missing.append((step,field,status))
            elif d=="lifecycle_event_only" and not filled(value) and status not in {"lifecycle_not_triggered","not_applicable"}: lifecycle_bad.append((step,field,status))
            elif d=="required_at_cutover" and stage_at_least(gate,"STEP-08") and not filled(value): cutover_missing.append((step,field))
            elif d=="removed_from_schema" and field in r: removed_present.append((step,field))
    res.add("CELL-01-required-populated",not required_missing,f"missing={required_missing}")
    res.add("CELL-02-deferred-gaps-explicit",not violations,f"missing_gap_ids={violations}")
    res.add("CELL-03-applicability-resolved",not applicability_missing,f"missing={applicability_missing}")
    res.add("CELL-04-derived-fields-marked",not derived_missing,f"missing={derived_missing}")
    res.add("CELL-05-lifecycle-fields-marked",not lifecycle_bad,f"missing={lifecycle_bad}")
    res.add("CELL-06-cutover-fields-populated",not cutover_missing,f"missing={cutover_missing}")
    res.add("CELL-07-removed-fields-absent",not removed_present,f"present={removed_present}")

def material_conflict(c,process_ids):
    if c.get("process_material") is True: return True
    if c.get("process_material") is False: return False
    if c.get("consolidation_pass_id")=="PROCESS-CONSOLIDATION-v1.1.0": return True
    if c.get("record_id") in process_ids or c.get("target_record_id") in process_ids: return True
    if str(c.get("conflict_id","")).startswith("CONFLICT::PROCESS::"): return True
    if c.get("record_type") in {"process_step","process_conflict"}: return True
    return c.get("domain") in {"process","process_authority"}

def check_conflicts(root,records,res,gate):
    p=root/CONFLICT_QUEUE
    if not p.exists(): res.add("CONF-00-present",False,f"missing {CONFLICT_QUEUE}"); return
    cs=read_jsonl(p); ids={r.get("record_id") for r in records}; relevant=[c for c in cs if material_conflict(c,ids)]
    unresolved=[c.get("conflict_id") for c in relevant if not c.get("review_decision")]
    res.add("CONF-01-readable",True,f"total={len(cs)} material={len(relevant)} unresolved_material={len(unresolved)}",severity="INFO")
    if stage_at_least(gate,"STEP-07"): res.add("CONF-02-material-resolved",not unresolved,f"unresolved={unresolved}")

def registry_map(records): return {r.get("record_id"):r for r in records}
def check_diff_scope(root,records,res,gate,base_ref):
    if not base_ref: return
    base=parse_jsonl_bytes(git_show(root,base_ref,REG_JSONL),f"{base_ref}:{REG_JSONL}")
    bm,cm=registry_map(base),registry_map(records)
    if set(bm)!=set(cm): res.add("DIFF-00-record-set",False,"record set changed"); return
    violations=[]
    for rid in bm:
        b,c=bm[rid],cm[rid]
        for f in sorted(set(b)|set(c)):
            if b.get(f)==c.get(f): continue
            if f in IMMUTABLE_FIELDS: violations.append((rid,f,"immutable")); continue
            if gate in {"STEP-00","STEP-01","STEP-02","STEP-03","STEP-05","STEP-07","STEP-09"}: violations.append((rid,f,"registry must not change in this gate"))
            elif gate=="STEP-04":
                if f=="source_refs" and isinstance(b.get(f),list) and isinstance(c.get(f),list) and c.get(f)[:len(b.get(f))]==b.get(f): pass
                elif not filled(b.get(f)) and filled(c.get(f)): pass
                else: violations.append((rid,f,"only empty-to-filled or source_refs append allowed"))
            elif gate=="STEP-06" and f!="gap_ids": violations.append((rid,f,"only gap_ids allowed"))
            elif gate=="STEP-08" and f not in {"authority_status","status","supersedes","superseded_by","source_refs","effective_from_utc"}: violations.append((rid,f,"cutover field not allowed"))
    res.add("DIFF-01-gate-scope",not violations,f"violations={violations[:50]}")

def projection_records(obj):
    if isinstance(obj,list): return obj
    for k in ("records","process_steps","steps"):
        if isinstance(obj.get(k),list): return obj[k]
    return []
def check_projection(root,records,res,gate,run_generator_check):
    if not stage_at_least(gate,"STEP-07"): return
    required=[PROJECTION,MARKDOWN_PROJECTION,BUILD_MANIFEST,COMPLETENESS]
    missing=[p for p in required if not (root/p).exists()]
    res.add("PROJ-01-files-present",not missing,f"missing={missing}")
    if missing: return
    pobj=read_json(root/PROJECTION); precs=projection_records(pobj)
    res.add("PROJ-02-record-count",len(precs)==26,f"found={len(precs)}")
    pm={r.get("record_id") or r.get("step_id"):r for r in precs}; drift=[]
    for r in records:
        p=pm.get(r.get("record_id"))
        if not p: drift.append((r.get("step_code"),"missing")); continue
        for f in ("step_code","step_name","phase_id","owner_module_id"):
            if p.get(f)!=r.get(f): drift.append((r.get("step_code"),f,r.get(f),p.get(f)))
    res.add("PROJ-03-identity-parity",not drift,f"drift={drift}")
    md=(root/MARKDOWN_PROJECTION).read_text(encoding="utf-8")
    absent=[r.get("step_code") for r in records if r.get("step_code") not in md or r.get("step_name") not in md]
    res.add("PROJ-04-markdown-step-coverage",not absent,f"missing={absent}")
    header_ok=("do not edit" in md.lower() or "generated" in md.lower()) and ("process_registry.jsonl" in md or "source" in md.lower())
    res.add("PROJ-05-generated-header",header_ok,"Markdown must identify generated status and source")
    if run_generator_check:
        cp=subprocess.run([sys.executable,str(root/BUILD_SCRIPT),"--check"],cwd=root,capture_output=True,text=True)
        combined=(cp.stdout+"\n"+cp.stderr).lower()
        ok = cp.returncode == 0 and "jsonschema package is required" not in combined
        res.add("PROJ-06-generator-check",ok,f"exit={cp.returncode} output={combined[-1000:]}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",default=".")
    ap.add_argument("--gate",choices=GATES,default="AUTH-00")
    ap.add_argument("--base-ref",help="Git ref used to enforce gate mutation scope")
    ap.add_argument("--json",dest="json_out")
    ap.add_argument("--run-generator-check",action="store_true")
    args=ap.parse_args(); root=Path(args.repo_root).resolve()
    reg=root/REG_JSONL
    if not reg.exists(): abort(f"missing {REG_JSONL}")
    records=read_jsonl(reg); res=Results()
    check_spine(root,records,res)
    check_authority(root,res,args.gate)
    manifest=load_manifest(root,res,args.gate)
    check_baseline(root,manifest,res,args.gate)
    check_sources(root,manifest,res,args.gate)
    ballot=check_ballot(root,res,args.gate)
    check_cell_completeness(records,ballot,res,args.gate)
    check_conflicts(root,records,res,args.gate)
    check_diff_scope(root,records,res,args.gate,args.base_ref)
    check_projection(root,records,res,args.gate,args.run_generator_check)
    verdict="PASS" if res.failed==0 else "FAIL"
    for c in res.checks: print(f"[{c['status']:<4}] {c['check_id']:<38} {c['detail']}")
    print(f"GATE {args.gate}: {verdict} ({res.failed} failed)")
    report={"gate":args.gate,"verdict":verdict,"record_count":len(records),"checks":res.checks}
    if args.json_out: Path(args.json_out).parent.mkdir(parents=True,exist_ok=True); Path(args.json_out).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return 0 if res.failed==0 else 1
if __name__=="__main__": raise SystemExit(main())
