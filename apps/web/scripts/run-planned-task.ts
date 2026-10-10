import {executePlannedTask} from '../lib/integration-runtime';

const [runId,taskId,...extra]=process.argv.slice(2);
if(!runId||!taskId||extra.length){console.error('Usage: node --import tsx scripts/run-planned-task.ts RUN_ID TASK_ID');process.exitCode=2;}
else{
 const controller=new AbortController();
 const abort=()=>controller.abort();process.once('SIGINT',abort);process.once('SIGTERM',abort);
 const timer=setTimeout(abort,45_000);
 try{const result=await executePlannedTask(runId,taskId,process.env,controller.signal);console.log(JSON.stringify(result));}
 catch(error){console.error(error instanceof Error?error.message:'Planned task failed.');process.exitCode=1;}
 finally{clearTimeout(timer);process.removeListener('SIGINT',abort);process.removeListener('SIGTERM',abort);}
}
