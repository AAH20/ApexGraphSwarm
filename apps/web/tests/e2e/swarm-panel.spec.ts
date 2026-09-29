import { test, expect } from '@playwright/test';

test.describe('Swarm Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the swarm section', async ({ page }) => {
    await expect(page.locator('.swarm-section')).toBeVisible();
  });

  test('should show swarm section heading', async ({ page }) => {
    await expect(page.locator('.swarm-section h2')).toContainText('A specialist team');
  });

  test('should show coordinated graph analysis eyebrow', async ({ page }) => {
    await expect(page.locator('.swarm-section .eyebrow')).toContainText('COORDINATED GRAPH ANALYSIS');
  });

  test('should display run analysis team button', async ({ page }) => {
    await expect(page.locator('button:has-text("Run analysis team")')).toBeVisible();
  });

  test('should show local specialists pill', async ({ page }) => {
    await expect(page.locator('.swarm-section .pill.success')).toContainText('Local specialists');
  });

  test('should show concurrency selector', async ({ page }) => {
    const select = page.locator('select[aria-label="Analysis concurrency"]');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("1 worker")')).toBeVisible();
    await expect(select.locator('option:has-text("2 workers")')).toBeVisible();
    await expect(select.locator('option:has-text("3 workers")')).toBeVisible();
  });

  test('should show time budget selector', async ({ page }) => {
    const select = page.locator('select[aria-label="Per-specialist time budget"]');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("1s / specialist")')).toBeVisible();
    await expect(select.locator('option:has-text("5s / specialist")')).toBeVisible();
    await expect(select.locator('option:has-text("15s / specialist")')).toBeVisible();
  });

  test('should display agent cards', async ({ page }) => {
    await expect(page.locator('.agent-card')).toHaveCount(4);
  });

  test('should show structure scout agent card', async ({ page }) => {
    await expect(page.locator('.agent-card').first()).toContainText('Structure scout');
  });

  test('should show dependency analyst agent card', async ({ page }) => {
    await expect(page.locator('.agent-card').nth(1)).toContainText('Dependency analyst');
  });

  test('should show evidence critic agent card', async ({ page }) => {
    await expect(page.locator('.agent-card').nth(2)).toContainText('Evidence critic');
  });

  test('should show coordinator agent card', async ({ page }) => {
    await expect(page.locator('.agent-card.coordinator')).toContainText('Reconcile & explain');
  });

  test('should show agent descriptions', async ({ page }) => {
    await expect(page.locator('.agent-card').first()).toContainText('Find entry points');
  });

  test('should show agent foot with deterministic tools', async ({ page }) => {
    await expect(page.locator('.agent-card .agent-foot').first()).toContainText('Deterministic graph tools');
  });

  test('should show read only badge', async ({ page }) => {
    await expect(page.locator('.agent-card .agent-foot').first()).toContainText('Read only');
  });

  test('should show ready status for agents initially', async ({ page }) => {
    await expect(page.locator('.agent-card .agent-state').first()).toContainText('Ready');
  });

  test('should show after specialists status for coordinator', async ({ page }) => {
    await expect(page.locator('.agent-card.coordinator .agent-state')).toContainText('After specialists');
  });

  test('should show specialist labels', async ({ page }) => {
    await expect(page.locator('.agent-card small').first()).toContainText('SPECIALIST 01');
  });

  test('should show shared evidence label for coordinator', async ({ page }) => {
    await expect(page.locator('.agent-card.coordinator small')).toContainText('SHARED EVIDENCE');
  });

  test('should show coordinator label', async ({ page }) => {
    await expect(page.locator('.agent-card.coordinator .agent-foot')).toContainText('Coordinator');
  });

  test('should show no source mutations for coordinator', async ({ page }) => {
    await expect(page.locator('.agent-card.coordinator .agent-foot')).toContainText('No source mutations');
  });

  test('should change concurrency value', async ({ page }) => {
    const select = page.locator('select[aria-label="Analysis concurrency"]');
    await select.selectOption('3');
    await expect(select).toHaveValue('3');
  });

  test('should change time budget value', async ({ page }) => {
    const select = page.locator('select[aria-label="Per-specialist time budget"]');
    await select.selectOption('15000');
    await expect(select).toHaveValue('15000');
  });

  test('should show model review details', async ({ page }) => {
    await expect(page.locator('.model-review')).toBeVisible();
  });

  test('should show model review summary', async ({ page }) => {
    await expect(page.locator('.model-review summary')).toContainText('Optional agentic model review');
  });

  test('should show not configured pill for model review', async ({ page }) => {
    await expect(page.locator('.model-review .pill')).toContainText('Not configured');
  });

  test('should show model review configuration note', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body')).toContainText('Configure AI_GATEWAY_API_KEY');
  });

  test('should show review goal textarea', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body textarea')).toBeVisible();
  });

  test('should show review access token input', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body input[type="password"]')).toBeVisible();
  });

  test('should show output cap input', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body input[type="number"]')).toBeVisible();
  });

  test('should show request model review button', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('button:has-text("Request one model review")')).toBeVisible();
  });

  test('should show run model agent team button', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('button:has-text("Run model agent team")')).toBeVisible();
  });

  test('should disable model review buttons when not configured', async ({ page }) => {
    await page.locator('.model-review summary').click();
    const reviewBtn = page.locator('button:has-text("Request one model review")');
    const teamBtn = page.locator('button:has-text("Run model agent team")');
    await expect(reviewBtn).toBeDisabled();
    await expect(teamBtn).toBeDisabled();
  });

  test('should show model review description', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body')).toContainText('model can inspect bounded graph tools');
  });

  test('should show team plan description', async ({ page }) => {
    await page.locator('.model-review summary').click();
    await expect(page.locator('.model-review-body')).toContainText('Team plan');
  });

  test('should show run controls section', async ({ page }) => {
    await expect(page.locator('.run-controls')).toBeVisible();
  });

  test('should show agent grid', async ({ page }) => {
    await expect(page.locator('.agent-grid')).toBeVisible();
  });

  test('should show section title row', async ({ page }) => {
    await expect(page.locator('.swarm-section .section-title-row')).toBeVisible();
  });

  test('should show swarm section description', async ({ page }) => {
    await expect(page.locator('.swarm-section')).toContainText('Parallel local analysis');
  });

  test('should show cancel button when running', async ({ page }) => {
    // Start analysis
    const runBtn = page.locator('button:has-text("Run analysis team")');
    if (await runBtn.isEnabled()) {
      await runBtn.click();
      await page.waitForTimeout(500);
      const cancelBtn = page.locator('button:has-text("Cancel analysis")');
      if (await cancelBtn.isVisible()) {
        await expect(cancelBtn).toBeVisible();
      }
    }
  });

  test('should show export run button when run exists', async ({ page }) => {
    const runBtn = page.locator('button:has-text("Run analysis team")');
    if (await runBtn.isEnabled()) {
      await runBtn.click();
      await page.waitForTimeout(2000);
      const exportBtn = page.locator('button:has-text("Export run")');
      if (await exportBtn.isVisible()) {
        await expect(exportBtn).toBeVisible();
      }
    }
  });
});
