import tempfile
import unittest
from pathlib import Path
from apexgraphswarm.preview import operate


class PreviewTests(unittest.TestCase):
    def test_fixture_persists_and_completes_without_model_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = {'dbPath': str(Path(tmp) / 'state.sqlite')}
            state = operate({**base, 'action': 'createFixture', 'agents': 30, 'idempotencyKey': 'fixture-test-01'})
            run_id = state['run']['id']
            self.assertEqual(len(state['agents']), 30)
            repeated = operate({**base, 'action': 'createFixture', 'agents': 30, 'idempotencyKey': 'fixture-test-01'})
            self.assertEqual(repeated['run']['id'], run_id)
            for _ in range(4):
                state = operate({**base, 'action': 'advanceFixture', 'runId': run_id})
                if state['run']['status'] in {'completed', 'succeeded'}:
                    break
            self.assertIn(state['run']['status'], {'completed', 'succeeded'})
            persisted = operate({**base, 'action': 'status', 'runId': run_id})
            self.assertEqual(persisted['run']['spentMicrousd'], 0)
            self.assertTrue(all(task['result']['modelCalls'] == 0 for task in persisted['tasks']))

    def test_fixture_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                operate({'dbPath': str(Path(tmp) / 'state.sqlite'), 'action': 'createFixture', 'agents': 301, 'idempotencyKey': 'rejected-count'})
