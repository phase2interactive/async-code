---
description: Complete TaskMaster command reference and integration guide for Claude Code
globs: **/*
alwaysApply: true
---

# TaskMaster Reference Guide

TaskMaster is an intelligent task management system that helps track work, manage context, and maintain project state across sessions.

## Core Commands

### Task Management

#### Creating Tasks
```bash
# Create a new task
task new "Implement user authentication"
task add "Fix login bug in production"

# Create with priority
task new "Critical: Fix security vulnerability" --priority high

# Create subtask of current task
task subtask "Write unit tests for auth module"
```

#### Task Selection and Navigation
```bash
# List all tasks
task
task list

# Show current task
task current

# Select a task to work on
task select 3
task select "Fix login"  # Partial match

# Navigate task tree
task tree
task parent
task subtasks
```

#### Task Status Management
```bash
# Update task status
task doing      # Mark as in progress
task blocked "Waiting for API documentation"
task complete "Fixed with regex validation"

# Update task details
task update "Fix: Users can't login with special characters"
task priority high
task assign @teammate
```

### Context and Progress Tracking

#### Adding Context
```bash
# Add context notes
task context "Found issue in utils/validation.js:45"
task context "Need to update tests after fix"
task note "Consider refactoring validation module"

# Add code references
task context "Pattern found in src/api/auth.ts:120-135"
```

#### Progress Updates
```bash
# Show progress summary
task progress

# Add specific progress update
task progress "Completed authentication flow, working on tests"

# Expand task with AI assistance
task expand  # AI breaks down task into steps
```

#### Dependencies
```bash
# Add dependencies
task depends "Update API documentation"
task depends "Deploy to staging environment"
task depends 5  # Depend on task #5

# View dependencies
task dependencies
task deps
```

### History and State

#### History Commands
```bash
# View task history
task history
task history --limit 10

# Search history
task search "authentication"
task search "bug fix" --status complete
```

#### State Management
```bash
# Archive completed tasks
task archive
task archive --days 30  # Archive tasks completed 30+ days ago

# State debugging
task debug          # Show raw task state
task reset         # Reset to last saved state
task reset --force # Force reset (caution!)
```

### Advanced Features

#### Bulk Operations
```bash
# Complete multiple subtasks
task complete --all-subtasks "All tests passing"

# Update multiple tasks
task bulk-update --status backlog --tag "v2.0"
```

#### Tags and Filtering
```bash
# Add tags
task tag "security" "high-priority"

# Filter by tags
task list --tag security
task list --status doing --tag "high-priority"
```

#### Time Tracking
```bash
# Start/stop time tracking
task start
task stop

# Add time manually
task time 2h 30m "Implemented core logic"

# View time summary
task time-summary
```

## Integration with Claude Code Workflow

### Starting Work Session
```bash
# Check current state
task
task current

# Resume or start new
task select <number>  # or
task new "New feature"
```

### During Development

#### With TodoWrite/TodoRead
- TaskMaster tracks overall task
- TodoWrite manages execution steps
- Use both for comprehensive tracking

#### With Search Operations
```bash
# After finding relevant code
task context "Key implementation in src/core/auth.ts"
task context "Similar pattern in tests/auth.test.ts"
```

#### With Git Operations
```bash
# Before commit
task context "Ready for commit - all tests passing"

# After PR
task complete "Merged in PR #123"
```

### Task Organization Patterns

#### Feature Development
```bash
task new "Feature: Add OAuth integration"
task expand
# ... work on subtasks
task subtask "Implement Google OAuth"
task subtask "Implement GitHub OAuth"
task subtask "Add OAuth tests"
```

#### Bug Tracking
```bash
task new "Bug: Users lose session on refresh"
task context "Session storage not persisting"
task context "Fixed in middleware/session.ts"
task complete "Fixed with persistent session storage"
```

#### Refactoring
```bash
task new "Refactor: Extract validation module"
task depends "Update all imports"
task depends "Ensure backward compatibility"
task expand
```

## Best Practices

### Task Descriptions
- Use clear, actionable language
- Start with verb: "Add", "Fix", "Update", "Refactor"
- Include enough context to understand later

### Context Management
- Add context as you discover information
- Include file paths and line numbers
- Note decisions and trade-offs

### Task Granularity
- Keep tasks completable in one session
- Use subtasks for larger features
- One task = one PR ideally

### Status Updates
- Move to "doing" when starting work
- Use "blocked" with clear reason
- Complete immediately when done

## Environment Variables

```bash
# Customize TaskMaster behavior
export TASKMASTER_AUTO_SAVE=true
export TASKMASTER_CONTEXT_LIMIT=100
export TASKMASTER_HISTORY_LIMIT=50
```

## Troubleshooting

### Common Issues

#### Lost Current Task
```bash
task history --limit 5
task select <recent-task-number>
```

#### Corrupted State
```bash
task debug > task_backup.json
task reset --force
```

#### Task Not Found
```bash
task search "partial name"
task list --all
```

### Emergency Recovery
```bash
# Export all tasks
task export > tasks_backup.json

# Import tasks
task import tasks_backup.json

# Clear and start fresh
task clear --confirm
```

## Quick Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `task` | `t` | List tasks |
| `task new` | `tn` | Create task |
| `task select` | `ts` | Select task |
| `task current` | `tc` | Show current |
| `task complete` | `td` | Mark done |
| `task context` | `tx` | Add context |
| `task progress` | `tp` | Show/update progress |

## Tips

1. **Always check current task** when starting work
2. **Add context liberally** - it's searchable later
3. **Use expand** for complex tasks to get AI help
4. **Complete promptly** to maintain accurate state
5. **Review task tree** before major commits

Remember: TaskMaster state persists across sessions, making it ideal for long-running projects and interrupted work.