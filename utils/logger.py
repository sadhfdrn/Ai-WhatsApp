"""
Logging utility for WhatsApp AI Bot
Provides consistent logging configuration across the application
"""

import logging
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)8s | %(name)20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the record
        formatted = super().format(record)
        
        # Add emoji prefixes for better visibility
        emoji_map = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '💥'
        }
        
        if levelname in emoji_map:
            formatted = f"{emoji_map[levelname]} {formatted}"
        
        return formatted

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper

def log_async_function_call(func):
    """Decorator to log async function calls"""
    import asyncio
    
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Async {func.__name__} failed: {e}")
            raise
    
    return wrapper

class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(f"{self.__module__}.{self.__class__.__name__}")
        return self._logger

def configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise"""
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)

def setup_file_logger(log_file: str = "whatsapp_bot.log", max_bytes: int = 10485760, backup_count: int = 5):
    """
    Setup file logging with rotation
    
    Args:
        log_file: Path to log file
        max_bytes: Maximum size before rotation (default: 10MB)
        backup_count: Number of backup files to keep
    """
    from logging.handlers import RotatingFileHandler
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Set format (no colors for file)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)8s | %(name)20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

def log_system_info():
    """Log system information at startup"""
    import platform
    import sys
    import os
    
    logger = setup_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("🤖 WhatsApp AI Bot Starting Up")
    logger.info("=" * 60)
    logger.info(f"🐍 Python Version: {sys.version}")
    logger.info(f"💻 Platform: {platform.platform()}")
    logger.info(f"🏛️  Architecture: {platform.architecture()}")
    logger.info(f"📁 Working Directory: {os.getcwd()}")
    logger.info(f"🕐 Start Time: {datetime.now()}")
    logger.info("=" * 60)

def log_memory_usage():
    """Log current memory usage"""
    try:
        import psutil
        import os
        
        logger = setup_logger(__name__)
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        logger.info(f"💾 Memory Usage: {memory_info.rss / 1024 / 1024:.1f} MB RSS, {memory_info.vms / 1024 / 1024:.1f} MB VMS")
        
        # System memory
        system_memory = psutil.virtual_memory()
        logger.info(f"🖥️  System Memory: {system_memory.percent}% used ({system_memory.available / 1024 / 1024 / 1024:.1f} GB available)")
        
    except ImportError:
        logger = setup_logger(__name__)
        logger.debug("psutil not available for memory monitoring")
    except Exception as e:
        logger = setup_logger(__name__)
        logger.debug(f"Error getting memory info: {e}")

def create_performance_logger():
    """Create a performance-specific logger"""
    perf_logger = setup_logger("performance")
    return perf_logger

class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or setup_logger(__name__)
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"⏱️  Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - (self.start_time or 0)
        
        if exc_type is None:
            self.logger.info(f"✅ Completed: {self.operation_name} in {duration:.3f}s")
        else:
            self.logger.error(f"❌ Failed: {self.operation_name} after {duration:.3f}s - {exc_val}")

# Initialize third-party logger configuration
configure_third_party_loggers()
