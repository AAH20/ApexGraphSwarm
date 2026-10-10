import { test, expect } from '@playwright/test';

test.describe('Navigation & App Shell', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display the app shell', async ({ page }) => {
    await expect(page.locator('.app-shell')).toBeVisible();
  });

  test('should show the sidebar', async ({ page }) => {
    await expect(page.locator('.app-sidebar')).toBeVisible();
  });

  test('should display the brand logo', async ({ page }) => {
    await expect(page.locator('.brand')).toContainText('ApexGraphSwarm');
  });

  test('should show agent engineering tagline', async ({ page }) => {
    await expect(page.locator('.brand')).toContainText('AGENT ENGINEERING');
  });

  test('should display main navigation', async ({ page }) => {
    await expect(page.locator('nav[aria-label="Main navigation"]')).toBeVisible();
  });

  test('should show Control room nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Control room")')).toBeVisible();
  });

  test('should show Graph Studio nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Graph Studio")')).toBeVisible();
  });

  test('should show Swarm control nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Swarm control")')).toBeVisible();
  });

  test('should show Specialist teams nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Specialist teams")')).toBeVisible();
  });

  test('should show Delegation & cost nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Delegation & cost")')).toBeVisible();
  });

  test('should show Optimization & hierarchy nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Optimization & hierarchy")')).toBeVisible();
  });

  test('should show Data & intelligence nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Data & intelligence")')).toBeVisible();
  });

  test('should show Decision intelligence nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Decision intelligence")')).toBeVisible();
  });

  test('should show Evaluation lab nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Evaluation lab")')).toBeVisible();
  });

  test('should show Swarm Arena nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Swarm Arena")')).toBeVisible();
  });

  test('should show Presentation Studio nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Presentation Studio")')).toBeVisible();
  });

  test('should show Ecosystem nav link', async ({ page }) => {
    await expect(page.locator('nav a:has-text("Ecosystem")')).toBeVisible();
  });

  test('should show engineering workspace section label', async ({ page }) => {
    await expect(page.locator('.nav-section')).toContainText('ENGINEERING WORKSPACE');
  });

  test('should show sidebar note', async ({ page }) => {
    await expect(page.locator('.sidebar-note')).toBeVisible();
    await expect(page.locator('.sidebar-note')).toContainText('Evidence before scale');
  });

  test('should show local engineering preview label', async ({ page }) => {
    await expect(page.locator('.sidebar-note')).toContainText('Local engineering preview');
  });

  test('should show framework integrations link', async ({ page }) => {
    await expect(page.locator('.sidebar-bottom a:has-text("Framework integrations")')).toBeVisible();
  });

  test('should show experienced mentorship link', async ({ page }) => {
    await expect(page.locator('.sidebar-bottom a:has-text("Experienced mentorship")')).toBeVisible();
  });

  test('should show version tag', async ({ page }) => {
    await expect(page.locator('.version-tag')).toContainText('APEXGRAPH');
  });

  test('should show skip to workspace link', async ({ page }) => {
    await expect(page.locator('.skip-link')).toBeVisible();
  });

  test('should show main workspace area', async ({ page }) => {
    await expect(page.locator('.main-workspace')).toBeVisible();
  });

  test('should navigate to Graph Studio', async ({ page }) => {
    await page.locator('nav a:has-text("Graph Studio")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/graph/);
  });

  test('should navigate to Swarm control', async ({ page }) => {
    await page.locator('nav a:has-text("Swarm control")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/swarm/);
  });

  test('should navigate to Control room', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.locator('nav a:has-text("Control room")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\//);
  });

  test('should show active nav indicator', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.nav-link.active')).toBeVisible();
  });

  test('should show nav dot for active page', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.nav-dot')).toBeVisible();
  });

  test('should navigate to Teams page', async ({ page }) => {
    await page.locator('nav a:has-text("Specialist teams")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/teams/);
  });

  test('should navigate to Analytics page', async ({ page }) => {
    await page.locator('nav a:has-text("Data & intelligence")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/analytics/);
  });

  test('should navigate to Decisions page', async ({ page }) => {
    await page.locator('nav a:has-text("Decision intelligence")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/decisions/);
  });

  test('should navigate to Ecosystem page', async ({ page }) => {
    await page.locator('nav a:has-text("Ecosystem")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/ecosystem/);
  });

  test('should navigate to Evaluations page', async ({ page }) => {
    await page.locator('nav a:has-text("Evaluation lab")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/evaluations/);
  });

  test('should navigate to Arena page', async ({ page }) => {
    await page.locator('nav a:has-text("Swarm Arena")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/arena/);
  });

  test('should navigate to Presentations page', async ({ page }) => {
    await page.locator('nav a:has-text("Presentation Studio")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/presentations/);
  });

  test('should navigate to Delegation page', async ({ page }) => {
    await page.locator('nav a:has-text("Delegation & cost")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/delegation/);
  });

  test('should navigate to Optimization page', async ({ page }) => {
    await page.locator('nav a:has-text("Optimization & hierarchy")').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/optimization/);
  });

  test('should show overview page content', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Build coordinated intelligence');
  });

  test('should show overview capabilities', async ({ page }) => {
    await expect(page.locator('.apex-tool-card')).toHaveCount(4);
  });

  test('should show overview principles', async ({ page }) => {
    await expect(page.locator('.apex-principles')).toBeVisible();
  });

  test('should show 300 logical agents principle', async ({ page }) => {
    await expect(page.locator('.apex-principles')).toContainText('300');
  });

  test('should show bounded principle', async ({ page }) => {
    await expect(page.locator('.apex-principles')).toContainText('Bounded');
  });

  test('should show versioned principle', async ({ page }) => {
    await expect(page.locator('.apex-principles')).toContainText('Versioned');
  });

  test('should show auditable principle', async ({ page }) => {
    await expect(page.locator('.apex-principles')).toContainText('Auditable');
  });

  test('should show overview boundary section', async ({ page }) => {
    await expect(page.locator('.apex-boundary')).toBeVisible();
  });

  test('should show explore graph button', async ({ page }) => {
    await expect(page.locator('a:has-text("Explore the graph")')).toBeVisible();
  });

  test('should show open swarm control button', async ({ page }) => {
    await expect(page.locator('a:has-text("Open swarm control")')).toBeVisible();
  });
});
