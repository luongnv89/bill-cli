"""Tests for CLI main module - requires no external deps for basic tests."""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys

pytest_plugins = []


def test_cli_help(capsys):
    """Test --help output."""
    if "bill_extract.main" not in sys.modules:
        import importlib
        import bill_extract.main
        importlib.reload(bill_extract.main)
    from bill_extract.main import app
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "input" in result.stdout.lower()


def test_cli_requires_input():
    """Test that --input is required."""
    if "bill_extract.main" not in sys.modules:
        import importlib
        import bill_extract.main
        importlib.reload(bill_extract.main)
    from bill_extract.main import app
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 1


def test_collect_images():
    """Test collecting images from a folder."""
    from bill_extract.main import _collect_images
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        (folder / "invoice1.png").touch()
        (folder / "invoice2.jpg").touch()
        (folder / "readme.txt").touch()
        
        images = _collect_images(folder)
        assert len(images) == 2
        assert all(img.suffix.lower() in {".jpg", ".png"} for img in images)


def test_collect_no_images():
    """Test empty folder returns empty list."""
    from bill_extract.main import _collect_images
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        images = _collect_images(Path(tmpdir))
        assert images == []