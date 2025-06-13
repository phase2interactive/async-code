"""Input validation models for security."""

import re
from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict

# Regex patterns for validation
SAFE_BRANCH_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]+$')
SAFE_REPO_URL_PATTERN = re.compile(r'^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+\.git$')
SAFE_MODEL_PATTERN = re.compile(r'^(claude|codex)$')
SAFE_TASK_ID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
SAFE_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

# Maximum lengths to prevent injection attacks
MAX_BRANCH_LENGTH = 255
MAX_REPO_URL_LENGTH = 1000
MAX_PROMPT_LENGTH = 10000
MAX_USERNAME_LENGTH = 100


class TaskInputValidator(BaseModel):
    """Validates task creation and execution inputs."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    task_id: str
    repo_url: str
    target_branch: str
    prompt: str
    model: str
    github_username: Optional[str] = None
    github_token: Optional[str] = None
    
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID format (UUID)."""
        if not SAFE_TASK_ID_PATTERN.match(v):
            raise ValueError('Invalid task ID format. Must be a valid UUID.')
        return v
    
    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        """Validate GitHub repository URL."""
        if len(v) > MAX_REPO_URL_LENGTH:
            raise ValueError(f'Repository URL too long. Maximum {MAX_REPO_URL_LENGTH} characters.')
        
        # Ensure it's a valid GitHub URL
        if not SAFE_REPO_URL_PATTERN.match(v):
            raise ValueError(
                'Invalid repository URL. Must be https://github.com/owner/repo.git format. '
                'Only alphanumeric characters, dots, hyphens, and underscores allowed.'
            )
        return v
    
    @field_validator('target_branch')
    @classmethod
    def validate_branch(cls, v: str) -> str:
        """Validate branch name."""
        if len(v) > MAX_BRANCH_LENGTH:
            raise ValueError(f'Branch name too long. Maximum {MAX_BRANCH_LENGTH} characters.')
        
        # Check for potentially dangerous characters
        if not SAFE_BRANCH_PATTERN.match(v):
            raise ValueError(
                'Invalid branch name. Only alphanumeric characters, dots, underscores, '
                'hyphens, and forward slashes allowed.'
            )
        
        # Prevent path traversal
        if '..' in v or v.startswith('/') or v.startswith('~'):
            raise ValueError('Branch name cannot contain path traversal sequences.')
        
        return v
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt content."""
        if len(v) > MAX_PROMPT_LENGTH:
            raise ValueError(f'Prompt too long. Maximum {MAX_PROMPT_LENGTH} characters.')
        
        # Remove any null bytes which could cause issues
        v = v.replace('\x00', '')
        
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model selection."""
        if not SAFE_MODEL_PATTERN.match(v.lower()):
            raise ValueError('Invalid model. Must be either "claude" or "codex".')
        return v.lower()
    
    @field_validator('github_username')
    @classmethod
    def validate_github_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate GitHub username if provided."""
        if v is None:
            return v
            
        if len(v) > MAX_USERNAME_LENGTH:
            raise ValueError(f'Username too long. Maximum {MAX_USERNAME_LENGTH} characters.')
            
        if not SAFE_USERNAME_PATTERN.match(v):
            raise ValueError(
                'Invalid GitHub username. Only alphanumeric characters, dots, '
                'hyphens, and underscores allowed.'
            )
        return v


class GitHubIntegrationValidator(BaseModel):
    """Validates GitHub integration inputs."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    task_id: str
    base_branch: str
    pr_title: str
    pr_body: str
    
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID format (UUID)."""
        if not SAFE_TASK_ID_PATTERN.match(v):
            raise ValueError('Invalid task ID format. Must be a valid UUID.')
        return v
    
    @field_validator('base_branch')
    @classmethod
    def validate_base_branch(cls, v: str) -> str:
        """Validate base branch name."""
        if len(v) > MAX_BRANCH_LENGTH:
            raise ValueError(f'Branch name too long. Maximum {MAX_BRANCH_LENGTH} characters.')
        
        if not SAFE_BRANCH_PATTERN.match(v):
            raise ValueError(
                'Invalid branch name. Only alphanumeric characters, dots, underscores, '
                'hyphens, and forward slashes allowed.'
            )
        
        if '..' in v or v.startswith('/') or v.startswith('~'):
            raise ValueError('Branch name cannot contain path traversal sequences.')
        
        return v
    
    @field_validator('pr_title')
    @classmethod
    def validate_pr_title(cls, v: str) -> str:
        """Validate PR title."""
        # Remove any potentially dangerous characters
        v = re.sub(r'[^\w\s\-.,!?()]+', '', v)
        return v[:200]  # Limit title length
    
    @field_validator('pr_body')
    @classmethod
    def validate_pr_body(cls, v: str) -> str:
        """Validate PR body."""
        # Allow more characters in body but still sanitize
        return v[:5000]  # Limit body length