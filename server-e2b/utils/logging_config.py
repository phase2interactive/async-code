"""
Logging configuration for the E2B backend
"""

import logging
import sys


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up a logger with a standard configuration.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger