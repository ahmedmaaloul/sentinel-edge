"""
Logging configuration for Sentinel-Edge.
Implements industrial-grade structured logging using loguru.
"""
import sys
from pathlib import Path
from loguru import logger

class SentinelLogger:
    """
    Wrapper around loguru to configure industrial-grade structured logging.
    Enforces JSON output for machine readability and robust file rotation.
    """

    def __init__(self, log_dir: str = "logs", app_name: str = "sentinel-edge"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.app_name = app_name
        self._configure_logger()

    def _configure_logger(self):
        """Configures the logger with standardized settings."""
        # Remove default handler
        logger.remove()

        # Add console handler (human-readable)
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )

        # Add file handler (structured JSON)
        # Rotation: 50 MB, Retention: 10 days, Compression: zip
        logger.add(
            self.log_dir / f"{self.app_name}.json",
            rotation="50 MB",
            retention="10 days",
            compression="zip",
            serialize=True,
            level="DEBUG",
            enqueue=True, # Thread-safe
            backtrace=True,
            diagnose=True
        )

    @staticmethod
    def get_logger():
        """Returns the configured logger instance."""
        return logger

# Global instance for easy import
sentinel_logger = SentinelLogger()
log = sentinel_logger.get_logger()
