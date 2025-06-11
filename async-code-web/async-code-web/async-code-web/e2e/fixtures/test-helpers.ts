import { test as base, expect } from '@playwright/test';
import { SignInPage } from '../pages/SignInPage';
import { HomePage } from '../pages/HomePage';
import { TasksPage } from '../pages/TasksPage';
import { SettingsPage } from '../pages/SettingsPage';
import { TestDataSeeder, TestUser, TestProject } from './test-data';

// Define custom fixtures
export const test = base.extend<{
  signInPage: SignInPage;
  homePage: HomePage;
  tasksPage: TasksPage;
  settingsPage: SettingsPage;
  authenticatedPage: HomePage;
  testData: { user: TestUser; project: TestProject };
}>({
  // Page object fixtures
  signInPage: async ({ page }, use) => {
    await use(new SignInPage(page));
  },
  
  homePage: async ({ page }, use) => {
    await use(new HomePage(page));
  },
  
  tasksPage: async ({ page }, use) => {
    await use(new TasksPage(page));
  },
  
  settingsPage: async ({ page }, use) => {
    await use(new SettingsPage(page));
  },
  
  // Test data fixture
  testData: async ({}, use) => {
    // Setup test data before test
    const data = await TestDataSeeder.setupTestEnvironment();
    
    // Use test data in test
    await use(data);
    
    // Cleanup after test
    await TestDataSeeder.teardownTestEnvironment(data.user.id);
  },
  
  // Authenticated page fixture
  authenticatedPage: async ({ page, testData }, use) => {
    // Sign in before test
    const signInPage = new SignInPage(page);
    await signInPage.navigate();
    await signInPage.signIn(testData.user.email, testData.user.password);
    
    // Verify logged in
    const homePage = new HomePage(page);
    await expect(page).toHaveURL('/');
    
    // Use authenticated page
    await use(homePage);
  },
});

export { expect } from '@playwright/test';

// Helper functions
export async function waitForTaskToComplete(page: any, taskId: string, timeout = 300000) {
  await page.waitForFunction(
    (id: string) => {
      const statusElement = document.querySelector(`[data-task-id="${id}"] .task-status`);
      return statusElement?.textContent?.toLowerCase() === 'completed';
    },
    taskId,
    { timeout }
  );
}

export async function mockAPIResponse(page: any, endpoint: string, response: any) {
  await page.route(`**/api/${endpoint}`, (route: any) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

export async function waitForNetworkIdle(page: any, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}