# Test User Management System

## Overview

The Test User Management System provides a secure, isolated environment for running automated tests without affecting production data. It implements all the recommendations from `TEST_USER_RECOMMENDATIONS.md` with a focus on security, isolation, and ease of use.

## Features

### 1. Test User Creation
- Automated test user provisioning via Supabase service role
- Fixed email pattern using `.test` TLD (e.g., `test@asynccode.test`)
- Consistent user IDs for reproducible testing
- JWT token generation for authentication
- 1-hour TTL with automatic cleanup

### 2. Data Isolation
- Row-level security (RLS) policies ensure test data isolation
- Test users marked with `is_test_user=true`
- Test data marked with `is_test_data=true`
- Regular users cannot see test data
- Test users can only create test data

### 3. API Endpoints
All test user endpoints are prefixed with `/api/test-users` and are only available in non-production environments.

#### Create Test User
```bash
POST /api/test-users
{
  "email": "custom@test.test",  # Optional, defaults to test@asynccode.test
  "user_id": "specific-uuid",    # Optional, auto-generated if not provided
  "metadata": {                  # Optional additional metadata
    "test_scenario": "auth_flow"
  }
}

Response:
{
  "user": {
    "id": "uuid",
    "email": "test@asynccode.test",
    "created_at": "2024-01-01T00:00:00Z",
    "metadata": {},
    "expires_at": "2024-01-01T01:00:00Z"
  },
  "tokens": {
    "access_token": "jwt...",
    "refresh_token": "jwt..."
  }
}
```

#### Delete Test User
```bash
DELETE /api/test-users/{user_id}
```

#### List Test Users
```bash
GET /api/test-users
```

#### Cleanup Expired Users
```bash
POST /api/test-users/cleanup
```

#### Refresh Tokens
```bash
POST /api/test-users/{user_id}/token
```

## Configuration

### Environment Variables
```bash
# Required for test user system
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret

# Enable test mode
ENVIRONMENT=test                # or "development"
ENABLE_TEST_USERS=true         # Must be explicitly enabled
```

### Database Setup
Run the migration to add test user support:
```sql
-- Run the migration script
psql $DATABASE_URL < db/add_test_user_support.sql
```

## Usage Examples

### Python Example
```python
from test_user_service import TestUserService

# Initialize service
service = TestUserService()

# Create a test user
test_user = service.create_test_user()
print(f"Created user: {test_user.email}")
print(f"Access token: {test_user.access_token}")

# Use the token for API requests
headers = {"Authorization": f"Bearer {test_user.access_token}"}
response = requests.get("http://localhost:5000/api/tasks", headers=headers)

# Cleanup when done
service.delete_test_user(test_user.id)
```

### Playwright Example
```typescript
// test-helpers.ts
export async function createTestUser() {
  const response = await fetch('http://localhost:5000/api/test-users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  
  const data = await response.json();
  return {
    user: data.user,
    accessToken: data.tokens.access_token,
    refreshToken: data.tokens.refresh_token
  };
}

// auth.test.ts
test('user can login and create task', async ({ page }) => {
  const { user, accessToken } = await createTestUser();
  
  // Set auth token in localStorage
  await page.evaluate((token) => {
    localStorage.setItem('access_token', token);
  }, accessToken);
  
  // Navigate and test
  await page.goto('/tasks');
  // ... test logic
});
```

### Demo Script
```bash
# Run the demo script to see all features
cd server
python demo_test_users.py
```

## Security Considerations

1. **Production Protection**
   - Test user endpoints automatically disabled in production
   - Requires explicit `ENABLE_TEST_USERS=true` flag
   - Environment check prevents accidental activation

2. **Data Isolation**
   - RLS policies enforce strict data separation
   - Test users cannot access production data
   - Production users cannot see test data

3. **Automatic Cleanup**
   - 1-hour TTL on all test users
   - Cascade deletion removes all associated data
   - Cleanup scheduler can be run periodically

4. **Validation**
   - Test emails must use `.test` TLD
   - Service role key required for user creation
   - JWT tokens marked as test tokens

## Testing

Run the test suite:
```bash
cd server
pytest tests/test_test_user_service.py -v
pytest tests/test_test_users_api.py -v
```

## Next Steps

1. **Local Git Repository Factory** (Task #33)
   - Implement file:// URL support
   - Create test repositories in /tmp/test-repos/
   - Add repository seeding functionality

2. **Docker Compose Test Profile** (Task #37)
   - Create docker-compose.test.yml
   - Add isolated test database
   - Configure test-specific environment

3. **Seed Scripts Framework** (Task #35)
   - Create idempotent seed scripts
   - Add test data generators
   - Implement fixture management

4. **Playwright Integration** (Task #38)
   - Update test configuration
   - Add authentication helpers
   - Create page object models

## Troubleshooting

### "Test user endpoints are disabled"
- Ensure `ENVIRONMENT` is not set to "production"
- Set `ENABLE_TEST_USERS=true` in environment

### "Missing required configuration"
- Check all required environment variables are set
- Verify Supabase service role key is correct
- Ensure JWT_SECRET is at least 32 characters

### "Cannot delete non-test user"
- Only users with `is_test_user=true` can be deleted via API
- Use Supabase dashboard for production user management

### Database errors
- Run the migration script to add test user columns
- Check Supabase service role key has proper permissions
- Verify RLS policies are correctly configured