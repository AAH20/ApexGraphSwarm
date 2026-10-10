"""The local JSON boundary never accepts executable commands or unbounded data."""
import json
import subprocess
import sys
import unittest
from apexgraphswarm.lab import dispatch


class OptimizationLabTests(unittest.TestCase):
    def test_only_known_actions_and_fixed_benchmark(self):
        for payload in ({"action": "shell", "command": "echo no"}, {"action": "benchmark", "path": "/tmp/arbitrary.py"}, []):
            with self.assertRaises(ValueError):
                dispatch(payload)

    def test_cli_rejects_nonfinite_and_oversized_input(self):
        for raw in ('{"action":"capacity","target_utilization":NaN}', 'x' * 131073):
            result = subprocess.run([sys.executable, "-m", "apexgraphswarm.lab"], input=raw, text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertIn("error", json.loads(result.stdout))
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_returns_inspectable_local_plan(self):
        result = subprocess.run([sys.executable, "-m", "apexgraphswarm.lab"], input=json.dumps({"action": "waves", "tasks": [{"id": "one", "writes": ["shared.py"]}, {"id": "two", "writes": ["shared.py"]}]}), text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report["waves"]), 2)
        self.assertEqual(report["conflicts"][0]["files"], ["shared.py"])
