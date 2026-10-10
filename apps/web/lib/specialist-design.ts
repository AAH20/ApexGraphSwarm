/**
 * Type SkillBinding.
 *
 *
 * @example
 * ```typescript
 * import { SkillBinding } from './module';
 * ```
 */
export type SkillBinding = { id: string; sourceUrl: string; revision: string; sha256: string };
/**
 * Type ToolBinding.
 *
 *
 * @example
 * ```typescript
 * import { ToolBinding } from './module';
 * ```
 */
export type ToolBinding = { serverId: string; toolName: string; gatewayId: string };
export type AccessPolicy = {
  provider: 'agentiam-lab' | 'agent-jit-iam' | 'external';
  subjectRef: string;
  ownerRef: string;
  tenantRef: string;
  audience: string;
  purpose: string;
  actions: string[];
  resourceIds: string[];
  ttlSeconds: number;
  maxDelegationDepth: number;
  approvalQuorum: number;
};
export type Specialist = {
  id: string;
  name: string;
  role: string;
  harnessId: string;
  modelRef: string;
  skills: SkillBinding[];
  tools: ToolBinding[];
  policy: AccessPolicy;
};
/**
 * Type SpecialistTeam.
 *
 *
 * @example
 * ```typescript
 * import { SpecialistTeam } from './module';
 * ```
 */
export type SpecialistTeam = { id: string; name: string; agentIds: string[] };
export type ScopeNode = {
  id: string;
  label: string;
  kind: 'workspace' | 'repository' | 'module' | 'swarm' | 'datacenter' | 'rack' | 'fleet' | 'device' | 'iot-center';
  parentId: string | null;
  teamIds: string[];
  externalRef: string;
};
/**
 * Type SpecialistDesign.
 *
 *
 * @example
 * ```typescript
 * import { SpecialistDesign } from './module';
 * ```
 */
export type SpecialistDesign = { schemaVersion: 1; id: string; name: string; agents: Specialist[]; teams: SpecialistTeam[]; nodes: ScopeNode[] };
/**
 * Type AccessPreviewRequest.
 *
 *
 * @example
 * ```typescript
 * import { AccessPreviewRequest } from './module';
 * ```
 */
export type AccessPreviewRequest = { agentId: string; nodeId: string; action: string; audience: string; purpose: string; elapsedSeconds: number; approverIds: string[] };
/**
 * Type AccessPreview.
 *
 *
 * @example
 * ```typescript
 * import { AccessPreview } from './module';
 * ```
 */
export type AccessPreview = { decision: 'denied' | 'approval-required' | 'eligible-for-review'; executionAllowed: false; reasons: string[] };

const MAX_JSON_BYTES = 512 * 1024;
const MAX_AGENTS = 300;
const MAX_TEAMS = 64;
const MAX_NODES = 300;
const MAX_LIST = 64;
const MAX_SKILLS_PER_AGENT = 32;
const MAX_TOOLS_PER_AGENT = 32;
const MAX_TTL_SECONDS = 300;
const MAX_DELEGATION_DEPTH = 8;
const MAX_APPROVAL_QUORUM = 8;
const MAX_JSON_DEPTH = 24;
const MAX_JSON_VALUES = 20_000;
const providerIds = new Set(['agentiam-lab', 'agent-jit-iam', 'external']);
const nodeKinds = new Set(['workspace', 'repository', 'module', 'swarm', 'datacenter', 'rack', 'fleet', 'device', 'iot-center']);
const forbiddenActionSegments = new Set(['admin', 'administer', 'actuate', 'actuation']);
const referencePattern = /^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}$/;

/**
 * Function plainRecord.
 *
 * @param value - Description of value.
 * @param {readonly string[]} expected - Description of expected.
 * @param {string} path - Description of path.
 * @param {string[]} errors - Description of errors.
 * @returns {Record<string, unknown> | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = plainRecord(..., ..., ..., ...);
 * ```
 */
