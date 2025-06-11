import { FullConfig } from '@playwright/test';
import { TestDataSeeder } from '../fixtures/test-data';

async function globalTeardown(config: FullConfig) {
  console.log('Running global teardown...');
  
  // Clean up test data
  const testUserId = process.env.TEST_USER_ID;
  if (testUserId) {
    try {
      await TestDataSeeder.cleanupTestData(testUserId);
      console.log('Test data cleaned up');
    } catch (error) {
      console.error('Failed to cleanup test data:', error);
    }
  }
  
  console.log('Global teardown complete');
}

export default globalTeardown;