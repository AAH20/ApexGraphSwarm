#!/usr/bin/env node
/**
 * Update Visual Regression Baselines
 * 
 * This script updates the baseline screenshots for all pages.
 * Run this after making intentional UI changes.
 * 
 * Usage: node tests/visual-regression/update-baselines.mjs
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..');
const webAppDir = path.join(projectRoot, 'apps', 'web');

console.log('🔄 Updating Visual Regression Baselines...\n');

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

// Run tests with update flag
try {
  execSync('npx playwright test tests/visual-regression/pages.spec.ts --update-snapshots', {
    stdio: 'inherit',
    cwd: webAppDir,
  });
  console.log('\n✅ Baselines updated successfully!');
  console.log('Review the changes and commit them.');
  process.exit(0);
} catch (error) {
  console.log('\n❌ Failed to update baselines.');
  process.exit(1);
}
