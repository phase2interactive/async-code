# Environment Variables Configuration

This document describes all environment variables used in the async-code application and their purposes.

## Required Environment Variables

These environment variables MUST be set for the application to start:

### Database Configuration
- `SUPABASE_URL` - The URL of your Supabase instance
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for server-side Supabase operations
- `DATABASE_URL` - PostgreSQL connection string (optional if using Supabase)

### Authentication
- `JWT_SECRET` - Secret key for signing JWT tokens (minimum 32 characters recommended)

## Optional Environment Variables

These variables have default values but can be customized:

### JWT Configuration
- `JWT_ALGORITHM` - Algorithm for JWT signing (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiration in minutes (default: `60`)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration in days (default: `7`)

### API Keys
- `ANTHROPIC_API_KEY` - API key for Claude AI integration
- `OPENAI_API_KEY` - API key for OpenAI integration
- `GOOGLE_API_KEY` - API key for Google AI integration

### Container Configuration
- `CONTAINER_UID` - User ID for container processes (default: `1000`)
- `CONTAINER_GID` - Group ID for container processes (default: `1000`)
- `CONTAINER_MEM_LIMIT` - Memory limit for containers (default: `2g`)
- `CONTAINER_CPU_SHARES` - CPU shares for containers (default: `1024`)
- `CONTAINER_READ_ONLY` - Enable read-only root filesystem (default: `false`)

### Workspace Configuration
- `WORKSPACE_BASE_PATH` - Base path for task workspaces (default: `/tmp`)

### Application Configuration
- `FLASK_ENV` - Flask environment (default: `production`)
- `DEBUG` - Enable debug mode (default: `false`)
- `PORT` - Port for the Flask server (default: `5000`)

## Setting Environment Variables

### Using .env File (Development)

Create a `.env` file in the server directory:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET=your-very-secure-secret-key-minimum-32-chars

# Optional API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key

# Optional Configuration
DEBUG=true
FLASK_ENV=development
```

### Using Docker Compose

Environment variables can be set in `docker-compose.yml`:

```yaml
services:
  server:
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

Or reference an env file:

```yaml
services:
  server:
    env_file:
      - .env
```

### Using System Environment Variables

Export variables in your shell:

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
export JWT_SECRET=your-very-secure-secret-key-minimum-32-chars
```

## Security Best Practices

1. **Never commit secrets to version control**
   - Add `.env` to `.gitignore`
   - Use `.env.example` to document required variables without values

2. **Use strong secrets**
   - JWT_SECRET should be at least 32 characters
   - Use cryptographically secure random generators

3. **Rotate secrets regularly**
   - Change JWT_SECRET periodically
   - Update API keys when team members change

4. **Use environment-specific values**
   - Different secrets for development, staging, and production
   - Never use production secrets in development

5. **Limit secret access**
   - Use service role keys only on the server
   - Keep anon keys for client-side usage

## Troubleshooting

### Missing Required Variables

If you see an error like:
```
ValueError: Missing required environment variables: JWT_SECRET, SUPABASE_URL
```

Ensure all required variables are set in your environment or `.env` file.

### Invalid JWT_SECRET

If authentication fails with JWT errors, ensure:
- JWT_SECRET is set and matches across all services
- The secret hasn't been changed after tokens were issued
- The secret is properly escaped if it contains special characters

### Container Permission Issues

If containers fail with permission errors:
- Check CONTAINER_UID and CONTAINER_GID match your system
- Ensure workspace paths have appropriate permissions
- Try setting CONTAINER_READ_ONLY=false for debugging