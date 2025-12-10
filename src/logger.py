import logging
# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
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

def setup_logging(log_file: str = "agent_execution.log") -> logging.Logger:
    """Setup comprehensive logging for agent execution"""
    
    logger = logging.getLogger("SalesAnalystAgent")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file)
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
    
    return logger

from datetime import datetime
import os
os.makedirs("logs", exist_ok=True)
logger = setup_logging(f"logs/app_logs_{str(datetime.now()).replace("-", "_").replace(" ", "_").replace(":", "_").replace(".", "_")}.log")

