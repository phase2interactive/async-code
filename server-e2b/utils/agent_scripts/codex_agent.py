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
    
    def apply_changes(self, instructions: str):
        """
        Parse the GPT response and apply file changes.
        This is a simple implementation - could be enhanced with
        better parsing of code blocks and file paths.
        """
        logger.info("Analyzing GPT response for file changes...")
        
        # This is a placeholder for more sophisticated parsing
        # In practice, you might want to:
        # 1. Parse markdown code blocks with file paths
        # 2. Use GPT to generate structured output (JSON)
        # 3. Implement a more robust change detection system
        
        # For now, we'll just log the instructions
        logger.info("GPT Response:")
        print(instructions)


def main():
    """Main entry point for the Codex agent."""
    try:
        agent = CodexAgent()
        
        # Read prompt
        prompt = agent.read_prompt()
        logger.info(f"Task prompt: {prompt[:100]}...")
        
        # Execute task
        result = agent.execute_task(prompt)
        
        # Apply changes (currently just prints)
        agent.apply_changes(result)
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()