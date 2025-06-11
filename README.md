# Async Code Agent

Use Claude Code / CodeX CLI to perform multiple tasks in parallel with a Codex-style UI.

A code agent task management system that provides parallel execution of AI-powered coding tasks. Users can run multiple Claude Code agents simultaneously through a Codex-style web interface, with support for different agents for comparison and evaluation.

![async-code-ui](https://github.com/user-attachments/assets/e490c605-681a-4abb-a440-323e15f1a90d)


![async-code-review](https://github.com/user-attachments/assets/bbf71c82-636c-487b-bb51-6ad0b393c2ef)


## Key Features

- 🤖 **Multi-Agent Support**: Run Claude Code and other AI agents in parallel
- 🔄 **Parallel Task Management**: Execute multiple coding tasks simultaneously  
- 🌐 **Codex-Style Web UI**: Clean interface for managing agent tasks
- 🔍 **Agent Comparison**: Compare outputs from different AI models
- 🐳 **Containerized Execution**: Secure sandboxed environment for each task
- 🔗 **Git Integration**: Automatic repository cloning, commits, and PR creation
- **Selfhost**: Deploy you rown parallel code agent platform.

## Architecture

- **Frontend**: Next.js with TypeScript and TailwindCSS
- **Backend**: Python Flask API with Docker orchestration
- **Agents**: Claude Code (Anthropic) with extensible support for other models
- **Task Management**: Parallel execution system based on container

## Security

The system implements comprehensive security measures to ensure safe execution of AI agents:

### Container Security
- **Non-root Execution**: All containers run as UID 1000 (non-root user)
- **No Privileged Access**: Containers run without `--privileged` flag or host PID namespace
- **Capability Restrictions**: No dangerous Linux capabilities granted (no `CAP_SYS_ADMIN`, etc.)
- **Privilege Escalation Prevention**: `no-new-privileges=true` security option enforced
- **Sandboxed Environment**: Proper namespace isolation between container and host

### File System Security
- **Volume Permissions**: Workspace volumes mounted with proper ownership (1000:1000)
- **Read-only System Paths**: Containers cannot modify `/etc`, `/usr`, or other system directories
- **Isolated Workspaces**: Each task gets its own temporary workspace with restricted permissions

### Security Testing
The project includes security test scripts:
- `test-container-security.sh`: Verifies container isolation and restrictions
- `test-ai-functionality.sh`: Ensures agents work correctly with security measures
- Unit tests in `server/tests/test_container_security.py`

## Quick Start

1. **Setup**
   ```bash
   git clone <this-repo>
   cd async-code
   ./build.sh
   ```

2. **Configure**
   - Add your Anthropic API key to `server/.env`
   - Get a GitHub Personal Access Token with repo permissions

3. **Run**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## Usage

1. **Setup GitHub Token**: Enter your GitHub token in the web interface
2. **Configure Repository**: Specify target repository and branch
3. **Select Agent**: Choose your preferred AI agent (Claude Code, etc.)
4. **Submit Tasks**: Start multiple coding tasks in parallel
5. **Compare Results**: Review and compare outputs from different agents
6. **Create PRs**: Generate pull requests from successful tasks

## Environment Variables

```bash
# server/.env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
FLASK_ENV=production
```


## Development

```bash
# Run all services
docker-compose up

# Development mode
cd async-code-web && npm run dev  # Frontend
cd server && python main.py      # Backend
```

## Testing

The project includes a comprehensive test user system for automated testing:

- **Test User Management**: Automated test user creation with JWT authentication
- **Local Git Repositories**: Tests use local repos in `/tmp/test-repos/` to avoid external dependencies
- **Isolated Test Environment**: Complete separation from production data
- **Automated Cleanup**: Test data automatically cleaned up after 1 hour

```bash
# Run tests with test profile
docker-compose -f docker-compose.yml -f docker-compose.test.yml up

# Run Playwright E2E tests
cd async-code-web && npm run test:e2e

# Run backend unit tests
cd server && pytest
```


## License

See LICENSE file for details.

