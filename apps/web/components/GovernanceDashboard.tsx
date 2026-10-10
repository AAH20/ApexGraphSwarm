'use client';
import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {Activity,AlertTriangle,Bot,CheckCircle2,Clock3,DollarSign,Eye,FileWarning,Gauge,Lock,Play,RefreshCw,Shield,ShieldAlert,ShieldCheck,ShieldX,Target,TrendingUp,Users,XCircle} from 'lucide-react';
import {formatMicrousd} from '@/lib/format-microusd';
import {type AnalyticsReport} from '@/lib/analytics-types';
import styles from './GovernanceDashboard.module.css';

// ── Types (from @apexgraphswarm/governance) ────────────────────────────────

import type {
  RunStatus,
  TaskSummary,
  EventSummary,
  GrantSummary,
  WorkerSummary,
  PolicyViolation,
  TrustScore,
} from '@apexgraphswarm/governance';

type SpendData={
  budgetMicrousd:number;spentMicrousd:number;reservedMicrousd:number;
  remainingMicrousd:number;costPerSuccessMicrousd:number|null;
  dailySpend:{date:string;amountMicrousd:number}[];
  byTool:{tool:string;amountMicrousd:number;attempts:number}[];
};

type GovernanceState={
  run:RunStatus|null;
  analytics:AnalyticsReport|null;
  grants:GrantSummary[];
  workers:WorkerSummary[];
  violations:PolicyViolation[];
  trustScores:TrustScore[];
  spend:SpendData|null;
  lastRefresh:string|null;
  loading:boolean;
  error:string;
  token:string;
  autoRefresh:boolean;
  refreshInterval:number;
};

// ── Helpers ────────────────────────────────────────────────────────────────

function computeTrustScores(run:RunStatus|null,grants:GrantSummary[],workers:WorkerSummary[]):TrustScore[]{
  const scores:TrustScore[]=[];
  const now=Date.now()/1000;

  for(const worker of workers){
    let score=100;
    const factors:TrustScore['factors']=[];

    if(worker.revokedAt){
      score=0;
      factors.push({label:'Worker credential revoked',impact:'negative',weight:100});
    }else if(worker.expiresAt<now){
      score=Math.min(score,20);
      factors.push({label:'Credential expired',impact:'negative',weight:80});
    }else{
      const timeToExpiry=worker.expiresAt-now;
      if(timeToExpiry<3600){
        score-=10;
        factors.push({label:'Credential expires within 1 hour',impact:'negative',weight:10});
      }else{
        factors.push({label:'Active credential',impact:'positive',weight:5});
      }
    }

    if(run){
      const workerTasks=run.tasks.filter(t=>t.workerId===worker.workerId);
      const succeeded=workerTasks.filter(t=>t.status==='succeeded'||t.status==='completed').length;
      const failed=workerTasks.filter(t=>t.status==='failed').length;
      if(succeeded>0){
        factors.push({label:`${succeeded} successful task${succeeded!==1?'s':''}`,impact:'positive',weight:Math.min(succeeded*5,20)});
        score=Math.min(100,score+succeeded*2);
      }
      if(failed>0){
        factors.push({label:`${failed} failed task${failed!==1?'s':''}`,impact:'negative',weight:Math.min(failed*10,30)});
        score-=failed*8;
      }
    }

    scores.push({
      entityId:worker.workerId,entityType:'worker',
      score:Math.max(0,Math.min(100,score)),
      factors,lastUpdated:new Date().toISOString(),
    });
  }

  for(const grant of grants){
    let score=100;
    const factors:TrustScore['factors']=[];

    if(grant.revokedAt){
      score=0;
      factors.push({label:'Grant revoked',impact:'negative',weight:100});
    }else if(grant.expiresAt<now){
      score=Math.min(score,15);
      factors.push({label:'Grant expired',impact:'negative',weight:85});
    }else{
      const timeToExpiry=grant.expiresAt-now;
      if(timeToExpiry<3600){
        score-=15;
        factors.push({label:'Grant expires within 1 hour',impact:'negative',weight:15});
      }
    }

    const utilization=grant.maxBudgetMicrousd>0?(grant.spentMicrousd+grant.reservedMicrousd)/grant.maxBudgetMicrousd:0;
    if(utilization>0.9){
      score-=20;
      factors.push({label:`Budget ${(utilization*100).toFixed(0)}% utilized`,impact:'negative',weight:20});
    }else if(utilization>0.7){
      score-=5;
      factors.push({label:`Budget ${(utilization*100).toFixed(0)}% utilized`,impact:'neutral',weight:5});
    }else{
      factors.push({label:`Budget ${(utilization*100).toFixed(0)}% utilized`,impact:'positive',weight:5});
    }

    scores.push({
      entityId:grant.grantId,entityType:'grant',
      score:Math.max(0,Math.min(100,score)),
      factors,lastUpdated:new Date().toISOString(),
    });
  }

  if(run){
    for(const agent of run.agents){
      const agentTasks=run.tasks.filter(t=>t.agentId===agent.id);
      const total=agentTasks.length;
      if(total===0)continue;
      const succeeded=agentTasks.filter(t=>t.status==='succeeded'||t.status==='completed').length;
      const failed=agentTasks.filter(t=>t.status==='failed').length;
      const running=agentTasks.filter(t=>t.status==='running').length;
      const successRate=succeeded/total;

      let score=Math.round(successRate*100);
      const factors:TrustScore['factors']=[];

      if(succeeded>0)factors.push({label:`${succeeded}/${total} tasks succeeded`,impact:'positive',weight:succeeded*3});
      if(failed>0){
        factors.push({label:`${failed} failed`,impact:'negative',weight:failed*10});
        score-=failed*5;
      }
      if(running>0)factors.push({label:`${running} in progress`,impact:'neutral',weight:0});

      scores.push({
        entityId:agent.id,entityType:'agent',
        score:Math.max(0,Math.min(100,score)),
        factors,lastUpdated:new Date().toISOString(),
      });
    }
  }

  return scores.sort((a,b)=>a.score-b.score);
}

