# Task: Refactor Large Code Files

**Priority**: MEDIUM
**Component**: Backend - server/utils/code_task_v2.py
**Type**: Code Quality

## Problem
The code_task_v2.py file is 723 lines long, violating modularity principles and making maintenance difficult.

## Current Structure Issues
- Mixed responsibilities (container management, git operations, task execution)
- Duplicate code between claude and codex implementations
- Hard to test individual components
- Difficult to understand flow

## Proposed Refactoring

### 1. Split into modules:
```
utils/
├── task_executor.py          # Main task execution orchestration
├── container_manager.py       # Docker container operations
├── git_manager.py            # Git operations (clone, commit, push)
├── chat_manager.py           # Chat history and prompts
├── file_differ.py            # File change detection and patches
└── agent_runners/
    ├── base.py              # Abstract base class
    ├── claude.py            # Claude-specific implementation
    └── codex.py             # Codex-specific implementation
```

### 2. Create interfaces:
- `TaskExecutor` - Main orchestration class
- `ContainerManager` - Docker operations
- `GitManager` - Git operations
- `AgentRunner` - Abstract base for agents

### 3. Benefits:
- Each module under 200 lines
- Single responsibility principle
- Easier testing
- Better code reuse
- Clearer architecture

## Implementation Steps
1. Create new module structure
2. Extract container management code
3. Extract git operations
4. Create base agent runner class
5. Refactor claude/codex to inherit from base
6. Update imports in main code
7. Add unit tests for each module

## Acceptance Criteria
- [ ] No file exceeds 300 lines
- [ ] Each module has single responsibility
- [ ] All existing functionality preserved
- [ ] Unit tests for each module
- [ ] Clear interfaces between modules