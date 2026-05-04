"""Tests for French invoice field extraction."""

from bill_extract.extractor import (
    BillExtractor,
    FieldExtractionResult,
    FieldExtractor,
)


class TestFieldExtractorDate:
    """Test date extraction with French patterns."""

    def test_date_with_keyword_facture_le(self):
        """Test date extraction with 'facturé le' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Facturé le 15/03/2024", "confidence": 0.9, "y_center": 50},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.value is not None
        assert "2024-03-15" in result.value
        assert result.confidence >= 0.6

    def test_date_with_keyword_date_de_facturation(self):
        """Test date extraction with 'date de facturation' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Date de facturation: 20.05.2024", "confidence": 0.85, "y_center": 100},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.value is not None
        assert "2024-05-20" in result.value

    def test_date_fallback_dd_mm_yyyy(self):
        """Test fallback date extraction."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Some text 25/12/2023", "confidence": 0.7, "y_center": 30},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.value is not None
        assert "2023-12-25" in result.value

    def test_date_y_coordinate_sorting(self):
        """Test Y-coordinate sorting for reading order."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Footer text", "confidence": 0.8, "y_center": 500},
            {"text": "Date: 10/01/2024", "confidence": 0.9, "y_center": 100},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.value is not None

    def test_date_no_match(self):
        """Test date extraction with no match."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Invoice for services", "confidence": 0.8, "y_center": 50},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.value is None
        assert result.confidence == 0.0


class TestFieldExtractorAmount:
    """Test TTC amount extraction with French patterns."""

    def test_amount_with_ttc_keyword(self):
        """Test amount extraction with 'Total TTC' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Total TTC: 125,50 €", "confidence": 0.9, "y_center": 400},
        ]
        result = extractor.extract_amount_ttc(ocr_results)

        assert result.value is not None
        assert isinstance(result.value, float)
        assert abs(result.value - 125.50) < 0.01

    def test_amount_with_montant_total(self):
        """Test amount extraction with 'Montant total' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Montant total: 250,00 EUR", "confidence": 0.85, "y_center": 350},
        ]
        result = extractor.extract_amount_ttc(ocr_results)

        assert result.value is not None
        assert abs(result.value - 250.00) < 0.01

    def test_amount_fallback_with_total(self):
        """Test fallback amount with total keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "TOTAL: 300.00", "confidence": 0.7, "y_center": 450},
            {"text": "Other line", "confidence": 0.8, "y_center": 50},
        ]
        result = extractor.extract_amount_ttc(ocr_results)

        assert result.value is not None
        assert abs(result.value - 300.00) < 0.01

    def test_amount_comma_as_decimal(self):
        """Test French number format (comma as decimal separator)."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Total TTC 1 234,56", "confidence": 0.9, "y_center": 300},
        ]
        result = extractor.extract_amount_ttc(ocr_results)

        assert result.value is not None
        assert abs(result.value - 1234.56) < 0.01

    def test_amount_no_match(self):
        """Test amount extraction with no match."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Just some text", "confidence": 0.8, "y_center": 50},
        ]
        result = extractor.extract_amount_ttc(ocr_results)

        assert result.value is None
        assert result.confidence == 0.0


