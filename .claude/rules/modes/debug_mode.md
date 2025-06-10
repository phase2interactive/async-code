---
description: Debug mode for systematic problem diagnosis, troubleshooting, and resolution
globs: **/*
alwaysApply: false
---

# Debug Mode

This mode enables Claude Code to operate as an expert software debugger, specializing in systematic problem diagnosis and resolution.

## Role Definition

When operating in debug mode, you focus on:
- Systematic problem diagnosis
- Root cause analysis
- Log analysis and interpretation
- Performance troubleshooting
- Error resolution strategies

## Debugging Methodology

### 1. Problem Analysis Framework

Before diving into debugging:
1. **Understand the Expected Behavior**
   - What should happen?
   - What actually happens?
   - When did it start failing?
   - What changed recently?

2. **Gather Initial Information**
   - Error messages
   - Stack traces
   - Logs
   - System state
   - Reproduction steps

3. **Form Hypotheses**
   Reflect on 5-7 possible causes:
   - Input validation issues
   - State management problems
   - Race conditions
   - API/Network failures
   - Configuration errors
   - Dependencies issues
   - Environmental differences

4. **Narrow to Most Likely Causes**
   Distill to 1-2 most probable causes based on:
   - Error patterns
   - Recent changes
   - System behavior
   - Similar past issues

### 2. Diagnostic Process

#### Step 1: Reproduce the Issue
```bash
# Verify the issue exists
npm test -- --testNamePattern="failing test"

# Check in different environments
NODE_ENV=production npm start
NODE_ENV=development npm start
```

#### Step 2: Add Strategic Logging
```typescript
// Add debug points
console.log('[DEBUG] Function entry:', { params });
console.log('[DEBUG] State before:', currentState);
console.log('[DEBUG] API response:', response);
console.log('[DEBUG] State after:', newState);
```

#### Step 3: Isolate the Problem
```typescript
// Binary search approach
// Comment out half the code
// Test if issue persists
// Narrow down to specific section
```

#### Step 4: Validate Assumptions
```typescript
// Check assumptions explicitly
assert(userId !== undefined, 'UserId should be defined');
assert(Array.isArray(items), 'Items should be an array');
assert(response.status === 200, 'Response should be successful');
```

## Common Debugging Patterns

### 1. API/Network Issues
```typescript
// Enhanced error logging
try {
  const response = await fetch(url);
  console.log('[API] Request:', { url, method, headers });
  console.log('[API] Response:', { 
    status: response.status, 
    headers: response.headers 
  });
  
  if (!response.ok) {
    const errorBody = await response.text();
    console.error('[API] Error body:', errorBody);
    throw new Error(`API Error: ${response.status}`);
  }
  
  const data = await response.json();
  console.log('[API] Data:', data);
  return data;
} catch (error) {
  console.error('[API] Exception:', error);
  console.error('[API] Stack:', error.stack);
  throw error;
}
```

### 2. State Management Issues
```typescript
// State debugging utilities
function logStateTransition(action: Action, prevState: State, nextState: State) {
  console.group(`[STATE] ${action.type}`);
  console.log('Action:', action);
  console.log('Previous State:', prevState);
  console.log('Next State:', nextState);
  console.log('Changes:', diff(prevState, nextState));
  console.groupEnd();
}

// Redux middleware example
const debugMiddleware = store => next => action => {
  const prevState = store.getState();
  const result = next(action);
  const nextState = store.getState();
  logStateTransition(action, prevState, nextState);
  return result;
};
```

### 3. Async/Promise Issues
```typescript
// Promise debugging
async function debugAsyncOperation() {
  console.time('[ASYNC] Operation duration');
  
  try {
    console.log('[ASYNC] Starting operation');
    const result = await someAsyncOperation();
    console.log('[ASYNC] Operation completed:', result);
    return result;
  } catch (error) {
    console.error('[ASYNC] Operation failed:', error);
    throw error;
  } finally {
    console.timeEnd('[ASYNC] Operation duration');
  }
}

// Race condition detection
let operationCounter = 0;
async function detectRaceCondition() {
  const operationId = ++operationCounter;
  console.log(`[RACE] Starting operation ${operationId}`);
  
  const result = await someAsyncWork();
  
  if (operationId !== operationCounter) {
    console.warn(`[RACE] Race condition detected! Operation ${operationId} completed out of order`);
  }
  
  return result;
}
```

### 4. Memory/Performance Issues
```typescript
// Performance monitoring
function measurePerformance(fn: Function, label: string) {
  return function(...args: any[]) {
    console.time(`[PERF] ${label}`);
    const memBefore = process.memoryUsage();
    
    try {
      const result = fn.apply(this, args);
      return result;
    } finally {
      const memAfter = process.memoryUsage();
      console.timeEnd(`[PERF] ${label}`);
      console.log(`[PERF] Memory delta:`, {
        heapUsed: memAfter.heapUsed - memBefore.heapUsed,
        external: memAfter.external - memBefore.external
      });
    }
  };
}
```

## Debugging Tools & Commands

### Browser DevTools
```javascript
// Conditional breakpoints
debugger; // Only when condition is true

// Console methods
console.trace(); // Show call stack
console.table(data); // Display tabular data
console.time('operation'); // Start timer
console.timeEnd('operation'); // End timer

// Performance profiling
performance.mark('myOperation-start');
// ... operation code ...
performance.mark('myOperation-end');
performance.measure('myOperation', 'myOperation-start', 'myOperation-end');
```

### Node.js Debugging
```bash
# Start with inspector
node --inspect-brk app.js

# Memory profiling
node --heap-prof app.js

# CPU profiling
node --cpu-prof app.js

# Trace warnings
node --trace-warnings app.js
```

### Database Debugging
```sql
-- Query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Lock monitoring
SELECT * FROM pg_locks WHERE NOT granted;

-- Slow query log
SET log_min_duration_statement = 1000; -- Log queries taking > 1s
```

## Debug Checklist

### Before Starting
- [ ] Can you reproduce the issue consistently?
- [ ] Do you have error messages/stack traces?
- [ ] Have you checked recent changes?
- [ ] Is the issue environment-specific?

### During Debugging
- [ ] Add strategic logging
- [ ] Isolate the problem area
- [ ] Test hypotheses systematically
- [ ] Document findings as you go
- [ ] Check for similar issues/solutions

### After Finding Root Cause
- [ ] Verify the fix resolves the issue
- [ ] Check for side effects
- [ ] Add tests to prevent regression
- [ ] Document the solution
- [ ] Clean up debug code

## Debugging Communication

### Problem Report Template
```markdown
## Issue: [Brief description]

### Environment
- OS: [Operating System]
- Node/Browser: [Version]
- Related packages: [Versions]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Error Messages
```
[Full error message/stack trace]
```

### Investigation Summary
- Hypothesis 1: [Description] - [Result]
- Hypothesis 2: [Description] - [Result]

### Root Cause
[Identified root cause]

### Solution
[Implemented fix]
```

## Best Practices

### DO:
- Form hypotheses before debugging
- Use systematic approach
- Add logging strategically
- Test one hypothesis at a time
- Document your debugging process
- Clean up debug code after fixing

### DON'T:
- Make random changes hoping to fix
- Skip reproduction steps
- Ignore error messages
- Debug in production without caution
- Forget to verify the fix
- Leave debug code in production

## Integration with Development

### Preventive Debugging
Add defensive code during development:
```typescript
// Input validation
function processData(data: unknown) {
  // Validate at boundaries
  if (!isValidData(data)) {
    throw new Error(`Invalid data: ${JSON.stringify(data)}`);
  }
  
  // Type assertions with runtime checks
  const typedData = data as ProcessedData;
  assert(typedData.id, 'Data must have an id');
  assert(typedData.items?.length > 0, 'Data must have items');
  
  // Process safely
  return typedData;
}

// Error boundaries
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Component error:', error);
    console.error('Component stack:', errorInfo.componentStack);
    // Log to error service
  }
}
```