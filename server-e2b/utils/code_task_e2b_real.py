"""
Real E2B implementation for AI code task execution.
This replaces the simulation with actual E2B sandboxes.
"""
import asyncio
import os
import time
import logging
import json
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
from e2b import Sandbox
from database import DatabaseOperations
from models import TaskStatus
import subprocess
from .async_runner import run_async_task
from .git_utils import parse_file_changes

logger = logging.getLogger(__name__)

class E2BCodeExecutor:
    """Handles AI code execution in E2B sandboxes"""
    
    # Timeout configurations (in seconds)
    SANDBOX_TIMEOUT = 600  # 10 minutes for sandbox lifetime
    CLONE_TIMEOUT = 60     # 1 minute for git clone
    AGENT_TIMEOUT = 300    # 5 minutes for AI agent execution
    COMMAND_TIMEOUT = 30   # 30 seconds for regular commands
    
    def __init__(self):
        self.api_key = os.getenv('E2B_API_KEY')
        if not self.api_key:
            raise ValueError("E2B_API_KEY not found in environment variables")
        
        # Use custom template if available (speeds up execution by pre-installing dependencies)
        self.template_id = os.getenv('E2B_TEMPLATE_ID')
    
    async def execute_task(self, task_id: int, user_id: str, github_token: str, 
                          repo_url: str, branch: str, prompt: str, agent: str) -> Dict:
        """
        Execute an AI coding task in an E2B sandbox.
        
        Args:
            task_id: Database task ID
            user_id: User ID for database updates
            github_token: GitHub personal access token
            repo_url: Repository URL to clone
            branch: Branch to work on
            prompt: Task prompt for the AI
            agent: AI agent to use ('claude' or 'codex')
            
        Returns:
            Dict with execution results
        """
        sandbox = None
        try:
            # Update task status
            DatabaseOperations.update_task(task_id, user_id, {"status": "running"})
            
            # Create E2B sandbox with appropriate template
            logger.info(f"🚀 Creating E2B sandbox for task {task_id}")
            if self.template_id:
                logger.info(f"🌟 Using custom template: {self.template_id}")
            
            try:
                # Prepare environment variables
                env_vars = {
                    "GITHUB_TOKEN": github_token,
                }
                if agent == "claude" and os.getenv("ANTHROPIC_API_KEY"):
                    env_vars["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
                elif agent == "codex" and os.getenv("OPENAI_API_KEY"):
                    env_vars["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
                
                # Create sandbox using the sync method with env vars
                sandbox_params = {
                    "api_key": self.api_key,
                    "timeout": self.SANDBOX_TIMEOUT,
                    "env_vars": env_vars  # Changed from 'envs' to 'env_vars'
                }
                
                # Add template if configured
                if self.template_id:
                    sandbox_params["template"] = self.template_id
                
                # Note: Sandbox() is synchronous, not async
                sandbox = Sandbox(**sandbox_params)
            except Exception as e:
                if "quota" in str(e).lower():
                    raise Exception("E2B sandbox quota exceeded. Please check your E2B account limits.")
                elif "api key" in str(e).lower():
                    raise Exception("Invalid E2B API key. Please check your E2B_API_KEY environment variable.")
                else:
                    raise Exception(f"Failed to create E2B sandbox: {str(e)}")
            
            # Clone repository
            logger.info(f"📦 Cloning repository: {repo_url}")
            
            # Add auth token to URL for private repos
            auth_repo_url = repo_url
            if "github.com" in repo_url and github_token:
                if repo_url.startswith("https://"):
                    auth_repo_url = repo_url.replace("https://", f"https://{github_token}@")
                elif repo_url.startswith("git@"):
                    auth_repo_url = repo_url.replace("git@github.com:", f"https://{github_token}@github.com/")
            
            try:
                clone_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        f"git clone -b {branch} {auth_repo_url} /workspace/repo"
                    ),
                    timeout=self.CLONE_TIMEOUT
                )
                
                if clone_result.exit_code != 0:
                    error_msg = clone_result.stderr or clone_result.stdout
                    if "authentication failed" in error_msg.lower():
                        raise Exception("GitHub authentication failed. Please check your GitHub token permissions.")
                    elif "not found" in error_msg.lower():
                        raise Exception(f"Repository not found or branch '{branch}' does not exist.")
                    else:
                        raise Exception(f"Failed to clone repository: {error_msg}")
                        
            except asyncio.TimeoutError:
                raise Exception(f"Git clone timed out after {self.CLONE_TIMEOUT} seconds. Repository might be too large.")
            
            # Configure git
            await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    "cd /workspace/repo && git config user.email 'ai-assistant@e2b.dev' && git config user.name 'AI Assistant'"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            # Record initial state
            initial_ls = await asyncio.to_thread(sandbox.process.start_and_wait, "ls -la /workspace/repo")
            
            # Execute AI agent based on type
            logger.info(f"🤖 Running {agent} agent with prompt: {prompt[:100]}...")
            
            if agent == "claude":
                result = await self._run_claude_agent(sandbox, prompt)
            elif agent == "codex":
                result = await self._run_codex_agent(sandbox, prompt)
            else:
                raise ValueError(f"Unknown agent type: {agent}")
            
            # Capture changes
            logger.info("📝 Capturing changes...")
            
            # Get git status
            status_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    "cd /workspace/repo && git status --porcelain"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            # Get git diff
            diff_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    "cd /workspace/repo && git diff"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            # Get list of changed files
            changed_files = []
            if status_result.stdout:
                for line in status_result.stdout.strip().split('\n'):
                    if line:
                        # Format: "M  file.py" or "A  newfile.py"
                        parts = line.strip().split(None, 1)
                        if len(parts) >= 2:
                            changed_files.append({
                                'status': parts[0],
                                'path': parts[1]
                            })
            
            # Get commit hash if we created a commit
            commit_hash = None
            
            # Create a commit if there are changes
            patch = ""
            if changed_files:
                # Stage all changes
                await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "cd /workspace/repo && git add -A"
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                
                # Create commit
                commit_message = f"AI: {prompt[:50]}..."
                commit_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        f'cd /workspace/repo && git commit -m "{commit_message}"'
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                
                # Get commit hash
                hash_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "cd /workspace/repo && git rev-parse HEAD"
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                commit_hash = hash_result.stdout.strip()
                
                # Generate patch
                patch_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "cd /workspace/repo && git format-patch -1 --stdout"
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                patch = patch_result.stdout
            
            # Prepare response
            execution_result = {
                'status': 'completed',
                'changes': changed_files,
                'patch': patch,
                'git_diff': diff_result.stdout,
                'agent_output': result['output'],
                'chat_messages': result.get('messages', [])
            }
            
            # Update database
            update_data = {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'commit_hash': commit_hash if 'commit_hash' in locals() else None,
                'git_diff': diff_result.stdout,
                'git_patch': patch,
                'changed_files': [f['path'] for f in changed_files]
            }
            
            # Process file changes for detailed diff view
            # Note: file_changes column doesn't exist in the database
            # The changed_files JSONB column is already being updated above
            
            # Add agent output as chat message
            if result.get('output'):
                DatabaseOperations.add_chat_message(
                    task_id,
                    user_id,
                    "assistant",
                    result['output']
                )
            
            DatabaseOperations.update_task(task_id, user_id, update_data)
            
            logger.info(f"✅ Task {task_id} completed successfully")
            return execution_result
            
        except asyncio.TimeoutError as e:
            error_msg = f"Task execution timed out. The operation took longer than expected."
            logger.error(f"⏱️ Task {task_id} timed out: {error_msg}")
            DatabaseOperations.update_task(task_id, user_id, {
                "status": "failed", 
                "error": error_msg
            })
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = str(e)
            # Sanitize error messages to avoid exposing sensitive information
            if github_token and github_token in error_msg:
                error_msg = error_msg.replace(github_token, "[REDACTED]")
            
            logger.error(f"❌ Task {task_id} failed: {error_msg}")
            DatabaseOperations.update_task(task_id, user_id, {
                "status": "failed", 
                "error": error_msg
            })
            raise
            
        finally:
            # Always close the sandbox
            if sandbox:
                try:
                    sandbox.close()  # close() is synchronous for Sandbox
                    logger.info(f"🧹 Cleaned up sandbox for task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to close sandbox: {e}")
    
    async def _run_claude_agent(self, sandbox: Sandbox, prompt: str) -> Dict:
        """Run Claude agent in the sandbox"""
        # Read the sophisticated agent script
        agent_script_path = os.path.join(
            os.path.dirname(__file__), 
            'agent_scripts', 
            'claude_agent.py'
        )
        
        # Use the sophisticated script if it exists, otherwise fall back to CLI
        if os.path.exists(agent_script_path):
            with open(agent_script_path, 'r') as f:
                script = f.read()
            
            # Write the script and prompt to sandbox
            await asyncio.to_thread(sandbox.filesystem.write, "/tmp/claude_agent.py", script)
            await asyncio.to_thread(sandbox.filesystem.write, "/tmp/agent_prompt.txt", prompt)
            
            try:
                # Check if anthropic is already installed (in custom template)
                check_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "python3 -c 'import anthropic'"
                    ),
                    timeout=5
                )
                
                # Only install if not found
                if check_result.exit_code != 0:
                    logger.info("📦 Installing Anthropic SDK...")
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            sandbox.process.start_and_wait,
                            "pip install anthropic"
                        ),
                        timeout=self.CLONE_TIMEOUT
                    )
                else:
                    logger.info("✅ Anthropic SDK already installed")
                
                # Run the Claude agent
                claude_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "cd /workspace/repo && python3 /tmp/claude_agent.py"
                    ),
                    timeout=self.AGENT_TIMEOUT
                )
                
                if claude_result.exit_code != 0:
                    raise Exception(f"Claude agent failed: {claude_result.stderr or 'Unknown error'}")
                    
            except asyncio.TimeoutError:
                raise Exception(f"Claude agent timed out after {self.AGENT_TIMEOUT} seconds")
            
            return {
                'output': claude_result.stdout,
                'messages': [
                    {'role': 'user', 'content': prompt},
                    {'role': 'assistant', 'content': claude_result.stdout}
                ]
            }
        
        else:
            # Fallback to CLI version
            try:
                # Check if Claude CLI is already installed (in custom template)
                check_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "which claude"
                    ),
                    timeout=5
                )
                
                # Only install if not found
                if check_result.exit_code != 0:
                    logger.info("📦 Installing Claude CLI...")
                    install_result = await asyncio.wait_for(
                        asyncio.to_thread(
                            sandbox.process.start_and_wait,
                            "npm install -g @anthropic-ai/claude-cli"
                        ),
                        timeout=self.CLONE_TIMEOUT
                    )
                else:
                    logger.info("✅ Claude CLI already installed")
                
                # Write prompt to file to avoid shell injection
                prompt_file = "/tmp/claude_prompt.txt"
                await asyncio.to_thread(sandbox.filesystem.write, prompt_file, prompt)
                
                # Run Claude with the prompt from file
                claude_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        f'cd /workspace/repo && claude < {prompt_file}'
                    ),
                    timeout=self.AGENT_TIMEOUT
                )
                
                if claude_result.exit_code != 0:
                    raise Exception(f"Claude agent failed: {claude_result.stderr or 'Unknown error'}")
                    
            except asyncio.TimeoutError:
                raise Exception(f"Claude agent timed out after {self.AGENT_TIMEOUT} seconds")
            
            return {
                'output': claude_result.stdout,
                'messages': [
                    {'role': 'user', 'content': prompt},
                    {'role': 'assistant', 'content': claude_result.stdout}
                ]
            }
    
    async def _run_codex_agent(self, sandbox: Sandbox, prompt: str) -> Dict:
        """Run Codex/GPT agent in the sandbox"""
        # Read the sophisticated agent script
        agent_script_path = os.path.join(
            os.path.dirname(__file__), 
            'agent_scripts', 
            'codex_agent.py'
        )
        
        # Use the sophisticated script if it exists, otherwise fall back to simple version
        if os.path.exists(agent_script_path):
            with open(agent_script_path, 'r') as f:
                script = f.read()
        else:
            # Fallback simple script
            script = f'''
import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {{"role": "system", "content": "You are a helpful coding assistant. Make the requested changes to the files in the current directory."}},
        {{"role": "user", "content": {json.dumps(prompt)}}}
    ]
)

print(response.choices[0].message.content)
'''
        
        # Write the script and prompt to sandbox
        await asyncio.to_thread(sandbox.filesystem.write, "/tmp/codex_agent.py", script)
        await asyncio.to_thread(sandbox.filesystem.write, "/tmp/agent_prompt.txt", prompt)
        
        try:
            # Check if OpenAI is already installed (in custom template)
            check_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    "python3 -c 'import openai'"
                ),
                timeout=5
            )
            
            # Only install if not found
            if check_result.exit_code != 0:
                logger.info("📦 Installing OpenAI SDK...")
                await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        "pip install openai"
                    ),
                    timeout=self.CLONE_TIMEOUT  # Use clone timeout for install
                )
            else:
                logger.info("✅ OpenAI SDK already installed")
            
            # Run the agent
            codex_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.process.start_and_wait,
                    "cd /workspace/repo && python /tmp/codex_agent.py"
                ),
                timeout=self.AGENT_TIMEOUT
            )
            
            if codex_result.exit_code != 0:
                raise Exception(f"Codex/GPT agent failed: {codex_result.stderr or 'Unknown error'}")
                
        except asyncio.TimeoutError:
            raise Exception(f"Codex/GPT agent timed out after {self.AGENT_TIMEOUT} seconds")
        
        return {
            'output': codex_result.stdout,
            'messages': [
                {'role': 'user', 'content': prompt},
                {'role': 'assistant', 'content': codex_result.stdout}
            ]
        }


# Sync wrapper for Flask integration
def run_ai_code_task_e2b(task_id: int, user_id: str, prompt: str, 
                         repo_url: str, branch: str, github_token: str, 
                         model: str = 'claude', project_id: Optional[int] = None):
    """
    Synchronous wrapper for Flask to call the async E2B executor.
    
    This function runs in a background thread and updates the database
    with progress and results.
    """
    try:
        # Create executor
        executor = E2BCodeExecutor()
        
        # Run async task using the async runner
        result = run_async_task(
            executor.execute_task,
            task_id=task_id,
            user_id=user_id,
            github_token=github_token,
            repo_url=repo_url,
            branch=branch,
            prompt=prompt,
            agent=model
        )
        
        logger.info(f"✅ E2B task {task_id} completed")
        
    except Exception as e:
        logger.error(f"❌ E2B task {task_id} failed: {str(e)}")
        DatabaseOperations.update_task(task_id, user_id, {"status": "failed", "error": str(e)})
        raise


