import json
import os
import logging
import docker
import docker.types
import uuid
import time
from models import TaskStatus

from .container import cleanup_orphaned_containers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker client
docker_client = docker.from_env()

# Legacy in-memory task storage (for backward compatibility)
tasks = {}

# Simple persistence for tasks (save to file)
TASKS_FILE = 'tasks_backup.json'

def save_tasks():
    """Save tasks to file for persistence"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2, default=str)
        logger.info(f"💾 Saved {len(tasks)} tasks to {TASKS_FILE}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save tasks: {e}")

def load_tasks():
    """Load tasks from file"""
    global tasks
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                tasks = json.load(f)
            logger.info(f"📂 Loaded {len(tasks)} tasks from {TASKS_FILE}")
        else:
            logger.info(f"📂 No tasks file found, starting fresh")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load tasks: {e}")
        tasks = {}


# Load tasks on startup
load_tasks()

# Legacy function for backward compatibility
def run_ai_code_task(task_id):
    """Legacy function - should not be used with new Supabase system"""
    logger.warning(f"Legacy run_ai_code_task called for task {task_id} - this should be migrated to use run_ai_code_task_v2")
    
    try:
        # Check if task exists and get model type
        if task_id not in tasks:
            logger.error(f"Task {task_id} not found in tasks")
            return
            
        task = tasks[task_id]
        model_cli = task.get('model', 'claude')
        
        # With comprehensive sandboxing fixes, both Claude and Codex can now run in parallel
        logger.info(f"🚀 Running legacy {model_cli.upper()} task {task_id} directly in parallel mode")
        return _run_ai_code_task_internal(task_id)
            
    except Exception as e:
        logger.error(f"💥 Exception in run_ai_code_task: {str(e)}")
        if task_id in tasks:
            tasks[task_id]['status'] = TaskStatus.FAILED
            tasks[task_id]['error'] = str(e)

def _run_ai_code_task_internal(task_id):
    """Internal implementation of legacy AI Code automation - called directly for Claude or via queue for Codex"""
    try:
        task = tasks[task_id]
        task['status'] = TaskStatus.RUNNING
        
        model_name = task.get('model', 'claude').upper()
        logger.info(f"🚀 Starting {model_name} Code task {task_id}")
        logger.info(f"📋 Task details: prompt='{task['prompt'][:50]}...', repo={task['repo_url']}, branch={task['branch']}, model={model_name}")
        logger.info(f"Starting {model_name} task {task_id}")
        
        # Escape special characters in prompt for shell safety
        escaped_prompt = task['prompt'].replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        
        # Create container environment variables
        env_vars = {
            'CI': 'true',  # Indicate we're in CI/non-interactive environment
            'TERM': 'dumb',  # Use dumb terminal to avoid interactive features
            'NO_COLOR': '1',  # Disable colors for cleaner output
            'FORCE_COLOR': '0',  # Disable colors for cleaner output
            'NONINTERACTIVE': '1',  # Common flag for non-interactive mode
            'DEBIAN_FRONTEND': 'noninteractive',  # Non-interactive package installs
        }
        
        # Add model-specific API keys and environment variables
        model_cli = task.get('model', 'claude')
        if model_cli == 'claude':
            env_vars.update({
                'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
                'ANTHROPIC_NONINTERACTIVE': '1'  # Custom flag for Anthropic tools
            })
        elif model_cli == 'codex':
            env_vars.update({
                'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
                'OPENAI_NONINTERACTIVE': '1',  # Custom flag for OpenAI tools
                'CODEX_QUIET_MODE': '1'  # Official Codex non-interactive flag
            })
        
        # Use specialized container images based on model
        if model_cli == 'codex':
            container_image = 'codex-automation:latest'
        else:
            container_image = 'claude-code-automation:latest'
        
        # Create the command to run in container
        container_command = f'''
set -e
echo "Setting up repository..."

# Clone repository
git clone -b {task['branch']} {task['repo_url']} /workspace/repo
cd /workspace/repo

# Configure git
git config user.email "claude-code@automation.com"
git config user.name "Claude Code Automation"

# We'll extract the patch instead of pushing directly
echo "📋 Will extract changes as patch for later PR creation..."

echo "Starting {model_cli.upper()} Code with prompt..."

# Create a temporary file with the prompt
echo "{escaped_prompt}" > /tmp/prompt.txt

# Check which CLI tool to use based on model selection
if [ "{model_cli}" = "codex" ]; then
    echo "Using Codex (OpenAI Codex) CLI..."
    
    # Set environment variables for non-interactive mode
    export CODEX_QUIET_MODE=1
    
    # Debug: Verify environment variables are set
    echo "=== CODEX DEBUG INFO ==="
    echo "CODEX_QUIET_MODE: $CODEX_QUIET_MODE"
    echo "OPENAI_API_KEY: $(echo $OPENAI_API_KEY | head -c 8)..."
    echo "USING OFFICIAL CODEX FLAGS: --approval-mode full-auto --quiet for non-interactive operation"
    echo "======================="
    
    # Read the prompt from file
    PROMPT_TEXT=$(cat /tmp/prompt.txt)
    
    # Check for codex installation
    if [ -f /usr/local/bin/codex ]; then
        echo "Found codex at /usr/local/bin/codex"
        echo "Running Codex in non-interactive mode..."
        
        # Use official non-interactive flags for Docker environment
        # Using --approval-mode full-auto as per official Codex documentation
        /usr/local/bin/codex --approval-mode full-auto --quiet "$PROMPT_TEXT"
        CODEX_EXIT_CODE=$?
        echo "Codex finished with exit code: $CODEX_EXIT_CODE"
        
        if [ $CODEX_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Codex failed with exit code $CODEX_EXIT_CODE"
            exit $CODEX_EXIT_CODE
        fi
        
        echo "✅ Codex completed successfully"
    elif command -v codex >/dev/null 2>&1; then
        echo "Using codex from PATH..."
        echo "Running Codex in non-interactive mode..."
        
        # Use official non-interactive flags for Docker environment
        # Using --approval-mode full-auto as per official Codex documentation
        codex --approval-mode full-auto --quiet "$PROMPT_TEXT"
        CODEX_EXIT_CODE=$?
        echo "Codex finished with exit code: $CODEX_EXIT_CODE"
        
        if [ $CODEX_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Codex failed with exit code $CODEX_EXIT_CODE"
            exit $CODEX_EXIT_CODE
        fi
        
        echo "✅ Codex completed successfully"
    else
        echo "ERROR: codex command not found anywhere"
        echo "Please ensure Codex CLI is installed in the container"
        exit 1
    fi
    
else
    echo "Using Claude CLI..."
    
    # Try different ways to invoke claude
    echo "Checking claude installation..."

if [ -f /usr/local/bin/claude ]; then
    echo "Found claude at /usr/local/bin/claude"
    echo "File type:"
    file /usr/local/bin/claude || echo "file command not available"
    echo "First few lines:"
    head -5 /usr/local/bin/claude || echo "head command failed"
    
    # Check if it's a shell script
    if head -1 /usr/local/bin/claude | grep -q "#!/bin/sh\|#!/bin/bash\|#!/usr/bin/env bash"; then
        echo "Detected shell script, running with sh..."
        sh /usr/local/bin/claude < /tmp/prompt.txt
    # Check if it's a Node.js script (including env -S node pattern)
    elif head -1 /usr/local/bin/claude | grep -q "#!/usr/bin/env.*node\|#!/usr/bin/node"; then
        echo "Detected Node.js script..."
        if command -v node >/dev/null 2>&1; then
            echo "Running with node..."
            # Try different approaches for Claude CLI
            
            # First try with --help to see available options
            echo "Checking claude options..."
            node /usr/local/bin/claude --help 2>/dev/null || echo "Help not available"
            
            # Try non-interactive approaches
            echo "Attempting non-interactive execution..."
            
            # Method 1: Use the official --print flag for non-interactive mode
            echo "Using --print flag for non-interactive mode..."
            cat /tmp/prompt.txt | node /usr/local/bin/claude --print --allowedTools "Edit,Bash"
            CLAUDE_EXIT_CODE=$?
            echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
            
            if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
                echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
                exit $CLAUDE_EXIT_CODE
            fi
            
            echo "✅ Claude Code completed successfully"
        else
            echo "Node.js not found, trying direct execution..."
            /usr/local/bin/claude < /tmp/prompt.txt
            CLAUDE_EXIT_CODE=$?
            echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
            if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
                echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
                exit $CLAUDE_EXIT_CODE
            fi
            echo "✅ Claude Code completed successfully"
        fi
    # Check if it's a Python script
    elif head -1 /usr/local/bin/claude | grep -q "#!/usr/bin/env python\|#!/usr/bin/python"; then
        echo "Detected Python script..."
        if command -v python3 >/dev/null 2>&1; then
            echo "Running with python3..."
            python3 /usr/local/bin/claude < /tmp/prompt.txt
            CLAUDE_EXIT_CODE=$?
        elif command -v python >/dev/null 2>&1; then
            echo "Running with python..."
            python /usr/local/bin/claude < /tmp/prompt.txt
            CLAUDE_EXIT_CODE=$?
        else
            echo "Python not found, trying direct execution..."
            /usr/local/bin/claude < /tmp/prompt.txt
            CLAUDE_EXIT_CODE=$?
        fi
        echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
        if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
            exit $CLAUDE_EXIT_CODE
        fi
        echo "✅ Claude Code completed successfully"
    else
        echo "Unknown script type, trying direct execution..."
        /usr/local/bin/claude < /tmp/prompt.txt
        CLAUDE_EXIT_CODE=$?
        echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
        if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
            exit $CLAUDE_EXIT_CODE
        fi
        echo "✅ Claude Code completed successfully"
    fi
elif command -v claude >/dev/null 2>&1; then
    echo "Using claude from PATH..."
    CLAUDE_PATH=$(which claude)
    echo "Claude found at: $CLAUDE_PATH"
    claude < /tmp/prompt.txt
    CLAUDE_EXIT_CODE=$?
    echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
    if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
        echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
        exit $CLAUDE_EXIT_CODE
    fi
    echo "✅ Claude Code completed successfully"
else
    echo "ERROR: claude command not found anywhere"
    echo "Checking available interpreters:"
    which python3 2>/dev/null && echo "python3: available" || echo "python3: not found"
    which python 2>/dev/null && echo "python: available" || echo "python: not found"
    which node 2>/dev/null && echo "node: available" || echo "node: not found"
    which sh 2>/dev/null && echo "sh: available" || echo "sh: not found"
    exit 1
fi

fi  # End of model selection (claude vs codex)

# Check if there are changes
if git diff --quiet; then
    echo "ℹ️  No changes made by {model_cli.upper()} - this is a valid outcome"
    echo "The AI tool ran successfully but decided not to make changes"
    
    # Create empty patch and diff for consistency
    echo "=== PATCH START ==="
    echo "No changes were made"
    echo "=== PATCH END ==="
    
    echo "=== GIT DIFF START ==="
    echo "No changes were made"
    echo "=== GIT DIFF END ==="
    
    echo "=== CHANGED FILES START ==="
    echo "No files were changed"
    echo "=== CHANGED FILES END ==="
    
    # Set empty commit hash
    echo "COMMIT_HASH="
else
    # Commit changes locally
    git add .
    git commit -m "{model_cli.capitalize()}: {escaped_prompt[:100]}"

    # Get commit info
    COMMIT_HASH=$(git rev-parse HEAD)
    echo "COMMIT_HASH=$COMMIT_HASH"

    # Generate patch file for later application
    echo "📦 Generating patch file..."
    git format-patch HEAD~1 --stdout > /tmp/changes.patch
    echo "=== PATCH START ==="
    cat /tmp/changes.patch
    echo "=== PATCH END ==="

    # Also get the diff for display
    echo "=== GIT DIFF START ==="
    git diff HEAD~1 HEAD
    echo "=== GIT DIFF END ==="

    # List changed files for reference
    echo "=== CHANGED FILES START ==="
    git diff --name-only HEAD~1 HEAD
    echo "=== CHANGED FILES END ==="
fi

# Explicitly exit with success code
echo "Container work completed successfully"
exit 0
'''
        
        # Run container with unified AI Code tools (supports both Claude and Codex)
        logger.info(f"🐳 Creating Docker container for task {task_id} using {container_image} (model: {model_name})")
        
        # Configure Docker security options for Codex compatibility
        container_kwargs = {
            'image': container_image,
            'command': ['bash', '-c', container_command],
            'environment': env_vars,
            'detach': True,
            'remove': False,  # Don't auto-remove so we can get logs
            'working_dir': '/workspace',
            'network_mode': 'bridge',  # Ensure proper networking
            'tty': False,  # Don't allocate TTY - may prevent clean exit
            'stdin_open': False,  # Don't keep stdin open - may prevent clean exit
            'name': f'ai-code-task-{task_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}',  # Highly unique container name with UUID
            'mem_limit': '2g',  # Limit memory usage to prevent resource conflicts
            'cpu_shares': 1024,  # Standard CPU allocation
            'ulimits': [docker.types.Ulimit(name='nofile', soft=1024, hard=2048)]  # File descriptor limits
        }
        
        # Add security configurations for better isolation
        logger.info(f"🔒 Running {model_name} with secure container configuration")
        container_kwargs.update({
            # Security options for better isolation
            'security_opt': [
                'no-new-privileges=true'   # Prevent privilege escalation
            ],
            'read_only': False,            # Allow writes to workspace only
            'user': '1000:1000'           # Run as non-root user
        })
        
        # Retry container creation with enhanced conflict handling
        container = None
        max_retries = 5  # Increased retries for better reliability
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Container creation attempt {attempt + 1}/{max_retries}")
                container = docker_client.containers.run(**container_kwargs)
                logger.info(f"✅ Container created successfully: {container.id[:12]} (name: {container_kwargs['name']})")
                break
            except docker.errors.APIError as e:
                error_msg = str(e)
                if "Conflict" in error_msg and "already in use" in error_msg:
                    # Handle container name conflicts by generating a new unique name
                    logger.warning(f"🔄 Container name conflict on attempt {attempt + 1}, generating new name...")
                    new_name = f'ai-code-task-{task_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}'
                    container_kwargs['name'] = new_name
                    logger.info(f"🆔 New container name: {new_name}")
                    # Try to clean up any conflicting containers
                    cleanup_orphaned_containers()
                else:
                    logger.warning(f"⚠️  Docker API error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to create container after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"❌ Unexpected error creating container on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        task['container_id'] = container.id  # Legacy function
        logger.info(f"⏳ Waiting for container to complete (timeout: 300s)...")
        
        # Wait for container to finish - should exit naturally when script completes
        try:
            logger.info(f"🔄 Waiting for container script to complete naturally...")
            
            # Check initial container state
            container.reload()
            logger.info(f"🔍 Container initial state: {container.status}")
            
            # Use standard wait - container should exit when bash script finishes
            logger.info(f"🔄 Calling container.wait() - container should exit when script completes...")
            result = container.wait(timeout=300)  # 5 minute timeout
            logger.info(f"🎯 Container exited naturally! Exit code: {result['StatusCode']}")
            
            # Verify final container state
            container.reload()
            logger.info(f"🔍 Final container state: {container.status}")
            
            # Get logs before any cleanup operations
            logger.info(f"📜 Retrieving container logs...")
            try:
                logs = container.logs().decode('utf-8')
                logger.info(f"📝 Retrieved {len(logs)} characters of logs")
                logger.info(f"🔍 First 200 chars of logs: {logs[:200]}...")
            except Exception as log_error:
                logger.warning(f"❌ Failed to get container logs: {log_error}")
                logs = f"Failed to retrieve logs: {log_error}"
            
            # Clean up container after getting logs
            try:
                container.reload()  # Refresh container state
                container.remove()
                logger.info(f"Successfully removed container {container.id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to remove container {container.id}: {cleanup_error}")
                # Try force removal as fallback
                try:
                    container.remove(force=True)
                    logger.info(f"Force removed container {container.id}")
                except Exception as force_cleanup_error:
                    logger.error(f"Failed to force remove container: {force_cleanup_error}")
                
        except Exception as e:
            logger.error(f"⏰ Container timeout or error: {str(e)}")
            logger.error(f"🔄 Updating task status to FAILED due to timeout/error...")
            task['status'] = TaskStatus.FAILED
            task['error'] = f"Container execution timeout or error: {str(e)}"
            
            # Try to get logs even on error
            try:
                logs = container.logs().decode('utf-8')
            except Exception as log_error:
                logs = f"Container failed and logs unavailable: {log_error}"
            
            # Try to clean up container on error
            try:
                container.reload()  # Refresh container state
                container.remove(force=True)
                logger.info(f"Cleaned up failed container {container.id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to remove failed container {container.id}: {cleanup_error}")
            return
        
        if result['StatusCode'] == 0:
            logger.info(f"✅ Container exited successfully (code 0) - parsing results...")
            # Parse output to extract commit hash, diff, and patch
            lines = logs.split('\n')
            commit_hash = None
            git_diff = []
            git_patch = []
            changed_files = []
            capturing_diff = False
            capturing_patch = False
            capturing_files = False
            
            for line in lines:
                if line.startswith('COMMIT_HASH='):
                    commit_hash = line.split('=', 1)[1]
                    logger.info(f"🔑 Found commit hash: {commit_hash}")
                elif line == '=== PATCH START ===':
                    capturing_patch = True
                    logger.info(f"📦 Starting to capture git patch...")
                elif line == '=== PATCH END ===':
                    capturing_patch = False
                    logger.info(f"📦 Finished capturing git patch ({len(git_patch)} lines)")
                elif line == '=== GIT DIFF START ===':
                    capturing_diff = True
                    logger.info(f"📊 Starting to capture git diff...")
                elif line == '=== GIT DIFF END ===':
                    capturing_diff = False
                    logger.info(f"📊 Finished capturing git diff ({len(git_diff)} lines)")
                elif line == '=== CHANGED FILES START ===':
                    capturing_files = True
                    logger.info(f"📁 Starting to capture changed files...")
                elif line == '=== CHANGED FILES END ===':
                    capturing_files = False
                    logger.info(f"📁 Finished capturing changed files ({len(changed_files)} files)")
                elif capturing_patch:
                    git_patch.append(line)
                elif capturing_diff:
                    git_diff.append(line)
                elif capturing_files:
                    if line.strip():  # Only add non-empty lines
                        changed_files.append(line.strip())
            
            logger.info(f"🔄 Updating task status to COMPLETED...")
            task['status'] = TaskStatus.COMPLETED
            task['commit_hash'] = commit_hash
            task['git_diff'] = '\n'.join(git_diff)
            task['git_patch'] = '\n'.join(git_patch)
            task['changed_files'] = changed_files
            
            # Save tasks after completion
            save_tasks()
            
            logger.info(f"🎉 {model_name} Task {task_id} completed successfully! Commit: {commit_hash[:8] if commit_hash else 'N/A'}, Diff lines: {len(git_diff)}")
            
        else:
            logger.error(f"❌ Container exited with error code {result['StatusCode']}")
            task['status'] = TaskStatus.FAILED
            task['error'] = f"Container exited with code {result['StatusCode']}: {logs}"
            save_tasks()  # Save failed task
            logger.error(f"💥 {model_name} Task {task_id} failed: {task['error'][:200]}...")
            
    except Exception as e:
        model_name = task.get('model', 'claude').upper()
        logger.error(f"💥 Unexpected exception in {model_name} task {task_id}: {str(e)}")
        task['status'] = TaskStatus.FAILED
        task['error'] = str(e)
        logger.error(f"🔄 {model_name} Task {task_id} failed with exception: {str(e)}")
