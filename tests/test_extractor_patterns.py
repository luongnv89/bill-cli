"""Tests for field extraction with configurable patterns."""

import pytest
from datetime import date

from bill_extract.extractor import BillExtractor, ExtractedBill


class TestExtractorWithPatterns:
    """Tests for BillExtractor with custom patterns."""

    def test_default_patterns_loaded(self):
        """Test that default patterns are loaded when no config provided."""
        extractor = BillExtractor()
        
        assert len(extractor.date_patterns) > 0
        assert len(extractor.amount_patterns) > 0
        assert len(extractor.id_patterns) > 0

    def test_custom_patterns_loaded(self):
        """Test that custom patterns override defaults."""
        custom_patterns = {
            "date": [
                {
                    "name": "test_date",
                    "pattern": r"(\d{4}-\d{2}-\d{2})",
                    "keywords": ["date"],
                    "confidence": 1.0,
                }
            ],
            "amount": [
                {
                    "name": "test_amount",
                    "pattern": r"(\d+)",
                    "keywords": ["total"],
                    "confidence": 1.0,
                }
            ],
            "id": [
                {
                    "name": "test_id",
                    "pattern": r"(INV-\d+)",
                    "keywords": ["invoice"],
                    "confidence": 1.0,
                }
            ],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        assert len(extractor.date_patterns) == 1
        assert extractor.date_patterns[0]["name"] == "test_date"
        assert len(extractor.amount_patterns) == 1
        assert extractor.amount_patterns[0]["name"] == "test_amount"
        assert len(extractor.id_patterns) == 1
        assert extractor.id_patterns[0]["name"] == "test_id"


class TestDateExtraction:
    """Tests for date extraction."""

    def test_extract_date_common_format(self):
        """Test extraction of common date format."""
        custom_patterns = {
            "date": [
                {
                    "name": "common_date",
                    "pattern": r"(\d{1,2}/\d{1,2}/\d{2,4})",
                    "keywords": ["date"],
                    "confidence": 0.8,
                }
            ],
            "amount": [],
            "id": [],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Date: 15/04/2026"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.date is not None

    def test_extract_date_iso_format(self):
        """Test extraction of ISO date format."""
        custom_patterns = {
            "date": [
                {
                    "name": "iso_date",
                    "pattern": r"(\d{4}-\d{2}-\d{2})",
                    "keywords": ["date"],
                    "confidence": 0.9,
                }
            ],
            "amount": [],
            "id": [],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Date: 2026-04-15"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.date is not None


class TestAmountExtraction:
    """Tests for amount extraction."""

    def test_extract_amount_with_currency(self):
        """Test extraction of amount with currency symbol."""
        custom_patterns = {
            "date": [],
            "amount": [
                {
                    "name": "euro_amount",
                    "pattern": r"([\d.,]+)\s*€",
                    "keywords": ["total"],
                    "confidence": 0.9,
                }
            ],
            "id": [],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Total: 245,80 €"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.total is not None

    def test_extract_amount_without_decimals(self):
        """Test extraction of amount without decimals."""
        custom_patterns = {
            "date": [],
            "amount": [
                {
                    "name": "simple_amount",
                    "pattern": r"(\d+)",
                    "keywords": ["total"],
                    "confidence": 0.8,
                }
            ],
            "id": [],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Total: 100"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.total == 100.0


class TestIDExtraction:
    """Tests for invoice ID extraction."""

    def test_extract_invoice_number(self):
        """Test extraction of invoice number."""
        custom_patterns = {
            "date": [],
            "amount": [],
            "id": [
                {
                    "name": "invoice_number",
                    "pattern": r"N°\s*(\d+)",
                    "keywords": [],
                    "confidence": 0.9,
                }
            ],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "N° 12345"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.invoice_number is not None

    def test_extract_invoice_with_prefix(self):
        """Test extraction of invoice with prefix."""
        custom_patterns = {
            "date": [],
            "amount": [],
            "id": [
                {
                    "name": "facture_ref",
                    "pattern": r"facture\s*([A-Z0-9-]+)",
                    "keywords": ["facture"],
                    "confidence": 0.9,
                }
            ],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Facture FACT-2026-001"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.invoice_number is not None
        assert "FACT" in bill.invoice_number.upper()


class TestFallback:
    """Tests for fallback behavior."""

    def test_fallback_when_no_matching_pattern(self):
        """Test fallback when custom patterns don't have matching keywords."""
        custom_patterns = {
            "date": [
                {
                    "name": "unused",
                    "pattern": r"NEVER_MATCHES",
                    "keywords": ["nonexistent_keyword"],
                    "confidence": 1.0,
                }
            ],
            "amount": [
                {
                    "name": "unused",
                    "pattern": r"NEVER_MATCHES",
                    "keywords": ["nonexistent_keyword"],
                    "confidence": 1.0,
                }
            ],
            "id": [
                {
                    "name": "unused",
                    "pattern": r"NEVER_MATCHES",
                    "keywords": ["nonexistent_keyword"],
                    "confidence": 1.0,
                }
            ],
        }
        
        extractor = BillExtractor(custom_patterns)
        
        ocr_results = [{"text": "Some random text that won't match"}]
        bill = extractor.extract(ocr_results)
        
        assert bill.invoice_number is None
        assert bill.date is None
        assert bill.total is None