function plainRecord(value: unknown, expected: readonly string[], path: string, errors: string[]): Record<string, unknown> | null {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    errors.push(`${path} must be an object.`);
    return null;
  }
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) {
    errors.push(`${path} must be a plain object.`);
    return null;
  }
  const descriptors = Object.getOwnPropertyDescriptors(value);
  const keys = Reflect.ownKeys(value);
  for (const key of keys) {
    if (typeof key !== 'string' || !expected.includes(key)) {
      errors.push(`${path} contains an unsupported field.`);
      continue;
    }
    const descriptor = descriptors[key];
    if (!descriptor || !('value' in descriptor) || !descriptor.enumerable) errors.push(`${path}.${key} must be a plain data field.`);
  }
  return value as Record<string, unknown>;
}

/**
 * Function ownArray.
 *
 * @param value - Description of value.
 * @param {string} path - Description of path.
 * @param {string[]} errors - Description of errors.
 * @returns {unknown[] | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = ownArray(..., ..., ...);
 * ```
 */
function ownArray(value: unknown, path: string, errors: string[]): unknown[] | null {
  if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) {
    errors.push(`${path} must be an array.`);
    return null;
  }
  const descriptors = Object.getOwnPropertyDescriptors(value);
  for (const key of Reflect.ownKeys(value)) {
    if (key === 'length') continue;
    if (typeof key !== 'string' || !/^(0|[1-9][0-9]*)$/.test(key) || Number(key) >= value.length) {
      errors.push(`${path} contains an unsupported array field.`);
      continue;
    }
    const descriptor = descriptors[key];
    if (!descriptor || !('value' in descriptor) || !descriptor.enumerable) errors.push(`${path}[${key}] must be a plain data value.`);
  }
  const result: unknown[] = [];
  for (let index = 0; index < value.length; index += 1) {
    if (!Object.hasOwn(descriptors, String(index))) errors.push(`${path} must not contain holes.`);
    result.push(descriptors[String(index)] && 'value' in descriptors[String(index)] ? descriptors[String(index)].value : undefined);
  }
  return result;
}

/**
 * Function copyBoundedJson.
 *
 * @param value - Description of value.
 * @param {{ seen: Set<object>; values: number }} state - Description of state.
 * @param {number} depth - Description of depth.
 * @returns {unknown} Description of return value.
 *
 * @example
 * ```typescript
 * const result = copyBoundedJson(..., ..., ...);
 * ```
 */
function copyBoundedJson(value: unknown, state: { seen: Set<object>; values: number }, depth: number): unknown {
  if (depth > MAX_JSON_DEPTH || ++state.values > MAX_JSON_VALUES) throw new Error('input bounds exceeded');
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return value;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('non-finite number');
    return value;
  }
  if (typeof value !== 'object') throw new Error('non-JSON value');
  if (state.seen.has(value)) throw new Error('cyclic input');
  state.seen.add(value);
  try {
    if (Array.isArray(value)) {
      if (Object.getPrototypeOf(value) !== Array.prototype) throw new Error('non-plain array');
      const descriptors = Object.getOwnPropertyDescriptors(value);
      for (const key of Reflect.ownKeys(value)) {
        if (key === 'length') continue;
        if (typeof key !== 'string' || !/^(0|[1-9][0-9]*)$/.test(key) || Number(key) >= value.length) throw new Error('array has extra properties');
        const descriptor = descriptors[key];
        if (!descriptor || !('value' in descriptor) || !descriptor.enumerable) throw new Error('array contains accessor or hidden data');
      }
      const result: unknown[] = [];
      for (let index = 0; index < value.length; index += 1) {
        const descriptor = descriptors[String(index)];
        if (!descriptor || !('value' in descriptor)) throw new Error('array contains holes or accessors');
        result.push(copyBoundedJson(descriptor.value, state, depth + 1));
      }
      return result;
    }
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) throw new Error('non-plain object');
    const descriptors = Object.getOwnPropertyDescriptors(value);
    const result: Record<string, unknown> = Object.create(null) as Record<string, unknown>;
    for (const key of Reflect.ownKeys(value)) {
      if (typeof key !== 'string' || key === '__proto__' || key === 'prototype' || key === 'constructor') throw new Error('unsafe object key');
      const descriptor = descriptors[key];
      if (!descriptor || !('value' in descriptor) || !descriptor.enumerable) throw new Error('object contains accessor or hidden data');
      result[key] = copyBoundedJson(descriptor.value, state, depth + 1);
    }
    return result;
  } finally {
    state.seen.delete(value);
  }
}

