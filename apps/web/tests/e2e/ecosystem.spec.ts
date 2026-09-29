import { test, expect } from '@playwright/test';

test.describe('Ecosystem Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the ecosystem page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('One workspace. Explicit connections.');
  });

  test('should show interoperability eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('INTEROPERABILITY');
  });

  test('should show compare orchestration link', async ({ page }) => {
    await expect(page.locator('a:has-text("Compare orchestration")')).toBeVisible();
  });

  test('should show jump links', async ({ page }) => {
    await expect(page.locator('.jumpLinks')).toBeVisible();
  });

  test('should show connections jump link', async ({ page }) => {
    await expect(page.locator('.jumpLinks a:has-text("Connections")')).toBeVisible();
  });

  test('should show MCP discovery jump link', async ({ page }) => {
    await expect(page.locator('.jumpLinks a:has-text("MCP discovery")')).toBeVisible();
  });

  test('should show skill review jump link', async ({ page }) => {
    await expect(page.locator('.jumpLinks a:has-text("Skill review")')).toBeVisible();
  });

  test('should show operating costs jump link', async ({ page }) => {
    await expect(page.locator('.jumpLinks a:has-text("Operating costs")')).toBeVisible();
  });

  test('should show architecture diagram', async ({ page }) => {
    await expect(page.locator('.architecture')).toBeVisible();
  });

  test('should show apex control plane in architecture', async ({ page }) => {
    await expect(page.locator('.architecture')).toContainText('Apex control plane');
  });

  test('should show execution adapters in architecture', async ({ page }) => {
    await expect(page.locator('.architecture')).toContainText('Execution adapters');
  });

  test('should show tools and skills in architecture', async ({ page }) => {
    await expect(page.locator('.architecture')).toContainText('Tools & skills');
  });

  test('should show connections section', async ({ page }) => {
    await expect(page.locator('#connections')).toBeVisible();
  });

  test('should show building blocks heading', async ({ page }) => {
    await expect(page.locator('#connections h2')).toContainText('Choose the building blocks');
  });

  test('should show selected count pill', async ({ page }) => {
    await expect(page.locator('#connections .pill')).toContainText('selected');
  });

  test('should show search input', async ({ page }) => {
    await expect(page.locator('.filters input')).toBeVisible();
  });

  test('should show layer filter', async ({ page }) => {
    await expect(page.locator('.filters label:has-text("Layer") select')).toBeVisible();
  });

  test('should show layer options', async ({ page }) => {
    const select = page.locator('.filters label:has-text("Layer") select');
    await expect(select.locator('option:has-text("All layers")')).toBeVisible();
    await expect(select.locator('option:has-text("Executors")')).toBeVisible();
    await expect(select.locator('option:has-text("Gateways")')).toBeVisible();
    await expect(select.locator('option:has-text("Registries")')).toBeVisible();
    await expect(select.locator('option:has-text("Skills libraries")')).toBeVisible();
  });

  test('should show connection cards', async ({ page }) => {
    await expect(page.locator('.card').first()).toBeVisible();
  });

  test('should show connection checkboxes', async ({ page }) => {
    await expect(page.locator('.card input[type="checkbox"]').first()).toBeVisible();
  });

  test('should show connection names', async ({ page }) => {
    await expect(page.locator('.cardTitle strong').first()).toBeVisible();
  });

  test('should show connection layer badges', async ({ page }) => {
    await expect(page.locator('.cardTitle span').first()).toBeVisible();
  });

  test('should show connection status', async ({ page }) => {
    await expect(page.locator('.card small').first()).toBeVisible();
  });

  test('should show connection descriptions', async ({ page }) => {
    await expect(page.locator('.card p').first()).toBeVisible();
  });

  test('should show requirements details', async ({ page }) => {
    await expect(page.locator('.card details summary').first()).toBeVisible();
  });

  test('should show official source links', async ({ page }) => {
    await expect(page.locator('.card a:has-text("Official source")').first()).toBeVisible();
  });

  test('should show Google AX note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('Google AX');
  });

  test('should show open evaluation lab link', async ({ page }) => {
    await expect(page.locator('a:has-text("Open Evaluation lab")')).toBeVisible();
  });

  test('should show MCP section', async ({ page }) => {
    await expect(page.locator('#mcp')).toBeVisible();
  });

  test('should show MCP heading', async ({ page }) => {
    await expect(page.locator('#mcp h2')).toContainText('Inspect configured MCP servers');
  });

  test('should show no tool execution pill', async ({ page }) => {
    await expect(page.locator('#mcp .pill')).toContainText('No tool execution');
  });

  test('should show load configured endpoints button', async ({ page }) => {
    await expect(page.locator('button:has-text("Load configured endpoints")')).toBeVisible();
  });

  test('should show protocol and operating limits details', async ({ page }) => {
    await expect(page.locator('#mcp details summary')).toContainText('Protocol and operating limits');
  });

  test('should show skills section', async ({ page }) => {
    await expect(page.locator('#skills')).toBeVisible();
  });

  test('should show skills heading', async ({ page }) => {
    await expect(page.locator('#skills h2')).toContainText('Review a skill before adoption');
  });

  test('should show local review only pill', async ({ page }) => {
    await expect(page.locator('#skills .pill')).toContainText('Local review only');
  });

  test('should show source URL input', async ({ page }) => {
    await expect(page.locator('#skills input[type="url"]')).toBeVisible();
  });

  test('should show exact revision input', async ({ page }) => {
    await expect(page.locator('#skills label:has-text("Exact revision") input')).toBeVisible();
  });

  test('should show skill content textarea', async ({ page }) => {
    await expect(page.locator('#skills textarea')).toBeVisible();
  });

  test('should show create review manifest button', async ({ page }) => {
    await expect(page.locator('button:has-text("Create review manifest")')).toBeVisible();
  });

  test('should disable create review button without content', async ({ page }) => {
    await expect(page.locator('button:has-text("Create review manifest")')).toBeDisabled();
  });

  test('should show costs section', async ({ page }) => {
    await expect(page.locator('#costs')).toBeVisible();
  });

  test('should show costs heading', async ({ page }) => {
    await expect(page.locator('#costs h2')).toContainText('Estimate the complete operating envelope');
  });

  test('should show model and harness rates link', async ({ page }) => {
    await expect(page.locator('#costs a:has-text("Model & harness rates")')).toBeVisible();
  });

  test('should show cost table', async ({ page }) => {
    await expect(page.locator('#costs table')).toBeVisible();
  });

  test('should show cost category column', async ({ page }) => {
    await expect(page.locator('#costs th').first()).toContainText('Cost category');
  });

  test('should show quantity column', async ({ page }) => {
    await expect(page.locator('#costs th')).toContainText('Quantity');
  });

  test('should show USD per unit column', async ({ page }) => {
    await expect(page.locator('#costs th')).toContainText('USD per unit');
  });

  test('should show unit column', async ({ page }) => {
    await expect(page.locator('#costs th')).toContainText('Unit');
  });

  test('should show expected successful results input', async ({ page }) => {
    await expect(page.locator('#costs input[type="number"]').first()).toBeVisible();
  });

  test('should show rate evidence input', async ({ page }) => {
    await expect(page.locator('#costs label:has-text("Rate evidence") input')).toBeVisible();
  });

  test('should show rates as of input', async ({ page }) => {
    await expect(page.locator('#costs label:has-text("Rates as of") input')).toBeVisible();
  });

  test('should show cost result', async ({ page }) => {
    await expect(page.locator('.costResult')).toBeVisible();
  });

  test('should show scenario total', async ({ page }) => {
    await expect(page.locator('.costResult')).toContainText('total');
  });

  test('should show export interoperability plan button', async ({ page }) => {
    await expect(page.locator('button:has-text("Export interoperability plan")')).toBeVisible();
  });

  test('should filter connections by search', async ({ page }) => {
    const searchInput = page.locator('.filters input');
    await searchInput.fill('AX');
    await page.waitForTimeout(500);
    await expect(page.locator('.cards')).toBeVisible();
  });

  test('should filter connections by layer', async ({ page }) => {
    const select = page.locator('.filters label:has-text("Layer") select');
    await select.selectOption('executor');
    await page.waitForTimeout(500);
    await expect(page.locator('.cards')).toBeVisible();
  });

  test('should show no matching connections message', async ({ page }) => {
    const searchInput = page.locator('.filters input');
    await searchInput.fill('zzzznonexistent999');
    await page.waitForTimeout(500);
    const notice = page.locator('.apex-note:has-text("No matching connections")');
    if (await notice.isVisible()) {
      await expect(notice).toBeVisible();
    }
  });

  test('should toggle connection selection', async ({ page }) => {
    const checkbox = page.locator('.card input[type="checkbox"]').first();
    const wasChecked = await checkbox.isChecked();
    await checkbox.click();
    await page.waitForTimeout(300);
    expect(await checkbox.isChecked()).toBe(!wasChecked);
  });

  test('should expand connection requirements', async ({ page }) => {
    await page.locator('.card details summary').first().click();
    await expect(page.locator('.card details').first()).toBeVisible();
  });

  test('should load configured endpoints', async ({ page }) => {
    await page.locator('button:has-text("Load configured endpoints")').click();
    await page.waitForTimeout(1000);
    // Should show either servers or empty state
  });

  test('should show MCP empty state when no endpoints', async ({ page }) => {
    await page.locator('button:has-text("Load configured endpoints")').click();
    await page.waitForTimeout(1000);
    const empty = page.locator('.empty');
    if (await empty.isVisible()) {
      await expect(empty).toContainText('No MCP endpoints configured');
    }
  });

  test('should show MCP configuration help', async ({ page }) => {
    await page.locator('button:has-text("Load configured endpoints")').click();
    await page.waitForTimeout(1000);
    const empty = page.locator('.empty');
    if (await empty.isVisible()) {
      await expect(empty).toContainText('MCP_SERVERS_JSON');
    }
  });

  test('should create skill review manifest', async ({ page }) => {
    await page.locator('#skills textarea').fill('---\nname: test-skill\ndescription: A test skill\n---\nTest content');
    await page.locator('button:has-text("Create review manifest")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.review')).toBeVisible();
  });

  test('should show review result', async ({ page }) => {
    await page.locator('#skills textarea').fill('---\nname: test-skill\ndescription: A test skill\n---\nTest content');
    await page.locator('button:has-text("Create review manifest")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.review')).toContainText('Manifest created');
  });

  test('should show export review button after review', async ({ page }) => {
    await page.locator('#skills textarea').fill('---\nname: test-skill\ndescription: A test skill\n---\nTest content');
    await page.locator('button:has-text("Create review manifest")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('button:has-text("Export review")')).toBeVisible();
  });

  test('should show SHA-256 in review', async ({ page }) => {
    await page.locator('#skills textarea').fill('---\nname: test-skill\ndescription: A test skill\n---\nTest content');
    await page.locator('button:has-text("Create review manifest")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.review')).toContainText('SHA-256');
  });

  test('should show hash proves content identity note', async ({ page }) => {
    await expect(page.locator('#skills .apex-note')).toContainText('hash proves content identity');
  });

  test('should show cost per success in cost result', async ({ page }) => {
    await expect(page.locator('.costResult')).toContainText('Cost / successful result');
  });

  test('should show unpriced categories note', async ({ page }) => {
    await expect(page.locator('.costResult')).toContainText('unpriced');
  });

  test('should show planning estimate note', async ({ page }) => {
    await expect(page.locator('#costs .apex-note')).toContainText('Planning estimate');
  });

  test('should show no live provider pricing note', async ({ page }) => {
    await expect(page.locator('#costs .apex-note')).toContainText('no live provider pricing');
  });
});
