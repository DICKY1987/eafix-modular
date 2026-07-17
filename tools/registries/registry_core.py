from __future__ import annotations
import argparse, hashlib, json, sys
from collections import defaultdict
from pathlib import Path
from typing import Any
try:
    import jsonschema
except ImportError:
    jsonschema=None
ROOT=Path(__file__).resolve().parents[2]
REG_ROOT=ROOT/'EAFIX_auth_docs/01_canonical_registries'
GEN_ROOT=ROOT/'EAFIX_auth_docs/generated/registries'

def canonical_json(data:Any)->str:
    return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(data:Any)->str: return hashlib.sha256(canonical_json(data).encode()).hexdigest()
def read_json(path:Path)->Any: return json.loads(path.read_text(encoding='utf-8'))
def read_jsonl(path:Path)->list[dict]:
    out=[]
    for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: obj=json.loads(line)
        except json.JSONDecodeError as e: raise ValueError(f'{path}:{n}: malformed JSON: {e}') from e
        out.append(obj)
    return out
def write_json(path:Path,data:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def write_text(path:Path,text:str):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8',newline='\n')
def load_index(): return read_json(REG_ROOT/'registry_index.json')
def load_all():
    idx=load_index(); out={}
    for r in idx['registries']: out[r['name']]=read_jsonl(ROOT/r['path'])
    return idx,out
def validate_schemas(idx,all_records):
    errors=[]
    if jsonschema is None: return ['jsonschema package is required']
    resolver_store={}
    for p in (REG_ROOT/'schemas').glob('*.json'):
        s=read_json(p); resolver_store[s.get('$id',p.name)]=s
    for r in idx['registries']:
        sch=read_json(ROOT/r['schema']); validator=jsonschema.Draft202012Validator(sch)
        # jsonschema automatically resolves sibling file refs when base URI is supplied poorly across versions;
        # domain schemas contain the complete envelope and do not require external refs.
        for i,rec in enumerate(all_records[r['name']],1):
            for e in validator.iter_errors(rec): errors.append(f"{r['name']}:{i}:{e.json_path}:{e.message}")
    return errors
def validate_ids(all_records):
    errors=[]
    for name,recs in all_records.items():
        seen=set()
        for rec in recs:
            rid=rec.get('record_id')
            if rid in seen: errors.append(f'{name}: duplicate record_id {rid}')
            seen.add(rid)
        if [r['record_id'] for r in recs] != sorted(r['record_id'] for r in recs): errors.append(f'{name}: JSONL records are not sorted by record_id')
    return errors
def ids(all_records,name): return {r['record_id'] for r in all_records[name]}
def validate_refs(all_records):
    e=[]; mids={r['module_id'] for r in all_records['module']}; cids={r['contract_id'] for r in all_records['contract']}; sids={r['step_id'] for r in all_records['process']}; iids={r['integration_id'] for r in all_records['integration']}; aids={r['artifact_id'] for r in all_records['artifact']}; cfgs={r['config_id'] for r in all_records['configuration']}; ctrls={r['control_id'] for r in all_records['operational_control']}
    def chk(kind,rid,field,vals,valid):
        for v in vals:
            if v and v not in valid: e.append(f'{kind}:{rid}: unknown {field} {v}')
    for r in all_records['module']: chk('module',r['record_id'],'dependency',r['dependencies'],mids)
    for r in all_records['artifact']: chk('artifact',r['record_id'],'owner_module_id',[r['owner_module_id']],mids); chk('artifact',r['record_id'],'process_step_id',r['process_step_ids'],sids); chk('artifact',r['record_id'],'contract_id',r['contract_ids'],cids)
    for r in all_records['contract']: chk('contract',r['record_id'],'producer_module_id',r['producer_module_ids'],mids); chk('contract',r['record_id'],'consumer_module_id',r['consumer_module_ids'],mids); chk('contract',r['record_id'],'producer_step_id',r['producer_step_ids'],sids); chk('contract',r['record_id'],'consumer_step_id',r['consumer_step_ids'],sids)
    for r in all_records['integration']: chk('integration',r['record_id'],'owner_module_id',[r['owner_module_id']],mids); chk('integration',r['record_id'],'producer_module_id',r['producer_module_ids'],mids); chk('integration',r['record_id'],'consumer_module_id',r['consumer_module_ids'],mids); chk('integration',r['record_id'],'contract_id',r['contract_ids'],cids); chk('integration',r['record_id'],'fallback_integration_id',[r['fallback_integration_id']],iids)
    for r in all_records['process']: chk('process',r['record_id'],'owner_module_id',[r['owner_module_id']],mids); chk('process',r['record_id'],'dependency_step_id',r['dependency_step_ids'],sids); chk('process',r['record_id'],'input_contract_id',r['input_contract_ids'],cids); chk('process',r['record_id'],'output_contract_id',r['output_contract_ids'],cids); chk('process',r['record_id'],'integration_id',r['integration_ids'],iids); chk('process',r['record_id'],'artifact_id',r['artifact_ids'],aids); chk('process',r['record_id'],'validation_control_id',r['validation_control_ids'],ctrls); chk('process',r['record_id'],'failure_control_id',r['failure_control_ids'],ctrls); chk('process',r['record_id'],'configuration_id',r['configuration_ids'],cfgs)
    for r in all_records['configuration']: chk('configuration',r['record_id'],'owner_module_id',[r['owner_module_id']],mids); chk('configuration',r['record_id'],'consumer_step_id',r['consumer_step_ids'],sids)
    for r in all_records['operational_control']: chk('control',r['record_id'],'module_id',r['module_ids'],mids); chk('control',r['record_id'],'step_id',r['step_ids'],sids); chk('control',r['record_id'],'config_id',r['config_ids'],cfgs)
    for r in all_records['operator']: chk('operator',r['record_id'],'step_id',r['step_ids'],sids); chk('operator',r['record_id'],'failure_control_id',r['failure_control_ids'],ctrls); chk('operator',r['record_id'],'integration_id',r['integration_ids'],iids); chk('operator',r['record_id'],'configuration_id',r['configuration_ids'],cfgs)
    for r in all_records['reuse']: chk('reuse',r['record_id'],'module_id',r['module_ids'],mids); chk('reuse',r['record_id'],'artifact_id',r['artifact_ids'],aids); chk('reuse',r['record_id'],'integration_id',r['integration_ids'],iids)
    return e
def validate_authority(all_records):
    e=[]
    for name,recs in all_records.items():
        for r in recs:
            if r['authority_status']=='canonical' and r['status']!='canonical': e.append(f"{name}:{r['record_id']}: canonical authority requires canonical status")
    return e
def build_snapshots(idx,all_records,check=False):
    changed=[]; outputs={}
    for reg in idx['registries']:
        recs=sorted(all_records[reg['name']],key=lambda r:r['record_id'])
        snap={'schema_version':'1.0.0','document_type':'generated_registry_snapshot','registry_id':reg['registry_id'],'source_path':reg['path'],'record_count':len(recs),'records_sha256':sha(recs),'records':recs}
        path=ROOT/reg['generated_snapshot']; text=json.dumps(snap,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
        if check:
            if not path.exists() or path.read_text(encoding='utf-8')!=text: changed.append(str(path.relative_to(ROOT)))
        else: write_text(path,text)
        outputs[reg['name']]=snap
    return changed,outputs
def graph(all_records):
    edges=[]
    for r in all_records['module']:
        for d in r['dependencies']: edges.append({'from':r['module_id'],'to':d,'type':'module_depends_on'})
    for r in all_records['contract']:
        for p in r['producer_module_ids']: edges.append({'from':p,'to':r['contract_id'],'type':'produces'})
        for c in r['consumer_module_ids']: edges.append({'from':r['contract_id'],'to':c,'type':'consumed_by'})
    for r in all_records['process']:
        edges.append({'from':r['owner_module_id'],'to':r['step_id'],'type':'owns_step'})
        for d in r['dependency_step_ids']: edges.append({'from':d,'to':r['step_id'],'type':'step_precedes'})
    return {'schema_version':'1.0.0','document_type':'eafix_registry_graph','nodes':{k:v for k,v in all_records.items()},'edges':sorted(edges,key=lambda x:(x['type'],x['from'],x['to']))}
def reports(all_records,errors):
    conflicts=[r for name,recs in all_records.items() for r in recs if r['status']=='conflicted' or r['authority_status']=='needs_review']
    orphans=[]
    for r in all_records['module']:
        if not r['process_step_ids'] and not any(r['module_id'] in c['producer_module_ids']+c['consumer_module_ids'] for c in all_records['contract']): orphans.append({'record_id':r['record_id'],'reason':'module has no process or contract links'})
    completeness={}
    for name,recs in all_records.items():
        completeness[name]={'record_count':len(recs),'with_source_refs':sum(bool(r['source_refs']) for r in recs),'conflicted_or_review':sum(r['status']=='conflicted' or r['authority_status']=='needs_review' for r in recs),'canonical_count':sum(r['status']=='canonical' for r in recs)}
    return {
      'registry_cross_reference_report.json':{'schema_version':'1.0.0','validation_error_count':len(errors),'errors':errors,'status':'pass' if not errors else 'fail'},
      'registry_orphan_report.json':{'schema_version':'1.0.0','orphan_count':len(orphans),'orphans':orphans},
      'registry_conflict_report.json':{'schema_version':'1.0.0','conflict_count':len(conflicts),'conflicts':[{'registry_record':r['record_id'],'status':r['status'],'authority_status':r['authority_status']} for r in conflicts]},
      'registry_completeness_report.json':{'schema_version':'1.0.0','registries':completeness}}
def mermaid(all_records):
    lines=['flowchart LR']
    for r in all_records['module']:
        lines.append(f"  {r['module_id']}[\"{r['canonical_symbol']}\"]")
        for d in r['dependencies']: lines.append(f"  {r['module_id']} --> {d}")
    return '\n'.join(lines)+'\n'
def views(all_records):
    docs={}
    docs['module_catalog.generated.md']='---\ndoc_id: DOC-REG-0001\n---\n# Generated Module Catalog\n\n> Generated from `module_registry.jsonl`. Do not edit manually.\n\n'+ '\n'.join(f"- `{r['module_id']}` **{r['canonical_symbol']}** — {r['module_name']} ({r['status']})" for r in all_records['module'])+'\n'
    docs['process_catalog.generated.md']='---\ndoc_id: DOC-REG-0002\n---\n# Generated Process Catalog\n\n> Generated from `process_registry.jsonl`. Do not edit manually.\n\n'+ '\n'.join(f"- `{r['step_code']}` {r['step_name']} — owner `{r['owner_module_id']}`" for r in sorted(all_records['process'],key=lambda x:x['step_number']))+'\n'
    docs['contract_catalog.generated.md']='---\ndoc_id: DOC-REG-0003\n---\n# Generated Contract Catalog\n\n> Generated from `contract_registry.jsonl`. Do not edit manually.\n\n'+ '\n'.join(f"- `{r['contract_id']}` — {r['implementation_status']}" for r in all_records['contract'])+'\n'
    docs['operational_catalog.generated.md']='---\ndoc_id: DOC-REG-0004\n---\n# Generated Operational Catalog\n\n> Generated from the configuration, operational-control, operator, and reuse registries. Do not edit manually.\n\n'+f"- Configuration records: {len(all_records['configuration'])}\n- Operational controls: {len(all_records['operational_control'])}\n- Operator records: {len(all_records['operator'])}\n- Reuse records: {len(all_records['reuse'])}\n"
    docs['registry_system.generated.md']='---\ndoc_id: DOC-REG-0005\n---\n# EAFIX Registry System — Shadow Candidate\n\nThis generated view summarizes the candidate registry system. It is **not yet the canonical authority**. Registry-by-registry cutover requires parity approval, conflict resolution, routing updates, document-authority updates, and blocking CI in separate pull requests.\n\n'+ '\n'.join(f"- {k}: {len(v)} records" for k,v in all_records.items())+'\n'
    return docs
def run(check=False,report_only=False):
    idx,all_records=load_all(); errors=[]
    errors+=validate_schemas(idx,all_records); errors+=validate_ids(all_records); errors+=validate_refs(all_records); errors+=validate_authority(all_records)
    changed,snaps=build_snapshots(idx,all_records,check=check)
    if not check:
        write_json(GEN_ROOT/'eafix_registry_graph.current.json',graph(all_records))
        for n,d in reports(all_records,errors).items(): write_json(GEN_ROOT/n,d)
        write_text(GEN_ROOT/'registry_dependency_graph.mmd',mermaid(all_records))
        for n,t in views(all_records).items(): write_text(GEN_ROOT/n,t)
        manifest={'schema_version':'1.0.0','document_type':'registry_build_manifest','input_hashes':{r['path']:hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() for r in idx['registries']},'output_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(GEN_ROOT.glob('*')) if p.is_file()}}
        write_json(GEN_ROOT/'registry_build_manifest.json',manifest)
    else:
        if changed: errors += [f'generated output differs or missing: {x}' for x in changed]
    if errors:
        print('\n'.join(errors),file=sys.stderr)
        if not report_only: return 1
    print(f"validated {sum(len(v) for v in all_records.values())} records across {len(all_records)} registries; errors={len(errors)}; changed={len(changed)}")
    return 0
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--check',action='store_true'); p.add_argument('--report-only',action='store_true'); a=p.parse_args(); raise SystemExit(run(a.check,a.report_only))
