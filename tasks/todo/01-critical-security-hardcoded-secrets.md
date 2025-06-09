# Critical Security Issue: Hardcoded Secrets and Improper Key Management

## Priority: CRITICAL

## Description
The application has several critical security vulnerabilities related to secret management and authentication:

1. **Service Role Key in Frontend**: The database.py file uses `SUPABASE_SERVICE_ROLE_KEY` which has full admin access. This should never be exposed or used in client-facing code.

2. **GitHub Token Storage**: GitHub tokens are stored in plain text in the database (users.github_token field) without encryption.

3. **Missing Environment Variable Validation**: The server doesn't properly validate that all required environment variables are set before starting.

## Impact
- Potential exposure of service role keys could allow attackers full database access
- Exposed GitHub tokens could lead to unauthorized repository access
- API keys could be leaked through logs or error messages

## Steps to Reproduce
1. Check server/database.py line 12 - uses service role key
2. Check db/init_supabase.sql line 13 - github_token stored as plain text
3. Environment variables are logged without masking

## Recommended Fix

### 1. Use Row Level Security (RLS) instead of service role key
```python
# Use anon key for client operations
supabase_key = os.getenv('SUPABASE_ANON_KEY')
```

### 2. Encrypt sensitive data
```sql
-- Add encryption for github_token
github_token_encrypted BYTEA,
github_token_iv BYTEA,
```

### 3. Add proper environment validation
```python
required_env_vars = [
    'SUPABASE_URL',
    'SUPABASE_ANON_KEY',
    'ANTHROPIC_API_KEY'
]

for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

### 4. Use secrets management service
Consider using HashiCorp Vault, AWS Secrets Manager, or similar for production deployments.

## Files Affected
- server/database.py
- db/init_supabase.sql
- server/main.py
- server/utils/code_task_v2.py

## References
- OWASP Top 10: A02:2021 – Cryptographic Failures
- CWE-798: Use of Hard-coded Credentials
- CWE-312: Cleartext Storage of Sensitive Information