import { test, expect } from '../fixtures/test-helpers';
import { testConfig } from '../config/test.config';

test.describe('Settings and GitHub Integration', () => {
  test('should set GitHub token', async ({ authenticatedPage, settingsPage }) => {
    // Navigate to settings
    await settingsPage.navigate();
    
    // Set GitHub token
    await settingsPage.setGitHubToken(testConfig.github.token);
    
    // Verify token is set
    const tokenStatus = await settingsPage.getGitHubTokenStatus();
    expect(tokenStatus).toBeTruthy();
  });

  test('should select default AI model', async ({ authenticatedPage, settingsPage }) => {
    // Navigate to settings
    await settingsPage.navigate();
    
    // Select Claude model
    await settingsPage.selectDefaultModel('claude');
    
    // Verify model is selected
    const selectedModel = await settingsPage.getSelectedModel();
    expect(selectedModel).toBe('claude');
    
    // Change to different model
    await settingsPage.selectDefaultModel('codex');
    
    // Verify change
    const updatedModel = await settingsPage.getSelectedModel();
    expect(updatedModel).toBe('codex');
  });

  test('should persist settings across sessions', async ({ page, authenticatedPage, settingsPage }) => {
    // Navigate to settings
    await settingsPage.navigate();
    
    // Set GitHub token and model
    await settingsPage.setGitHubToken(testConfig.github.token);
    await settingsPage.selectDefaultModel('claude');
    
    // Refresh page
    await page.reload();
    
    // Verify settings are persisted
    const tokenStatus = await settingsPage.getGitHubTokenStatus();
    expect(tokenStatus).toBeTruthy();
    
    const selectedModel = await settingsPage.getSelectedModel();
    expect(selectedModel).toBe('claude');
  });

  test('should validate GitHub token format', async ({ authenticatedPage, settingsPage }) => {
    // Navigate to settings
    await settingsPage.navigate();
    
    // Try to set invalid token
    await settingsPage.page.fill('input[name="github_token"]', 'invalid-token');
    await settingsPage.clickButton('Save Settings');
    
    // Should show validation error
    await expect(settingsPage.page.locator('text=Invalid GitHub token format')).toBeVisible();
  });
});