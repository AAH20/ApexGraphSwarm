import {controlOperation} from '@/lib/control-client';
import {hasIntegrationSafeOrigin,isIntegrationAuthorized} from '@/lib/integration-runtime';
export const runtime='nodejs';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
export async function POST(request:Request){
 if(!isIntegrationAuthorized(request)||!hasIntegrationSafeOrigin(request))return Response.json({error:'Enter the private workspace execution token.'},{status:401,headers});
 if(!request.headers.get('content-type')?.startsWith('application/json'))return Response.json({error:'JSON is required.'},{status:415,headers});
 if(!request.body)return Response.json({error:'A request is required.'},{status:400,headers});
 const reader=request.body.getReader();let text='',bytes=0;const decoder=new TextDecoder();
 try{
  while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>4096){await reader.cancel();throw Error('Request exceeds 4 KB.');}text+=decoder.decode(value,{stream:true});}
  text+=decoder.decode();const body=JSON.parse(text);
  if(!body||typeof body!=='object'||Object.keys(body).some(k=>!['action','agents','runId','idempotencyKey'].includes(k)))throw Error('Unexpected request fields.');
  if(!['createFixture','status','advanceFixture','cancel'].includes(body.action))throw Error('Unsupported operation.');
  if(body.action==='createFixture'){
   if(![1,10,30,100,300].includes(body.agents)||typeof body.idempotencyKey!=='string'||!/^[a-zA-Z0-9_-]{8,100}$/.test(body.idempotencyKey))throw Error('Invalid fixture parameters.');
  }else if(typeof body.runId!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(body.runId))throw Error('A valid run ID is required.');
  return Response.json({state:await controlOperation(body)},{headers});
 }catch(error){const message=error instanceof Error?error.message:'Control request failed.';return Response.json({error:message.replace(/\/(?:Users|private|tmp)\/[^\s]+/g,'[local path]').slice(0,300)},{status:400,headers});}
}
