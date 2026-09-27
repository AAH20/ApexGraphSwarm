import assert from 'node:assert/strict';
import test from 'node:test';
import {
  createStarterDesign,
  previewSpecialistAccess,
  validateSpecialistDesign,
  type AccessPreviewRequest,
  type SpecialistDesign,
} from '../lib/specialist-design';

function copyStarter(): SpecialistDesign {
  return JSON.parse(JSON.stringify(createStarterDesign())) as SpecialistDesign;
}

function grantStarterRead(design: SpecialistDesign): AccessPreviewRequest {
  const agent = design.agents[0]!;
  agent.policy.actions = ['read'];
  agent.policy.resourceIds = ['workspace-main'];
  agent.policy.audience = 'apexgraphswarm';
  agent.policy.purpose = 'review';
  return { agentId: agent.id, nodeId: 'workspace-main', action: 'read', audience: 'apexgraphswarm', purpose: 'review', elapsedSeconds: 0, approverIds: [] };
}

test('starter design is valid and grants no actions or resources', () => {
  const design = createStarterDesign();
  const result = validateSpecialistDesign(design);
  assert.equal(result.valid, true);
  assert.deepEqual(design.agents.map(agent => agent.role), [
    'Break a goal into bounded tasks.',
    'Collect cited evidence for a task.',
    'Check outputs against explicit criteria.',
  ]);
  assert.ok(design.agents.every(agent => agent.policy.actions.length === 0 && agent.policy.resourceIds.length === 0));
  const request = { agentId: 'agent-planner', nodeId: 'workspace-main', action: 'read', audience: 'apexgraphswarm', purpose: 'unassigned', elapsedSeconds: 0, approverIds: ['owner:alice'] };
  assert.equal(previewSpecialistAccess(design, request).decision, 'denied');
});

test('preview distinguishes approval-required from eligible review but never enables execution', () => {
  const design = copyStarter();
  const request = grantStarterRead(design);
  let preview = previewSpecialistAccess(design, request);
  assert.equal(preview.decision, 'approval-required');
  assert.equal(preview.executionAllowed, false);
  request.approverIds = ['owner:alice'];
  preview = previewSpecialistAccess(design, request);
  assert.equal(preview.decision, 'eligible-for-review');
  assert.equal(preview.executionAllowed, false);
  assert.ok(preview.reasons.some(reason => reason.includes('not verified')));
});

test('scope assignment and resource grants are exact; parent scope is not inherited', () => {
  const design = copyStarter();
  const request = grantStarterRead(design);
  design.nodes.push({ id: 'repo-one', label: 'Repository', kind: 'repository', parentId: 'workspace-main', teamIds: [], externalRef: 'graph:repo-one' });
  design.agents[0]!.policy.resourceIds = ['repo-one'];
  request.nodeId = 'repo-one';
  assert.equal(validateSpecialistDesign(design).valid, true);
  assert.match(previewSpecialistAccess(design, request).reasons.join(' '), /not explicitly assigned/);
  design.nodes[1]!.teamIds = ['team-core'];
  assert.equal(previewSpecialistAccess(design, request).decision, 'approval-required');
});

test('dangling references, duplicate IDs and invalid hierarchy cycles fail closed', () => {
  const dangling = copyStarter();
  dangling.teams[0]!.agentIds.push('missing-agent');
  assert.equal(validateSpecialistDesign(dangling).valid, false);
  const duplicate = copyStarter();
  duplicate.nodes[0]!.id = duplicate.agents[0]!.id;
  assert.ok(validateSpecialistDesign(duplicate).errors.some(error => error.includes('unique IDs')));
  const cycle = copyStarter();
  cycle.nodes.push({ id: 'repo-one', label: 'Repository', kind: 'repository', parentId: 'workspace-main', teamIds: [], externalRef: 'repo:one' });
  cycle.nodes[0]!.parentId = 'repo-one';
  assert.ok(validateSpecialistDesign(cycle).errors.some(error => error.includes('cycle')));
});

test('wildcard actions/scopes, unpinned skills, wildcard tools and credential-bearing URLs are rejected', () => {
  const wildcard = copyStarter();
  wildcard.agents[0]!.policy.actions = ['*'];
  wildcard.agents[0]!.policy.resourceIds = ['*'];
  assert.equal(validateSpecialistDesign(wildcard).valid, false);
  const skill = copyStarter();
  skill.agents[0]!.skills.push({ id: 'skill:review', sourceUrl: 'https://example.test/skill?api_key=secret', revision: 'main', sha256: 'a'.repeat(64) });
  assert.equal(validateSpecialistDesign(skill).valid, false);
  const fragmentSkill = copyStarter();
  fragmentSkill.agents[0]!.skills.push({ id: 'skill:fragment', sourceUrl: 'https://example.test/skill#access_token=secret', revision: 'v1', sha256: 'b'.repeat(64) });
  assert.equal(validateSpecialistDesign(fragmentSkill).valid, false);
  const unhashed = copyStarter();
  unhashed.agents[0]!.skills.push({ id: 'skill:review', sourceUrl: 'https://example.test/skill', revision: '', sha256: '' });
  assert.equal(validateSpecialistDesign(unhashed).valid, false);
  const tool = copyStarter();
  tool.agents[0]!.tools.push({ serverId: 'server:mcp', toolName: '*', gatewayId: 'gateway:local' });
  assert.equal(validateSpecialistDesign(tool).valid, false);
});

