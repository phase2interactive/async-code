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
from parser_utils import parse_file_changes, normalize_file_path

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

You must respond with a JSON object containing:
- "summary": A brief description of changes made
- "file_operations": An array of file operations to perform

Each file operation must have:
- "action": One of "create", "update", or "delete"
- "path": The file path relative to repository root
- "content": The complete file content (for create/update actions)

Example response format:
{{
  "summary": "Added new feature X and updated tests",
  "file_operations": [
    {{
      "action": "create",
      "path": "src/feature.py",
      "content": "import os\n\ndef new_feature():\n    pass"
    }},
    {{
      "action": "update",
      "path": "tests/test_feature.py",
      "content": "import pytest\n..."
    }}
  ]
}}"""
    
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
            
            # Define the function schema for structured output
            functions = [
                {
                    "name": "apply_code_changes",
                    "description": "Apply code changes to the repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Brief description of changes made"
                            },
                            "file_operations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "action": {
                                            "type": "string",
                                            "enum": ["create", "update", "delete"],
                                            "description": "The operation to perform"
                                        },
                                        "path": {
                                            "type": "string",
                                            "description": "File path relative to repository root"
                                        },
                                        "content": {
                                            "type": "string",
                                            "description": "Complete file content (required for create/update)"
                                        }
                                    },
                                    "required": ["action", "path"],
                                    "additionalProperties": False
                                },
                                "description": "List of file operations to perform"
                            }
                        },
                        "required": ["summary", "file_operations"],
                        "additionalProperties": False
                    }
                }
            ]
            
            # Make API call with function calling
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                functions=functions,
                function_call={"name": "apply_code_changes"},
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract the function call arguments
            if response.choices[0].message.get("function_call"):
                return response.choices[0].message.function_call.arguments
            else:
                # Fallback to regular content if no function call
                return response.choices[0].message.content
            
        except openai.error.RateLimitError:
            logger.error("OpenAI API rate limit exceeded")
            return json.dumps({
                "summary": "Error: API rate limit exceeded. Please try again later.",
                "file_operations": []
            })
        except openai.error.AuthenticationError:
            logger.error("OpenAI API authentication failed")
            return json.dumps({
                "summary": "Error: Invalid API key",
                "file_operations": []
            })
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return json.dumps({
                "summary": f"Error: {str(e)}",
                "file_operations": []
            })
    
    def apply_changes(self, response: str) -> bool:
        """
        Parse the GPT response and apply file changes.
        Returns True if all changes were applied successfully, False otherwise.
        """
        logger.info("Parsing GPT response...")
        
        try:
            # Parse JSON response
            data = json.loads(response)
            
            if "file_operations" not in data:
                logger.error("Response missing 'file_operations' field")
                return False
            
            logger.info(f"Found structured output with {len(data['file_operations'])} operations")
            changes = data["file_operations"]
            
            # Print summary for orchestrator
            if "summary" in data:
                print(f"Summary: {data['summary']}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            print(f"Error: Invalid JSON response from GPT")
            return False
        
        if not changes:
            logger.warning("No file changes detected in GPT's response")
            return True  # Not a failure - GPT might have provided instructions only
        
        logger.info(f"Applying {len(changes)} file changes...")
        
        errors = 0
        for change in changes:
            # Handle both structured and regex-parsed formats
            if isinstance(change, dict):
                file_path = change.get('path', '')
                content = change.get('content', '')
                action = change.get('action', 'update')
            else:
                # Shouldn't happen, but be defensive
                logger.error(f"Invalid change format: {change}")
                errors += 1
                continue
            
            # Normalize path
            file_path = normalize_file_path(file_path)
            
            try:
                if action == 'delete':
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"✅ Deleted file: {file_path}")
                    else:
                        logger.warning(f"File to delete not found: {file_path}")
                else:
                    # Create or update
                    if not content and action in ['create', 'update']:
                        logger.error(f"No content provided for {action} operation on {file_path}")
                        errors += 1
                        continue
                    
                    # Create directory if needed
                    dir_path = os.path.dirname(file_path)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        logger.info(f"Created directory: {dir_path}")
                    
                    # Check if file exists
                    file_exists = os.path.exists(file_path)
                    
                    # Write the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    if action == 'create' or not file_exists:
                        logger.info(f"✅ Created file: {file_path}")
                    else:
                        logger.info(f"✅ Updated file: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to {action} {file_path}: {e}")
                errors += 1
        
        if errors > 0:
            logger.error(f"Failed to apply {errors} out of {len(changes)} changes")
            return False
        
        logger.info("✅ All changes applied successfully")
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