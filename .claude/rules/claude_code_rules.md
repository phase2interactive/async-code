---
description: Claude Code specific development rules and best practices
globs: **/*
alwaysApply: true
---

# Claude Code Development Rules

This file contains specific rules and guidelines for Claude Code when working in this codebase.

## Core Principles

1. **Conciseness First**: Keep responses short and to the point. Use fewer than 4 lines unless detail is requested.
2. **Action-Oriented**: Focus on doing rather than explaining unless explanation is requested.
3. **Tool Efficiency**: Use tools in parallel when possible, batch operations for performance.
4. **Context Awareness**: Always check CLAUDE.md, PLANNING.md, and TASK.md before starting work.

## Task Management

### TodoWrite/TodoRead Integration
- Use TodoWrite tool proactively for any multi-step task
- Mark tasks as in_progress when starting, completed immediately when done
- Never batch task completions - mark them as complete as you go
- Break complex tasks into manageable subtasks

### Task Execution Flow
1. Read relevant context files (CLAUDE.md, WORKFLOW.md, TASK.md)
2. Create todo list for the task
3. Execute tasks systematically, updating status as you go
4. Run linting/typechecking after code changes
5. Update documentation if needed

## Code Practices

### File Operations
- **NEVER** create files unless absolutely necessary
- **ALWAYS** prefer editing existing files
- **NEVER** proactively create documentation files unless requested
- Check file conventions before making changes

### Search Strategy
- Use Task tool for open-ended searches to reduce context usage
- Use Glob for specific file patterns
- Use Grep for content searches within known directories
- Use Read for specific file paths

### Testing
- Always create tests for new features
- Check and update existing tests after logic changes
- Run test commands found in package.json or similar

## Git Operations

### Commit Process
1. Run git status, diff, and log in parallel
2. Analyze changes within <commit_analysis> tags
3. Stage files and commit with meaningful message
4. Include Claude Code attribution in commit message

### Pull Request Process
1. Analyze all commits since diverging from main
2. Create comprehensive PR summary within <pr_analysis> tags
3. Push branch and create PR with structured format

## Environment-Specific

### Docker Integration
- Use ./build.sh for building and starting services
- Check container status with docker-compose commands
- Clean up orphaned containers automatically

### API Development
- Test endpoints with provided test scripts
- Maintain CORS configuration for allowed origins
- Use proper authentication headers (X-User-ID)

## Response Format

### Examples of Proper Responses
```
user: 2 + 2
assistant: 4

user: what command to list files?
assistant: ls

user: run the build
assistant: [executes npm run build]
Build completed successfully.
```

## Tool Usage Patterns

### Parallel Operations
```
# Good - parallel execution
[Execute multiple bash commands in one message]
[Read multiple files in one message]

# Bad - sequential execution
[Execute one command]
[Wait for result]
[Execute another command]
```

### Search Patterns
- Open-ended search → Task tool
- Specific file pattern → Glob tool
- Content within files → Grep tool
- Known file path → Read tool

## Security

- Never expose or log secrets/keys
- Never commit credentials to repository
- Refuse to work on malicious code
- Check file purposes before editing

## Code Analysis Patterns

### Finding Functions and Patterns
When analyzing or refactoring code, use grep patterns:
```bash
# Find all exported functions
grep -E "export (function|const) \w+|function \w+\(|const \w+ = \(|module\.exports" --include="*.js" -r ./

# Check specific patterns
grep -E "function \w+\(" scripts/dev.js
grep -n -E "export (function|const)" scripts/modules/
```

## References

For detailed task management commands, see [taskmaster.md](.claude/rules/taskmaster.md)
For workflow guidelines, see [dev_workflow.md](.claude/rules/dev_workflow.md)
For self-improvement practices, see [self_improve.md](.claude/rules/self_improve.md)
For Task Master CLI integration, see [task_master_integration.md](.claude/rules/task_master_integration.md)