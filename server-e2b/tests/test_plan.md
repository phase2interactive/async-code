Comprehensive Testing Strategy for E2B Integration

  Phase 1: Immediate Fixes (Today)

  1. Fix Production Code - Add directory creation fallback
  2. Fix Existing Tests - Align test paths with production
  3. Add Regression Test - Specific test for this bug

  Phase 2: Test Environment Parity (This Week)

  1. Create Test Fixtures that mirror production exactly
  2. Use Production Classes in tests (not manual sandbox creation)
  3. Test Multiple Scenarios:
    - With custom template (happy path)
    - Without custom template (fallback)
    - With invalid template ID
    - Permission denied scenarios

  Phase 3: Comprehensive Coverage (Next Sprint)

  1. Environment Matrix Testing:
  - E2B_TEMPLATE_ID=valid → Custom environment
  - E2B_TEMPLATE_ID=invalid → Error handling
  - E2B_TEMPLATE_ID=null → Default environment
  2. Integration Test Suite:
    - End-to-end task execution
    - Git operations (clone, commit, push)
    - File system operations
    - Error recovery scenarios
  3. Mock vs Real Testing:
    - Unit tests with mocked E2B client
    - Integration tests with real sandboxes
    - Contract tests to ensure mocks match reality

  Phase 4: Test Infrastructure (Long-term)

  1. CI/CD Pipeline:
    - Run tests with different E2B configurations
    - Automated sandbox cleanup
    - Performance benchmarks
  2. Monitoring & Alerting:
    - Track sandbox creation failures
    - Monitor permission errors
    - Alert on environment mismatches
  3. Documentation:
    - Test environment setup guide
    - Known issues and workarounds
    - Debugging playbook

  Key Testing Principles

  - Test Like Production: Same paths, same permissions, same environment
  - Fail Fast: Validate environment before operations
  - Clear Errors: Distinguish between app bugs and environment issues
  - Defensive Code: Never assume directories exist