import { chromium, FullConfig } from '@playwright/test';
import { TestDataSeeder } from '../fixtures/test-data';

async function globalSetup(config: FullConfig) {
  console.log('Running global setup...');
  
  // Ensure test database is ready
  try {
    // Create a test user that will be reused across tests
    const testUser = await TestDataSeeder.ensureTestUser();
    console.log('Test user ready:', testUser.email);
    
    // Store test user ID in environment for cleanup
    process.env.TEST_USER_ID = testUser.id;
  } catch (error) {
    console.error('Failed to setup test environment:', error);
    throw error;
  }
  
  console.log('Global setup complete');
}

export default globalSetup;