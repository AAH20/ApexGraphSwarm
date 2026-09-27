'use client';

import { useEffect, useMemo, useState } from 'react';
import styles from './EvaluationLab.module.css';

type Scenario = {
  logicalAgents: number;
  activeWorkerLimit: number;
  observedPeakActive: number;
  taskCount: number;
  completed: number;
  throughputTasksPerSecond: number;
  latencyMs: { queueP50: number; queueP95: number; serviceP50: number; serviceP95: number; endToEndP50: number; endToEndP95: number };
  duplicateCompletions: number;
  restart: { reopened: boolean; persistedCompleted: number; leaseRecoveries: number; staleLeaseFenced: boolean };
  cost: { reservedMicrousd: number; actualMicrousd: number; consistent: boolean; providerCalls: 0 };
};

type Artifact = {
  schemaVersion: 1;
  measuredAt: string;
  classification: 'deterministic_local_queue_fixture';
  note: string;
  provenance: { controlPlane: string; scriptSha256: string; python: string; sqlite: string; platform: string };
  config: { activeWorkerCap: number; tasksPerLogicalAgent: number; fixture: string; providerCalls: 0 };
  scenarios: Scenario[];
  proposedTargets: { label: string; value: string; status: 'unmeasured' }[];
};

type Candidate = { id: string; version: string; name: string; topology: 'star' | 'graph'; graphRouting: boolean; maxWorkers: number; budgetUsd: string; evidence: string };

const seeds: Candidate[] = [
  { id: 'baseline', version: '1.0.0', name: 'Single coordinator baseline', topology: 'star', graphRouting: false, maxWorkers: 1, budgetUsd: 'unknown', evidence: 'Proposed; no model evaluation recorded.' },
  { id: 'graph-swarm', version: '2.0.0', name: 'Graph-routed swarm candidate', topology: 'graph', graphRouting: true, maxWorkers: 10, budgetUsd: 'unknown', evidence: 'Proposed; requires held-out quality and safety evidence.' },
];

function number(value: number | undefined, places = 2) {
  return Number.isFinite(value) ? value!.toFixed(places) : '—';
}

function validArtifact(value: unknown): value is Artifact {
  if (!value || typeof value !== 'object') return false;
  const item = value as Partial<Artifact>;
  return item.schemaVersion === 1 && item.classification === 'deterministic_local_queue_fixture' && Array.isArray(item.scenarios) && !!item.provenance && Array.isArray(item.proposedTargets);
}

