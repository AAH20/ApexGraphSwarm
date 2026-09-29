import AppShell from '@/components/AppShell';
import DelegationPlanner from '@/components/DelegationPlanner';
/**
 * React component Page.
 *
 *
 * @example
 * ```typescript
 * import { Page } from './module';
 * ```
 */
export default function Page(){return <AppShell active="delegation"><div className="apex-page"><header className="apex-section-heading"><span className="eyebrow">ROUTING / UNIT ECONOMICS</span><h1>Delegate with a reason.</h1><p>Match task requirements to explicit capabilities, measured evidence and an accountable budget.</p></header><DelegationPlanner/></div></AppShell>;}
