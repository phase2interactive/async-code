# Task Management Workflow

## Overview
This repository uses a `tasks/` folder structure to help Claude maintain context and track progress across work sessions. Each task serves as a living document that captures the full journey from conception to completion.

## Folder Structure
```
tasks/
├── ideas/       # High-level concepts and features to explore
├── todo/        # Decomposed tasks ready to be started
├── inprogress/  # Tasks currently being worked on
├── review/      # Completed work awaiting code review
└── done/        # Fully completed and reviewed tasks
```

## Workflow
The task lifecycle follows this progression:

**Ideas → Todo → In Progress → Review → Done**

### Managing Ideas
- **Purpose**: Capture high-level concepts, features, or improvements
- **Content**: Rough concepts that need decomposition before work can begin
- **Actions**: 
  - Document the core idea and its potential value
  - Note any initial thoughts on approach or complexity
  - When ready to act, decompose into specific, workable tasks in `todo/`

### Working on Tasks
1. **Starting Work**: Move the task file from `tasks/todo/` to `tasks/inprogress/`
2. **During Work**: Use the task file as your primary scratch pad and context manager
   - Document decisions made and rationale
   - Track blockers, dependencies, and questions
   - Note key findings and learnings
   - Update progress at meaningful milestones
3. **Code Complete**: Move to `tasks/review/` when code is written but needs review
4. **Final Completion**: Move to `tasks/done/` after successful code review

## File Formats

### Ideas Files
- **Purpose**: High-level vision and rough concepts
- **Format**: 
  - Problem statement or opportunity
  - Potential approaches or solutions
  - Success criteria or goals
  - Rough complexity/effort estimates
  - Dependencies or prerequisites

### Task Files
Each active task should maintain:
- **Current Status**: Brief summary of where things stand
- **Progress Log**: Chronological updates (like GitHub issue comments)
- **Key Decisions**: Important choices made and why
- **Blockers/Dependencies**: What's preventing progress or needed from others
- **Next Steps**: Clear actions for continuation
- **Learning Notes**: Insights gained that might be useful later
- **Review Notes**: (For items in review) Feedback received and responses

## Benefits
- **Idea Capture**: Never lose promising concepts, even if not ready to implement
- **Clear Decomposition**: Separate ideation from execution planning
- **Context Persistence**: Maintain understanding across multiple sessions
- **Decision Tracking**: Remember why choices were made
- **Review Management**: Track code review feedback and responses
- **Knowledge Capture**: Preserve learnings for future reference
- **Progress Visibility**: Clear history of what's been accomplished

Think of the `ideas/` folder as your innovation backlog, while task files serve as your personal project journals - capturing not just what you did, but your thought process, challenges encountered, and insights gained.