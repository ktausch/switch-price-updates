"""Module with a function to get a logger useful inside AWS Lambda functions."""
import logging

DEFAULT_LOGGING_LEVEL: int = logging.INFO


def get_logger(name: str) -> logging.Logger:
    """Gets the logger for the file with the given name (usually __file__)."""
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOGGING_LEVEL)
    return logger
