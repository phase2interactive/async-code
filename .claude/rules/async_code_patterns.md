---
description: Project-specific patterns and conventions for the async-code codebase
globs: **/*.{ts,tsx,py,js,jsx}
alwaysApply: true
---

# Async-Code Project Patterns

This file documents specific patterns and conventions unique to the async-code project.

## Architecture Patterns

### Frontend (Next.js)

#### API Service Pattern
```typescript
// lib/api-service.ts pattern
export const apiService = {
  async methodName(params: ParamType): Promise<ReturnType> {
    const response = await fetch(`${API_BASE_URL}/endpoint`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
      body: JSON.stringify(params),
    });
    return response.json();
  }
};
```

#### Supabase Service Pattern
```typescript
// lib/supabase-service.ts pattern
export const supabaseService = {
  async getItems(userId: string) {
    const { data, error } = await supabase
      .from('table_name')
      .select('*')
      .eq('user_id', userId);
    
    if (error) throw error;
    return data;
  }
};
```

#### Component Structure
```typescript
// components/feature-name.tsx
'use client';

import { useState, useEffect } from 'react';
import { ComponentProps } from '@/types';

export function FeatureName({ prop1, prop2 }: ComponentProps) {
  // State and logic
  return (
    <div className="space-y-4">
      {/* Component JSX */}
    </div>
  );
}
```

### Backend (Flask)

#### Route Pattern
```python
# Blueprint-based routes
from flask import Blueprint, request, jsonify
from database import supabase

bp = Blueprint('resource', __name__)

@bp.route('/resource/<id>', methods=['GET'])
def get_resource(id):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Logic here
    return jsonify(result)
```

#### Database Operations
```python
# database.py patterns
def get_user_resources(user_id: str):
    result = supabase.table('resources')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    return result.data
```

#### Task Execution Pattern
```python
# utils/code_task_v2.py patterns
def execute_task(task_id: str, model: str = 'claude'):
    container_name = f"ai-code-task-{task_id}"
    
    # Container setup
    container = docker_client.containers.run(
        image=get_image_for_model(model),
        name=container_name,
        environment=env_vars,
        detach=True
    )
    
    # Execute and monitor
    # Update database with results
```

## Database Patterns

### Supabase Table Structure
```sql
-- Standard fields across tables
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
user_id UUID REFERENCES auth.users(id),
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
```

### Row Level Security
```sql
-- Standard RLS pattern
CREATE POLICY "Users can only see their own data"
ON table_name
FOR ALL
USING (auth.uid() = user_id);
```

## Authentication Pattern

### Frontend Auth Check
```typescript
// Protected route pattern
const user = useAuth();
if (!user) {
  redirect('/signin');
}
```

### Backend Auth Check
```python
# All endpoints check X-User-ID header
user_id = request.headers.get('X-User-ID')
if not user_id:
    return jsonify({'error': 'Unauthorized'}), 401
```

## Task Management Patterns

### Task Status Flow
```
'pending' -> 'running' -> 'completed'|'failed'
```

### Task Result Storage
```python
# Store in JSONB columns
{
    'output': str,
    'exit_code': int,
    'container_id': str,
    'error': str | None,
    'patches': List[Dict],
    'chat_history': List[Dict]
}
```

## Error Handling Patterns

### Frontend
```typescript
try {
  const data = await apiService.method();
  // Handle success
} catch (error) {
  console.error('Error message:', error);
  // Show user-friendly error
}
```

### Backend
```python
try:
    # Operation
    return jsonify(result), 200
except Exception as e:
    return jsonify({'error': str(e)}), 500
```

## Docker Patterns

### Container Naming
```python
container_name = f"ai-code-task-{uuid}"
```

### Container Cleanup
```python
# Auto-cleanup orphaned containers > 2 hours old
for container in docker_client.containers.list(all=True):
    if container.name.startswith('ai-code-task-'):
        # Check age and remove if old
```

## File Organization

### Frontend
```
app/
  - page.tsx           # Route pages
  - layout.tsx         # Layouts
components/
  - ui/               # Reusable UI components
  - feature.tsx       # Feature-specific components
lib/
  - *-service.ts      # Service layers
  - utils.ts          # Utilities
```

### Backend
```
server/
  - main.py           # Flask app entry
  - *.py              # Route modules
  - utils/            # Utility modules
  - database.py       # Database operations
```

## Testing Patterns

### Test File Location
```
# Frontend
__tests__/
  - components/
  - lib/

# Backend
tests/
  - test_*.py
```

### Test Naming
```typescript
// Frontend
describe('ComponentName', () => {
  it('should handle expected behavior', () => {});
  it('should handle edge case', () => {});
  it('should handle error case', () => {});
});
```

```python
# Backend
def test_endpoint_success():
    """Test successful case"""
    
def test_endpoint_error():
    """Test error handling"""
```

## Git Commit Patterns

### Branch Naming
```
feature/description
fix/issue-description
refactor/module-name
```

### Commit Messages
```
feat: add new feature
fix: resolve specific issue
refactor: improve code structure
test: add/update tests
docs: update documentation
```

## Environment Variables

### Required Frontend
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### Required Backend
```
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_KEY
```

## Common Gotchas

1. **CORS**: Backend configured for localhost:3000 and Vercel domains
2. **Auth Headers**: Always include X-User-ID in API requests
3. **Container Names**: Must be unique, use UUIDs
4. **Git Operations**: Require GITHUB_TOKEN in task execution
5. **TypeScript Paths**: Use @ alias for imports from root