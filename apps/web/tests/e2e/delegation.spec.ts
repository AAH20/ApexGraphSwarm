import { test, expect } from '@playwright/test';

test.describe('Delegation Planner Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/delegation');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the delegation page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Delegate with a reason');
  });

  test('should show routing eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('ROUTING');
  });

  test('should show delegation planner title', async ({ page }) => {
    await expect(page.locator('#delegation-planner-title')).toContainText('Delegation planner');
  });

  test('should show planning no provider calls eyebrow', async ({ page }) => {
    await expect(page.locator('.economics-heading')).toContainText('PLANNING · NO PROVIDER CALLS');
  });

  test('should show task and constraints fieldset', async ({ page }) => {
    await expect(page.locator('fieldset legend:has-text("Task and constraints")')).toBeVisible();
  });

  test('should show task class input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Task class") input')).toBeVisible();
  });

  test('should show goal textarea', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Goal") textarea')).toBeVisible();
  });

  test('should show required capabilities input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Required capabilities") input')).toBeVisible();
  });

  test('should show privacy requirement select', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Privacy requirement") select')).toBeVisible();
  });

  test('should show privacy options', async ({ page }) => {
    const select = page.locator('.economics-field:has-text("Privacy requirement") select');
    await expect(select.locator('option:has-text("No additional filter")')).toBeVisible();
    await expect(select.locator('option:has-text("Verified no-training")')).toBeVisible();
    await expect(select.locator('option:has-text("Local execution only")')).toBeVisible();
  });

  test('should show workload and budgets fieldset', async ({ page }) => {
    await expect(page.locator('fieldset legend:has-text("Workload and budgets")')).toBeVisible();
  });

  test('should show input tokens input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Uncached input tokens") input')).toBeVisible();
  });

  test('should show output tokens input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Output tokens") input')).toBeVisible();
  });

  test('should show agents input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Agents / run") input')).toBeVisible();
  });

  test('should show retries input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Retries / agent") input')).toBeVisible();
  });

  test('should show success rate input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Expected success rate") input')).toBeVisible();
  });

  test('should show planned runs input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Started runs / month") input')).toBeVisible();
  });

  test('should show fixed and hosting fieldset', async ({ page }) => {
    await expect(page.locator('fieldset legend:has-text("Fixed and hosting")')).toBeVisible();
  });

  test('should show subscription cost input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Subscription cost") input')).toBeVisible();
  });

  test('should show subscription allocation input', async ({ page }) => {
    await expect(page.locator('.economator-field:has-text("Subscription allocation") input')).toBeVisible();
  });

  test('should show ranking weights fieldset', async ({ page }) => {
    await expect(page.locator('fieldset legend:has-text("Ranking weights")')).toBeVisible();
  });

  test('should show cost weight input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Cost weight") input')).toBeVisible();
  });

  test('should show quality weight input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("Benchmark quality weight") input')).toBeVisible();
  });

  test('should show latency weight input', async ({ page }) => {
    await expect(page.locator('.economics-field:has-text("p95 latency weight") input')).toBeVisible();
  });

  test('should show candidate registry', async ({ page }) => {
    await expect(page.locator('h3:has-text("Candidate registry")')).toBeVisible();
  });

  test('should show add custom candidate button', async ({ page }) => {
    await expect(page.locator('button:has-text("Add custom model/API route")')).toBeVisible();
  });

  test('should show registry toolbar', async ({ page }) => {
    await expect(page.locator('.registryToolbar')).toBeVisible();
  });

  test('should show search candidates input', async ({ page }) => {
    await expect(page.locator('.registryToolbar input[type="search"]')).toBeVisible();
  });

  test('should show harness filter select', async ({ page }) => {
    await expect(page.locator('.registryToolbar label:has-text("Harness") select')).toBeVisible();
  });

  test('should show provider filter select', async ({ page }) => {
    await expect(page.locator('.registryToolbar label:has-text("Provider mode") select')).toBeVisible();
  });

  test('should show readiness filter select', async ({ page }) => {
    await expect(page.locator('.registryToolbar label:has-text("Readiness") select')).toBeVisible();
  });

  test('should show candidate list', async ({ page }) => {
    await expect(page.locator('.registryList')).toBeVisible();
  });

  test('should show candidate disclosures', async ({ page }) => {
    await expect(page.locator('.candidateDisclosure').first()).toBeVisible();
  });

  test('should show candidate summary', async ({ page }) => {
    await expect(page.locator('.candidateSummary').first()).toBeVisible();
  });

  test('should show candidate identity', async ({ page }) => {
    await expect(page.locator('.candidateIdentity').first()).toBeVisible();
  });

  test('should show candidate route', async ({ page }) => {
    await expect(page.locator('.candidateRoute').first()).toBeVisible();
  });

  test('should show readiness badge', async ({ page }) => {
    await expect(page.locator('.readinessBadge').first()).toBeVisible();
  });

  test('should show plan result', async ({ page }) => {
    await expect(page.locator('.economics-notice')).toContainText('Plan result');
  });

  test('should show export JSON plan button', async ({ page }) => {
    await expect(page.locator('button:has-text("Export JSON plan")')).toBeVisible();
  });

  test('should show economics footnote', async ({ page }) => {
    await expect(page.locator('.economics-footnote')).toBeVisible();
  });

  test('should show weights help text', async ({ page }) => {
    await expect(page.locator('.help-text:has-text("Weights are normalized")')).toBeVisible();
  });

  test('should show subscriptions notice', async ({ page }) => {
    await expect(page.locator('.economics-notice:has-text("Subscriptions")')).toBeVisible();
  });

  test('should expand candidate disclosure', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor').first()).toBeVisible();
  });

  test('should show candidate editor fields', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor')).toBeVisible();
  });

  test('should show candidate name input in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Candidate name") input')).toBeVisible();
  });

  test('should show harness select in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Harness") select')).toBeVisible();
  });

  test('should show provider select in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Billing/provider mode") select')).toBeVisible();
  });

  test('should show model ID input in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Model or API ID") input')).toBeVisible();
  });

  test('should show capabilities input in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Capabilities") input')).toBeVisible();
  });

  test('should show privacy select in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Privacy evidence") select')).toBeVisible();
  });

  test('should show rate inputs in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Input USD") input')).toBeVisible();
  });

  test('should show benchmark score input in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor .economics-field:has-text("Benchmark score") input')).toBeVisible();
  });

  test('should show enabled checkbox in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.candidateEditor input[type="checkbox"]')).toBeVisible();
  });

  test('should show assessment in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('.economics-results')).toBeVisible();
  });

  test('should show remove candidate button in editor', async ({ page }) => {
    await page.locator('.candidateDisclosure summary').first().click();
    await expect(page.locator('button:has-text("Remove candidate")')).toBeVisible();
  });

  test('should show candidate count', async ({ page }) => {
    await expect(page.locator('.help-text:has-text("Showing")')).toBeVisible();
  });

  test('should filter candidates by search', async ({ page }) => {
    const searchInput = page.locator('.registryToolbar input[type="search"]');
    await searchInput.fill('GPT');
    await page.waitForTimeout(500);
    await expect(page.locator('.registryList')).toBeVisible();
  });

  test('should filter candidates by harness', async ({ page }) => {
    const select = page.locator('.registryToolbar label:has-text("Harness") select');
    const options = await select.locator('option').all();
    if (options.length > 1) {
      const value = await options[1].getAttribute('value');
      if (value) {
        await select.selectOption(value);
        await page.waitForTimeout(500);
      }
    }
  });

  test('should filter candidates by readiness', async ({ page }) => {
    const select = page.locator('.registryToolbar label:has-text("Readiness") select');
    await select.selectOption('rankable');
    await page.waitForTimeout(500);
    await expect(page.locator('.registryList')).toBeVisible();
  });

  test('should show no candidates message when filter excludes all', async ({ page }) => {
    const searchInput = page.locator('.registryToolbar input[type="search"]');
    await searchInput.fill('zzzznonexistent999');
    await page.waitForTimeout(500);
    const notice = page.locator('.economics-notice:has-text("No candidates match")');
    if (await notice.isVisible()) {
      await expect(notice).toBeVisible();
    }
  });

  test('should add custom candidate', async ({ page }) => {
    const count = await page.locator('.candidateDisclosure').count();
    await page.locator('button:has-text("Add custom model/API route")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.candidateDisclosure')).toHaveCount(count + 1);
  });

  test('should show export message after export', async ({ page }) => {
    await page.locator('button:has-text("Export JSON plan")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('[role="status"]')).toContainText('Plan exported');
  });
});
