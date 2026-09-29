import { test, expect } from '@playwright/test';

test.describe('Responsive & Visual', () => {
  test('should render graph page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.graph-workbench')).toBeVisible();
  });

  test('should render graph page at tablet width', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.graph-workbench')).toBeVisible();
  });

  test('should render graph page at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.graph-workbench')).toBeVisible();
  });

  test('should render analytics page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Turn activity into evidence');
  });

  test('should render decisions page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/decisions');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Ask precisely');
  });

  test('should render ecosystem page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('One workspace');
  });

  test('should render arena page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/arena');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Make the run easy to inspect');
  });

  test('should render presentations page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/presentations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Presentation Studio');
  });

  test('should render teams page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Design the team');
  });

  test('should render optimization page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/optimization');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Make every constraint visible');
  });

  test('should render evaluations page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/evaluations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Improvement needs evidence');
  });

  test('should render delegation page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/delegation');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Delegate with a reason');
  });

  test('should render swarm page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('A plan is only the beginning');
  });

  test('should render overview page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('Build coordinated intelligence');
  });

  test('should render graph-enhanced page at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/graph-enhanced');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('h1')).toContainText('See the system');
  });

  test('should show sidebar at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.app-sidebar')).toBeVisible();
  });

  test('should show main workspace at desktop width', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.main-workspace')).toBeVisible();
  });

  test('should show topbar on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.topbar')).toBeVisible();
  });

  test('should show page content on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.page-content')).toBeVisible();
  });

  test('should show page heading on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.page-heading')).toBeVisible();
  });

  test('should show heading actions on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.heading-actions')).toBeVisible();
  });

  test('should show graph grid on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.graph-grid')).toBeVisible();
  });

  test('should show graph center on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.graph-center')).toBeVisible();
  });

  test('should show graph canvas on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.graph-canvas')).toBeVisible();
  });

  test('should show canvas header on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.canvas-header')).toBeVisible();
  });

  test('should show canvas footer on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.canvas-footer')).toBeVisible();
  });

  test('should show scope note on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.scope-note')).toBeVisible();
  });

  test('should show graph bottom bar on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.graph-bottom-bar')).toBeVisible();
  });

  test('should show workspace footer on graph page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.workspace-footer')).toBeVisible();
  });
});
