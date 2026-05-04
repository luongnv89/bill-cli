"""OCR functionality using PaddleOCR."""

import logging
import time
from typing import Any, Optional

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

from bill_extract.logging import get_logger

logger = get_logger("bill_extract.ocr")

FIRST_LOAD = True


class OCREngine:
    """PaddleOCR-based text recognition."""

    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        if not PADDLE_AVAILABLE:
            raise ImportError("paddlepaddle and paddleocr are required. Install with: pip install paddlepaddle paddleocr")
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            global FIRST_LOAD
            if FIRST_LOAD:
                logger.info("[bold cyan]Loading PaddleOCR models...[/bold cyan]")
                logger.info("[dim]First time loading may take a few minutes[/dim]")
                FIRST_LOAD = False
            
            start = time.time()
            self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang, show_log=False)
            elapsed = time.time() - start
            logger.info(f"[green]OCR models loaded in {elapsed:.1f}s[/green]")
            
        return self._ocr

    def read_text(self, image_path: str) -> list[dict[str, Any]]:
        """Read text from an image file."""
        ocr = self._get_ocr()
        result = ocr.ocr(image_path, cls=True)
        if not result or not result[0]:
            return []
        return [{
            "text": line[1][0],
            "confidence": line[1][1],
            "bbox": line[0]
        } for line in result[0]]

    def read_text_from_array(self, image_array) -> list[dict[str, Any]]:
        """Read text from a numpy array."""
        ocr = self._get_ocr()
        result = ocr.ocr(image_array, cls=True)
        if not result or not result[0]:
            return []
        return [{
            "text": line[1][0],
            "confidence": line[1][1],
            "bbox": line[0]
        } for line in result[0]]