/**
 * Function text.
 *
 * @param {Record<string, unknown>} record - Description of record.
 * @param {string} key - Description of key.
 * @param {string} path - Description of path.
 * @param {string[]} errors - Description of errors.
 * @param {number} max - Description of max.
 * @param min - Description of min.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = text(..., ..., ..., ..., ..., ...);
 * ```
 */
function text(record: Record<string, unknown>, key: string, path: string, errors: string[], max: number, min = 1): string {
  const value = record[key];
  if (typeof value !== 'string' || value.trim().length < min || value.length > max || /[\u0000-\u001f\u007f]/.test(value)) {
    errors.push(`${path}.${key} must be text of ${min}–${max} characters without control characters.`);
    return '';
  }
  return value;
}

/**
 * Function identifier.
 *
 * @param value - Description of value.
 * @param {string} path - Description of path.
 * @param {string[]} errors - Description of errors.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = identifier(..., ..., ...);
 * ```
 */
function identifier(value: unknown, path: string, errors: string[]): string {
  if (typeof value !== 'string' || !referencePattern.test(value) || value.includes('://') || /[?*]/.test(value)) {
    errors.push(`${path} must be a non-secret exact identifier.`);
    return '';
  }
  return value;
}

/**
 * Function stringList.
 *
 * @param value - Description of value.
 * @param {string} path - Description of path.
 * @param {string[]} errors - Description of errors.
 * @param max - Description of max.
 * @param exactIdentifier - Description of exactIdentifier.
 * @returns {string[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = stringList(..., ..., ..., ..., ...);
 * ```
 */
function stringList(value: unknown, path: string, errors: string[], max = MAX_LIST, exactIdentifier = false): string[] {
  const items = ownArray(value, path, errors);
  if (!items) return [];
  if (items.length > max) errors.push(`${path} may contain at most ${max} entries.`);
  const result = items.slice(0, max).map((item, index) => exactIdentifier
    ? identifier(item, `${path}[${index}]`, errors)
    : typeof item === 'string' && /^[a-z][a-z0-9._:-]{0,63}$/.test(item)
      ? item
      : (errors.push(`${path}[${index}] must be a lowercase exact action with no wildcard.`), ''));
  if (new Set(result).size !== result.length) errors.push(`${path} must not contain duplicates.`);
  return result;
}

/**
 * Function parseSkill.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {SkillBinding | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseSkill(..., ..., ...);
 * ```
 */
function parseSkill(value: unknown, index: number, errors: string[]): SkillBinding | null {
  const path = `agents.skills[${index}]`;
  const item = plainRecord(value, ['id', 'sourceUrl', 'revision', 'sha256'], path, errors);
  if (!item) return null;
  const id = identifier(item.id, `${path}.id`, errors);
  const sourceUrl = text(item, 'sourceUrl', path, errors, 2048);
  const revision = text(item, 'revision', path, errors, 256);
  const sha256 = text(item, 'sha256', path, errors, 64);
  try {
    const url = new URL(sourceUrl);
    if (url.protocol !== 'https:' || url.username || url.password) errors.push(`${path}.sourceUrl must be HTTPS without URL credentials.`);
    if (url.search || url.hash) errors.push(`${path}.sourceUrl must not contain a query or fragment.`);
  } catch {
    errors.push(`${path}.sourceUrl must be an absolute HTTPS URL.`);
  }
  if (!/^[a-f0-9]{64}$/.test(sha256)) errors.push(`${path}.sha256 must be a pinned lowercase SHA-256 digest.`);
  return { id, sourceUrl, revision, sha256 };
}

/**
 * Function parseTool.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {ToolBinding | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseTool(..., ..., ...);
 * ```
 */
