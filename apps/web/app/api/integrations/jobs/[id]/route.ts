import {NextResponse} from 'next/server';
import {integrationRuntime} from '@/lib/integration-runtime-instance';
import {hasIntegrationSafeOrigin,isIntegrationAuthorized} from '@/lib/integration-runtime';

/**
 * Constant runtime.
 *
 *
 * @example
 * ```typescript
 * import { runtime } from './module';
 * ```
 */
export const runtime='nodejs';
/**
 * Constant dynamic.
 *
 *
 * @example
 * ```typescript
 * import { dynamic } from './module';
 * ```
 */
export const dynamic='force-dynamic';
/**
 * API route handler for integrations jobs [id] endpoints.
 *
 * @module route
 * @packageDocumentation
 */
/**
 * Type RouteContext.
 *
 *
 * @example
 * ```typescript
 * import { RouteContext } from './module';
 * ```
 */
type RouteContext={params:Promise<{id:string}>};
const noStore={'Cache-Control':'no-store, max-age=0'};
/**
 * Function authorized.
 *
 * @param {Request} request - Description of request.
 *
 * @example
 * ```typescript
 * const result = authorized(...);
 * ```
 */
function authorized(request:Request){return isIntegrationAuthorized(request)&&hasIntegrationSafeOrigin(request);}

/**
 * Function GET.
 *
 * @param {Request} request - Description of request.
 * @param {RouteContext} context - Description of context.
 *
 * @example
 * ```typescript
 * const result = GET(..., ...);
 * ```
 */
/**
 * API route handler for GET requests.
 *
 * @param {Request} request - Description of request.
 * @param {RouteContext} context - Description of context.
 *
 * @example
 * ```typescript
 * const result = GET(..., ...);
 * ```
 */
export async function GET(request:Request,context:RouteContext){if(!authorized(request))return NextResponse.json({error:'Unauthorized integration request.'},{status:401,headers:noStore});const {id}=await context.params;const job=integrationRuntime.get(id);return job?NextResponse.json({job},{headers:noStore}):NextResponse.json({error:'Integration job not found.'},{status:404,headers:noStore});}

/**
 * Function DELETE.
 *
 * @param {Request} request - Description of request.
 * @param {RouteContext} context - Description of context.
 *
 * @example
 * ```typescript
 * const result = DELETE(..., ...);
 * ```
 */
/**
 * API route handler for DELETE requests.
 *
 * @param {Request} request - Description of request.
 * @param {RouteContext} context - Description of context.
 *
 * @example
 * ```typescript
 * const result = DELETE(..., ...);
 * ```
 */
export async function DELETE(request:Request,context:RouteContext){if(!authorized(request))return NextResponse.json({error:'Unauthorized integration request.'},{status:401,headers:noStore});const {id}=await context.params;const job=await integrationRuntime.cancel(id);return job?NextResponse.json({job},{headers:noStore}):NextResponse.json({error:'Integration job not found.'},{status:404,headers:noStore});}