function detectViolations(run:RunStatus|null,grants:GrantSummary[],workers:WorkerSummary[],analytics:AnalyticsReport|null):PolicyViolation[]{
  const violations:PolicyViolation[]=[];
  const now=Date.now()/1000;

  if(!run)return violations;

  if(run.run.budgetMicrousd>0){
    const utilization=run.run.spentMicrousd/run.run.budgetMicrousd;
    if(utilization>0.95){
      violations.push({
        id:'budget-critical',severity:'critical',category:'budget',
        message:`Run budget ${(utilization*100).toFixed(1)}% consumed`,
        timestamp:new Date().toISOString(),
        details:{budget:run.run.budgetMicrousd,spent:run.run.spentMicrousd,remaining:run.run.remainingMicrousd},
      });
    }else if(utilization>0.8){
      violations.push({
        id:'budget-warning',severity:'warning',category:'budget',
        message:`Run budget ${(utilization*100).toFixed(1)}% consumed`,
        timestamp:new Date().toISOString(),
        details:{budget:run.run.budgetMicrousd,spent:run.run.spentMicrousd,remaining:run.run.remainingMicrousd},
      });
    }
  }

  for(const task of run.tasks){
    if(task.reservedCostMicrousd&&task.actualCostMicrousd&&task.actualCostMicrousd>task.reservedCostMicrousd){
      violations.push({
        id:`task-budget-${task.taskId}`,severity:'critical',category:'budget',
        message:`Task ${task.id} exceeded reserved budget`,
        timestamp:new Date().toISOString(),
        details:{taskId:task.taskId,reserved:task.reservedCostMicrousd,actual:task.actualCostMicrousd},
      });
    }
  }

  for(const grant of grants){
    if(grant.revokedAt){
      violations.push({
        id:`grant-revoked-${grant.grantId}`,severity:'warning',category:'access',
        message:`Grant ${grant.grantId.slice(0,8)}… revoked`,
        timestamp:new Date(grant.revokedAt*1000).toISOString(),
        details:{grantId:grant.grantId,principal:grant.principalId},
      });
    }else if(grant.expiresAt<now){
      violations.push({
        id:`grant-expired-${grant.grantId}`,severity:'warning',category:'access',
        message:`Grant ${grant.grantId.slice(0,8)}… expired`,
        timestamp:new Date(grant.expiresAt*1000).toISOString(),
        details:{grantId:grant.grantId,principal:grant.principalId},
      });
    }
  }

  for(const worker of workers){
    if(worker.revokedAt){
      violations.push({
        id:`worker-revoked-${worker.workerId}`,severity:'critical',category:'identity',
        message:`Worker ${worker.workerId} revoked`,
        timestamp:new Date(worker.revokedAt*1000).toISOString(),
        details:{workerId:worker.workerId,principal:worker.principalId},
      });
    }else if(worker.expiresAt<now){
      violations.push({
        id:`worker-expired-${worker.workerId}`,severity:'warning',category:'identity',
        message:`Worker ${worker.workerId} credential expired`,
        timestamp:new Date(worker.expiresAt*1000).toISOString(),
        details:{workerId:worker.workerId,principal:worker.principalId},
      });
    }
  }

  if(analytics){
    const unresolved=analytics.quality.unknownCostRows;
    if(unresolved>0){
      violations.push({
        id:'reconciliation-unknown',severity:'warning',category:'reconciliation',
        message:`${unresolved} attempt${unresolved!==1?'s':''} with unknown cost`,
        timestamp:new Date().toISOString(),
        details:{unknownCostRows:unresolved},
      });
    }
    if(analytics.quality.invalidRows>0){
      violations.push({
        id:'reconciliation-invalid',severity:'critical',category:'reconciliation',
        message:`${analytics.quality.invalidRows} invalid ledger row${analytics.quality.invalidRows!==1?'s':''}`,
        timestamp:new Date().toISOString(),
        details:{invalidRows:analytics.quality.invalidRows},
      });
    }
  }

  const runningTasks=run.tasks.filter(t=>t.status==='running');
  if(runningTasks.length>0){
    const expiredLeases=runningTasks.filter(t=>t.leaseExpiresAt&&t.leaseExpiresAt<now);
    if(expiredLeases.length>0){
      violations.push({
        id:'capacity-expired-leases',severity:'warning',category:'capacity',
        message:`${expiredLeases.length} running task${expiredLeases.length!==1?'s':''} with expired lease${expiredLeases.length!==1?'s':''}`,
        timestamp:new Date().toISOString(),
        details:{expiredLeaseCount:expiredLeases.length,taskIds:expiredLeases.map(t=>t.taskId)},
      });
    }
  }

  const severityOrder={critical:0,warning:1,info:2};
  return violations.sort((a,b)=>severityOrder[a.severity]-severityOrder[b.severity]);
}

