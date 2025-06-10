---
description: Implementation mode for focused code development and feature building
globs: **/*
alwaysApply: false
---

# Implementation Mode (Code Pattern)

This mode enables Claude Code to focus exclusively on implementing features, writing code, and building functionality based on specifications.

## Role Definition

When operating in implementation mode, you focus on:
- Writing clean, efficient code
- Following established patterns
- Implementing features to specification
- Maintaining code quality
- Ensuring proper testing

## Core Principles

### 1. Specification-Driven Development
- Follow provided specifications exactly
- Don't expand scope beyond requirements
- Ask for clarification if specs are unclear
- Document assumptions when necessary

### 2. Code Quality Standards
- Write readable, maintainable code
- Follow project conventions
- Use meaningful variable names
- Add comments for complex logic
- Ensure proper error handling

### 3. Pattern Consistency
- Study existing code patterns
- Maintain consistency with codebase
- Use established libraries and utilities
- Follow file organization standards

## Implementation Workflow

### 1. Understand the Task
```bash
# Review specifications
cat tasks/task-001.md

# Check existing patterns
grep -r "similar_pattern" src/

# Review related code
Read relevant implementation files
```

### 2. Plan Implementation
- Break down into logical steps
- Identify required components
- Plan file structure
- Consider dependencies

### 3. Write Code
- Implement incrementally
- Test as you go
- Commit logical chunks
- Maintain clean history

### 4. Verify Implementation
```bash
# Run tests
npm test

# Check linting
npm run lint

# Verify types
npm run typecheck
```

## Code Patterns by Language

### TypeScript/React
```typescript
// Component Pattern
import { useState, useEffect } from 'react';
import { ComponentProps } from '@/types';

export function FeatureComponent({ prop1, prop2 }: ComponentProps) {
  const [state, setState] = useState<StateType>(initialState);
  
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  const handleAction = async () => {
    try {
      // Implementation
    } catch (error) {
      // Error handling
    }
  };
  
  return (
    <div className="component-class">
      {/* JSX */}
    </div>
  );
}
```

### Python/Flask
```python
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from database import db

bp = Blueprint('feature', __name__)

@bp.route('/api/feature', methods=['POST'])
def create_feature() -> tuple[Dict[str, Any], int]:
    """Create a new feature."""
    try:
        data = request.get_json()
        # Validation
        if not data.get('required_field'):
            return jsonify({'error': 'Missing required field'}), 400
        
        # Implementation
        result = process_feature(data)
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### API Implementation
```typescript
// Service Layer Pattern
export const featureService = {
  async create(data: CreateFeatureDto): Promise<Feature> {
    const response = await fetch('/api/features', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': getUserId(),
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create feature: ${response.statusText}`);
    }
    
    return response.json();
  },
  
  async list(filters?: FeatureFilters): Promise<Feature[]> {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/features?${params}`);
    
    if (!response.ok) {
      throw new Error(`Failed to list features: ${response.statusText}`);
    }
    
    return response.json();
  }
};
```

## Testing Patterns

### Unit Tests
```typescript
describe('FeatureComponent', () => {
  it('should render with required props', () => {
    const { getByText } = render(
      <FeatureComponent prop1="value1" prop2="value2" />
    );
    expect(getByText('Expected Text')).toBeInTheDocument();
  });
  
  it('should handle user interaction', async () => {
    const { getByRole } = render(<FeatureComponent />);
    const button = getByRole('button');
    
    await userEvent.click(button);
    
    expect(mockFunction).toHaveBeenCalled();
  });
});
```

### Integration Tests
```python
def test_create_feature(client, auth_headers):
    """Test creating a new feature."""
    response = client.post(
        '/api/features',
        json={'name': 'Test Feature', 'description': 'Test'},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json['name'] == 'Test Feature'
```

## Implementation Checklist

Before starting:
- [ ] Understand requirements fully
- [ ] Review existing patterns
- [ ] Plan implementation approach
- [ ] Set up development environment

During implementation:
- [ ] Follow coding standards
- [ ] Write clean, readable code
- [ ] Handle errors appropriately
- [ ] Add necessary logging
- [ ] Update types/interfaces

After implementation:
- [ ] Run all tests
- [ ] Fix linting issues
- [ ] Update documentation
- [ ] Verify functionality
- [ ] Clean up code

## Common Implementation Tasks

### 1. CRUD Operations
```typescript
// Create
async function createResource(data: CreateDto): Promise<Resource> {
  // Validate input
  // Save to database
  // Return created resource
}

// Read
async function getResource(id: string): Promise<Resource | null> {
  // Fetch from database
  // Handle not found
  // Return resource
}

// Update
async function updateResource(id: string, data: UpdateDto): Promise<Resource> {
  // Validate input
  // Check existence
  // Update database
  // Return updated resource
}

// Delete
async function deleteResource(id: string): Promise<void> {
  // Check existence
  // Delete from database
  // Handle cascading deletes
}
```

### 2. Form Handling
```typescript
function FormComponent() {
  const [formData, setFormData] = useState(initialData);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const validated = validateForm(formData);
      const result = await api.submit(validated);
      // Handle success
    } catch (error) {
      setErrors(error.validationErrors || {});
      // Handle error
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
}
```

### 3. State Management
```typescript
// Context Pattern
const FeatureContext = createContext<FeatureContextType | null>(null);

export function FeatureProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(featureReducer, initialState);
  
  const value = useMemo(
    () => ({ state, dispatch }),
    [state]
  );
  
  return (
    <FeatureContext.Provider value={value}>
      {children}
    </FeatureContext.Provider>
  );
}

export function useFeature() {
  const context = useContext(FeatureContext);
  if (!context) {
    throw new Error('useFeature must be used within FeatureProvider');
  }
  return context;
}
```

## Best Practices

### DO:
- Write self-documenting code
- Handle edge cases
- Validate inputs
- Log important operations
- Follow DRY principles
- Write testable code

### DON'T:
- Over-optimize prematurely
- Skip error handling
- Ignore existing patterns
- Write overly complex solutions
- Forget about maintenance

## Completion Criteria

Implementation is complete when:
- All requirements are met
- Code follows project standards
- Tests are passing
- Documentation is updated
- Code review feedback is addressed
- Feature works as expected