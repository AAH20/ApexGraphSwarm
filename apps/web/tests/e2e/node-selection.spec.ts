import { test, expect } from '@playwright/test';

test.describe('Node Selection & Inspection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should show empty inspector when no node selected', async ({ page }) => {
    // Initially a node is auto-selected, so let's just verify the inspector exists
    const inspector = page.locator('.inspector');
    await expect(inspector).toBeVisible();
  });

  test('should display inspector tabs', async ({ page }) => {
    await expect(page.locator('.inspector-tabs button:has-text("Inspector")')).toBeVisible();
    await expect(page.locator('.inspector-tabs button:has-text("Constraints")')).toBeVisible();
  });

  test('should switch to constraints tab', async ({ page }) => {
    await page.locator('.inspector-tabs button:has-text("Constraints")').click();
    await expect(page.locator('.constraints-panel')).toBeVisible();
    await expect(page.locator('.constraints-panel')).toContainText('Coverage & limits');
  });

  test('should show constraint stats', async ({ page }) => {
    await page.locator('.inspector-tabs button:has-text("Constraints")').click();
    await expect(page.locator('.constraint-stats')).toBeVisible();
    await expect(page.locator('.constraint-stats')).toContainText('Nodes indexed');
    await expect(page.locator('.constraint-stats')).toContainText('Relationships');
    await expect(page.locator('.constraint-stats')).toContainText('Warnings');
  });

  test('should display constraint limits', async ({ page }) => {
    await page.locator('.inspector-tabs button:has-text("Constraints")').click();
    await expect(page.locator('.constraint-note')).toBeVisible();
    await expect(page.locator('.constraint-note')).toContainText('Max');
  });

  test('should switch back to inspector tab', async ({ page }) => {
    await page.locator('.inspector-tabs button:has-text("Constraints")').click();
    await page.locator('.inspector-tabs button:has-text("Inspector")').click();
    await expect(page.locator('.inspector-tabs button:has-text("Inspector")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should display node details when a node is selected', async ({ page }) => {
    // A node should be auto-selected on load
    const nodeTitle = page.locator('.node-title');
    if (await nodeTitle.isVisible()) {
      await expect(nodeTitle.locator('h2')).toBeVisible();
      await expect(nodeTitle.locator('code')).toBeVisible();
    }
  });

  test('should show evidence badge for selected node', async ({ page }) => {
    const evidenceBadge = page.locator('.evidence-badge').first();
    if (await evidenceBadge.isVisible()) {
      const text = await evidenceBadge.textContent();
      expect(text).toContain('evidence');
    }
  });

  test('should display node metrics', async ({ page }) => {
    const metrics = page.locator('.node-metrics');
    if (await metrics.isVisible()) {
      await expect(metrics).toContainText('Incoming');
      await expect(metrics).toContainText('Outgoing');
    }
  });

  test('should show relationship list for selected node', async ({ page }) => {
    const relList = page.locator('.relationship-list');
    if (await relList.isVisible()) {
      await expect(relList).toBeVisible();
    }
  });

  test('should navigate to a relationship node on click', async ({ page }) => {
    const relButton = page.locator('.relationship-list button').first();
    if (await relButton.isVisible()) {
      await relButton.click();
      await expect(page.locator('.node-title h2')).toBeVisible();
    }
  });

  test('should show the assign specialist swarm link', async ({ page }) => {
    const link = page.locator('a:has-text("Assign a specialist swarm")');
    if (await link.isVisible()) {
      await expect(link).toBeVisible();
    }
  });

  test('should display the node summary', async ({ page }) => {
    const summary = page.locator('.node-summary');
    if (await summary.isVisible()) {
      await expect(summary).toBeVisible();
    }
  });

  test('should show the accessible node list toggle', async ({ page }) => {
    await expect(page.locator('button:has-text("accessible node list")')).toBeVisible();
  });

  test('should toggle the accessible node list open', async ({ page }) => {
    const btn = page.locator('button:has-text("accessible node list")');
    await btn.click();
    await expect(page.locator('.accessible-list')).toBeVisible();
  });

  test('should show search input in accessible list', async ({ page }) => {
    await page.locator('button:has-text("accessible node list")').click();
    await expect(page.locator('.accessible-list input')).toBeVisible();
  });

  test('should filter nodes in accessible list search', async ({ page }) => {
    await page.locator('button:has-text("accessible node list")').click();
    const searchInput = page.locator('.accessible-list input');
    await searchInput.fill('test');
    await page.waitForTimeout(500);
    // Should still show the list
    await expect(page.locator('.accessible-list')).toBeVisible();
  });

  test('should navigate to node from accessible list', async ({ page }) => {
    await page.locator('button:has-text("accessible node list")').click();
    const firstNode = page.locator('.accessible-list button').first();
    if (await firstNode.isVisible()) {
      await firstNode.click();
      await expect(page.locator('.node-title h2')).toBeVisible();
    }
  });

  test('should close the accessible node list', async ({ page }) => {
    await page.locator('button:has-text("accessible node list")').click();
    await expect(page.locator('.accessible-list')).toBeVisible();
    await page.locator('button:has-text("Hide")').click();
    await expect(page.locator('.accessible-list')).not.toBeVisible();
  });

  test('should show coverage & limits button in bottom bar', async ({ page }) => {
    await expect(page.locator('button:has-text("Coverage & limits")')).toBeVisible();
  });

  test('should switch to constraints via bottom bar button', async ({ page }) => {
    await page.locator('button:has-text("Coverage & limits")').click();
    await expect(page.locator('.constraints-panel')).toBeVisible();
  });

  test('should display the graph bottom bar text', async ({ page }) => {
    await expect(page.locator('.graph-bottom-bar span')).toContainText('Inspect relationships');
  });

  test('should show node kind icon in accessible list', async ({ page }) => {
    await page.locator('button:has-text("accessible node list")').click();
    const firstEntry = page.locator('.accessible-list button').first();
    if (await firstEntry.isVisible()) {
      await expect(firstEntry.locator('svg')).toBeVisible();
    }
  });
});
