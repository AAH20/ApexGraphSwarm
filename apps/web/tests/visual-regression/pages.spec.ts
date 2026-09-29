import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PAGES = [
  { path: '/', name: 'home' },
  { path: '/analytics', name: 'analytics' },
  { path: '/arena', name: 'arena' },
  { path: '/decisions', name: 'decisions' },
  { path: '/delegation', name: 'delegation' },
  { path: '/ecosystem', name: 'ecosystem' },
  { path: '/ecosystem/research', name: 'ecosystem-research' },
  { path: '/evaluations', name: 'evaluations' },
  { path: '/graph', name: 'graph' },
  { path: '/graph-enhanced', name: 'graph-enhanced' },
  { path: '/optimization', name: 'optimization' },
  { path: '/presentations', name: 'presentations' },
  { path: '/swarm', name: 'swarm' },
  { path: '/teams', name: 'teams' },
];

const BASELINE_DIR = path.join(__dirname, 'baselines');
const ACTUAL_DIR = path.join(__dirname, 'actual');
const DIFF_DIR = path.join(__dirname, 'diff');

// Ensure directories exist
for (const dir of [BASELINE_DIR, ACTUAL_DIR, DIFF_DIR]) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function compareImages(baselinePath: string, actualPath: string, diffPath: string): { diffPixels: number; totalPixels: number; diffPercentage: number } {
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  const actual = PNG.sync.read(fs.readFileSync(actualPath));
  
  const { width, height } = baseline;
  const diff = new PNG({ width, height });
  
  const diffPixels = pixelmatch(
    baseline.data,
    actual.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );
  
  fs.writeFileSync(diffPath, PNG.sync.write(diff));
  
  const totalPixels = width * height;
  const diffPercentage = (diffPixels / totalPixels) * 100;
  
  return { diffPixels, totalPixels, diffPercentage };
}

test.describe('Visual Regression Tests', () => {
  for (const page of PAGES) {
    test(`screenshot ${page.name}`, async ({ page: browserPage }) => {
      await browserPage.goto(page.path, { waitUntil: 'networkidle' });
      await browserPage.waitForTimeout(1000); // Allow animations to settle

      const baselinePath = path.join(BASELINE_DIR, `${page.name}.png`);
      const actualPath = path.join(ACTUAL_DIR, `${page.name}.png`);
      const diffPath = path.join(DIFF_DIR, `${page.name}.png`);

      // Take screenshot
      await browserPage.screenshot({
        path: actualPath,
        fullPage: true,
      });

      // If baseline doesn't exist, create it and skip comparison
      if (!fs.existsSync(baselinePath)) {
        fs.copyFileSync(actualPath, baselinePath);
        test.info().annotations.push({
          type: 'baseline-created',
          description: `Baseline created for ${page.name}`,
        });
        return;
      }

      // Compare screenshots using pixel-level comparison
      const { diffPixels, totalPixels, diffPercentage } = compareImages(baselinePath, actualPath, diffPath);

      // Fail if more than 1% of pixels differ
      expect(diffPercentage).toBeLessThan(1);
    });
  }
});