function parseTool(value: unknown, index: number, errors: string[]): ToolBinding | null {
  const path = `agents.tools[${index}]`;
  const item = plainRecord(value, ['serverId', 'toolName', 'gatewayId'], path, errors);
  if (!item) return null;
  const serverId = identifier(item.serverId, `${path}.serverId`, errors);
  const toolName = identifier(item.toolName, `${path}.toolName`, errors);
  const gatewayId = identifier(item.gatewayId, `${path}.gatewayId`, errors);
  return { serverId, toolName, gatewayId };
}

/**
 * Function parsePolicy.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {AccessPolicy | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parsePolicy(..., ..., ...);
 * ```
 */
function parsePolicy(value: unknown, index: number, errors: string[]): AccessPolicy | null {
  const path = `agents[${index}].policy`;
  const item = plainRecord(value, ['provider', 'subjectRef', 'ownerRef', 'tenantRef', 'audience', 'purpose', 'actions', 'resourceIds', 'ttlSeconds', 'maxDelegationDepth', 'approvalQuorum'], path, errors);
  if (!item) return null;
  const provider = item.provider;
  if (typeof provider !== 'string' || !providerIds.has(provider)) errors.push(`${path}.provider is unsupported.`);
  const subjectRef = identifier(item.subjectRef, `${path}.subjectRef`, errors);
  const ownerRef = identifier(item.ownerRef, `${path}.ownerRef`, errors);
  const tenantRef = identifier(item.tenantRef, `${path}.tenantRef`, errors);
  const audience = identifier(item.audience, `${path}.audience`, errors);
  const purpose = identifier(item.purpose, `${path}.purpose`, errors);
  const actions = stringList(item.actions, `${path}.actions`, errors);
  const resourceIds = stringList(item.resourceIds, `${path}.resourceIds`, errors, MAX_LIST, true);
  const ttlSeconds = item.ttlSeconds;
  const maxDelegationDepth = item.maxDelegationDepth;
  const approvalQuorum = item.approvalQuorum;
  if (!Number.isSafeInteger(ttlSeconds) || (ttlSeconds as number) < 1 || (ttlSeconds as number) > MAX_TTL_SECONDS) errors.push(`${path}.ttlSeconds must be an integer from 1 to ${MAX_TTL_SECONDS}.`);
  if (!Number.isSafeInteger(maxDelegationDepth) || (maxDelegationDepth as number) < 0 || (maxDelegationDepth as number) > MAX_DELEGATION_DEPTH) errors.push(`${path}.maxDelegationDepth must be an integer from 0 to ${MAX_DELEGATION_DEPTH}.`);
  if (!Number.isSafeInteger(approvalQuorum) || (approvalQuorum as number) < 0 || (approvalQuorum as number) > MAX_APPROVAL_QUORUM) errors.push(`${path}.approvalQuorum must be an integer from 0 to ${MAX_APPROVAL_QUORUM}.`);
  return {
    provider: providerIds.has(String(provider)) ? provider as AccessPolicy['provider'] : 'external',
    subjectRef, ownerRef, tenantRef, audience, purpose, actions, resourceIds,
    ttlSeconds: Number.isSafeInteger(ttlSeconds) ? ttlSeconds as number : 0,
    maxDelegationDepth: Number.isSafeInteger(maxDelegationDepth) ? maxDelegationDepth as number : 0,
    approvalQuorum: Number.isSafeInteger(approvalQuorum) ? approvalQuorum as number : 0,
  };
}

/**
 * Function parseAgent.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {Specialist | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseAgent(..., ..., ...);
 * ```
 */
