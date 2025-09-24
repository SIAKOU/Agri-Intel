"""
Logging configuration
"""

import logging
import logging.config
import os
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[{asctime}] {levelname} in {name}: {message}",
                "style": "{",
            },
            "detailed": {
                "format": "[{asctime}] {levelname} {name}:{lineno} - {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Get logger instance
    logger = logging.getLogger("app")
    logger.info(f"Logging setup complete. Level: {settings.LOG_LEVEL}")
    
    return logger