import AppShell from '@/components/AppShell';
import GovernanceDashboard from '@/components/GovernanceDashboard';
export default function Page(){return <AppShell active="governance"><div className="apex-page"><header className="apex-section-heading"><span className="eyebrow">GOVERNANCE / REAL-TIME MONITORING</span><h1>Agent governance, live.</h1><p>Monitor agent actions, policy violations, trust scores and spend in real time.</p></header><GovernanceDashboard/></div></AppShell>;}
