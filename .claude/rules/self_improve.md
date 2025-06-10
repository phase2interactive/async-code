---
description: Guidelines for Claude Code to self-improve by creating and updating rules based on code patterns
globs: **/*
alwaysApply: false
---

# Self-Improvement Guidelines for Claude Code

This document outlines how Claude Code should identify patterns and create or update rules to improve future performance.

## When to Create New Rules

Create new rules when you encounter:
1. **Repeated Patterns**: Same type of task or code pattern appears 3+ times
2. **Project-Specific Conventions**: Unique patterns not covered by general rules
3. **Common Mistakes**: Errors that could be prevented with explicit guidance
4. **Workflow Optimizations**: Better ways to accomplish frequent tasks

## Rule Creation Process

### 1. Identify the Pattern
Look for:
- Repeated code structures
- Common file organizations
- Specific naming conventions
- Testing patterns
- Error handling approaches

### 2. Analyze the Context
Before creating a rule:
- Check if existing rules cover this pattern
- Verify the pattern is project-wide, not file-specific
- Ensure the pattern is beneficial and intentional

### 3. Create the Rule File

```bash
# Rule file location
.claude/rules/<domain>_<specific>_rules.md

# Examples:
.claude/rules/api_error_handling_rules.md
.claude/rules/component_structure_rules.md
.claude/rules/testing_patterns_rules.md
```

### 4. Rule File Format

```markdown
---
description: Brief, clear description of what this rule covers
globs: path/pattern/*.ext  # Files this rule applies to
alwaysApply: false  # Usually false for specific patterns
---

# Rule Title

## Context
Brief explanation of why this rule exists and what problem it solves.

## Pattern
```language
// Code example showing the pattern
```

## Guidelines
1. Specific instruction
2. Another instruction
3. Edge cases to consider

## Examples

### Good ✓
```language
// Correct implementation
```

### Bad ✗
```language
// What to avoid
```

## References
- Related files: [file.ts](path/to/file.ts)
- Similar patterns: [other_rule.md](.claude/rules/other_rule.md)
```

## Updating Existing Rules

### When to Update
- Pattern has evolved or changed
- New edge cases discovered
- Better approach identified
- Conflicts with other patterns

### Update Process
1. Read current rule completely
2. Identify what needs changing
3. Update with clear additions/modifications
4. Add update note with date

```markdown
## Updates
- 2024-01-15: Added handling for async validators
- 2024-01-20: Updated to match new error format
```

## Pattern Categories

### Code Structure
- File organization patterns
- Module boundaries
- Import conventions
- Export patterns

### API Patterns
- Endpoint naming
- Error response formats
- Authentication patterns
- Validation approaches

### Frontend Patterns
- Component structure
- State management
- Event handling
- Styling approaches

### Testing Patterns
- Test file organization
- Mock strategies
- Assertion patterns
- Test data management

### Infrastructure
- Docker patterns
- Environment configuration
- Build processes
- Deployment patterns

## Rule Quality Checklist

Before creating/updating a rule, verify:
- [ ] Pattern appears 3+ times or is critically important
- [ ] Not already covered by existing rules
- [ ] Clear, actionable guidelines
- [ ] Includes concrete examples
- [ ] Specifies applicable file patterns
- [ ] No conflicts with other rules

## Meta-Rules

### Rule Naming
```
<domain>_<specific>_rules.md

domains: api, frontend, testing, infrastructure, database
specific: error_handling, validation, structure, patterns
```

### Rule Scope
- Keep rules focused on single concern
- Avoid overly broad rules
- Prefer multiple specific rules over one general rule

### Rule Maintenance
- Review rules when patterns change significantly
- Archive outdated rules with explanation
- Cross-reference related rules

## Examples of Good Rules

### Project-Specific Convention
"All API endpoints must return `{ data, error, meta }` structure"

### Workflow Optimization
"Use parallel tool calls for git status, diff, and log operations"

### Error Prevention
"Always check for existing tests before creating new test files"

## Integration with Development

When working on tasks:
1. Check applicable rules before starting
2. Note patterns that could become rules
3. Create rules after task completion if patterns identified
4. Update CLAUDE.md if rule is fundamental

## Rule Improvement Triggers

Monitor for:
- New code patterns not covered by existing rules
- Repeated similar implementations across files
- Common error patterns that could be prevented
- New libraries or tools being used consistently
- Emerging best practices in the codebase

## Analysis Process

1. Compare new code with existing rules
2. Identify patterns that should be standardized
3. Look for references to external documentation
4. Check for consistent error handling patterns
5. Monitor test patterns and coverage

## Rule Lifecycle

### Add New Rules When:
- A new technology/pattern is used in 3+ files
- Common bugs could be prevented by a rule
- Code reviews repeatedly mention the same feedback
- New security or performance patterns emerge

### Modify Existing Rules When:
- Better examples exist in the codebase
- Additional edge cases are discovered
- Related rules have been updated
- Implementation details have changed

### Deprecate Rules When:
- Patterns are no longer used
- Technology has been replaced
- Better approaches have been adopted
- Rules conflict with new standards

Remember: Rules should make future work more efficient and consistent, not add unnecessary constraints.