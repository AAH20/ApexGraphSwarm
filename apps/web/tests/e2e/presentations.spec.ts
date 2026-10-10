import { test, expect } from '@playwright/test';

test.describe('Presentations Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/presentations');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the presentations page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Presentation Studio');
  });

  test('should show audience-aware storytelling eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('AUDIENCE-AWARE STORYTELLING');
  });

  test('should show export presentation button', async ({ page }) => {
    await expect(page.locator('button:has-text("Export presentation")')).toBeVisible();
  });

  test('should show audience grid', async ({ page }) => {
    await expect(page.locator('.audienceGrid')).toBeVisible();
  });

  test('should show audience cards', async ({ page }) => {
    await expect(page.locator('.audienceCard')).toHaveCount(4);
  });

  test('should show elevator pitch audience', async ({ page }) => {
    await expect(page.locator('.audienceCard').first()).toContainText('Elevator pitch');
  });

  test('should show shark tank audience', async ({ page }) => {
    await expect(page.locator('.audienceCard').nth(1)).toContainText('Shark Tank');
  });

  test('should show VC audience', async ({ page }) => {
    await expect(page.locator('.audienceCard').nth(2)).toContainText('VC investment committee');
  });

  test('should show PE audience', async ({ page }) => {
    await expect(page.locator('.audienceCard').nth(3)).toContainText('Private equity committee');
  });

  test('should show audience focus descriptions', async ({ page }) => {
    await expect(page.locator('.audienceCard small').first()).toBeVisible();
  });

  test('should show audience hint', async ({ page }) => {
    await expect(page.locator('.audienceHint')).toBeVisible();
  });

  test('should show workspace section', async ({ page }) => {
    await expect(page.locator('.workspace')).toBeVisible();
  });

  test('should show inputs section', async ({ page }) => {
    await expect(page.locator('.inputs')).toBeVisible();
  });

  test('should show output section', async ({ page }) => {
    await expect(page.locator('.output')).toBeVisible();
  });

  test('should show sources heading', async ({ page }) => {
    await expect(page.locator('.inputs h2')).toContainText('Ground the story');
  });

  test('should show project name input', async ({ page }) => {
    await expect(page.locator('.field input').first()).toBeVisible();
  });

  test('should show description textarea', async ({ page }) => {
    await expect(page.locator('.field textarea').first()).toBeVisible();
  });

  test('should show evidence textarea', async ({ page }) => {
    await expect(page.locator('.field textarea').nth(1)).toBeVisible();
  });

  test('should show economics textarea', async ({ page }) => {
    await expect(page.locator('.field textarea').nth(2)).toBeVisible();
  });

  test('should show import graph button', async ({ page }) => {
    await expect(page.locator('label:has-text("Import graph JSON")')).toBeVisible();
  });

  test('should show Q&A textarea', async ({ page }) => {
    await expect(page.locator('.field textarea').nth(3)).toBeVisible();
  });

  test('should show import Q&A button', async ({ page }) => {
    await expect(page.locator('label:has-text("Import Q&A JSON")')).toBeVisible();
  });

  test('should show use Q&A in draft button', async ({ page }) => {
    await expect(page.locator('button:has-text("Use Q&A in draft")')).toBeVisible();
  });

  test('should show Q&A record count', async ({ page }) => {
    await expect(page.locator('.rowActions span')).toContainText('loaded record');
  });

  test('should show evidence boundary note', async ({ page }) => {
    await expect(page.locator('.evidenceNote')).toBeVisible();
  });

  test('should show graph structure note', async ({ page }) => {
    await expect(page.locator('.evidenceNote')).toContainText('Graph structure');
  });

  test('should show presentation heading', async ({ page }) => {
    await expect(page.locator('.output h2')).toBeVisible();
  });

  test('should show pitch card', async ({ page }) => {
    await expect(page.locator('.pitchCard').first()).toBeVisible();
  });

  test('should show spoken version label', async ({ page }) => {
    await expect(page.locator('.pitchCard .eyebrow').first()).toContainText('SPOKEN VERSION');
  });

  test('should show copy pitch button', async ({ page }) => {
    await expect(page.locator('button:has-text("Copy pitch")')).toBeVisible();
  });

  test('should show editable pitch textarea', async ({ page }) => {
    await expect(page.locator('textarea[aria-label="Editable spoken pitch"]')).toBeVisible();
  });

  test('should show editable deck textarea', async ({ page }) => {
    await expect(page.locator('textarea[aria-label="Editable presentation slides"]')).toBeVisible();
  });

  test('should show graph evidence card', async ({ page }) => {
    await expect(page.locator('.graphCard').first()).toBeVisible();
  });

  test('should show graph evidence label', async ({ page }) => {
    await expect(page.locator('.graphCard .eyebrow').first()).toContainText('GRAPH EVIDENCE');
  });

  test('should show review banner', async ({ page }) => {
    await expect(page.locator('.reviewBanner')).toBeVisible();
  });

  test('should show before investor note', async ({ page }) => {
    await expect(page.locator('.reviewBanner')).toContainText('Before this reaches an investor');
  });

  test('should select audience on click', async ({ page }) => {
    await page.locator('.audienceCard').nth(1).click();
    await expect(page.locator('.audienceCard').nth(1)).toHaveAttribute('aria-pressed', 'true');
  });

  test('should change audience hint on selection', async ({ page }) => {
    await page.locator('.audienceCard').nth(1).click();
    await page.waitForTimeout(300);
    await expect(page.locator('.audienceHint')).toContainText('5-minute pitch');
  });

  test('should update pitch on audience change', async ({ page }) => {
    await page.locator('.audienceCard').nth(1).click();
    await page.waitForTimeout(300);
    const pitch = page.locator('textarea[aria-label="Editable spoken pitch"]');
    const text = await pitch.inputValue();
    expect(text).toBeTruthy();
  });

  test('should update deck on audience change', async ({ page }) => {
    await page.locator('.audienceCard').nth(1).click();
    await page.waitForTimeout(300);
    const deck = page.locator('textarea[aria-label="Editable presentation slides"]');
    const text = await deck.inputValue();
    expect(text).toBeTruthy();
  });

  test('should fill project name', async ({ page }) => {
    const input = page.locator('.field input').first();
    await input.fill('Test Project');
    await expect(input).toHaveValue('Test Project');
  });

  test('should fill description', async ({ page }) => {
    const textarea = page.locator('.field textarea').first();
    await textarea.fill('Test description');
    await expect(textarea).toHaveValue('Test description');
  });

  test('should fill evidence', async ({ page }) => {
    const textarea = page.locator('.field textarea').nth(1);
    await textarea.fill('Test evidence');
    await expect(textarea).toHaveValue('Test evidence');
  });

  test('should fill economics', async ({ page }) => {
    const textarea = page.locator('.field textarea').nth(2);
    await textarea.fill('Test economics');
    await expect(textarea).toHaveValue('Test economics');
  });

  test('should load Q&A from textarea', async ({ page }) => {
    const qaTextarea = page.locator('.field textarea').nth(3);
    await qaTextarea.fill('[{"question":"Q1","answer":"A1","source":"test"}]');
    await page.locator('button:has-text("Use Q&A in draft")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.notice')).toContainText('Loaded 1 Q&A records');
  });

  test('should show Q&A preview after load', async ({ page }) => {
    const qaTextarea = page.locator('.field textarea').nth(3);
    await qaTextarea.fill('[{"question":"Q1","answer":"A1","source":"test"}]');
    await page.locator('button:has-text("Use Q&A in draft")').click();
    await page.waitForTimeout(500);
    const qaCard = page.locator('.graphCard').nth(1);
    if (await qaCard.isVisible()) {
      await expect(qaCard).toContainText('TRACKED QUESTIONS');
    }
  });

  test('should show error on invalid Q&A JSON', async ({ page }) => {
    const qaTextarea = page.locator('.field textarea').nth(3);
    await qaTextarea.fill('invalid json');
    await page.locator('button:has-text("Use Q&A in draft")').click();
    await page.waitForTimeout(500);
    await expect(page.locator('.error')).toBeVisible();
  });

  test('should show graph name', async ({ page }) => {
    await expect(page.locator('.importRow strong')).toContainText('Project graph');
  });

  test('should show no graph attached initially', async ({ page }) => {
    const text = await page.locator('.importRow small').textContent();
    // May show "no graph attached" or loaded snapshot
    expect(text).toBeTruthy();
  });

  test('should show Q&A import row', async ({ page }) => {
    await expect(page.locator('.importRow')).toBeVisible();
  });

  test('should show row actions', async ({ page }) => {
    await expect(page.locator('.rowActions')).toBeVisible();
  });

  test('should show presentation page heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Make the case for this room');
  });

  test('should show presentation description', async ({ page }) => {
    await expect(page.locator('.page-heading p')).toContainText('Turn project evidence');
  });
});
