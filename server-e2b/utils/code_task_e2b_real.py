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
    
    # Default workspace path
    WORKSPACE_PATH = "/home/user/workspace"
    
    def __init__(self):
        # Validate and load environment variables
        self._validate_environment()
        
        self.api_key = os.getenv('E2B_API_KEY')
        if not self.api_key:
            raise ValueError("E2B_API_KEY not found in environment variables")
        
        # Use custom template if available (speeds up execution by pre-installing dependencies)
        self.template_id = os.getenv('E2B_TEMPLATE_ID')
        
        # Load optional API keys
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        # Log environment configuration
        self._log_environment_info()
    
    def _validate_environment(self):
        """Validate required environment variables and configurations"""
        required_vars = ['E2B_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate optional but recommended variables
        optional_vars = {
            'ANTHROPIC_API_KEY': 'Required for Claude agent',
            'OPENAI_API_KEY': 'Required for Codex agent',
            'GITHUB_TOKEN': 'Required for private repositories',
            'E2B_TEMPLATE_ID': 'Speeds up sandbox creation'
        }
        
        for var, description in optional_vars.items():
            if not os.getenv(var):
                logger.warning(f"⚠️  {var} not set - {description}")
    
    def _log_environment_info(self):
        """Log environment configuration for debugging"""
        logger.info("🔧 E2B Environment Configuration:")
        logger.info(f"  - E2B API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        logger.info(f"  - Template ID: {self.template_id or 'Default (no custom template)'}")
        logger.info(f"  - Anthropic API Key: {'✅ Set' if self.anthropic_api_key else '❌ Missing'}")
        logger.info(f"  - OpenAI API Key: {'✅ Set' if self.openai_api_key else '❌ Missing'}")
        logger.info(f"  - GitHub Token: {'✅ Set' if self.github_token else '❌ Missing'}")
        logger.info(f"  - Timeouts: Sandbox={self.SANDBOX_TIMEOUT}s, Clone={self.CLONE_TIMEOUT}s, Agent={self.AGENT_TIMEOUT}s")
    
    def _sanitize_error_message(self, error_msg: str) -> str:
        """Remove sensitive information from error messages"""
        # List of sensitive values to redact
        sensitive_values = [
            self.api_key,
            self.anthropic_api_key,
            self.openai_api_key,
            self.github_token
        ]
        
        sanitized = error_msg
        for value in sensitive_values:
            if value and len(value) > 10:  # Only redact substantial values
                # Keep first 4 chars for debugging
                masked = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                sanitized = sanitized.replace(value, masked)
        
        return sanitized
    
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
            logger.info(f"  Repository: {repo_url}")
            logger.info(f"  Branch: {branch}")
            logger.info(f"  Agent: {agent}")
            
            if self.template_id:
                logger.info(f"🌟 Using custom template: {self.template_id}")
            else:
                logger.info("📦 Using default E2B template")
            
            try:
                # Prepare environment variables
                env_vars = {
                    "GITHUB_TOKEN": github_token or self.github_token or "",
                }
                
                # Add agent-specific API keys
                if agent == "claude":
                    if self.anthropic_api_key:
                        env_vars["ANTHROPIC_API_KEY"] = self.anthropic_api_key
                        logger.info("✅ Anthropic API key configured for Claude agent")
                    else:
                        logger.warning("⚠️  No Anthropic API key available for Claude agent")
                elif agent == "codex":
                    if self.openai_api_key:
                        env_vars["OPENAI_API_KEY"] = self.openai_api_key
                        logger.info("✅ OpenAI API key configured for Codex agent")
                    else:
                        logger.warning("⚠️  No OpenAI API key available for Codex agent")
                
                # Log sandbox environment (without exposing secrets)
                logger.info(f"🔐 Environment variables configured: {list(env_vars.keys())}")
                
                # Create sandbox using the sync method with env vars
                sandbox_params = {
                    "api_key": self.api_key,
                    "timeout": self.SANDBOX_TIMEOUT,
                    "envs": env_vars  # Use 'envs' for e2b v1.5.1
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
            
            # Create workspace directory in user's home
            logger.info("📁 Creating workspace directory...")
            workspace_path = self.WORKSPACE_PATH
            
            mkdir_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.commands.run,
                    f"mkdir -p {workspace_path}"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            if mkdir_result.exit_code != 0:
                raise Exception(f"Failed to create workspace directory: {mkdir_result.stderr}")
            
            logger.info(f"✅ Workspace directory ready at {workspace_path}")
            
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
                        sandbox.commands.run,
                        f"git clone -b {branch} {auth_repo_url} {self.WORKSPACE_PATH}/repo"
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
                    sandbox.commands.run,
                    f"cd {self.WORKSPACE_PATH}/repo && git config user.email 'ai-assistant@e2b.dev' && git config user.name 'AI Assistant'"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            # Record initial state
            initial_ls = await asyncio.to_thread(sandbox.commands.run, f"ls -la {self.WORKSPACE_PATH}/repo")
            
            # Execute AI agent based on type
            logger.info(f"🤖 Running {agent} agent...")
            logger.info(f"  Prompt preview: {prompt[:100]}...")
            logger.info(f"  Prompt length: {len(prompt)} characters")
            logger.info(f"  Working directory: {self.WORKSPACE_PATH}/repo")
            logger.info(f"  Timeout: {self.AGENT_TIMEOUT}s")
            
            agent_start_time = time.time()
            
            if agent == "claude":
                result = await self._run_claude_agent(sandbox, prompt)
            elif agent == "codex":
                result = await self._run_codex_agent(sandbox, prompt)
            else:
                raise ValueError(f"Unknown agent type: {agent}")
            
            agent_time = time.time() - agent_start_time
            logger.info(f"✅ Agent completed in {agent_time:.2f}s")
            
            # Capture changes
            logger.info("📝 Capturing changes made by AI agent...")
            
            # Get git status
            logger.debug("Getting git status...")
            status_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.commands.run,
                    f"cd {self.WORKSPACE_PATH}/repo && git status --porcelain"
                ),
                timeout=self.COMMAND_TIMEOUT
            )
            
            if status_result.stdout:
                logger.info(f"📁 Found {len(status_result.stdout.strip().split('\n'))} changed files")
            else:
                logger.info("📁 No files were changed")
            
            # Get git diff
            diff_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.commands.run,
                    f"cd {self.WORKSPACE_PATH}/repo && git diff"
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
                logger.info(f"💾 Creating git commit for {len(changed_files)} changed files...")
                
                # Stage all changes
                logger.debug("Staging all changes...")
                add_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f"cd {self.WORKSPACE_PATH}/repo && git add -A"
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                
                if add_result.exit_code != 0:
                    logger.warning(f"⚠️ Git add had issues: {add_result.stderr}")
                
                # Create commit
                commit_message = f"AI: {prompt[:50]}..."
                commit_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f'cd {self.WORKSPACE_PATH}/repo && git commit -m "{commit_message}"'
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                
                # Get commit hash
                hash_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f"cd {self.WORKSPACE_PATH}/repo && git rev-parse HEAD"
                    ),
                    timeout=self.COMMAND_TIMEOUT
                )
                commit_hash = hash_result.stdout.strip()
                
                # Generate patch
                patch_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f"cd {self.WORKSPACE_PATH}/repo && git format-patch -1 --stdout"
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
                    logger.info(f"🧹 Cleaning up sandbox for task {task_id}...")
                    sandbox.kill()  # kill() is the method in e2b v1.5.1
                    logger.info(f"✅ Sandbox cleaned up successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to close sandbox: {self._sanitize_error_message(str(e))}")
                    # Don't re-raise as we want to ensure other cleanup happens
    
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
            await asyncio.to_thread(sandbox.files.write, "/tmp/claude_agent.py", script)
            await asyncio.to_thread(sandbox.files.write, "/tmp/agent_prompt.txt", prompt)
            
            try:
                # Check if anthropic is already installed (in custom template)
                check_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        "python3 -c 'import anthropic'"
                    ),
                    timeout=5
                )
                
                # Only install if not found
                if check_result.exit_code != 0:
                    logger.info("📦 Installing Anthropic SDK...")
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            sandbox.commands.run,
                            "pip install anthropic"
                        ),
                        timeout=self.CLONE_TIMEOUT
                    )
                else:
                    logger.info("✅ Anthropic SDK already installed")
                
                # Run the Claude agent
                claude_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f"cd {self.WORKSPACE_PATH}/repo && WORKSPACE_PATH={self.WORKSPACE_PATH} python3 /tmp/claude_agent.py"
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
                        sandbox.commands.run,
                        "which claude"
                    ),
                    timeout=5
                )
                
                # Only install if not found
                if check_result.exit_code != 0:
                    logger.info("📦 Installing Claude CLI...")
                    install_result = await asyncio.wait_for(
                        asyncio.to_thread(
                            sandbox.commands.run,
                            "npm install -g @anthropic-ai/claude-cli"
                        ),
                        timeout=self.CLONE_TIMEOUT
                    )
                else:
                    logger.info("✅ Claude CLI already installed")
                
                # Write prompt to file to avoid shell injection
                prompt_file = "/tmp/claude_prompt.txt"
                await asyncio.to_thread(sandbox.files.write, prompt_file, prompt)
                
                # Run Claude with the prompt from file
                claude_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        f'cd {self.WORKSPACE_PATH}/repo && WORKSPACE_PATH={self.WORKSPACE_PATH} claude < {prompt_file}'
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
        await asyncio.to_thread(sandbox.files.write, "/tmp/codex_agent.py", script)
        await asyncio.to_thread(sandbox.files.write, "/tmp/agent_prompt.txt", prompt)
        
        try:
            # Check if OpenAI is already installed (in custom template)
            check_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.commands.run,
                    "python3 -c 'import openai'"
                ),
                timeout=5
            )
            
            # Only install if not found
            if check_result.exit_code != 0:
                logger.info("📦 Installing OpenAI SDK...")
                await asyncio.wait_for(
                    asyncio.to_thread(
                        sandbox.commands.run,
                        "pip install openai"
                    ),
                    timeout=self.CLONE_TIMEOUT  # Use clone timeout for install
                )
            else:
                logger.info("✅ OpenAI SDK already installed")
            
            # Run the agent
            codex_result = await asyncio.wait_for(
                asyncio.to_thread(
                    sandbox.commands.run,
                    f"cd {self.WORKSPACE_PATH}/repo && WORKSPACE_PATH={self.WORKSPACE_PATH} python /tmp/codex_agent.py"
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


