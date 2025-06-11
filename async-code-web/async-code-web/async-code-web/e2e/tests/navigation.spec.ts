import { test, expect } from '../fixtures/test-helpers';

test.describe('Basic Navigation', () => {
  test('should navigate between main pages', async ({ authenticatedPage, page }) => {
    // Start at home
    await expect(page).toHaveURL('/');
    
    // Navigate to Projects
    await authenticatedPage.navigateToProjects();
    await expect(page).toHaveURL('/projects');
    await expect(page.locator('h1')).toContainText('Projects');
    
    // Navigate to Tasks
    await authenticatedPage.navigateToTasks();
    await expect(page).toHaveURL('/tasks');
    await expect(page.locator('h1')).toContainText('Tasks');
    
    // Navigate to Settings
    await authenticatedPage.navigateToSettings();
    await expect(page).toHaveURL('/settings');
    await expect(page.locator('h1')).toContainText('Settings');
    
    // Navigate back to home
    await page.click('a[href="/"]');
    await expect(page).toHaveURL('/');
  });

  test('should work on mobile viewport', async ({ page, authenticatedPage }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Should show mobile menu button
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
    await expect(mobileMenuButton).toBeVisible();
    
    // Open mobile menu
    await mobileMenuButton.click();
    
    // Should show navigation links
    await expect(page.locator('a[href="/projects"]')).toBeVisible();
    await expect(page.locator('a[href="/tasks"]')).toBeVisible();
    await expect(page.locator('a[href="/settings"]')).toBeVisible();
    
    // Navigate to tasks
    await page.click('a[href="/tasks"]');
    await expect(page).toHaveURL('/tasks');
    
    // Mobile menu should close after navigation
    await expect(page.locator('a[href="/projects"]')).not.toBeVisible();
  });

  test('should show loading states during navigation', async ({ page, authenticatedPage }) => {
    // Set up route interception to slow down navigation
    await page.route('**/api/**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
      await route.continue();
    });
    
    // Navigate to tasks
    const tasksLink = page.locator('a[href="/tasks"]');
    await tasksLink.click();
    
    // Should show loading indicator
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    
    // Should eventually show tasks page
    await expect(page).toHaveURL('/tasks', { timeout: 10000 });
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
  });

  test('should handle 404 pages', async ({ page, authenticatedPage }) => {
    // Navigate to non-existent page
    await page.goto('/non-existent-page');
    
    // Should show 404 message
    await expect(page.locator('text=404')).toBeVisible();
    await expect(page.locator('text=Page not found')).toBeVisible();
    
    // Should have link back to home
    const homeLink = page.locator('a[href="/"]');
    await expect(homeLink).toBeVisible();
    
    // Navigate back to home
    await homeLink.click();
    await expect(page).toHaveURL('/');
  });
});