"""
Logging configuration.
"""

import logging


def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("my_logger")

    return logger