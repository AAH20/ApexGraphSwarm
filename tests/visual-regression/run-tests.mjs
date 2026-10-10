#!/usr/bin/env node
/**
 * Visual Regression Test Runner
 * 
 * This script runs visual regression tests for the entire project.
 * It delegates to the web app's Playwright tests.
 * 
 * Usage: node tests/visual-regression/run-tests.mjs
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..');
const webAppDir = path.join(projectRoot, 'apps', 'web');

console.log('🎨 Running Visual Regression Tests...\n');

// Check if dev server is running
try {
  const response = await fetch('http://127.0.0.1:3010');
  if (!response.ok) {
    throw new Error('Server not ready');
  }
  console.log('✓ Development server is running\n');
} catch (error) {
  console.log('⚠ Development server is not running.');
  console.log('Please start it first:');
  console.log('  cd apps/web && npm run dev\n');
  process.exit(1);
}

// Run tests
try {
  execSync('npx playwright test tests/visual-regression/pages.spec.ts', {
    stdio: 'inherit',
    cwd: webAppDir,
  });
  console.log('\n✅ All visual regression tests passed!');
  process.exit(0);
} catch (error) {
  console.log('\n❌ Some visual regression tests failed.');
  console.log('Check the report at: apps/web/tests/visual-regression/report/index.html');
  process.exit(1);
}
