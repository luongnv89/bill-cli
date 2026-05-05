"""OCR functionality using PaddleOCR."""

import time
from pathlib import Path

try:
    from paddleocr import PaddleOCR

    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

from bill_extract.logging import get_logger

logger = get_logger("bill_extract.ocr")

FIRST_LOAD = True


class OCRError(Exception):
    """Base exception for OCR errors."""

    pass


class CorruptImageError(OCRError):
    """Raised when image file is corrupt or unreadable."""

    pass


class NoTextDetectedError(OCRError):
    """Raised when OCR detects no text in the image."""

    pass


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
            raise ImportError(
                "paddlepaddle and paddleocr are required. Install with: pip install paddlepaddle paddleocr"
            )
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
            self._ocr = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
            )
            elapsed = time.time() - start
            logger.info(f"[green]OCR models loaded in {elapsed:.1f}s[/green]")

        return self._ocr

    def _validate_image(self, image_path: str) -> None:
        """Validate image file is readable and not corrupt.

        Args:
            image_path: Path to the image file.

        Raises:
            CorruptImageError: If image is corrupt or unreadable.
            FileNotFoundError: If image file does not exist.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if path.stat().st_size == 0:
            raise CorruptImageError(f"Image file is empty: {image_path}")

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            raise CorruptImageError(
                f"Image file appears corrupt or invalid: {image_path}. "
                f"Error: {str(e)}. Try a different image or check if it's a valid image format."
            ) from e

    def extract_text(self, image_path: str) -> list[tuple[list, tuple[str, float]]]:
        """Extract text from an image file.

        Args:
            image_path: Path to the image file.

        Returns:
            List of (bbox, (text, confidence)) tuples.

        Raises:
            CorruptImageError: If image file is corrupt or unreadable.
            NoTextDetectedError: If no text is detected in the image.
        """
        self._validate_image(image_path)

        ocr = self._get_ocr()
        try:
            result = ocr.ocr(image_path, cls=True)
        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            raise CorruptImageError(
                f"Failed to process image: {image_path}. "
                f"The image may be corrupted or in an unsupported format. Error: {str(e)}"
            ) from e

        if not result or not result[0]:
            logger.warning(
                f"OCR returned no text for {image_path}. Try preprocessing or use a better quality image."
            )
            raise NoTextDetectedError(
                f"OCR returned no text for {image_path}. "
                f"Try preprocessing or use a better quality screenshot."
            )

        ocr_results = [(line[0], (line[1][0], line[1][1])) for line in result[0]]
        confidences = [item[1][1] for item in ocr_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if avg_confidence < 0.6:
            logger.warning(
                f"Low confidence OCR result for {image_path}: average confidence {avg_confidence:.2f}. "
                f"Consider using a clearer image or enabling preprocessing."
            )

        return ocr_results

    def extract_text_from_array(self, image_array) -> list[tuple[list, tuple[str, float]]]:
        """Extract text from a numpy array.

        Args:
            image_array: NumPy array representing the image.

        Returns:
            List of (bbox, (text, confidence)) tuples.

        Raises:
            NoTextDetectedError: If no text is detected in the image.
        """
        ocr = self._get_ocr()
        try:
            result = ocr.ocr(image_array, cls=True)
        except Exception as e:
            logger.error(f"OCR processing failed for array input: {e}")
            raise CorruptImageError(
                f"Failed to process image array: {str(e)}. The image data may be corrupted."
            ) from e

        if not result or not result[0]:
            logger.warning(
                "OCR returned no text from preprocessed image. Try a better quality original image."
            )
            raise NoTextDetectedError(
                "OCR returned no text from preprocessed image. "
                "Try a better quality original image or adjust preprocessing."
            )

        ocr_results = [(line[0], (line[1][0], line[1][1])) for line in result[0]]
        confidences = [item[1][1] for item in ocr_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if avg_confidence < 0.6:
            logger.warning(
                f"Low confidence OCR result from preprocessed image: {avg_confidence:.2f}. "
                f"Consider using a clearer original image."
            )

        return ocr_results


OCREngine = BillOCR
