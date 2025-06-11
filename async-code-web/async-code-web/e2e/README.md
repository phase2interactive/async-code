# End-to-End Integration Tests

This directory contains Playwright-based end-to-end tests for the async-code application.

## Test Coverage

### Critical Path Tests
1. **Authentication Flow** (`auth.spec.ts`)
   - Sign in with valid credentials
   - Sign out functionality
   - Protected route enforcement
   - Session persistence

2. **Task Creation and Execution** (`tasks.spec.ts`)
   - Create new AI coding tasks
   - Real-time progress monitoring
   - View completed task results
   - Task list management

3. **Settings and GitHub Integration** (`settings.spec.ts`)
   - Configure GitHub token
   - Select default AI model
   - Settings persistence

4. **Navigation** (`navigation.spec.ts`)
   - Main page navigation
   - Mobile responsive testing
   - Loading states
   - 404 handling

## Setup

### Prerequisites
1. Install dependencies:
   ```bash
   cd async-code-web
   npm install
   ```

2. Install Playwright browsers:
   ```bash
   npx playwright install
   ```

3. Configure test environment:
   ```bash
   cp .env.test.example .env.test
   # Edit .env.test with your test configuration
   ```

### Test User Setup
The tests use a dedicated test user account. The test framework will:
- Create a test user if it doesn't exist
- Clean up test data before each test run
- Maintain isolation between test runs

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run tests in UI mode (recommended for development)
```bash
npm run test:e2e:ui
```

### Debug a specific test
```bash
npm run test:e2e:debug -- auth.spec.ts
```

### Generate test code with Codegen
```bash
npm run test:e2e:codegen
```

### View test report
```bash
npm run test:e2e:report
```

## Test Architecture

### Page Object Model
Tests use the Page Object Model pattern for maintainability:
- `pages/` - Page object classes encapsulating UI interactions
- `fixtures/` - Test data and helper utilities
- `tests/` - Actual test specifications

### Test Data Management
- `TestDataSeeder` - Handles test user and project creation
- Database cleanup between tests ensures isolation
- Test data is namespaced to avoid conflicts

### Configuration
- `test.config.ts` - Central configuration for timeouts, URLs, credentials
- `.env.test` - Environment-specific configuration
- `playwright.config.ts` - Playwright test runner configuration

## Writing New Tests

1. Create a new page object if testing a new page:
   ```typescript
   // pages/NewPage.ts
   export class NewPage extends BasePage {
     async doSomething() {
       // Page-specific actions
     }
   }
   ```

2. Write test specifications:
   ```typescript
   // tests/feature.spec.ts
   import { test, expect } from '../fixtures/test-helpers';
   
   test('should do something', async ({ page, authenticatedPage }) => {
     // Test implementation
   });
   ```

3. Use fixtures for common setup:
   - `authenticatedPage` - Pre-authenticated page
   - `testData` - Test user and project data
   - Page objects - Injected page object instances

## CI/CD Integration

For CI environments:
1. Set `CI=true` environment variable
2. Configure headless execution
3. Use single worker to avoid flakiness
4. Enable test retries

Example GitHub Actions:
```yaml
- name: Run E2E tests
  env:
    CI: true
  run: |
    npm run test:e2e
```

## Troubleshooting

### Tests failing locally
1. Ensure services are running:
   ```bash
   docker-compose up
   npm run dev
   ```

2. Check test user exists in database
3. Verify environment variables in `.env.test`

### Flaky tests
1. Increase timeouts in `test.config.ts`
2. Add explicit waits for network requests
3. Use `waitForLoadState('networkidle')`

### Visual debugging
1. Use `--debug` flag to step through tests
2. Take screenshots: `await page.screenshot({ path: 'debug.png' })`
3. Use Playwright Inspector UI mode