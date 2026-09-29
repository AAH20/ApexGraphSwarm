/**
 * React component for graph workspace enhanced.
 *
 * @module GraphWorkspaceEnhanced
 * @packageDocumentation
 */
'use client';

import { useState, useEffect, useMemo, useCallback, useRef, useDeferredValue } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import {
  Maximize2, Minimize2, Network, Search, Upload, Download, ArrowUpRight,
  ChevronRight, SlidersHorizontal, Info, FileCode2, Layers, Code2, Link2,
  Focus, RotateCcw, GitBranch, AlertTriangle, CheckCircle2, Workflow, X,
  FolderOpen, Route, Users, Zap, Clock, GitCommit, Boxes, Eye, EyeOff,
  ChevronDown, ChevronUp, Copy, Check, Filter, BarChart3, PieChart,
} from 'lucide-react';
import AppShell from './AppShell';
import SwarmPanel from './SwarmPanel';
import IntegrationsPanel from './IntegrationsPanel';
import { useGraphFullscreen } from './useGraphFullscreen';
import GraphStorePanel from './GraphStorePanel';
import {
  type Snapshot, type Filters, type GraphNode, type GraphEdge,
  parseSnapshot, indexGraph, filterGraph, shortestPath, semanticEdges,
  downloadJSON, LIMITS,
} from '@/lib/graph';
import { neo4jBundle } from '@/lib/neo4j-export';

const GraphCanvasEnhanced = dynamic(() => import('./GraphCanvasEnhanced'), {
  ssr: false,
  loading: () => <div className="canvas-loading"><Network size={32} /><span>Preparing the graph renderer…</span></div>,
});

const initialFilters: Filters = {
  query: '', kind: 'all', relation: 'all', evidence: 'all',
  directory: 'all', view: 'modules', focus: null, hops: 1, direction: 'both',
};

const COLORS: Record<string, string> = {
  module: '#8493ff', file: '#53c5ad', function: '#70a8ff',
  class: '#f2bf68', external: '#9ba6b8',
};

const COMMUNITY_PALETTE = [
  '#8493ff', '#53c5ad', '#70a8ff', '#f2bf68', '#e879f9',
  '#fb923c', '#34d399', '#f472b6', '#a78bfa', '#fbbf24',
];

/**
 * Function NodeIcon.
 *
 * @param {{ kind}  kind  - Description of  kind .
 *
 * @example
 * ```typescript
 * const result = NodeIcon(...);
 * ```
 */
function NodeIcon({ kind }: { kind: string }) {
  return kind === 'module' ? <Layers size={15} /> : kind === 'file' ? <FileCode2 size={15} /> : <Code2 size={15} />;
}

/**
 * React component GraphWorkspaceEnhanced.
 *
 * @param {{ embedded?}  embedded = false  - Description of  embedded = false .
 *
 * @example
 * ```typescript
 * const result = GraphWorkspaceEnhanced(...);
 * ```
 */
