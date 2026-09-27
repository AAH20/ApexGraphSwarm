import json
import tempfile
import unittest
from pathlib import Path
from apexgraphswarm.repository_graph import build_repository_graph


class RepositoryPrivacyTests(unittest.TestCase):
    def test_private_environment_and_generated_trees_are_not_indexed_without_git(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'main.py').write_text('def public_function():\n    return 1\n')
            (root / '.env.local').write_text('PRIVATE_TOKEN=fixture-sensitive-value\n')
            (root / '.env.example').write_text('PRIVATE_TOKEN=\n')
            for name in ['.next', '.runtime', '.integration-sources']:
                (root / name).mkdir()
                (root / name / 'private.py').write_text('def should_not_be_indexed(): pass\n')
            graph = build_repository_graph(root)
            paths = {node.get('path') for node in graph['nodes']}
            self.assertIn('main.py', paths)
            self.assertNotIn('.env.local', paths)
            rendered = json.dumps(graph)
            self.assertNotIn('fixture-sensitive-value', rendered)
            self.assertNotIn('should_not_be_indexed', rendered)
