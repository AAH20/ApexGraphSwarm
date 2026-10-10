/**
 * Constant MAX_SKILL_BYTES.
 *
 *
 * @example
 * ```typescript
 * import { MAX_SKILL_BYTES } from './module';
 * ```
 */
export const MAX_SKILL_BYTES = 200_000;
/**
 * Constant MAX_FRONTMATTER_BYTES.
 *
 *
 * @example
 * ```typescript
 * import { MAX_FRONTMATTER_BYTES } from './module';
 * ```
 */
export const MAX_FRONTMATTER_BYTES = 16_000;
/**
 * Constant MAX_DECLARATIONS.
 *
 *
 * @example
 * ```typescript
 * import { MAX_DECLARATIONS } from './module';
 * ```
 */
export const MAX_DECLARATIONS = 64;
/**
 * Core library module for skill manifest.ts functionality.
 *
 * @module skill-manifest
 * @packageDocumentation
 */
const KNOWN_HARNESSES = new Set(['codex', 'claude-code', 'cursor', 'antigravity', 'opencode', 'hermes']);

export type SkillImportInput = {
  /** Exact pasted SKILL.md text. Content is never fetched from sourceUrl. */
  skillText?: string;
  sourceUrl?: string;
  /** User-supplied source revision/tag/commit. It is provenance text, not remotely verified. */
  exactRevision?: string;
  /** Explicitly reviewed harness mapping; not inferred from free-form compatibility text. */
  supportedHarnesses?: string[];
};

export type LockedSkillManifest = Readonly<{
  id: string;
  name: string;
  description: string;
  sourceUrl: string | null;
  exactRevision: string | null;
  contentSha256: string;
  rawFrontmatter: string;
  rawFields: Readonly<Record<string, string>>;
  compatibility: string | null;
  license: string | null;
  declaredPermissions: readonly string[];
  declaredCapabilities: readonly string[];
  supportedHarnesses: readonly string[];
  /** Exact text only; never executed, installed, fetched recursively, or interpreted as paths. */
  skillText: string;
  trustReviewStatus: 'pending-review';
  locked: true;
}>;

export type SkillImportReview = {
  status: 'content-required' | 'invalid' | 'pending-review';
  valid: boolean;
  errors: string[];
  warnings: string[];
  manifest: LockedSkillManifest | null;
};

/**
 * Type ParsedFrontmatter.
 *
 *
 * @example
 * ```typescript
 * import { ParsedFrontmatter } from './module';
 * ```
 */
type ParsedFrontmatter = { raw: string; fields: Record<string, string>; errors: string[]; warnings: string[]; body: string };

/**
 * Function utf8Size.
 *
 * @param {string} value - Description of value.
 * @returns {number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = utf8Size(...);
 * ```
 */
function utf8Size(value: string): number {
  return new TextEncoder().encode(value).byteLength;
}

/**
 * Function parseScalar.
 *
 * @param {string} rawValue - Description of rawValue.
 * @param {number} lineNumber - Description of lineNumber.
 * @param {string[]} errors - Description of errors.
 * @returns {string | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseScalar(..., ..., ...);
 * ```
 */
