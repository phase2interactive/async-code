# Task: Add XSS Protection

**Priority**: HIGH
**Component**: Frontend
**Security Impact**: Medium - Script injection prevention

## Problem
User-generated content displayed without sanitization, allowing XSS attacks.

## Vulnerable Areas
1. Task prompts display
2. Project descriptions
3. Error messages
4. Chat history display
5. File diff viewer

## Required Implementation

### 1. Install DOMPurify
```bash
cd async-code-web
npm install dompurify @types/dompurify
```

### 2. Create Sanitization Hook
```typescript
// hooks/useSanitize.ts
import DOMPurify from 'dompurify';

export const useSanitize = () => {
  const sanitize = (dirty: string) => {
    return DOMPurify.sanitize(dirty, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'code', 'pre'],
      ALLOWED_ATTR: []
    });
  };
  
  return { sanitize };
};
```

### 3. Update Components
```typescript
// Before
<div>{task.prompt}</div>

// After
<div dangerouslySetInnerHTML={{ __html: sanitize(task.prompt) }} />
```

### 4. Content Security Policy
Add CSP headers to prevent inline scripts:
```typescript
// next.config.ts
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
  }
];
```

## Implementation Steps
1. Install DOMPurify
2. Create sanitization utilities
3. Audit all user content display points
4. Apply sanitization to all user content
5. Implement CSP headers
6. Test with XSS payloads
7. Add XSS prevention tests

## Test Payloads
```javascript
// Test these don't execute
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
```

## Acceptance Criteria
- [ ] All user content sanitized before display
- [ ] CSP headers implemented
- [ ] XSS payloads don't execute
- [ ] Legitimate formatting preserved
- [ ] No impact on performance