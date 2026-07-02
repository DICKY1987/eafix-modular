from __future__ import annotations

import json
import os
import unittest


class TestScenarios(unittest.TestCase):
    def test_sample_scenario_loads(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "P_tests", "fixtures", "sample_scenario.json")
        path = os.path.abspath(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("symbol", data)
        self.assertIsInstance(data.get("events", []), list)


if __name__ == "__main__":
    unittest.main()

