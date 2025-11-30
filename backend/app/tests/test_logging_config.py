import pytest
import os
import logging
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock
from app.logging_config import setup_logging


def test_setup_logging():
    """Test logging configuration setup."""
    # Save original handlers
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    
    # Clear handlers for clean test
    for handler in original_handlers:
        root_logger.removeHandler(handler)
    
    try:
        # Use tempfile to avoid permission issues
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock file handler that uses StringIO
            mock_file_handler = logging.StreamHandler(StringIO())
            
            with patch("os.path.exists", return_value=True):
                with patch("os.makedirs"):
                    with patch("logging.handlers.RotatingFileHandler", return_value=mock_file_handler):
                        logger = setup_logging()
                        
                        assert logger is not None
                        assert len(logger.handlers) >= 2  # File and console handlers
    finally:
        # Restore original handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)


def test_setup_logging_creates_directory():
    """Test logging setup creates log directory if it doesn't exist."""
    # Save original handlers
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    
    # Clear handlers for clean test
    for handler in original_handlers:
        root_logger.removeHandler(handler)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_log_dir = os.path.join(tmpdir, "new_logs")
            
            # Ensure directory doesn't exist
            assert not os.path.exists(test_log_dir)
            
            # Create a mock file handler that uses StringIO
            mock_file_handler = logging.StreamHandler(StringIO())
            
            with patch("os.path.exists", return_value=False):
                with patch("os.makedirs") as mock_makedirs:
                    with patch("logging.handlers.RotatingFileHandler", return_value=mock_file_handler):
                        setup_logging()
                        
                        # Verify makedirs was called with the correct path
                        mock_makedirs.assert_called_once_with("/logs/backend", exist_ok=True)
    finally:
        # Restore original handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)

