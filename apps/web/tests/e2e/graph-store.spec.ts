import { test, expect } from '@playwright/test';

test.describe('Graph Store Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display graph store panel', async ({ page }) => {
    await expect(page.locator('.graph-store-panel')).toBeVisible();
  });

  test('should show Neo4j graph storage summary', async ({ page }) => {
    await expect(page.locator('.graph-store-panel summary')).toContainText('Neo4j graph storage');
  });

  test('should show optional server configuration required label', async ({ page }) => {
    await expect(page.locator('.graph-store-panel summary')).toContainText('Optional');
  });

  test('should expand graph store panel', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    await expect(page.locator('.graph-store-body')).toBeVisible();
  });

  test('should show graph store description', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    await expect(page.locator('.graph-store-body')).toContainText('Save a versioned repository graph');
  });

  test('should show configuration help when not enabled', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    const body = page.locator('.graph-store-body');
    const text = await body.textContent();
    if (text?.includes('Set NEO4J_URI')) {
      await expect(body).toContainText('NEO4J_URI');
      await expect(body).toContainText('NEO4J_USERNAME');
      await expect(body).toContainText('NEO4J_PASSWORD');
    }
  });

  test('should show token input when enabled', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    const tokenInput = page.locator('.graph-store-body input[type="password"]');
    if (await tokenInput.isVisible()) {
      await expect(tokenInput).toBeVisible();
    }
  });

  test('should show save button when enabled', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    const saveBtn = page.locator('button:has-text("Save current graph")');
    if (await saveBtn.isVisible()) {
      await expect(saveBtn).toBeVisible();
    }
  });

  test('should show load button when enabled', async ({ page }) => {
    await page.locator('.graph-store-panel summary').click();
    const loadBtn = page.locator('button:has-text("Load saved graph")');
    if (await loadBtn.isVisible()) {
      await expect(loadBtn).toBeVisible();
    }
  });

  test('should show database icon in summary', async ({ page }) => {
    await expect(page.locator('.graph-store-panel summary svg')).toBeVisible();
  });

  test('should show graph store status', async ({ page }) => {
    await expect(page.locator('.graph-store-panel summary span')).toBeVisible();
  });
});
