import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class HomePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate() {
    await super.navigate('/');
  }

  async isLoggedIn(): Promise<boolean> {
    // Check if user avatar is visible (indicates logged in state)
    return await this.isVisible('[data-testid="user-avatar"]');
  }

  async signOut() {
    // Click on user avatar to open dropdown
    await this.page.click('[data-testid="user-avatar"]');
    
    // Click sign out
    await this.page.click('text=Sign out');
    
    // Wait for redirect to sign in page
    await this.page.waitForURL('/signin');
  }

  async navigateToProjects() {
    await this.page.click('a[href="/projects"]');
    await this.page.waitForURL('/projects');
  }

  async navigateToTasks() {
    await this.page.click('a[href="/tasks"]');
    await this.page.waitForURL('/tasks');
  }

  async navigateToSettings() {
    await this.page.click('a[href="/settings"]');
    await this.page.waitForURL('/settings');
  }

  async getWelcomeMessage(): Promise<string | null> {
    const welcomeElement = await this.page.locator('h1').first();
    if (await welcomeElement.isVisible()) {
      return await welcomeElement.textContent();
    }
    return null;
  }
}