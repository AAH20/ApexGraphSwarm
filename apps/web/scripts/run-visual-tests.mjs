#!/usr/bin/env node
/**
 * Run visual regression tests
 * 
 * Usage: node scripts/run-visual-tests.mjs
 * 
 * This script runs the visual regression tests and generates a report.
 */

import { execSync } from 'child_process';
import path from 'path';

console.log('Running visual regression tests...');

try {
  execSync('npx playwright test tests/visual-regression/pages.spec.ts', {
    stdio: 'inherit',
    cwd: path.join(__dirname, '..'),
  });
  console.log('\n✅ All visual regression tests passed!');
  process.exit(0);
} catch (error) {
  console.log('\n❌ Some visual regression tests failed.');
  console.log('Check the report at: tests/visual-regression/report/index.html');
  process.exit(1);
}
