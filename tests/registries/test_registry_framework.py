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
if __name__=="__main__": unittest.main()