function parseAgent(value: unknown, index: number, errors: string[]): Specialist | null {
  const path = `agents[${index}]`;
  const item = plainRecord(value, ['id', 'name', 'role', 'harnessId', 'modelRef', 'skills', 'tools', 'policy'], path, errors);
  if (!item) return null;
  const id = identifier(item.id, `${path}.id`, errors);
  const name = text(item, 'name', path, errors, 128);
  const role = text(item, 'role', path, errors, 256);
  const harnessId = identifier(item.harnessId, `${path}.harnessId`, errors);
  const modelRef = identifier(item.modelRef, `${path}.modelRef`, errors);
  const rawSkills = ownArray(item.skills, `${path}.skills`, errors) ?? [];
  const rawTools = ownArray(item.tools, `${path}.tools`, errors) ?? [];
  if (rawSkills.length > MAX_SKILLS_PER_AGENT) errors.push(`${path}.skills may contain at most ${MAX_SKILLS_PER_AGENT} bindings.`);
  if (rawTools.length > MAX_TOOLS_PER_AGENT) errors.push(`${path}.tools may contain at most ${MAX_TOOLS_PER_AGENT} bindings.`);
  const skills = rawSkills.slice(0, MAX_SKILLS_PER_AGENT).map((skill, skillIndex) => parseSkill(skill, skillIndex, errors)).filter((skill): skill is SkillBinding => skill !== null);
  const tools = rawTools.slice(0, MAX_TOOLS_PER_AGENT).map((tool, toolIndex) => parseTool(tool, toolIndex, errors)).filter((tool): tool is ToolBinding => tool !== null);
  const skillIds = skills.map(skill => skill.id);
  if (new Set(skillIds).size !== skillIds.length) errors.push(`${path}.skills must not contain duplicate IDs.`);
  if (new Set(tools.map(tool => `${tool.serverId}\u0000${tool.toolName}\u0000${tool.gatewayId}`)).size !== tools.length) errors.push(`${path}.tools must not contain duplicate bindings.`);
  const policy = parsePolicy(item.policy, index, errors);
  return { id, name, role, harnessId, modelRef, skills, tools, policy: policy ?? emptyPolicy() };
}

/**
 * Function emptyPolicy.
 *
 * @returns {AccessPolicy} Description of return value.
 *
 * @example
 * ```typescript
 * import { emptyPolicy } from './module';
 * ```
 */
function emptyPolicy(): AccessPolicy {
  return { provider: 'external', subjectRef: 'subject:unassigned', ownerRef: 'owner:unassigned', tenantRef: 'tenant:local', audience: 'apexgraphswarm', purpose: 'unassigned', actions: [], resourceIds: [], ttlSeconds: 300, maxDelegationDepth: 0, approvalQuorum: 1 };
}

/**
 * Function parseTeam.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {SpecialistTeam | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseTeam(..., ..., ...);
 * ```
 */
function parseTeam(value: unknown, index: number, errors: string[]): SpecialistTeam | null {
  const path = `teams[${index}]`;
  const item = plainRecord(value, ['id', 'name', 'agentIds'], path, errors);
  if (!item) return null;
  return { id: identifier(item.id, `${path}.id`, errors), name: text(item, 'name', path, errors, 128), agentIds: stringList(item.agentIds, `${path}.agentIds`, errors, MAX_AGENTS, true) };
}

/**
 * Function parseNode.
 *
 * @param value - Description of value.
 * @param {number} index - Description of index.
 * @param {string[]} errors - Description of errors.
 * @returns {ScopeNode | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseNode(..., ..., ...);
 * ```
 */
function parseNode(value: unknown, index: number, errors: string[]): ScopeNode | null {
  const path = `nodes[${index}]`;
  const item = plainRecord(value, ['id', 'label', 'kind', 'parentId', 'teamIds', 'externalRef'], path, errors);
  if (!item) return null;
  const id = identifier(item.id, `${path}.id`, errors);
  const label = text(item, 'label', path, errors, 128);
  const kind = item.kind;
  if (typeof kind !== 'string' || !nodeKinds.has(kind)) errors.push(`${path}.kind is unsupported.`);
  const rawParent = item.parentId;
  const parentId = rawParent === null ? null : identifier(rawParent, `${path}.parentId`, errors) || null;
  const teamIds = stringList(item.teamIds, `${path}.teamIds`, errors, MAX_TEAMS, true);
  const externalRef = text(item, 'externalRef', path, errors, 2048, 0);
  if (externalRef.includes('://')) {
    try {
      const url = new URL(externalRef);
      if (url.username || url.password || url.search || url.hash) errors.push(`${path}.externalRef URLs must not contain userinfo, queries, or fragments.`);
    } catch { errors.push(`${path}.externalRef URL is invalid.`); }
  }
  return { id, label, kind: nodeKinds.has(String(kind)) ? kind as ScopeNode['kind'] : 'workspace', parentId, teamIds, externalRef };
}

