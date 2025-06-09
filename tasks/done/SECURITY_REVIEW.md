# Backend API Security and Code Quality Review

## Executive Summary

This review identifies critical security vulnerabilities and code quality issues in the server/ backend API code. Several high-severity vulnerabilities were found that require immediate attention, including command injection risks, privilege escalation in Docker containers, and insufficient authentication mechanisms.

## Critical Security Vulnerabilities

### 1. **Command Injection Vulnerabilities** [CRITICAL]

**Location**: `server/utils/code_task_v2.py`

The code constructs shell commands using user-provided input with inadequate sanitization:

```python
# Line 131: Escaping is insufficient
escaped_prompt = prompt.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

# Line 409: Direct interpolation into shell command
git commit -m "{model_cli.capitalize()}: {escaped_prompt[:100]}"
```

**Risk**: Attackers can inject arbitrary commands. The current escaping is incomplete and doesn't handle:
- Newline characters (`\n`)
- Semicolons (`;`)
- Pipe operators (`|`)
- Command substitution (`$(...)`)
- Other shell metacharacters

**Recommendation**: 
- Use `shlex.quote()` for proper shell escaping
- Avoid shell=True, use subprocess with array arguments
- Consider using Git Python libraries instead of shell commands

### 2. **Excessive Docker Privileges** [CRITICAL]

**Location**: `server/utils/code_task_v2.py` (lines 473-485)

```python
container_kwargs.update({
    'security_opt': [
        'seccomp=unconfined',      # Disables seccomp
        'apparmor=unconfined',     # Disables AppArmor
        'no-new-privileges=false'  # Allows privilege escalation
    ],
    'cap_add': ['ALL'],            # Grants all capabilities
    'privileged': True,            # Full privileged mode
    'pid_mode': 'host'            # Shares host PID namespace
})
```

**Risk**: Containers run with full host privileges, enabling:
- Container escape to host system
- Access to all host processes
- Kernel exploitation
- Complete system compromise

**Recommendation**:
- Remove privileged mode and host PID namespace
- Use minimal required capabilities only
- Keep security profiles enabled
- Run containers with restricted user

### 3. **Weak Authentication** [HIGH]

**Location**: Throughout API endpoints

Authentication relies solely on user-provided `X-User-ID` header without verification:

```python
user_id = request.headers.get('X-User-ID')
if not user_id:
    return jsonify({'error': 'User ID required'}), 400
```

**Risk**: Any user can impersonate another by setting the header. No JWT validation or signature verification.

**Recommendation**:
- Implement proper JWT token validation
- Verify tokens against Supabase Auth
- Add middleware for authentication
- Use Supabase RLS policies

### 4. **GitHub Token Exposure** [HIGH]

**Location**: `server/tasks.py`, `server/utils/code_task_v2.py`

GitHub tokens are:
- Passed through multiple functions
- Stored in environment variables of containers
- Potentially logged in debug output
- Not encrypted at rest

**Risk**: Token leakage could grant repository access.

**Recommendation**:
- Use encrypted token storage
- Implement token rotation
- Minimize token scope
- Audit token usage

### 5. **SQL Injection Potential** [MEDIUM]

**Location**: `server/database.py`

While Supabase client provides some protection, direct query construction exists:

```python
# Line 177: Direct string interpolation in query
result = supabase.table('tasks').select('*').eq('execution_metadata->>legacy_id', legacy_id).execute()
```

**Risk**: If Supabase client doesn't properly escape, SQL injection is possible.

**Recommendation**:
- Use parameterized queries exclusively
- Validate all inputs
- Implement query whitelisting

## Code Quality Issues

### 1. **Excessive File Length**

`server/utils/code_task_v2.py` has 723 lines - violates the 1000-line guideline but is still too long.

**Recommendation**: Split into:
- `container_manager.py` - Docker operations
- `git_manager.py` - Git operations  
- `task_executor.py` - Task execution logic
- `output_parser.py` - Log parsing

### 2. **Lack of Input Validation**

Most endpoints lack comprehensive input validation:
- No regex validation for GitHub URLs
- No prompt length limits
- No branch name validation
- Missing model whitelist enforcement

### 3. **Poor Error Handling**

Generic exception catching without proper categorization:
```python
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return jsonify({'error': str(e)}), 500
```

**Risk**: Information disclosure through error messages.

### 4. **Missing Rate Limiting**

No rate limiting on any endpoints, enabling:
- Resource exhaustion
- DDoS attacks
- Container spawning abuse

### 5. **Insufficient Logging**

Security events not properly logged:
- Failed authentication attempts
- Privilege escalation attempts
- Invalid input attempts
- Token validation failures

## Additional Security Concerns

### 1. **Container Resource Limits**

While memory limits exist (2GB), missing:
- CPU time limits
- Disk I/O limits
- Network bandwidth limits
- Process count limits

### 2. **Secrets Management**

API keys stored as environment variables without:
- Encryption at rest
- Access auditing
- Rotation policies
- Secure injection methods

### 3. **CORS Configuration**

Overly permissive CORS with wildcard subdomain matching:
```python
resources={r"/*": {"origins": ["http://localhost:3000", "https://*.vercel.app"]}}
```

### 4. **Missing Security Headers**

No implementation of:
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security

### 5. **File Operations Security**

No validation on:
- File paths in containers
- File sizes
- File types
- Directory traversal prevention

## Recommendations Priority

### Immediate (P0)
1. Fix command injection vulnerabilities
2. Remove Docker privileged mode
3. Implement proper JWT authentication
4. Add input validation on all endpoints

### Short-term (P1)
1. Implement rate limiting
2. Add security headers
3. Encrypt tokens at rest
4. Improve error handling

### Medium-term (P2)
1. Refactor large files
2. Add comprehensive logging
3. Implement monitoring/alerting
4. Add security testing

## Security Testing Recommendations

1. **Penetration Testing**: Focus on command injection and container escape
2. **Static Analysis**: Run Bandit, Semgrep for Python security issues
3. **Dependency Scanning**: Check for vulnerable dependencies
4. **Container Scanning**: Scan Docker images for vulnerabilities
5. **API Security Testing**: Use OWASP ZAP or similar tools

## Conclusion

The application has several critical security vulnerabilities that could lead to complete system compromise. The use of privileged Docker containers and command injection vulnerabilities are the most severe issues requiring immediate remediation. Additionally, the authentication mechanism needs to be completely redesigned to use proper JWT validation rather than trusting client-provided headers.