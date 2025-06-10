# Claude Code Operation Modes

This directory contains specialized operation modes for Claude Code, adapted from Roo's multi-agent patterns. Each mode provides focused expertise for specific types of tasks.

## Available Modes

### 1. **Orchestrator Mode** (`orchestrator_mode.md`)
Strategic workflow coordination and task decomposition.
- Breaks down complex tasks into manageable subtasks
- Manages dependencies and progress tracking
- Synthesizes results from multiple approaches

### 2. **Architect Mode** (`architect_mode.md`)
Technical analysis, system design, and planning.
- Analyzes requirements and constraints
- Creates system architecture diagrams
- Plans implementation strategies
- Documents technical decisions

### 3. **Implementation Mode** (`implementation_mode.md`)
Focused code development and feature building.
- Writes clean, efficient code
- Follows established patterns
- Implements features to specification
- Maintains code quality

### 4. **Research Mode** (`research_mode.md`)
Technical research, analysis, and explanation.
- Researches best practices
- Analyzes code and systems
- Explains complex concepts
- Provides actionable insights

### 5. **Debug Mode** (`debug_mode.md`)
Systematic problem diagnosis and resolution.
- Diagnoses issues methodically
- Performs root cause analysis
- Implements fixes
- Validates solutions

### 6. **Test Mode** (`test_mode.md`)
Test planning, implementation, and quality assurance.
- Develops test strategies
- Writes comprehensive tests
- Executes test plans
- Reports test results

## Mode Selection Guide

Choose the appropriate mode based on the task:

| Task Type | Recommended Mode |
|-----------|-----------------|
| Complex project planning | Orchestrator |
| System design | Architect |
| Feature implementation | Implementation |
| Technical questions | Research |
| Bug fixing | Debug |
| Quality assurance | Test |

## Using Modes

### Activation
Modes are not automatically applied. Activate them when needed by:
1. Identifying the task type
2. Selecting the appropriate mode
3. Following the mode's specific guidelines

### Mode Switching
When a task requires multiple perspectives:
1. Start with Orchestrator mode for complex tasks
2. Switch to specialized modes for specific subtasks
3. Return to Orchestrator to synthesize results

### Integration with Claude Code

These modes complement Claude Code's core functionality:
- Use alongside TodoWrite/TodoRead for task tracking
- Leverage Task Master for project management
- Apply mode-specific patterns and best practices
- Maintain Claude Code's conciseness principles

## Best Practices

1. **Start Simple**: Don't use modes for straightforward tasks
2. **Stay Focused**: One mode at a time for clarity
3. **Document Transitions**: Note when switching modes
4. **Maintain Context**: Pass relevant information between modes
5. **Complete Cycles**: Finish mode-specific work before switching

## Examples

### Complex Feature Development
```
1. Orchestrator: Break down "Add payment processing"
2. Architect: Design payment system architecture
3. Implementation: Build payment components
4. Test: Create payment test suite
5. Debug: Fix integration issues
6. Orchestrator: Synthesize and complete
```

### Performance Optimization
```
1. Research: Investigate performance best practices
2. Debug: Profile and identify bottlenecks
3. Architect: Design optimization strategy
4. Implementation: Apply optimizations
5. Test: Verify improvements
```