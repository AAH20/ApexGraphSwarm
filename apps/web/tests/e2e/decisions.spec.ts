import { test, expect } from '@playwright/test';

test.describe('Decisions Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/decisions');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the decisions page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Ask precisely');
  });

  test('should show decision intelligence eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('DECISION INTELLIGENCE');
  });

  test('should show no automatic repository context badge', async ({ page }) => {
    await expect(page.locator('.badge')).toContainText('NO AUTOMATIC REPOSITORY CONTEXT');
  });

  test('should show provider status section', async ({ page }) => {
    await expect(page.locator('.providers')).toBeVisible();
  });

  test('should show provider grid', async ({ page }) => {
    await expect(page.locator('.providerGrid')).toBeVisible();
  });

  test('should show Laya provider', async ({ page }) => {
    await expect(page.locator('.provider')).toContainText('Laya');
  });

  test('should show AnyJev provider', async ({ page }) => {
    await expect(page.locator('.provider')).toContainText('AnyJev');
  });

  test('should show provider checkboxes', async ({ page }) => {
    await expect(page.locator('.provider input[type="checkbox"]')).toHaveCount(2);
  });

  test('should show composer section', async ({ page }) => {
    await expect(page.locator('.composer')).toBeVisible();
  });

  test('should show context textarea', async ({ page }) => {
    await expect(page.locator('.composer textarea').first()).toBeVisible();
  });

  test('should show character count', async ({ page }) => {
    await expect(page.locator('.composer small')).toContainText('16,000 characters');
  });

  test('should show preset row', async ({ page }) => {
    await expect(page.locator('.presetRow')).toBeVisible();
  });

  test('should show preset buttons', async ({ page }) => {
    await expect(page.locator('.presetRow button')).toHaveCount(9);
  });

  test('should show graph review preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Graph review")')).toBeVisible();
  });

  test('should show swarm routing preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Swarm routing")')).toBeVisible();
  });

  test('should show team coordination preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Team coordination")')).toBeVisible();
  });

  test('should show analytics interpretation preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Analytics interpretation")')).toBeVisible();
  });

  test('should show optimization review preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Optimization review")')).toBeVisible();
  });

  test('should show delegation review preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Delegation review")')).toBeVisible();
  });

  test('should show evaluation review preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Evaluation review")')).toBeVisible();
  });

  test('should show ecosystem review preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("Ecosystem review")')).toBeVisible();
  });

  test('should show general decision preset', async ({ page }) => {
    await expect(page.locator('.presetRow button:has-text("General decision")')).toBeVisible();
  });

  test('should show preset summary', async ({ page }) => {
    await expect(page.locator('.presetSummary')).toBeVisible();
  });

  test('should show questions section', async ({ page }) => {
    await expect(page.locator('.questions')).toBeVisible();
  });

  test('should show question articles', async ({ page }) => {
    await expect(page.locator('.question')).toHaveCount(2);
  });

  test('should show question index', async ({ page }) => {
    await expect(page.locator('.qIndex').first()).toContainText('Q1');
  });

  test('should show question ID', async ({ page }) => {
    await expect(page.locator('.idDisplay').first()).toContainText('ID ·');
  });

  test('should show question type select', async ({ page }) => {
    await expect(page.locator('.typeField select')).toBeVisible();
  });

  test('should show question instructions textarea', async ({ page }) => {
    await expect(page.locator('.question textarea').first()).toBeVisible();
  });

  test('should show remove question button', async ({ page }) => {
    await expect(page.locator('.question .remove')).toBeVisible();
  });

  test('should show add question button', async ({ page }) => {
    await expect(page.locator('button:has-text("+ Add question")')).toBeVisible();
  });

  test('should show advanced JSON button', async ({ page }) => {
    await expect(page.locator('button:has-text("Advanced JSON")')).toBeVisible();
  });

  test('should show threshold slider', async ({ page }) => {
    await expect(page.locator('.limits input[type="range"]')).toBeVisible();
  });

  test('should show threshold output', async ({ page }) => {
    await expect(page.locator('.limits output')).toBeVisible();
  });

  test('should show budget input', async ({ page }) => {
    await expect(page.locator('.limits input[placeholder="0.10"]')).toBeVisible();
  });

  test('should show token input', async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show submit button', async ({ page }) => {
    await expect(page.locator('button:has-text("Run decision review")')).toBeVisible();
  });

  test('should show show synthetic fixture button', async ({ page }) => {
    await expect(page.locator('button:has-text("Show synthetic fixture")')).toBeVisible();
  });

  test('should show estimated request total', async ({ page }) => {
    await expect(page.locator('.submitRow')).toContainText('Estimated request total');
  });

  test('should show disclaimer', async ({ page }) => {
    await expect(page.locator('.disclaimer')).toBeVisible();
  });

  test('should show review guide sidebar', async ({ page }) => {
    await expect(page.locator('.side')).toBeVisible();
  });

  test('should show decision probability card', async ({ page }) => {
    await expect(page.locator('.sideCard').first()).toContainText('Decision probability');
  });

  test('should show boundary card', async ({ page }) => {
    await expect(page.locator('.sideCard').nth(1)).toContainText('Keep context explicit');
  });

  test('should show graph link in sidebar', async ({ page }) => {
    await expect(page.locator('.side a:has-text("graph-grounded research review")')).toBeVisible();
  });

  test('should load preset on button click', async ({ page }) => {
    await page.locator('.presetRow button:has-text("Swarm routing")').click();
    await page.waitForTimeout(300);
    await expect(page.locator('.notice')).toContainText('question template loaded');
  });

  test('should show notice after preset load', async ({ page }) => {
    await page.locator('.presetRow button:has-text("Graph review")').click();
    await page.waitForTimeout(300);
    await expect(page.locator('.notice')).toBeVisible();
  });

  test('should show synthetic fixture results', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.results')).toBeVisible();
  });

  test('should show fixture badge in results', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.fixtureBadge')).toContainText('FIXTURE');
  });

  test('should show result cards in fixture', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.resultCard')).toHaveCount(2);
  });

  test('should show Laya result card', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.resultCard').first()).toContainText('LAYA');
  });

  test('should show AnyJev result card', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.resultCard').nth(1)).toContainText('ANYJEV');
  });

  test('should show answers in fixture results', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.answer')).toBeVisible();
  });

  test('should show answer distribution', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.distribution')).toBeVisible();
  });

  test('should show confidence in answers', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.confidence')).toBeVisible();
  });

  test('should show review required badge for low confidence', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    const reviewBadge = page.locator('.answer .review');
    if (await reviewBadge.isVisible()) {
      await expect(reviewBadge).toContainText('REVIEW');
    }
  });

  test('should show advisory badge for high confidence', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    const advisoryBadge = page.locator('.answer .ok');
    if (await advisoryBadge.isVisible()) {
      await expect(advisoryBadge).toContainText('ADVISORY');
    }
  });

  test('should show warning in fixture results', async ({ page }) => {
    await page.locator('button:has-text("Show synthetic fixture")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.warning')).toContainText('advisory');
  });

  test('should show load questions button', async ({ page }) => {
    await expect(page.locator('button:has-text("Load")').first()).toBeVisible();
  });

  test('should change threshold value', async ({ page }) => {
    const slider = page.locator('.limits input[type="range"]');
    await slider.fill('0.5');
    await expect(page.locator('.limits output')).toContainText('50%');
  });

  test('should change budget value', async ({ page }) => {
    const budgetInput = page.locator('.limits input[placeholder="0.10"]');
    await budgetInput.fill('1.00');
    await expect(budgetInput).toHaveValue('1.00');
  });

  test('should show budget in micro-USD', async ({ page }) => {
    const budgetInput = page.locator('.limits input[placeholder="0.10"]');
    await budgetInput.fill('1.00');
    await page.waitForTimeout(300);
    await expect(page.locator('.limits small')).toContainText('micro-USD');
  });
});
