export const testConfig = {
  // Test user credentials
  testUser: {
    email: process.env.TEST_USER_EMAIL || 'test@example.com',
    password: process.env.TEST_USER_PASSWORD || 'testpassword123',
  },
  
  // GitHub integration
  github: {
    token: process.env.TEST_GITHUB_TOKEN || 'test-github-token',
    testRepo: process.env.TEST_GITHUB_REPO || 'test-user/test-repo',
  },
  
  // Timeouts
  timeouts: {
    navigation: 30000,
    taskCreation: 60000,
    taskCompletion: 300000, // 5 minutes for AI task completion
  },
  
  // API endpoints
  api: {
    baseUrl: process.env.API_BASE_URL || 'http://localhost:5000',
  },
  
  // Supabase test configuration
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  },
};