function parseScalar(rawValue: string, lineNumber: number, errors: string[]): string | null {
  const value = rawValue.trim();
  if (!value) {
    errors.push(`Frontmatter line ${lineNumber}: empty scalar values are unsupported.`);
    return null;
  }
  if (/^(?:[|>]|[&*!])/.test(value) || /^[\[{]/.test(value) || /(?:^|\s)[&*!][A-Za-z0-9_-]+/.test(value)) {
    errors.push(`Frontmatter line ${lineNumber}: YAML blocks, collections, tags, anchors, and aliases are unsupported.`);
    return null;
  }
  if (value.startsWith('"')) {
    try {
      const parsed: unknown = JSON.parse(value);
      if (typeof parsed !== 'string') throw new Error('not a string');
      return parsed;
    } catch {
      errors.push(`Frontmatter line ${lineNumber}: double-quoted values must use valid JSON string escaping.`);
      return null;
    }
  }
  if (value.startsWith("'")) {
    if (!/^'(?:[^']|'')*'$/.test(value)) {
      errors.push(`Frontmatter line ${lineNumber}: unterminated single-quoted scalar.`);
      return null;
    }
    return value.slice(1, -1).replace(/''/g, "'");
  }
  const implicitlyTyped = /^(?:null|~|true|false|yes|no|on|off|[-+]?(?:0|[1-9][0-9_]*|0x[0-9a-f_]+|0o[0-7_]+|0b[01_]+|(?:[0-9][0-9_]*)?\.[0-9_]+(?:[eE][-+]?[0-9_]+)?|[0-9][0-9_]*[eE][-+]?[0-9_]+|\.(?:inf|nan)))$/i;
  const dateLike = /^\d{4}-\d{1,2}-\d{1,2}(?:[Tt ]\d{2}:\d{2}.*)?$/;
  if (value.includes(': ') || value.includes('\t') || /\s#/.test(value) || /^[-?:](?:\s|$)/.test(value) || implicitlyTyped.test(value) || dateLike.test(value)) {
    errors.push(`Frontmatter line ${lineNumber}: ambiguous or implicitly typed plain scalar; quote strings containing ': ', comments, YAML indicators, numbers, booleans, nulls, or dates.`);
    return null;
  }
  return value;
}

function parseFrontmatter(skillText: string): ParsedFrontmatter {
  const lines = skillText.split(/\r?\n/);
  const errors: string[] = [];
  const warnings: string[] = [];
  if (lines[0] !== '---') return { raw: '', fields: {}, errors: ['SKILL.md must start with a YAML frontmatter delimiter (---).'], warnings, body: '' };
  const close = lines.findIndex((line, index) => index > 0 && line === '---');
  if (close < 0) return { raw: '', fields: {}, errors: ['YAML frontmatter closing delimiter (---) is missing.'], warnings, body: '' };
  const rawLines = lines.slice(1, close);
  const raw = rawLines.join('\n');
  if (utf8Size(raw) > MAX_FRONTMATTER_BYTES) errors.push(`YAML frontmatter exceeds ${MAX_FRONTMATTER_BYTES} bytes.`);
  const fields: Record<string, string> = {};
  const seenTopLevel = new Set<string>();
  let metadataSeen = false;
  let metadataChildren = 0;
  let inMetadata = false;
  for (let index = 0; index < rawLines.length; index += 1) {
    const line = rawLines[index];
    const lineNumber = index + 2;
    if (!line.trim() || line.trimStart().startsWith('#')) continue;
    if (line.includes('\t')) {
      errors.push(`Frontmatter line ${lineNumber}: tabs/indentation are unsupported.`);
      continue;
    }
    if (line.startsWith('  ')) {
      if (!inMetadata || !line.startsWith('  ') || line.startsWith('   ')) {
        errors.push(`Frontmatter line ${lineNumber}: only a flat two-space metadata mapping is supported.`);
        continue;
      }
      const nested = /^  ([A-Za-z0-9_.-]+):(?:\s+(.*))?$/.exec(line);
      if (!nested) {
        errors.push(`Frontmatter line ${lineNumber}: unsupported metadata structure.`);
        continue;
      }
      const key = `metadata.${nested[1]}`;
      metadataChildren += 1;
      if (Object.hasOwn(fields, key)) {
        errors.push(`Frontmatter line ${lineNumber}: duplicate field '${key}'.`);
        continue;
      }
      const scalar = parseScalar(nested[2] ?? '', lineNumber, errors);
      if (scalar !== null) fields[key] = scalar;
      continue;
    }
    if (/^\s/.test(line)) {
      errors.push(`Frontmatter line ${lineNumber}: unexpected indentation.`);
      continue;
    }
    const top = /^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$/.exec(line);
    if (!top) {
      errors.push(`Frontmatter line ${lineNumber}: expected a simple 'key: scalar' field.`);
      inMetadata = false;
      continue;
    }
    const key = top[1];
    if (seenTopLevel.has(key)) {
      errors.push(`Frontmatter line ${lineNumber}: duplicate field '${key}'.`);
      inMetadata = false;
      continue;
    }
    seenTopLevel.add(key);
    if (key === 'metadata') {
      metadataSeen = true;
      if ((top[2] ?? '').trim() === '') {
        inMetadata = true;
      } else {
        errors.push(`Frontmatter line ${lineNumber}: metadata must be a flat mapping; scalar and inline map forms are unsupported.`);
      }
      continue;
    }
    inMetadata = false;
    const scalar = parseScalar(top[2] ?? '', lineNumber, errors);
    if (scalar !== null) fields[key] = scalar;
  }
  if (metadataSeen && metadataChildren === 0) errors.push('metadata must contain at least one supported two-space scalar entry; null/empty mappings are unsupported.');
  const body = lines.slice(close + 1).join('\n');
  const standard = new Set(['name', 'description', 'license', 'compatibility', 'allowed-tools', 'metadata']);
  for (const key of Object.keys(fields)) {
    const base = key.startsWith('metadata.') ? 'metadata' : key;
    if (!standard.has(base) && !['permissions', 'capabilities', 'supported-harnesses'].includes(key)) {
      warnings.push(`Custom frontmatter field '${key}' is preserved as raw metadata only.`);
    }
  }
  return { raw, fields, errors, warnings, body };
}

