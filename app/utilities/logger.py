import logging
from logging.config import dictConfig


class LogConfig:
    """Logging configuration to be set for the application"""

    LOG_FORMAT = "%(levelname)s | %(asctime)s | %(name)s | %(message)s"
    LOG_FILE = "api_service.log"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(levelname)s | %(asctime)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": "INFO",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": LOG_FILE,
                "formatter": "detailed",
                "level": "INFO",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "api_service": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }


class AppLogger:
    """Custom logger to be used across the FastAPI application"""

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Returns a logger instance configured with the standard settings"""
        return logging.getLogger(name)


# Initialize the logger config
dictConfig(LogConfig.config)

# Create a reusable logger for the application
logger = AppLogger.get_logger("api_service")
