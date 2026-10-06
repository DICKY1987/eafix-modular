import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/registries"))
import build_authority_graph as ag


class AuthorityGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = ag.build()
        cls.graph = cls.outputs[f"{ag.OUTPUT}/authority_graph.current.json"]

    def test_all_modules_have_generated_context_and_boundary_view(self):
        self.assertEqual(34, len(self.graph["modules"]))
        self.assertEqual([], ag.validate_graph(self.graph))
        for module in self.graph["modules"]:
            mid = module["module_id"]
            self.assertIn(f"{ag.OUTPUT}/modules/{mid}.json", self.outputs)
            diagram = self.outputs[f"{ag.OUTPUT}/diagrams/{mid}.md"]
            self.assertIn("```mermaid", diagram)
            self.assertIn("Declared consumers:", diagram)

    def test_foreign_service_entrypoint_is_not_promoted(self):
        s17 = next(s for s in self.graph["steps"] if s["number"] == 17)
        self.assertEqual([], s17["entrypoint_files"])
        self.assertTrue(any(f["kind"] == "unverified_entrypoint" and
                            f["module_id"] == s17["owner_module_id"] for f in self.graph["findings"]))

    def test_duplicate_file_ownership_fails(self):
        graph = copy.deepcopy(self.graph)
        graph["files"].append(copy.deepcopy(graph["files"][0]))
        self.assertIn("File paths must be unique", ag.validate_graph(graph))

    def test_schema_cannot_execute_a_process_step(self):
        graph = copy.deepcopy(self.graph)
        file = next(f for f in graph["files"] if f["step_refs"])
        file["role"] = "schema"
        self.assertTrue(any("Non-entrypoint" in e for e in ag.validate_graph(graph)))

    def test_cross_module_executor_fails(self):
        graph = copy.deepcopy(self.graph)
        step = next(s for s in graph["steps"] if s["entrypoint_files"])
        step["owner_module_id"] = graph["modules"][-1]["module_id"]
        self.assertTrue(any("Invalid step entrypoint" in e for e in ag.validate_graph(graph)))

    def test_contract_outside_manifest_boundary_fails(self):
        graph = copy.deepcopy(self.graph)
        graph["steps"][0]["output_contract_names"].append("ImaginaryContract")
        self.assertTrue(any("outputs outside module boundary" in e for e in ag.validate_graph(graph)))

    def test_backlinks_are_enforced(self):
        graph = copy.deepcopy(self.graph)
        file = next(f for f in graph["files"] if f["step_refs"])
        file["step_refs"] = []
        self.assertTrue(any("Missing reverse file link" in e for e in ag.validate_graph(graph)))

    def test_regeneration_is_byte_deterministic(self):
        self.assertEqual(self.outputs, ag.build())

    def test_candidate_contracts_remain_candidates(self):
        _, records = ag.rc.load_all()
        before = {c["contract_id"]: c["authority_status"] for c in records["contract"]}
        for contract in self.graph["contracts"]:
            self.assertEqual(before[contract["contract_id"]], contract["authority_status"])

    def test_path_traversal_and_windows_paths_are_rejected(self):
        for path in ("../secret", "/tmp/secret", "C:/secret", "dir\\secret"):
            with self.assertRaises(ValueError):
                ag.safe_path(ag.ROOT, path)

    def test_check_detects_tampering_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = f"{ag.OUTPUT}/example.json"
            with mock.patch.object(ag, "build", return_value={path: {"valid": True}}):
                self.assertEqual(0, ag.run(root=root))
                self.assertEqual(0, ag.run(check=True, root=root))
                destination = root / path
                destination.write_text("tampered\n")
                self.assertEqual(1, ag.run(check=True, root=root))
                self.assertEqual("tampered\n", destination.read_text())

    def test_unexpected_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / ag.OUTPUT / "untracked.json"
            destination.parent.mkdir(parents=True)
            destination.write_text("{}")
            with mock.patch.object(ag, "build", return_value={}):
                with self.assertRaisesRegex(ValueError, "Unexpected generated files"):
                    ag.run(check=True, root=root)


if __name__ == "__main__":
    unittest.main()
