# Visual Regression Testing

This directory contains visual regression tests for the ApexGraphSwarm web application.

## Overview

Visual regression tests capture screenshots of all pages and compare them against baselines to detect UI changes.

## Structure

```
tests/visual-regression/
├── README.md           # This file
├── baselines/          # Baseline screenshots (golden images)
├── actual/             # Actual screenshots from test runs
├── diff/               # Diff images showing differences
└── report/             # HTML test report
```

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   cd apps/web
   npm install
   npx playwright install chromium
   ```

2. Start the development server:
   ```bash
   cd apps/web
   npm run dev
   ```

### Run Tests

```bash
# From apps/web directory
cd apps/web

# Run visual regression tests
npm run test:visual

# Update baselines (after intentional UI changes)
npm run test:visual:update
```

Or using Playwright directly:

```bash
npx playwright test tests/visual-regression/pages.spec.ts
```

## Test Configuration

Tests are configured in `apps/web/playwright.config.ts`:

- **Base URL**: http://127.0.0.1:3010
- **Browser**: Chromium
- **Viewport**: Desktop (1280x720)
- **Threshold**: 1% pixel difference allowed

## Pages Covered

- Home (`/`)
- Analytics (`/analytics`)
- Arena (`/arena`)
- Decisions (`/decisions`)
- Delegation (`/delegation`)
- Ecosystem (`/ecosystem`)
- Ecosystem Research (`/ecosystem/research`)
- Evaluations (`/evaluations`)
- Graph (`/graph`)
- Graph Enhanced (`/graph-enhanced`)
- Optimization (`/optimization`)
- Presentations (`/presentations`)
- Swarm (`/swarm`)
- Teams (`/teams`)

## Updating Baselines

When you make intentional UI changes:

1. Run the update script:
   ```bash
   cd apps/web
   npm run test:visual:update
   ```

2. Review the changes in `tests/visual-regression/baselines/`

3. Commit the updated baselines

## CI Integration

Add to your CI pipeline:

```yaml
- name: Run visual regression tests
  run: |
    cd apps/web
    npm install
    npx playwright install chromium
    npm run dev &
    sleep 10
    npm run test:visual
```

## Troubleshooting

### Tests fail with "No tests found"

Make sure you're running from the `apps/web` directory.

### Screenshots differ slightly

The tests allow 1% pixel difference to account for:
- Font rendering differences
- Animation timing
- Anti-aliasing

If differences are too strict, adjust the threshold in `pages.spec.ts`.

### Browser not found

Run `npx playwright install chromium` to install the browser.
