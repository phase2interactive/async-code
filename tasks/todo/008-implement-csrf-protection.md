# Task: Implement CSRF Protection

**Priority**: HIGH
**Component**: Frontend & Backend
**Security Impact**: Medium - State-changing operation protection

## Problem
No CSRF protection allows cross-site request forgery attacks on state-changing operations.

## Vulnerable Operations
- Task creation
- Project deletion
- Settings updates
- GitHub token updates

## Required Implementation

### Backend (Flask)
1. **Install Flask-WTF**
   ```bash
   pip install Flask-WTF
   ```

2. **Configure CSRF protection**
   ```python
   from flask_wtf.csrf import CSRFProtect
   
   csrf = CSRFProtect(app)
   app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
   ```

3. **Exempt only safe endpoints**
   ```python
   @csrf.exempt
   @app.route('/health', methods=['GET'])
   ```

### Frontend (Next.js)
1. **Fetch CSRF token**
   ```typescript
   const getCSRFToken = async () => {
     const response = await fetch('/api/csrf-token');
     const data = await response.json();
     return data.csrf_token;
   };
   ```

2. **Include in requests**
   ```typescript
   const response = await fetch('/api/tasks/create', {
     method: 'POST',
     headers: {
       'X-CSRF-Token': csrfToken,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify(data)
   });
   ```

## Implementation Steps
1. Add Flask-WTF to requirements.txt
2. Configure CSRF protection in main.py
3. Create CSRF token endpoint
4. Update frontend API service to fetch and include tokens
5. Handle CSRF errors gracefully
6. Test all state-changing operations

## Acceptance Criteria
- [ ] CSRF protection enabled on all POST/PUT/DELETE endpoints
- [ ] Frontend automatically includes CSRF tokens
- [ ] Clear error messages for CSRF failures
- [ ] No impact on user experience
- [ ] Documentation updated