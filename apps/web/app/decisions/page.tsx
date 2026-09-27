import AppShell from '@/components/AppShell';
import DecisionStudio from '@/components/DecisionStudio';
export default async function Page({searchParams}: {searchParams: Promise<{context?: string}>}) {
  const params = await searchParams;
  const contexts = ['graph','swarm','teams','analytics','optimization','delegation','evaluations','ecosystem','overview'] as const;
  const context = contexts.find(value => value === params.context) ?? 'overview';
  return <AppShell active="decisions"><div className="apex-page"><header className="apex-section-heading"><span className="eyebrow">DECISION INTELLIGENCE / LAYA · ANYJEV</span><h1>Ask precisely. Decide with evidence.</h1><p>Batch typed questions about repository work, swarm routing and operational evidence. Compare provider probabilities, measured latency and estimated costs in one workspace.</p></header><DecisionStudio context={context} /></div></AppShell>;
}
