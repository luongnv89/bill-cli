"""Utility functions."""

import os
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def ensure_dir(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cache_dir(subdir: Optional[str] = None) -> Path:
    """Get cache directory for models/data."""
    base = get_project_root() / ".cache"
    if subdir:
        base = base / subdir
    ensure_dir(str(base))
    return base


def get_models_dir() -> Path:
    """Get models directory."""
    return get_cache_dir("models")


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    required = [
        "paddleocr",
        "paddlepaddle",
        "cv2",
        "PIL",
        "typer",
        "pydantic",
        "rich",
    ]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        return False
    return True


def print_status(message: str, success: bool = True) -> None:
    """Print colored status message."""
    from rich.console import Console
    from rich.theme import Theme

    theme = Theme({"success": "green", "error": "red"})
    console = Console(theme=theme)

    if success:
        console.print(f"[success]{message}[/success]")
    else:
        console.print(f"[error]{message}[/error]")


def format_amount(amount: float, currency: str = "USD") -> str:
    """Format amount for display."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def setup_logging(level: str = "INFO") -> None:
    """Setup basic logging."""
    import logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )