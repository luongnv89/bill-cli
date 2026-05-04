# Bill Extractor CLI

Extract structured information from bills and invoices using OCR.

## Features

- **OCR**: PaddleOCR-powered text recognition
- **Data Extraction**: Automatic vendor, date, invoice number, and amount parsing
- **Image Preprocessing**: Built-in image enhancement and denoising
- **CLI Interface**: Simple command-line interface with rich formatting

## Installation

### Prerequisites

- Python 3.9+
- pip or uv

### Install from source

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the CLI:

```bash
bill-extract
```

### Extract from an invoice image

```python
from bill_extract.ocr import OCREngine
from bill_extract.extractor import BillExtractor
from bill_extract.preprocess import preprocessing_pipeline

# Preprocess the image
image = preprocessing_pipeline("invoice.jpg")

# Run OCR
ocr = OCREngine()
results = ocr.read_text("invoice.jpg")

# Extract structured data
extractor = BillExtractor()
bill = extractor.extract(results)
print(f"Vendor: {bill.vendor}")
print(f"Date: {bill.date}")
print(f"Total: {bill.total}")
```

### Using the CLI programmatically

```python
from bill_extract.main import app
import typer

if __name__ == "__main__":
    app()
```

## Project Structure

```
bill-cli/
├── bill_extract/       # Main package
│   ├── __init__.py   # Package initialization
│   ├── main.py       # CLI entry point
│   ├── ocr.py       # OCR functionality
│   ├── extractor.py # Data extraction
│   ├── preprocess.py # Image preprocessing
│   └── utils.py     # Utilities
├── pyproject.toml    # Package configuration
├── requirements.txt # Dependencies
└── README.md       # This file
```

## Dependencies

- **paddleocr** - OCR engine
- **paddlepaddle** - Deep learning framework
- **opencv-python** - Image processing
- **pillow** - Image handling
- **typer** - CLI framework
- **pydantic** - Data validation
- **rich** - Terminal rendering
- **tqdm** - Progress bars

## Development

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Lint code:

```bash
ruff check .
```

Format code:

```bash
black .
```

Type check:

```bash
mypy .
```

## License

MIT License - see LICENSE file for details.