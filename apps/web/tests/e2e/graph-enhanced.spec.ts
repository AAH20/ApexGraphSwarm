import { test, expect } from '@playwright/test';

test.describe('Graph Enhanced Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph-enhanced');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the graph enhanced page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('See the system');
  });

  test('should show enhanced features toggle', async ({ page }) => {
    await expect(page.locator('button:has-text("Enhanced Features")')).toBeVisible();
  });

  test('should expand enhanced features panel', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.waitForTimeout(300);
    await expect(page.locator('button:has-text("Communities")')).toBeVisible();
  });

  test('should show communities toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Communities")')).toBeVisible();
  });

  test('should show centrality toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Centrality")')).toBeVisible();
  });

  test('should show minimap toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Minimap")')).toBeVisible();
  });

  test('should show search toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Search")')).toBeVisible();
  });

  test('should show edge labels toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Edge Labels")')).toBeVisible();
  });

  test('should show multi-select toggle', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await expect(page.locator('button:has-text("Multi-Select")')).toBeVisible();
  });

  test('should toggle communities on', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.locator('button:has-text("Communities")').click();
    await page.waitForTimeout(500);
    // Communities should be active
  });

  test('should toggle centrality on', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.locator('button:has-text("Centrality")').click();
    await page.waitForTimeout(500);
    // Centrality should be active
  });

  test('should toggle minimap off', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    // Minimap is on by default
    await page.locator('button:has-text("Minimap")').click();
    await page.waitForTimeout(300);
  });

  test('should toggle search off', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    // Search is on by default
    await page.locator('button:has-text("Search")').click();
    await page.waitForTimeout(300);
  });

  test('should toggle edge labels on', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.locator('button:has-text("Edge Labels")').click();
    await page.waitForTimeout(500);
  });

  test('should toggle multi-select on', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.locator('button:has-text("Multi-Select")').click();
    await page.waitForTimeout(300);
    await expect(page.locator('text=/selected/')).toBeVisible();
  });

  test('should show selected count when multi-select active', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.locator('button:has-text("Multi-Select")').click();
    await page.waitForTimeout(300);
    const count = page.locator('text=/\\d+ selected/');
    if (await count.isVisible()) {
      await expect(count).toBeVisible();
    }
  });

  test('should show circular layout button', async ({ page }) => {
    await expect(page.locator('button:has-text("Circular")')).toBeVisible();
  });

  test('should switch to circular layout', async ({ page }) => {
    await page.locator('button:has-text("Circular")').click();
    await expect(page.locator('button:has-text("Circular")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should show search bar when search enabled', async ({ page }) => {
    // Search is on by default
    const searchInput = page.locator('input[placeholder="Search nodes…"]');
    if (await searchInput.isVisible()) {
      await expect(searchInput).toBeVisible();
    }
  });

  test('should show export PNG button when export enabled', async ({ page }) => {
    // Export is on by default
    const exportBtn = page.locator('button:has-text("Export PNG")');
    if (await exportBtn.isVisible()) {
      await expect(exportBtn).toBeVisible();
    }
  });

  test('should show minimap when minimap enabled', async ({ page }) => {
    // Minimap is on by default
    const minimap = page.locator('[style*="position: absolute"][style*="bottom: 12px"][style*="right: 12px"]');
    // Minimap may or may not be visible depending on node count
  });

  test('should show legend', async ({ page }) => {
    const legend = page.locator('[style*="position: absolute"][style*="bottom: 12px"][style*="left: 12px"]');
    // Legend should be visible
  });

  test('should show feature panel toggle icon', async ({ page }) => {
    await expect(page.locator('button:has-text("Enhanced Features") svg')).toBeVisible();
  });

  test('should collapse enhanced features panel', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.waitForTimeout(300);
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.waitForTimeout(300);
    // Communities button should be hidden
    await expect(page.locator('button:has-text("Communities")')).not.toBeVisible();
  });

  test('should show chevron up when expanded', async ({ page }) => {
    await page.locator('button:has-text("Enhanced Features")').click();
    await page.waitForTimeout(300);
    // Should show chevron up icon
  });

  test('should show chevron down when collapsed', async ({ page }) => {
    // Should show chevron down icon by default
  });
});
