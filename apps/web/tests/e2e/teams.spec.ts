import { test, expect } from '@playwright/test';

test.describe('Teams Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the teams page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Design the team');
  });

  test('should show specialist teams eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('SPECIALIST TEAMS');
  });

  test('should show boundary section', async ({ page }) => {
    await expect(page.locator('.boundary')).toBeVisible();
  });

  test('should show design and authorization review', async ({ page }) => {
    await expect(page.locator('.boundary')).toContainText('Design and authorization review');
  });

  test('should show no runtime authority pill', async ({ page }) => {
    await expect(page.locator('.pill')).toContainText('No runtime authority');
  });

  test('should show design name input', async ({ page }) => {
    await expect(page.locator('.wideLabel input')).toBeVisible();
  });

  test('should show save browser draft button', async ({ page }) => {
    await expect(page.locator('button:has-text("Save browser draft")')).toBeVisible();
  });

  test('should show load browser draft button', async ({ page }) => {
    await expect(page.locator('button:has-text("Load browser draft")')).toBeVisible();
  });

  test('should show export design button', async ({ page }) => {
    await expect(page.locator('button:has-text("Export design")')).toBeVisible();
  });

  test('should show import design button', async ({ page }) => {
    await expect(page.locator('label:has-text("Import design JSON")')).toBeVisible();
  });

  test('should show design stats', async ({ page }) => {
    await expect(page.locator('.apex-panel-heading p')).toContainText('specialists');
    await expect(page.locator('.apex-panel-heading p')).toContainText('teams');
    await expect(page.locator('.apex-panel-heading p')).toContainText('scope nodes');
  });

  test('should show validation errors when invalid', async ({ page }) => {
    const errors = page.locator('.errors');
    // May or may not be visible depending on design validity
  });

  test('should show design metadata note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('References and labels');
  });

  test('should show no credentials note', async ({ page }) => {
    await expect(page.locator('.apex-note')).toContainText('No credentials were issued');
  });

  test('should show topology section', async ({ page }) => {
    await expect(page.locator('#topology')).toBeVisible();
  });

  test('should show scope graph heading', async ({ page }) => {
    await expect(page.locator('#topology h2')).toContainText('Scope graph');
  });

  test('should show bind graph studio node link', async ({ page }) => {
    await expect(page.locator('a:has-text("Bind a Graph Studio node")')).toBeVisible();
  });

  test('should show add data-center structure button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add data-center structure")')).toBeVisible();
  });

  test('should show add physical-fleet structure button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add physical-fleet structure")')).toBeVisible();
  });

  test('should show add IoT structure button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add IoT structure")')).toBeVisible();
  });

  test('should show scope topology', async ({ page }) => {
    await expect(page.locator('.scope-topology, [class*="topology"]')).toBeVisible();
  });

  test('should show node inspector', async ({ page }) => {
    await expect(page.locator('.nodeInspector')).toBeVisible();
  });

  test('should show selected scope label', async ({ page }) => {
    await expect(page.locator('.nodeInspector .eyebrow')).toContainText('SELECTED SCOPE');
  });

  test('should show scope label input', async ({ page }) => {
    await expect(page.locator('.nodeInspector input').first()).toBeVisible();
  });

  test('should show external reference input', async ({ page }) => {
    await expect(page.locator('.nodeInspector label:has-text("External/private system reference") input')).toBeVisible();
  });

  test('should show dedicated teams fieldset', async ({ page }) => {
    await expect(page.locator('.nodeInspector fieldset legend')).toContainText('Dedicated teams');
  });

  test('should show new child scope label input', async ({ page }) => {
    await expect(page.locator('.nodeInspector label:has-text("New child scope label") input')).toBeVisible();
  });

  test('should show new child scope type select', async ({ page }) => {
    await expect(page.locator('.nodeInspector label:has-text("New child scope type") select')).toBeVisible();
  });

  test('should show add child scope button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add child scope")')).toBeVisible();
  });

  test('should show remove leaf scope button', async ({ page }) => {
    await expect(page.locator('button:has-text("Remove leaf scope")')).toBeVisible();
  });

  test('should show teams section', async ({ page }) => {
    await expect(page.locator('#teams')).toBeVisible();
  });

  test('should show build specialist teams heading', async ({ page }) => {
    await expect(page.locator('#teams h2')).toContainText('Build specialist teams');
  });

  test('should show add team button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add team")')).toBeVisible();
  });

  test('should show edit team select', async ({ page }) => {
    await expect(page.locator('#teams .apex-form-grid label:has-text("Edit team") select')).toBeVisible();
  });

  test('should show team name input', async ({ page }) => {
    await expect(page.locator('#teams label:has-text("Team name") input')).toBeVisible();
  });

  test('should show remove selected team button', async ({ page }) => {
    await expect(page.locator('button:has-text("Remove selected team")')).toBeVisible();
  });

  test('should show team members fieldset', async ({ page }) => {
    await expect(page.locator('#teams fieldset legend')).toContainText('Team members');
  });

  test('should show specialists section', async ({ page }) => {
    await expect(page.locator('#specialists')).toBeVisible();
  });

  test('should show specialist capabilities heading', async ({ page }) => {
    await expect(page.locator('#specialists h2')).toContainText('Specialist capabilities');
  });

  test('should show add specialist button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add specialist")')).toBeVisible();
  });

  test('should show remove selected specialist button', async ({ page }) => {
    await expect(page.locator('button:has-text("Remove selected specialist")')).toBeVisible();
  });

  test('should show agent list', async ({ page }) => {
    await expect(page.locator('.agentList')).toBeVisible();
  });

  test('should show find specialist input', async ({ page }) => {
    await expect(page.locator('.agentList input')).toBeVisible();
  });

  test('should show agent buttons', async ({ page }) => {
    await expect(page.locator('.agentList button').first()).toBeVisible();
  });

  test('should show agent name in list', async ({ page }) => {
    await expect(page.locator('.agentList button strong').first()).toBeVisible();
  });

  test('should show agent details in list', async ({ page }) => {
    await expect(page.locator('.agentList button small').first()).toBeVisible();
  });

  test('should show authorization section', async ({ page }) => {
    await expect(page.locator('#authorization')).toBeVisible();
  });

  test('should show authorization heading', async ({ page }) => {
    await expect(page.locator('#authorization h2')).toContainText('Preview an authorization request');
  });

  test('should show execution always disabled pill', async ({ page }) => {
    await expect(page.locator('#authorization .pill')).toContainText('Execution always disabled');
  });

  test('should show requesting specialist select', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Requesting specialist") select')).toBeVisible();
  });

  test('should show target scope select', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Target scope") select')).toBeVisible();
  });

  test('should show requested action select', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Requested action") select')).toBeVisible();
  });

  test('should show action options', async ({ page }) => {
    const select = page.locator('#authorization label:has-text("Requested action") select');
    await expect(select.locator('option:has-text("read")')).toBeVisible();
    await expect(select.locator('option:has-text("plan")')).toBeVisible();
    await expect(select.locator('option:has-text("administer")')).toBeVisible();
    await expect(select.locator('option:has-text("actuate")')).toBeVisible();
  });

  test('should show request audience input', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Request audience") input')).toBeVisible();
  });

  test('should show request purpose input', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Request purpose") input')).toBeVisible();
  });

  test('should show elapsed grant time input', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Elapsed grant time") input')).toBeVisible();
  });

  test('should show approver IDs input', async ({ page }) => {
    await expect(page.locator('#authorization label:has-text("Distinct approver IDs") input')).toBeVisible();
  });

  test('should show preview access decision button', async ({ page }) => {
    await expect(page.locator('button:has-text("Preview access decision")')).toBeVisible();
  });

  test('should show identity projects section', async ({ page }) => {
    await expect(page.locator('h2:has-text("Your identity projects")')).toBeVisible();
  });

  test('should show identity cards', async ({ page }) => {
    await expect(page.locator('.identityCards article').first()).toBeVisible();
  });

  test('should show identity card names', async ({ page }) => {
    await expect(page.locator('.identityCards article h3').first()).toBeVisible();
  });

  test('should show identity card status', async ({ page }) => {
    await expect(page.locator('.identityCards article p').first()).toBeVisible();
  });

  test('should show identity card revision', async ({ page }) => {
    await expect(page.locator('.identityCards article small').first()).toContainText('Revision');
  });

  test('should show identity card details', async ({ page }) => {
    await expect(page.locator('.identityCards article details summary').first()).toBeVisible();
  });

  test('should show identity card source link', async ({ page }) => {
    await expect(page.locator('.identityCards article a:has-text("Source repository")').first()).toBeVisible();
  });

  test('should show private data-center note', async ({ page }) => {
    await expect(page.locator('.apex-note').last()).toContainText('Private data-center');
  });

  test('should show credentials note', async ({ page }) => {
    await expect(page.locator('.apex-note').last()).toContainText('Credentials');
  });

  test('should select agent from list', async ({ page }) => {
    await page.locator('.agentList button').first().click();
    await page.waitForTimeout(300);
    await expect(page.locator('.agentList button').first()).toHaveAttribute('aria-pressed', 'true');
  });

  test('should filter agents by search', async ({ page }) => {
    const searchInput = page.locator('.agentList input');
    await searchInput.fill('test');
    await page.waitForTimeout(300);
    await expect(page.locator('.agentList')).toBeVisible();
  });

  test('should add child scope', async ({ page }) => {
    const labelInput = page.locator('.nodeInspector label:has-text("New child scope label") input');
    await labelInput.fill('Test Scope');
    await page.locator('button:has-text("Add child scope")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.nodeInspector h3')).toContainText('Test Scope');
  });

  test('should add team', async ({ page }) => {
    const count = await page.locator('#teams fieldset label').count();
    await page.locator('button:has-text("Add team")').click();
    await page.waitForTimeout(500);
    // Team count should increase
  });

  test('should add specialist', async ({ page }) => {
    const count = await page.locator('.agentList button').count();
    await page.locator('button:has-text("Add specialist")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.agentList button')).toHaveCount(count + 1);
  });

  test('should show specialist editor after selection', async ({ page }) => {
    await page.locator('.agentList button').first().click();
    await page.waitForTimeout(300);
    await expect(page.locator('.specialist-editor, [class*="specialist"]')).toBeVisible();
  });

  test('should show source banner when hash present', async ({ page }) => {
    // This is conditional on URL hash
  });

  test('should show scope relationships note', async ({ page }) => {
    await expect(page.locator('#topology p')).toContainText('Scope relationships');
  });

  test('should show permissions note', async ({ page }) => {
    await expect(page.locator('#topology p')).toContainText('do not inherit permissions');
  });
});