function computeSpendData(run:RunStatus|null,analytics:AnalyticsReport|null):SpendData|null{
  if(!run&&!analytics)return null;

  const budget=run?.run.budgetMicrousd??0;
  const spent=run?.run.spentMicrousd??0;
  const reserved=run?.run.reservedMicrousd??0;
  const remaining=run?.run.remainingMicrousd??0;

  const dailySpend=analytics?.daily.map(d=>({date:d.date,amountMicrousd:d.knownCostMicrousd}))??[];
  const byTool=analytics?.cohorts.map(c=>({tool:c.tool,amountMicrousd:c.knownCostMicrousd,attempts:c.attempts}))??[];

  return {
    budgetMicrousd:budget,spentMicrousd:spent,reservedMicrousd:reserved,
    remainingMicrousd:remaining,
    costPerSuccessMicrousd:analytics?.kpis.costPerSuccessMicrousd??null,
    dailySpend,byTool,
  };
}

// ── Sub-components ─────────────────────────────────────────────────────────

function KpiCard({icon:Icon,label,value,detail,tone='default'}:{icon:React.ComponentType<{size?:number|string;className?:string}>;label:string;value:string;detail?:string;tone?:'default'|'success'|'warning'|'danger'}){
  const toneClass=tone==='success'?'kpi-success':tone==='warning'?'kpi-warning':tone==='danger'?'kpi-danger':'';
  return <div className={`${styles['kpi-card']} ${toneClass}`}>
    <div className={styles['kpi-icon']}><Icon size={18}/></div>
    <div className={styles['kpi-content']}>
      <span className={styles['kpi-label']}>{label}</span>
      <strong className={styles['kpi-value']}>{value}</strong>
      {detail&&<small className={styles['kpi-detail']}>{detail}</small>}
    </div>
  </div>;
}

