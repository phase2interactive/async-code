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

logger = logging.getLogger(__name__)


def run_ai_code_task_e2b(task_id: int, user_id: str, github_token: str):
    """
    Execute a code task using E2B sandbox.
    This is a simplified version that uses subprocess to run commands.
    """
    logger.info(f"Starting E2B execution for task {task_id}")
    
    try:
        # Get task data
        task_data = DatabaseOperations.get_task_by_id(task_id, user_id)
        if not task_data:
            raise Exception(f"Task {task_id} not found")
        
        # Update status to running
        DatabaseOperations.update_task(task_id, user_id, {"status": "running"})
        
        # Create temporary workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = os.path.join(temp_dir, "workspace")
            os.makedirs(workspace_dir)
            
            # Clone repository
            repo_url = task_data["repo_url"]
            branch = task_data.get("target_branch", "main")
            
            # Add auth token to URL for private repos
            if "github.com" in repo_url and github_token:
                if repo_url.startswith("https://"):
                    repo_url = repo_url.replace("https://", f"https://{github_token}@")
                elif repo_url.startswith("git@"):
                    repo_url = repo_url.replace("git@github.com:", f"https://{github_token}@github.com/")
            
            logger.info(f"Cloning repository: {task_data['repo_url']} (branch: {branch})")
            
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
            
            # Get the prompt
            prompt = task_data["chat_messages"][0]["content"] if task_data.get("chat_messages") else ""
            agent = task_data.get("agent", "claude")
            
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
                if result.get("git_diff"):
                    file_changes = parse_file_changes(result["git_diff"])
                    update_data["file_changes"] = file_changes
                
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


def parse_file_changes(git_diff: str) -> List[Dict[str, Any]]:
    """Parse git diff to extract individual file changes"""
    file_changes = []
    current_file = None
    before_lines = []
    after_lines = []
    in_diff = False
    
    for line in git_diff.split('\n'):
        if line.startswith('diff --git'):
            # Save previous file if exists
            if current_file:
                file_changes.append({
                    "path": current_file,
                    "before": '\n'.join(before_lines),
                    "after": '\n'.join(after_lines)
                })
            
            # Extract filename
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith('b/') else parts[3]
            before_lines = []
            after_lines = []
            in_diff = False
            
        elif line.startswith('@@'):
            in_diff = True
        elif in_diff and current_file:
            if line.startswith('-') and not line.startswith('---'):
                before_lines.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                after_lines.append(line[1:])
            elif not line.startswith('\\'):
                before_lines.append(line[1:] if line else '')
                after_lines.append(line[1:] if line else '')
    
    # Save last file
    if current_file:
        file_changes.append({
            "path": current_file,
            "before": '\n'.join(before_lines),
            "after": '\n'.join(after_lines)
        })
    
    return file_changes