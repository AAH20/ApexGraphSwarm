import {IntegrationRuntime} from './integration-runtime';

/**
 * Core library module for integration runtime instance.ts functionality.
 *
 * @module integration-runtime-instance
 * @packageDocumentation
 */
const globalRuntime=globalThis as typeof globalThis&{__playAnythingIntegrationRuntime?:IntegrationRuntime;__playAnythingIntegrationRuntimeVersion?:number};
const runtimeVersion=4;
if(globalRuntime.__playAnythingIntegrationRuntimeVersion!==runtimeVersion){globalRuntime.__playAnythingIntegrationRuntime=new IntegrationRuntime();globalRuntime.__playAnythingIntegrationRuntimeVersion=runtimeVersion;}
/**
 * Constant integrationRuntime.
 *
 *
 * @example
 * ```typescript
 * import { integrationRuntime } from './module';
 * ```
 */
export const integrationRuntime=globalRuntime.__playAnythingIntegrationRuntime!;
