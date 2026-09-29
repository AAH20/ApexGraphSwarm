/**
 * React component for scope topology.
 *
 * @module ScopeTopology
 * @packageDocumentation
 */
'use client';

import { useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from 'react';
import styles from './ScopeTopology.module.css';

export type ScopeTopologyNode = {
  id: string;
  label: string;
  kind: string;
  parentId: string | null;
  teamIds: readonly string[];
  externalRef: string;
};
export type ScopeTopologyProps = {
  nodes: readonly ScopeTopologyNode[];
  selectedId: string;
  onSelect: (id: string) => void;
};

const MAX_DIAGRAM_CHILDREN = 40;
const PAGE_SIZE = 40;
const WIDTH = 960;
const CARD_W = 164;
const CARD_H = 58;
const MAX_COLS = 5;
const MIN_GAP_X = 20;
const MAX_GAP_X = 32;
const GAP_Y = 82;
const START_Y = 186;
const colors: Record<string, string> = {
  workspace: '#6676d8', repository: '#438c75', repo: '#438c75', module: '#3d8fa5',
  swarm: '#a666a6', team: '#c17a3b', datacenter: '#456b9a', rack: '#3b837f',
  fleet: '#8a7035', device: '#555f70', iot: '#408273', 'iot-center': '#408273',
};
const colorFor = (kind: string) => colors[kind.trim().toLowerCase()] ?? '#607184';
const compact = (value: string, max = 22) => value.length > max ? `${value.slice(0, max - 1)}…` : value;
const compareNodes = (a: ScopeTopologyNode, b: ScopeTopologyNode) =>
  a.label < b.label ? -1 : a.label > b.label ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0;

/**
 * React component ScopeTopology.
 *
 * @param {ScopeTopologyProps}  nodes, selectedId, onSelect  - Description of  nodes, selectedId, onSelect .
 *
 * @example
 * ```typescript
 * const result = ScopeTopology(...);
 * ```
 */
export default function ScopeTopology({ nodes, selectedId, onSelect }: ScopeTopologyProps) {
  const [focusedId, setFocusedId] = useState(selectedId);
  const [zoom, setZoom] = useState(1);
  const [search, setSearch] = useState('');
  const [listPage, setListPage] = useState(0);
  const [containerWidth, setContainerWidth] = useState(0);
  const viewportRef = useRef<HTMLDivElement>(null);


  const nodeIndex = useMemo(() => {
    const result = new Map<string, ScopeTopologyNode>();
    for (const node of nodes) if (node.id.trim() && !result.has(node.id)) result.set(node.id, node);
    return result;
  }, [nodes]);
  const allNodes = useMemo(() => [...nodeIndex.values()], [nodeIndex]);
  const roots = useMemo(() => allNodes.filter((node) => !node.parentId || !nodeIndex.has(node.parentId)), [allNodes, nodeIndex]);
  const fallbackId = roots[0]?.id ?? allNodes[0]?.id ?? '';
  useEffect(() => {
    const element = viewportRef.current;
    if (!element) return;
    const updateWidth = (width = element.clientWidth) => {
      const next = Math.max(320, Math.floor(width));
      setContainerWidth((current) => current === next ? current : next);
    };
    updateWidth();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width !== undefined) updateWidth(width);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [allNodes.length > 0]);

  useEffect(() => setFocusedId(nodeIndex.has(selectedId) ? selectedId : fallbackId), [fallbackId, nodeIndex, selectedId]);
  useEffect(() => setZoom(1), [focusedId]);

  const focused = nodeIndex.get(focusedId) ?? nodeIndex.get(fallbackId);
  const children = useMemo(() => focused
    ? allNodes.filter((node) => node.parentId === focused.id).sort(compareNodes)
    : [], [allNodes, focused]);
  const visibleChildren = children.slice(0, MAX_DIAGRAM_CHILDREN);
  const diagramWidth = containerWidth || WIDTH;
  const columns = Math.max(1, Math.min(MAX_COLS, Math.floor((diagramWidth - 24 + MIN_GAP_X) / (CARD_W + MIN_GAP_X))));
  const gapX = columns === 1 ? 0 : Math.max(MIN_GAP_X, Math.min(MAX_GAP_X, (diagramWidth - CARD_W * columns - 24) / (columns - 1)));
  const childStartX = (diagramWidth - (CARD_W * columns + gapX * (columns - 1))) / 2 + CARD_W / 2;
  const rows = Math.max(1, Math.ceil(visibleChildren.length / columns));
  const height = START_Y + rows * GAP_Y + 30;
  const crumbs = useMemo(() => {
    const chain: ScopeTopologyNode[] = [];
    const seen = new Set<string>();
    let current = focused;
    while (current && !seen.has(current.id)) {
      seen.add(current.id);
      chain.unshift(current);
      current = current.parentId ? nodeIndex.get(current.parentId) : undefined;
    }
    return chain;
  }, [focused, nodeIndex]);

  const matches = useMemo(() => {
    const q = search.trim().toLocaleLowerCase();
    return allNodes.filter((node) => !q || `${node.label} ${node.kind} ${node.externalRef}`.toLocaleLowerCase().includes(q))
      .sort(compareNodes);
  }, [allNodes, search]);
  const pages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
  const page = Math.min(listPage, pages - 1);
  const listed = matches.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const select = (id: string) => { setFocusedId(id); onSelect(id); };
  const adjustZoom = (delta: number) => setZoom((value) => Math.min(1.8, Math.max(0.7, Number((value + delta).toFixed(2)))));
  const activateByKey = (event: KeyboardEvent<SVGGElement>, id: string) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(id); }
  };

  if (!allNodes.length) return <section className={styles.root} aria-label="Scope topology"><p className={styles.empty}>Add a scope node to see its hierarchy here.</p></section>;

  return <section className={styles.root} aria-label="Scope topology designer">
    <div className={styles.toolbar}>
      <nav className={styles.breadcrumb} aria-label="Scope hierarchy breadcrumb">
        {crumbs.map((node, index) => <span className={styles.crumbItem} key={node.id}>
          {index > 0 && <span className={styles.separator} aria-hidden="true">/</span>}
          <button type="button" className={styles.crumbButton} aria-current={index === crumbs.length - 1 ? 'location' : undefined} onClick={() => select(node.id)}>{compact(node.label, 28)}</button>
        </span>)}
      </nav>
      <div className={styles.zoom} role="group" aria-label="Topology zoom controls">
        <button type="button" onClick={() => adjustZoom(-0.15)} disabled={zoom <= 0.7} aria-label="Zoom out">−</button>
        <span aria-live="polite">{Math.round(zoom * 100)}%</span>
        <button type="button" onClick={() => adjustZoom(0.15)} disabled={zoom >= 1.8} aria-label="Zoom in">+</button>
        <button type="button" onClick={() => setZoom(1)} disabled={zoom === 1}>Reset</button>
      </div>
    </div>
    <p className={styles.caption}>Focused scope: <strong>{focused?.label}</strong><span>{visibleChildren.length} of {children.length} direct children shown</span></p>

    {focused ? <div ref={viewportRef} className={styles.viewport}>
      <svg className={styles.diagram} viewBox={`0 0 ${diagramWidth} ${height}`} role="group" aria-label={`Hierarchy centered on ${focused.label}; ${visibleChildren.length} child scopes`}>
        <g transform={`translate(${diagramWidth / 2} 120) scale(${zoom}) translate(${-diagramWidth / 2} -120)`}>
          {visibleChildren.map((node, index) => {
            const x = childStartX + (index % columns) * (CARD_W + gapX);
            const y = START_Y + Math.floor(index / columns) * GAP_Y;
            return <path key={`link-${node.id}`} className={styles.edge} d={`M ${diagramWidth / 2} 106 V 148 H ${x} V ${y - CARD_H / 2}`} aria-hidden="true" />;
          })}
          <g className={`${styles.node} ${styles.focusNode} ${focused.id === selectedId ? styles.selected : ''}`} role="button" tabIndex={0}
            aria-label={`${focused.label}, ${focused.kind}, focused scope, ${focused.teamIds.length} assigned teams`} aria-pressed={focused.id === selectedId}
            onClick={() => select(focused.id)} onKeyDown={(event) => activateByKey(event, focused.id)} style={{ '--accent': colorFor(focused.kind) } as CSSProperties}>
            <title>{`${focused.label} · ${focused.kind} · ${focused.teamIds.length} assigned teams`}</title>
            <rect x={diagramWidth / 2 - CARD_W / 2} y={48} width={CARD_W} height={CARD_H} rx={11} />
            <text className={styles.label} x={diagramWidth / 2} y={71} textAnchor="middle">{compact(focused.label)}</text>
            <text className={styles.meta} x={diagramWidth / 2} y={91} textAnchor="middle">{focused.kind} · {focused.teamIds.length} teams</text>
          </g>
          {visibleChildren.map((node, index) => {
            const x = childStartX + (index % columns) * (CARD_W + gapX);
            const y = START_Y + Math.floor(index / columns) * GAP_Y;
            const selected = node.id === selectedId;
            return <g key={node.id} className={`${styles.node} ${selected ? styles.selected : ''}`} role="button" tabIndex={0}
              aria-label={`${node.label}, ${node.kind}, ${node.teamIds.length} assigned teams${selected ? ', selected' : ''}`} aria-pressed={selected}
              onClick={() => select(node.id)} onKeyDown={(event) => activateByKey(event, node.id)} style={{ '--accent': colorFor(node.kind) } as CSSProperties}>
              <title>{`${node.label} · ${node.kind} · ${node.teamIds.length} assigned teams${node.externalRef ? ` · ${node.externalRef}` : ''}`}</title>
              <rect x={x - CARD_W / 2} y={y - CARD_H / 2} width={CARD_W} height={CARD_H} rx={10} />
              <text className={styles.label} x={x} y={y - 4} textAnchor="middle">{compact(node.label)}</text>
              <text className={styles.meta} x={x} y={y + 16} textAnchor="middle">{node.kind} · {node.teamIds.length} teams</text>
            </g>;
          })}
        </g>
      </svg>
    </div> : <p className={styles.empty}>Choose a scope node to focus the hierarchy.</p>}

    {children.length > MAX_DIAGRAM_CHILDREN && <p className={styles.note} role="status">The diagram is capped at {MAX_DIAGRAM_CHILDREN} direct children. Select any scope from the searchable directory.</p>}

    <div className={styles.listHeader}>
      <div><h3>Scope directory</h3><p>{matches.length.toLocaleString()} matching · {allNodes.length.toLocaleString()} total</p></div>
      <label className={styles.search}>Search scopes
        <input type="search" value={search} placeholder="Name, type, or external reference" onChange={(event) => { setSearch(event.target.value); setListPage(0); }} />
      </label>
    </div>
    <ul className={styles.scopeList} aria-label="Selectable scope nodes">
      {listed.map((node) => <li key={node.id}><button type="button" className={`${styles.listNode} ${node.id === selectedId ? styles.listSelected : ''}`} aria-current={node.id === selectedId ? 'true' : undefined} onClick={() => select(node.id)}>
        <span className={styles.kindMark} style={{ backgroundColor: colorFor(node.kind) }} aria-hidden="true" />
        <span className={styles.listText}><strong>{node.label}</strong><small>{node.kind}{node.externalRef ? ` · ${node.externalRef}` : ''}</small></span>
        <span className={styles.teamCount}>{node.teamIds.length} teams</span>
      </button></li>)}
      {!listed.length && <li className={styles.noResults}>No scopes match this search.</li>}
    </ul>
    {matches.length > PAGE_SIZE && <div className={styles.pagination}><span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, matches.length)} of {matches.length}</span>
      <div><button type="button" onClick={() => setListPage((value) => Math.max(0, value - 1))} disabled={page === 0}>Previous</button><button type="button" onClick={() => setListPage((value) => Math.min(pages - 1, value + 1))} disabled={page >= pages - 1}>Next</button></div>
    </div>}
  </section>;
}
