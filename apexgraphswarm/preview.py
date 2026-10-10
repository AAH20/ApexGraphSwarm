"""Bounded local fixture operations for the engineering UI; never calls a model."""
import hashlib
import json
import sys
from .control import ControlStore


def operate(command):
    with ControlStore(command['dbPath'], max_active=4) as store:
        return _operate(command, store)


def _operate(command, store):
    action = command['action']
    if action == 'createFixture':
        count = command.get('agents', 10)
        if type(count) is not int or count not in (1, 10, 30, 100, 300):
            raise ValueError('Choose 1, 10, 30, 100 or 300 logical agents.')
        plan = {'version': 1, 'agents': [{'id': f'agent-{i}', 'name': f'Fixture agent {i+1}'} for i in range(count)], 'tasks': [
            {'id': f'task-{i}', 'agentId': f'agent-{i}', 'dependencies': [f'task-{i-10}'] if i >= 10 else [],
             'executionClass': 'fixture', 'payload': {'kind': 'deterministic-fixture', 'index': i, 'seed': 42}, 'reservedCostMicrousd': 0, 'maxAttempts': 2}
            for i in range(count)]}
        result = store.create_run(plan, idempotency_key=command['idempotencyKey'], budget_microusd=0)
        run_id = result.get('runId') or result.get('id') or result.get('run', {}).get('id') if isinstance(result, dict) else result
        return store.status(run_id)
    run_id = command['runId']
    if action == 'status':
        return store.status(run_id)
    if action == 'cancel':
        store.cancel(run_id)
        return store.status(run_id)
    if action == 'advanceFixture':
        existing = store.status(run_id)
        # Imported or model-backed plans are not executable through this preview.
        # Result payloads are checked again after each fenced claim below.
        if any(not str(agent['id']).startswith('agent-') for agent in existing['agents']):
            raise ValueError('Only generated fixture plans can use this executor.')
        store.recover_expired()
        for _ in range(10):
            claims = []
            for worker in range(4):
                claim = store.claim(run_id, f'preview-worker-{worker}', lease_seconds=30)
                if claim:
                    claims.append(claim)
            if not claims:
                break
            for claim in claims:
                payload = claim.get('payload', {})
                if payload.get('kind') != 'deterministic-fixture':
                    store.fail(claim['taskId'], claim['leaseToken'], 'Preview refuses non-fixture work.', retryable=False, actual_cost_microusd=0)
                    continue
                digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                store.complete(claim['taskId'], claim['leaseToken'], {'kind': 'fixture-result', 'sha256': digest, 'modelCalls': 0}, 0)
        return store.status(run_id)
    raise ValueError('Unsupported preview operation.')


def main():
    try:
        command = json.loads(sys.stdin.read(65537))
        print(json.dumps(operate(command), separators=(',', ':')))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
