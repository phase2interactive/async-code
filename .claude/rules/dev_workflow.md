---
description: Development workflow best practices using TaskMaster for Claude Code
globs: **/*
alwaysApply: true
---

# Development Workflow with TaskMaster

This guide outlines the standard workflow when working on tasks with Claude Code.

## Task Initialization

When starting any development work:

1. **Check Context Files**
   ```bash
   # Read project guidance
   cat CLAUDE.md
   cat WORKFLOW.md
   
   # Check current tasks
   task
   ```

2. **Initialize Task if Needed**
   ```bash
   # Create new task
   task new "Implement feature X"
   
   # Or select existing task
   task select <number>
   ```

3. **Review Task Context**
   ```bash
   # View current task details
   task current
   
   # Check task history
   task history
   ```

## Development Flow

### 1. Planning Phase
- Use TodoWrite to create task breakdown
- Check existing code patterns with search tools
- Review related files and dependencies

### 2. Implementation Phase
```bash
# Expand task with implementation steps
task expand

# As you work, add context
task context "Found existing validation in utils.py"
task context "Need to update tests for new validation"

# Track dependencies
task depends "Update API documentation"
task depends "Add integration tests"
```

### 3. Testing Phase
```bash
# After implementation
npm test  # or appropriate test command
npm run lint
npm run typecheck

# Add test results to context
task context "All tests passing, lint clean"
```

### 4. Completion Phase
```bash
# Mark task complete with summary
task complete "Implemented feature X with tests and documentation"

# Or if blocked
task blocked "Waiting for API endpoint from backend team"
```

## Best Practices

### Context Management
- Add context notes as you discover important information
- Include file paths and line numbers in context
- Note any decisions or trade-offs made

### Dependency Tracking
- Add dependencies as soon as they're identified
- Use clear, actionable descriptions
- Check dependencies before marking task complete

### Progress Updates
- Use task progress regularly
- Update task state (backlog → doing → done)
- Keep task descriptions current with `task update`

### Sub-task Management
```bash
# Create related sub-tasks
task subtask "Write unit tests for validation"
task subtask "Update API documentation"

# View task tree
task tree
```

## Integration with Claude Code Tools

### With TodoWrite/TodoRead
- TodoWrite creates the execution plan
- TaskMaster tracks the overall task progress
- Use both in tandem for comprehensive tracking

### With Search Tools
- Use results to add context: `task context "Found pattern in src/utils.ts:45"`
- Track files to review: `task depends "Review src/api/routes.ts"`

### With Git Operations
- Before commits: `task context "Ready for commit - all tests passing"`
- After PR: `task complete "Merged in PR #123"`

## Common Workflows

### Feature Development
1. `task new "Add user authentication"`
2. `task expand` → Break down into steps
3. Implement with TodoWrite tracking
4. `task context` → Add discoveries
5. `task complete` → Finish with summary

### Bug Fixing
1. `task new "Fix: Users can't login with email"`
2. `task context "Error in auth.js:validateEmail"`
3. Fix issue and test
4. `task complete "Fixed email validation regex"`

### Refactoring
1. `task new "Refactor: Extract validation logic"`
2. `task depends "Update all calling code"`
3. `task depends "Ensure backward compatibility"`
4. Refactor systematically
5. `task complete` with changes summary

## Emergency Commands

If task state gets corrupted:
```bash
# Force reset current task (use with caution)
task reset --force

# Archive all completed tasks
task archive

# Show raw task data for debugging
task debug
```

## Tips

1. **Small, Focused Tasks**: Keep tasks atomic and completable in one session
2. **Clear Descriptions**: Use imperative mood ("Add", "Fix", "Update")
3. **Regular Updates**: Add context as you work, not just at the end
4. **Complete Promptly**: Mark done as soon as finished to maintain accurate state

Remember: TaskMaster maintains state across sessions, so always check current task status when resuming work.