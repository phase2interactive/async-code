import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate() {
    await super.navigate('/settings');
  }

  async setGitHubToken(token: string) {
    // Fill GitHub token input
    await this.page.fill('input[name="github_token"]', token);
    
    // Save settings
    await this.clickButton('Save Settings');
    
    // Wait for success message
    await this.page.waitForSelector('text=Settings saved successfully', { timeout: 5000 });
  }

  async getGitHubTokenStatus(): Promise<boolean> {
    // Check if token is set (usually shown as masked or status indicator)
    const tokenStatus = await this.page.locator('.github-token-status').first();
    if (await tokenStatus.isVisible()) {
      const text = await tokenStatus.textContent();
      return text?.includes('configured') || text?.includes('set') || false;
    }
    return false;
  }

  async selectDefaultModel(model: string) {
    await this.page.selectOption('select[name="default_model"]', model);
    await this.clickButton('Save Settings');
    await this.page.waitForSelector('text=Settings saved successfully', { timeout: 5000 });
  }

  async getSelectedModel(): Promise<string | null> {
    const selectElement = await this.page.locator('select[name="default_model"]');
    return await selectElement.inputValue();
  }
}