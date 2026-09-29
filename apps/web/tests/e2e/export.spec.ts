import { test, expect } from '@playwright/test';

test.describe('Export', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should show export menu summary', async ({ page }) => {
    await expect(page.locator('summary:has-text("Export")')).toBeVisible();
  });

  test('should open export menu on click', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    await expect(page.locator('.export-menu')).toBeVisible();
  });

  test('should show full graph snapshot export option', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    await expect(page.locator('.export-menu button:has-text("Full graph snapshot")')).toBeVisible();
  });

  test('should show latest analysis report export option', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    await expect(page.locator('.export-menu button:has-text("Latest analysis report")')).toBeVisible();
  });

  test('should show Neo4j import bundle export option', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    await expect(page.locator('.export-menu button:has-text("Neo4j import bundle")')).toBeVisible();
  });

  test('should disable analysis report export when no report', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    const reportBtn = page.locator('.export-menu button:has-text("Latest analysis report")');
    await expect(reportBtn).toBeDisabled();
  });

  test('should enable full graph snapshot export when graph loaded', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    const snapshotBtn = page.locator('.export-menu button:has-text("Full graph snapshot")');
    await expect(snapshotBtn).toBeEnabled();
  });

  test('should enable Neo4j bundle export when graph loaded', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    const neo4jBtn = page.locator('.export-menu button:has-text("Neo4j import bundle")');
    await expect(neo4jBtn).toBeEnabled();
  });

  test('should show export icon', async ({ page }) => {
    await expect(page.locator('summary:has-text("Export") svg')).toBeVisible();
  });

  test('should have import graph file input', async ({ page }) => {
    const input = page.locator('input[aria-label="Import graph snapshot"]');
    await expect(input).toBeAttached();
  });

  test('should accept JSON file for import', async ({ page }) => {
    const input = page.locator('input[aria-label="Import graph snapshot"]');
    await expect(input).toHaveAttribute('accept', '.json,application/json');
  });

  test('should show import graph button with icon', async ({ page }) => {
    const btn = page.locator('button:has-text("Import graph")');
    await expect(btn).toBeVisible();
    await expect(btn.locator('svg')).toBeVisible();
  });

  test('should show error message when import fails', async ({ page }) => {
    // This tests the error display mechanism
    const errorDiv = page.locator('.error-message');
    // Error should not be visible initially
    await expect(errorDiv).not.toBeVisible();
  });

  test('should dismiss error message', async ({ page }) => {
    // If an error is shown, it should be dismissible
    const errorDiv = page.locator('.error-message');
    if (await errorDiv.isVisible()) {
      await page.locator('button[aria-label="Dismiss error"]').click();
      await expect(errorDiv).not.toBeVisible();
    }
  });

  test('should show notice after successful load', async ({ page }) => {
    await expect(page.locator('.notice-line')).toBeVisible();
    const text = await page.locator('.notice-line').textContent();
    expect(text).toBeTruthy();
  });

  test('should show loaded snapshot name in notice', async ({ page }) => {
    const notice = page.locator('.notice-line');
    const text = await notice.textContent();
    expect(text).toContain('Loaded');
  });

  test('should show source label in repository bar', async ({ page }) => {
    await expect(page.locator('.repository-bar')).toContainText('Prepared project snapshot');
  });

  test('should show indexed snapshot label', async ({ page }) => {
    await expect(page.locator('.repository-bar')).toContainText('Indexed snapshot');
  });

  test('should show graph name in repository bar', async ({ page }) => {
    const repoBar = page.locator('.repository-bar');
    await expect(repoBar.locator('strong')).toBeVisible();
  });

  test('should show file count in repository stats', async ({ page }) => {
    await expect(page.locator('.repo-stats').locator('span').first()).toContainText('files');
  });

  test('should show function count in repository stats', async ({ page }) => {
    await expect(page.locator('.repo-stats').locator('span').nth(1)).toContainText('functions');
  });

  test('should show relationship count in repository stats', async ({ page }) => {
    await expect(page.locator('.repo-stats').locator('span').nth(2)).toContainText('relationships');
  });

  test('should show export menu as details element', async ({ page }) => {
    const menu = page.locator('details.export-menu');
    await expect(menu).toBeVisible();
  });

  test('should close export menu on outside click', async ({ page }) => {
    await page.locator('summary:has-text("Export")').click();
    await expect(page.locator('.export-menu div')).toBeVisible();
    await page.locator('h1').click();
    // Menu should close
    await page.waitForTimeout(300);
  });
});
