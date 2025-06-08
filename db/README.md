# Supabase Database Design

This document describes the database schema for the async-code project, built on Supabase.

## Overview

The database consists of three main tables:
- **`users`**: User profiles with auto-sync from Supabase Auth (UUID PK for RLS simplicity)
- **`projects`**: GitHub repositories managed by users (BIGSERIAL PK for performance)
- **`tasks`**: AI automation tasks with chat messages, git patches, and execution status (BIGSERIAL PK for performance)

### Primary Key Strategy

- **Users table**: Uses `UUID` to match Supabase Auth and simplify RLS policies (`auth.uid() = user_id`)
- **Projects & Tasks tables**: Use `BIGSERIAL` for optimal performance in joins, indexing, and frequent operations

## Table Schemas

### 1. Users Table (`public.users`)

Automatically synced with `auth.users` via database triggers.

```sql
CREATE TABLE public.users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  github_username TEXT,
  github_token TEXT, -- Encrypted GitHub token
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Features:**
- ✅ Auto-sync with Supabase Auth
- ✅ Row Level Security (RLS) enabled
- ✅ Users can only access their own data
- ✅ Secure GitHub token storage
- ✅ Extensible preferences via JSONB

### 2. Projects Table (`public.projects`)

Represents GitHub repositories managed by users.

```sql
CREATE TABLE public.projects (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  
  -- GitHub repository information
  repo_url TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  repo_owner TEXT NOT NULL,
  
  -- Project settings
  name TEXT NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  
  -- Custom settings (extensible)
  settings JSONB DEFAULT '{}',
  
  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Constraints
  UNIQUE(user_id, repo_url)
);
```

**Features:**
- ✅ One project per user per repository
- ✅ Branch selection is task-specific, not project-specific
- ✅ Extensible settings via JSONB
- ✅ Full RLS protection
- ✅ Auto-updated timestamps

### 3. Tasks Table (`public.tasks`)

Stores AI automation tasks with full execution history.

```sql
CREATE TABLE public.tasks (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  project_id BIGINT REFERENCES public.projects(id) ON DELETE CASCADE,
  
  -- Task information
  status task_status DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
  agent TEXT DEFAULT 'claude', -- AI agent name (flexible string)
  
  -- GitHub/Repository information
  repo_url TEXT,
  target_branch TEXT DEFAULT 'main', -- The branch we're targeting (e.g., 'main')
  pr_branch TEXT, -- The branch we created for the PR (e.g., 'feature/optimize-readme')
  
  -- Container and execution details
  container_id TEXT,
  
  -- Git workflow tracking
  commit_hash TEXT, -- Final commit hash
  pr_number INTEGER, -- Pull request number
  pr_url TEXT, -- Full PR URL
  
  -- Results and patches
  git_diff TEXT,
  git_patch TEXT,
  changed_files JSONB DEFAULT '[]',
  
  -- Error handling
  error TEXT,
  
  -- AI Chat Messages (stored as JSONB array)
  chat_messages JSONB DEFAULT '[]', -- Array of {role, content, timestamp} objects
  
  -- Execution metadata
  execution_metadata JSONB DEFAULT '{}', -- Store execution logs, timing, etc.
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE
);
```

**Features:**
- ✅ Complete task execution tracking with AI agents
- ✅ AI chat messages storage (no separate prompt field needed)
- ✅ Full Git workflow tracking (target branch, PR branch, PR number/URL)
- ✅ Git patch and diff storage
- ✅ Flexible metadata storage
- ✅ Comprehensive status tracking
- ✅ Flexible AI agent support (any string value)
- ✅ GitHub token from user settings (not per-task)

## Database Design

Clean and simple schema focusing on essential functionality:
- **Minimal indexes** for performance where needed
- **Flexible agent field** (TEXT instead of ENUM) 
- **User-level GitHub tokens** (not per-task)
- **Direct Supabase SDK usage** (no custom functions)

## Security (Row Level Security)

All tables have RLS enabled with policies ensuring users can only access their own data:

- **Users**: Can view and update own profile
- **Projects**: Full CRUD access to own projects only
- **Tasks**: Full CRUD access to own tasks only

## Indexes

Essential indexes only for optimal performance:

```sql
-- Essential indexes only
CREATE INDEX idx_projects_user_id ON public.projects(user_id);
CREATE INDEX idx_tasks_user_id ON public.tasks(user_id);
CREATE INDEX idx_tasks_project_id ON public.tasks(project_id);
CREATE INDEX idx_tasks_status ON public.tasks(status);
```

## Setup Instructions

### 1. Initialize Database

Run the SQL script in your Supabase dashboard:

```bash
# In Supabase SQL Editor, execute:
psql -f db/init_supabase.sql
```

### 2. Enable Authentication

Ensure you have authentication enabled in your Supabase project:

```javascript
// In your app
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'your-project-url',
  'your-anon-key'
)
```

### 3. Environment Variables

Set these environment variables:

```bash
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Data Migration

No migration functions needed - data will be handled through normal Supabase SDK operations during refactoring.

## Usage Examples

### Creating a Project

```javascript
const { data, error } = await supabase
  .from('projects')
  .insert({
    repo_url: 'https://github.com/user/repo',
    repo_name: 'repo',
    repo_owner: 'user',
    name: 'My Project',
    description: 'Project description'
  });
```

### Creating a Task

```javascript
// Create a task with initial chat message
const { data, error } = await supabase
  .from('tasks')
  .insert({
    project_id: projectId,
    repo_url: 'https://github.com/user/repo',
    target_branch: 'main',
    agent: 'claude',
    chat_messages: [
      {
        role: 'user',
        content: 'Optimize the README file',
        timestamp: Date.now() / 1000
      }
    ]
  });
```

### Querying Tasks

```javascript
// Get user tasks with filtering
const { data, error } = await supabase
  .from('tasks')
  .select(`
    *,
    projects (
      name,
      repo_name
    )
  `)
  .eq('status', 'completed')
  .order('created_at', { ascending: false })
  .limit(50);

// Get tasks by PR status
const { data: tasksWithPRs } = await supabase
  .from('tasks')
  .select('id, target_branch, pr_branch, pr_number, pr_url, status')
  .not('pr_number', 'is', null)
  .order('pr_number', { ascending: false });
```

### Updating Chat Messages

```javascript
// Update chat messages array directly
const { data, error } = await supabase
  .from('tasks')
  .update({
    chat_messages: [
      ...existingMessages,
      {
        role: 'assistant',
        content: 'I have optimized your README file with better structure.',
        timestamp: Date.now() / 1000
      }
    ]
  })
  .eq('id', taskId);
```

## Best Practices

1. **Use Supabase SDK** for all database operations
2. **Leverage JSONB fields** for flexible data storage (chat_messages, settings)
3. **Follow RLS policies** for automatic security
4. **Store GitHub tokens in user table** (not per-task)
5. **Keep schema simple** and add complexity only when needed

## Monitoring

Key metrics to monitor:

- Task completion rates by model
- Average execution time per task
- Error rates and patterns
- User activity and engagement
- Database performance and query times 