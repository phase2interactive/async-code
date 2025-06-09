# Task: Add React Error Boundaries

**Priority**: MEDIUM
**Component**: Frontend
**Type**: Error Handling

## Problem
No error boundaries implemented, causing entire app to crash on component errors.

## Required Implementation

### 1. Create Base Error Boundary
```typescript
// components/error-boundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // Send to error tracking service
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <details>
            <summary>Error details</summary>
            <pre>{this.state.error?.message}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 2. Create Specific Error Boundaries
- `TaskErrorBoundary` - For task-related errors
- `ApiErrorBoundary` - For API communication errors
- `RouteErrorBoundary` - For page-level errors

### 3. Implement Error Recovery
```typescript
// Add reset functionality
const resetError = () => {
  this.setState({ hasError: false, error: null });
};
```

### 4. Integration Points
- Wrap main app in global error boundary
- Wrap individual routes
- Wrap complex components (diff viewer, task list)
- Wrap API-dependent sections

## Implementation Steps
1. Create base ErrorBoundary component
2. Create specialized error boundaries
3. Add error logging integration
4. Wrap critical components
5. Create error UI components
6. Add error recovery mechanisms
7. Test with simulated errors

## Error UI Requirements
- User-friendly error messages
- Option to retry failed operations
- Contact support link
- Error ID for tracking

## Acceptance Criteria
- [ ] Global error boundary implemented
- [ ] Route-level error boundaries added
- [ ] Component errors don't crash app
- [ ] Error details logged properly
- [ ] User-friendly error messages
- [ ] Recovery mechanisms work