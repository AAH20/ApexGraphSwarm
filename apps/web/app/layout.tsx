import type {Metadata} from 'next';
import './globals.css';
/**
 * Constant metadata.
 *
 *
 * @example
 * ```typescript
 * import { metadata } from './module';
 * ```
 */
export const metadata:Metadata={title:'ApexGraphSwarm · Agent Engineering',description:'Engineer source-grounded agents, inspect graph relationships, benchmark orchestration and account for every execution.'};
/**
 * React component RootLayout.
 *
 * @param {{children} children - Description of children.
 *
 * @example
 * ```typescript
 * const result = RootLayout(...);
 * ```
 */
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
