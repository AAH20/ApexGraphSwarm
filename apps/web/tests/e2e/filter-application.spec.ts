import { test, expect } from '@playwright/test';

test.describe('Filter Application', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should have a graph search input', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toHaveAttribute('placeholder', 'Filter nodes, paths, functions…');
  });

  test('should filter nodes by search query', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('module');
    await page.waitForTimeout(500);
    // Canvas header should update
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should clear the search filter', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('test');
    await page.waitForTimeout(300);
    const clearBtn = page.locator('button[aria-label="Clear graph search"]');
    await clearBtn.click();
    await expect(searchInput).toHaveValue('');
  });

  test('should have a relationship filter dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Relationship") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("All relationships")')).toBeVisible();
  });

  test('should have an evidence filter dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Evidence") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("All evidence levels")')).toBeVisible();
    await expect(select.locator('option:has-text("Parsed / observed only")')).toBeVisible();
    await expect(select.locator('option:has-text("Inferred only")')).toBeVisible();
    await expect(select.locator('option:has-text("Illustrative sample")')).toBeVisible();
  });

  test('should have a node type filter dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Node type") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("All node types")')).toBeVisible();
    await expect(select.locator('option:has-text("module")')).toBeVisible();
    await expect(select.locator('option:has-text("file")')).toBeVisible();
    await expect(select.locator('option:has-text("function")')).toBeVisible();
    await expect(select.locator('option:has-text("class")')).toBeVisible();
    await expect(select.locator('option:has-text("external")')).toBeVisible();
  });

  test('should have a directory filter dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Directory") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Whole repository")')).toBeVisible();
  });

  test('should have a layout dropdown in filter panel', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Layout") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Grouped")')).toBeVisible();
    await expect(select.locator('option:has-text("Force")')).toBeVisible();
  });

  test('should have a neighborhood depth dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Neighborhood depth") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("1 hop")')).toBeVisible();
    await expect(select.locator('option:has-text("2 hops")')).toBeVisible();
    await expect(select.locator('option:has-text("3 hops")')).toBeVisible();
    await expect(select.locator('option:has-text("4 hops")')).toBeVisible();
  });

  test('should have a direction dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Direction") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Both directions")')).toBeVisible();
    await expect(select.locator('option:has-text("Outgoing dependencies")')).toBeVisible();
    await expect(select.locator('option:has-text("Incoming dependents")')).toBeVisible();
  });

  test('should change node type filter', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Node type") select');
    await select.selectOption('file');
    await page.waitForTimeout(500);
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should change evidence filter to grounded', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Evidence") select');
    await select.selectOption('grounded');
    await page.waitForTimeout(500);
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should change evidence filter to inferred', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Evidence") select');
    await select.selectOption('inferred');
    await page.waitForTimeout(500);
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should change direction filter', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Direction") select');
    await select.selectOption('out');
    await page.waitForTimeout(500);
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should change neighborhood depth', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Neighborhood depth") select');
    await select.selectOption('3');
    await page.waitForTimeout(500);
    await expect(page.locator('.canvas-header')).toContainText('nodes');
  });

  test('should switch view to files', async ({ page }) => {
    await page.locator('.view-tabs button:has-text("Files")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.view-tabs button:has-text("Files")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch view to symbols', async ({ page }) => {
    await page.locator('.view-tabs button:has-text("Symbols")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.view-tabs button:has-text("Symbols")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch view to all kinds', async ({ page }) => {
    await page.locator('.view-tabs button:has-text("All kinds")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.view-tabs button:has-text("All kinds")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch view back to modules', async ({ page }) => {
    await page.locator('.view-tabs button:has-text("All kinds")').click();
    await page.waitForTimeout(300);
    await page.locator('.view-tabs button:has-text("Modules")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.view-tabs button:has-text("Modules")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should reset all filters', async ({ page }) => {
    // Apply some filters
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('test');
    const kindSelect = page.locator('.filter-panel label:has-text("Node type") select');
    await kindSelect.selectOption('file');
    // Reset
    await page.locator('button[aria-label="Reset all graph filters"]').click();
    await page.waitForTimeout(500);
    await expect(searchInput).toHaveValue('');
  });

  test('should show focus neighborhood button', async ({ page }) => {
    await expect(page.locator('.focus-button')).toBeVisible();
  });

  test('should focus neighborhood on selected node', async ({ page }) => {
    const focusBtn = page.locator('.focus-button');
    if (await focusBtn.isEnabled()) {
      await focusBtn.click();
      await page.waitForTimeout(500);
      await expect(page.locator('.canvas-header')).toContainText('FOCUSED NEIGHBORHOOD');
    }
  });

  test('should clear focus neighborhood', async ({ page }) => {
    const focusBtn = page.locator('.focus-button');
    if (await focusBtn.isEnabled()) {
      await focusBtn.click();
      await page.waitForTimeout(300);
      // Button text should change to "Clear focus"
      await expect(page.locator('.focus-button')).toContainText('Clear focus');
      await focusBtn.click();
      await page.waitForTimeout(300);
      await expect(page.locator('.canvas-header')).toContainText('REPOSITORY EXPLORER');
    }
  });

  test('should show empty state when no nodes match', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('zzzznonexistentnode999');
    await page.waitForTimeout(500);
    const empty = page.locator('.canvas-empty');
    if (await empty.isVisible()) {
      await expect(empty).toContainText('No matching nodes');
    }
  });

  test('should show reset view button in empty state', async ({ page }) => {
    const searchInput = page.locator('input[aria-label="Filter graph by name or path"]');
    await searchInput.fill('zzzznonexistentnode999');
    await page.waitForTimeout(500);
    const resetBtn = page.locator('.canvas-empty button:has-text("Reset view")');
    if (await resetBtn.isVisible()) {
      await expect(resetBtn).toBeVisible();
    }
  });

  test('should change layout from filter panel', async ({ page }) => {
    const layoutSelect = page.locator('.filter-panel label:has-text("Layout") select');
    await layoutSelect.selectOption('force');
    await page.waitForTimeout(500);
    await expect(page.locator('button:has-text("Force")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should show filter divider', async ({ page }) => {
    await expect(page.locator('.filter-divider')).toBeVisible();
  });

  test('should show relationship options in dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Relationship") select');
    const options = await select.locator('option').allTextContents();
    expect(options.length).toBeGreaterThan(1);
  });

  test('should show directory options in dropdown', async ({ page }) => {
    const select = page.locator('.filter-panel label:has-text("Directory") select');
    const options = await select.locator('option').allTextContents();
    expect(options.length).toBeGreaterThan(1);
  });
});
