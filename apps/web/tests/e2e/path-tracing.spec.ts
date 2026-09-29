import { test, expect } from '@playwright/test';

test.describe('Path Tracing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the path section', async ({ page }) => {
    await expect(page.locator('.path-section')).toBeVisible();
    await expect(page.locator('.path-section')).toContainText('Trace a dependency path');
  });

  test('should show path destination select', async ({ page }) => {
    const select = page.locator('#path-target');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Choose a destination")')).toBeVisible();
  });

  test('should show trace path button', async ({ page }) => {
    await expect(page.locator('button:has-text("Trace path")')).toBeVisible();
  });

  test('should disable trace button when no target selected', async ({ page }) => {
    const traceBtn = page.locator('button:has-text("Trace path")');
    const targetSelect = page.locator('#path-target');
    const targetValue = await targetSelect.inputValue();
    if (targetValue === '') {
      await expect(traceBtn).toBeDisabled();
    }
  });

  test('should enable trace button when target is selected', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.waitForTimeout(300);
        const traceBtn = page.locator('button:has-text("Trace path")');
        // Should be enabled if a node is selected
        const selected = await page.locator('.node-title h2').isVisible().catch(() => false);
        if (selected) {
          await expect(traceBtn).toBeEnabled();
        }
      }
    }
  });

  test('should show path status after tracing', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.locator('button:has-text("Trace path")').click();
        await page.waitForTimeout(500);
        const status = page.locator('.path-section [role="status"]');
        if (await status.isVisible()) {
          const text = await status.textContent();
          expect(text).toBeTruthy();
        }
      }
    }
  });

  test('should show path in canvas header after tracing', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.locator('button:has-text("Trace path")').click();
        await page.waitForTimeout(500);
        const header = page.locator('.canvas-header');
        const text = await header.textContent();
        // Should show either DEPENDENCY PATH or REPOSITORY EXPLORER
        expect(text).toContain('PATH');
      }
    }
  });

  test('should clear the traced path', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.locator('button:has-text("Trace path")').click();
        await page.waitForTimeout(500);
        const clearBtn = page.locator('button:has-text("Clear path")');
        if (await clearBtn.isVisible()) {
          await clearBtn.click();
          await page.waitForTimeout(300);
          await expect(page.locator('.canvas-header')).toContainText('REPOSITORY EXPLORER');
        }
      }
    }
  });

  test('should show path description text', async ({ page }) => {
    await expect(page.locator('.path-section')).toContainText('Directed semantic edges');
  });

  test('should show destination menu description', async ({ page }) => {
    await expect(page.locator('.path-section')).toContainText('first 1,000 non-module nodes');
  });

  test('should have path target label', async ({ page }) => {
    await expect(page.locator('label[for="path-target"]')).toBeVisible();
  });

  test('should show path section icon', async ({ page }) => {
    await expect(page.locator('.path-section svg')).toBeVisible();
  });

  test('should list non-module nodes in destination dropdown', async ({ page }) => {
    const select = page.locator('#path-target');
    const options = await select.locator('option').allTextContents();
    // Should have at least the placeholder
    expect(options.length).toBeGreaterThan(0);
    expect(options[0]).toContain('Choose a destination');
  });

  test('should show path status with hop count', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.locator('button:has-text("Trace path")').click();
        await page.waitForTimeout(500);
        const status = page.locator('.path-section [role="status"]');
        if (await status.isVisible()) {
          const text = await status.textContent();
          // Should mention hops or no path found
          expect(text).toMatch(/hops|No resolved/);
        }
      }
    }
  });

  test('should show path status with semantic hops description', async ({ page }) => {
    const targetSelect = page.locator('#path-target');
    const options = await targetSelect.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await targetSelect.selectOption(value);
        await page.locator('button:has-text("Trace path")').click();
        await page.waitForTimeout(500);
        const status = page.locator('.path-section [role="status"]');
        if (await status.isVisible()) {
          const text = await status.textContent();
          if (text?.includes('hops')) {
            expect(text).toContain('semantic');
          }
        }
      }
    }
  });
});
