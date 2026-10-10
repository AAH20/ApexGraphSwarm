import { test, expect } from '@playwright/test';

test.describe('Graph Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
  });

  test('should load the graph page with header', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('See the system');
    await expect(page.locator('.eyebrow').first()).toContainText('REPOSITORY INTELLIGENCE');
  });

  test('should display the repository bar with stats', async ({ page }) => {
    await expect(page.locator('.repository-bar')).toBeVisible();
    await expect(page.locator('.repo-stats')).toContainText('files');
    await expect(page.locator('.repo-stats')).toContainText('functions');
    await expect(page.locator('.repo-stats')).toContainText('relationships');
  });

  test('should show the graph canvas or SVG fallback', async ({ page }) => {
    const canvas = page.locator('.graph-canvas-renderer');
    const fallback = page.locator('.graph-canvas-svg-fallback');
    const loading = page.locator('.canvas-loading');
    // One of these should be visible
    const visible = await canvas.isVisible() || await fallback.isVisible() || await loading.isVisible();
    expect(visible).toBeTruthy();
  });

  test('should display canvas controls toolbar', async ({ page }) => {
    const controls = page.locator('.canvas-controls');
    await expect(controls).toBeVisible();
    await expect(controls.locator('button[aria-label="Zoom in"]')).toBeVisible();
    await expect(controls.locator('button[aria-label="Zoom out"]')).toBeVisible();
    await expect(controls.locator('button:has-text("Fit")')).toBeVisible();
  });

  test('should have layout toggle buttons', async ({ page }) => {
    const groupedBtn = page.locator('button:has-text("Grouped")');
    const forceBtn = page.locator('button:has-text("Force")');
    await expect(groupedBtn).toBeVisible();
    await expect(forceBtn).toBeVisible();
  });

  test('should switch to force layout', async ({ page }) => {
    await page.locator('button:has-text("Force")').click();
    await expect(page.locator('button:has-text("Force")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch back to grouped layout', async ({ page }) => {
    await page.locator('button:has-text("Force")').click();
    await page.locator('button:has-text("Grouped")').click();
    await expect(page.locator('button:has-text("Grouped")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should show the graph legend', async ({ page }) => {
    const legend = page.locator('.graph-legend');
    await expect(legend).toBeVisible();
    await expect(legend).toContainText('module');
    await expect(legend).toContainText('file');
    await expect(legend).toContainText('function');
  });

  test('should display the canvas header with node count', async ({ page }) => {
    const header = page.locator('.canvas-header');
    await expect(header).toBeVisible();
    await expect(header).toContainText('nodes');
    await expect(header).toContainText('links');
  });

  test('should show the scope note', async ({ page }) => {
    await expect(page.locator('.scope-note')).toBeVisible();
  });

  test('should display the notice line', async ({ page }) => {
    await expect(page.locator('.notice-line')).toBeVisible();
  });

  test('should show the topbar with workspace label', async ({ page }) => {
    await expect(page.locator('.topbar')).toContainText('WORKSPACE');
    await expect(page.locator('.topbar')).toContainText('Graph Studio');
  });

  test('should have the source-grounded pill', async ({ page }) => {
    await expect(page.locator('.pill').first()).toContainText('Source-grounded workspace');
  });

  test('should display the page heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Find your next move');
  });

  test('should show the import graph button', async ({ page }) => {
    await expect(page.locator('button:has-text("Import graph")')).toBeVisible();
  });

  test('should show the export menu', async ({ page }) => {
    await expect(page.locator('summary:has-text("Export")')).toBeVisible();
  });

  test('should display the graph workbench section', async ({ page }) => {
    await expect(page.locator('.graph-workbench')).toBeVisible();
  });

  test('should show the filter panel', async ({ page }) => {
    await expect(page.locator('.filter-panel')).toBeVisible();
    await expect(page.locator('.panel-heading')).toContainText('Refine the view');
  });

  test('should display the inspector panel', async ({ page }) => {
    await expect(page.locator('.inspector')).toBeVisible();
  });

  test('should show the graph bottom bar', async ({ page }) => {
    await expect(page.locator('.graph-bottom-bar')).toBeVisible();
  });

  test('should display the workspace footer', async ({ page }) => {
    await expect(page.locator('.workspace-footer')).toBeVisible();
  });

  test('should show the path section', async ({ page }) => {
    await expect(page.locator('.path-section')).toBeVisible();
    await expect(page.locator('.path-section')).toContainText('Trace a dependency path');
  });

  test('should display the swarm section', async ({ page }) => {
    await expect(page.locator('.swarm-section')).toBeVisible();
  });

  test('should show the integrations section', async ({ page }) => {
    await expect(page.locator('.integrations-panel')).toBeVisible();
  });

  test('should have the fullscreen toggle button', async ({ page }) => {
    await expect(page.locator('[data-fullscreen-toggle]')).toBeVisible();
  });

  test('should have the reset filters button', async ({ page }) => {
    await expect(page.locator('button[aria-label="Reset all graph filters"]')).toBeVisible();
  });

  test('should show the graph search input', async ({ page }) => {
    await expect(page.locator('input[aria-label="Filter graph by name or path"]')).toBeVisible();
  });

  test('should display view tabs', async ({ page }) => {
    await expect(page.locator('.view-tabs')).toBeVisible();
    await expect(page.locator('.view-tabs button:has-text("Modules")')).toBeVisible();
    await expect(page.locator('.view-tabs button:has-text("Files")')).toBeVisible();
    await expect(page.locator('.view-tabs button:has-text("Symbols")')).toBeVisible();
    await expect(page.locator('.view-tabs button:has-text("All kinds")')).toBeVisible();
  });

  test('should show the canvas footer with renderer status', async ({ page }) => {
    await expect(page.locator('.canvas-footer')).toBeVisible();
  });
});
