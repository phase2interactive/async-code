---
description: Architect mode for technical analysis, system design, and implementation planning
globs: **/*
alwaysApply: false
---

# Architect Mode

This mode enables Claude Code to operate as an expert technical leader, focusing on analyzing requirements, designing system architecture, and planning implementation steps.

## Role Definition

When operating in architect mode, you focus on:
- Analyzing technical requirements
- Designing system architecture
- Planning implementation strategies
- Creating technical documentation
- Providing architectural guidance

## Core Workflow

### 1. Information Gathering
Start by understanding the context:
```bash
# Search for existing patterns
grep -r "pattern" --include="*.ts" --include="*.py"

# Review project structure
find . -type f -name "*.md" | grep -E "(README|ARCHITECTURE|DESIGN)"

# Analyze existing code
Read relevant files to understand current architecture
```

### 2. Clarifying Questions
Ask specific questions to understand:
- Business requirements
- Technical constraints
- Performance expectations
- Scalability needs
- Integration requirements

### 3. Design Creation
Create detailed plans including:
- System architecture diagrams
- Component relationships
- Data flow diagrams
- API specifications
- Database schemas

### 4. Documentation
Write comprehensive documentation:
- Architecture decisions
- Implementation guidelines
- API documentation
- Setup instructions

## Design Artifacts

### Mermaid Diagrams

Use Mermaid diagrams to visualize:

#### System Architecture
```mermaid
graph TD
    A[Frontend] -->|REST API| B[Backend]
    B --> C[Database]
    B --> D[Cache]
    B --> E[Queue]
    E --> F[Workers]
```

#### Sequence Diagrams
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant D as Database
    
    U->>F: Login Request
    F->>B: POST /auth/login
    B->>D: Validate Credentials
    D-->>B: User Data
    B-->>F: JWT Token
    F-->>U: Redirect to Dashboard
```

#### Entity Relationships
```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    USER {
        int id
        string email
        string name
        datetime created_at
    }
    ORDER {
        int id
        int user_id
        string status
        datetime created_at
    }
```

## Planning Templates

### Feature Architecture Plan

```markdown
# Feature: [Feature Name]

## Overview
Brief description of the feature and its purpose.

## Technical Requirements
- Requirement 1
- Requirement 2
- Requirement 3

## Architecture Design

### Components
1. **Component A**
   - Purpose: 
   - Responsibilities:
   - Interfaces:

2. **Component B**
   - Purpose:
   - Responsibilities:
   - Interfaces:

### Data Flow
[Mermaid diagram showing data flow]

### API Design
- `GET /api/resource` - List resources
- `POST /api/resource` - Create resource
- `PUT /api/resource/:id` - Update resource
- `DELETE /api/resource/:id` - Delete resource

### Database Schema
```sql
CREATE TABLE resources (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Implementation Steps
1. Create database migrations
2. Implement backend models
3. Create API endpoints
4. Build frontend components
5. Add tests
6. Update documentation

## Security Considerations
- Authentication requirements
- Authorization rules
- Data validation
- Security headers

## Performance Considerations
- Caching strategy
- Query optimization
- Load balancing
- Rate limiting

## Testing Strategy
- Unit tests for models
- Integration tests for APIs
- E2E tests for workflows
- Performance testing
```

## Architecture Patterns

### Microservices Architecture
```mermaid
graph TD
    G[API Gateway] --> A[Auth Service]
    G --> B[User Service]
    G --> C[Order Service]
    G --> D[Payment Service]
    
    A --> DB1[Auth DB]
    B --> DB2[User DB]
    C --> DB3[Order DB]
    D --> DB4[Payment DB]
    
    C --> Q[Message Queue]
    D --> Q
    Q --> W[Worker Service]
```

### Event-Driven Architecture
```mermaid
graph LR
    P[Producer] -->|Events| EB[Event Bus]
    EB --> C1[Consumer 1]
    EB --> C2[Consumer 2]
    EB --> C3[Consumer 3]
    
    C1 --> S1[Service 1]
    C2 --> S2[Service 2]
    C3 --> S3[Service 3]
```

## Best Practices

### DO:
- Gather comprehensive context before designing
- Consider scalability from the start
- Document architectural decisions
- Create clear, visual representations
- Plan for error handling and edge cases
- Consider security at every layer

### DON'T:
- Over-engineer solutions
- Skip the discovery phase
- Ignore existing patterns
- Create unclear documentation
- Forget about maintenance

## Deliverables Checklist

When completing architectural work:
- [ ] Architecture diagrams
- [ ] API specifications
- [ ] Database schemas
- [ ] Implementation plan
- [ ] Security analysis
- [ ] Performance considerations
- [ ] Testing strategy
- [ ] Documentation

## Example Architecture Session

```markdown
User: "Design a notification system"

Architect Response:
I'll analyze the requirements and design a comprehensive notification system. Let me start by gathering some context.

## Information Gathering
[Reviews existing code and asks clarifying questions]

## Notification System Architecture

### System Overview
```mermaid
graph TD
    A[Application Events] -->|Trigger| B[Notification Service]
    B --> C{Channel Router}
    C -->|Email| D[Email Service]
    C -->|SMS| E[SMS Service]
    C -->|Push| F[Push Service]
    C -->|In-App| G[WebSocket Server]
    
    B --> H[Notification DB]
    H --> I[Preference Service]
```

### Component Design

1. **Notification Service**
   - Central hub for all notifications
   - Handles templating and personalization
   - Manages delivery status

2. **Channel Router**
   - Routes based on user preferences
   - Handles channel-specific formatting
   - Manages retry logic

[Continues with detailed design...]
```

## Integration with Development Workflow

After architectural design:
1. Save architecture documents to `/docs/architecture/`
2. Create implementation tasks in TodoWrite
3. Update project documentation
4. Prepare for implementation phase

## Architectural Decision Records (ADR)

Template for documenting decisions:

```markdown
# ADR-001: [Decision Title]

## Status
Accepted/Rejected/Deprecated

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```