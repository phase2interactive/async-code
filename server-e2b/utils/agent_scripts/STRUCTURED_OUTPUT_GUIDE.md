# Structured Output Guide for AI Agents

## Overview

Both Claude and Codex agents now require structured JSON output for code changes. This eliminates parsing ambiguities and ensures consistent, reliable results.

## JSON Response Format

AI agents should respond with the following JSON structure:

```json
{
  "summary": "Brief description of changes made",
  "file_operations": [
    {
      "action": "create",
      "path": "src/new_file.py",
      "content": "# Complete file content here\nprint('Hello')"
    },
    {
      "action": "update",
      "path": "src/existing_file.py",
      "content": "# Updated content"
    },
    {
      "action": "delete",
      "path": "src/old_file.py"
    }
  ]
}
```

## Implementation Details

### Codex Agent (GPT)
- Uses OpenAI function calling to enforce structured output
- Function schema defined in `codex_agent.py`
- Automatically validates response format

### Claude Agent
- Explicit instructions added to prompt for JSON format
- Falls back to regex parsing if JSON parsing fails
- Returns error information in JSON format on API failures

### Parser Utils
The `parser_utils.py` module provides:
- `parse_json_response()`: Attempts to parse structured JSON
- `parse_file_changes()`: First tries JSON, then falls back to regex
- `validate_file_operations()`: Validates and normalizes operations
- `normalize_file_path()`: Ensures paths are relative to repo root

## Benefits

1. **Reliability**: Structured output eliminates parsing ambiguities
2. **Validation**: Operations are validated before execution
3. **Error Handling**: Clear error reporting in structured format
4. **Consistency**: Same format across different AI models
5. **Extensibility**: Easy to add new fields or operation types

## Requirements

- AI responses MUST be valid JSON
- The response MUST include a `file_operations` field
- Each operation MUST have `action` and `path` fields
- `content` field is required for `create` and `update` actions
- Invalid JSON will cause the task to fail with an error

## Error Handling

If the AI response is not valid JSON or missing required fields:
1. The agent will log an error
2. The task will fail with exit code 1
3. An error message will be displayed to the user

### API Error Responses

When API calls fail (rate limits, authentication errors, etc.), both agents return a valid JSON response with an error summary:

```json
{
  "summary": "Error: API rate limit exceeded. Please try again later.",
  "file_operations": []
}
```

This ensures consistent error handling throughout the pipeline, as `apply_changes()` always receives valid JSON to parse.