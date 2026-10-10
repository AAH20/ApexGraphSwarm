import {execFileSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const root=fileURLToPath(new URL('../../../',import.meta.url));
const output=resolve(root,'apps/web/public');
mkdirSync(output,{recursive:true});
execFileSync('python3',['-m','apexgraphswarm','graph',root,'--output',resolve(output,'repository-graph.json')],{cwd:root,stdio:'inherit'});
console.log('ApexGraphSwarm source graph refreshed; no source code or model executed.');
