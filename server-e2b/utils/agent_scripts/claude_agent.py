#!/usr/bin/env python3
"""
Claude Agent Script for E2B Sandbox Execution.

This script provides a Python-based interface to Claude for code generation tasks.
It uses the Anthropic Python SDK instead of the CLI for better control and security.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import anthropic
except ImportError:
    logger.error("Anthropic library not found. Please install it with: pip install anthropic")
    sys.exit(1)


class ClaudeAgent:
    """Handles Claude-based code generation tasks."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Configuration from environment variables
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", os.getenv("MAX_TOKENS", "4000")))
        self.temperature = float(os.getenv("CLAUDE_TEMPERATURE", os.getenv("TEMPERATURE", "0.7")))
        
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
            "languages": set(),
            "key_files": []
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
                        language_map = {
                            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                            '.java': 'java', '.cpp': 'c++', '.c': 'c', '.go': 'go',
                            '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.swift': 'swift'
                        }
                        if ext in language_map:
                            repo_info["languages"].add(language_map[ext])
                        
                        # Identify key files
                        key_patterns = ['readme', 'main', 'index', 'app', 'setup', 'requirements', 'package']
                        if any(pattern in file.lower() for pattern in key_patterns):
                            repo_info["key_files"].append(relative_path)
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, "/workspace/repo")
                    repo_info["directories"].append(relative_path)
        
        except Exception as e:
            logger.warning(f"Error analyzing repository: {e}")
        
        repo_info["languages"] = list(repo_info["languages"])
        return repo_info
    
    def read_key_files(self, repo_info: Dict) -> Dict[str, str]:
        """Read content of key files for better context."""
        file_contents = {}
        
        # Prioritize certain files
        priority_files = []
        for f in repo_info["key_files"][:5]:  # Limit to 5 key files
            if any(name in f.lower() for name in ['readme', 'requirements', 'package.json']):
                priority_files.insert(0, f)
            else:
                priority_files.append(f)
        
        for file_path in priority_files:
            try:
                full_path = os.path.join("/workspace/repo", file_path)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Limit content length
                    if len(content) > 1000:
                        content = content[:1000] + "\n... (truncated)"
                    file_contents[file_path] = content
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")
        
        return file_contents
    
    def generate_system_prompt(self, repo_info: Dict, file_contents: Dict) -> str:
        """Generate a system prompt with repository context."""
        languages = ", ".join(repo_info["languages"]) if repo_info["languages"] else "unknown"
        file_count = len(repo_info["files"])
        
        prompt = f"""You are Claude, an expert coding assistant working on a {languages} project.
The repository contains {file_count} files. You have full access to read and modify any file.

Your task is to implement the requested changes following these guidelines:
1. Write clean, idiomatic code that matches the existing style
2. Add appropriate error handling and validation
3. Include necessary imports and dependencies
4. Ensure backward compatibility unless breaking changes are explicitly requested
5. Add comments for complex logic
6. Follow the project's existing patterns and conventions

When making changes, clearly indicate:
- Which files to modify
- What changes to make
- Any new files to create

Format your response to make it easy to parse programmatically. Use markdown code blocks with file paths."""
        
        # Add key file contents for context
        if file_contents:
            prompt += "\n\nKey files in the repository:\n"
            for file_path, content in file_contents.items():
                prompt += f"\n--- {file_path} ---\n{content}\n"
        
        return prompt
    
    def execute_task(self, prompt: str) -> str:
        """Execute the code generation task using Claude."""
        try:
            # Analyze repository for context
            repo_info = self.analyze_repository()
            file_contents = self.read_key_files(repo_info)
            system_prompt = self.generate_system_prompt(repo_info, file_contents)
            
            # Add repository structure to user prompt
            enhanced_prompt = f"{prompt}\n\nRepository structure:\n"
            enhanced_prompt += f"Languages: {', '.join(repo_info['languages'])}\n"
            enhanced_prompt += f"Total files: {len(repo_info['files'])}\n"
            enhanced_prompt += f"Key directories: {', '.join(repo_info['directories'][:10])}\n"
            
            logger.info(f"Executing task with model: {self.model}")
            
            # Make API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ]
            )
            
            return message.content[0].text
            
        except anthropic.RateLimitError:
            logger.error("Anthropic API rate limit exceeded")
            return "Error: API rate limit exceeded. Please try again later."
        except anthropic.AuthenticationError:
            logger.error("Anthropic API authentication failed")
            return "Error: Invalid API key"
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return f"Error: {str(e)}"
    
    def parse_file_changes(self, response: str) -> List[Dict[str, str]]:
        """Parse Claude's response to extract file changes."""
        changes = []
        
        # Look for markdown code blocks with file paths
        # Pattern: ```language:path/to/file or ```path/to/file
        pattern = r'```(?:[\w]+:)?([\w/.-]+)\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for file_path, content in matches:
            changes.append({
                'path': file_path,
                'content': content.strip(),
                'action': 'create_or_update'
            })
        
        # Also look for explicit file instructions
        # Pattern: "Create file path/to/file:" or "Update file path/to/file:"
        instruction_pattern = r'(Create|Update|Modify)\s+file\s+([\w/.-]+):'
        instruction_matches = re.findall(instruction_pattern, response, re.IGNORECASE)
        
        for action, file_path in instruction_matches:
            if not any(c['path'] == file_path for c in changes):
                # Find the content after this instruction
                start_idx = response.find(f"{action} file {file_path}:")
                if start_idx != -1:
                    # Look for the next file instruction or code block
                    end_patterns = [
                        r'\n(Create|Update|Modify)\s+file',
                        r'\n```',
                        r'\n\n\n'  # Triple newline as section separator
                    ]
                    
                    end_idx = len(response)
                    for pattern in end_patterns:
                        match = re.search(pattern, response[start_idx:])
                        if match:
                            end_idx = min(end_idx, start_idx + match.start())
                    
                    content = response[start_idx:end_idx].split(':', 1)[1].strip()
                    changes.append({
                        'path': file_path,
                        'content': content,
                        'action': action.lower()
                    })
        
        return changes
    
    def apply_changes(self, response: str) -> bool:
        """
        Apply the changes suggested by Claude.
        Returns True if all changes were applied successfully, False otherwise.
        """
        logger.info("Parsing Claude's response for file changes...")
        
        changes = self.parse_file_changes(response)
        
        if not changes:
            logger.warning("No file changes detected in Claude's response")
            logger.info("Claude's response:")
            print(response)
            return True  # Not a failure - Claude might have provided instructions only
        
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
                
                # Write the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"✅ {action.capitalize()}d file: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to {action} {file_path}: {e}")
                errors += 1
        
        # Also print the full response for reference
        logger.info("\nFull Claude response:")
        print(response)
        
        if errors > 0:
            logger.error(f"Failed to apply {errors} out of {len(changes)} changes")
            return False
        
        return True


def main():
    """Main entry point for the Claude agent."""
    try:
        agent = ClaudeAgent()
        
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