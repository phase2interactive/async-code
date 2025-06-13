# Agent Scripts for E2B Sandbox Execution

This directory contains the agent scripts that are uploaded to E2B sandboxes for AI-powered code generation tasks.

## Overview

The agent scripts provide a standardized interface for different AI models (Claude, GPT/Codex) to execute code generation tasks within isolated E2B sandbox environments.

## Key Features

### 1. Structured JSON Output (Required)
Both agents require structured JSON output for all responses:

```json
{
  "summary": "Brief description of changes",
  "file_operations": [
    {
      "action": "create|update|delete",
      "path": "file/path",
      "content": "file content"
    }
  ]
}
```

### 2. Repository Analysis
Agents analyze the repository structure to provide better context:
- File and directory listing
- Language detection
- Key file identification (README, package.json, etc.)

### 3. Error Handling
- Proper exit codes (sys.exit(1) on failure)
- Detailed logging for debugging
- JSON validation with clear error messages

## Agent Scripts

### claude_agent.py
- Uses Anthropic Python SDK (no more CLI security issues)
- Supports environment variables for configuration
- Returns structured JSON output

### codex_agent.py
- Uses OpenAI function calling for enforced structured output
- Sophisticated repository analysis
- Support for create, update, and delete operations

### parser_utils.py
- Shared parsing utilities
- JSON parsing with regex fallback
- Path normalization
- Operation validation

## Testing

Run the test suite:
```bash
cd /workspaces/async-code-worktrees/e2b-migration/server-e2b/utils/agent_scripts
python -m pytest tests/ -v
```

## Environment Variables

### Claude Agent
- `ANTHROPIC_API_KEY` (required)
- `CLAUDE_MODEL` (default: claude-3-sonnet-20240229)
- `CLAUDE_MAX_TOKENS` or `MAX_TOKENS` (default: 4000)
- `CLAUDE_TEMPERATURE` or `TEMPERATURE` (default: 0.7)

### Codex Agent
- `OPENAI_API_KEY` (required)
- `GPT_MODEL` (default: gpt-4)
- `MAX_TOKENS` (default: 2000)
- `TEMPERATURE` (default: 0.7)

## JSON Output Requirements

**Important**: All AI responses must be valid JSON with the required format.
Regex-based parsing has been removed to ensure consistency.

See `STRUCTURED_OUTPUT_GUIDE.md` for detailed information.