"""Tests for logging and progress functionality."""

import logging
from unittest.mock import patch, Mock

import pytest
from rich.logging import RichHandler


class TestLogging:
    """Test logging configuration."""

    def test_setup_logging_returns_logger(self):
        """Test setup_logging returns a logger."""
        from bill_extract.logging import setup_logging, get_logger
        
        logger = setup_logging("INFO")
        assert logger is not None
        assert logger.name == "bill_extract"

    def test_setup_logging_sets_level(self):
        """Test logging level is set correctly."""
        from bill_extract.logging import setup_logging
        
        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG
        
        logger = setup_logging("ERROR")
        assert logger.level == logging.ERROR

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger."""
        from bill_extract.logging import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_rich_handler_configured(self):
        """Test RichHandler is configured."""
        from bill_extract.logging import setup_logging
        
        logger = setup_logging("INFO")
        
        handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
        assert len(handlers) > 0


class TestOCRFirstLoad:
    """Test OCR first-load flag."""

    def test_first_load_flag_exists(self):
        """Test FIRST_LOAD flag exists."""
        from bill_extract.ocr import FIRST_LOAD
        assert FIRST_LOAD is True

    def test_first_load_can_be_imported(self):
        """Test FIRST_LOAD can be imported."""
        from bill_extract.ocr import FIRST_LOAD as FL
        assert FL is True


class TestProgress:
    """Test progress bar functionality."""

    def test_progress_columns_imported(self):
        """Test progress columns are imported."""
        from rich.progress import (
            Progress,
            SpinnerColumn,
            TextColumn,
            BarColumn,
            TaskProgressColumn,
        )
        assert Progress is not None
        assert SpinnerColumn is not None
        assert TextColumn is not None
        assert BarColumn is not None
        assert TaskProgressColumn is not None