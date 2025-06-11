import { test, expect } from '../fixtures/test-helpers';
import { testConfig } from '../config/test.config';

test.describe('Authentication Flow', () => {
  test('should show sign in page for unauthenticated users', async ({ page, signInPage }) => {
    // Navigate to home page
    await page.goto('/');
    
    // Should redirect to sign in
    await expect(page).toHaveURL('/signin');
    
    // Should show sign in form
    expect(await signInPage.isSignInFormVisible()).toBeTruthy();
  });

  test('should sign in with valid credentials', async ({ page, signInPage, testData }) => {
    // Navigate to sign in page
    await signInPage.navigate();
    
    // Sign in
    await signInPage.signIn(testData.user.email, testData.user.password);
    
    // Should redirect to home page
    await expect(page).toHaveURL('/');
    
    // Should show user is logged in
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ signInPage }) => {
    // Navigate to sign in page
    await signInPage.navigate();
    
    // Try to sign in with invalid credentials
    await signInPage.signIn('invalid@example.com', 'wrongpassword');
    
    // Should show error message
    const errorMessage = await signInPage.getErrorMessage();
    expect(errorMessage).toBeTruthy();
    expect(errorMessage).toContain('Invalid');
  });

  test('should sign out successfully', async ({ authenticatedPage }) => {
    // User is already signed in via fixture
    
    // Sign out
    await authenticatedPage.signOut();
    
    // Should redirect to sign in page
    await expect(authenticatedPage.page).toHaveURL('/signin');
  });

  test('should protect authenticated routes', async ({ page }) => {
    // Try to access protected routes without authentication
    const protectedRoutes = ['/tasks', '/projects', '/settings'];
    
    for (const route of protectedRoutes) {
      await page.goto(route);
      // Should redirect to sign in
      await expect(page).toHaveURL('/signin');
    }
  });

  test('should persist authentication across page refreshes', async ({ page, signInPage, testData }) => {
    // Sign in
    await signInPage.navigate();
    await signInPage.signIn(testData.user.email, testData.user.password);
    
    // Should be on home page
    await expect(page).toHaveURL('/');
    
    // Refresh page
    await page.reload();
    
    // Should still be authenticated
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });
});