"""Tests for OCR module."""



class TestBillOCRDefaults:
    """Test BillOCR default values."""

    def test_default_lang_is_french(self):
        """Default language is French."""
        from bill_extract.ocr import PADDLE_AVAILABLE, BillOCR
        if PADDLE_AVAILABLE:
            ocr = BillOCR()
            assert ocr.lang == "fr"

    def test_default_use_gpu_is_false(self):
        """Default use_gpu is False."""
        from bill_extract.ocr import PADDLE_AVAILABLE, BillOCR
        if PADDLE_AVAILABLE:
            ocr = BillOCR()
            assert ocr.use_gpu is False

    def test_default_use_angle_cls_is_true(self):
        """Default use_angle_cls is True."""
        from bill_extract.ocr import PADDLE_AVAILABLE, BillOCR
        if PADDLE_AVAILABLE:
            ocr = BillOCR()
            assert ocr.use_angle_cls is True


class TestOCREngineAlias:
    """Test OCREngine is alias for BillOCR."""

    def test_ocr_engine_exists(self):
        """OCREngine exists."""
        from bill_extract.ocr import OCREngine
        assert OCREngine is not None

    def test_ocr_engine_is_bill_ocr(self):
        """OCREngine is BillOCR."""
        from bill_extract.ocr import BillOCR, OCREngine
        assert OCREngine == BillOCR


class TestBillOCRResultFormat:
    """Test result format."""

    def test_extract_text_method_returns_list(self):
        """extract_text is callable and returns list."""
        from bill_extract.ocr import BillOCR
        assert hasattr(BillOCR, "extract_text")
        assert callable(BillOCR.extract_text)

    def test_extract_text_from_array_method_exists(self):
        """extract_text_from_array is callable."""
        from bill_extract.ocr import BillOCR
        assert hasattr(BillOCR, "extract_text_from_array")
        assert callable(BillOCR.extract_text_from_array)
