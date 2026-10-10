import AppShell from '@/components/AppShell';
import PresentationStudio from '@/components/PresentationStudio';

/**
 * React component Page.
 *
 *
 * @example
 * ```typescript
 * import { Page } from './module';
 * ```
 */
export default function Page() {
/**
 * Next.js page component for page.
 *
 * @module page
 * @packageDocumentation
 */
  return <AppShell active="presentations"><PresentationStudio /></AppShell>;
}