test('privileged actions always deny, and TTL or quorum failures do not become approvals', () => {
  const design = copyStarter();
  const request = grantStarterRead(design);
  request.action = 'device.actuate';
  assert.match(previewSpecialistAccess(design, request).reasons.join(' '), /Privileged/);
  request.action = 'read';
  request.elapsedSeconds = design.agents[0]!.policy.ttlSeconds;
  assert.match(previewSpecialistAccess(design, request).reasons.join(' '), /expired/);
  request.elapsedSeconds = 0;
  request.approverIds = ['owner:alice', 'owner:alice'];
  assert.match(previewSpecialistAccess(design, request).reasons.join(' '), /duplicates/);
  request.approverIds = [];
  design.agents[0]!.policy.approvalQuorum = 9;
  assert.equal(validateSpecialistDesign(design).valid, false);
});

test('required text is nonblank and URL-shaped external references reject queries/fragments', () => {
  const blank = copyStarter();
  blank.name = '   \t';
  assert.equal(validateSpecialistDesign(blank).valid, false);
  const fragment = copyStarter();
  fragment.nodes[0]!.externalRef = 'https://graph.example/workspace#access_token=secret';
  assert.equal(validateSpecialistDesign(fragment).valid, false);
  const query = copyStarter();
  query.nodes[0]!.externalRef = 'https://graph.example/workspace?token=secret';
  assert.equal(validateSpecialistDesign(query).valid, false);
});

test('limits and unknown fields are enforced', () => {
  const unknown = { ...copyStarter(), providerCredential: 'do-not-accept' };
  assert.equal(validateSpecialistDesign(unknown).valid, false);
  const tooMany = copyStarter();
  tooMany.agents[0]!.tools = Array.from({ length: 33 }, (_, i) => ({ serverId: `s${i}`, toolName: 'read', gatewayId: 'g1' }));
  assert.ok(validateSpecialistDesign(tooMany).errors.some(error => error.includes('at most 32')));
  const longExternalRef = copyStarter();
  longExternalRef.nodes[0]!.externalRef = 'x'.repeat(2049);
  assert.equal(validateSpecialistDesign(longExternalRef).valid, false);
});

test('hostile prototypes and accessor-bearing objects are rejected without invoking getters', () => {
  const inherited = Object.assign(Object.create({ injected: true }), copyStarter());
  assert.equal(validateSpecialistDesign(inherited).valid, false);
  const withGetter = copyStarter() as SpecialistDesign & { get credential(): string };
  let invoked = false;
  Object.defineProperty(withGetter, 'credential', { enumerable: true, get() { invoked = true; return 'secret'; } });
  assert.equal(validateSpecialistDesign(withGetter).valid, false);
  assert.equal(invoked, false);
});

test('malformed preview requests and excess delegation metadata cannot grant access', () => {
  const design = copyStarter();
  const request = grantStarterRead(design);
  const malformed = { ...request, nodeId: 'workspace-main', delegationDepth: 99 };
  assert.equal(previewSpecialistAccess(design, malformed as AccessPreviewRequest).decision, 'denied');
  for (const elapsedSeconds of [Number.NaN, Number.POSITIVE_INFINITY, 0.5, -1, 301]) {
    const badElapsed = { ...request, elapsedSeconds };
    assert.equal(previewSpecialistAccess(design, badElapsed).decision, 'denied');
  }
  design.agents[0]!.policy.maxDelegationDepth = 9;
  assert.equal(validateSpecialistDesign(design).valid, false);
});


test('unconnected planned infrastructure accepts an empty reference without authority', () => {
  const design = copyStarter();
  design.nodes.push({id:'planned-dc',label:'Planned data center',kind:'datacenter',parentId:'workspace-main',teamIds:[],externalRef:''});
  assert.equal(validateSpecialistDesign(design).valid, true);
  const request = grantStarterRead(design);
  request.nodeId = 'planned-dc';
  assert.equal(previewSpecialistAccess(design, request).decision, 'denied');
  assert.equal(previewSpecialistAccess(design, request).executionAllowed, false);
});
