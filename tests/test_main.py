"""Tests for CLI main module."""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def mock_image_file(tmp_path):
    """Create a mock image file."""
    img = tmp_path / "test_invoice.png"
    img.touch()
    return img


@pytest.fixture
def mock_image_folder(tmp_path):
    """Create a folder with mock images."""
    folder = tmp_path / "invoices"
    folder.mkdir()
    (folder / "invoice1.png").touch()
    (folder / "invoice2.jpg").touch()
    (folder / "readme.txt").touch()
    return folder


class TestCLI:
    """Test CLI interface."""

    def test_cli_help(self, runner):
        """Test --help output."""
        from bill_extract.main import app
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "bill-extract" in result.stdout.lower()

    def test_cli_requires_input(self, runner):
        """Test that --input is required."""
        from bill_extract.main import app
        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "required" in result.stdout.lower()


class TestCollectImages:
    """Test image collection."""

    def test_collect_from_folder(self, mock_image_folder):
        """Test collecting images from a folder."""
        from bill_extract.main import _collect_images

        images = _collect_images(mock_image_folder)
        assert len(images) == 2
        assert all(img.suffix.lower() in {".jpg", ".png"} for img in images)

    def test_collect_no_images(self, tmp_path):
        """Test empty folder returns empty list."""
        from bill_extract.main import _collect_images

        images = _collect_images(tmp_path)
        assert images == []

    def test_collect_with_subfolders(self, tmp_path, mock_image_folder):
        """Test that subfolders are not included."""
        from bill_extract.main import _collect_images

        subfolder = mock_image_folder / "subfolder"
        subfolder.mkdir()
        (subfolder / "nested.png").touch()

        images = _collect_images(mock_image_folder)
        assert len(images) == 2
        assert not any("subfolder" in str(img) for img in images)


class TestDisplayResults:
    """Test result display."""

    def test_display_results_table(self):
        """Test table display."""
        from bill_extract.extractor import ExtractedBill, BillItem
        from bill_extract.main import _display_results

        bill = ExtractedBill(
            vendor="Test Vendor",
            date=None,
            invoice_number="INV-001",
            items=[BillItem(description="Item 1", quantity=1.0, total=10.0)],
            total=10.0,
            tax=1.0,
            currency="EUR",
        )
        results = [("test.png", bill)]

        _display_results(results, verbose=False)


class TestSaveResults:
    """Test result saving."""

    def test_save_results_json(self, tmp_path):
        """Test saving results to JSON in simplified format."""
        from datetime import date
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _save_results

        bill = ExtractedBill(
            vendor="Test",
            date=date(2026, 4, 15),
            invoice_number="FACT-987654",
            total=245.80,
            currency="EUR"
        )
        results = [("test.png", bill)]
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        _save_results(results, output_dir)

        output_file = output_dir / "test.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
            assert data["date"] == "2026-04-15"
            assert data["amount"] == 245.80
            assert data["id"] == "FACT-987654"

    def test_save_results_json_missing_fields(self, tmp_path, caplog):
        """Test JSON output with null values and warning logs."""
        caplog.set_level(logging.WARNING, logger="bill_extract")
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _save_results

        bill = ExtractedBill(vendor="Test", total=None, currency="EUR")
        results = [("test.png", bill)]
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        _save_results(results, output_dir)

        output_file = output_dir / "test.json"
        with open(output_file) as f:
            data = json.load(f)
            assert data["amount"] is None
            assert "Missing amount" in caplog.text


class TestPrintJsonOutput:
    """Test JSON output."""

    def test_print_json_output(self):
        """Test JSON output to stdout."""
        from datetime import date
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _print_json_output

        bill = ExtractedBill(
            vendor="Test",
            date=date(2026, 4, 15),
            invoice_number="FACT-987654",
            total=245.80,
            currency="EUR"
        )
        results = [("test.png", bill)]

        with patch("bill_extract.main.console", new=Mock()) as mock_console:
            mock_console.print_json = Mock()
            _print_json_output(results)
            mock_console.print_json.assert_called_once()

    def test_print_json_output_missing_fields(self, caplog):
        """Test JSON output with missing fields logs warnings."""
        caplog.set_level(logging.WARNING, logger="bill_extract")
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _print_json_output

        bill = ExtractedBill(vendor="Test", total=None, invoice_number=None, currency="EUR")
        results = [("test.png", bill)]

        with patch("bill_extract.main.console", new=Mock()):
            _print_json_output(results)

        assert "Missing amount" in caplog.text
        assert "Missing invoice number" in caplog.text


class TestFormatJsonOutput:
    """Test JSON format function."""

    def test_format_json_complete(self):
        """Test formatting complete bill data."""
        from datetime import date
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _format_json_output

        bill = ExtractedBill(
            date=date(2026, 4, 15),
            invoice_number="FACT-987654",
            total=245.80
        )
        result = _format_json_output(bill, "test.png")

        assert result == {"date": "2026-04-15", "amount": 245.80, "id": "FACT-987654"}

    def test_format_json_missing_fields(self, caplog):
        """Test formatting with missing fields returns null and logs warnings."""
        caplog.set_level(logging.WARNING, logger="bill_extract")
        from bill_extract.extractor import ExtractedBill
        from bill_extract.main import _format_json_output

        bill = ExtractedBill()
        result = _format_json_output(bill, "test.png")

        assert result["date"] is None
        assert result["amount"] is None
        assert result["id"] is None
        assert "Missing date" in caplog.text
        assert "Missing amount" in caplog.text
        assert "Missing invoice number" in caplog.text