"""Configuration module for container security settings."""
import os

# Container user configuration
CONTAINER_UID = int(os.getenv('CONTAINER_UID', '1000'))
CONTAINER_GID = int(os.getenv('CONTAINER_GID', '1000'))
CONTAINER_USER = f"{CONTAINER_UID}:{CONTAINER_GID}"

# Security configuration
CONTAINER_SECURITY_OPTS = ['no-new-privileges=true']
CONTAINER_READ_ONLY = False  # Set to True for read-only root filesystem
CONTAINER_MEM_LIMIT = os.getenv('CONTAINER_MEM_LIMIT', '2g')
CONTAINER_CPU_SHARES = int(os.getenv('CONTAINER_CPU_SHARES', '1024'))

# Workspace configuration
WORKSPACE_BASE_PATH = os.getenv('WORKSPACE_BASE_PATH', '/tmp')
WORKSPACE_PREFIX = 'ai-workspace-'

def get_container_user_mapping():
    """Get the user mapping for containers."""
    return CONTAINER_USER

def get_workspace_path(task_id):
    """Get the workspace path for a specific task."""
    return os.path.join(WORKSPACE_BASE_PATH, f"{WORKSPACE_PREFIX}{task_id}")

def get_security_options():
    """Get the security options for containers."""
    return CONTAINER_SECURITY_OPTS.copy()