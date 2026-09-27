'use client';

import dynamic from 'next/dynamic';
import { Maximize2, Minimize2, Network, Search } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';
import type { AnalyticsReport } from '@/lib/analytics-types';
import { dollars } from '@/lib/analytics-types';
import { adaptAnalyticsGraph, analyticsEdgeKey, filterAnalyticsGraph, type AnalyticsCategory } from '@/lib/analytics-graph';
import type { GraphCanvasStatus } from './GraphCanvas';
import { useGraphFullscreen } from './useGraphFullscreen';
import styles from './AnalyticsRelationshipGraph.module.css';

const GraphCanvas = dynamic(() => import('./GraphCanvas'), {
  ssr: false,
  loading: () => <div className={styles.loading}><Network size={28} /><span>Preparing the WebGL relationship graph…</span></div>,
});

export function AnalyticsRelationshipGraph({ report }: { report: AnalyticsReport }) {
  const stage = useRef<HTMLElement>(null);
  const fullscreen = useGraphFullscreen(stage);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<AnalyticsCategory>('all');
  const [selected, setSelected] = useState<string | null>(null);
  const [neighborhoodOnly, setNeighborhoodOnly] = useState(false);
  const [renderer, setRenderer] = useState<GraphCanvasStatus>({ renderer: 'Loading WebGL renderer', layoutRunning: false, visible: 0 });

  const adapted = useMemo(() => adaptAnalyticsGraph(report.graph, report.source, report.quality), [report.graph, report.source, report.quality]);
  const visible = useMemo(() => filterAnalyticsGraph(adapted, { query, category, selected, neighborhoodOnly }),
    [adapted, query, category, selected, neighborhoodOnly]);
  const visibleSelected = selected && visible.nodes.some((node) => node.id === selected) ? selected : null;
  const selectedNode = selected ? adapted.nodes.find((node) => node.id === selected) : undefined;
  const selectedEdges = selectedNode ? adapted.edges.filter((edge) => edge.source === selected || edge.target === selected) : [];
  const omitted = adapted.quality.omittedNodes + adapted.quality.omittedEdges + adapted.quality.invalidNodes + adapted.quality.invalidEdges;
  const unknownCosts = Number(report.quality.unknownCostRows) || 0;
  const dataPartial = report.quality.truncated || report.quality.graphTruncated === true || !report.quality.selectionKnownCoverage;

  return (
    <section ref={stage} className={`${styles.root} ${fullscreen.expanded ? styles.fullscreen : ''}`} aria-label="Analytics relationship graph">
      <div className={styles.toolbar} role="toolbar" aria-label="Analytics graph filters and actions">
        <label className={styles.search}>
          <Search size={15} aria-hidden="true" />
          <span className={styles.srOnly}>Search tools and resources</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a tool or resource" />
        </label>
        <label className={styles.category}>
          <span>Show</span>
          <select value={category} onChange={(event) => setCategory(event.target.value as AnalyticsCategory)} aria-label="Filter analytics graph category">
            <option value="all">Tools and resources</option>
            <option value="tool">Tools</option>
            <option value="resource">Resources</option>
          </select>
        </label>
        <button type="button" className={styles.action} aria-pressed={neighborhoodOnly}
          disabled={!visibleSelected} onClick={() => setNeighborhoodOnly((value) => !value)}>
          {neighborhoodOnly ? 'Show all matches' : 'Selected neighborhood'}
        </button>
        <button type="button" className={styles.fullscreenButton} data-fullscreen-toggle
          aria-label={fullscreen.expanded ? 'Exit analytics graph fullscreen' : 'Open analytics graph fullscreen'}
          aria-pressed={fullscreen.expanded} onClick={() => void fullscreen.toggle()}>
          {fullscreen.expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>

      <p className={styles.scopeNote}>
        Edges represent aggregated observed tool-to-resource usage. They are not repository dependencies or causal claims.
        {report.source === 'demo' ? ' Demo graph evidence is illustrative.' : ' Non-demo graph evidence is aggregated from attempts.'}
      </p>

      {(omitted > 0 || dataPartial) && <p className={styles.quality} role="status">
        {omitted > 0 ? `${adapted.quality.omittedNodes} nodes and ${adapted.quality.omittedEdges} edges omitted; ${adapted.quality.invalidNodes + adapted.quality.invalidEdges} invalid records skipped. ` : ''}
        {dataPartial ? 'The source report is partial or its ledger coverage is unverified; graph totals may be incomplete.' : ''}
      </p>}

      <div className={styles.graphPanel}>
        <GraphCanvas nodes={visible.nodes} edges={visible.edges} selected={visibleSelected}
          onSelect={setSelected} layout="grouped" onStatus={setRenderer}
          graphLabel="Interactive analytics tool and resource graph. Use the node list below for keyboard navigation."
          fallbackLabel="Analytics relationship graph SVG fallback"
          nodeActionLabel={(node) => `Select analytics ${node.kind === 'function' ? 'tool' : 'resource'}: ${node.name}`}
          labelsAlwaysVisible />
      </div>

      <div className={styles.rendererStatus} role="status" aria-live="polite">
        <span>{renderer.layoutRunning ? 'Force layout running' : renderer.renderer}</span>
        <span>{visible.nodes.length} nodes · {visible.edges.length} relationships shown</span>
        {renderer.error && <span className={styles.rendererError}>{renderer.error}</span>}
      </div>

      <div className={styles.columns}>
        <section className={styles.listSection} aria-labelledby="analytics-graph-nodes-heading">
          <div className={styles.sectionHead}><h3 id="analytics-graph-nodes-heading">Graph nodes</h3><span>{visible.nodes.length}</span></div>
          <p className={styles.categoryNote}>Tool IDs use the function shape; resource IDs use the external shape for visualization only.</p>
          {visible.nodes.length ? <ul className={styles.nodeList} aria-label="Keyboard-accessible analytics graph nodes">
            {visible.nodes.map((node) => {
              const isTool = node.kind === 'function';
              return <li key={node.id}><button type="button" aria-pressed={selected === node.id}
                onClick={() => setSelected((current) => current === node.id ? null : node.id)}>
                <span className={isTool ? styles.toolDot : styles.resourceDot} aria-hidden="true" />
                <span><strong>{node.name}</strong><small>{isTool ? 'Tool identifier' : 'Resource label'}</small></span>
              </button></li>;
            })}
          </ul> : <p className={styles.empty}>No graph nodes match these filters.</p>}
        </section>

        <section className={styles.inspector} aria-label="Selected relationship metrics">
          <div className={styles.sectionHead}><h3>Selection details</h3>{selectedNode && <span>{adapted.quality.evidence}</span>}</div>
          {!selectedNode ? <p className={styles.empty}>Select a node from the graph or keyboard-accessible list to inspect observed links.</p> : <>
            <h4>{selectedNode.name}</h4>
            <p>{selectedNode.kind === 'function' ? 'Tool identifier' : 'Resource label · external display category only'}</p>
            <ul className={styles.metricList}>
              {selectedEdges.map((edge) => {
                const neighborId = edge.source === selectedNode.id ? edge.target : edge.source;
                const neighbor = adapted.nodes.find((node) => node.id === neighborId);
                const metric = adapted.edgeMetrics.get(analyticsEdgeKey(edge.source, edge.target));
                if (!neighbor || !metric) return null;
                return <li key={analyticsEdgeKey(edge.source, edge.target)}>
                  <div><strong>{neighbor.name}</strong><span>{metric.attempts} observed attempts</span></div>
                  <b>{dollars(metric.knownCostMicrousd)} known-cost subtotal</b>
                  <span>{metric.complete ? 'Cost coverage complete' : 'Unknown liability is not allocated to this edge'}</span>
                </li>;
              })}
            </ul>
            {selectedEdges.length === 0 && <p className={styles.empty}>No observed relationship connects this node.</p>}
            <p className={styles.metricCaveat}>
              Cost shows the exact known-cost subtotal reported for each relationship. {unknownCosts > 0
                ? `${unknownCosts} costs are unknown at report level; unknown liability is not attributed to individual edges.`
                : 'The report contains no unknown-cost rows.'}
              {dataPartial ? ' The ledger coverage is incomplete or unverified.' : ''}
            </p>
          </>}
        </section>
      </div>
    </section>
  );
}

export default AnalyticsRelationshipGraph;
