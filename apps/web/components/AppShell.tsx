import Link from 'next/link';
import {Orbit,Network,Workflow,Route,FlaskConical,Plug,Users,ArrowUpRight,ShieldCheck,ChartNoAxesCombined,Presentation} from 'lucide-react';
/**
 * React component for app shell.
 *
 * @module AppShell
 * @packageDocumentation
 */
/**
 * Type Page.
 *
 *
 * @example
 * ```typescript
 * import { Page } from './module';
 * ```
 */
type Page='overview'|'graph'|'swarm'|'delegation'|'evaluations'|'ecosystem'|'teams'|'optimization'|'analytics'|'decisions'|'arena'|'presentations'|'governance';
const links=[['overview','/','Control room',Orbit],['graph','/graph','Graph Studio',Network],['swarm','/swarm','Swarm control',Workflow],['teams','/teams','Specialist teams',Users],['delegation','/delegation','Delegation & cost',Route],['optimization','/optimization?view=hierarchy','Optimization & hierarchy',Route],['analytics','/analytics','Data & intelligence',ChartNoAxesCombined],['decisions','/decisions','Decision intelligence',FlaskConical],['evaluations','/evaluations','Evaluation lab',FlaskConical],['arena','/arena','Swarm Arena',FlaskConical],['presentations','/presentations','Presentation Studio',Presentation],['ecosystem','/ecosystem','Ecosystem',Plug],['governance','/governance','Governance',ShieldCheck]] as const;
/**
 * React component AppShell.
 *
 * @param {{children} children,active='graph' - Description of children,active='graph'.
 *
 * @example
 * ```typescript
 * const result = AppShell(...);
 * ```
 */
export default function AppShell({children,active='graph'}:{children:React.ReactNode;active?:Page}){
 return <div className="app-shell"><a className="skip-link" href="#workspace">Skip to workspace</a><aside className="app-sidebar"><Link href="/" className="brand"><Orbit size={31}/><span>ApexGraphSwarm<small>AGENT ENGINEERING</small></span></Link><div className="nav-section">ENGINEERING WORKSPACE</div><nav aria-label="Main navigation">{links.map(([id,href,label,Icon])=><Link key={id} className={active===id?'nav-link active':'nav-link'} href={id==='decisions'&&active!=='decisions'?`${href}?context=${active}`:href} aria-current={active===id?'page':undefined}><Icon size={18}/>{label}{active===id&&<span className="nav-dot"/>}</Link>)}</nav><div className="sidebar-note"><span className="live-dot"/>Local engineering preview<h3>Evidence before scale.</h3><p>Understand the system. Delegate within limits. Measure the result.</p></div><div className="sidebar-bottom"><Link href="/graph#integrations"><Workflow size={16}/>Framework integrations<ArrowUpRight size={12}/></Link><a href="mailto:aah@a2zsoc.com"><ShieldCheck size={16}/>Experienced mentorship<ArrowUpRight size={12}/></a><span className="version-tag">APEXGRAPH / 0.1</span></div></aside><main id="workspace" className="main-workspace">{children}</main></div>;
}
