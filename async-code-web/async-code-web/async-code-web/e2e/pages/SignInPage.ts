import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class SignInPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate() {
    await super.navigate('/signin');
  }

  async signIn(email: string, password: string) {
    // Fill in email
    await this.page.fill('input[type="email"]', email);
    
    // Fill in password
    await this.page.fill('input[type="password"]', password);
    
    // Click sign in button
    await this.page.click('button:has-text("Sign in")');
    
    // Wait for navigation
    await this.page.waitForURL('/', { timeout: 30000 });
  }

  async isSignInFormVisible(): Promise<boolean> {
    return await this.isVisible('input[type="email"]') && 
           await this.isVisible('input[type="password"]');
  }

  async getErrorMessage(): Promise<string | null> {
    const errorElement = await this.page.locator('.text-red-500').first();
    if (await errorElement.isVisible()) {
      return await errorElement.textContent();
    }
    return null;
  }
}