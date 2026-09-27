import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'ApexGraphSwarm · Agent Engineering',description:'Engineer source-grounded agents, inspect graph relationships, benchmark orchestration and account for every execution.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
