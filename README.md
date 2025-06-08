# Async Code Agent

Use Claude Code / CodeX CLI to perform multiple tasks in parallel with a Codex-style UI.

A code agent task management system that provides parallel execution of AI-powered coding tasks. Users can run multiple Claude Code agents simultaneously through a Codex-style web interface, with support for different agents for comparison and evaluation.

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


## License

See LICENSE file for details.