function TrustScoreBar({score}:{score:number}){
  const color=score>=80?'#4ade80':score>=60?'#facc15':score>=40?'#fb923c':'#f87171';
  return <div className={styles['trust-bar']}>
    <div className={styles['trust-bar-track']}>
      <div className={styles['trust-bar-fill']} style={{width:`${score}%`,background:color}}/>
    </div>
    <span className={styles['trust-bar-value']} style={{color}}>{score}</span>
  </div>;
}

function ViolationItem({violation}:{violation:PolicyViolation}){
  const severityIcon=violation.severity==='critical'?ShieldX:violation.severity==='warning'?ShieldAlert:Shield;
  const Icon=severityIcon;
  return <div className={`${styles['violation-item']} severity-${violation.severity}`}>
    <div className={styles['violation-icon']}><Icon size={16}/></div>
    <div className={styles['violation-body']}>
      <span className={styles['violation-category']}>{violation.category}</span>
      <p className={styles['violation-message']}>{violation.message}</p>
      <time className={styles['violation-time']}>{new Date(violation.timestamp).toLocaleTimeString()}</time>
    </div>
  </div>;
}

function AgentActionRow({task,agentName}:{task:TaskSummary;agentName?:string}){
  const statusIcon=task.status==='succeeded'||task.status==='completed'?CheckCircle2:task.status==='failed'?XCircle:task.status==='running'?Play:Clock3;
  const Icon=statusIcon;
  return <tr className={`${styles['agent-action-row']} status-${task.status}`}>
    <td><Icon size={14}/></td>
    <td>{task.id}</td>
    <td>{agentName??task.agentId}</td>
    <td><span className={`${styles['status-pill']} ${task.status}`}>{task.status}</span></td>
    <td>{task.attempts}/{task.maxAttempts}</td>
    <td>{formatMicrousd(task.actualCostMicrousd)}</td>
    <td>{task.executionClass}</td>
  </tr>;
}

// ── Main Component ─────────────────────────────────────────────────────────

export default function GovernanceDashboard(){
  const [state,setState]=useState<GovernanceState>({
    run:null,analytics:null,grants:[],workers:[],violations:[],
    trustScores:[],spend:null,lastRefresh:null,loading:false,error:'',
    token:'',autoRefresh:false,refreshInterval:30,
  });

  const requestRef=useRef<AbortController|null>(null);
  const runningRef=useRef(false);

  const fetchGovernance=useCallback(async()=>{
    if(runningRef.current)return;
    const token=state.token;
    if(!token){
      setState(s=>({...s,error:'Enter the private workspace execution token to load governance data.',autoRefresh:false}));
      return;
    }
    runningRef.current=true;
    const controller=new AbortController();
    requestRef.current=controller;
    setState(s=>({...s,loading:true,error:''}));

    try{
      const runResponse=await fetch('/api/control',{
        method:'POST',
        headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},
        body:JSON.stringify({action:'status',runId:'governance-overview'}),
        signal:controller.signal,
      });
      const runBody=await runResponse.json();
      let run:RunStatus|null=null;
      if(runResponse.ok&&runBody.state){
        run=runBody.state;
      }

      const analyticsResponse=await fetch('/api/analytics',{
        method:'POST',
        headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},
        body:JSON.stringify({source:'live',days:30}),
        signal:controller.signal,
      });
      const analyticsBody=await analyticsResponse.json();
      let analytics:AnalyticsReport|null=null;
      if(analyticsResponse.ok&&analyticsBody.result){
        analytics=analyticsBody.result;
      }

      const grants:GrantSummary[]=[];
      const workers:WorkerSummary[]=[];

      const trustScores=computeTrustScores(run,grants,workers);
      const violations=detectViolations(run,grants,workers,analytics);
      const spend=computeSpendData(run,analytics);

      setState(s=>({
        ...s,run,analytics,grants,workers,violations,trustScores,spend,
        lastRefresh:new Date().toISOString(),loading:false,
      }));
    }catch(err){
      if(!controller.signal.aborted){
        setState(s=>({
          ...s,loading:false,
          error:err instanceof Error?err.message:'Failed to load governance data.',
          autoRefresh:false,
        }));
      }
    }finally{
      if(requestRef.current===controller){
        runningRef.current=false;
      }
    }
  },[state.token]);

  useEffect(()=>{
    if(!state.autoRefresh)return;
    const timer=setInterval(()=>{
      if(document.visibilityState==='visible')void fetchGovernance();
    },state.refreshInterval*1000);
    return()=>clearInterval(timer);
  },[state.autoRefresh,state.refreshInterval,fetchGovernance]);

  useEffect(()=>()=>requestRef.current?.abort(),[]);

  const taskStats=useMemo(()=>{
    const r=state.run;
    if(!r)return null;
    const total=r.tasks.length;
    const succeeded=r.tasks.filter((t:TaskSummary)=>t.status==='succeeded'||t.status==='completed').length;
    const failed=r.tasks.filter((t:TaskSummary)=>t.status==='failed').length;
    const running=r.tasks.filter((t:TaskSummary)=>t.status==='running').length;
    const pending=r.tasks.filter((t:TaskSummary)=>t.status==='pending').length;
    return{total,succeeded,failed,running,pending};
  },[state.run]);

  const criticalCount=useMemo(()=>state.violations.filter(v=>v.severity==='critical').length,[state.violations]);
  const warningCount=useMemo(()=>state.violations.filter(v=>v.severity==='warning').length,[state.violations]);

  return <div className={styles.dashboard}>
    <div className={styles['gov-header']}>
      <div className={styles['gov-header-left']}>
        <span className={styles.eyebrow}>GOVERNANCE / REAL-TIME MONITORING</span>
        <h2>Agent Governance Dashboard</h2>
        <p>Live visibility into agent actions, policy compliance, trust scores and spend.</p>
      </div>
      <div className={styles['gov-header-actions']}>
        <label className={styles['gov-toggle']}>
          <input type="checkbox" checked={state.autoRefresh} disabled={state.loading||!state.token}
            onChange={e=>setState(s=>({...s,autoRefresh:e.target.checked}))}/>
          <span>Auto-refresh</span>
        </label>
        <label className={styles['gov-interval']}>
          Interval
          <select value={state.refreshInterval} disabled={state.loading||!state.autoRefresh}
            onChange={e=>setState(s=>({...s,refreshInterval:Number(e.target.value)}))}>
            <option value={10}>10s</option>
            <option value={30}>30s</option>
            <option value={60}>60s</option>
          </select>
        </label>
        <button className="primary-button" disabled={state.loading||!state.token} onClick={()=>void fetchGovernance()}>
          <RefreshCw size={14}/>{state.loading?'Loading…':'Refresh'}
        </button>
      </div>
    </div>

    <div className={styles['gov-token-bar']}>
      <label>
        <Lock size={14}/>
        <input type="password" autoComplete="off" value={state.token}
          onChange={e=>setState(s=>({...s,token:e.target.value}))}
          placeholder="INTEGRATION_ACCESS_TOKEN from .env.local"/>
      </label>
      {state.lastRefresh&&<span className={styles['gov-freshness']}>Last refresh: {new Date(state.lastRefresh).toLocaleTimeString()}</span>}
    </div>

    {state.error&&<div className={styles['gov-error']}><AlertTriangle size={16}/>{state.error}</div>}

    {state.loading&&!state.run&&<div className={styles['gov-loading']}><Activity size={20} className={styles.spin}/>Loading governance data…</div>}

    {(state.run||state.analytics)&&<>
      <div className={styles['gov-kpis']}>
        <KpiCard icon={Bot} label="Active Agents" value={String(state.run?.agents.length??'—')}
          detail={taskStats?`${taskStats.running} running · ${taskStats.pending} pending`:undefined}/>
        <KpiCard icon={Target} label="Success Rate"
          value={state.analytics?.kpis.successRate!=null?`${(state.analytics.kpis.successRate*100).toFixed(1)}%`:'—'}
          detail={state.analytics?`${state.analytics.kpis.succeeded}/${state.analytics.kpis.attempts} attempts`:undefined}
          tone={state.analytics&&state.analytics.kpis.successRate!=null&&state.analytics.kpis.successRate>=0.8?'success':state.analytics&&state.analytics.kpis.successRate!=null&&state.analytics.kpis.successRate<0.5?'danger':'default'}/>
        <KpiCard icon={DollarSign} label="Known Spend"
          value={formatMicrousd(state.analytics?.kpis.knownCostMicrousd??state.run?.run.spentMicrousd??null)}
          detail={state.spend?`Budget: ${formatMicrousd(state.spend.budgetMicrousd)}`:undefined}
          tone={state.spend&&state.spend.budgetMicrousd>0&&state.spend.spentMicrousd/state.spend.budgetMicrousd>0.9?'warning':'default'}/>
        <KpiCard icon={ShieldAlert} label="Violations"
          value={String(state.violations.length)}
          detail={criticalCount>0?`${criticalCount} critical · ${warningCount} warning`:`${warningCount} warning`}
          tone={criticalCount>0?'danger':warningCount>0?'warning':'success'}/>
      </div>

      <div className={styles['gov-grid']}>
        <section className={styles['gov-panel']}>
          <div className={styles['gov-panel-header']}>
            <h3><Activity size={16}/> Agent Actions</h3>
            <span className={styles['gov-badge']}>{state.run?.tasks.length??0} tasks</span>
          </div>
          {state.run&&taskStats&&<div className={styles['gov-task-stats']}>
            <div><span className={`${styles['task-stat']} succeeded`}><CheckCircle2 size={12}/>{taskStats.succeeded}</span></div>
            <div><span className={`${styles['task-stat']} failed`}><XCircle size={12}/>{taskStats.failed}</span></div>
            <div><span className={`${styles['task-stat']} running`}><Play size={12}/>{taskStats.running}</span></div>
            <div><span className={`${styles['task-stat']} pending`}><Clock3 size={12}/>{taskStats.pending}</span></div>
          </div>}
          <div className={styles['gov-table-wrap']}>
            <table className={styles['gov-table']}>
              <thead><tr><th></th><th>Task</th><th>Agent</th><th>Status</th><th>Attempts</th><th>Cost</th><th>Class</th></tr></thead>
              <tbody>
                {state.run?.tasks.slice(0,20).map(task=>{
                  const agent=state.run?.agents.find(a=>a.id===task.agentId);
                  return <AgentActionRow key={task.taskId} task={task} agentName={agent?.name}/>;
                })??<tr><td colSpan={7} className={styles['gov-empty']}>No tasks loaded</td></tr>}
              </tbody>
            </table>
          </div>
          {state.run&&state.run.tasks.length>20&&<p className={styles['gov-note']}>Showing 20 of {state.run.tasks.length} tasks</p>}
        </section>

        <section className={styles['gov-panel']}>
          <div className={styles['gov-panel-header']}>
            <h3><Shield size={16}/> Policy Violations</h3>
            <span className={`${styles['gov-badge']} ${criticalCount>0?'badge-danger':warningCount>0?'badge-warning':'badge-success'}`}>
              {state.violations.length}
            </span>
          </div>
          {state.violations.length>0?<div className={styles['gov-violations']}>
            {state.violations.slice(0,15).map(v=><ViolationItem key={v.id} violation={v}/>)}
          </div>:<div className={styles['gov-empty']}><ShieldCheck size={24}/><p>No policy violations detected</p></div>}
        </section>

        <section className={styles['gov-panel']}>
          <div className={styles['gov-panel-header']}>
            <h3><Gauge size={16}/> Trust Scores</h3>
            <span className={styles['gov-badge']}>{state.trustScores.length} entities</span>
          </div>
          {state.trustScores.length>0?<div className={styles['gov-trust-list']}>
            {state.trustScores.slice(0,10).map(ts=><div key={ts.entityId} className={styles['gov-trust-item']}>
              <div className={styles['gov-trust-header']}>
                <span className={styles['gov-trust-name']}>{ts.entityId.slice(0,16)}…</span>
                <span className={`${styles['gov-trust-type']} type-${ts.entityType}`}>{ts.entityType}</span>
              </div>
              <TrustScoreBar score={ts.score}/>
              <div className={styles['gov-trust-factors']}>
                {ts.factors.slice(0,3).map((f,i)=><span key={i} className={`${styles['trust-factor']} ${f.impact}`}>{f.label}</span>)}
              </div>
            </div>)}
          </div>:<div className={styles['gov-empty']}><Users size={24}/><p>No trust data available</p></div>}
        </section>

        <section className={styles['gov-panel']}>
          <div className={styles['gov-panel-header']}>
            <h3><DollarSign size={16}/> Spend Tracking</h3>
          </div>
          {state.spend?<>
            <div className={styles['gov-spend-summary']}>
              <div className={styles['gov-spend-row']}>
                <span>Budget</span>
                <strong>{formatMicrousd(state.spend.budgetMicrousd)}</strong>
              </div>
              <div className={styles['gov-spend-row']}>
                <span>Spent</span>
                <strong>{formatMicrousd(state.spend.spentMicrousd)}</strong>
              </div>
              <div className={styles['gov-spend-row']}>
                <span>Reserved</span>
                <strong>{formatMicrousd(state.spend.reservedMicrousd)}</strong>
              </div>
              <div className={styles['gov-spend-row']}>
                <span>Remaining</span>
                <strong className={state.spend.remainingMicrousd<0?'text-danger':''}>{formatMicrousd(state.spend.remainingMicrousd)}</strong>
              </div>
              {state.spend.costPerSuccessMicrousd!=null&&<div className={styles['gov-spend-row']}>
                <span>Cost / Success</span>
                <strong>{formatMicrousd(state.spend.costPerSuccessMicrousd)}</strong>
              </div>}
            </div>
            {state.spend.dailySpend.length>0&&<div className={styles['gov-spend-chart']}>
              <h4>Daily Spend (Last 14 Days)</h4>
              <div className={styles['gov-bar-chart']}>
                {state.spend.dailySpend.slice(-14).map(d=>{
                  const max=Math.max(...state.spend!.dailySpend.slice(-14).map(x=>x.amountMicrousd),1);
                  const height=d.amountMicrousd>0?Math.max(4,(d.amountMicrousd/max)*80):2;
                  return <div key={d.date} className={styles['gov-bar']} title={`${d.date}: ${formatMicrousd(d.amountMicrousd)}`}>
                    <div className={styles['gov-bar-fill']} style={{height:`${height}px`}}/>
                    <span className={styles['gov-bar-label']}>{d.date.slice(5)}</span>
                  </div>;
                })}
              </div>
            </div>}
            {state.spend.byTool.length>0&&<div className={styles['gov-spend-by-tool']}>
              <h4>Spend by Tool</h4>
              {state.spend.byTool.slice(0,5).map(t=><div key={t.tool} className={styles['gov-tool-spend']}>
                <span className={styles['gov-tool-name']}>{t.tool}</span>
                <span className={styles['gov-tool-amount']}>{formatMicrousd(t.amountMicrousd)}</span>
                <span className={styles['gov-tool-attempts']}>{t.attempts} attempts</span>
              </div>)}
            </div>}
          </>:<div className={styles['gov-empty']}><DollarSign size={24}/><p>No spend data available</p></div>}
        </section>
      </div>

      {state.run&&state.run.events.length>0&&<section className={`${styles['gov-panel']} ${styles['gov-events']}`}>
        <div className={styles['gov-panel-header']}>
          <h3><Eye size={16}/> Recent Events</h3>
          <span className={styles['gov-badge']}>{state.run.events.length}</span>
        </div>
        <div className={styles['gov-event-log']}>
          {state.run.events.slice(-10).reverse().map(event=><div key={event.sequence} className={styles['gov-event']}>
            <time>{event.at.slice(11,19)}</time>
            <span className={styles['gov-event-type']}>{event.type}</span>
            {event.taskId&&<span className={styles['gov-event-task']}>{event.taskId.slice(0,12)}…</span>}
          </div>)}
        </div>
      </section>}
    </>}

    {!state.run&&!state.analytics&&!state.loading&&<div className={styles['gov-empty-state']}>
      <Shield size={48}/>
      <h3>Governance Dashboard</h3>
      <p>Enter your private workspace token and click Refresh to load real-time agent governance data.</p>
    </div>}
  </div>;
}
