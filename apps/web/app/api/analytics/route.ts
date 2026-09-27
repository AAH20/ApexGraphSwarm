import {analyticsOperation} from '@/lib/analytics-client';
import {assertJsonPrecision} from '@/lib/optimization-json';
import {hasIntegrationSafeOrigin,isIntegrationAuthorized} from '@/lib/integration-runtime';
export const runtime='nodejs';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
let active=0;
export async function POST(request:Request){
 if(!isIntegrationAuthorized(request)||!hasIntegrationSafeOrigin(request))return Response.json({error:'Enter the private workspace execution token.'},{status:401,headers});
 if(!request.headers.get('content-type')?.startsWith('application/json'))return Response.json({error:'JSON is required.'},{status:415,headers});
 if(active>=2)return Response.json({error:'Two analytics queries are running. Try again after completion.'},{status:429,headers});
 active++;
 try{
  if(!request.body)throw Error('A request is required.');
  const reader=request.body.getReader(),decoder=new TextDecoder();let text='',bytes=0;
  while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>2097152){await reader.cancel();throw Error('Request exceeds 2 MiB.');}text+=decoder.decode(value,{stream:true});}
  const body=JSON.parse(text+decoder.decode());assertJsonPrecision(body);
  if(!body||typeof body!=='object'||Array.isArray(body)||Object.keys(body).some(key=>!['source','days','tool','rows'].includes(key)))throw Error('Only source, days, tool and rows are accepted.');
  if(!['live','import'].includes(body.source))throw Error('Choose recorded data or an event import.');
  return Response.json({result:await analyticsOperation(body)},{headers});
 }catch(error){const message=error instanceof Error?error.message:'Analytics failed.';return Response.json({error:message.replace(/\/(?:Users|private|tmp)\/[^\s]+/g,'[local path]').slice(0,240)},{status:400,headers});}
 finally{active--;}
}
