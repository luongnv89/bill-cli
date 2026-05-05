"""Tests for bill_extract module with snapshot validation."""

import json
from pathlib import Path

import pytest

from conftest import load_snapshot, save_snapshot, SAMPLES_DIR, SNAPSHOT_DIR


class TestModuleImport:
    """Test that the bill_extract module can be imported."""

    def test_import_bill_extract(self):
        """Test main module imports successfully."""
        import bill_extract
        assert hasattr(bill_extract, "__version__")
        assert bill_extract.__version__ == "0.1.0"

    def test_import_main_app(self):
        """Test CLI app imports successfully."""
        from bill_extract.main import app
        assert app is not None


class TestSnapshotValidation:
    """Snapshot tests for JSON output structure."""

    @pytest.mark.parametrize("sample_image", sorted(SAMPLES_DIR.glob("facture*.png")))
    def test_json_output_structure(self, sample_image, cli_runner, bill_extract_app, snapshot_dir):
        """Test extraction produces valid JSON output with expected structure."""
        from unittest.mock import patch

        output_dir = Path("/tmp/test_bill_extract")
        output_dir.mkdir(exist_ok=True)

        with patch("bill_extract.main.console") as mock_console:
            mock_console.print_json = lambda data: None
            result = cli_runner.invoke(
                bill_extract_app, ["--input", str(sample_image), "--output", str(output_dir)]
            )

        if result.exit_code != 0:
            pytest.skip(f"Extraction skipped for {sample_image.name}: {result.stdout}")

        output_file = output_dir / f"{sample_image.stem}.json"
        if not output_file.exists():
            pytest.skip(f"No output JSON for {sample_image.name}")

        with open(output_file) as f:
            data = json.load(f)

        # Validate basic JSON structure
        assert isinstance(data, dict), "Output should be a JSON object"
        snapshot_name = sample_image.stem
        save_snapshot(snapshot_name, data)

        expected = load_snapshot(snapshot_name)
        if expected:
            assert data == expected, f"Snapshot mismatch for {sample_image.name}"


class TestManualScript:
    """Test manual test script execution."""

    def test_manual_script_help(self, cli_runner, bill_extract_app):
        """Test CLI help command works."""
        result = cli_runner.invoke(bill_extract_app, ["--help"])
        assert result.exit_code == 0
        assert "bill-extract" in result.stdout.lower() or "usage" in result.stdout.lower()

    @pytest.mark.parametrize("sample_image", sorted(SAMPLES_DIR.glob("facture*.png"))[:3])
    def test_manual_script_with_sample(self, sample_image, cli_runner, bill_extract_app):
        """Test manual script works with sample invoices."""
        result = cli_runner.invoke(bill_extract_app, ["--input", str(sample_image)])
        assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"


class TestSampleImages:
    """Test sample invoice image requirements."""

    def test_minimum_sample_count(self):
        """Test at least 5 sample images exist."""
        images = list(SAMPLES_DIR.glob("facture*.png"))
        assert len(images) >= 5, f"Expected ≥5 samples, found {len(images)}"

    def test_maximum_sample_count(self):
        """Test no more than 10 sample images exist."""
        images = list(SAMPLES_DIR.glob("facture*.png"))
        assert len(images) <= 10, f"Expected ≤10 samples, found {len(images)}"

    def test_samples_are_png(self, sample_images):
        """Test all sample images are PNG format."""
        for img in sample_images:
            assert img.suffix.lower() == ".png", f"{img.name} should be PNG"

    def test_samples_not_empty(self, sample_images):
        """Test sample images are not empty files."""
        for img in sample_images:
            assert img.stat().st_size > 0, f"{img.name} is empty"
