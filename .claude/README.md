# Claude Code Configuration

This directory contains configuration and rules specifically for Claude Code when working with the async-code project.

## Structure

```
.claude/
├── README.md                    # This file
├── config.json                  # Main configuration
├── mcp.json                     # MCP server configurations
└── rules/                       # Development rules and patterns
    ├── claude_code_rules.md     # Core Claude Code behavior rules
    ├── dev_workflow.md          # Development workflow with TaskMaster
    ├── self_improve.md          # Self-improvement guidelines
    ├── taskmaster.md            # TaskMaster command reference
    ├── task_master_integration.md # Task Master CLI integration guide
    ├── async_code_patterns.md   # Project-specific patterns
    └── modes/                   # Specialized operation modes
        ├── README.md            # Mode selection guide
        ├── orchestrator_mode.md # Complex task coordination
        ├── architect_mode.md    # System design and planning
        ├── implementation_mode.md # Code development
        ├── research_mode.md     # Technical research
        ├── debug_mode.md        # Problem diagnosis
        └── test_mode.md         # Testing and QA
```

## Quick Start

1. **Context Awareness**: Claude Code automatically loads rules from this directory
2. **Task Management**: Uses TaskMaster for tracking work progress
3. **MCP Integration**: Configured servers for task management, Supabase, and GitHub

## Key Features

### Automatic Rule Loading
Rules with `alwaysApply: true` are automatically loaded for every interaction:
- Core Claude Code behavior
- Development workflow
- TaskMaster integration
- Task Master CLI integration
- Project patterns

### Specialized Operation Modes
Adapted from Roo's multi-agent patterns, these modes provide focused expertise:
- **Orchestrator**: Coordinate complex workflows
- **Architect**: Design systems and plan implementations
- **Implementation**: Focus on code development
- **Research**: Analyze and explain technical concepts
- **Debug**: Diagnose and fix issues systematically
- **Test**: Ensure quality through comprehensive testing

### Task Tracking
Integrated with TaskMaster for:
- Task creation and management
- Context preservation across sessions
- Progress tracking
- Dependency management

### Tool Optimization
- Prefers Task tool for open-ended searches
- Parallel execution for multiple operations
- Batch processing for efficiency

### Git Integration
- Standardized commit messages with Claude Code attribution
- Structured PR creation process
- Automated analysis tags

## Configuration Details

### MCP Servers
1. **task-master-ai**: Task management and context tracking
2. **supabase**: Database operations and real-time features
3. **gitmcp**: GitHub integration for documentation and code search

### Code Style
- TypeScript: Single quotes, semicolons, 2-space tabs
- Python: Black formatter, Ruff linter, MyPy type checker

### Testing
- Frontend: `npm test`, `npm run lint`, `npm run typecheck`
- Backend: `pytest`, `ruff check`, `mypy`

## Usage

Claude Code will automatically:
1. Load configuration on startup
2. Apply relevant rules based on file patterns
3. Use TaskMaster for task tracking
4. Follow project-specific patterns

## Customization

To add new rules:
1. Create a new `.md` file in the `rules/` directory
2. Use the standard frontmatter format
3. Set `alwaysApply: true` for universal rules
4. Update `config.json` if needed

## Integration with Project

This configuration works alongside:
- `/CLAUDE.md` - Project-wide instructions
- `/WORKFLOW.md` - Development workflow
- `~/.claude/CLAUDE.md` - User's global preferences

Priority: User preferences → Project config → Claude Code config → Defaults