"""Tests for image preprocessing module."""

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from unittest.mock import patch


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return img


@pytest.fixture
def grayscale_image():
    """Create a sample grayscale image."""
    return np.random.randint(0, 255, (100, 100), dtype=np.uint8)


class TestGrayscale:
    """Test grayscale conversion."""

    def test_grayscale_color(self, sample_image):
        """Convert color image to grayscale."""
        from bill_extract.preprocess import grayscale
        gray = grayscale(sample_image)
        assert len(gray.shape) == 2
        assert gray.dtype == np.uint8

    def test_grayscale_already_gray(self, grayscale_image):
        """Grayscale image remains unchanged."""
        from bill_extract.preprocess import grayscale
        gray = grayscale(grayscale_image)
        assert np.array_equal(gray, grayscale_image)


class TestEnhanceContrast:
    """Test CLAHE contrast enhancement."""

    def test_enhance_contrast(self, sample_image):
        """Apply CLAHE enhancement."""
        from bill_extract.preprocess import enhance_contrast
        enhanced = enhance_contrast(sample_image)
        assert enhanced.shape == sample_image.shape
        assert enhanced.dtype == np.uint8


class TestDeskew:
    """Test deskewing function."""

    def test_correct_skew_no_rotation(self, grayscale_image):
        """Image with minimal skew stays same."""
        from bill_extract.preprocess import correct_skew
        result = correct_skew(grayscale_image)
        assert result.shape == grayscale_image.shape


class TestDenoise:
    """Test denoising."""

    def test_denoise_returns_array(self, grayscale_image):
        """Denoise returns numpy array."""
        from bill_extract.preprocess import denoise
        denoised = denoise(grayscale_image)
        assert isinstance(denoised, np.ndarray)


class TestSharpen:
    """Test sharpening."""

    def test_sharpen_returns_array(self, grayscale_image):
        """Sharpen returns numpy array."""
        from bill_extract.preprocess import sharpen
        sharp = sharpen(grayscale_image)
        assert isinstance(sharp, np.ndarray)


class TestPreprocessingPipeline:
    """Test full preprocessing pipeline."""

    @patch("bill_extract.preprocess.load_image")
    @patch("bill_extract.preprocess.grayscale")
    @patch("bill_extract.preprocess.enhance_contrast")
    @patch("bill_extract.preprocess.correct_skew")
    @patch("bill_extract.preprocess.denoise")
    def test_pipeline_calls_functions(
        self, mock_denoise, mock_deskew, mock_enhance, mock_gray, mock_load
    ):
        """Pipeline calls all preprocessing functions."""
        from bill_extract.preprocess import preprocessing_pipeline

        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_gray.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_enhance.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_deskew.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_denoise.return_value = np.zeros((100, 100), dtype=np.uint8)

        _result = preprocessing_pipeline("test.jpg")

        mock_load.assert_called_once_with("test.jpg")
        mock_gray.assert_called_once()
        mock_enhance.assert_called_once()
        mock_deskew.assert_called_once()
        mock_denoise.assert_called_once()

    @patch("bill_extract.preprocess.load_image")
    @patch("bill_extract.preprocess.resize_image")
    @patch("bill_extract.preprocess.grayscale")
    @patch("bill_extract.preprocess.enhance_contrast")
    def test_pipeline_resize_option(self, mock_enhance, mock_gray, mock_resize, mock_load):
        """Pipeline respects resize flag."""
        from bill_extract.preprocess import preprocessing_pipeline

        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_gray.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_enhance.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        preprocessing_pipeline("test.jpg", resize=True)
        mock_resize.assert_called_once()

        mock_resize.reset_mock()
        preprocessing_pipeline("test.jpg", resize=False)
        mock_resize.assert_not_called()

    @patch("bill_extract.preprocess.load_image")
    @patch("bill_extract.preprocess.grayscale")
    @patch("bill_extract.preprocess.enhance_contrast")
    @patch("bill_extract.preprocess.correct_skew")
    @patch("bill_extract.preprocess.denoise")
    def test_pipeline_deskew_option(
        self, mock_denoise, mock_deskew, mock_enhance, mock_gray, mock_load
    ):
        """Pipeline respects deskew flag."""
        from bill_extract.preprocess import preprocessing_pipeline

        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_gray.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_enhance.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_deskew.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_denoise.return_value = np.zeros((100, 100), dtype=np.uint8)

        preprocessing_pipeline("test.jpg", deskew=True)
        mock_deskew.assert_called_once()

        mock_deskew.reset_mock()
        preprocessing_pipeline("test.jpg", deskew=False)
        mock_deskew.assert_not_called()
