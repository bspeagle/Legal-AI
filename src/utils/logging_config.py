"""
Logging configuration for the Legal AI Virtual Courtroom application
"""
import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configure root logger
def setup_logging(log_file="app.log", log_level=logging.DEBUG):
    """
    Setup application logging with file and console handlers
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file_path = log_dir / log_file
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handlers
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Set levels
    file_handler.setLevel(log_level)
    console_handler.setLevel(log_level)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup
    root_logger.info("Logging initialized")
    
    return root_logger

def log_exception(logger, exc_info=None):
    """
    Log exception with full traceback
    
    Args:
        logger: Logger instance
        exc_info: Exception info tuple from sys.exc_info()
    """
    if exc_info is None:
        exc_info = sys.exc_info()
        
    if exc_info and exc_info[0]:
        logger.error(
            "Exception occurred: %s", 
            exc_info[1],
            exc_info=exc_info
        )
        
        # Log full traceback as separate lines for better readability
        tb_lines = traceback.format_exception(*exc_info)
        for line in tb_lines:
            for subline in line.splitlines():
                if subline.strip():
                    logger.debug("  %s", subline)