function listFrom(value: string | undefined): string[] {
  if (!value) return [];
  return [...new Set(value.split(/[\s,]+/).map(item => item.trim()).filter(Boolean))];
}

function validateSourceUrl(value: string | undefined, errors: string[]): string | null {
  if (value === undefined || value === '') return null;
  if (typeof value !== 'string') {
    errors.push('Source URL must be a string.');
    return null;
  }
  const raw = value.trim();
  if (!raw) return null;
  if (raw.length > 2048 || raw.includes('?') || raw.includes('#')) {
    errors.push('Source URL must be at most 2048 characters and cannot contain a query or fragment (which may include secrets).');
    return null;
  }
  try {
    const parsed = new URL(raw);
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password) throw new Error('unsafe URL');
    return raw;
  } catch {
    errors.push('Source URL must be an HTTPS URL without embedded credentials. No URL is fetched.');
    return null;
  }
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

function uniqueStrings(values: string[], label: string, errors: string[]): string[] {
  const clean = [...new Set(values.map(value => value.trim()).filter(Boolean))];
  if (clean.length > MAX_DECLARATIONS) errors.push(`${label} may contain at most ${MAX_DECLARATIONS} entries.`);
  for (const value of clean) {
    if (value.length > 160 || /[\u0000-\u001f\u007f]/.test(value)) errors.push(`${label} contains an invalid or overlong entry.`);
  }
  return clean;
}

/**
 * Parse and freeze a user-supplied Agent Skill for review. This does not fetch
 * the source URL, install the skill, load local files, or execute any content.
 */
