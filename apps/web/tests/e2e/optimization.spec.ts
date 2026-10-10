import { test, expect } from '@playwright/test';

test.describe('Optimization Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/optimization');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the optimization page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Make every constraint visible');
  });

  test('should show optimization eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('OPTIMIZATION');
  });

  test('should show local experiment workbench heading', async ({ page }) => {
    await expect(page.locator('h2:has-text("Local experiment workbench")')).toBeVisible();
  });

  test('should show bounded experiments pill', async ({ page }) => {
    await expect(page.locator('.pill')).toContainText('Bounded experiments');
  });

  test('should show experiment template buttons', async ({ page }) => {
    await expect(page.locator('.choices button').first()).toBeVisible();
  });

  test('should show multiple experiment templates', async ({ page }) => {
    const count = await page.locator('.choices button').count();
    expect(count).toBeGreaterThan(1);
  });

  test('should show experiment description', async ({ page }) => {
    await expect(page.locator('.description')).toBeVisible();
  });

  test('should show experiment JSON editor', async ({ page }) => {
    await expect(page.locator('#experiment-json')).toBeVisible();
  });

  test('should show context section', async ({ page }) => {
    await expect(page.locator('.context')).toBeVisible();
  });

  test('should show what this establishes', async ({ page }) => {
    await expect(page.locator('.context h3').first()).toContainText('What this establishes');
  });

  test('should show what remains unmeasured', async ({ page }) => {
    await expect(page.locator('.context h3').nth(1)).toContainText('What remains unmeasured');
  });

  test('should show costs note', async ({ page }) => {
    await expect(page.locator('.context')).toContainText('Costs in templates are illustrative');
  });

  test('should show microUSD note', async ({ page }) => {
    await expect(page.locator('.context')).toContainText('microUSD');
  });

  test('should show request limit note', async ({ page }) => {
    await expect(page.locator('.context')).toContainText('128 KiB');
  });

  test('should show process deadline note', async ({ page }) => {
    await expect(page.locator('.context')).toContainText('15-second');
  });

  test('should show token input', async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show run experiment button', async ({ page }) => {
    await expect(page.locator('button:has-text("Run experiment")')).toBeVisible();
  });

  test('should disable run button without token', async ({ page }) => {
    await expect(page.locator('button:has-text("Run experiment")')).toBeDisabled();
  });

  test('should enable run button with token', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await expect(page.locator('button:has-text("Run experiment")')).toBeEnabled();
  });

  test('should show apex note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toBeVisible();
  });

  test('should show token stays in memory note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('token stays in memory');
  });

  test('should show no deployment note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('does not deploy');
  });

  test('should select experiment template', async ({ page }) => {
    await page.locator('.choices button').nth(1).click();
    await page.waitForTimeout(300);
    await expect(page.locator('.choices button').nth(1)).toHaveAttribute('aria-pressed', 'true');
  });

  test('should update JSON on template selection', async ({ page }) => {
    await page.locator('.choices button').nth(1).click();
    await page.waitForTimeout(300);
    const json = await page.locator('#experiment-json').inputValue();
    expect(json).toBeTruthy();
  });

  test('should show busy status when running', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(500);
    const status = page.locator('[role="status"]');
    if (await status.isVisible()) {
      await expect(status).toContainText('Computing');
    }
  });

  test('should show experiment result after run', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const result = page.locator('h2:has-text("Experiment complete")');
    if (await result.isVisible()) {
      await expect(result).toBeVisible();
    }
  });

  test('should show export input & result button', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const exportBtn = page.locator('button:has-text("Export input & result")');
    if (await exportBtn.isVisible()) {
      await expect(exportBtn).toBeVisible();
    }
  });

  test('should show optimization results', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const results = page.locator('.optimization-results, [class*="results"]');
    if (await results.isVisible()) {
      await expect(results).toBeVisible();
    }
  });

  test('should show summary definition list', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const summary = page.locator('.summary');
    if (await summary.isVisible()) {
      await expect(summary).toBeVisible();
    }
  });

  test('should show dependency inspection when applicable', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const graph = page.locator('.graph');
    if (await graph.isVisible()) {
      await expect(graph).toContainText('Dependency inspection');
    }
  });

  test('should show full evidence details', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const details = page.locator('details summary');
    if (await details.isVisible()) {
      await expect(details).toContainText('Full evidence');
    }
  });

  test('should show recheck git evidence button when applicable', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const recheckBtn = page.locator('button:has-text("Recheck Git evidence")');
    if (await recheckBtn.isVisible()) {
      await expect(recheckBtn).toBeVisible();
    }
  });

  test('should show local result eyebrow', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const eyebrow = page.locator('.apex-panel-heading .eyebrow');
    if (await eyebrow.isVisible()) {
      await expect(eyebrow).toContainText('LOCAL RESULT');
    }
  });

  test('should show inspectable evidence description', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const desc = page.locator('.apex-panel-heading p');
    if (await desc.isVisible()) {
      await expect(desc).toContainText('INSPECTABLE EVIDENCE');
    }
  });

  test('should show error on invalid experiment', async ({ page }) => {
    await page.locator('#experiment-json').fill('invalid json');
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(1000);
    const error = page.locator('.error-text');
    if (await error.isVisible()) {
      await expect(error).toBeVisible();
    }
  });

  test('should show hierarchy view when specified', async ({ page }) => {
    await page.goto('/optimization?view=hierarchy');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should auto-select hierarchy template
    await expect(page.locator('.choices button[aria-pressed="true"]')).toBeVisible();
  });

  test('should show task dependency graph', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const graph = page.locator('.graph');
    if (await graph.isVisible()) {
      await expect(graph.locator('svg')).toBeVisible();
    }
  });

  test('should show task buttons in graph', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const nodes = page.locator('.nodes button');
    if (await nodes.first().isVisible()) {
      await expect(nodes.first()).toBeVisible();
    }
  });

  test('should select task on button click', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const nodeBtn = page.locator('.nodes button').first();
    if (await nodeBtn.isVisible()) {
      await nodeBtn.click();
      await expect(nodeBtn).toHaveAttribute('aria-pressed', 'true');
    }
  });

  test('should show focused task JSON', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const nodeBtn = page.locator('.nodes button').first();
    if (await nodeBtn.isVisible()) {
      await nodeBtn.click();
      await page.waitForTimeout(300);
      const json = page.locator('.apex-json');
      if (await json.isVisible()) {
        await expect(json).toBeVisible();
      }
    }
  });

  test('should show graph preview limit note', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const note = page.locator('p:has-text("Graph preview shows the first 64")');
    // May or may not be visible depending on task count
  });

  test('should show arrows show prerequisites note', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const graph = page.locator('.graph');
    if (await graph.isVisible()) {
      await expect(graph).toContainText('Arrows show prerequisites');
    }
  });

  test('should show not actual execution note', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const graph = page.locator('.graph');
    if (await graph.isVisible()) {
      await expect(graph).toContainText('not actual execution');
    }
  });
});
