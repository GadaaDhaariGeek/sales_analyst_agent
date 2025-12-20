"""
Comprehensive logging configuration for the Sales Analyst Agent.
Handles file and console logging with timestamps and color formatting.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.msg = f"{log_color}{record.getMessage()}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "SalesAnalystAgent",
    log_dir: str = "logs",
    log_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Setup comprehensive logging for the agent.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
        log_level: Logging level
    
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"agent_{timestamp}.log"
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized. File: {log_file}")
    
    return logger


def log_graph_execution(logger: logging.Logger, node_name: str, state: dict):
    """
    Log node execution with state information.
    
    Args:
        logger: Logger instance
        node_name: Name of the node being executed
        state: Current graph state
    """
    logger.debug(f"Executing node: {node_name}")
    logger.debug(f"State keys: {list(state.keys())}")
    if 'messages' in state:
        logger.debug(f"Message count: {len(state['messages'])}")


def log_tool_call(logger: logging.Logger, tool_name: str, tool_input: dict):
    """Log tool invocation"""
    logger.info(f"Calling tool: {tool_name}")
    logger.debug(f"Tool input: {tool_input}")


def log_tool_result(logger: logging.Logger, tool_name: str, result: str):
    """Log tool result"""
    logger.info(f"Tool {tool_name} completed")
    logger.debug(f"Result length: {len(result)} characters")

# from datetime import datetime
# import os
# os.makedirs("logs", exist_ok=True)
# logger = setup_logging(f"logs/app_logs_{str(datetime.now()).replace("-", "_").replace(" ", "_").replace(":", "_").replace(".", "_")}.log")



