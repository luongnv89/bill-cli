import json
from pathlib import Path

import pytest

# Test directories
SAMPLES_DIR = Path(__file__).parent / "samples"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


@pytest.fixture
def samples_dir():
    """Return path to sample invoice images directory."""
    return SAMPLES_DIR


@pytest.fixture
def snapshot_dir():
    """Ensure snapshot directory exists and return path."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    return SNAPSHOT_DIR


@pytest.fixture
def sample_images():
    """Get sorted list of sample invoice images."""
    return sorted(SAMPLES_DIR.glob("facture*.png"))


@pytest.fixture
def cli_runner():
    """Provide Typer CLI runner for testing."""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def bill_extract_app():
    """Import and return the main bill_extract app."""
    from bill_extract.main import app

    return app


def load_snapshot(name: str) -> dict | None:
    """Load a snapshot JSON file if it exists."""
    snapshot_file = SNAPSHOT_DIR / f"{name}.json"
    if snapshot_file.exists():
        with open(snapshot_file) as f:
            return json.load(f)
    return None


def save_snapshot(name: str, data: dict):
    """Save data to a snapshot JSON file."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    snapshot_file = SNAPSHOT_DIR / f"{name}.json"
    with open(snapshot_file, "w") as f:
        json.dump(data, f, indent=2)
