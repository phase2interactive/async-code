import json
import os
import logging
import docker
import docker.types
import uuid
import time
from models import TaskStatus

from .container import cleanup_orphaned_containers
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_container_user_mapping, get_workspace_path, get_security_options, CONTAINER_UID, CONTAINER_GID
from utils.validators import TaskInputValidator
from utils.secure_exec import create_safe_docker_script

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
        
        # Validate inputs using Pydantic model
        try:
            validated_inputs = TaskInputValidator(
                task_id=str(task_id),
                repo_url=task['repo_url'],
                target_branch=task['branch'],
                prompt=task['prompt'],
                model=task.get('model', 'claude'),
                github_username=task.get('github_username')
            )
        except Exception as validation_error:
            error_msg = f"Input validation failed: {str(validation_error)}"
            logger.error(error_msg)
            task['status'] = TaskStatus.FAILED
            task['error'] = error_msg
            save_tasks()
            return
        
        logger.info(f"📋 Task details: prompt='{validated_inputs.prompt[:50]}...', repo={validated_inputs.repo_url}, branch={validated_inputs.target_branch}, model={model_name}")
        logger.info(f"Starting {model_name} task {task_id}")
        
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
        model_cli = validated_inputs.model
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
        
        # Ensure workspace permissions for non-root container execution
        workspace_path = get_workspace_path(task_id)
        try:
            os.makedirs(workspace_path, exist_ok=True)
            # Set ownership to configured UID/GID for container user
            os.chown(workspace_path, CONTAINER_UID, CONTAINER_GID)
            logger.info(f"🔧 Created workspace with proper permissions: {workspace_path} (UID:{CONTAINER_UID}, GID:{CONTAINER_GID})")
        except Exception as e:
            logger.warning(f"⚠️  Could not set workspace permissions: {e}")
        
        # Create the command to run in container using secure method
        container_command = create_safe_docker_script(
            repo_url=validated_inputs.repo_url,
            branch=validated_inputs.target_branch,
            prompt=validated_inputs.prompt,
            model_cli=validated_inputs.model,
            github_username=validated_inputs.github_username
        )
        
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
            'ulimits': [docker.types.Ulimit(name='nofile', soft=1024, hard=2048)],  # File descriptor limits
            'volumes': {
                workspace_path: {'bind': '/workspace/tmp', 'mode': 'rw'}  # Mount workspace with proper permissions
            }
        }
        
        # Add security configurations for better isolation
        logger.info(f"🔒 Running {model_name} with secure container configuration")
        container_kwargs.update({
            # Security options for better isolation
            'security_opt': get_security_options(),
            'read_only': False,            # Allow writes to workspace only
            'user': get_container_user_mapping()  # Run as configured non-root user
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
