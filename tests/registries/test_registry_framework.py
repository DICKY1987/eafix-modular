import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools/registries"))
import registry_core as rc
import build_registries as cli
class RegistryFrameworkTests(unittest.TestCase):
 def test_canonical_json_is_stable(self):
  self.assertEqual(rc.canonical_json({"b":1,"a":2}),rc.canonical_json({"a":2,"b":1}))
 def test_current_records_have_unique_ids(self):
  _,records=rc.load_all(); self.assertEqual([],rc.validate_ids(records))
 def test_current_cross_references_resolve(self):
  _,records=rc.load_all(); self.assertEqual([],rc.validate_refs(records))
 def test_cli_forwards_check_and_report_only_flags(self):
  with mock.patch.object(sys,'argv',['build_registries.py','--check','--report-only']), mock.patch.object(cli,'run',return_value=0) as run:
   cli.main()
  run.assert_called_once_with(check=True,report_only=True)
 def test_cli_defaults_to_no_flags(self):
  with mock.patch.object(sys,'argv',['build_registries.py']), mock.patch.object(cli,'run',return_value=0) as run:
   cli.main()
  run.assert_called_once_with(check=False,report_only=False)
 def test_check_mode_does_not_write_snapshots(self):
  idx,records=rc.load_all()
  before={p:p.read_bytes() for p in (rc.GEN_ROOT).glob('*')}
  changed,_=rc.build_snapshots(idx,records,check=True)
  after={p:p.read_bytes() for p in (rc.GEN_ROOT).glob('*')}
  self.assertEqual([],changed); self.assertEqual(before,after)
 def test_current_dataset_has_no_authority_or_global_id_errors(self):
  _,records=rc.load_all()
  self.assertEqual([],rc.validate_authority(records)); self.assertEqual([],rc.validate_ids(records))
 def test_validate_ids_detects_cross_registry_duplicate(self):
  records={'a':[{'record_id':'DUP'}],'b':[{'record_id':'DUP'}]}
  errors=rc.validate_ids(records)
  self.assertTrue(any('DUP' in e and 'multiple registries' in e for e in errors))
 def test_validate_ids_allows_unique_ids_across_registries(self):
  records={'a':[{'record_id':'A1'}],'b':[{'record_id':'B1'}]}
  self.assertEqual([],rc.validate_ids(records))
 def test_validate_authority_flags_disallowed_status_for_authority(self):
  records={'reg':[{'record_id':'R1','status':'draft','authority_status':'canonical','supersedes':[],'superseded_by':[]}]}
  errors=rc.validate_authority(records)
  self.assertTrue(any('does not permit status draft' in e for e in errors))
 def test_validate_authority_allows_matrix_permitted_combo(self):
  records={'reg':[{'record_id':'R1','status':'partial','authority_status':'needs_review','supersedes':[],'superseded_by':[]}]}
  self.assertEqual([],rc.validate_authority(records))
 def test_validate_authority_detects_missing_supersede_target(self):
  records={'reg':[{'record_id':'R1','status':'active','authority_status':'legacy_source','supersedes':['R-MISSING'],'superseded_by':[]}]}
  errors=rc.validate_authority(records)
  self.assertTrue(any('supersedes unknown record_id R-MISSING' in e for e in errors))
 def test_validate_authority_detects_asymmetric_supersede_link(self):
  records={'reg':[
    {'record_id':'R1','status':'active','authority_status':'legacy_source','supersedes':['R2'],'superseded_by':[]},
    {'record_id':'R2','status':'superseded','authority_status':'legacy_source','supersedes':[],'superseded_by':[]},
  ]}
  errors=rc.validate_authority(records)
  self.assertTrue(any('supersedes R2 but R2 does not list it in superseded_by' in e for e in errors))
  records['reg'][1]['superseded_by']=['R1']
  self.assertEqual([],rc.validate_authority(records))
 def test_read_jsonl_raises_on_malformed_line(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.jsonl'; p.write_text('{"a":1}\nnot-json\n',encoding='utf-8')
   with self.assertRaises(ValueError) as ctx: rc.read_jsonl(p)
  self.assertIn('bad.jsonl:2',str(ctx.exception))
 def test_conflict_report_includes_severity_and_resolution_fields(self):
  idx={'registries':[{'name':'module','owner':'Team A'},{'name':'contract','owner':'Team B'}]}
  all_records={'module':[{'record_id':'MOD-1','status':'conflicted','authority_status':'needs_review','source_refs':[],'owner_module_id':None,'process_step_ids':[],'module_id':'MOD-1'}],'contract':[]}
  out=rc.reports(idx,all_records,[])
  conflict=out['registry_conflict_report.json']['conflicts'][0]
  self.assertEqual(conflict['severity'],'high')
  self.assertEqual(sorted(conflict['reasons']),['authority_needs_review','status_conflicted'])
  self.assertEqual(conflict['registry_owner'],'Team A')
  self.assertEqual(conflict['resolution_state'],'unresolved')
if __name__=="__main__": unittest.main()
