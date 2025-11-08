"""
Centralized logging configuration for the Kafka streaming lab.

This module provides consistent logging setup across all components,
ensuring uniform log formatting and levels throughout the application.
"""

import logging
import sys

# Single logger name for the entire application
LOGGER_NAME = "kafka_lab"

# Create formatter with file:line suffix
log_format = "%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"

formatter = logging.Formatter(
    fmt=log_format,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger(LOGGER_NAME)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)
logger.propagate = False
