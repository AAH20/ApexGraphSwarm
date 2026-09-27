import Link from 'next/link';
import AppShell from '@/components/AppShell';
import SwarmControl from '@/components/SwarmControl';
export default function Page(){return <AppShell active="swarm"><div className="apex-page"><header className="apex-section-heading"><span className="eyebrow">ORCHESTRATION / DURABLE LOCAL STATE</span><h1>A plan is only the beginning.</h1><p>Inspect dependencies, execution leases and the accounting ledger. Start with a harmless scheduler fixture before connecting real workers.</p><div className="apex-actions"><Link href="/teams" className="primary-button">Configure specialist teams →</Link><Link href="/ecosystem/research" className="secondary-button">Architecture comparisons & benchmark design →</Link></div></header><SwarmControl/></div></AppShell>;}
