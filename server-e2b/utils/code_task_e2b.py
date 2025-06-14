"""
E2B-based implementation of code task execution.
Replaces Docker containers with E2B sandboxes for AI agent execution.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import subprocess
import tempfile

from database import DatabaseOperations
from .git_utils import parse_file_changes

logger = logging.getLogger(__name__)

# Check if E2B is properly configured
try:
    if os.getenv('E2B_API_KEY'):
        # Use real E2B implementation if API key is available
        from .code_task_e2b_real import run_ai_code_task_e2b as _real_run_ai_code_task_e2b
        USE_REAL_E2B = True
        logger.info("✅ Using real E2B implementation")
    else:
        USE_REAL_E2B = False
        logger.warning("⚠️ E2B_API_KEY not found, using simulation mode")
except ImportError as e:
    USE_REAL_E2B = False
    logger.warning(f"⚠️ Could not import E2B: {e}, using simulation mode")


def run_ai_code_task_e2b(task_id: int, user_id: str, github_token: str, 
                        repo_url: str = None, branch: str = None, 
                        prompt: str = None, model: str = None, 
                        project_id: Optional[int] = None):
    """
    Execute a code task using E2B sandbox.
    Dispatches to real E2B implementation if available, otherwise uses simulation.
    """
    logger.info(f"Starting E2B execution for task {task_id}")
    
    try:
        # Get task data if not provided
        if not all([repo_url, branch, prompt, model]):
            task_data = DatabaseOperations.get_task_by_id(task_id, user_id)
            if not task_data:
                raise Exception(f"Task {task_id} not found")
            
            repo_url = repo_url or task_data["repo_url"]
            branch = branch or task_data.get("target_branch", "main")
            prompt = prompt or (task_data["chat_messages"][0]["content"] if task_data.get("chat_messages") else "")
            model = model or task_data.get("agent", "claude")
        
        # Use real E2B if available
        if USE_REAL_E2B:
            logger.info("🚀 Using real E2B implementation")
            return _real_run_ai_code_task_e2b(
                task_id=task_id,
                user_id=user_id,
                prompt=prompt,
                repo_url=repo_url,
                branch=branch,
                github_token=github_token,
                model=model,
                project_id=project_id
            )
        
        # Otherwise continue with simulation
        logger.info("🔧 Using simulation mode (set E2B_API_KEY to use real E2B)")
        
        # Update status to running
        DatabaseOperations.update_task(task_id, user_id, {"status": "running"})
        
        # Create temporary workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = os.path.join(temp_dir, "workspace")
            os.makedirs(workspace_dir)
            
            # Clone repository - use the parameters we have
            # (repo_url and branch are already set from parameters or task_data above)
            
            # Add auth token to URL for private repos
            if "github.com" in repo_url and github_token:
                if repo_url.startswith("https://"):
                    repo_url = repo_url.replace("https://", f"https://{github_token}@")
                elif repo_url.startswith("git@"):
                    repo_url = repo_url.replace("git@github.com:", f"https://{github_token}@github.com/")
            
            logger.info(f"Cloning repository: {repo_url} (branch: {branch})")
            
            # Clone the repository
            clone_result = subprocess.run(
                ["git", "clone", "-b", branch, repo_url, workspace_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            # Change to repo directory
            os.chdir(workspace_dir)
            
            # Configure git for commits
            subprocess.run(["git", "config", "user.name", "AI Assistant"], check=True)
            subprocess.run(["git", "config", "user.email", "ai@example.com"], check=True)
            
            # Use the prompt and model we already have from parameters
            # (prompt and model are already set from parameters or task_data above)
            agent = model
            
            logger.info(f"Executing {agent} agent with prompt: {prompt[:100]}...")
            
            # For now, simulate task execution by creating a simple change
            # In a real E2B implementation, this would call the actual AI agent
            result = simulate_ai_execution(workspace_dir, prompt, agent)
            
            # Process results
            if result["success"]:
                # Update task with results
                update_data = {
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "commit_hash": result.get("commit_hash"),
                    "git_diff": result.get("git_diff"),
                    "git_patch": result.get("git_patch"),
                    "changed_files": result.get("changed_files", [])
                }
                
                # Process file changes for detailed diff view
                # Note: file_changes column doesn't exist in the database
                # The changed_files JSONB column is already being updated above
                
                # Add agent output as chat message
                if result.get("output"):
                    DatabaseOperations.add_chat_message(
                        task_id,
                        user_id,
                        "assistant",
                        result["output"]
                    )
                
                DatabaseOperations.update_task(task_id, user_id, update_data)
                logger.info(f"Task {task_id} completed successfully")
            else:
                raise Exception(result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        DatabaseOperations.update_task(task_id, user_id, {
            "status": "failed",
            "error": str(e)
        })


def simulate_ai_execution(workspace_dir: str, prompt: str, agent: str) -> Dict[str, Any]:
    """
    Simulate AI execution for testing purposes.
    In a real implementation, this would call the actual AI agent via E2B.
    """
    try:
        # Create a simple test file to demonstrate functionality
        test_file = os.path.join(workspace_dir, "AI_GENERATED.md")
        with open(test_file, "w") as f:
            f.write(f"# AI Generated Content\n\n")
            f.write(f"Agent: {agent}\n")
            f.write(f"Prompt: {prompt}\n\n")
            f.write(f"This file was generated by the E2B backend simulation.\n")
            f.write(f"In a real implementation, this would contain actual AI-generated code.\n")
        
        # Git operations
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-m", f"AI: {prompt[:50]}..."], check=True)
        
        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = hash_result.stdout.strip()
        
        # Get diff
        diff_result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        git_diff = diff_result.stdout
        
        # Get patch
        patch_result = subprocess.run(
            ["git", "format-patch", "-1", "HEAD", "--stdout"],
            capture_output=True,
            text=True,
            check=True
        )
        git_patch = patch_result.stdout
        
        # Get changed files
        status_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = [f for f in status_result.stdout.strip().split('\n') if f]
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "git_diff": git_diff,
            "git_patch": git_patch,
            "changed_files": changed_files,
            "output": f"Simulated {agent} execution completed. Created test file: AI_GENERATED.md"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