export default function GraphWorkspaceEnhanced({ embedded = false }: { embedded?: boolean }) {
  // ─── State ─────────────────────────────────────────────────────────────
  const [graph, setGraph] = useState<Snapshot | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [source, setSource] = useState('Prepared project snapshot');
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [selected, setSelected] = useState<string | null>(null);
  const [layout, setLayout] = useState<'grouped' | 'force' | 'circular'>('grouped');
  const [inspectorTab, setInspectorTab] = useState<'node' | 'constraints'>('node');
  const [listOpen, setListOpen] = useState(false);
  const [searchAll, setSearchAll] = useState('');
  const [canvasStatus, setCanvasStatus] = useState({ renderer: 'Starting', layoutRunning: false, visible: 0 });
  const [report, setReport] = useState<unknown>(null);
  const [target, setTarget] = useState('');
  const [path, setPath] = useState<string[]>([]);
  const [pathStatus, setPathStatus] = useState('');

  // Enhanced features
  const [showCommunities, setShowCommunities] = useState(false);
  const [showCentrality, setShowCentrality] = useState(false);
  const [showMinimap, setShowMinimap] = useState(true);
  const [showSearch, setShowSearch] = useState(true);
  const [showExport, setShowExport] = useState(true);
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const [multiSelect, setMultiSelect] = useState(false);
  const [selectedMulti, setSelectedMulti] = useState<string[]>([]);
  const [showFeaturePanel, setShowFeaturePanel] = useState(false);

  const fileInput = useRef<HTMLInputElement>(null);
  const graphSection = useRef<HTMLElement>(null);
  const generation = useRef(0);
  const query = useDeferredValue(filters.query);
  const fullscreen = useGraphFullscreen(graphSection);

  // ─── Data loading ──────────────────────────────────────────────────────
  const accept = useCallback((raw: unknown, label: string) => {
    const value = parseSnapshot(raw);
    generation.current++;
    setGraph(value);
    setSource(label);
    setFilters(initialFilters);
    setSelected(value.nodes.find(n => n.path === 'play_anything' && n.kind === 'module')?.id || value.nodes.find(n => n.kind === 'module')?.id || null);
    setPath([]);
    setPathStatus('');
    setReport(null);
    setError('');
    setNotice(`Loaded ${value.name}. Evidence and limitations travel with this snapshot.`);
  }, []);

  useEffect(() => {
    const abort = new AbortController();
    const requestGeneration = generation.current;
    fetch('/repository-graph.json', { signal: abort.signal })
      .then(r => {
        if (!r.ok) throw Error('Prepared snapshot unavailable. Run npm run assets or import an exported graph.');
        return r.json();
      })
      .then(raw => {
        if (requestGeneration === generation.current) accept(raw, 'Prepared project snapshot');
      })
      .catch(e => {
        if (!abort.signal.aborted) setError(e.message);
      });
    return () => abort.abort();
  }, [accept]);

  useEffect(() => {
    if (!embedded) return;
    const receive = (e: MessageEvent) => {
      if (e.origin !== location.origin || e.source !== window.parent || e.data?.type !== 'play-graph-snapshot') return;
      try { accept(e.data.graph, 'Embedded repository'); } catch (err) { setError(String(err)); }
    };
    window.addEventListener('message', receive);
    window.parent.postMessage({ type: 'play-graph-ready' }, location.origin);
    return () => window.removeEventListener('message', receive);
  }, [embedded, accept]);

  // ─── Derived data ──────────────────────────────────────────────────────
  const index = useMemo(() => graph ? indexGraph(graph) : null, [graph]);
  const filtered = useMemo(() => graph ? filterGraph(graph, { ...filters, query }) : { nodes: [], edges: [], matching: 0, capped: false, matchingEdges: 0, edgeCapped: false }, [graph, filters, query]);
  const directories = useMemo(() => graph?.nodes.filter(n => n.kind === 'module').map(n => n.path).sort() || [], [graph]);
  const relations = useMemo(() => [...new Set(graph?.edges.map(e => e.relation) || [])].sort(), [graph]);
  const selectedNode = selected ? index?.nodes.get(selected) : undefined;
  const links = useMemo(() => selected && index ? [...(index.out.get(selected) || []).map(e => ({ ...e, direction: 'out' as const })), ...(index.incoming.get(selected) || []).map(e => ({ ...e, direction: 'in' as const }))] : [], [index, selected]);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const n of graph?.nodes || []) c[n.kind] = (c[n.kind] || 0) + 1;
    return c;
  }, [graph]);
  const searchResults = useMemo(() => {
    const q = searchAll.trim().toLowerCase();
    return q && graph ? graph.nodes.filter(n => (n.name + ' ' + n.path).toLowerCase().includes(q)).slice(0, 30) : [];
  }, [graph, searchAll]);

  // ─── Actions ───────────────────────────────────────────────────────────
  const inspect = useCallback((id: string) => { setSelected(id); setInspectorTab('node'); }, []);
  const navigateNode = useCallback((id: string) => {
    setSelected(id);
    setInspectorTab('node');
    setFilters({ ...initialFilters, view: 'all', focus: id });
    setSearchAll('');
    setPath([]);
    setPathStatus('');
    graphSection.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);
  const patch = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPath([]);
    setPathStatus('');
  };

  async function importFile(file: File | undefined) {
    if (!file) return;
    try {
      if (file.size > LIMITS.bytes) throw Error('Snapshot exceeds the 15 MB import limit.');
      accept(JSON.parse(await file.text()), `Imported · ${file.name}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid graph snapshot');
    } finally {
      if (fileInput.current) fileInput.current.value = '';
    }
  }

  function trace() {
    if (!graph || !selected || !target) return;
    const result = shortestPath({ ...graph, edges: semanticEdges(graph, filters.evidence) }, selected, target);
    if (result.length > LIMITS.visible) {
      setPath([]);
      setPathStatus(`Found ${result.length - 1} directed hops, exceeding the ${LIMITS.visible}-node render budget. Inspect smaller neighborhoods or export the snapshot.`);
      return;
    }
    setPath(result);
    setPathStatus(result.length ? `${result.length - 1} directed semantic hops. This path uses the full snapshot and current evidence policy; inventory edges are excluded.` : 'No resolved directed semantic path found. Unresolved calls may hide dependencies.');
  }

  const rendered = useMemo(() => {
    if (!path.length || !graph) return filtered;
    const ids = new Set(path);
    const pairs = new Set(path.slice(0, -1).map((id, i) => JSON.stringify([id, path[i + 1]])));
    const edges = semanticEdges(graph, filters.evidence).filter(e => pairs.has(JSON.stringify([e.source, e.target])));
    return {
      nodes: graph.nodes.filter(n => ids.has(n.id)),
      edges: edges.slice(0, LIMITS.visibleEdges),
      matching: path.length,
      capped: false,
      matchingEdges: edges.length,
      edgeCapped: edges.length > LIMITS.visibleEdges,
    };
  }, [filtered, path, graph, filters.evidence]);

  const integrationView = useMemo(() => graph ? {
    version: graph.version,
    name: graph.name + " · filtered view",
    nodes: rendered.nodes,
    edges: rendered.edges,
    truncated: true,
    warnings: [...graph.warnings, "Filtered view only; omitted nodes and unresolved references are not represented."],
  } : null, [graph, rendered]);

  // ─── Render ────────────────────────────────────────────────────────────
  const body = (
    <>
      <header className="topbar">
        <div>
          <span className="workspace-avatar">AX</span>
          <span>WORKSPACE <span className="breadcrumb-divider">/</span> Graph Studio</span>
        </div>
        <div className="topbar-right">
          <span className="pill"><span className="live-dot" />Source-grounded workspace</span>
          <a href="#integrations">Run integrations <ArrowUpRight size={13} /></a>
          <a href="/swarm">Swarm control <ArrowUpRight size={13} /></a>
        </div>
      </header>

      <div className="page-content">
        <section className="page-heading">
          <div>
            <span className="eyebrow">REPOSITORY INTELLIGENCE, AT EVERY LEVEL</span>
            <h1>See the system.<span> Find your next move.</span></h1>
            <p>Explore the code. Follow its relationships. Let a coordinated team help you reason through the evidence.</p>
          </div>
          <div className="heading-actions">
            <input ref={fileInput} className="visually-hidden" type="file" accept=".json,application/json" aria-label="Import graph snapshot" onChange={e => importFile(e.target.files?.[0])} />
            <button className="secondary-button" onClick={() => fileInput.current?.click()}><Upload size={15} />Import graph</button>
            <details className="export-menu">
              <summary className="secondary-button"><Download size={15} />Export</summary>
              <div>
                <button disabled={!graph} onClick={() => graph && downloadJSON('repository-graph.json', graph)}>Full graph snapshot</button>
                <button disabled={!report} onClick={() => downloadJSON('graph-analysis.json', report)}>Latest analysis report</button>
                <button disabled={!graph} onClick={async () => { if (graph) { try { downloadJSON('neo4j-import-bundle.json', await neo4jBundle(graph)); setNotice('Neo4j bundle exported. No database connection or import was performed.'); } catch (e) { setError(String(e)); } } }}>Neo4j import bundle</button>
              </div>
            </details>
          </div>
        </section>

        {error && <div className="message error-message" role="alert"><AlertTriangle size={17} /><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}><X size={14} /></button></div>}

        <div className="repository-bar">
          <div className="repo-icon"><GitBranch size={20} /></div>
          <div>
            <strong>{graph?.name || 'Loading repository…'}</strong>
            <span>{source} · {graph?.truncated ? 'Partial inventory' : 'Indexed snapshot'}</span>
          </div>
          <div className="repo-stats">
            <span><b>{counts.file || 0}</b> files</span>
            <span><b>{counts.function || 0}</b> functions</span>
            <span><b>{graph?.edges.length.toLocaleString() || 0}</b> relationships</span>
          </div>
        </div>

        <div className="notice-line" role="status"><CheckCircle2 size={12} />{notice || 'Loading a prepared snapshot; source code is never executed by this explorer.'}</div>

        <GraphStorePanel graph={graph} onLoad={accept} />

        {/* Feature toggles bar */}
        <div style={{
          display: 'flex', gap: 8, padding: '8px 0', flexWrap: 'wrap',
          borderBottom: '1px solid rgba(184,199,222,0.12)', marginBottom: 12,
        }}>
          <button
            onClick={() => setShowFeaturePanel(!showFeaturePanel)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px',
              borderRadius: 6, border: '1px solid rgba(184,199,222,0.24)',
              background: showFeaturePanel ? 'rgba(132,147,255,0.15)' : 'transparent',
              color: showFeaturePanel ? '#b4c5ff' : '#71829d', fontSize: 12, cursor: 'pointer',
            }}
          >
            <Zap size={14} /> Enhanced Features {showFeaturePanel ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {[
            { label: 'Communities', value: showCommunities, set: setShowCommunities, icon: <Users size={12} /> },
            { label: 'Centrality', value: showCentrality, set: setShowCentrality, icon: <BarChart3 size={12} /> },
            { label: 'Minimap', value: showMinimap, set: setShowMinimap, icon: <Eye size={12} /> },
            { label: 'Search', value: showSearch, set: setShowSearch, icon: <Search size={12} /> },
            { label: 'Edge Labels', value: showEdgeLabels, set: setShowEdgeLabels, icon: <Link2 size={12} /> },
            { label: 'Multi-Select', value: multiSelect, set: setMultiSelect, icon: <Boxes size={12} /> },
          ].map((t) => (
            <button
              key={t.label}
              onClick={() => t.set(!t.value)}
              style={{
                display: 'flex', alignItems: 'center', gap: 4, padding: '6px 10px',
                borderRadius: 6, fontSize: 12, cursor: 'pointer',
                border: `1px solid ${t.value ? '#8493ff' : 'rgba(184,199,222,0.24)'}`,
                background: t.value ? 'rgba(132,147,255,0.15)' : 'transparent',
                color: t.value ? '#b4c5ff' : '#71829d',
              }}
            >
              {t.icon} {t.label}
            </button>
          ))}
          {multiSelect && selectedMulti.length > 0 && (
            <span style={{ fontSize: 12, color: '#b4c5ff', display: 'flex', alignItems: 'center' }}>
              {selectedMulti.length} selected
            </span>
          )}
        </div>

        <section className={`graph-workbench${fullscreen.expanded ? ' is-fullscreen' : ''}`} ref={graphSection} aria-label="Repository graph explorer">
          <div className="graph-toolbar">
            <div className="view-tabs" role="group" aria-label="Graph detail level">
              {(['modules', 'files', 'symbols', 'all'] as const).map(view => (
                <button key={view} aria-pressed={filters.view === view && !filters.focus} onClick={() => { setFilters(prev => ({ ...prev, view, focus: null })); setPath([]); setPathStatus(''); }}>
                  {view === 'all' ? 'All kinds' : view[0].toUpperCase() + view.slice(1)}
                </button>
              ))}
            </div>
            <div className="graph-search">
              <Search size={15} />
              <input aria-label="Filter graph by name or path" value={filters.query} onChange={e => patch('query', e.target.value)} placeholder="Filter nodes, paths, functions…" />
              {filters.query && <button aria-label="Clear graph search" onClick={() => patch('query', '')}><X size={13} /></button>}
            </div>
            <button className="icon-button" data-fullscreen-toggle aria-label={fullscreen.expanded ? 'Exit graph fullscreen' : 'Open graph fullscreen'} title={fullscreen.expanded ? 'Exit fullscreen (Esc)' : 'Fullscreen graph'} aria-pressed={fullscreen.expanded} onClick={() => void fullscreen.toggle()}>
              {fullscreen.expanded ? <Minimize2 size={17} /> : <Maximize2 size={17} />}
            </button>
            <button className="icon-button" title="Reset all filters" aria-label="Reset all graph filters" onClick={() => { setFilters(initialFilters); setPath([]); setPathStatus(''); }}>
              <RotateCcw size={16} />
            </button>
          </div>

          <div className="graph-grid">
            <aside className="filter-panel">
              <div className="panel-heading"><SlidersHorizontal size={14} /><strong>Refine the view</strong></div>
              <label>Relationship
                <select value={filters.relation} onChange={e => patch('relation', e.target.value)}>
                  <option value="all">All relationships</option>
                  {relations.map(r => <option key={r}>{r}</option>)}
                </select>
              </label>
              <label>Evidence
                <select value={filters.evidence} onChange={e => patch('evidence', e.target.value)}>
                  <option value="all">All evidence levels</option>
                  <option value="grounded">Parsed / observed only</option>
                  <option value="inferred">Inferred only</option>
                  <option value="illustrative">Illustrative sample</option>
                </select>
              </label>
              <label>Node type
                <select value={filters.kind} onChange={e => patch('kind', e.target.value)}>
                  <option value="all">All node types</option>
                  {['module', 'file', 'function', 'class', 'external'].map(k => <option key={k}>{k}</option>)}
                </select>
              </label>
              <label>Directory
                <select value={filters.directory} onChange={e => patch('directory', e.target.value)}>
                  <option value="all">Whole repository</option>
                  {directories.map(p => <option key={p} value={p}>{p === '.' ? 'Root files' : p}</option>)}
                </select>
              </label>
              <div className="filter-divider" />
              <label>Layout
                <select value={layout} onChange={e => setLayout(e.target.value as 'grouped' | 'force' | 'circular')}>
                  <option value="grouped">Grouped · stable</option>
                  <option value="force">Force · background worker</option>
                  <option value="circular">Circular · radial</option>
                </select>
              </label>
              <label>Neighborhood depth
                <select value={filters.hops} onChange={e => patch('hops', Number(e.target.value))}>
                  {[1, 2, 3, 4].map(n => <option key={n} value={n}>{n} {n === 1 ? 'hop' : 'hops'}</option>)}
                </select>
              </label>
              <label>Direction
                <select value={filters.direction} onChange={e => patch('direction', e.target.value as Filters['direction'])}>
                  <option value="both">Both directions</option>
                  <option value="out">Outgoing dependencies</option>
                  <option value="in">Incoming dependents</option>
                </select>
              </label>
              <button className="focus-button" disabled={!selected} onClick={() => selected && setFilters(prev => ({ ...prev, focus: prev.focus === selected ? null : selected }))}>
                {filters.focus === selected ? 'Clear focus' : 'Focus neighborhood'}
              </button>
            </aside>

            <div className="graph-center">
              <div className="canvas-header">
                <span><span className="live-dot" />{filters.focus ? 'FOCUSED NEIGHBORHOOD' : path.length ? 'DEPENDENCY PATH' : 'REPOSITORY EXPLORER'}</span>
                <span>{rendered.nodes.length} nodes · {rendered.edges.length} links</span>
              </div>
              <div className="graph-canvas">
                {graph ? (
                  <GraphCanvasEnhanced
                    nodes={rendered.nodes}
                    edges={rendered.edges}
                    selected={selected}
                    onSelect={inspect}
                    layout={layout}
                    onStatus={setCanvasStatus}
                    showCommunities={showCommunities}
                    showCentrality={showCentrality}
                    showMinimap={showMinimap}
                    showSearch={showSearch}
                    showExport={showExport}
                    showEdgeLabels={showEdgeLabels}
                    showLegend={true}
                    multiSelect={multiSelect}
                    onMultiSelect={setSelectedMulti}
                  />
                ) : (
                  <div className="canvas-loading"><Network size={30} /><span>Loading source relationships…</span></div>
                )}
                {!rendered.nodes.length && graph && (
                  <div className="canvas-empty">
                    <Search size={28} />
                    <h3>No matching nodes</h3>
                    <p>Try a broader detail level or clear a filter.</p>
                    <button className="secondary-button" onClick={() => setFilters(initialFilters)}>Reset view</button>
                  </div>
                )}
              </div>
              <div className="canvas-footer">
                <div className="graph-legend">
                  {Object.entries(COLORS).map(([kind, color]) => (
                    <span key={kind}><i style={{ background: color }} />{kind}</span>
                  ))}
                </div>
                <span>{canvasStatus.layoutRunning ? 'Layout worker running…' : canvasStatus.renderer}</span>
              </div>
              <div className="scope-note">
                {rendered.edgeCapped && `Showing 12,000 of ${rendered.matchingEdges.toLocaleString()} eligible links. Narrow the filters to inspect omitted links. `}
                {rendered.capped ? `Showing the first ${LIMITS.visible.toLocaleString()} of ${rendered.matching.toLocaleString()} matches. Narrow the view or inspect a neighborhood.` : 'Arrows show relationship direction. Visual proximity is not a dependency.'}
              </div>
            </div>

            <aside className="inspector">
              <div className="inspector-tabs">
                <button aria-pressed={inspectorTab === 'node'} onClick={() => setInspectorTab('node')}>Inspector</button>
                <button aria-pressed={inspectorTab === 'constraints'} onClick={() => setInspectorTab('constraints')}>Constraints <Info size={12} /></button>
              </div>
              {inspectorTab === 'node' ? (
                selectedNode ? (
                  <>
                    <div className="node-title">
                      <span style={{ color: COLORS[selectedNode.kind] }}><NodeIcon kind={selectedNode.kind} />{selectedNode.kind}</span>
                      <h2>{selectedNode.name}</h2>
                      <code>{selectedNode.path}{selectedNode.line ? ':' + selectedNode.line : ''}</code>
                    </div>
                    <span className={'evidence-badge ' + selectedNode.confidence}>{selectedNode.confidence} evidence</span>
                    <p className="node-summary">{selectedNode.summary}</p>
                    <Link className="secondary-button" href={`/teams#source=${encodeURIComponent(JSON.stringify({ id: selectedNode.id, label: selectedNode.name.slice(0, 200), repository: graph?.name || 'repository' }))}`}>
                      Assign a specialist swarm →
                    </Link>
                    <div className="node-metrics">
                      <div><strong>{index?.incoming.get(selectedNode.id)?.length || 0}</strong><span>Incoming</span></div>
                      <div><strong>{index?.out.get(selectedNode.id)?.length || 0}</strong><span>Outgoing</span></div>
                    </div>
                    <div className="inspector-subheading">RELATIONSHIPS <span>{links.length}</span></div>
                    <div className="relationship-list">
                      {links.slice(0, 30).map((edge, i) => {
                        const id = edge.direction === 'out' ? edge.target : edge.source;
                        return (
                          <button key={i} onClick={() => navigateNode(id)}>
                            <span>{edge.direction === 'out' ? '↗' : '↙'} {edge.relation}<small>{edge.confidence}</small></span>
                            <strong>{index?.nodes.get(id)?.name || id}</strong>
                            <ChevronRight size={12} />
                          </button>
                        );
                      })}
                      {!links.length && <p className="help-text">No indexed relationships. This does not rule out dynamic dependencies.</p>}
                    </div>
                    {links.length > 30 && <p className="help-text">First 30 shown. Export preserves the full graph.</p>}
                  </>
                ) : (
                  <div className="empty-inspector">
                    <Focus size={26} />
                    <h3>Follow a connection.</h3>
                    <p>Select a node to inspect its summary, source location, and relationships.</p>
                  </div>
                )
              ) : (
                <div className="constraints-panel">
                  <h3>Coverage & limits</h3>
                  <p className="help-text">This snapshot is a static index of the repository. It does not execute code, resolve dynamic imports, or guarantee completeness.</p>
                  <div className="constraint-stats">
                    <div><strong>{graph?.nodes.length.toLocaleString() || 0}</strong><span>Nodes indexed</span></div>
                    <div><strong>{graph?.edges.length.toLocaleString() || 0}</strong><span>Relationships</span></div>
                    <div><strong>{graph?.warnings?.length || 0}</strong><span>Warnings</span></div>
                  </div>
                  {graph && graph.warnings.length > 0 && (
                    <div className="warning-list">
                      <strong>Warnings</strong>
                      {graph.warnings.slice(0, 10).map((w, i) => <p key={i}>{w}</p>)}
                    </div>
                  )}
                  <div className="constraint-note">
                    <strong>Limits</strong>
                    <ul>
                      <li>Max {LIMITS.nodes.toLocaleString()} nodes</li>
                      <li>Max {LIMITS.edges.toLocaleString()} edges</li>
                      <li>Max {LIMITS.visible.toLocaleString()} visible nodes</li>
                      <li>Max {LIMITS.visibleEdges.toLocaleString()} visible edges</li>
                    </ul>
                  </div>
                </div>
              )}
            </aside>
          </div>

          <div className="graph-bottom-bar">
            <button className="text-button" onClick={() => setListOpen(!listOpen)} aria-expanded={listOpen}>
              <Layers size={14} />{listOpen ? 'Hide' : 'Open'} accessible node list
            </button>
            <span>Inspect relationships, not just a picture.</span>
            <button className="text-button" onClick={() => setInspectorTab('constraints')}>Coverage & limits <ArrowUpRight size={13} /></button>
          </div>

          {listOpen && (
            <div className="accessible-list">
              <label>Search every indexed node
                <input value={searchAll} onChange={e => setSearchAll(e.target.value)} placeholder="Search the full snapshot…" />
              </label>
              <div>
                {(searchAll ? searchResults : filtered.nodes.slice(0, 40)).map(n => (
                  <button key={n.id} onClick={() => navigateNode(n.id)}>
                    <NodeIcon kind={n.kind} />
                    <span>{n.name}<small>{n.path}{n.line ? ':' + n.line : ''}</small></span>
                    <ArrowUpRight size={13} />
                  </button>
                ))}
              </div>
              <p className="help-text">Showing up to {searchAll ? 30 : 40} results. Refine the search for other indexed nodes.</p>
            </div>
          )}
        </section>

        <section className="path-section">
          <div>
            <Route size={18} />
            <strong>Trace a dependency path</strong>
            <span>Directed semantic edges; destination menu shows the first 1,000 non-module nodes.</span>
          </div>
          <label className="visually-hidden" htmlFor="path-target">Path destination</label>
          <select id="path-target" value={target} onChange={e => setTarget(e.target.value)}>
            <option value="">Choose a destination…</option>
            {graph?.nodes.filter(n => n.kind !== 'module').slice(0, 1000).map(n => <option key={n.id} value={n.id}>{n.name} · {n.path}</option>)}
          </select>
          <button className="secondary-button" disabled={!selected || !target} onClick={trace}>Trace path</button>
          {path.length > 0 && <button className="text-button" onClick={() => { setPath([]); setPathStatus(''); }}>Clear path</button>}
          {pathStatus && <p role="status">{pathStatus}</p>}
        </section>

        {graph && <SwarmPanel graph={graph} onSelect={navigateNode} onReport={setReport} />}
        {graph && <IntegrationsPanel graph={graph} viewGraph={integrationView || undefined} />}

        <footer className="workspace-footer">
          <span><Network size={13} />Built to make complex code understandable.</span>
          <a href="mailto:aah@a2zsoc.com">Need an experienced guide? <ArrowUpRight size={12} /></a>
        </footer>
      </div>
    </>
  );

  return embedded ? <div className="embedded-workspace">{body}</div> : <AppShell>{body}</AppShell>;
}
