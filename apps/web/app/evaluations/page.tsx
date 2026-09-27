import Link from 'next/link';
import AppShell from '@/components/AppShell';
import EvaluationLab from '@/components/EvaluationLab';
export default function Page(){return <AppShell active="evaluations"><div className="apex-page"><header className="apex-section-heading"><span className="eyebrow">EVALUATION / CONTROLLED EVOLUTION</span><h1>Improvement needs evidence.</h1><p>Separate measured scheduler behavior from live task quality. Promote a change only when its evaluation supports it.</p><div className="apex-actions"><Link href="/ecosystem/research" className="secondary-button">Architecture comparisons & benchmark design →</Link><Link href="/arena" className="secondary-button">Open the reproducible Swarm Arena →</Link></div></header><EvaluationLab/></div></AppShell>;}
