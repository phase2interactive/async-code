# Broken Tests Task List

## Overview
There are currently 21 failing async tests that need to be fixed. The tests are now running with the anyio framework, but they have various implementation issues.

## Categories of Failures

### 1. Tests Calling Non-Existent `_create_e2b_sandbox` Method
These tests are trying to call a method that doesn't exist in the E2BCodeExecutor class.

**Files:** `test_e2b_sandbox_scenarios.py`
- [ ] test_template_fallback_on_error
- [ ] test_quota_exceeded_handling  
- [ ] test_clone_timeout_handling
- [ ] test_permission_error_with_sudo_fallback
- [ ] test_claude_agent_fallback_on_sdk_error

**Fix:** Update tests to use the actual `execute_task` method with proper mocking of database operations.

### 2. Tests Making Real Database Calls
These tests are failing because they're trying to connect to the real Supabase database.

**Files:** `test_e2b_sandbox_scenarios.py`
- [ ] test_private_repo_with_github_token
- [ ] test_large_command_output_truncation
- [ ] test_concurrent_sandbox_isolation
- [ ] test_sandbox_cleanup_on_exception
- [ ] test_binary_file_operations
- [ ] test_non_existent_branch_handling

**Fix:** Add proper mocking for `utils.code_task_e2b_real.DatabaseOperations` in each test.

### 3. Tests with Incorrect Sandbox Mock Path
These tests have the wrong patch path for the E2B Sandbox class.

**Files:** `test_e2b_template_matrix.py`
- [ ] test_template_configuration[test_case0]
- [ ] test_template_configuration[test_case1]
- [ ] test_template_configuration[test_case2]
- [ ] test_template_configuration[test_case3]
- [ ] test_template_configuration[test_case4]
- [ ] test_template_configuration[test_case5]
- [ ] test_template_configuration[test_case6]
- [ ] test_template_configuration[test_case7]

**Fix:** Change patch from `'e2b.Sandbox'` to `'utils.code_task_e2b_real.Sandbox'`

### 4. Tests with Multiple Issues
These tests have both database mocking issues and other problems.

**Files:** `test_e2b_template_matrix.py`
- [ ] test_template_agent_compatibility - Database mock issues + task_id type mismatch (string vs bigint)
- [ ] test_template_performance_characteristics - Calling non-existent `_create_e2b_sandbox` method

**Fix:** 
- Add database mocking
- Fix task_id to be an integer instead of string
- Update to use proper methods

## Summary Statistics
- Total failing tests: 21
- Tests in `test_e2b_sandbox_scenarios.py`: 11
- Tests in `test_e2b_template_matrix.py`: 10
- Root causes: 4 main categories

## Recommended Approach
1. Start with fixing the mock paths (easiest fix)
2. Add database mocking to prevent real DB calls
3. Update tests calling non-existent methods to use the actual API
4. Fix type mismatches

## Time Estimate
- Mock path fixes: ~15 minutes
- Database mocking: ~30 minutes  
- Method updates: ~45 minutes
- Total: ~1.5 hours