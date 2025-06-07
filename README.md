# Claude Code Automation MVP

An MVP application that automates coding tasks using Claude Code or Codex CLI in sandboxed environments. Users can submit text prompts describing what they want to develop for a configured GitHub repository, and the selected AI model will analyze the codebase, make the necessary changes, and create commits that can be turned into pull requests.

## Features

- 🤖 **Multiple AI Models**: Choose between Claude Code and Codex CLI for code generation
- 🐳 **Sandboxed Execution**: Runs AI models in isolated Docker containers for security
- 🔄 **Git Integration**: Automatically clones repositories, makes commits, and creates pull requests
- 🌐 **Web Interface**: Clean, modern UI for submitting prompts and reviewing changes
- 📊 **Real-time Status**: Live updates on task progress and completion
- 🔍 **Git Diff Viewer**: Review all changes before creating pull requests
- 🎯 **Model Comparison**: Easily compare outputs from different AI models

## Architecture

- **Frontend**: Next.js with TypeScript and TailwindCSS
- **Backend**: Python Flask API with Docker orchestration
- **AI Models**: 
  - Claude Code (Anthropic) - Advanced coding model
  - Codex CLI (OpenAI) - Lightweight coding agent
- **Git Operations**: GitHub API integration for repository management

## Prerequisites

- Docker and Docker Compose
- [Anthropic API Key](https://console.anthropic.com/) for Claude Code
- GitHub Personal Access Token with repo permissions

## Quick Start

1. **Clone and Build**
   ```bash
   git clone <this-repo>
   cd <repo-directory>
   ./build.sh
   ```

2. **Configure Environment**
   - Edit `server/.env` with your Anthropic API key
   - The build script will create this file from the example

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

4. **Get a GitHub Token**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Create a token with `repo` permissions
   - Use this token in the frontend interface

## Usage

1. **Setup GitHub Token**: Click "Setup GitHub Token" in the frontend and enter your token
2. **Configure Repository**: Enter the GitHub repository URL and branch
3. **Select AI Model**: Choose between Claude Code or Codex CLI
4. **Enter Prompt**: Describe what you want the AI to develop
5. **Start Task**: Click "Code" to begin the automation process
6. **Review Changes**: View the git diff when the task completes
7. **Create PR**: If satisfied with changes, click "Create PR"

## Example Prompts

- "Add a new API endpoint for user authentication"
- "Fix the responsive design issues on mobile"
- "Add error handling to the database connection logic"
- "Implement input validation for the contact form"
- "Update the styling to match the new design system"

## Environment Variables

### Backend (`server/.env`)
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

## API Endpoints

- `POST /start-task` - Start a new automation task (supports `model` parameter: "claude" or "codex")
- `GET /task-status/<task_id>` - Get task status and progress (includes model used)
- `GET /git-diff/<task_id>` - Retrieve git diff for completed tasks
- `POST /create-pr/<task_id>` - Create a pull request from completed task

## Security Considerations

For this MVP:
- GitHub tokens are handled client-side only
- Tasks run in isolated Docker containers
- No persistent storage of sensitive data
- Direct API communication with Anthropic

For production:
- Implement proper authentication system
- Use GitHub Apps instead of personal tokens
- Add rate limiting and request validation
- Implement proper secret management

## Development

### Running Locally
```bash
# Start all services
docker-compose up

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Frontend Development
```bash
cd async-code-web
npm install
npm run dev
```

### Backend Development
```bash
cd server
pip install -r requirements.txt
python main.py
```

## Limitations (MVP)

- No user authentication system
- In-memory task storage (resets on restart)
- Basic error handling
- Single concurrent task per instance
- No task persistence across restarts

## Future Enhancements

- User authentication and session management
- Database persistence (Supabase integration planned)
- Multiple concurrent tasks
- GitHub App integration
- Advanced task scheduling
- Webhook support for repository events
- Task history and analytics

## Troubleshooting

### Common Issues

1. **Docker permission errors**: Ensure your user is in the docker group
2. **Port conflicts**: Change ports in docker-compose.yml if needed
3. **API key errors**: Verify your Anthropic API key is correctly set
4. **GitHub token issues**: Ensure token has proper repo permissions

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

## Contributing

This is an MVP implementation. For production use, consider implementing:
- Proper error handling and validation
- Security hardening
- Performance optimizations
- Comprehensive testing
- Monitoring and logging

## License

See LICENSE file for details.

