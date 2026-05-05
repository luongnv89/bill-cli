"""Image preprocessing utilities."""

import cv2
import numpy as np
from PIL import Image


def load_image(image_path: str) -> np.ndarray:
    """Load an image from file path."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    return img


def load_image_pil(image_path: str) -> Image.Image:
    """Load an image using PIL."""
    return Image.open(image_path)


def resize_image(
    image: np.ndarray, max_size: tuple[int, int] = (1200, 1600), inter: int = cv2.INTER_AREA
) -> np.ndarray:
    """Resize image while maintaining aspect ratio."""
    h, w = image.shape[:2]
    max_w, max_h = max_size

    if w <= max_w and h <= max_h:
        return image

    scale = min(max_w / w, max_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    return cv2.resize(image, (new_w, new_h), interpolation=inter)


def grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale."""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def apply_threshold(image: np.ndarray, method: str = "adaptive") -> np.ndarray:
    """Apply thresholding to binarize image."""
    gray = grayscale(image)

    if method == "otsu":
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

    return thresh


def denoise(image: np.ndarray) -> np.ndarray:
    """Remove noise from image."""
    return cv2.fastNlMeansDenoising(image, h=10)


def sharpen(image: np.ndarray) -> np.ndarray:
    """Sharpen image."""
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)


def correct_skew(image: np.ndarray) -> np.ndarray:
    """Correct document skew."""
    coords = np.column_stack(np.where(image > 127))
    if len(coords) == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    if angle > 45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if angle == 0:
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance image contrast."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    enhanced = cv2.merge([l_channel, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def preprocessing_pipeline(
    image_path: str,
    resize: bool = True,
    denoise_flag: bool = True,
    sharpen_flag: bool = False,
    enhance: bool = True,
    deskew: bool = True,
) -> np.ndarray:
    """Run full preprocessing pipeline.

    Args:
        image_path: Path to input image
        resize: Resize image to reduce processing time
        denoise_flag: Apply light denoising
        sharpen_flag: Apply sharpening filter
        enhance: Apply CLAHE contrast enhancement
        deskew: Correct document skew using OpenCV

    Returns:
        Enhanced numpy array suitable for OCR
    """
    img = load_image(image_path)

    if resize:
        img = resize_image(img)

    img = grayscale(img)

    if enhance:
        img = enhance_contrast(img)

    if deskew:
        img = correct_skew(img)

    if denoise_flag:
        img = denoise(img)

    if sharpen_flag:
        img = sharpen(img)

    return img
