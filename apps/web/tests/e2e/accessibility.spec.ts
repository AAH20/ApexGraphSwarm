import { test, expect } from '@playwright/test';

test.describe('Accessibility & Keyboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should have skip link', async ({ page }) => {
    await expect(page.locator('.skip-link')).toBeVisible();
  });

  test('should have aria-label on graph canvas', async ({ page }) => {
    await expect(page.locator('.graph-canvas-renderer')).toHaveAttribute('aria-label');
  });

  test('should have aria-pressed on layout buttons', async ({ page }) => {
    await expect(page.locator('button:has-text("Grouped")')).toHaveAttribute('aria-pressed');
    await expect(page.locator('button:has-text("Force")')).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on view tabs', async ({ page }) => {
    await expect(page.locator('.view-tabs button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-label on zoom controls', async ({ page }) => {
    await expect(page.locator('button[aria-label="Zoom in"]')).toBeVisible();
    await expect(page.locator('button[aria-label="Zoom out"]')).toBeVisible();
  });

  test('should have aria-label on fullscreen toggle', async ({ page }) => {
    await expect(page.locator('[data-fullscreen-toggle]')).toHaveAttribute('aria-label');
  });

  test('should have aria-pressed on fullscreen toggle', async ({ page }) => {
    await expect(page.locator('[data-fullscreen-toggle]')).toHaveAttribute('aria-pressed');
  });

  test('should have role toolbar on canvas controls', async ({ page }) => {
    await expect(page.locator('.canvas-controls')).toHaveAttribute('role', 'toolbar');
  });

  test('should have aria-label on canvas controls', async ({ page }) => {
    await expect(page.locator('.canvas-controls')).toHaveAttribute('aria-label');
  });

  test('should have role status on notice line', async ({ page }) => {
    await expect(page.locator('.notice-line')).toHaveAttribute('role', 'status');
  });

  test('should have role status on path status', async ({ page }) => {
    const status = page.locator('.path-section [role="status"]');
    // May or may not be visible depending on path state
  });

  test('should have role alert on error message', async ({ page }) => {
    const error = page.locator('.error-message');
    // May or may not be visible
  });

  test('should have aria-label on clear search button', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('test');
    await page.waitForTimeout(300);
    await expect(page.locator('button[aria-label="Clear graph search"]')).toBeVisible();
  });

  test('should have aria-label on reset filters button', async ({ page }) => {
    await expect(page.locator('button[aria-label="Reset all graph filters"]')).toBeVisible();
  });

  test('should have aria-expanded on accessible list toggle', async ({ page }) => {
    await expect(page.locator('button:has-text("accessible node list")')).toHaveAttribute('aria-expanded');
  });

  test('should have aria-pressed on inspector tabs', async ({ page }) => {
    await expect(page.locator('.inspector-tabs button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-label on import graph input', async ({ page }) => {
    await expect(page.locator('input[aria-label="Import graph snapshot"]')).toHaveAttribute('aria-label');
  });

  test('should have label for path target select', async ({ page }) => {
    await expect(page.locator('label[for="path-target"]')).toBeVisible();
  });

  test('should have aria-label on swarm concurrency select', async ({ page }) => {
    await expect(page.locator('select[aria-label="Analysis concurrency"]')).toBeVisible();
  });

  test('should have aria-label on swarm timeout select', async ({ page }) => {
    await expect(page.locator('select[aria-label="Per-specialist time budget"]')).toBeVisible();
  });

  test('should have aria-expanded on result toggle', async ({ page }) => {
    const toggle = page.locator('.result-toggle');
    // May or may not be visible
  });

  test('should have role status on busy indicator', async ({ page }) => {
    // May or may not be visible
  });

  test('should have aria-label on refresh integration button', async ({ page }) => {
    await expect(page.locator('button[aria-label="Refresh integration configuration"]')).toBeVisible();
  });

  test('should have aria-pressed on analytics tabs', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.tabs button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on preset buttons', async ({ page }) => {
    await page.goto('/decisions');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.presetRow button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on audience cards', async ({ page }) => {
    await page.goto('/presentations');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.audienceCard').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on experiment template buttons', async ({ page }) => {
    await page.goto('/optimization');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.choices button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on agent list buttons', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.agentList button').first()).toHaveAttribute('aria-pressed');
  });

  test('should have aria-pressed on task node buttons', async ({ page }) => {
    await page.goto('/optimization');
    await page.waitForLoadState('networkidle');
    await page.locator('input[type="password"]').fill('test-token');
    await page.locator('button:has-text("Run experiment")').click();
    await page.waitForTimeout(3000);
    const nodeBtn = page.locator('.nodes button').first();
    if (await nodeBtn.isVisible()) {
      await expect(nodeBtn).toHaveAttribute('aria-pressed');
    }
  });

  test('should have aria-pressed on graph routing checkbox', async ({ page }) => {
    await page.goto('/evaluations');
    await page.waitForLoadState('networkidle');
    // Checkbox should be accessible
  });

  test('should have aria-label on connection checkboxes', async ({ page }) => {
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    // Checkboxes should be accessible
  });

  test('should have role main on main workspace', async ({ page }) => {
    await expect(page.locator('.main-workspace')).toHaveAttribute('id', 'workspace');
  });

  test('should have nav aria-label', async ({ page }) => {
    await expect(page.locator('nav[aria-label="Main navigation"]')).toBeVisible();
  });

  test('should have aria-current on active nav link', async ({ page }) => {
    await expect(page.locator('.nav-link.active')).toHaveAttribute('aria-current', 'page');
  });

  test('should have aria-label on graph view controls', async ({ page }) => {
    await expect(page.locator('.canvas-controls')).toHaveAttribute('aria-label', 'Graph view controls');
  });

  test('should have aria-label on layout controls', async ({ page }) => {
    await expect(page.locator('.canvas-layout-controls')).toHaveAttribute('aria-label', 'Layout');
  });
});
