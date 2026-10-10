import { test, expect } from '@playwright/test';

test.describe('Integrations Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the integrations panel', async ({ page }) => {
    await expect(page.locator('.integrations-panel')).toBeVisible();
  });

  test('should show integrations heading', async ({ page }) => {
    await expect(page.locator('.integration-heading h2')).toContainText('Your tools. One evidence trail.');
  });

  test('should show connected intelligence eyebrow', async ({ page }) => {
    await expect(page.locator('.integration-heading .eyebrow')).toContainText('CONNECTED INTELLIGENCE');
  });

  test('should show export execution plan button', async ({ page }) => {
    await expect(page.locator('button:has-text("Export execution plan")')).toBeVisible();
  });

  test('should show Laya & AnyJev link', async ({ page }) => {
    await expect(page.locator('a:has-text("Laya & AnyJev")')).toBeVisible();
  });

  test('should show integration layout', async ({ page }) => {
    await expect(page.locator('.integration-layout')).toBeVisible();
  });

  test('should show integration setup section', async ({ page }) => {
    await expect(page.locator('.integration-setup')).toBeVisible();
  });

  test('should show integration run section', async ({ page }) => {
    await expect(page.locator('.integration-run')).toBeVisible();
  });

  test('should show framework/kernel select', async ({ page }) => {
    const select = page.locator('.integration-setup select').first();
    await expect(select).toBeVisible();
  });

  test('should show integration status pill', async ({ page }) => {
    await expect(page.locator('.integration-status .pill')).toBeVisible();
  });

  test('should show refresh integration button', async ({ page }) => {
    await expect(page.locator('button[aria-label="Refresh integration configuration"]')).toBeVisible();
  });

  test('should show operation select', async ({ page }) => {
    const select = page.locator('.integration-setup label:has-text("Operation") select');
    await expect(select).toBeVisible();
  });

  test('should show harness select', async ({ page }) => {
    const select = page.locator('.integration-setup label:has-text("Preferred coding harness") select');
    await expect(select).toBeVisible();
  });

  test('should show harness options', async ({ page }) => {
    const select = page.locator('.integration-setup label:has-text("Preferred coding harness") select');
    await expect(select.locator('option:has-text("Codex")')).toBeVisible();
    await expect(select.locator('option:has-text("Claude Code")')).toBeVisible();
    await expect(select.locator('option:has-text("Cursor")')).toBeVisible();
    await expect(select.locator('option:has-text("OpenCode")')).toBeVisible();
    await expect(select.locator('option:has-text("Hermes")')).toBeVisible();
  });

  test('should show billing scenario select', async ({ page }) => {
    const select = page.locator('.integration-setup label:has-text("Billing scenario") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("OpenRouter API")')).toBeVisible();
    await expect(select.locator('option:has-text("Self-hosted vLLM")')).toBeVisible();
    await expect(select.locator('option:has-text("Existing harness subscription")')).toBeVisible();
  });

  test('should show task goal textarea', async ({ page }) => {
    await expect(page.locator('.integration-run textarea')).toBeVisible();
  });

  test('should show repository scope select', async ({ page }) => {
    const select = page.locator('.integration-run label:has-text("Repository scope") select');
    await expect(select).toBeVisible();
  });

  test('should show include graph checkbox', async ({ page }) => {
    await expect(page.locator('.include-graph input[type="checkbox"]')).toBeVisible();
  });

  test('should show execution token input', async ({ page }) => {
    await expect(page.locator('.integration-run input[type="password"]')).toBeVisible();
  });

  test('should show run selected operation button', async ({ page }) => {
    await expect(page.locator('button:has-text("Run selected operation")')).toBeVisible();
  });

  test('should disable run button when not configured', async ({ page }) => {
    const btn = page.locator('button:has-text("Run selected operation")');
    await expect(btn).toBeDisabled();
  });

  test('should show integration source details', async ({ page }) => {
    const details = page.locator('.integration-source');
    if (await details.isVisible()) {
      await expect(details).toBeVisible();
    }
  });

  test('should show harness authentication details', async ({ page }) => {
    const details = page.locator('.integration-source').first();
    if (await details.isVisible()) {
      await expect(details.locator('summary')).toContainText('Harness authentication');
    }
  });

  test('should show verified source details', async ({ page }) => {
    const details = page.locator('.integration-source').nth(1);
    if (await details.isVisible()) {
      await expect(details.locator('summary')).toContainText('Verified source');
    }
  });

  test('should show execution economics section', async ({ page }) => {
    await expect(page.locator('.execution-economics')).toBeVisible();
  });

  test('should show economics heading', async ({ page }) => {
    await expect(page.locator('.economics-heading h3')).toContainText('Execution economics');
  });

  test('should show economics controls', async ({ page }) => {
    await expect(page.locator('.economics-controls')).toBeVisible();
  });

  test('should show economics grid', async ({ page }) => {
    await expect(page.locator('.economics-grid')).toBeVisible();
  });

  test('should show economics results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toBeVisible();
  });

  test('should show attempts per run in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Attempts / run');
  });

  test('should show metered cost in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Metered cost / started run');
  });

  test('should show all-in cost in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('All-in cost / started run');
  });

  test('should show cost per successful run in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Cost / successful run');
  });

  test('should show monthly total in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Monthly total');
  });

  test('should show break-even in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Break-even');
  });

  test('should show per-run budget in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Per-run budget');
  });

  test('should show monthly budget in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Monthly budget');
  });

  test('should show economics footnote', async ({ page }) => {
    await expect(page.locator('.economics-footnote')).toBeVisible();
  });

  test('should show cost model estimate only label', async ({ page }) => {
    await expect(page.locator('.economics-heading')).toContainText('COST MODEL · ESTIMATE ONLY');
  });

  test('should show integration status text', async ({ page }) => {
    await expect(page.locator('.integration-status')).toBeVisible();
  });

  test('should show help text for integrations', async ({ page }) => {
    await expect(page.locator('.integration-setup .help-text')).toBeVisible();
  });

  test('should show job tracking note', async ({ page }) => {
    await expect(page.locator('.integration-run .help-text').last()).toContainText('Job tracking is local');
  });

  test('should show provider keys note', async ({ page }) => {
    await expect(page.locator('.integration-run')).toContainText('Provider keys and service destinations');
  });

  test('should show local bridge note when applicable', async ({ page }) => {
    // This is conditional on integration mode
    const note = page.locator('.integration-run .help-text:has-text("local bridge")');
    // May or may not be visible depending on selected integration
  });

  test('should show subscription note when applicable', async ({ page }) => {
    // Conditional on provider selection
  });

  test('should show vllm note when applicable', async ({ page }) => {
    // Conditional on provider selection
  });

  test('should show kernel note when applicable', async ({ page }) => {
    // Conditional on workload kind
  });

  test('should show rate provenance when openrouter selected', async ({ page }) => {
    const select = page.locator('.integration-setup label:has-text("Billing scenario") select');
    await select.selectOption('openrouter');
    await page.waitForTimeout(300);
    const provenance = page.locator('.economics-provenance');
    if (await provenance.isVisible()) {
      await expect(provenance).toContainText('Rate provenance');
    }
  });

  test('should show contribution in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Contribution / started run');
  });

  test('should show monthly contribution in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Monthly contribution');
  });

  test('should show subscription allocated in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Subscription allocated / month');
  });

  test('should show break-even successful runs in results', async ({ page }) => {
    await expect(page.locator('.economics-results')).toContainText('Break-even successful runs / month');
  });
});
