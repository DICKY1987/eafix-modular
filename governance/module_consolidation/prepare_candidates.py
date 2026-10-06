"""Lossless v1 migration and evidence-backed, explicitly incomplete v2 candidates.

This command cannot replace active module manifests or flip authority routing.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
from pathlib import Path
from collections import Counter, defaultdict

from authority_core import (BUNDLE, CONTROL, PROCESS, REGISTRIES, REPO, SCHEMA, SHARED,
                            file_sha, jsonl, leaves, load, pointer, value_sha, write, write_jsonl)

APPROVER = 'Codex acting under the repository owner\'s execution instructions v1.0.0'


def obj(properties, required=None):
    return {'type':'object','additionalProperties':False,'properties':properties,
            'required':list(properties) if required is None else required}


def arr(item):
    return {'type':'array','items':item}


def schema():
    text={'type':'string'}
    strings=arr(text)
    identifier={'type':'string','minLength':1}
    fact=obj({'applicability':{'enum':['applicable','not_applicable','undetermined']},
              'knowledge':{'enum':['confirmed','unknown','conflicted','deferred']},
              'value':{},'reason':{'type':['string','null']},'decision_id':identifier,
              'evidence_refs':strings,'gap_ids':strings})
    fact['allOf']=[
      {'if':{'properties':{'knowledge':{'const':'confirmed'}}},'then':{'properties':{'evidence_refs':{'minItems':1}}}},
      {'if':{'properties':{'applicability':{'const':'not_applicable'}}},'then':{'properties':{'knowledge':{'const':'confirmed'},'reason':{'type':'string','minLength':1},'value':{'type':'null'}}}},
      {'if':{'properties':{'knowledge':{'enum':['unknown','conflicted','deferred']}}},'then':{'properties':{'gap_ids':{'minItems':1}}}}
    ]
    ref=lambda name:{'$ref':'#/$defs/'+name}
    evidence=obj({'evidence_id':identifier,'target_json_pointer':identifier,'target_element_id':{'type':['string','null']},
                  'approved_value_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
                  'source_path':identifier,'source_commit':{'type':['string','null']},'source_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
                  'source_locator':{'type':'object','additionalProperties':True},'claim_summary':text,
                  'claim_disposition':{'enum':['MIGRATE','ALREADY_COVERED','MERGE','REJECTED','RETAINED_EXTERNAL']},
                  'decision_id':identifier,'approver':identifier,'verification_status':{'enum':['source_verified','candidate_applied','authority_applied','unverified']}})
    file_record=obj({'file_id':identifier,'path':identifier,'role':{'enum':['entrypoint','library','schema','config','fixture','test','doc','data','tooling','runtime_asset']},
                     'required':{'type':['boolean','null']},'ownership_status':{'enum':['baseline_declared','verified','candidate','global_shared']},
                     'current_or_proposed_location':{'enum':['current','proposed']},'content_sha256':{'type':['string','null']},
                     'entrypoint':{'type':'boolean'},'runtime_relevance':{'enum':['runtime','supporting','undetermined']},
                     'contracts_produced':strings,'contracts_consumed':strings,'evidence_refs':strings})
    file_use=obj({'file_id':identifier,'path':identifier,'role_in_this_step':text,'required':{'type':['boolean','null']},'knowledge':{'enum':['confirmed','unknown','deferred']}})
    step_properties={'step_id':{'type':'string','pattern':'^6[0-9]{19}$'},'step_code':{'type':'string','pattern':'^S[0-9]{2}$'},
                     'process_registry_ref':{'const':PROCESS},'participation_role':{'enum':['primary_owner','supporting']}}
    for name in ['trigger','preconditions','inputs','processing','decisions','primary_output','secondary_outputs','validation',
                 'failure_output','retry_timeout_recovery','observability','completion_criteria','next_handoff_refs']:
        step_properties[name]=ref('fact')
    step_properties.update({'exclusive_files':arr(ref('file_use')),'shared_files':arr(ref('file_use')),
                            'contract_refs':strings,'state_transition_refs':strings})
    contract=obj({'usage_id':identifier,'name':identifier,'contract_id':{'type':['string','null']},'version':{'type':['string','null']},
                  'authority_path':{'type':['string','null']},'schema_path':{'type':['string','null']},
                  'role':{'enum':['producer','consumer','transformer','validator','boundary']},'step_ids':strings,
                  'compatibility':ref('fact'),'knowledge':{'enum':['confirmed','unknown','deferred']},'gap_ids':strings,'evidence_refs':strings})
    identity=obj({'module_id':{'type':'string','pattern':'^5[0-9]{19}$'},'short_id':{'type':'string','pattern':'^m[0-9]{4}$'},
                  'canonical_symbol':identifier,'canonical_root':identifier,'module_name':identifier,'aliases':strings,
                  'identity_status':{'const':'canonical'},'lifecycle_status':identifier,'specification_version':identifier,'accountable_owner':identifier})
    properties={'schema_version':{'const':'2.0.0'},'document_type':{'const':'atomic_module_manifest'},'manifest_version':identifier,
                'authority':obj({'status':{'enum':['candidate','canonical']},'policy':{'const':'reviewed_module_root_authority'},
                  'effective_baseline_commit':{'type':'string','pattern':'^[0-9a-f]{40}$'},'approval_authority':identifier}),
                'module_identity':identity,'profile':{'enum':['process_service','mt4_runtime','operator_ui','shared_reusable','cross_cutting']},
                'purpose_and_boundaries':obj({k:ref('fact') for k in ['purpose','responsibilities','exclusions','owned_capabilities','side_effects','trust_boundary','externally_visible_behavior']}),
                'process_steps':arr(ref('process_step')),
                'process_participation':ref('fact'),
                'files':obj({'scope_status':{'enum':['open','closed']},'definitions':arr(ref('file_definition')),'shared_uses':arr(ref('file_use')),'required_file_inventory':ref('fact')}),
                'contracts':arr(ref('contract_use')),
                'runtime':obj({k:ref('fact') for k in ['kind','language_platform','entrypoints','ports_channels','deployment_unit','external_dependencies','configuration_sources','startup_shutdown','restart_semantics','concurrency_ordering','required_files']}),
                'state':obj({'variables':ref('fact'),'owner':ref('fact'),'persistence':ref('fact'),'transitions':arr(obj({'transition_id':identifier,'from_state':text,'to_state':text,'trigger':text,'evidence_refs':strings})),
                             'ordering':ref('fact'),'idempotency':ref('fact'),'duplicate_handling':ref('fact'),'recovery':ref('fact')}),
                'failure_and_safety':obj({k:ref('fact') for k in ['validation','failure_modes','rejection_outputs','retry_policy','timeout_policy','fail_closed','recovery_quarantine','safety_gates','risk_controls','error_codes','operator_escalation']}),
                'observability_quality':obj({k:ref('fact') for k in ['logs','metrics','health_checks','slos','performance','acceptance_criteria','test_references','implementation_evidence']}),
                'verification_commands':obj({k:ref('fact') for k in ['build','test','lint','typecheck','smoke_check','local_run']}),
                'evidence':arr(ref('evidence')),
                'reconciliation':obj({'status':{'enum':['candidate','blocked','reconciled']},'schema_valid':{'type':'boolean'},'specification_ready':{'type':'boolean'},
                  'implementation_verified':{'type':'boolean'},'implementation_conformance':{'enum':['unverified','partial','verified','diverged']},
                  'unresolved_gap_ids':strings,'conflict_ids':strings,'last_verified_commit':text,'stale_after':text}),
                'migration':obj({'source_manifest_path':identifier,'source_manifest_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'source_commit':text,
                  'original_snapshot_path':identifier,'original_v1':{'type':'object','additionalProperties':True},'original_content_role':{'const':'immutable_historical_evidence_only'},
                  'migration_map_ref':{'const':'governance/module_consolidation/v1_to_v2_migration_map.json'}})}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:eafix:atomic-module-manifest:2.0.0',
            'title':'EAFIX atomic module manifest v2','description':'Candidate and canonical structure. Specification readiness is enforced separately; unknown is never not-applicable.',
            **obj(properties),'$defs':{'fact':fact,'evidence':evidence,'file_definition':file_record,'file_use':file_use,'process_step':obj(step_properties),'contract_use':contract}}


def role(path):
    low=path.lower()
    if '/tests/' in low or '/test' in low or low.split('/')[-1].startswith('test_'): return 'test'
    if 'fixtures/' in low: return 'fixture'
    if '.schema.' in low: return 'schema'
    if 'config' in low or low.endswith('settings.py'): return 'config'
    if low.endswith(('.md','.txt','.pdf','.docx')): return 'doc'
    if low.endswith(('.py','.mq4','.mqh')): return 'library'
    if low.endswith(('.json','.csv','.yaml','.yml')): return 'data'
    return 'runtime_asset'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--instruction-path',type=Path,default=CONTROL/'inputs/00-execution-instructions.txt');args=parser.parse_args()
    baseline=load(CONTROL/'run/baseline.json'); commit=baseline['baseline_commit']; timestamp=baseline['pinned_at_utc']
    for root, expected_hash in baseline['original_manifest_hashes'].items():
        if file_sha(REPO/root/'manifest.json') != expected_hash:
            raise ValueError('STALE_BASELINE: active root changed; candidate regeneration is forbidden')
    universe=load(CONTROL/'module_universe.json'); sources=jsonl(CONTROL/'run/source_processing_ledger.jsonl'); source_index={x['path']:x for x in sources}
    instruction=args.instruction_path.read_text(); decisions=[]
    pattern=r'(DEC-\d{3}): ([^\n]+)\n\nDecision: (.*?)(?=\n\nDEC-|\n\nRecord the actual)'
    for did,title,body in re.findall(pattern,instruction,re.S):
        decisions.append({'decision_id':did,'status':'approved_policy_pending_cutover','title':title,'decision':body.strip(),
          'rationale':'Prescribed by the owner in the standalone execution instructions; no reversal is authorized.',
          'affected_authorities':['34 module-root manifests',PROCESS,SHARED,BUNDLE], 'effective_baseline':commit,
          'effective_commit':None,'evidence_refs':[{'path':args.instruction_path.relative_to(REPO).as_posix(),'sha256':file_sha(args.instruction_path),'section':'9'}],
          'approved_by':'Repository owner through execution instructions 1.0.0','executed_by':APPROVER})
    if len(decisions)!=26: raise ValueError('Expected exactly 26 prescribed decisions')
    decisions.extend([
      {'decision_id':'DEC-027','status':'approved_for_execution','title':'No cutover waiver for missing mandatory facts',
       'decision':'Do not convert source scanning or structural schema validity into specification readiness. Keep active v1 authorities in place until P5 passes.',
       'rationale':'Sections 21, 30, 31 and 35 explicitly require fail-closed handling of insufficient evidence.',
       'affected_authorities':['34 module-root manifests'],'effective_baseline':commit,'effective_commit':None,
       'evidence_refs':[{'path':args.instruction_path.relative_to(REPO).as_posix(),'sha256':file_sha(args.instruction_path),'section':'21,30,31,35'}],'approved_by':APPROVER},
      {'decision_id':'DEC-028','status':'approved_for_execution','title':'Confirm process participation by registry identity',
       'decision':'Use owner_module_id and supporting_module_ids from process_registry.jsonl. Empty participation means no authored registry binding at this baseline; it does not mean the module has no runtime behavior.',
       'rationale':'The live registry owns process identity and topology. Legacy step 0 / N/A has no valid process identity.',
       'affected_authorities':[PROCESS,'34 v2 candidates'],'effective_baseline':commit,'effective_commit':None,
       'evidence_refs':[{'path':PROCESS,'sha256':file_sha(REPO/PROCESS),'section':'owner_module_id and supporting_module_ids'}],'approved_by':APPROVER},
      {'decision_id':'DEC-029','status':'approved_for_execution','title':'Keep unversioned wire references explicit',
       'decision':'A resolved live contract-registry record may be referenced without an invented schema. Mark a missing executable schema as deferred and nonblocking for schema structure only; do not waive an unknown mandatory boundary definition.',
       'rationale':'DEC-020 permits explicit schema gaps but does not authorize an invented interface or a specification-readiness waiver.',
       'affected_authorities':['contract uses in 34 candidates'],'effective_baseline':commit,'effective_commit':None,
       'evidence_refs':[{'path':args.instruction_path.relative_to(REPO).as_posix(),'sha256':file_sha(args.instruction_path),'section':'8.7,30'}],'approved_by':APPROVER},
      {'decision_id':'DEC-030','status':'approved_for_execution','title':'Preserve historical location decisions without executing moves',
       'decision':'Account for all 86 historical records against the new baseline, including moved paths. Keep runtime code physically unchanged.',
       'rationale':'DEC-017 and section 4 exclude bulk physical source migration.',
       'affected_authorities':['historical file mappings'],'effective_baseline':commit,'effective_commit':None,
       'evidence_refs':[{'path':'governance/module_consolidation/run/historical_86_revalidation.json','sha256':file_sha(CONTROL/'run/historical_86_revalidation.json'),'section':'all 86 records'}],'approved_by':APPROVER},
    ])
    # Reseeding must not discard subsequently approved governance decisions.
    existing_decisions = CONTROL/'resolution_decisions.json'
    if existing_decisions.is_file():
        generated_ids = {item['decision_id'] for item in decisions}
        decisions.extend(item for item in load(existing_decisions)['decisions']
                         if item['decision_id'] not in generated_ids)
    write(existing_decisions,{'schema_version':'1.0.0','decisions':decisions})
    write(REPO/SCHEMA,schema())
    matrix=[]
    for fact,authority,mode,rule in [
      ('module identity','<canonical-module-root>/manifest.json','authored','Pinned .module-id and the exact 34-module universe must agree.'),
      ('module purpose','<canonical-module-root>/manifest.json','authored','Preserve valid existing facts unless an evidenced decision changes them.'),
      ('module boundaries','<canonical-module-root>/manifest.json','authored','Private cross-module access remains forbidden.'),
      ('module behavior','<canonical-module-root>/manifest.json','authored','Do not turn observed implementation divergence into an intended behavior change.'),
      ('process step identity/order',PROCESS,'referenced','Module entries cannot reauthor global topology.'),
      ('shared contract schema','contracts/ and specialized contract authorities','referenced','No invented schemas; resolve exact live references.'),
      ('global identifier rules','contracts/identifiers/ and active naming governance','referenced','No new permanent IDs or aliases without a governed decision.'),
      ('shared-file consumer topology',SHARED,'authored','Local usage is declared in manifests; global fan-out only in the registry.'),
      ('current implementation','source code and tests at '+commit,'observed','Commit-pinned evidence only; runtime verification remains separate.'),
      ('reconciliation decisions','governance/module_consolidation/resolution_decisions.json','authored','Every accepted change needs a decision and provenance.'),
      ('archive status','governance/module_consolidation/run/source_processing_ledger.jsonl','authored','Fully scraped and safe-to-archive are independent.'),
      ('generated projections','root manifests plus global authorities','derived','Never read back to overwrite a module authority.')]:
        matrix.append({'fact_class':fact,'active_authority_after_cutover':authority,'mode':mode,'permitted_evidence_sources':['commit-pinned current authorities','complete reviewed sources','current code/tests for observations'],
                       'conflict_rule':rule,'duplication_policy':'prohibited' if mode=='referenced' else 'one_way' if mode=='derived' else 'single_authority'})
    write(CONTROL/'field_authority_matrix.json',{'status':'approved_policy_pending_cutover','effective_baseline':commit,'rows':matrix})
    processes=jsonl(REPO/PROCESS); contracts=jsonl(REPO/REGISTRIES/'contract_registry.jsonl'); controls=jsonl(REPO/REGISTRIES/'operational_control_registry.jsonl')
    by_contract={x['contract_name']:x for x in contracts}; by_control={x['record_id']:x for x in controls}
    claims=[]; gaps=[]; migration=[]; shared=defaultdict(list); candidates=[]
    for u in universe:
        short=u['short_id']; root=u['root']; mp=root+'/manifest.json'; old=load(REPO/mp); evidence=[]; module_gaps=[]
        snapshot=CONTROL/'staging'/short/'manifest.v1.original.json';snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/mp,snapshot)
        def ev(target,src,locator,summary,decision='DEC-007',disposition='MIGRATE',element=None):
            eid='EV-'+value_sha([short,target,src,locator])[:20]
            evidence.append({'evidence_id':eid,'target_json_pointer':target,'target_element_id':element,'source_path':src,'source_commit':commit if src in source_index and source_index[src]['source_class']=='repository' else None,
                'source_sha256':file_sha(REPO/src),'source_locator':locator,'claim_summary':summary,'claim_disposition':disposition,'decision_id':decision,'approver':APPROVER,'verification_status':'candidate_applied'})
            return eid
        def gap(target,reason,mandatory=True,source_refs=None):
            gid='GAP-'+short+'-'+value_sha([target,reason])[:12]
            record={'blocker_id':gid,'module':short,'json_pointer':target,'fact':target.split('/')[-1],'reason':reason,
                    'missing_evidence_or_decision':reason,'responsible_decision_maker':'repository owner or delegated specification reviewer','next_action':'Review the cited source and supply an approved, source-grounded value; preserve the original snapshot.',
                    'severity':'blocking' if mandatory else 'nonblocking','resolution_state':'unresolved','decision_id':'DEC-027' if mandatory else 'DEC-029','evidence_refs':source_refs or [mp]}
            gaps.append(record);module_gaps.append(gid);return gid
        def known(value,target,src=mp,source_pointer=None,decision='DEC-007',summary=None,element=None):
            eid=ev(target,src,{'json_pointer':target if source_pointer is None else source_pointer},summary or 'Preserved or referenced commit-pinned source value.',decision,element=element)
            return {'applicability':'applicable','knowledge':'confirmed','value':value,'reason':None,'decision_id':decision,'evidence_refs':[eid],'gap_ids':[]}
        def unknown(target,reason,mandatory=False,value=None):
            gid=gap(target,reason,mandatory)
            return {'applicability':'applicable','knowledge':'unknown','value':value,'reason':reason,'decision_id':'DEC-027','evidence_refs':[],'gap_ids':[gid]}
        def inherited(target,source_pointer,mandatory=False):
            value=pointer(old,source_pointer)
            if value is None or value=='' or value==[] or value=={} or value=='needs_review' or (isinstance(value,list) and 'needs_review' in value):
                return unknown(target,'Existing v1 source does not establish an approved value for '+source_pointer,mandatory)
            return known(value,target,source_pointer=source_pointer)
        profile='mt4_runtime' if old['service_runtime']['language']=='mql4' else 'shared_reusable' if short in ['m0033','m0034'] else 'operator_ui' if old['module_classification']['module_kind']=='UI_MODULE' else 'process_service'
        m={'schema_version':'2.0.0','document_type':'atomic_module_manifest','manifest_version':'2.0.0',
           'authority':{'status':'candidate','policy':'reviewed_module_root_authority','effective_baseline_commit':commit,'approval_authority':APPROVER},
           'module_identity':{'module_id':u['module_id'],'short_id':short,'canonical_symbol':u['canonical_symbol'],'canonical_root':root,'module_name':old['module_identity']['module_name'],
             'aliases':old['module_identity']['legacy_aliases'],'identity_status':'canonical','lifecycle_status':'active','specification_version':'2.0.0','accountable_owner':'DICKY1987'},
           'profile':profile,
           'purpose_and_boundaries':{},'process_steps':[], 'files':{'scope_status':'open','definitions':[],'shared_uses':[]},'contracts':[],
           'runtime':{},'state':{'transitions':[]},'failure_and_safety':{},'observability_quality':{},'verification_commands':{},'evidence':evidence,
           'migration':{'source_manifest_path':mp,'source_manifest_sha256':file_sha(REPO/mp),'source_commit':commit,'original_snapshot_path':snapshot.relative_to(REPO).as_posix(),
             'original_v1':old,'original_content_role':'immutable_historical_evidence_only','migration_map_ref':'governance/module_consolidation/v1_to_v2_migration_map.json'}}
        for key,source_pointer in [('purpose','/purpose'),('responsibilities','/module_scope/responsibilities'),('exclusions','/module_scope/forbidden_responsibilities'),('owned_capabilities','/module_scope/key_functions')]:
            m['purpose_and_boundaries'][key]=inherited('/purpose_and_boundaries/'+key,source_pointer,key in ['purpose','responsibilities'])
        for key in ['side_effects','trust_boundary','externally_visible_behavior']:
            m['purpose_and_boundaries'][key]=unknown('/purpose_and_boundaries/'+key,'No reviewed module-local '+key+' specification established during lossless migration.',False)
        owned=old['file_ownership']['owned_files']; declared_entries=set(old['process_binding']['entrypoint_files'])
        for index,path in enumerate(owned):
            fid='FILE-'+value_sha(path)[:20]; path_role=role(path); is_entry=path in declared_entries and path_role=='library'
            eid=ev('/files/definitions',mp,{'json_pointer':f'/file_ownership/owned_files/{index}','element_key':path},'Baseline-declared ownership; file exists at the pinned commit.',element=fid)
            m['files']['definitions'].append({'file_id':fid,'path':path,'role':'entrypoint' if is_entry else path_role,'required':None,'ownership_status':'baseline_declared','current_or_proposed_location':'current',
               'content_sha256':file_sha(REPO/path) if (REPO/path).is_file() else None,'entrypoint':is_entry,'runtime_relevance':'supporting' if path_role in ['test','schema','doc','fixture'] else 'undetermined',
               'contracts_produced':[],'contracts_consumed':[],'evidence_refs':[eid]})
        for index,use in enumerate(old['file_ownership'].get('shared_files',[])):
            path=use['path']; fid='FILE-'+value_sha(path)[:20]; ref={'file_id':fid,'path':path,'role_in_this_step':'baseline_declared_supporting_use','required':None,'knowledge':'unknown'}
            m['files']['shared_uses'].append(ref);shared[path].append({'module_id':u['module_id'],'module_short_id':short,'step_id':old['process_binding']['step_id'] if re.fullmatch(r'6\d{19}',old['process_binding']['step_id']) else None,
               'usage_role':'baseline_declared_supporting_use','required':None,'knowledge':'unknown','source_manifest':mp,'source_json_pointer':f'/file_ownership/shared_files/{index}'})
        m['files']['required_file_inventory']=unknown('/files/required_file_inventory','Baseline file inventory does not establish required status or step-local usage for all runtime assets; semantic/import review is required before closed-world enforcement.',True)
        matched=[(idx,p) for idx,p in enumerate(processes) if p['owner_module_id']==u['module_id'] or u['module_id'] in p.get('supporting_module_ids',[])]
        m['process_participation']=known({'process_registry_ref':PROCESS,'step_ids':[p['step_id'] for _,p in matched]},'/process_participation',PROCESS,'','DEC-028','Participation derived by permanent owner/supporting identity; zero is confirmed only for this authored registry.')
        for idx,p in matched:
            sid=p['step_id']; sc=p['step_code']; prefix='/process_steps/'+str(len(m['process_steps'])); step={'step_id':sid,'step_code':sc,'process_registry_ref':PROCESS,'participation_role':'primary_owner' if p['owner_module_id']==u['module_id'] else 'supporting',
                    'exclusive_files':[], 'shared_files':[], 'contract_refs':p['input_contract_ids']+p['output_contract_ids'],'state_transition_refs':[]}
            refmap={'trigger':'trigger','preconditions':'preconditions','inputs':'input_contract_ids','processing':'atomic_activities','decisions':'branches','primary_output':'output_contract_ids',
                    'secondary_outputs':'terminal_outcomes','validation':'validation_control_ids','failure_output':'failure_control_ids','completion_criteria':'terminal_outcomes'}
            for key,field in refmap.items():
                step[key]=known({'authority_ref':PROCESS,'record_id':sid,'json_pointer':'/'+field},prefix+'/'+key,PROCESS,'/'+str(idx)+'/'+field,'DEC-002','External process fact is referenced; it is not reauthored in the module.',sid)
            for key in ['retry_timeout_recovery','observability','next_handoff_refs']:
                step[key]=unknown(prefix+'/'+key,'The referenced global step does not establish reviewed module-local '+key+' details.',key in ['retry_timeout_recovery'])
            for use in m['files']['shared_uses']: step['shared_files'].append(copy.deepcopy(use))
            # Only baseline-declared owned entrypoints qualify for direct step-file mapping.
            for f in m['files']['definitions']:
                if f['entrypoint']:
                    step['exclusive_files'].append({'file_id':f['file_id'],'path':f['path'],'role_in_this_step':'baseline_declared_entrypoint','required':None,'knowledge':'unknown'})
            m['process_steps'].append(step)
        for direction,role_name in [('input_contracts','consumer'),('output_contracts','producer')]:
            for index,item in enumerate(old['contracts'][direction]):
                name=item['name']; item_id='USE-'+value_sha([short,direction,name,index])[:20]; c=by_contract.get(name)
                placeholder=name in ['needs_review','N/A','Either']
                if placeholder:
                    gap('/contracts/'+item_id,'Placeholder '+name+' is not an approved interface definition.',True)
                    continue
                cid=c['contract_id'] if c else None; cref=REGISTRIES+'/contract_registry.jsonl' if c else None; schema_path=c.get('schema_ref') if c else item.get('schema_ref')
                schema_path=schema_path if schema_path and (REPO/schema_path).is_file() else None
                use_gaps=[]
                if not c: use_gaps.append(gap('/contracts/'+item_id+'/authority_path','No exact live contract authority record for '+name+'.',True))
                elif not schema_path: use_gaps.append(gap('/contracts/'+item_id+'/schema_path','Executable schema is absent for '+name+'; use the exact registry record without inventing a path.',False,[cref]))
                eid=ev('/contracts',mp,{'json_pointer':f'/contracts/{direction}/{index}','element_key':name},'Declared module boundary contract use.',element=item_id)
                m['contracts'].append({'usage_id':item_id,'name':name,'contract_id':cid,'version':c.get('version') if c else item.get('version'),'authority_path':cref,'schema_path':schema_path,'role':role_name,
                   'step_ids':[p['step_id'] for _,p in matched if cid and cid in p['input_contract_ids']+p['output_contract_ids']],
                   'compatibility':inherited('/contracts/'+str(len(m['contracts']))+'/compatibility','/contracts/contract_version_policy'),
                   'knowledge':'confirmed' if c else 'unknown','gap_ids':use_gaps,'evidence_refs':[eid]})
        for key,sp in [('kind','runtime_kind'),('language_platform','language'),('entrypoints','startup_entrypoints'),('deployment_unit','deployment_unit'),('external_dependencies','external_systems')]:
            m['runtime'][key]=inherited('/runtime/'+key,'/service_runtime/'+sp,key=='entrypoints' and profile not in ['shared_reusable'])
        m['runtime']['ports_channels']=known({'port':old['service_runtime']['microservice_port'],'channel_ids':old['reconciliation_status']['owned_channel_ids']},'/runtime/ports_channels',source_pointer='/service_runtime')
        for key in ['configuration_sources','startup_shutdown','restart_semantics','concurrency_ordering','required_files']:
            m['runtime'][key]=unknown('/runtime/'+key,'Review runtime specification and distinguish intended behavior from commit-pinned implementation for '+key+'.',False)
        for key in ['variables','owner','persistence','ordering','idempotency','duplicate_handling','recovery']:
            m['state'][key]=unknown('/state/'+key,'No reviewed module-owned state specification for '+key+'.',False)
        for key,sp in [('validation','validation_contract'),('failure_modes','failure_contract'),('retry_policy','retry_policy'),('timeout_policy','timeout_policy'),('recovery_quarantine','quarantine_policy')]:
            target='/failure_and_safety/'+key; value=old['state_and_failure_behavior'][sp]
            if isinstance(value,dict) and value.get('rule')=='needs_review': m['failure_and_safety'][key]=unknown(target,'Mandatory '+key+' semantics are still needs_review in the v1 source.',True)
            else: m['failure_and_safety'][key]=inherited(target,'/state_and_failure_behavior/'+sp,key in ['validation','failure_modes'])
        # v1 default booleans are preserved as historical values, not silently asserted as verified safety intent.
        for key in ['rejection_outputs','fail_closed','safety_gates','risk_controls','error_codes','operator_escalation']:
            m['failure_and_safety'][key]=unknown('/failure_and_safety/'+key,'Require explicit applicability and evidence before approving '+key+'.',False)
        for key in ['logs','metrics','health_checks','slos','performance','acceptance_criteria','test_references','implementation_evidence']:
            m['observability_quality'][key]=unknown('/observability_quality/'+key,'Review source evidence for '+key+'; a blank v1 collection does not mean none.',key=='acceptance_criteria')
        for key in ['build','test','lint','typecheck','smoke_check','local_run']:
            m['verification_commands'][key]=unknown('/verification_commands/'+key,'A repository-supported module-specific command has not been demonstrated during migration.',False)
        for target,source_pointer in [('/module_identity','/module_identity'),('/profile','/module_classification'),('/authority','/source_authority')]:
            ev(target,mp,{'json_pointer':source_pointer},'Mechanical identity/profile migration; authority remains candidate until P6.','DEC-006')
        for address,value in leaves(old):
            target='/migration/original_v1'+address
            claim_id='CL-'+value_sha([mp,file_sha(REPO/mp),address])[:22]
            claim={'claim_id':claim_id,'source_id':source_index[mp]['source_id'],'source_path':mp,'source_commit':commit,'source_sha256':file_sha(REPO/mp),
                   'source_locator':{'json_pointer':address,'page':None,'line_start':None,'line_end':None,'section':address.split('/')[1] if '/' in address else None},
                   'claim_type':'v1_snapshot_preservation','target_module':short,'target_json_pointer':target,'current_authoritative_value':value,'candidate_value':value,
                   'disposition':'MIGRATE','conflict_type':None,'decision_id':'DEC-007','rationale':'Lossless historical snapshot retained in candidate; semantic confirmation is tracked independently.',
                   'evidence_strength':'direct','status':'candidate_applied','approval_actor':APPROVER,'active_authority_applied':False}
            claims.append(claim)
            migration.append({'module':short,'v1_json_pointer':address,'v2_target':target,'transformation':'identity: preserve exact JSON value as immutable historical evidence',
                              'action':'retain','reason':'No original v1 value is discarded; active normalized facts have separate evidence and knowledge status.',
                              'data_loss_check':pointer(m,target)==value,'claim_id':claim_id})
        m['reconciliation']={'status':'blocked','schema_valid':False,'specification_ready':False,'implementation_verified':False,'implementation_conformance':'unverified',
             'unresolved_gap_ids':module_gaps,'conflict_ids':[],'last_verified_commit':commit,'stale_after':'Any source or baseline hash change requires reconciliation; supporting sources cannot auto-overwrite authorities.'}
        for item in evidence:
            value = pointer(m, item['target_json_pointer'])
            if isinstance(value, list) and item['target_element_id']:
                value = next(v for v in value if item['target_element_id'] in [v.get('file_id'), v.get('usage_id'), v.get('step_id')])
            item['approved_value_sha256'] = value_sha(value)
        import jsonschema
        m['reconciliation']['schema_valid'] = not list(jsonschema.Draft202012Validator(schema()).iter_errors(m))
        write(CONTROL/'staging'/short/'manifest.v2.candidate.json',m);candidates.append(m)
    # Global shared topology is a candidate until local step-use semantics are reconciled.
    owners={f['path']:m['module_identity']['short_id'] for m in candidates for f in m['files']['definitions']}
    shared_registry={'schema_version':'1.0.0','authority_status':'candidate','authority_scope':'global shared-file consumer topology','effective_baseline':commit,'records':[]}
    for path,consumers in sorted(shared.items()):
        owner=owners.get(path)
        shared_registry['records'].append({'file_id':'FILE-'+value_sha(path)[:20],'path':path,'content_sha256':file_sha(REPO/path),
            'file_role':role(path),'ownership_class':'module_owned_shared_use' if owner else 'global_shared','steward':owner or 'EAFIX Governance',
            'status':'candidate','consumers':consumers,'provenance':[{'path':c['source_manifest'],'json_pointer':c['source_json_pointer'],'decision_id':'DEC-004'} for c in consumers]})
    write(CONTROL/'staging/shared_file_registry.candidate.json',shared_registry)
    write(CONTROL/'v1_to_v2_migration_map.json',{'schema_version':'1.0.0','baseline_commit':commit,'source_schema':REGISTRIES+'/eafix_unified_atomic_module_schema_v1_0_0.json',
          'target_schema':SCHEMA,'mapping_policy':'Every concrete v1 leaf retained losslessly in a non-authoritative historical snapshot; normalized v2 fields are separately reconciled.',
          'field_count':len(migration),'all_data_loss_checks_pass':all(x['data_loss_check'] for x in migration),'mappings':migration})
    write_jsonl(CONTROL/'run/claim_ledger.jsonl',claims)
    write_jsonl(CONTROL/'run/blocker_resolution_queue.jsonl',gaps)
    for s in sources:
        cs=[c for c in claims if c['source_id']==s['source_id']]
        if cs:
            s.update({'extraction_status':'complete','reconciliation_status':'in_progress','source_status':'candidate_claims_applied','relevant_claim_count':len(cs),
                      'accepted_claim_count':len(cs),'fully_scraped':False,'retention_reason':'Preserved in v2 candidate; not active-authority-applied and not fully semantically adjudicated.'})
    write_jsonl(CONTROL/'run/source_processing_ledger.jsonl',sources)
    print({'candidates':len(candidates),'lossless_v1_fields':len(migration),'mandatory_gaps':sum(g['severity']=='blocking' for g in gaps),'other_gaps':sum(g['severity']=='nonblocking' for g in gaps),'shared_records':len(shared_registry['records'])})
    return 0


if __name__=='__main__':
    raise SystemExit(main())
