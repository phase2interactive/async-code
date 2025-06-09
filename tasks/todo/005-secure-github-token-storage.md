# Task: Secure GitHub Token Storage

**Priority**: HIGH
**Component**: Frontend & Backend
**Security Impact**: Medium - Credential theft

## Problem
GitHub tokens are stored insecurely and passed in plaintext, risking exposure.

## Current Issues
1. Frontend stores tokens in localStorage (XSS vulnerable)
2. Tokens passed in request bodies (logged)
3. Tokens stored in container environment variables
4. No encryption at rest in database

## Required Changes

### Frontend
1. **Remove localStorage usage**
   - Store tokens in httpOnly cookies
   - Or use secure server-side session storage

2. **Implement token encryption**
   - Encrypt tokens before sending to backend
   - Use Web Crypto API for client-side encryption

### Backend
1. **Encrypt tokens in database**
   - Use Supabase vault or custom encryption
   - Never log tokens
   - Encrypt before storing in container env

2. **Token rotation**
   - Support token expiration
   - Implement refresh mechanism

## Implementation Steps
1. Set up Supabase Vault for token encryption
2. Modify frontend to remove localStorage usage
3. Implement secure token transmission
4. Update database schema for encrypted storage
5. Add token masking in logs
6. Implement token rotation mechanism

## Code Example
```python
# Backend token encryption
from cryptography.fernet import Fernet

def encrypt_token(token: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.decrypt(encrypted.encode()).decode()
```

## Acceptance Criteria
- [ ] Tokens never stored in plaintext
- [ ] Tokens not visible in logs
- [ ] XSS attacks cannot steal tokens
- [ ] Token rotation implemented
- [ ] Secure key management for encryption