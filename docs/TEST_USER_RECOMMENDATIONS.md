# Test User System Recommendations

## Quick Summary

After testing the JWT authentication system with Playwright, here are the key recommendations for implementing a test user system:

### 🚀 Recommended Approach

1. **Use Local Git Repositories**
   - Sidestep GitHub entirely for tests
   - Create repos in `/tmp/test-repos/`
   - Use `file://` URLs instead of `https://github.com/`
   - Full control over test data without external dependencies

2. **Implement Seed Scripts**
   - Create test users via Supabase service role key
   - Generate consistent test data
   - Initialize sample Git repositories
   - Make it idempotent and fast

3. **Test User Specifications**
   - Email: `test@asynccode.test` (use .test TLD)
   - Fixed user ID for consistency
   - Limited permissions (own data only)
   - Auto-cleanup after 1 hour

4. **Docker Compose Test Profile**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.test.yml up
   ```

### ❌ What NOT to Do

1. **Don't use real GitHub tokens** - Rate limits and security risks
2. **Don't use production Supabase** - Use local Supabase or test instance
3. **Don't mix test and production data** - Complete isolation
4. **Don't skip cleanup** - Always clean up, even on test failure

### 🔧 Implementation Priority

1. **Phase 1**: Test user creation service (1-2 days)
2. **Phase 2**: Local Git repository system (1 day)
3. **Phase 3**: Seed scripts and fixtures (1 day)
4. **Phase 4**: Playwright integration (1-2 days)
5. **Phase 5**: CI/CD updates (1 day)

### 🛡️ Security Best Practices

- Store test credentials in `.env.test` (gitignored)
- Use time-limited test data
- Implement automatic cleanup
- Never use production credentials
- Validate test mode before operations

### 📝 Key Design Decisions

1. **Why local Git repos?**
   - No GitHub API limits
   - No security concerns
   - Full control over test scenarios
   - Faster test execution

2. **Why seed scripts?**
   - Reproducible test environment
   - Easy onboarding for developers
   - Consistent test data
   - Version-controlled test scenarios

3. **Why service role key?**
   - Bypass email verification
   - Programmatic user creation
   - Full control over test users
   - No manual setup required

### 🚦 Success Metrics

- Test setup time < 30 seconds
- Zero manual steps required
- 100% cleanup success rate
- No flaky tests due to external dependencies
- New developer can run tests in < 5 minutes

## Example Commands

```bash
# Run tests with test profile
./scripts/run-tests.sh

# Seed test data manually
python scripts/seed_test_data.py

# Clean up test data
python scripts/cleanup_test_data.py

# Run specific Playwright test
npm run test:e2e -- --grep "authentication"
```

## Next Steps

1. Review and approve the approach
2. Create test user service
3. Implement local Git system
4. Write comprehensive seed scripts
5. Update Playwright configuration
6. Document for team