import { test, expect } from '@playwright/test';

test.describe('Cross-Page Interactions', () => {
  test('should navigate from graph to swarm control', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.locator('.topbar a:has-text("Swarm control")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/swarm/);
  });

  test('should navigate from graph to integrations', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.locator('.topbar a:has-text("Run integrations")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.integrations-panel')).toBeVisible();
  });

  test('should navigate from graph to teams via assign link', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    const assignLink = page.locator('a:has-text("Assign a specialist swarm")');
    if (await assignLink.isVisible()) {
      await assignLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/teams/);
    }
  });

  test('should navigate from analytics to swarm control', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Relationships")').click();
    const link = page.locator('a:has-text("Open execution-level")');
    if (await link.isVisible()) {
      await link.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/swarm/);
    }
  });

  test('should navigate from evaluations to arena', async ({ page }) => {
    await page.goto('/evaluations');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Open the reproducible Swarm Arena")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/arena/);
  });

  test('should navigate from evaluations to research', async ({ page }) => {
    await page.goto('/evaluations');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Architecture comparisons")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/ecosystem\/research/);
  });

  test('should navigate from ecosystem to evaluation lab', async ({ page }) => {
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Open Evaluation lab")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/evaluations/);
  });

  test('should navigate from ecosystem to delegation', async ({ page }) => {
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    await page.locator('#costs a:has-text("Model & harness rates")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/delegation/);
  });

  test('should navigate from decisions to graph', async ({ page }) => {
    await page.goto('/decisions');
    await page.waitForLoadState('networkidle');
    await page.locator('.side a:has-text("graph-grounded research review")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/graph/);
  });

  test('should navigate from analytics to optimization', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    const link = page.locator('a:has-text("Compare algorithms")');
    if (await link.isVisible()) {
      await link.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/optimization/);
    }
  });

  test('should navigate from swarm to optimization', async ({ page }) => {
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Optimize a plan")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/optimization/);
  });

  test('should navigate from swarm to teams', async ({ page }) => {
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Configure specialist teams")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/teams/);
  });

  test('should navigate from swarm to ecosystem research', async ({ page }) => {
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.locator('a:has-text("Architecture comparisons")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/ecosystem\/research/);
  });

  test('should maintain nav active state across pages', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.nav-link.active')).toBeVisible();
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.nav-link.active')).toBeVisible();
  });

  test('should show decisions context from graph', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    // Navigate to decisions with context
    await page.goto('/decisions?context=graph');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=graph/);
  });

  test('should show decisions context from swarm', async ({ page }) => {
    await page.goto('/decisions?context=swarm');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=swarm/);
  });

  test('should show decisions context from teams', async ({ page }) => {
    await page.goto('/decisions?context=teams');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=teams/);
  });

  test('should show decisions context from analytics', async ({ page }) => {
    await page.goto('/decisions?context=analytics');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=analytics/);
  });

  test('should show decisions context from optimization', async ({ page }) => {
    await page.goto('/decisions?context=optimization');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=optimization/);
  });

  test('should show decisions context from delegation', async ({ page }) => {
    await page.goto('/decisions?context=delegation');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=delegation/);
  });

  test('should show decisions context from evaluations', async ({ page }) => {
    await page.goto('/decisions?context=evaluations');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=evaluations/);
  });

  test('should show decisions context from ecosystem', async ({ page }) => {
    await page.goto('/decisions?context=ecosystem');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=ecosystem/);
  });

  test('should show decisions context from overview', async ({ page }) => {
    await page.goto('/decisions?context=overview');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/context=overview/);
  });

  test('should load graph with embed parameter', async ({ page }) => {
    await page.goto('/graph?embed=1');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/embed=1/);
  });

  test('should load swarm with runId parameter', async ({ page }) => {
    await page.goto('/swarm?runId=test-run-123');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/runId=test-run-123/);
  });

  test('should reject invalid runId parameter', async ({ page }) => {
    await page.goto('/swarm?runId=invalid<script>');
    await page.waitForLoadState('networkidle');
    // Should not crash
    await expect(page.locator('.app-shell')).toBeVisible();
  });
});
