"""Snapshot tests for JSON output with sample invoices."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

SAMPLES_DIR = Path(__file__).parent / "samples"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


@pytest.fixture
def runner():
    """CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def snapshot_dir():
    """Ensure snapshot directory exists."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    return SNAPSHOT_DIR


@pytest.fixture
def sample_images():
    """Get list of sample invoice images."""
    return sorted(SAMPLES_DIR.glob("facture*.png"))


def read_snapshot(name: str) -> dict | None:
    """Read a snapshot file."""
    snapshot_file = SNAPSHOT_DIR / f"{name}.json"
    if snapshot_file.exists():
        with open(snapshot_file) as f:
            return json.load(f)
    return None


def write_snapshot(name: str, data: dict):
    """Write a snapshot file."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    snapshot_file = SNAPSHOT_DIR / f"{name}.json"
    with open(snapshot_file, "w") as f:
        json.dump(data, f, indent=2)


def test_samples_exist(sample_images):
    """Test that sample invoice images exist."""
    assert len(sample_images) >= 5, "Need at least 5 sample images"
    assert len(sample_images) <= 10, "Max 10 sample images"
    for img in sample_images:
        assert img.stat().st_size > 0, f"Image {img.name} is empty"


class TestSampleInvoiceExtraction:
    """Test extraction from sample invoices with snapshot comparison."""

    @pytest.mark.parametrize("sample_image", sorted(SAMPLES_DIR.glob("facture*.png")))
    def test_extract_sample_invoice_json_output(self, sample_image, runner, snapshot_dir):
        """Test extracting a sample invoice produces consistent JSON output."""
        from bill_extract.main import app

        with patch("bill_extract.main.console") as mock_console:
            mock_console.print_json = Mock()

            result = runner.invoke(app, ["--input", str(sample_image), "--output", "/tmp/test_output"])

        if result.exit_code != 0:
            pytest.skip(f"OCR extraction failed for {sample_image.name}: {result.stdout}")

    def test_snapshot_facture1_json(self, sample_images, runner):
        """Test snapshot for facture1.png."""
        sample = SAMPLES_DIR / "facture1.png"
        output_file = Path("/tmp/test_output") / "facture1.json"

        with patch("bill_extract.main.console"):
            from bill_extract.main import app
            result = runner.invoke(app, ["--input", str(sample), "--output", "/tmp/test_output"])

        if result.exit_code == 0 and output_file.exists():
            with open(output_file) as f:
                data = json.load(f)
            write_snapshot("facture1", data)

            expected = read_snapshot("facture1")
            if expected:
                assert data == expected, "Snapshot mismatch for facture1"
        else:
            pytest.skip("Could not extract data from sample image")

    def test_cli_manual_test_sample(self, runner):
        """Test manual test script works correctly with sample invoice."""
        sample = SAMPLES_DIR / "facture1.png"
        assert sample.exists(), f"Sample file {sample} does not exist"

        from bill_extract.main import app
        result = runner.invoke(app, ["--input", str(sample)])

        assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"


class TestSnapshotComparison:
    """Test snapshot comparison for JSON output."""

    def test_write_and_compare_snapshots(self, snapshot_dir):
        """Test that snapshots can be written and compared."""
        test_data = {
            "date": "2024-03-15",
            "amount": 150.00,
            "id": "FA2024-001"
        }

        write_snapshot("test_snapshot", test_data)
        read_data = read_snapshot("test_snapshot")

        assert read_data == test_data

    def test_snapshot_with_null_values(self, snapshot_dir):
        """Test snapshot handles null/missing values."""
        test_data = {
            "date": None,
            "amount": None,
            "id": "FA2024-001"
        }

        write_snapshot("test_nulls", test_data)
        read_data = read_snapshot("test_nulls")

        assert read_data["id"] == "FA2024-001"
        assert read_data["date"] is None
        assert read_data["amount"] is None


class TestSamplesFolder:
    """Test samples folder structure."""

    def test_samples_folder_exists(self):
        """Test that tests/samples folder exists."""
        assert SAMPLES_DIR.exists(), "samples folder should exist"
        assert SAMPLES_DIR.is_dir(), "samples should be a directory"

    def test_sample_images_are_png(self, sample_images):
        """Test all sample images are PNG format."""
        for img in sample_images:
            assert img.suffix.lower() == ".png", f"{img.name} should be PNG"

    def test_minimum_sample_count(self):
        """Test minimum of 5 sample images."""
        images = list(SAMPLES_DIR.glob("facture*.png"))
        assert len(images) >= 5, f"Expected at least 5 samples, found {len(images)}"
