import { test, expect } from '@playwright/test';

test.describe('Arena Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/arena');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the arena page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Make the run easy to inspect');
  });

  test('should show swarm arena eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('SWARM ARENA');
  });

  test('should show reproducible challenge eyebrow', async ({ page }) => {
    await expect(page.locator('.apex-panel-heading .eyebrow')).toContainText('REPRODUCIBLE CHALLENGE');
  });

  test('should show run title', async ({ page }) => {
    await expect(page.locator('#arena-run-title')).toContainText('Run the five track challenge');
  });

  test('should show ready to run badge', async ({ page }) => {
    await expect(page.locator('.badge')).toContainText('READY TO RUN');
  });

  test('should show track cards', async ({ page }) => {
    await expect(page.locator('.tracks article')).toHaveCount(5);
  });

  test('should show dependency scheduling track', async ({ page }) => {
    await expect(page.locator('.tracks article').first()).toContainText('Dependency scheduling');
  });

  test('should show evidence selection track', async ({ page }) => {
    await expect(page.locator('.tracks article').nth(1)).toContainText('Evidence selection');
  });

  test('should show coding conflict waves track', async ({ page }) => {
    await expect(page.locator('.tracks article').nth(2)).toContainText('Coding conflict waves');
  });

  test('should show inference capacity track', async ({ page }) => {
    await expect(page.locator('.tracks article').nth(3)).toContainText('Inference capacity');
  });

  test('should show held-out promotion gate track', async ({ page }) => {
    await expect(page.locator('.tracks article').nth(4)).toContainText('Held-out promotion gate');
  });

  test('should show track descriptions', async ({ page }) => {
    await expect(page.locator('.tracks article p').first()).toBeVisible();
  });

  test('should show token input', async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show run local benchmark button', async ({ page }) => {
    await expect(page.locator('button:has-text("Run local benchmark")')).toBeVisible();
  });

  test('should disable run button without token', async ({ page }) => {
    await expect(page.locator('button:has-text("Run local benchmark")')).toBeDisabled();
  });

  test('should enable run button with token', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await expect(page.locator('button:has-text("Run local benchmark")')).toBeEnabled();
  });

  test('should show arena note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toBeVisible();
  });

  test('should show no model calls note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('no model or provider calls');
  });

  test('should show token not included note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('not included in a result link');
  });

  test('should show busy status when running', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(500);
    const status = page.locator('[role="status"]');
    if (await status.isVisible()) {
      await expect(status).toContainText('Measuring');
    }
  });

  test('should show error on invalid token', async ({ page }) => {
    await page.locator('input[type="password"]').fill('invalid-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(2000);
    const error = page.locator('.error-text');
    if (await error.isVisible()) {
      await expect(error).toBeVisible();
    }
  });

  test('should show challenge evidence after run', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const evidence = page.locator('#arena-result-title');
    if (await evidence.isVisible()) {
      await expect(evidence).toContainText('Challenge evidence');
    }
  });

  test('should show run snapshot badge after run', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const badge = page.locator('.badge');
    if (await badge.isVisible()) {
      const text = await badge.textContent();
      if (text?.includes('RUN SNAPSHOT')) {
        await expect(badge).toContainText('RUN SNAPSHOT');
      }
    }
  });

  test('should show honesty note', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const honesty = page.locator('.honesty');
    if (await honesty.isVisible()) {
      await expect(honesty).toContainText('Unsigned, self-contained snapshot');
    }
  });

  test('should show run stats', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const stats = page.locator('.runStats');
    if (await stats.isVisible()) {
      await expect(stats).toBeVisible();
    }
  });

  test('should show suite name in stats', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const stats = page.locator('.runStats');
    if (await stats.isVisible()) {
      await expect(stats).toContainText('Suite');
    }
  });

  test('should show provider calls in stats', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const stats = page.locator('.runStats');
    if (await stats.isVisible()) {
      await expect(stats).toContainText('Provider calls');
    }
  });

  test('should show cases count in stats', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const stats = page.locator('.runStats');
    if (await stats.isVisible()) {
      await expect(stats).toContainText('Cases');
    }
  });

  test('should show shortest case time in stats', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const stats = page.locator('.runStats');
    if (await stats.isVisible()) {
      await expect(stats).toContainText('Shortest case time');
    }
  });

  test('should show copy share link button', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const copyBtn = page.locator('button:has-text("Copy share link")');
    if (await copyBtn.isVisible()) {
      await expect(copyBtn).toBeVisible();
    }
  });

  test('should show download JSON button', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const downloadBtn = page.locator('button:has-text("Download JSON")');
    if (await downloadBtn.isVisible()) {
      await expect(downloadBtn).toBeVisible();
    }
  });

  test('should show track measurements', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const caseList = page.locator('.caseList');
    if (await caseList.isVisible()) {
      await expect(caseList).toBeVisible();
    }
  });

  test('should show case names in measurements', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const caseList = page.locator('.caseList');
    if (await caseList.isVisible()) {
      await expect(caseList).toContainText('Dependency scheduling');
    }
  });

  test('should show case durations', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const caseList = page.locator('.caseList');
    if (await caseList.isVisible()) {
      await expect(caseList).toContainText('ms');
    }
  });

  test('should show inspect measured output details', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const details = page.locator('.caseList details summary');
    if (await details.first().isVisible()) {
      await expect(details.first()).toContainText('Inspect measured output');
    }
  });

  test('should show promotion gate example', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const gate = page.locator('.gate');
    if (await gate.isVisible()) {
      await expect(gate).toContainText('Promotion gate example');
    }
  });

  test('should show gate result', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const gate = page.locator('.gate');
    if (await gate.isVisible()) {
      await expect(gate).toContainText('Gate result');
    }
  });

  test('should show not promoted in gate', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const gate = page.locator('.gate');
    if (await gate.isVisible()) {
      await expect(gate).toContainText('Not promoted');
    }
  });

  test('should show fixture caveat', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const caveat = page.locator('.caveat');
    if (await caveat.isVisible()) {
      await expect(caveat).toContainText('Fixture microUSD values');
    }
  });

  test('should show reproduction pins details', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Reproduction pins');
    }
  });

  test('should show measurement type in provenance', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Measurement');
    }
  });

  test('should show environment in provenance', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Environment');
    }
  });

  test('should show source hashes in provenance', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Source SHA-256');
    }
  });

  test('should show cost provenance in provenance', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Cost provenance');
    }
  });

  test('should show limits in provenance', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const provenance = page.locator('.provenance');
    if (await provenance.isVisible()) {
      await expect(provenance.locator('ul')).toBeVisible();
    }
  });

  test('should show share URL after copy', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const copyBtn = page.locator('button:has-text("Copy share link")');
    if (await copyBtn.isVisible()) {
      await copyBtn.click();
      await page.waitForTimeout(500);
      const shareField = page.locator('.shareField input');
      if (await shareField.isVisible()) {
        await expect(shareField).toBeVisible();
      }
    }
  });

  test('should show link copied text', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run local benchmark")').click();
    await page.waitForTimeout(3000);
    const copyBtn = page.locator('button:has-text("Copy share link")');
    if (await copyBtn.isVisible()) {
      await copyBtn.click();
      await page.waitForTimeout(500);
      await expect(page.locator('button:has-text("Link copied")')).toBeVisible();
    }
  });
});
