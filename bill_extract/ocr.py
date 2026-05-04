"""OCR functionality using PaddleOCR."""

import logging
import time
from typing import Any

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

from bill_extract.logging import get_logger

logger = get_logger("bill_extract.ocr")

FIRST_LOAD = True


class BillOCR:
    """PaddleOCR-based text recognition for bill extraction."""

    def __init__(self, use_angle_cls: bool = True, lang: str = "fr", use_gpu: bool = False):
        """Initialize BillOCR with PaddleOCR.

        Args:
            use_angle_cls: Use angle classifier for text orientation.
            lang: Language code (default: "fr" for French).
            use_gpu: Use GPU acceleration (default: False for CPU mode).
        """
        if not PADDLE_AVAILABLE:
            raise ImportError("paddlepaddle and paddleocr are required. Install with: pip install paddlepaddle paddleocr")
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.use_gpu = use_gpu
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            global FIRST_LOAD
            if FIRST_LOAD:
                logger.info("[bold cyan]Loading PaddleOCR models...[/bold cyan]")
                logger.info("[dim]First time loading may take a few minutes[/dim]")
                FIRST_LOAD = False

            start = time.time()
            self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang, use_gpu=self.use_gpu, show_log=False)
            elapsed = time.time() - start
            logger.info(f"[green]OCR models loaded in {elapsed:.1f}s[/green]")

        return self._ocr

    def extract_text(self, image_path: str) -> list[tuple[list, tuple[str, float]]]:
        """Extract text from an image file.

        Args:
            image_path: Path to the image file.

        Returns:
            List of (bbox, (text, confidence)) tuples.
        """
        ocr = self._get_ocr()
        result = ocr.ocr(image_path, cls=True)
        if not result or not result[0]:
            return []
        return [(line[0], (line[1][0], line[1][1])) for line in result[0]]

    def extract_text_from_array(
        self, image_array
    ) -> list[tuple[list, tuple[str, float]]]:
        """Extract text from a numpy array.

        Args:
            image_array: NumPy array representing the image.

        Returns:
            List of (bbox, (text, confidence)) tuples.
        """
        ocr = self._get_ocr()
        result = ocr.ocr(image_array, cls=True)
        if not result or not result[0]:
            return []
        return [(line[0], (line[1][0], line[1][1])) for line in result[0]]


OCREngine = BillOCR