export default function EvaluationLab() {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'missing' | 'invalid'>('loading');
  const [selectedId, setSelectedId] = useState('baseline');
  const [plans, setPlans] = useState<Candidate[]>(seeds);
  const selected = plans.find((candidate) => candidate.id === selectedId) || plans[0];
  const [draft, setDraft] = useState<Candidate>(selected);

  useEffect(() => {
    let active = true;
    fetch('/benchmarks/local-swarm.json', { cache: 'no-store' })
      .then(async (response) => {
        if (!response.ok) throw new Error('missing');
        const value: unknown = await response.json();
        if (!validArtifact(value)) throw new Error('invalid');
        if (active) { setArtifact(value); setLoadState('ready'); }
      })
      .catch((error: unknown) => { if (active) setLoadState(error instanceof Error && error.message === 'invalid' ? 'invalid' : 'missing'); });
    return () => { active = false; };
  }, []);

  useEffect(() => { setDraft(selected); }, [selected]);

  const benchmarkPassed = useMemo(() => artifact?.scenarios.length ? artifact.scenarios.every((row) => row.cost.consistent && row.duplicateCompletions === 0 && row.completed === row.taskCount && row.restart.reopened && row.restart.leaseRecoveries === 1 && row.restart.staleLeaseFenced) : false, [artifact]);

  function saveDraft() {
    const [major = 1, minor = 0] = draft.version.split('.').map((part) => Number.parseInt(part, 10));
    const version = `${Number.isFinite(major) ? major : 1}.${(Number.isFinite(minor) ? minor : 0) + 1}.0-draft`;
    const next = { ...draft, id: `draft-${Date.now()}`, version, name: `${draft.name} (draft)`, evidence: 'Draft only. No worker run or held-out evaluation was performed.' };
    setPlans((current) => [...current, next]);
    setSelectedId(next.id);
  }

  return <section className={`${styles.lab} apex-panel`} aria-labelledby="evaluation-title">
    <header className={styles.header}>
      <div><p className="eyebrow">EVALUATION LAB</p><h1 id="evaluation-title">Measure coordination before promotion</h1><p>Compare versioned orchestration plans against isolated, held-out tasks. A local queue fixture measures scheduler behavior; it does not evaluate LLM quality.</p></div>
      <span className={styles.badge}>{artifact ? 'LOCAL FIXTURE' : 'AWAITING FIXTURE'}</span>
    </header>

    <div className={styles.notice} role="note"><strong>Evidence boundary:</strong> any numbers below are deterministic local SQLite queue measurements with zero model-provider calls. They are not proof of multi-agent reasoning quality or simultaneous model capacity. Proposed targets stay labeled unmeasured.</div>

    <div className={styles.grid}>
      <article className={styles.card}>
        <h2>Evaluation parameters</h2>
        {artifact ? <dl className={styles.definitionList}>
          <div><dt>Control plane</dt><dd>{artifact.provenance.controlPlane}</dd></div>
          <div><dt>Logical agents</dt><dd>{artifact.scenarios.map((row) => row.logicalAgents).join(' · ')}</dd></div>
          <div><dt>Active-worker cap</dt><dd>{artifact.config.activeWorkerCap}</dd></div>
          <div><dt>Tasks per logical agent</dt><dd>{artifact.config.tasksPerLogicalAgent}</dd></div>
          <div><dt>Fixture</dt><dd>{artifact.config.fixture}</dd></div>
          <div><dt>Provider calls</dt><dd>0</dd></div>
          <div><dt>Measured at</dt><dd>{new Date(artifact.measuredAt).toLocaleString()}</dd></div>
        </dl> : <p className={styles.muted}>{loadState === 'loading' ? 'Loading the committed benchmark artifact…' : loadState === 'invalid' ? 'The benchmark artifact has an unsupported schema.' : 'No benchmark artifact is available yet. Run the local fixture to populate this panel.'}</p>}
        {artifact && <details className={styles.provenance}><summary>Run provenance</summary><p>{artifact.note}</p><p>Python {artifact.provenance.python} · SQLite {artifact.provenance.sqlite} · {artifact.provenance.platform}</p><code>{artifact.provenance.scriptSha256}</code></details>}
      </article>

      <article className={styles.card}>
        <h2>Versioned candidate plans</h2>
        <label className={styles.label}>Candidate
          <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · v{plan.version}</option>)}</select>
        </label>
        <div className={styles.fields}>
          <label className={styles.label}>Topology<select value={draft.topology} onChange={(event) => setDraft((current) => ({ ...current, topology: event.target.value as Candidate['topology'] }))}><option value="star">Coordinator / star</option><option value="graph">Graph routed</option></select></label>
          <label className={styles.label}>Worker limit<input type="number" min={1} max={64} value={draft.maxWorkers} onChange={(event) => setDraft((current) => ({ ...current, maxWorkers: Math.min(64, Math.max(1, Number(event.target.value) || 1)) }))} /><small>ControlStore currently caps active leases at 64; logical-agent roster size is a separate limit.</small></label>
          <label className={styles.label}>Cost ceiling<input value={draft.budgetUsd} onChange={(event) => setDraft((current) => ({ ...current, budgetUsd: event.target.value }))} maxLength={32} /></label>
        </div>
        <label className={styles.toggle}><input type="checkbox" checked={draft.graphRouting} onChange={(event) => setDraft((current) => ({ ...current, graphRouting: event.target.checked }))} />Use graph-derived task routing (candidate parameter only)</label>
        <p className={styles.muted}>Editing creates a browser-local draft. It is not persisted, executed, or automatically promoted.</p>
        <button className="secondary-button" type="button" onClick={saveDraft}>Create versioned draft</button>
        <p className={styles.evidence}>{selected.evidence}</p>
      </article>
    </div>

    <article className={styles.card}>
      <div className={styles.tableHeader}><div><h2>Queue fixture results</h2><p>Observed scheduler measurements by logical-agent roster size; active concurrency is bounded separately.</p></div><span>{loadState === 'ready' ? 'MEASURED FIXTURE' : 'NOT MEASURED'}</span></div>
      <div className="apex-table-wrap"><table className={styles.table}>
        <thead><tr><th>Logical agents</th><th>Active cap / peak</th><th>Tasks</th><th>Throughput / s</th><th>Queue p50 / p95 ms</th><th>End-to-end p50 / p95 ms</th><th>Duplicate completions</th><th>Restart check</th><th>Cost ledger</th></tr></thead>
        <tbody>{artifact?.scenarios.map((row) => <tr key={row.logicalAgents}>
          <td>{row.logicalAgents}</td><td>{row.activeWorkerLimit} / {row.observedPeakActive}</td><td>{row.completed} / {row.taskCount}</td>
          <td>{number(row.throughputTasksPerSecond)}</td><td>{number(row.latencyMs.queueP50)} / {number(row.latencyMs.queueP95)}</td>
          <td>{number(row.latencyMs.endToEndP50)} / {number(row.latencyMs.endToEndP95)}</td><td>{row.duplicateCompletions}</td>
          <td>{row.restart.reopened ? `reopened · ${row.restart.persistedCompleted} persisted` : 'not verified'}</td>
          <td>{row.cost.consistent ? 'consistent · $0 fixture' : 'mismatch'}</td>
        </tr>) || <tr><td colSpan={9}>{loadState === 'loading' ? 'Loading…' : 'No measured fixture rows.'}</td></tr>}</tbody>
      </table></div>
      {artifact && <p className={styles.fixtureStatus}>{benchmarkPassed ? 'Queue-fixture invariants passed for every recorded row.' : 'One or more queue-fixture invariants are not satisfied; inspect the artifact before relying on these measurements.'}</p>}
    </article>

    <article className={styles.card}>
      <div className={styles.tableHeader}><div><h2>Promotion gates</h2><p>Promotion requires verifier-produced evidence, not UI declarations.</p></div><span className={styles.unmeasured}>HELD OUT · UNMEASURED</span></div>
      <div className="apex-table-wrap"><table className={styles.table}>
        <thead><tr><th>Gate</th><th>Target</th><th>Status</th><th>Evidence required</th></tr></thead>
        <tbody>{(artifact?.proposedTargets || [
          { label: 'Graph correctness', value: '100% schema and reference-valid outputs on deterministic fixtures', status: 'unmeasured' as const },
          { label: 'Permission safety', value: 'Zero successful out-of-scope tool actions', status: 'unmeasured' as const },
          { label: 'Held-out task quality', value: 'Non-inferior to single-agent at equal budget', status: 'unmeasured' as const },
          { label: 'Worker recovery', value: 'At least 99% terminal transitions under fault injection', status: 'unmeasured' as const },
        ]).map((target) => <tr key={target.label}><td>{target.label}</td><td>{target.value}</td><td><span className={styles.unmeasured}>Unmeasured</span></td><td>Independent held-out evaluator artifact and reviewer sign-off</td></tr>)}</tbody>
      </table></div>
      <div className={styles.promotionLock}><button className="secondary-button" type="button" disabled aria-describedby="promotion-lock-reason">Promote candidate</button><p id="promotion-lock-reason" className={styles.muted}>Locked: requires an independently generated held-out report, safety/graph checks, and reviewer sign-off. This UI cannot accept a self-attested checkbox as proof.</p></div>
      <p className={styles.muted}>No automatic promotion endpoint is connected. A local draft cannot represent verification evidence, and a passing SQLite queue run does not clear quality, permission, graph-correctness, or concurrency gates.</p>
    </article>
  </section>;
}
