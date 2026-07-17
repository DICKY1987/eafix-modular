import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools/registries"))
import registry_core as rc
class RegistryFrameworkTests(unittest.TestCase):
 def test_canonical_json_is_stable(self):
  self.assertEqual(rc.canonical_json({"b":1,"a":2}),rc.canonical_json({"a":2,"b":1}))
 def test_current_records_have_unique_ids(self):
  _,records=rc.load_all(); self.assertEqual([],rc.validate_ids(records))
 def test_current_cross_references_resolve(self):
  _,records=rc.load_all(); self.assertEqual([],rc.validate_refs(records))
if __name__=="__main__": unittest.main()
