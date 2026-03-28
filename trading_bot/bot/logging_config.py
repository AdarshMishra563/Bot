import logging
import sys

def setup_logging(log_file="trading_bot.log"):
    """Configure structured logging for the application."""
    # Create logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times if instantiated again
    if logger.handlers:
        return logger

    # Log format: Time - Name - Level - Message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler - Logs everything (DEBUG and above)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # We will let Typer/Rich handle CLI outputs, but we can also add a stream handler for errors
    # Let's keep console logs minimal or disabled to avoid cluttering Typer UI, 
    # but we can optionally add it if needed. Standard approach is to log all API requests to file.
    logger.addHandler(file_handler)

    # Suppress verbose logs from third-party libraries (e.g., urllib3 used by requests)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger

logger = setup_logging()