function addDuplicateErrors<T>(items: readonly T[], key: (item: T) => string, path: string, errors: string[]): void {
  const seen = new Set<string>();
  for (const item of items) {
    const value = key(item);
    if (seen.has(value)) errors.push(`${path} must have unique IDs.`);
    seen.add(value);
  }
}

/**
 * Function validateHierarchy.
 *
 * @param {readonly ScopeNode[]} nodes - Description of nodes.
 * @param {string[]} errors - Description of errors.
 *
 * @example
 * ```typescript
 * const result = validateHierarchy(..., ...);
 * ```
 */
function validateHierarchy(nodes: readonly ScopeNode[], errors: string[]): void {
  const byId = new Map(nodes.map(node => [node.id, node]));
  const roots = nodes.filter(node => node.parentId === null);
  if (roots.length !== 1 || roots[0]?.kind !== 'workspace') errors.push('nodes must form one hierarchy with exactly one workspace root.');
  for (const node of nodes) {
    if (node.parentId !== null && !byId.has(node.parentId)) errors.push(`nodes.${node.id}.parentId references an unknown node.`);
    const seen = new Set<string>();
    let current: ScopeNode | undefined = node;
    while (current && current.parentId !== null) {
      if (seen.has(current.id)) {
        errors.push(`nodes.${node.id} participates in a parent cycle.`);
        break;
      }
      seen.add(current.id);
      current = byId.get(current.parentId);
    }
    if (current && current.parentId === null && current.kind !== 'workspace') errors.push(`nodes.${node.id} is not under the workspace root.`);
    if (!current) errors.push(`nodes.${node.id} is disconnected from the workspace root.`);
  }
}

/**
 * Function validateSpecialistDesign.
 *
 * @param input - Description of input.
 *
 * @example
 * ```typescript
 * const result = validateSpecialistDesign(...);
 * ```
 */