class TestFieldExtractorBillID:
    """Test bill ID extraction with French patterns."""

    def test_bill_id_with_numero_facture(self):
        """Test bill ID extraction with 'Numéro de facture' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Numéro de facture: FAC-2024-001", "confidence": 0.9, "y_center": 50},
        ]
        result = extractor.extract_bill_id(ocr_results)

        assert result.value is not None
        assert "FAC-2024-001" in result.value
        assert result.value == result.value.upper()

    def test_bill_id_with_reference(self):
        """Test bill ID extraction with 'Référence' keyword."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Référence: 24A0001", "confidence": 0.85, "y_center": 80},
        ]
        result = extractor.extract_bill_id(ocr_results)

        assert result.value is not None

    def test_bill_id_uppercase_normalized(self):
        """Test bill ID normalization (uppercase)."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Facture n°: fac-2024-abc-123", "confidence": 0.9, "y_center": 100},
        ]
        result = extractor.extract_bill_id(ocr_results)

        assert result.value is not None
        assert result.value == result.value.upper()

    def test_bill_id_fallback_pattern(self):
        """Test fallback bill ID with pattern."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Random text with AB123456", "confidence": 0.7, "y_center": 150},
        ]
        result = extractor.extract_bill_id(ocr_results)

        assert result.value is not None

    def test_bill_id_no_match(self):
        """Test bill ID extraction with no match."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Generic invoice text", "confidence": 0.8, "y_center": 50},
        ]
        result = extractor.extract_bill_id(ocr_results)

        assert result.value is None
        assert result.confidence == 0.0


class TestFieldExtractorAll:
    """Test all fields extraction."""

    def test_extract_all_returns_dict(self):
        """Test extract_all returns dict of results."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Date: 15/03/2024", "confidence": 0.9, "y_center": 50},
            {"text": "Total TTC: 100,00 €", "confidence": 0.9, "y_center": 400},
            {"text": "Facture: FA2024001", "confidence": 0.9, "y_center": 100},
        ]
        result = extractor.extract_all(ocr_results)

        assert "date" in result
        assert "amount_ttc" in result
        assert "bill_id" in result

    def test_extract_all_with_realistic_invoice(self):
        """Test extraction from realistic French invoice."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Logo Company", "confidence": 0.9, "y_center": 20},
            {"text": "Facturé le 15/03/2024", "confidence": 0.95, "y_center": 80},
            {"text": "Numéro de facture: FAC-2024-0001", "confidence": 0.95, "y_center": 120},
            {"text": "Service: Réparation", "confidence": 0.85, "y_center": 180},
            {"text": "Sous-total: 85,00 €", "confidence": 0.85, "y_center": 300},
            {"text": "TVA (20%): 17,00 €", "confidence": 0.85, "y_center": 320},
            {"text": "Total TTC: 102,00 €", "confidence": 0.95, "y_center": 350},
        ]
        result = extractor.extract_all(ocr_results)

        assert result["date"].value is not None
        assert result["amount_ttc"].value is not None
        assert result["bill_id"].value is not None


class TestConfidenceScoring:
    """Test confidence scoring and warnings."""

    def test_high_confidence_extraction(self):
        """Test high confidence gets boosted."""
        extractor = FieldExtractor()
        ocr_results = [
            {"text": "Date: 15/03/2024", "confidence": 0.9, "y_center": 50},
        ]
        result = extractor.extract_date(ocr_results)

        assert result.confidence >= 0.9

    def test_low_confidence_logs_warning(self, caplog):
        """Test low confidence triggers warning log."""
        import logging

        extractor = FieldExtractor()
        ocr_results = [
            {"text": "some date 15/03/2024", "confidence": 0.3, "y_center": 50},
        ]

        with caplog.at_level(logging.WARNING):
            result = extractor.extract_date(ocr_results)

        if result.confidence < 0.6:
            assert any("Low confidence" in msg for msg in caplog.messages)


class TestPydanticValidation:
    """Test Pydantic validation."""

    def test_field_extraction_result_validates(self):
        """Test FieldExtractionResult validates with Pydantic."""
        result = FieldExtractionResult(
            value="2024-03-15", confidence=0.85, matched_text="Date: 15/03/2024"
        )

        assert result.value == "2024-03-15"
        assert result.confidence == 0.85

    def test_field_extraction_result_with_float(self):
        """Test FieldExtractionResult with float value."""
        result = FieldExtractionResult(value=125.50, confidence=0.9, matched_text="Total: 125,50")

        assert isinstance(result.value, float)
        assert result.value == 125.50


class TestBillExtractorIntegration:
    """Test BillExtractor with field extraction."""

    def test_extractor_has_field_extractor(self):
        """Test BillExtractor has field_extractor attribute."""
        extractor = BillExtractor()

        assert hasattr(extractor, "field_extractor")
        assert isinstance(extractor.field_extractor, FieldExtractor)

    def test_extract_fields_returns_results(self):
        """Test extract_fields returns extraction results."""
        extractor = BillExtractor()
        ocr_results = [
            {"text": "Date: 15/03/2024", "confidence": 0.9, "y_center": 50},
            {"text": "Total TTC: 100 €", "confidence": 0.9, "y_center": 200},
        ]

        result = extractor.extract_fields(ocr_results)

        assert "date" in result
        assert "amount_ttc" in result
        assert "bill_id" in result
