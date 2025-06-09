# Task: Add Comprehensive Input Validation

**Priority**: HIGH
**Component**: Backend API
**Security Impact**: Medium - Multiple vulnerabilities

## Problem
No input validation allows malformed data, injection attacks, and system abuse.

## Required Validations

### 1. Repository URLs
- Must be valid GitHub/GitLab URLs
- Validate format: `https://github.com/owner/repo`
- Prevent local file paths
- Limit to allowed domains

### 2. Branch Names
- Must match git branch naming rules
- No special characters that could break git
- Length limits (max 255 chars)

### 3. Task Prompts
- Maximum length (e.g., 10,000 chars)
- No null bytes or control characters
- UTF-8 validation

### 4. User IDs
- Must be valid UUIDs
- Must match authenticated user

## Implementation Steps
1. Create validation schemas using Pydantic
2. Add validation middleware
3. Implement specific validators for each input type
4. Add clear error messages
5. Unit test all validators

## Code Example
```python
from pydantic import BaseModel, validator, HttpUrl
import re

class CreateTaskRequest(BaseModel):
    repo_url: HttpUrl
    branch: str
    prompt: str
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        if not re.match(r'https://github\.com/[\w-]+/[\w-]+', str(v)):
            raise ValueError('Invalid GitHub repository URL')
        return v
    
    @validator('branch')
    def validate_branch(cls, v):
        if not re.match(r'^[\w\-\.]+$', v):
            raise ValueError('Invalid branch name')
        return v
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if len(v) > 10000:
            raise ValueError('Prompt too long')
        return v
```

## Acceptance Criteria
- [ ] All API inputs validated
- [ ] Clear error messages for validation failures
- [ ] Injection attacks prevented
- [ ] Length limits enforced
- [ ] Special characters handled safely