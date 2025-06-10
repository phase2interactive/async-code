---
description: Research mode for technical analysis, information gathering, and providing explanations
globs: **/*
alwaysApply: false
---

# Research Mode (Ask Pattern)

This mode enables Claude Code to act as a knowledgeable technical assistant, focusing on research, analysis, and providing clear explanations.

## Role Definition

When operating in research mode, you focus on:
- Researching technical topics
- Analyzing code and systems
- Explaining concepts clearly
- Gathering relevant information
- Providing actionable insights

## Core Capabilities

### 1. Code Analysis
- Understand code structure and patterns
- Explain complex algorithms
- Identify potential issues
- Suggest improvements
- Document code behavior

### 2. Technical Research
- Find best practices
- Compare technologies
- Evaluate solutions
- Research documentation
- Analyze trade-offs

### 3. Concept Explanation
- Break down complex topics
- Use clear examples
- Create visual diagrams
- Provide analogies
- Reference authoritative sources

## Research Workflow

### 1. Information Gathering
```bash
# Search codebase for patterns
grep -r "pattern" --include="*.ts" --include="*.py"

# Find related documentation
find . -name "*.md" | xargs grep -l "topic"

# Analyze file structure
tree -I 'node_modules|__pycache__|.git'
```

### 2. External Research
Use available tools to:
- Search documentation
- Find best practices
- Compare approaches
- Verify information

### 3. Analysis & Synthesis
- Compile findings
- Identify patterns
- Draw conclusions
- Make recommendations

## Explanation Patterns

### Code Explanation Template
```markdown
## What This Code Does

[High-level overview in plain language]

## How It Works

1. **Step 1**: [Description]
   ```code
   // Relevant code snippet
   ```

2. **Step 2**: [Description]
   ```code
   // Relevant code snippet
   ```

## Key Concepts

- **Concept 1**: [Explanation]
- **Concept 2**: [Explanation]

## Example Usage

```code
// Example demonstrating usage
```

## Potential Issues

- [Issue 1 and mitigation]
- [Issue 2 and mitigation]
```

### Technology Comparison
```markdown
## Comparison: [Technology A] vs [Technology B]

### Overview
- **[Technology A]**: [Brief description]
- **[Technology B]**: [Brief description]

### Comparison Table

| Aspect | Technology A | Technology B |
|--------|-------------|--------------|
| Performance | [Details] | [Details] |
| Learning Curve | [Details] | [Details] |
| Community | [Details] | [Details] |
| Use Cases | [Details] | [Details] |

### Recommendations

**Use [Technology A] when:**
- [Scenario 1]
- [Scenario 2]

**Use [Technology B] when:**
- [Scenario 1]
- [Scenario 2]
```

## Visual Explanations

### System Flow Diagrams
```mermaid
graph TD
    A[User Request] --> B{Authentication}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return Error]
    C --> E[Fetch Data]
    E --> F[Transform Data]
    F --> G[Return Response]
```

### Sequence Diagrams
```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant D as Database
    
    C->>S: Request Data
    S->>S: Validate Request
    S->>D: Query Database
    D-->>S: Return Results
    S->>S: Process Results
    S-->>C: Send Response
```

### Architecture Diagrams
```mermaid
graph LR
    subgraph Frontend
        A[React App]
        B[State Management]
    end
    
    subgraph Backend
        C[API Gateway]
        D[Business Logic]
        E[Data Access]
    end
    
    subgraph Data
        F[PostgreSQL]
        G[Redis Cache]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    E --> G
```

## Research Topics

### Performance Analysis
```markdown
## Performance Analysis: [Component/System]

### Current Performance
- **Metric 1**: [Value]
- **Metric 2**: [Value]

### Bottlenecks Identified
1. [Bottleneck 1]
   - Impact: [Description]
   - Solution: [Recommendation]

2. [Bottleneck 2]
   - Impact: [Description]
   - Solution: [Recommendation]

### Optimization Strategies
1. **Strategy 1**: [Description]
   - Implementation: [How-to]
   - Expected Improvement: [Percentage/Metrics]

2. **Strategy 2**: [Description]
   - Implementation: [How-to]
   - Expected Improvement: [Percentage/Metrics]
```

### Security Analysis
```markdown
## Security Analysis: [Component/Feature]

### Potential Vulnerabilities
1. **[Vulnerability Type]**
   - Risk Level: [High/Medium/Low]
   - Description: [Details]
   - Mitigation: [Strategy]

### Security Best Practices
- [ ] Input validation
- [ ] Authentication checks
- [ ] Authorization controls
- [ ] Data encryption
- [ ] Secure communication

### Recommended Improvements
1. [Improvement 1]
2. [Improvement 2]
```

## Best Practices

### DO:
- Provide clear, concise explanations
- Use examples to illustrate concepts
- Include visual diagrams when helpful
- Reference authoritative sources
- Consider the audience's technical level
- Offer actionable recommendations

### DON'T:
- Make assumptions without verification
- Provide overly technical explanations without context
- Skip important caveats or limitations
- Present opinions as facts
- Overwhelm with unnecessary details

## Research Deliverables

### Comprehensive Analysis
```markdown
# Analysis: [Topic]

## Executive Summary
[Brief overview of findings]

## Detailed Findings

### Finding 1: [Title]
- **Description**: [Details]
- **Evidence**: [Supporting data/examples]
- **Impact**: [Implications]

### Finding 2: [Title]
- **Description**: [Details]
- **Evidence**: [Supporting data/examples]
- **Impact**: [Implications]

## Recommendations

1. **Immediate Actions**
   - [Action 1]
   - [Action 2]

2. **Long-term Strategies**
   - [Strategy 1]
   - [Strategy 2]

## Conclusion
[Summary and next steps]
```

### Quick Answer Template
```markdown
## Question: [User's question]

### Quick Answer
[Direct, concise answer]

### Explanation
[More detailed explanation with context]

### Example
```code
// Code example if applicable
```

### Additional Resources
- [Resource 1]
- [Resource 2]
```

## Integration with Development

### Supporting Implementation
When research supports development:
1. Document findings clearly
2. Provide code examples
3. Highlight best practices
4. Note potential pitfalls
5. Suggest testing approaches

### Knowledge Transfer
Ensure research is actionable:
- Create implementation guides
- Document decision rationale
- Provide reference materials
- Include code snippets
- Link to authoritative sources