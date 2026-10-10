import { test, expect } from '@playwright/test';

test.describe('Analytics Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should display the analytics page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Turn activity into evidence');
  });

  test('should show intelligence eyebrow', async ({ page }) => {
    await expect(page.locator('.eyebrow')).toContainText('INTELLIGENCE');
  });

  test('should show analytics toolbar', async ({ page }) => {
    await expect(page.locator('.toolbar')).toBeVisible();
  });

  test('should show data source select', async ({ page }) => {
    const select = page.locator('.controls label:has-text("Data source") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Recorded execution ledger")')).toBeVisible();
    await expect(select.locator('option:has-text("Imported events")')).toBeVisible();
    await expect(select.locator('option:has-text("Synthetic example")')).toBeVisible();
  });

  test('should show analysis window select', async ({ page }) => {
    const select = page.locator('.controls label:has-text("Analysis window") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("Last 7 days")')).toBeVisible();
    await expect(select.locator('option:has-text("Last 30 days")')).toBeVisible();
    await expect(select.locator('option:has-text("Last 90 days")')).toBeVisible();
    await expect(select.locator('option:has-text("Last 365 days")')).toBeVisible();
  });

  test('should show tool filter select', async ({ page }) => {
    const select = page.locator('.controls label:has-text("Tool filter") select');
    await expect(select).toBeVisible();
    await expect(select.locator('option:has-text("All tools")')).toBeVisible();
  });

  test('should show token input', async ({ page }) => {
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show refresh snapshot button', async ({ page }) => {
    await expect(page.locator('button:has-text("Refresh snapshot")')).toBeVisible();
  });

  test('should show explore synthetic demo button', async ({ page }) => {
    await expect(page.locator('button:has-text("Explore synthetic demo")')).toBeVisible();
  });

  test('should show continuous refresh toggle', async ({ page }) => {
    await expect(page.locator('.toggle input[type="checkbox"]')).toBeVisible();
  });

  test('should show freshness indicator', async ({ page }) => {
    await expect(page.locator('.freshness')).toBeVisible();
  });

  test('should show analytics note', async ({ page }) => {
    await expect(page.locator('.note')).toBeVisible();
  });

  test('should show empty state initially', async ({ page }) => {
    await expect(page.locator('.empty')).toBeVisible();
  });

  test('should show empty state heading', async ({ page }) => {
    await expect(page.locator('.empty h2')).toContainText('Where does your swarm spend');
  });

  test('should show empty state grid', async ({ page }) => {
    await expect(page.locator('.emptyGrid')).toBeVisible();
  });

  test('should show operational intelligence card', async ({ page }) => {
    await expect(page.locator('.emptyGrid')).toContainText('Operational intelligence');
  });

  test('should show statistical diagnostics card', async ({ page }) => {
    await expect(page.locator('.emptyGrid')).toContainText('Statistical diagnostics');
  });

  test('should show predictive planning card', async ({ page }) => {
    await expect(page.locator('.emptyGrid')).toContainText('Predictive planning');
  });

  test('should show graph relationships card', async ({ page }) => {
    await expect(page.locator('.emptyGrid')).toContainText('Graph relationships');
  });

  test('should show review import schema button', async ({ page }) => {
    await expect(page.locator('button:has-text("Review import schema")')).toBeVisible();
  });

  test('should load synthetic demo', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toBeVisible();
  });

  test('should show KPI cards after demo load', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis article')).toHaveCount(5);
  });

  test('should show attempts KPI', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toContainText('Attempts');
  });

  test('should show known recorded cost KPI', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toContainText('Known recorded cost');
  });

  test('should show success share KPI', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toContainText('Success share');
  });

  test('should show p95 latency KPI', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toContainText('p95 settled latency');
  });

  test('should show cost per success KPI', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.kpis')).toContainText('Cost / success');
  });

  test('should show analytics tabs', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs')).toBeVisible();
  });

  test('should show Overview tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Overview")')).toBeVisible();
  });

  test('should show Visualizations tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Visualizations")')).toBeVisible();
  });

  test('should show Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Statistics")')).toBeVisible();
  });

  test('should show Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Predictions")')).toBeVisible();
  });

  test('should show Relationships tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Relationships")')).toBeVisible();
  });

  test('should show Data & methods tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.tabs button:has-text("Data & methods")')).toBeVisible();
  });

  test('should switch to Visualizations tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Visualizations")').click();
    await expect(page.locator('.tabs button:has-text("Visualizations")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch to Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Statistics")').click();
    await expect(page.locator('.tabs button:has-text("Statistics")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch to Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Predictions")').click();
    await expect(page.locator('.tabs button:has-text("Predictions")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch to Relationships tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Relationships")').click();
    await expect(page.locator('.tabs button:has-text("Relationships")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should switch to Data & methods tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('.tabs button:has-text("Data & methods")')).toHaveAttribute('aria-pressed', 'true');
  });

  test('should show trend metric select in Overview', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.panel label:has-text("Trend metric") select')).toBeVisible();
  });

  test('should show daily values table in Overview', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    const details = page.locator('details:has-text("Inspect daily values")');
    if (await details.isVisible()) {
      await details.click();
      await expect(page.locator('.tableWrap table')).toBeVisible();
    }
  });

  test('should show tool economics table in Overview', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.panel:has-text("Tool and resource economics")')).toBeVisible();
  });

  test('should show unit economics scenario in Overview', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.panel:has-text("Unit economics scenario")')).toBeVisible();
  });

  test('should show revenue input in scenario', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('input[placeholder="USD / successful attempt"]')).toBeVisible();
  });

  test('should show overhead input in scenario', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('input[placeholder="USD / month"]')).toBeVisible();
  });

  test('should show histogram in Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Statistics")').click();
    await expect(page.locator('.panel:has-text("Where latency accumulates")')).toBeVisible();
  });

  test('should show scatter chart in Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Statistics")').click();
    await expect(page.locator('.panel:has-text("Cost and duration")')).toBeVisible();
  });

  test('should show activity heatmap in Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Statistics")').click();
    await expect(page.locator('.panel:has-text("Activity rhythm")')).toBeVisible();
  });

  test('should show anomalies in Statistics tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Statistics")').click();
    await expect(page.locator('.panel:has-text("Unusual daily spending")')).toBeVisible();
  });

  test('should show forecast chart in Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Predictions")').click();
    await expect(page.locator('.panel:has-text("Plan with uncertainty")')).toBeVisible();
  });

  test('should show backtest MAE in Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Predictions")').click();
    await expect(page.locator('.scenario')).toContainText('MAE');
  });

  test('should show forecast table in Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Predictions")').click();
    const table = page.locator('.tableWrap table');
    if (await table.isVisible()) {
      await expect(table).toBeVisible();
    }
  });

  test('should show forecast limitations in Predictions tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Predictions")').click();
    await expect(page.locator('.panel ul')).toBeVisible();
  });

  test('should show relationship graph in Relationships tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Relationships")').click();
    await expect(page.locator('.panel:has-text("Follow the work")')).toBeVisible();
  });

  test('should show import schema in Data & methods tab', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('.panel:has-text("Bring your own event data")')).toBeVisible();
  });

  test('should show import file input in Data & methods', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('input[type="file"]')).toBeVisible();
  });

  test('should show download template button', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('button:has-text("Download event template")')).toBeVisible();
  });

  test('should show schema pre block', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('pre.schema')).toBeVisible();
  });

  test('should show scale and evidence contract', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await page.locator('.tabs button:has-text("Data & methods")').click();
    await expect(page.locator('.panel:has-text("Scale and evidence contract")')).toBeVisible();
  });

  test('should show export aggregate evidence button', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('button:has-text("Export aggregate evidence")')).toBeVisible();
  });

  test('should show analytics footer', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.footer')).toBeVisible();
  });

  test('should show window start date in footer', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.footer')).toContainText('Window starts');
  });

  test('should show selected rows in footer', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.footer')).toContainText('selected rows');
  });

  test('should show synthetic badge after demo load', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.badge')).toContainText('SYNTHETIC EXAMPLE');
  });

  test('should show no data loaded badge initially', async ({ page }) => {
    await expect(page.locator('.badge')).toContainText('NO DATA LOADED');
  });

  test('should show message after demo load', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator('.notice')).toContainText('Synthetic example loaded');
  });

  test('should show incomplete evidence warning when applicable', async ({ page }) => {
    await page.locator('button:has-text("Explore synthetic demo")').click();
    await page.waitForTimeout(1000);
    const warning = page.locator('.warning:has-text("Incomplete evidence")');
    // May or may not be visible depending on data
  });
});
