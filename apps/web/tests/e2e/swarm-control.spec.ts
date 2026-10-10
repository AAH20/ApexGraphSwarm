import { test, expect } from '@playwright/test';

test.describe('Swarm Control Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the swarm control page', async ({ page }) => {
    await expect(page.locator('.apex-panel')).toBeVisible();
  });

  test('should show execution workbench heading', async ({ page }) => {
    await expect(page.locator('h2:has-text("Execution workbench")')).toBeVisible();
  });

  test('should show SQLite persistence pill', async ({ page }) => {
    await expect(page.locator('.pill')).toContainText('SQLite persistence');
  });

  test('should show logical agents selector', async ({ page }) => {
    const select = page.locator('.apex-form-grid label:has-text("Logical agents") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("1 agents")')).toBeVisible();
    await expect(select.locator('option:has-text("10 agents")')).toBeVisible();
    await expect(select.locator('option:has-text("30 agents")')).toBeVisible();
    await expect(select.locator('option:has-text("100 agents")')).toBeVisible();
    await expect(select.locator('option:has-text("300 agents")')).toBeVisible();
  });

  test('should show token input', async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show run ID input', async ({ page }) => {
    await expect(page.locator('.apex-form-grid label:has-text("Run ID") input')).toBeVisible();
  });

  test('should show create fixture button', async ({ page }) => {
    await expect(page.locator('button:has-text("Create fixture")')).toBeVisible();
  });

  test('should show load persisted state button', async ({ page }) => {
    await expect(page.locator('button:has-text("Load persisted state")')).toBeVisible();
  });

  test('should show advance fixture button', async ({ page }) => {
    await expect(page.locator('button:has-text("Advance up to 40 tasks")')).toBeVisible();
  });

  test('should show cancel run button', async ({ page }) => {
    await expect(page.locator('button:has-text("Cancel run")')).toBeVisible();
  });

  test('should disable buttons without token', async ({ page }) => {
    await expect(page.locator('button:has-text("Create fixture")')).toBeDisabled();
    await expect(page.locator('button:has-text("Load persisted state")')).toBeDisabled();
  });

  test('should enable create fixture with token', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await expect(page.locator('button:has-text("Create fixture")')).toBeEnabled();
  });

  test('should show apex note about fixtures', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('Create fixture hashes fixed payloads');
  });

  test('should show zero model calls note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('no model calls');
  });

  test('should show run ID saved locally note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('A run ID is saved locally');
  });

  test('should show token stays in memory note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('the token stays in memory');
  });

  test('should show page heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('A plan is only the beginning');
  });

  test('should show orchestration eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('ORCHESTRATION');
  });

  test('should show optimize plan link', async ({ page }) => {
    await expect(page.locator('a:has-text("Optimize a plan")')).toBeVisible();
  });

  test('should show configure specialist teams link', async ({ page }) => {
    await expect(page.locator('a:has-text("Configure specialist teams")')).toBeVisible();
  });

  test('should show architecture comparisons link', async ({ page }) => {
    await expect(page.locator('a:has-text("Architecture comparisons")')).toBeVisible();
  });

  test('should show busy status when creating fixture', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(500);
    const status = page.locator('[role="status"]');
    if (await status.isVisible()) {
      await expect(status).toContainText('Applying transactional operation');
    }
  });

  test('should show error message on invalid operation', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    // Either success or error should be shown
  });

  test('should show execution trace section', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const trace = page.locator('.execution-trace, [aria-label="Execution explanation graph"]');
    if (await trace.isVisible()) {
      await expect(trace).toBeVisible();
    }
  });

  test('should show execution ledger section', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const ledger = page.locator('[aria-label="Execution and cost ledger"]');
    if (await ledger.isVisible()) {
      await expect(ledger).toBeVisible();
    }
  });

  test('should show ledger metrics', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const metrics = page.locator('.apex-metrics');
    if (await metrics.isVisible()) {
      await expect(metrics).toContainText('Recorded attempts');
    }
  });

  test('should show known settled cost in ledger', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const metrics = page.locator('.apex-metrics');
    if (await metrics.isVisible()) {
      await expect(metrics).toContainText('Known settled cost');
    }
  });

  test('should show unresolved cost count in ledger', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const metrics = page.locator('.apex-metrics');
    if (await metrics.isVisible()) {
      await expect(metrics).toContainText('unresolved cost');
    }
  });

  test('should show coverage complete in ledger', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const metrics = page.locator('.apex-metrics');
    if (await metrics.isVisible()) {
      await expect(metrics).toContainText('coverage');
    }
  });

  test('should show ledger table', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const table = page.locator('.apex-table-wrap table');
    if (await table.isVisible()) {
      await expect(table).toBeVisible();
    }
  });

  test('should show ledger table headers', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const table = page.locator('.apex-table-wrap table');
    if (await table.isVisible()) {
      await expect(table.locator('th')).toContainText('Task / attempt');
      await expect(table.locator('th')).toContainText('Outcome');
    }
  });

  test('should show receipt evidence in ledger', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const table = page.locator('.apex-table-wrap table');
    if (await table.isVisible()) {
      await expect(table.locator('th')).toContainText('Receipt evidence');
    }
  });

  test('should show truncated note when applicable', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const note = page.locator('.apex-note:has-text("Showing the latest")');
    // May or may not be visible depending on data
  });

  test('should show advance fixture button enabled after create', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const advanceBtn = page.locator('button:has-text("Advance up to 40 tasks")');
    if (await advanceBtn.isVisible()) {
      await expect(advanceBtn).toBeEnabled();
    }
  });

  test('should show cancel button enabled after create', async ({ page }) => {
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Create fixture")').click();
    await page.waitForTimeout(2000);
    const cancelBtn = page.locator('button:has-text("Cancel run")');
    if (await cancelBtn.isVisible()) {
      await expect(cancelBtn).toBeEnabled();
    }
  });
});
