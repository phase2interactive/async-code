# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Always check the WORKFLOW.md file before starting a tast. 

## Common Development Commands

### Frontend (Next.js)
```bash
cd async-code-web
npm install                  # Install dependencies
npm run dev                  # Start development server with Turbopack
npm run build                # Build for production
npm run lint                 # Run ESLint
```

### Backend (Flask)
```bash
cd server
pip install -r requirements.txt  # Install dependencies
python main.py                   # Run development server
```

### Docker Operations
```bash
./build.sh                   # Build all Docker images and start services
docker-compose up            # Start all services
docker-compose logs -f       # View logs
docker-compose down          # Stop all services
```

### Testing APIs
```bash
./test-api.sh                # Test basic API endpoints
./test-model-selection.sh    # Test model selection functionality
```

### Testing the Application
**IMPORTANT: Always use Docker Compose for testing to ensure proper environment setup**
```bash
# Start all services for testing
docker-compose up            # Run in foreground to see logs
docker-compose up -d         # Run in background

# Stop all services after testing
docker-compose down

# View logs if running in background
docker-compose logs -f

# DO NOT manually start services with `python main.py` or `npm run dev` for testing
# This can cause port conflicts and permission issues
```

For test user implementation details, see: `docs/TEST_USER_RECOMMENDATIONS.md`

## Architecture Overview

This is a multi-agent code task management system with three main components:

### 1. Frontend (async-code-web/)
- **Tech Stack**: Next.js 15, TypeScript, TailwindCSS, Supabase Auth
- **Key Components**:
  - `/app/tasks/` - Task management UI
  - `/app/projects/` - Project organization
  - `/components/diff-viewer.tsx` - Code diff visualization using CodeMirror
  - `/contexts/auth-context.tsx` - Authentication state management
  - `/lib/api-service.ts` - Backend API communication
  - `/lib/supabase-service.ts` - Database operations

### 2. Backend API (server/)
- **Tech Stack**: Flask, Docker Python SDK, Supabase
- **Core Modules**:
  - `main.py` - Flask app with CORS configuration
  - `tasks.py` - Task creation and management endpoints
  - `projects.py` - Project management endpoints
  - `database.py` - Supabase database operations
  - `utils/code_task_v2.py` - Docker container orchestration for AI agents
  - `utils/container.py` - Container management utilities

### 3. Agent Execution
- **Containerized Agents**: Each AI task runs in an isolated Docker container
- **Supported Models**: Claude Code (`claude`) and Codex (`codex`)
- **Execution Flow**:
  1. Task created via API → stored in Supabase
  2. Container spawned with agent-specific image
  3. Git repository cloned into container
  4. AI agent executes task with prompts
  5. Results, patches, and chat history saved to database

## Key Technical Details

### Task Execution System
- Tasks run in isolated Docker containers with names like `ai-code-task-{uuid}`
- Container cleanup happens automatically for orphaned/stuck containers (>2 hours old)
- Each task maintains chat history, file changes, and git patches in the database

### Database Schema (Supabase)
- `tasks` - Stores task details, status, prompts, results
- `projects` - Groups tasks by repository/feature
- `users` - User authentication and preferences
- Row-level security (RLS) ensures users only see their own data

### API Authentication (JWT-based)
- Frontend sends JWT tokens in `Authorization: Bearer <token>` header
- Backend validates JWT tokens and verifies user existence
- Tokens expire after 1 hour, refresh tokens valid for 7 days
- Automatic token refresh handled by frontend auth context
- CORS configured for localhost:3000 and Vercel deployments
- Supabase handles initial user authentication via Auth UI

### Git Integration
- Automatic repository cloning with provided GitHub token
- Branch creation and management
- Commit creation with AI-generated changes
- Pull request generation support

## Environment Variables

### Frontend (.env)
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Backend (.env)
```
ANTHROPIC_API_KEY=your_anthropic_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
JWT_SECRET=your-very-secure-secret-key-minimum-32-chars
```

## Code Style
- Frontend: TypeScript with ESLint (some rules disabled in eslint.config.mjs)
- Backend: Python following PEP8
- Prettier configured with 4-space tabs and 160 character line width