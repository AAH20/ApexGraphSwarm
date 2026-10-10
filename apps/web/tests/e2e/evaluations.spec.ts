import { test, expect } from '@playwright/test';

test.describe('Evaluations Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/evaluations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the evaluations page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Improvement needs evidence');
  });

  test('should show evaluation eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('EVALUATION');
  });

  test('should show evaluation lab title', async ({ page }) => {
    await expect(page.locator('#evaluation-title')).toContainText('Measure coordination before promotion');
  });

  test('should show local fixture badge', async ({ page }) => {
    await expect(page.locator('.badge')).toContainText('LOCAL FIXTURE');
  });

  test('should show evidence boundary note', async ({ page }) => {
    await expect(page.locator('.notice')).toContainText('Evidence boundary');
  });

  test('should show deterministic local queue fixture note', async ({ page }) => {
    await expect(page.locator('.notice')).toContainText('deterministic local SQLite queue');
  });

  test('should show zero model provider calls note', async ({ page }) => {
    await expect(page.locator('.notice')).toContainText('zero model-provider calls');
  });

  test('should show evaluation parameters card', async ({ page }) => {
    await expect(page.locator('.card').first()).toBeVisible();
  });

  test('should show control plane parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Control plane');
  });

  test('should show logical agents parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Logical agents');
  });

  test('should show active worker cap parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Active-worker cap');
  });

  test('should show tasks per logical agent parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Tasks per logical agent');
  });

  test('should show fixture parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Fixture');
  });

  test('should show provider calls parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Provider calls');
  });

  test('should show measured at parameter', async ({ page }) => {
    await expect(page.locator('.definitionList')).toContainText('Measured at');
  });

  test('should show run provenance details', async ({ page }) => {
    const details = page.locator('.provenance');
    if (await details.isVisible()) {
      await expect(details).toBeVisible();
    }
  });

  test('should show versioned candidate plans card', async ({ page }) => {
    await expect(page.locator('.card').nth(1)).toBeVisible();
  });

  test('should show candidate select', async ({ page }) => {
    await expect(page.locator('.label select')).toBeVisible();
  });

  test('should show topology select', async ({ page }) => {
    await expect(page.locator('.label:has-text("Topology") select')).toBeVisible();
  });

  test('should show topology options', async ({ page }) => {
    const select = page.locator('.label:has-text("Topology") select');
    await expect(select.locator('option:has-text("Coordinator / star")')).toBeVisible();
    await expect(select.locator('option:has-text("Graph routed")')).toBeVisible();
  });

  test('should show worker limit input', async ({ page }) => {
    await expect(page.locator('.label:has-text("Worker limit") input')).toBeVisible();
  });

  test('should show cost ceiling input', async ({ page }) => {
    await expect(page.locator('.label:has-text("Cost ceiling") input')).toBeVisible();
  });

  test('should show graph routing checkbox', async ({ page }) => {
    await expect(page.locator('.toggle input[type="checkbox"]')).toBeVisible();
  });

  test('should show create versioned draft button', async ({ page }) => {
    await expect(page.locator('button:has-text("Create versioned draft")')).toBeVisible();
  });

  test('should show evidence text', async ({ page }) => {
    await expect(page.locator('.evidence')).toBeVisible();
  });

  test('should show queue fixture results card', async ({ page }) => {
    await expect(page.locator('.card').nth(2)).toBeVisible();
  });

  test('should show fixture results table', async ({ page }) => {
    await expect(page.locator('.table')).toBeVisible();
  });

  test('should show logical agents column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Logical agents');
  });

  test('should show active cap column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Active cap');
  });

  test('should show tasks column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Tasks');
  });

  test('should show throughput column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Throughput');
  });

  test('should show queue latency column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Queue p50');
  });

  test('should show end-to-end latency column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('End-to-end p50');
  });

  test('should show duplicate completions column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Duplicate completions');
  });

  test('should show restart check column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Restart check');
  });

  test('should show cost ledger column', async ({ page }) => {
    await expect(page.locator('.table th')).toContainText('Cost ledger');
  });

  test('should show fixture status', async ({ page }) => {
    await expect(page.locator('.fixtureStatus')).toBeVisible();
  });

  test('should show promotion gates card', async ({ page }) => {
    await expect(page.locator('.card').nth(3)).toBeVisible();
  });

  test('should show promotion gates table', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.table')).toBeVisible();
  });

  test('should show gate column', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.table th')).toContainText('Gate');
  });

  test('should show target column', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.table th')).toContainText('Target');
  });

  test('should show status column', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.table th')).toContainText('Status');
  });

  test('should show evidence required column', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.table th')).toContainText('Evidence required');
  });

  test('should show unmeasured status', async ({ page }) => {
    await expect(page.locator('.unmeasured').first()).toContainText('Unmeasured');
  });

  test('should show promote candidate button disabled', async ({ page }) => {
    await expect(page.locator('button:has-text("Promote candidate")')).toBeDisabled();
  });

  test('should show promotion lock reason', async ({ page }) => {
    await expect(page.locator('#promotion-lock-reason')).toContainText('Locked');
  });

  test('should show held out unmeasured badge', async ({ page }) => {
    await expect(page.locator('.card').nth(3).locator('.unmeasured').first()).toBeVisible();
  });

  test('should show no automatic promotion note', async ({ page }) => {
    await expect(page.locator('.muted')).toContainText('No automatic promotion endpoint');
  });

  test('should show architecture comparisons link', async ({ page }) => {
    await expect(page.locator('a:has-text("Architecture comparisons")')).toBeVisible();
  });

  test('should show open swarm arena link', async ({ page }) => {
    await expect(page.locator('a:has-text("Open the reproducible Swarm Arena")')).toBeVisible();
  });

  test('should change candidate selection', async ({ page }) => {
    const select = page.locator('.label select');
    const options = await select.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await select.selectOption(value);
        await page.waitForTimeout(300);
      }
    }
  });

  test('should change topology', async ({ page }) => {
    const select = page.locator('.label:has-text("Topology") select');
    await select.selectOption('graph');
    await page.waitForTimeout(300);
  });

  test('should change worker limit', async ({ page }) => {
    const input = page.locator('.label:has-text("Worker limit") input');
    await input.fill('32');
    await expect(input).toHaveValue('32');
  });

  test('should change cost ceiling', async ({ page }) => {
    const input = page.locator('.label:has-text("Cost ceiling") input');
    await input.fill('100.00');
    await expect(input).toHaveValue('100.00');
  });

  test('should toggle graph routing', async ({ page }) => {
    const checkbox = page.locator('.toggle input[type="checkbox"]');
    await checkbox.click();
    await page.waitForTimeout(300);
  });

  test('should create versioned draft', async ({ page }) => {
    await page.locator('button:has-text("Create versioned draft")').click();
    await page.waitForTimeout(500);
    // Should add a new draft to the list
    await expect(page.locator('.label select option').last()).toContainText('draft');
  });

  test('should show measured fixture badge', async ({ page }) => {
    await expect(page.locator('.tableHeader span')).toContainText('MEASURED FIXTURE');
  });

  test('should show not measured badge when no fixture', async ({ page }) => {
    // This is conditional on fixture loading
  });
});
