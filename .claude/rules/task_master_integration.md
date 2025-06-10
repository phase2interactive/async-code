---
description: Task Master CLI integration and development workflow for Claude Code
globs: **/*
alwaysApply: true
---

# Task Master Integration Guide

This rule provides comprehensive integration with the Task Master global CLI for managing task-driven development workflows.

## Installation and Setup

### Global CLI Commands
- Task Master provides a global CLI through the `task-master` command
- Install globally: `npm install -g claude-task-master`
- Or use locally via: `npx task-master <command>`
- All functionality from legacy `scripts/dev.js` is available through this interface

### Command Migration
Replace legacy commands with Task Master CLI:
- `node scripts/dev.js list` → `task-master list`
- `node scripts/dev.js next` → `task-master next`
- `node scripts/dev.js expand --id=3` → `task-master expand --id=3`

## Development Workflow Process

### Starting New Projects
1. Initialize with `task-master init` or parse PRD: `task-master parse-prd --input=<prd-file.txt>`
2. Review generated tasks with `task-master list`
3. Analyze complexity: `task-master analyze-complexity --research`
4. Begin implementation based on dependencies and priorities

### Task Selection Strategy
1. Run `task-master next` to identify the next task
2. Check dependencies are marked 'done'
3. Consider priority levels and ID order
4. Review task details with `task-master show <id>`

### Task Implementation Flow
1. **Clarify**: Check task files in `tasks/` directory
2. **Expand**: Break down complex tasks with `task-master expand --id=<id>`
3. **Implement**: Follow task details and project standards
4. **Verify**: Test according to strategy before completion
5. **Complete**: Mark done with `task-master set-status --id=<id> --status=done`

### Managing Dependencies
- Add: `task-master add-dependency --id=<id> --depends-on=<id>`
- Remove: `task-master remove-dependency --id=<id> --depends-on=<id>`
- Validate: `task-master validate-dependencies`
- Fix: `task-master fix-dependencies`

## Command Reference

### Core Task Commands

#### task-master init
Initialize a new project with Task Master structure.
```bash
task-master init
```

#### task-master parse-prd
Parse a PRD document and generate tasks.json.
```bash
task-master parse-prd --input=requirements.txt
```

#### task-master list
List all tasks with status and dependencies.
```bash
task-master list
task-master list --status=pending
task-master list --with-subtasks
```

#### task-master next
Show the next task to work on based on dependencies.
```bash
task-master next
```

#### task-master show
View detailed information about a specific task.
```bash
task-master show 3
task-master show 1.2  # Subtask 2 of task 1
```

### Task Management

#### task-master add-task
Add a new task using AI.
```bash
task-master add-task --prompt="Create user authentication" --priority=high
```

#### task-master set-status
Update task status.
```bash
task-master set-status --id=3 --status=done
```

#### task-master update
Update future tasks based on implementation changes.
```bash
task-master update --from=4 --prompt="Now using Express instead of Fastify"
```

### Task Analysis

#### task-master analyze-complexity
Analyze task complexity and generate recommendations.
```bash
task-master analyze-complexity --research
task-master analyze-complexity --threshold=5
```

#### task-master complexity-report
Display formatted complexity analysis.
```bash
task-master complexity-report
```

### Task Breakdown

#### task-master expand
Expand tasks into subtasks.
```bash
task-master expand --id=3
task-master expand --id=3 --research --prompt="Focus on security"
task-master expand --all  # Expand all pending tasks
```

#### task-master clear-subtasks
Remove subtasks for regeneration.
```bash
task-master clear-subtasks --id=3
task-master clear-subtasks --id=1,2,3
task-master clear-subtasks --all
```

### Task Generation

#### task-master generate
Generate individual task files from tasks.json.
```bash
task-master generate
task-master generate --file=custom-tasks.json --output=custom-tasks/
```

## Task Structure Reference

```javascript
{
  "id": 1,
  "title": "Initialize Repository",
  "description": "Create repository and initial structure",
  "status": "pending",  // pending, done, deferred
  "dependencies": [1, 2],  // Shows as ✅ (done) or ⏱️ (pending)
  "priority": "high",  // high, medium, low
  "details": "Detailed implementation instructions...",
  "testStrategy": "How to verify completion...",
  "subtasks": [
    {
      "id": 1,
      "title": "Create package.json",
      "status": "pending"
    }
  ]
}
```

## Environment Configuration

```bash
# Required
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional
export MODEL=claude-3-sonnet-20241022
export MAX_TOKENS=4000
export TEMPERATURE=0.7
export DEBUG=true
export TASKMASTER_LOG_LEVEL=debug
export DEFAULT_SUBTASKS=3
export DEFAULT_PRIORITY=medium
export PROJECT_NAME="My Project"
export PROJECT_VERSION=1.0.0

# For research features
export PERPLEXITY_API_KEY=pplx-...
export PERPLEXITY_MODEL=sonar-medium-online
```

## Implementation Drift Handling

When implementation differs from plan:
1. Identify which future tasks are affected
2. Run: `task-master update --from=<id> --prompt="explanation"`
3. Review and adjust updated tasks
4. Regenerate task files with `task-master generate`

## Code Analysis Techniques

### Function Discovery Pattern
```bash
# Find all exported functions
grep -E "export (function|const) \w+|function \w+\(|const \w+ = \(|module\.exports" --include="*.js" -r ./

# Check specific file
grep -E "function \w+\(" scripts/dev.js

# Find naming conflicts
grep -E "function (get|set|create|update)\w+\(" -r ./

# With line numbers
grep -n -E "export (function|const)" scripts/modules/
```

Use for:
- Mapping functions before refactoring
- Verifying migration completeness
- Identifying duplicate functionality
- Finding naming conflicts

## Best Practices

1. **Session Start**: Always run `task-master list` and `task-master next`
2. **Regular Updates**: Use `task-master set-status` immediately after completion
3. **Complex Tasks**: Run complexity analysis before breaking down
4. **Dependencies**: Validate regularly with `task-master validate-dependencies`
5. **Context**: Add implementation notes to task details
6. **Progress**: Report regularly using list command

## Integration with Claude Code

### With TodoWrite/TodoRead
- Task Master manages overall project tasks
- TodoWrite tracks execution steps within a task
- Use both for comprehensive tracking

### Workflow Example
```bash
# 1. Check next task
task-master next

# 2. Use TodoWrite for execution plan
# 3. Implement following task details
# 4. Mark complete
task-master set-status --id=3 --status=done

# 5. Check for new tasks
task-master next
```

## Emergency Commands

```bash
# Force reset if corrupted
task-master reset --force

# Export for backup
task-master export > backup.json

# Import from backup
task-master import backup.json

# Clear all tasks (caution!)
task-master clear --confirm
```