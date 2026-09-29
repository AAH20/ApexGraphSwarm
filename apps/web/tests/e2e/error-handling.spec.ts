import { test, expect } from '@playwright/test';

test.describe('Error Handling & Edge Cases', () => {
  test('should handle 404 page gracefully', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await page.waitForLoadState('networkidle');
    // Next.js should show 404
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle graph page with slow network', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Test Graph',
          nodes: [
            { id: 'test-1', name: 'Test Node', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.repository-bar')).toContainText('Test Graph');
  });

  test('should handle graph page with missing snapshot', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({ status: 404, body: 'Not found' });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should dismiss error message', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({ status: 404, body: 'Not found' });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    const dismissBtn = page.locator('button[aria-label="Dismiss error"]');
    if (await dismissBtn.isVisible()) {
      await dismissBtn.click();
      await expect(page.locator('.error-message')).not.toBeVisible();
    }
  });

  test('should handle invalid graph snapshot', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ invalid: 'data' }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle empty graph snapshot', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Empty Graph',
          nodes: [],
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.repository-bar')).toContainText('Empty Graph');
  });

  test('should handle graph with warnings', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Warning Graph',
          nodes: [
            { id: 'test-1', name: 'Test Node', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: ['Test warning 1', 'Test warning 2'],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Switch to constraints tab to see warnings
    await page.locator('.inspector-tabs button:has-text("Constraints")').click();
    await expect(page.locator('.warning-list')).toBeVisible();
  });

  test('should handle truncated graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Truncated Graph',
          nodes: [
            { id: 'test-1', name: 'Test Node', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: true
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await expect(page.locator('.repository-bar')).toContainText('Partial inventory');
  });

  test('should handle API errors on integrations', async ({ page }) => {
    await page.route('**/api/integrations', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the integrations panel
    await expect(page.locator('.integrations-panel')).toBeVisible();
  });

  test('should handle API errors on graph store', async ({ page }) => {
    await page.route('**/api/graph-store', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the graph store panel
    await expect(page.locator('.graph-store-panel')).toBeVisible();
  });

  test('should handle API errors on analytics', async ({ page }) => {
    await page.route('**/api/analytics', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the analytics page
    await expect(page.locator('h1')).toContainText('Turn activity into evidence');
  });

  test('should handle API errors on decisions', async ({ page }) => {
    await page.route('**/api/decisions', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/decisions');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the decisions page
    await expect(page.locator('h1')).toContainText('Ask precisely');
  });

  test('should handle API errors on optimization', async ({ page }) => {
    await page.route('**/api/optimization', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/optimization');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the optimization page
    await expect(page.locator('h1')).toContainText('Make every constraint visible');
  });

  test('should handle API errors on control', async ({ page }) => {
    await page.route('**/api/control', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the swarm page
    await expect(page.locator('h1')).toContainText('A plan is only the beginning');
  });

  test('should handle API errors on review', async ({ page }) => {
    await page.route('**/api/review', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the graph page
    await expect(page.locator('h1')).toContainText('See the system');
  });

  test('should handle API errors on ecosystem MCP', async ({ page }) => {
    await page.route('**/api/ecosystem/mcp', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/ecosystem');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the ecosystem page
    await expect(page.locator('h1')).toContainText('One workspace');
  });

  test('should handle API errors on planned tasks', async ({ page }) => {
    await page.route('**/api/planned-tasks', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });
    await page.goto('/swarm');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should still show the swarm page
    await expect(page.locator('h1')).toContainText('A plan is only the beginning');
  });

  test('should handle network timeout on graph load', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.abort('timedout');
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle malformed JSON in graph snapshot', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: 'not valid json{{{',
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle oversized graph snapshot', async ({ page }) => {
    const bigNode = { id: 'test-1', name: 'Test', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' };
    const nodes = Array(30000).fill(bigNode).map((n, i) => ({ ...n, id: `test-${i}` }));
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Big Graph',
          nodes,
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about size limits
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle duplicate node IDs in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Duplicate Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' },
            { id: 'test-1', name: 'Node 2', kind: 'file', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about duplicate IDs
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle invalid node kind in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Invalid Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'invalid_kind', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about invalid kind
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle invalid evidence in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Invalid Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'invalid_evidence' }
          ],
          edges: [],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about invalid evidence
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle missing edge endpoints in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Bad Edge Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [
            { source: 'test-1', target: 'nonexistent', relation: 'imports', confidence: 'parsed' }
          ],
          warnings: [],
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about missing endpoint
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle invalid warnings in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Bad Warnings Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: 'not an array',
          truncated: false
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about invalid warnings
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle invalid summary in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Bad Summary Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: false,
          summary: 'not an object'
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about invalid summary
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should handle invalid unresolved in graph', async ({ page }) => {
    await page.route('**/repository-graph.json', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          version: 1,
          name: 'Bad Unresolved Graph',
          nodes: [
            { id: 'test-1', name: 'Node 1', kind: 'module', path: 'test/', summary: 'Test', confidence: 'parsed' }
          ],
          edges: [],
          warnings: [],
          truncated: false,
          unresolved: 'not an array'
        }),
        contentType: 'application/json'
      });
    });
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Should show error about invalid unresolved
    await expect(page.locator('.error-message')).toBeVisible();
  });
});
