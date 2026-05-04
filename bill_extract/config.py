"""Pattern configuration loading."""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml

from bill_extract.logging import get_logger

logger = get_logger(__name__)

DEFAULT_PATTERNS_PATH = Path(__file__).parent / "patterns.yaml"


def load_patterns(config_path: Optional[str] = None) -> dict:
    """Load regex patterns from YAML configuration.
    
    Args:
        config_path: Optional path to custom patterns YAML file.
                     If None, uses default patterns.
    
    Returns:
        Dictionary containing pattern configurations.
    """
    if config_path and Path(config_path).exists():
        logger.info(f"Loading custom patterns from: {config_path}")
        with open(config_path, "r") as f:
            patterns = yaml.safe_load(f)
        return patterns.get("patterns", {})
    
    if DEFAULT_PATTERNS_PATH.exists():
        logger.info("Loading default patterns")
        with open(DEFAULT_PATTERNS_PATH, "r") as f:
            patterns = yaml.safe_load(f)
        return patterns.get("patterns", {})
    
    logger.warning("No patterns configuration found, using empty patterns")
    return {}


def get_date_patterns(patterns: dict) -> list[dict]:
    """Get date patterns from configuration."""
    return patterns.get("date", [])


def get_amount_patterns(patterns: dict) -> list[dict]:
    """Get amount patterns from configuration."""
    return patterns.get("amount", [])


def get_id_patterns(patterns: dict) -> list[dict]:
    """Get ID patterns from configuration."""
    return patterns.get("id", [])