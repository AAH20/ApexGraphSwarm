import test from 'node:test';
import assert from 'node:assert/strict';
import {POST} from '../../app/api/planned-tasks/route';

const TOKEN = 'planned-tasks-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/planned-tasks', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

test('planned-tasks POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/planned-tasks', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ runId: 'test-run', taskId: 'test-task' }),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('planned-tasks POST rejects wrong token', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('planned-tasks POST rejects unsafe origin', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('planned-tasks POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('planned-tasks POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/planned-tasks', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '',
  });
  const res = await POST(req);
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/planned-tasks', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '{invalid',
  });
  const res = await POST(req);
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects missing runId', async () => {
  const res = await POST(makeReq({ taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects missing taskId', async () => {
  const res = await POST(makeReq({ runId: 'test-run' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects empty runId', async () => {
  const res = await POST(makeReq({ runId: '', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects empty taskId', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with special chars', async () => {
  const res = await POST(makeReq({ runId: 'test-run!', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with special chars', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task!' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with spaces', async () => {
  const res = await POST(makeReq({ runId: 'test run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with spaces', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId too long', async () => {
  const res = await POST(makeReq({ runId: 'a'.repeat(129), taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId too long', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'a'.repeat(129) }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId as number', async () => {
  const res = await POST(makeReq({ runId: 123, taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId as number', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 123 }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId as boolean', async () => {
  const res = await POST(makeReq({ runId: true, taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId as boolean', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: true }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId as null', async () => {
  const res = await POST(makeReq({ runId: null, taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId as null', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: null }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId as array', async () => {
  const res = await POST(makeReq({ runId: ['test-run'], taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId as array', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: ['test-task'] }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId as object', async () => {
  const res = await POST(makeReq({ runId: { id: 'test-run' }, taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId as object', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: { id: 'test-task' } }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects extra fields', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task', extra: 'field' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with unicode', async () => {
  const res = await POST(makeReq({ runId: 'test-run\u00e9', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with unicode', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\u00e9' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with emoji', async () => {
  const res = await POST(makeReq({ runId: 'test-run\ud83d\ude00', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with emoji', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\ud83d\ude00' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with null byte', async () => {
  const res = await POST(makeReq({ runId: 'test-run\u0000', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with null byte', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\u0000' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with control char', async () => {
  const res = await POST(makeReq({ runId: 'test-run\u0001', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with control char', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\u0001' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with tab', async () => {
  const res = await POST(makeReq({ runId: 'test-run\t', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with tab', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\t' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with newline', async () => {
  const res = await POST(makeReq({ runId: 'test-run\n', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with newline', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\n' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with carriage return', async () => {
  const res = await POST(makeReq({ runId: 'test-run\r', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with carriage return', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\r' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with form feed', async () => {
  const res = await POST(makeReq({ runId: 'test-run\f', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with form feed', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\f' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with vertical tab', async () => {
  const res = await POST(makeReq({ runId: 'test-run\v', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with vertical tab', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\v' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with backspace', async () => {
  const res = await POST(makeReq({ runId: 'test-run\b', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with backspace', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\b' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with escape', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with escape', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with delete', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with delete', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with unit separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with unit separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with record separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with record separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with group separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with group separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with file separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run ', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with file separator', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task ' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects oversized body', async () => {
  const big = 'x'.repeat(1025);
  const res = await POST(makeReq({ runId: big, taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId at max length', async () => {
  const res = await POST(makeReq({ runId: 'a'.repeat(128), taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId at max length', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'a'.repeat(128) }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with only special chars', async () => {
  const res = await POST(makeReq({ runId: '!@#$%', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with only special chars', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '!@#$%' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with only numbers', async () => {
  const res = await POST(makeReq({ runId: '12345', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with only numbers', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '12345' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with only letters', async () => {
  const res = await POST(makeReq({ runId: 'abcde', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with only letters', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'abcde' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with only underscores', async () => {
  const res = await POST(makeReq({ runId: '_____', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with only underscores', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '_____' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with only hyphens', async () => {
  const res = await POST(makeReq({ runId: '-----', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with only hyphens', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '-----' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid', async () => {
  const res = await POST(makeReq({ runId: 'test-run!', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task!' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with leading space', async () => {
  const res = await POST(makeReq({ runId: ' test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with leading space', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: ' test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with trailing space', async () => {
  const res = await POST(makeReq({ runId: 'test-run ', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with trailing space', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task ' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with leading hyphen', async () => {
  const res = await POST(makeReq({ runId: '-test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with leading hyphen', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '-test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with trailing hyphen', async () => {
  const res = await POST(makeReq({ runId: 'test-run-', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with trailing hyphen', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task-' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with leading underscore', async () => {
  const res = await POST(makeReq({ runId: '_test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with leading underscore', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '_test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with trailing underscore', async () => {
  const res = await POST(makeReq({ runId: 'test-run_', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with trailing underscore', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task_' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with double hyphen', async () => {
  const res = await POST(makeReq({ runId: 'test--run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with double hyphen', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test--task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with double underscore', async () => {
  const res = await POST(makeReq({ runId: 'test__run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with double underscore', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test__task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed case', async () => {
  const res = await POST(makeReq({ runId: 'Test-Run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed case', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'Test-Task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with uppercase', async () => {
  const res = await POST(makeReq({ runId: 'TEST-RUN', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with uppercase', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'TEST-TASK' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with lowercase', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with lowercase', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with numeric start', async () => {
  const res = await POST(makeReq({ runId: '123-test-run', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with numeric start', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '123-test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with numeric end', async () => {
  const res = await POST(makeReq({ runId: 'test-run-123', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with numeric end', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task-123' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with all numeric', async () => {
  const res = await POST(makeReq({ runId: '12345678', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with all numeric', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '12345678' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with all alpha', async () => {
  const res = await POST(makeReq({ runId: 'abcdefghij', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with all alpha', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'abcdefghij' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with all special', async () => {
  const res = await POST(makeReq({ runId: '!@#$%^&*()', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with all special', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: '!@#$%^&*()' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 2', async () => {
  const res = await POST(makeReq({ runId: 'test-run@', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 2', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task@' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 3', async () => {
  const res = await POST(makeReq({ runId: 'test-run#', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 3', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task#' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 4', async () => {
  const res = await POST(makeReq({ runId: 'test-run$', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 4', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task$' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 5', async () => {
  const res = await POST(makeReq({ runId: 'test-run%', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 5', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task%' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 6', async () => {
  const res = await POST(makeReq({ runId: 'test-run^', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 6', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task^' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 7', async () => {
  const res = await POST(makeReq({ runId: 'test-run&', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 7', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task&' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 8', async () => {
  const res = await POST(makeReq({ runId: 'test-run*', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 8', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task*' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 9', async () => {
  const res = await POST(makeReq({ runId: 'test-run(', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 9', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task(' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 10', async () => {
  const res = await POST(makeReq({ runId: 'test-run)', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 10', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task)' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 11', async () => {
  const res = await POST(makeReq({ runId: 'test-run+', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 11', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task+' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 12', async () => {
  const res = await POST(makeReq({ runId: 'test-run=', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 12', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task=' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 13', async () => {
  const res = await POST(makeReq({ runId: 'test-run[', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 13', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task[' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 14', async () => {
  const res = await POST(makeReq({ runId: 'test-run]', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 14', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task]' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 15', async () => {
  const res = await POST(makeReq({ runId: 'test-run{', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 15', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task{' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 16', async () => {
  const res = await POST(makeReq({ runId: 'test-run}', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 16', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task}' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 17', async () => {
  const res = await POST(makeReq({ runId: 'test-run|', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 17', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task|' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 18', async () => {
  const res = await POST(makeReq({ runId: 'test-run\\', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 18', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task\\' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 19', async () => {
  const res = await POST(makeReq({ runId: 'test-run/', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 19', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task/' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 20', async () => {
  const res = await POST(makeReq({ runId: 'test-run?', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 20', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task?' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 21', async () => {
  const res = await POST(makeReq({ runId: 'test-run<', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 21', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task<' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 22', async () => {
  const res = await POST(makeReq({ runId: 'test-run>', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 22', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task>' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 23', async () => {
  const res = await POST(makeReq({ runId: 'test-run,', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 23', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task,' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 24', async () => {
  const res = await POST(makeReq({ runId: 'test-run.', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 24', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task.' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 25', async () => {
  const res = await POST(makeReq({ runId: 'test-run:', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 25', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task:' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 26', async () => {
  const res = await POST(makeReq({ runId: 'test-run;', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 26', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task;' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 27', async () => {
  const res = await POST(makeReq({ runId: 'test-run"', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 27', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task"' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 28', async () => {
  const res = await POST(makeReq({ runId: "test-run'", taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 28', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: "test-task'" }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 29', async () => {
  const res = await POST(makeReq({ runId: 'test-run`', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 29', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task`' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 30', async () => {
  const res = await POST(makeReq({ runId: 'test-run~', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 30', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task~' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 31', async () => {
  const res = await POST(makeReq({ runId: 'test-run^', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 31', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task^' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects runId with mixed valid invalid 32', async () => {
  const res = await POST(makeReq({ runId: 'test-run!', taskId: 'test-task' }));
  assert.equal(res.status, 400);
});

test('planned-tasks POST rejects taskId with mixed valid invalid 32', async () => {
  const res = await POST(makeReq({ runId: 'test-run', taskId: 'test-task!' }));
  assert.equal(res.status, 400);
});
