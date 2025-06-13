"""Configuration module for container security settings."""
# Import from centralized configuration
from env_config import Config

# Re-export container configuration for backward compatibility
CONTAINER_UID = Config.CONTAINER_UID
CONTAINER_GID = Config.CONTAINER_GID
CONTAINER_USER = Config.CONTAINER_USER
CONTAINER_SECURITY_OPTS = Config.CONTAINER_SECURITY_OPTS
CONTAINER_READ_ONLY = Config.CONTAINER_READ_ONLY
CONTAINER_MEM_LIMIT = Config.CONTAINER_MEM_LIMIT
CONTAINER_CPU_SHARES = Config.CONTAINER_CPU_SHARES
WORKSPACE_BASE_PATH = Config.WORKSPACE_BASE_PATH
WORKSPACE_PREFIX = Config.WORKSPACE_PREFIX

# Re-export functions for backward compatibility
get_container_user_mapping = Config.get_container_user_mapping
get_workspace_path = Config.get_workspace_path
get_security_options = Config.get_security_options