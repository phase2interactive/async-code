#!/usr/bin/env python3
"""
Codex/GPT Agent Script for E2B Sandbox Execution.

This script is uploaded to the E2B sandbox and executed to run GPT-based
code generation tasks. It reads configuration from environment variables
and the task prompt from a file.
"""
import os
import sys
import json
import logging
import re
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    logger.error("OpenAI library not found. Please install it with: pip install openai")
    sys.exit(1)


class CodexAgent:
    """Handles GPT-based code generation tasks."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Configure OpenAI
        openai.api_key = self.api_key
        
        # Configuration
        self.model = os.getenv("GPT_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
    def read_prompt(self, prompt_file: str = "/tmp/agent_prompt.txt") -> str:
        """Read the task prompt from a file."""
        try:
            with open(prompt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            raise
    
    def analyze_repository(self) -> Dict[str, List[str]]:
        """Analyze the repository structure to provide context."""
        repo_info = {
            "files": [],
            "directories": [],
            "languages": set()
        }
        
        try:
            for root, dirs, files in os.walk("/workspace/repo"):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, "/workspace/repo")
                        repo_info["files"].append(relative_path)
                        
                        # Detect language by extension
                        ext = os.path.splitext(file)[1].lower()
                        if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
                            repo_info["languages"].add(ext[1:])
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, "/workspace/repo")
                    repo_info["directories"].append(relative_path)
        
        except Exception as e:
            logger.warning(f"Error analyzing repository: {e}")
        
        repo_info["languages"] = list(repo_info["languages"])
        return repo_info
    
    def generate_system_prompt(self, repo_info: Dict) -> str:
        """Generate a system prompt with repository context."""
        languages = ", ".join(repo_info["languages"]) if repo_info["languages"] else "unknown"
        file_count = len(repo_info["files"])
        
        return f"""You are an expert coding assistant working on a {languages} project.
The repository contains {file_count} files. You have full access to read and modify any file.

Your task is to implement the requested changes following these guidelines:
1. Write clean, idiomatic code that matches the existing style
2. Add appropriate error handling and validation
3. Include necessary imports and dependencies
4. Ensure backward compatibility unless breaking changes are explicitly requested
5. Add comments for complex logic
6. Follow the project's existing patterns and conventions

