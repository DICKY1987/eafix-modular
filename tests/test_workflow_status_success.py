from __future__ import annotations

import io
import sys
import types
import unittest
from contextlib import redirect_stdout


class _DummyOrchestrator:
    def print_status_table(self) -> None:
        # Simulate printing a status table
        print("[dummy] status table")


class _DummyRoadmap:
    def print_status(self) -> None:
        # Simulate printing a roadmap
        print("[dummy] roadmap")


class TestWorkflowStatusSuccess(unittest.TestCase):
    def setUp(self) -> None:
        # Inject dummy workflow modules so workflow-status path succeeds
        orch_mod = types.ModuleType("workflows.orchestrator")
        setattr(orch_mod, "WorkflowOrchestrator", _DummyOrchestrator)
        roadmap_mod = types.ModuleType("workflows.execution_roadmap")
        setattr(roadmap_mod, "ExecutionRoadmap", _DummyRoadmap)
        self._old_orch = sys.modules.get("workflows.orchestrator")
        self._old_roadmap = sys.modules.get("workflows.execution_roadmap")
        sys.modules["workflows.orchestrator"] = orch_mod
        sys.modules["workflows.execution_roadmap"] = roadmap_mod

    def tearDown(self) -> None:
        # Restore prior modules if they existed
        if self._old_orch is None:
            sys.modules.pop("workflows.orchestrator", None)
        else:
            sys.modules["workflows.orchestrator"] = self._old_orch
        if self._old_roadmap is None:
            sys.modules.pop("workflows.execution_roadmap", None)
        else:
            sys.modules["workflows.execution_roadmap"] = self._old_roadmap

    def test_workflow_status_success(self) -> None:
        # Import here to ensure our module shims are in place
        from cli_multi_rapid.cli import main  # type: ignore

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["workflow-status"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Enhanced Workflow Status", out)
        self.assertIn("Implementation Roadmap", out)
        self.assertIn("[dummy] status table", out)
        self.assertIn("[dummy] roadmap", out)


if __name__ == "__main__":
    unittest.main()

