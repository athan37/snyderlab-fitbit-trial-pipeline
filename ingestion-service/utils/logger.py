import logging
from typing import Optional
from config.settings import settings

class Logger:
    """Centralized logging utility for the ETL pipeline"""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with proper formatting"""
        if not self.logger.handlers:
            self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
            
            # Create console handler
            handler = logging.StreamHandler()
            handler.setLevel(getattr(logging, settings.LOG_LEVEL))
            
            # Create formatter
            formatter = logging.Formatter(settings.LOG_FORMAT)
            handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)

# Global logger instance
logger = Logger() 