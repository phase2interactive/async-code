# E2B Integration Documentation

## Overview

This document describes the E2B (e2b.dev) integration in the async-code backend. E2B provides secure sandboxed environments for executing AI-generated code, replacing the previous Docker-based implementation.

## Architecture

The E2B integration consists of two modes:

1. **Real E2B Mode**: Uses actual E2B sandboxes when `E2B_API_KEY` is configured
2. **Simulation Mode**: Falls back to subprocess execution for local development/testing

### Key Components

- `utils/code_task_e2b.py`: Main entry point with conditional loading
- `utils/code_task_e2b_real.py`: Real E2B implementation using the E2B SDK
- `utils/async_runner.py`: Async execution helper for Flask integration

## Configuration

### Environment Variables

```bash
# Required for real E2B mode
E2B_API_KEY=your_e2b_api_key

# Required for AI agents
ANTHROPIC_API_KEY=your_anthropic_key  # For Claude
OPENAI_API_KEY=your_openai_key       # For Codex/GPT

# Required for repository access
GITHUB_TOKEN=your_github_token
```

### E2B Account Setup

1. Sign up at [e2b.dev](https://e2b.dev)
2. Get your API key from the dashboard
3. Add the API key to your `.env` file

## Features

### Real E2B Implementation

When `E2B_API_KEY` is configured:

- Creates isolated sandboxes for each task
- Executes AI agents (Claude/Codex) in secure environments
- Supports git operations and code modifications
- Automatic cleanup of sandboxes
- Comprehensive error handling and timeouts

### Timeout Configuration

- **Sandbox lifetime**: 10 minutes
- **Git clone**: 1 minute
- **AI agent execution**: 5 minutes
- **Regular commands**: 30 seconds

### Error Handling

The implementation includes specific error handling for:

- E2B quota exceeded
- Invalid API keys
- GitHub authentication failures
- Repository not found
- Timeout errors
- Agent execution failures

## Testing

### Check Active Mode

```bash
cd server-e2b
python test_e2b_mode.py
```

### Test E2B Integration

```bash
cd server-e2b
python tests/test_e2b_integration.py
```

### Test API Endpoint

```bash
# Start the server
python main.py

# In another terminal, test task creation
curl -X POST http://localhost:8000/api/start-task \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "prompt": "Add a hello world function",
    "repo_url": "https://github.com/user/repo.git",
    "branch": "main",
    "github_token": "YOUR_GITHUB_TOKEN",
    "model": "claude"
  }'
```

## Migration from Docker

### Key Differences

1. **Isolation**: E2B provides stronger isolation than Docker containers
2. **No local Docker required**: Works in any environment
3. **Automatic scaling**: E2B handles resource allocation
4. **Built-in security**: Sandboxes are isolated from host system

### Backward Compatibility

The implementation maintains full backward compatibility:
- Same API endpoints
- Same database schema
- Same task execution flow
- Graceful fallback to simulation mode

## Troubleshooting

### Common Issues

1. **"E2B_API_KEY not found"**
   - Add your E2B API key to `.env`
   - Restart the server

2. **"E2B sandbox quota exceeded"**
   - Check your E2B account limits
   - Upgrade your plan if needed

3. **"GitHub authentication failed"**
   - Verify your GitHub token has required scopes
   - Token should start with `ghp_`

4. **Timeout errors**
   - Check repository size (large repos may timeout)
   - Consider increasing timeout values

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('utils.code_task_e2b_real').setLevel(logging.DEBUG)
```

## Development

### Running in Simulation Mode

For local development without E2B:

1. Don't set `E2B_API_KEY`
2. The system will use subprocess execution
3. Limited to local file operations

### Running with Real E2B

For production or full testing:

1. Set `E2B_API_KEY` in `.env`
2. Ensure you have sufficient E2B quota
3. Monitor sandbox usage in E2B dashboard

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Token Sanitization**: Error messages sanitize sensitive tokens
3. **Sandbox Isolation**: Each task runs in isolated environment
4. **Resource Limits**: Timeouts prevent resource exhaustion

## Future Enhancements

1. **Custom Templates**: Use specialized E2B templates for different languages
2. **Persistent Workspaces**: Support for long-running tasks
3. **Real-time Streaming**: Stream agent output as it's generated
4. **Multi-agent Support**: Run multiple agents in parallel