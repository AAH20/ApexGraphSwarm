#!/usr/bin/env node
/**
 * Update visual regression baselines
 * 
 * Usage: node scripts/update-visual-baselines.mjs
 * 
 * This script runs the visual regression tests and updates the baselines
 * for any pages that have changed.
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';

const BASELINE_DIR = path.join(__dirname, '..', 'tests', 'visual-regression', 'baselines');
const ACTUAL_DIR = path.join(__dirname, '..', 'tests', 'visual-regression', 'actual');

console.log('Updating visual regression baselines...');

// Run tests to generate actual screenshots
try {
  execSync('npx playwright test tests/visual-regression/pages.spec.ts --update-snapshots', {
    stdio: 'inherit',
    cwd: path.join(__dirname, '..'),
  });
} catch (error) {
  console.log('Tests completed (some may have failed as expected)');
}

// Copy actual screenshots to baselines
if (fs.existsSync(ACTUAL_DIR)) {
  const files = fs.readdirSync(ACTUAL_DIR);
  for (const file of files) {
    if (file.endsWith('.png')) {
      const src = path.join(ACTUAL_DIR, file);
      const dest = path.join(BASELINE_DIR, file);
      fs.copyFileSync(src, dest);
      console.log(`Updated baseline: ${file}`);
    }
  }
}

console.log('Baseline update complete!');