export async function reviewSkillImport(input: SkillImportInput): Promise<SkillImportReview> {
  const errors: string[] = [];
  const warnings: string[] = ['Skill instructions and declared permissions are untrusted claims and require human review before any harness use.'];
  const sourceUrl = validateSourceUrl(input.sourceUrl, errors);
  const exactRevision = typeof input.exactRevision === 'string' ? input.exactRevision.trim() || null : null;
  if (input.exactRevision !== undefined && typeof input.exactRevision !== 'string') errors.push('Exact revision must be a string.');
  if (exactRevision && (exactRevision.length > 256 || /[\u0000-\u001f\u007f]/.test(exactRevision))) errors.push('Exact revision must be at most 256 printable characters. It is not remotely verified.');
  else if (exactRevision) warnings.push('The supplied revision is preserved as provenance text; it is not remotely verified against the source.');
  const rawHarnesses = input.supportedHarnesses ?? [];
  if (!Array.isArray(rawHarnesses)) errors.push('supportedHarnesses must be a list of strings.');
  if (Array.isArray(rawHarnesses) && rawHarnesses.some(value => typeof value !== 'string')) errors.push('supportedHarnesses entries must be strings.');
  const requestedHarnesses = uniqueStrings(Array.isArray(rawHarnesses) ? rawHarnesses.filter((value): value is string => typeof value === 'string') : [], 'supportedHarnesses', errors);
  for (const harness of requestedHarnesses) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(harness)) errors.push(`Unsupported harness identifier syntax: '${harness}'.`);
    else if (!KNOWN_HARNESSES.has(harness)) warnings.push(`Harness '${harness}' is custom or unknown; compatibility is not verified.`);
  }

  const skillText = input.skillText;
  if (typeof skillText !== 'string' || skillText.trim() === '') {
    errors.push('Paste the exact SKILL.md text to review; reference-only imports cannot be fetched automatically.');
    return { status: 'content-required', valid: false, errors, warnings, manifest: null };
  }
  if (utf8Size(skillText) > MAX_SKILL_BYTES) errors.push(`SKILL.md exceeds ${MAX_SKILL_BYTES} bytes.`);
  const parsed = parseFrontmatter(skillText);
  errors.push(...parsed.errors);
  warnings.push(...parsed.warnings);
  const name = parsed.fields.name ?? '';
  const description = parsed.fields.description ?? '';
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) || name.length > 64) errors.push('name must follow Agent Skills naming: lowercase letters/digits separated by single hyphens, at most 64 characters.');
  if (!description.trim() || description.length > 1024) errors.push('description is required and must be 1–1024 characters.');
  if (parsed.fields.compatibility && parsed.fields.compatibility.length > 500) errors.push('compatibility must be at most 500 characters.');
  const allowedTools = listFrom(parsed.fields['allowed-tools']);
  const declaredPermissions = uniqueStrings([...allowedTools, ...listFrom(parsed.fields.permissions)], 'declared permissions', errors);
  const declaredCapabilities = uniqueStrings(listFrom(parsed.fields.capabilities ?? parsed.fields['metadata.capabilities']), 'declared capabilities', errors);
  const frontmatterHarnesses = listFrom(parsed.fields['supported-harnesses'] ?? parsed.fields['metadata.supported-harnesses']);
  const supportedHarnesses = uniqueStrings([...requestedHarnesses, ...frontmatterHarnesses], 'supported harnesses', errors);
  for (const harness of supportedHarnesses) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(harness)) errors.push(`Unsupported harness identifier syntax: '${harness}'.`);
    else if (!KNOWN_HARNESSES.has(harness)) warnings.push(`Harness '${harness}' is custom or unknown; compatibility is not verified.`);
  }
  if (allowedTools.length) warnings.push('allowed-tools is experimental in the Agent Skills format; harness support and enforcement vary.');
  const contentSha256 = await sha256Hex(skillText);
  if (errors.length) return { status: 'invalid', valid: false, errors: [...new Set(errors)], warnings: [...new Set(warnings)], manifest: null };

  const immutableFields = Object.freeze({ ...parsed.fields });
  const manifest: LockedSkillManifest = Object.freeze({
    id: `${name}@sha256:${contentSha256.slice(0, 16)}`,
    name,
    description,
    sourceUrl,
    exactRevision,
    contentSha256,
    rawFrontmatter: parsed.raw,
    rawFields: immutableFields,
    compatibility: parsed.fields.compatibility ?? null,
    license: parsed.fields.license ?? null,
    declaredPermissions: Object.freeze(declaredPermissions),
    declaredCapabilities: Object.freeze(declaredCapabilities),
    supportedHarnesses: Object.freeze(supportedHarnesses),
    skillText,
    trustReviewStatus: 'pending-review',
    locked: true,
  });
  return { status: 'pending-review', valid: true, errors: [], warnings: [...new Set(warnings)], manifest };
}
