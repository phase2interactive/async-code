"""
Utilities for E2B task execution.

This module provides the main entry point for executing AI code generation
tasks in E2B sandboxes. It exports the run_ai_code_task_e2b function which
handles task execution with automatic fallback between real E2B sandboxes
and local simulation mode.

The module configures logging and provides a clean interface for the Flask
application to execute background tasks.
"""
import logging

# Import E2B implementation
from .code_task_e2b import run_ai_code_task_e2b

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: The codex_execution_queue has been removed as it's no longer needed with E2B.
# E2B sandboxes are isolated and can run concurrently without resource conflicts.
# If rate limiting is needed for API calls, it should be implemented at the API
# client level rather than queueing entire task executions.