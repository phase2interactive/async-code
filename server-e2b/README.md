# AI Code Automation API - E2B Backend

This is the E2B-powered backend for the AI Code Automation system. It provides the same API interface as the original Docker-based backend but uses E2B sandboxes for secure, isolated code execution.

## Key Differences from Docker Backend

1. **E2B Sandboxes**: Instead of Docker containers, tasks run in E2B sandboxes
2. **No Docker Dependency**: The server doesn't require Docker to be installed
3. **Cloud-Native**: Designed to run on E2B's infrastructure
4. **Same API**: Maintains compatibility with the existing frontend

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `JWT_SECRET`: Secret for JWT token generation (min 32 chars)
- `E2B_API_KEY`: Your E2B API key

Optional:
- `ANTHROPIC_API_KEY`: For Claude agent
- `OPENAI_API_KEY`: For Codex agent

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Deploy to E2B

```bash
# Install E2B CLI
npm install -g @e2b/cli

# Login to E2B
e2b auth login

# Deploy
e2b deploy
```

## Local Development

For local testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export PORT=5000

# Run the server
python main.py
```

## API Endpoints

The API maintains full compatibility with the original backend:

### Authentication
- `POST /api/auth/token` - Generate JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/verify` - Verify token validity

### Tasks
- `POST /start-task` - Create a new AI code task
- `GET /task-status/<task_id>` - Get task status
- `GET /tasks` - List all tasks
- `GET /tasks/<task_id>` - Get task details
- `POST /tasks/<task_id>/chat` - Add chat message
- `POST /create-pr/<task_id>` - Create GitHub PR

### Projects
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/<id>` - Get project
- `PUT /projects/<id>` - Update project
- `DELETE /projects/<id>` - Delete project

### Health
- `GET /ping` - Health check
- `GET /health` - Detailed health status

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  E2B Backend │────▶│ E2B Sandbox │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Supabase  │
                    └─────────────┘
```

## E2B Sandbox Execution

When a task is created:

1. Task is saved to Supabase database
2. E2B sandbox is created with appropriate runtime
3. Repository is cloned into sandbox
4. AI agent (Claude/Codex) executes the task
5. Results are captured and saved to database
6. Sandbox is automatically cleaned up

## Security

- All code execution happens in isolated E2B sandboxes
- No direct Docker access required
- Sandboxes have resource limits and timeouts
- GitHub tokens are never stored, only used during execution

## Monitoring

View logs in E2B dashboard or using the CLI:

```bash
e2b logs -f
```

## Troubleshooting

### Common Issues

1. **E2B API Key**: Ensure your E2B_API_KEY is set correctly
2. **Sandbox Creation**: Check E2B quota and limits
3. **Agent API Keys**: Verify ANTHROPIC_API_KEY or OPENAI_API_KEY are valid
4. **Database Connection**: Check Supabase URL and service key

### Debug Mode

Set `FLASK_ENV=development` for detailed logging.

## Contributing

1. Make changes in the `server-e2b/` directory
2. Test locally with `python main.py`
3. Deploy to E2B with `e2b deploy`
4. Monitor logs for any issues