export function validateSpecialistDesign(input: unknown): { valid: boolean; errors: string[]; design: SpecialistDesign | null } {
  try {
    if (input === null || typeof input !== 'object') return { valid: false, errors: ['Design must be a JSON object.'], design: null };
    let encoded: string;
    try { encoded = JSON.stringify(copyBoundedJson(input, { seen: new Set(), values: 0 }, 0)); } catch { return { valid: false, errors: ['Design must be bounded, acyclic plain JSON data without accessors or unsafe object keys.'], design: null }; }
    if (typeof encoded !== 'string' || new TextEncoder().encode(encoded).byteLength > MAX_JSON_BYTES) return { valid: false, errors: [`Design exceeds the ${MAX_JSON_BYTES}-byte limit.`], design: null };
    const errors: string[] = [];
    const root = plainRecord(input, ['schemaVersion', 'id', 'name', 'agents', 'teams', 'nodes'], 'design', errors);
    if (!root) return { valid: false, errors, design: null };
    if (root.schemaVersion !== 1) errors.push('design.schemaVersion must be 1.');
    const id = identifier(root.id, 'design.id', errors);
    const name = text(root, 'name', 'design', errors, 128);
    const rawAgents = ownArray(root.agents, 'design.agents', errors) ?? [];
    const rawTeams = ownArray(root.teams, 'design.teams', errors) ?? [];
    const rawNodes = ownArray(root.nodes, 'design.nodes', errors) ?? [];
    if (rawAgents.length > MAX_AGENTS) errors.push(`design.agents may contain at most ${MAX_AGENTS}.`);
    if (rawTeams.length > MAX_TEAMS) errors.push(`design.teams may contain at most ${MAX_TEAMS}.`);
    if (rawNodes.length > MAX_NODES) errors.push(`design.nodes may contain at most ${MAX_NODES}.`);
    const agents = rawAgents.slice(0, MAX_AGENTS).map((agent, index) => parseAgent(agent, index, errors)).filter((agent): agent is Specialist => agent !== null);
    const teams = rawTeams.slice(0, MAX_TEAMS).map((team, index) => parseTeam(team, index, errors)).filter((team): team is SpecialistTeam => team !== null);
    const nodes = rawNodes.slice(0, MAX_NODES).map((node, index) => parseNode(node, index, errors)).filter((node): node is ScopeNode => node !== null);
    addDuplicateErrors(agents, agent => agent.id, 'design.agents', errors);
    addDuplicateErrors(teams, team => team.id, 'design.teams', errors);
    addDuplicateErrors(nodes, node => node.id, 'design.nodes', errors);
    addDuplicateErrors([...agents, ...teams, ...nodes], item => item.id, 'design', errors);
    const agentIds = new Set(agents.map(agent => agent.id));
    const teamIds = new Set(teams.map(team => team.id));
    const nodeIds = new Set(nodes.map(node => node.id));
    for (const team of teams) for (const agentId of team.agentIds) if (!agentIds.has(agentId)) errors.push(`teams.${team.id} references unknown specialist ${agentId}.`);
    for (const node of nodes) for (const teamId of node.teamIds) if (!teamIds.has(teamId)) errors.push(`nodes.${node.id} references unknown team ${teamId}.`);
    for (const agent of agents) for (const resourceId of agent.policy.resourceIds) if (!nodeIds.has(resourceId)) errors.push(`agents.${agent.id} references unknown resource node ${resourceId}.`);
    validateHierarchy(nodes, errors);
    return errors.length ? { valid: false, errors: [...new Set(errors)], design: null } : {
      valid: true,
      errors: [],
      design: { schemaVersion: 1, id, name, agents, teams, nodes },
    };
  } catch {
    return { valid: false, errors: ['Design contains invalid or hostile object data.'], design: null };
  }
}

/**
 * Function privilegedAction.
 *
 * @param {string} action - Description of action.
 * @returns {boolean} Description of return value.
 *
 * @example
 * ```typescript
 * const result = privilegedAction(...);
 * ```
 */
function privilegedAction(action: string): boolean {
  return action.split(/[^a-z]+/i).some(part => forbiddenActionSegments.has(part.toLowerCase()));
}

/**
 * Function denied.
 *
 * @param {string[]} reasons - Description of reasons.
 * @returns {AccessPreview} Description of return value.
 *
 * @example
 * ```typescript
 * const result = denied(...);
 * ```
 */
function denied(reasons: string[]): AccessPreview {
  return { decision: 'denied', executionAllowed: false, reasons: [...new Set(reasons)] };
}

/**
 * Function previewSpecialistAccess.
 *
 * @param {SpecialistDesign} design - Description of design.
 * @param {AccessPreviewRequest} request - Description of request.
 * @returns {AccessPreview} Description of return value.
 *
 * @example
 * ```typescript
 * const result = previewSpecialistAccess(..., ...);
 * ```
 */
