"""
Centralized logging configuration for the Learning Machine project.
"""
import logging
import sys
from pathlib import Path


def setup_logging(level=logging.INFO, log_file=None):
    """
    Set up logging configuration for the entire application.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path. If None, logs only to console.
    """
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels for external libraries
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create a default logger for convenience
default_logger = logging.getLogger('LearningMachine')
