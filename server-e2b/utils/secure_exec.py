"""Secure command execution utilities."""

import shlex
import subprocess
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def safe_git_clone(repo_url: str, branch: str, target_dir: str) -> Tuple[int, str, str]:
    """
    Safely clone a git repository using subprocess with shell=False.
    
    Args:
        repo_url: The validated repository URL
        branch: The validated branch name
        target_dir: The target directory path
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Build command as a list for shell=False
    cmd = [
        'git', 'clone',
        '-b', branch,
        repo_url,
        target_dir
    ]
    
    logger.info(f"Executing git clone: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out after 5 minutes")
        return 1, "", "Git clone operation timed out"
    except Exception as e:
        logger.error(f"Error executing git clone: {e}")
        return 1, "", str(e)


def safe_git_config(config_key: str, config_value: str, repo_dir: str) -> Tuple[int, str, str]:
    """
    Safely set git configuration using subprocess with shell=False.
    
    Args:
        config_key: The git config key (e.g., 'user.email')
        config_value: The config value
        repo_dir: The repository directory
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Build command as a list
    cmd = ['git', 'config', config_key, config_value]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error setting git config: {e}")
        return 1, "", str(e)


def safe_git_commit(message: str, repo_dir: str) -> Tuple[int, str, str]:
    """
    Safely create a git commit using subprocess with shell=False.
    
    Args:
        message: The commit message (will be properly escaped)
        repo_dir: The repository directory
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Build command as a list - no need to escape when using shell=False
    cmd = ['git', 'commit', '-m', message]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error creating git commit: {e}")
        return 1, "", str(e)


def safe_git_command(git_args: List[str], repo_dir: str, timeout: int = 60) -> Tuple[int, str, str]:
    """
    Safely execute any git command using subprocess with shell=False.
    
    Args:
        git_args: List of git command arguments (e.g., ['diff', 'HEAD~1', 'HEAD'])
        repo_dir: The repository directory
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Build command starting with 'git'
    cmd = ['git'] + git_args
    
    logger.info(f"Executing git command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out after {timeout} seconds")
        return 1, "", f"Git command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error executing git command: {e}")
        return 1, "", str(e)


def create_safe_docker_script(
    repo_url: str,
    branch: str,
    prompt: str,
    model_cli: str,
    github_username: Optional[str] = None
) -> str:
    """
    Create a safe Docker container script with properly escaped values.
    
    Args:
        repo_url: Validated repository URL
        branch: Validated branch name
        prompt: User prompt (will be escaped)
        model_cli: Validated model CLI name ('claude' or 'codex')
        github_username: Optional GitHub username
        
    Returns:
        Safe shell script for Docker container execution
    """
    # Use shlex.quote for proper shell escaping
    safe_repo_url = shlex.quote(repo_url)
    safe_branch = shlex.quote(branch)
    safe_prompt = shlex.quote(prompt)
    safe_model = shlex.quote(model_cli)
    
    # Build script with properly escaped values
    script = f'''#!/bin/bash
set -e
echo "Setting up repository..."

# Clone repository with validated and escaped parameters
git clone -b {safe_branch} {safe_repo_url} /workspace/repo
cd /workspace/repo

# Configure git
git config user.email "claude-code@automation.com"
git config user.name "Claude Code Automation"

echo "📋 Will extract changes as patch for later PR creation..."
echo "Starting {safe_model.upper()} Code with prompt..."

# Create a temporary file with the prompt
echo {safe_prompt} > /tmp/prompt.txt

# Check which CLI tool to use based on model selection
if [ {safe_model} = "codex" ]; then
    echo "Using Codex (OpenAI Codex) CLI..."
    
    # Set environment variables for non-interactive mode
    export CODEX_QUIET_MODE=1
    
    # Run Codex with the prompt
    if command -v codex >/dev/null 2>&1; then
        codex < /tmp/prompt.txt
        CODEX_EXIT_CODE=$?
        echo "Codex finished with exit code: $CODEX_EXIT_CODE"
        
        if [ $CODEX_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Codex failed with exit code $CODEX_EXIT_CODE"
            exit $CODEX_EXIT_CODE
        fi
        
        echo "✅ Codex completed successfully"
    else
        echo "ERROR: codex command not found"
        exit 1
    fi
else
    echo "Using Claude CLI..."
    
    # Run Claude with the prompt
    if [ -f /usr/local/bin/claude ]; then
        # Use the official --print flag for non-interactive mode
        cat /tmp/prompt.txt | node /usr/local/bin/claude --print --allowedTools "Edit,Bash"
        CLAUDE_EXIT_CODE=$?
        echo "Claude Code finished with exit code: $CLAUDE_EXIT_CODE"
        
        if [ $CLAUDE_EXIT_CODE -ne 0 ]; then
            echo "ERROR: Claude Code failed with exit code $CLAUDE_EXIT_CODE"
            exit $CLAUDE_EXIT_CODE
        fi
        
        echo "✅ Claude Code completed successfully"
    else
        echo "ERROR: claude command not found"
        exit 1
    fi
fi

# Extract changes for PR creation
echo "🔍 Checking for changes..."
if git diff --quiet && git diff --cached --quiet; then
    echo "❌ No changes detected after running {safe_model}"
    exit 1
fi

# Stage all changes
echo "📝 Staging all changes..."
git add -A

# Create commit with safe message
echo "💾 Creating commit..."'''
    
    # Add commit message handling
    if github_username:
        safe_username = shlex.quote(github_username)
        commit_msg = f"{model_cli.capitalize()}: {prompt[:100]}"
        safe_commit_msg = shlex.quote(commit_msg)
        script += f'''
git commit -m {safe_commit_msg}
'''
    else:
        commit_msg = f"{model_cli.capitalize()}: Automated changes"
        safe_commit_msg = shlex.quote(commit_msg)
        script += f'''
git commit -m {safe_commit_msg}
'''
    
    script += '''
# Generate patch and diff information
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

# Get before/after content for merge view
echo "=== FILE CHANGES START ==="
for file in $(git diff --name-only HEAD~1 HEAD); do
    echo "FILE: $file"
    echo "=== BEFORE START ==="
    git show HEAD~1:"$file" 2>/dev/null || echo "FILE_NOT_EXISTS"
    echo "=== BEFORE END ==="
    echo "=== AFTER START ==="
    cat "$file" 2>/dev/null || echo "FILE_DELETED"
    echo "=== AFTER END ==="
    echo "=== FILE END ==="
done
echo "=== FILE CHANGES END ==="

# Exit successfully
echo "Container work completed successfully"
exit 0
'''
    
    return script