After making changes, provide a clear summary of what was modified and why."""
    
    def execute_task(self, prompt: str) -> str:
        """Execute the code generation task using GPT."""
        try:
            # Analyze repository for context
            repo_info = self.analyze_repository()
            system_prompt = self.generate_system_prompt(repo_info)
            
            # Add file list to user prompt for better context
            enhanced_prompt = f"{prompt}\n\nRepository structure:\n"
            enhanced_prompt += f"Languages detected: {', '.join(repo_info['languages'])}\n"
            enhanced_prompt += f"Total files: {len(repo_info['files'])}\n"
            
            # Include some key files in context
            key_files = [f for f in repo_info['files'] 
                        if any(name in f.lower() for name in ['readme', 'package.json', 'requirements.txt', 'main', 'index'])]
            if key_files:
                enhanced_prompt += f"Key files: {', '.join(key_files[:5])}\n"
            
            logger.info(f"Executing task with model: {self.model}")
            
            # Make API call
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except openai.error.RateLimitError:
            logger.error("OpenAI API rate limit exceeded")
            return "Error: API rate limit exceeded. Please try again later."
        except openai.error.AuthenticationError:
            logger.error("OpenAI API authentication failed")
            return "Error: Invalid API key"
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return f"Error: {str(e)}"
    
    def parse_file_changes(self, response: str) -> List[Dict[str, str]]:
        """
        Parse GPT's response to extract file changes.
        Looks for various patterns that indicate file modifications.
        """
        changes = []
        
        # Pattern 1: Markdown code blocks with file paths
        # ```python:path/to/file.py or ```path/to/file.py
        pattern = r'```(?:[\w]+:)?([\w/.-]+)\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for file_path, content in matches:
            # Skip generic code blocks without clear file paths
            if '/' in file_path or file_path.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml')):
                changes.append({
                    'path': file_path,
                    'content': content.strip(),
                    'action': 'create_or_update'
                })
        
        # Pattern 2: Explicit file instructions
        # "Create/Update/Modify file path/to/file:"
        instruction_pattern = r'(Create|Update|Modify|Edit)\s+(?:the\s+)?file\s+([\w/.-]+)[:\s]'
        instruction_matches = re.findall(instruction_pattern, response, re.IGNORECASE)
        
        for action, file_path in instruction_matches:
            if not any(c['path'] == file_path for c in changes):
                # Find content after this instruction
                start_pattern = f"{action}.*?file\s+{re.escape(file_path)}"
                start_match = re.search(start_pattern, response, re.IGNORECASE)
                if start_match:
                    start_idx = start_match.end()
                    
                    # Look for the next file instruction, code block, or section
                    end_patterns = [
                        r'\n(?:Create|Update|Modify|Edit)\s+(?:the\s+)?file',
                        r'\n```',
                        r'\n\n#+\s',  # Markdown headers
                        r'\n\n\n'      # Triple newline
                    ]
                    
                    end_idx = len(response)
                    for pattern in end_patterns:
                        match = re.search(pattern, response[start_idx:])
                        if match:
                            end_idx = min(end_idx, start_idx + match.start())
                    
                    content = response[start_idx:end_idx].strip()
                    # Clean up common formatting
                    content = re.sub(r'^[:\s]+', '', content)
                    
                    if content:
                        changes.append({
                            'path': file_path,
                            'content': content,
                            'action': action.lower()
                        })
        
        # Pattern 3: File paths followed by code blocks
        # "In file.py:\n```python\ncode\n```"
        file_block_pattern = r'(?:In|File:|For)\s+([\w/.-]+)[:\s]*\n+```[\w]*\n(.*?)```'
        file_block_matches = re.findall(file_block_pattern, response, re.DOTALL)
        
        for file_path, content in file_block_matches:
            if not any(c['path'] == file_path for c in changes):
                changes.append({
                    'path': file_path,
                    'content': content.strip(),
                    'action': 'create_or_update'
                })
        
        return changes
    
    def apply_changes(self, instructions: str) -> bool:
        """
        Parse the GPT response and apply file changes.
        Returns True if all changes were applied successfully, False otherwise.
        """
        logger.info("Parsing GPT response for file changes...")
        
        changes = self.parse_file_changes(instructions)
        
        if not changes:
            logger.warning("No file changes detected in GPT's response")
            logger.info("GPT Response:")
            print(instructions)
            return True  # Not a failure - GPT might have provided instructions only
        
        logger.info(f"Found {len(changes)} file changes to apply")
        
        errors = 0
        for change in changes:
            file_path = change['path']
            content = change['content']
            action = change['action']
            
            # Ensure path is relative to repo root
            if not file_path.startswith('/'):
                file_path = f"/workspace/repo/{file_path}"
            elif not file_path.startswith('/workspace/repo/'):
                file_path = f"/workspace/repo{file_path}"
            
            try:
                # Create directory if needed
                dir_path = os.path.dirname(file_path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                
                # Check if file exists for update vs create
                file_exists = os.path.exists(file_path)
                
                # Write the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                if file_exists:
                    logger.info(f"✅ Updated file: {file_path}")
                else:
                    logger.info(f"✅ Created file: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to {action} {file_path}: {e}")
                errors += 1
        
        # Also print the full response for reference
        logger.info("\nFull GPT response:")
        print(instructions)
        
        if errors > 0:
            logger.error(f"Failed to apply {errors} out of {len(changes)} changes")
            return False
        
        return True


def main():
    """Main entry point for the Codex agent."""
    try:
        agent = CodexAgent()
        
        # Read prompt
        prompt = agent.read_prompt()
        logger.info(f"Task prompt: {prompt[:100]}...")
        
        # Execute task
        result = agent.execute_task(prompt)
        
        # Apply changes
        success = agent.apply_changes(result)
        
        if not success:
            logger.error("Failed to apply some changes")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()