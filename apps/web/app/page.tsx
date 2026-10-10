import Link from 'next/link';
import {ArrowUpRight,Network,Workflow,Route,FlaskConical} from 'lucide-react';
import AppShell from '@/components/AppShell';
/**
 * Next.js page component for page.
 *
 * @module page
 * @packageDocumentation
 */
const capabilities=[{href:'/graph',Icon:Network,title:'Understand the system',text:'Explore source relationships, evidence, neighborhoods and dependency paths.'},{href:'/swarm',Icon:Workflow,title:'Coordinate the work',text:'Inspect durable local task state, leases, dependencies and admission budgets.'},{href:'/delegation',Icon:Route,title:'Choose with evidence',text:'Compare eligible models and harnesses against capability, cost and latency constraints.'},{href:'/evaluations',Icon:FlaskConical,title:'Prove the improvement',text:'Inspect reproducible scheduler benchmarks and versioned evaluation plans.'}];
/**
 * React component Page.
 *
 *
 * @example
 * ```typescript
 * import { Page } from './module';
 * ```
 */
export default function Page(){return <AppShell active="overview"><div className="apex-page"><header className="apex-heading"><span className="eyebrow">APEXGRAPH SWARM / ENGINEERING CONTROL ROOM</span><h1>Build coordinated intelligence.<br/><em>Measure every decision.</em></h1><p>A dedicated workspace for graph-grounded agent engineering, bounded orchestration and transparent unit economics.</p><div className="apex-actions"><Link className="primary-button" href="/graph">Explore the graph <ArrowUpRight size={15}/></Link><Link className="secondary-button" href="/swarm">Open swarm control</Link></div></header><div className="apex-principles"><div><strong>300</strong><span>Logical agents in the fixture benchmark target</span></div><div><strong>Bounded</strong><span>Active concurrency, retries and spend</span></div><div><strong>Versioned</strong><span>Plans, evidence and evaluation outcomes</span></div><div><strong>Auditable</strong><span>Estimated, reserved and settled costs</span></div></div><section className="apex-card-grid" aria-label="Engineering tools">{capabilities.map(({href,Icon,title,text})=><Link href={href} className="apex-tool-card" key={href}><Icon size={23}/><h2>{title}</h2><p>{text}</p><span>Open workspace <ArrowUpRight size={14}/></span></Link>)}</section><section className="apex-boundary"><span className="eyebrow">READINESS, WITHOUT AMBIGUITY</span><h2>A local foundation with explicit scaling gates.</h2><p>The graph tools and configured integrations are executable. The SQLite control plane persists its own tasks; existing integration jobs still use separate process-local tracking. Fixture benchmarks measure scheduler behavior, not model intelligence or 300 concurrent paid agents.</p><p>Production rollout requires multi-tenant authorization, isolated workers, distributed storage and live workload evaluation. Unknown rates remain unknown; no provider is called merely by opening this project.</p></section></div></AppShell>;}