export function previewSpecialistAccess(design: SpecialistDesign, request: AccessPreviewRequest): AccessPreview {
  try {
  const validation = validateSpecialistDesign(design);
  if (!validation.valid || !validation.design) return denied(['Design is invalid; access preview is unavailable.', ...validation.errors]);
  const errors: string[] = [];
  const safeRequest = plainRecord(request, ['agentId', 'nodeId', 'action', 'audience', 'purpose', 'elapsedSeconds', 'approverIds'], 'request', errors);
  if (!safeRequest) return denied(['Request is invalid.', ...errors]);
  const agentId = identifier(safeRequest.agentId, 'request.agentId', errors);
  const nodeId = identifier(safeRequest.nodeId, 'request.nodeId', errors);
  const actionValue = safeRequest.action;
  if (typeof actionValue !== 'string' || !/^[a-z][a-z0-9._:-]{0,63}$/.test(actionValue)) errors.push('request.action must be a lowercase exact action.');
  const action = typeof actionValue === 'string' ? actionValue : '';
  const audience = identifier(safeRequest.audience, 'request.audience', errors);
  const purpose = identifier(safeRequest.purpose, 'request.purpose', errors);
  const elapsedSeconds = safeRequest.elapsedSeconds;
  if (typeof elapsedSeconds !== 'number' || !Number.isSafeInteger(elapsedSeconds) || elapsedSeconds < 0 || elapsedSeconds > MAX_TTL_SECONDS) errors.push(`request.elapsedSeconds must be between 0 and ${MAX_TTL_SECONDS}.`);
  const approverIds = stringList(safeRequest.approverIds, 'request.approverIds', errors, MAX_APPROVAL_QUORUM * 6, true);
  if (errors.length) return denied(errors);
  if (privilegedAction(action)) return denied(['Privileged administer/actuate actions are disabled without an enforcing adapter and physical controller.']);
  if (action !== 'read' && action !== 'plan') return denied(['Only exact read or plan requests can be eligible for review.']);
  const current = validation.design;
  const agent = current.agents.find(item => item.id === agentId);
  const node = current.nodes.find(item => item.id === nodeId);
  if (!agent || !node) return denied(['Specialist and scope node must exist in this design.']);
  const assigned = node.teamIds.some(teamId => current.teams.some(team => team.id === teamId && team.agentIds.includes(agentId)));
  if (!assigned) return denied(['Specialist is not explicitly assigned through a team to this exact scope node.']);
  const policy = agent.policy;
  if (!policy.actions.includes(action)) return denied(['The exact action is not in the specialist allow-list.']);
  if (!policy.resourceIds.includes(nodeId)) return denied(['The exact scope node is not in the specialist resource allow-list; parent scopes are not inherited.']);
  if (policy.audience !== audience) return denied(['Request audience does not exactly match the policy.']);
  if (policy.purpose !== purpose) return denied(['Request purpose does not exactly match the policy.']);
  if ((elapsedSeconds as number) >= policy.ttlSeconds) return denied(['The requested access window has expired.']);
  if (approverIds.length < policy.approvalQuorum) return {
    decision: 'approval-required', executionAllowed: false,
    reasons: [`${policy.approvalQuorum - approverIds.length} additional unique approver identity/identities are required; identities are not authenticated by this preview.`],
  };
  return {
    decision: 'eligible-for-review', executionAllowed: false,
    reasons: ['Preview only: request may be submitted to a separately authenticated approval and enforcement system.', 'Approver identities and IAM provider claims are not verified here; no credentials or capabilities are minted.'],
  };
  } catch {
    return denied(['Request contains invalid or hostile object data.']);
  }
}

/**
 * Function createStarterDesign.
 *
 * @returns {SpecialistDesign} Description of return value.
 *
 * @example
 * ```typescript
 * import { createStarterDesign } from './module';
 * ```
 */
export function createStarterDesign(): SpecialistDesign {
  const agents: Specialist[] = [
    { id: 'agent-planner', name: 'Planner', role: 'Break a goal into bounded tasks.', harnessId: 'unconfigured', modelRef: 'unconfigured', skills: [], tools: [], policy: emptyPolicy() },
    { id: 'agent-researcher', name: 'Researcher', role: 'Collect cited evidence for a task.', harnessId: 'unconfigured', modelRef: 'unconfigured', skills: [], tools: [], policy: emptyPolicy() },
    { id: 'agent-reviewer', name: 'Reviewer', role: 'Check outputs against explicit criteria.', harnessId: 'unconfigured', modelRef: 'unconfigured', skills: [], tools: [], policy: emptyPolicy() },
  ];
  return {
    schemaVersion: 1,
    id: 'design-starter',
    name: 'New specialist workspace',
    agents,
    teams: [{ id: 'team-core', name: 'Core team', agentIds: agents.map(agent => agent.id) }],
    nodes: [{ id: 'workspace-main', label: 'Workspace', kind: 'workspace', parentId: null, teamIds: ['team-core'], externalRef: 'workspace:main' }],
  };
}
