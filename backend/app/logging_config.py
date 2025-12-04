import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_dir = "/logs/backend"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    general_log_file = os.path.join(log_dir, "general.log")
    api_log_file = os.path.join(log_dir, "api.log")

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # General File Handler
    general_handler = RotatingFileHandler(
        general_log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    general_handler.setFormatter(formatter)

    # API File Handler
    api_handler = RotatingFileHandler(
        api_log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    api_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger (for general logs)
    logger.addHandler(general_handler)
    logger.addHandler(console_handler)

    # Setup API Logger
    api_logger = logging.getLogger("api_logger")
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    api_logger.propagate = False  # Don't propagate to root logger

    # Uvicorn access logs - redirect to general log or keep separate?
    # User said "backend.log is too verbose", usually due to uvicorn access logs.
    # Let's keep uvicorn logs in general log but maybe reduce level or separate?
    # For now, keep them in general log as requested "more or less like current one"
    logging.getLogger("uvicorn.access").addHandler(general_handler)
    logging.getLogger("uvicorn.error").addHandler(general_handler)

    return logger
