# Task: Implement API Rate Limiting

**Priority**: HIGH
**Component**: Backend API
**Security Impact**: Medium - DoS prevention

## Problem
No rate limiting allows attackers to spawn unlimited Docker containers and overwhelm the system.

## Requirements

1. **Global Rate Limits**
   - Max 10 task creations per user per hour
   - Max 100 API requests per user per minute
   - Max 5 concurrent running tasks per user

2. **Implementation Options**
   - Flask-Limiter for API endpoints
   - Redis for distributed rate limiting
   - Custom middleware for container limits

3. **Specific Limits**
   - POST /tasks/create: 10 per hour
   - GET endpoints: 100 per minute
   - Container spawning: 5 concurrent max

## Implementation Steps
1. Install Flask-Limiter: `pip install Flask-Limiter`
2. Set up Redis for rate limit storage
3. Add rate limiting decorator to all endpoints
4. Implement custom limiter for container spawning
5. Add rate limit headers to responses
6. Create bypass mechanism for admin users

## Code Example
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-User-ID', get_remote_address()),
    storage_uri="redis://localhost:6379"
)

@app.route('/tasks/create', methods=['POST'])
@limiter.limit("10 per hour")
def create_task():
    # ...
```

## Acceptance Criteria
- [ ] Rate limits enforced on all endpoints
- [ ] Clear error messages when limits exceeded
- [ ] Rate limit headers in responses
- [ ] Container spawning limits enforced
- [ ] Monitoring for rate limit violations