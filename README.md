# Bill Extractor CLI

Extract structured information from bills and invoices using OCR.

## Features

- **Dual OCR Support**: EasyOCR (default) and PaddleOCR engines
- **Data Extraction**: Automatic vendor, date, invoice number, and amount parsing
- **Image Preprocessing**: Built-in image enhancement and denoising
- **CLI Interface**: Simple command-line interface with rich formatting

## Installation

### Prerequisites

- Python 3.9+
- pip or uv

### OCR Engine Support

This tool supports two OCR engines:

1. **EasyOCR** (recommended, default)
   - Supports Python 3.8+
   - Easier installation, no platform-specific issues
   - Good accuracy for most documents

2. **PaddleOCR** (optional)
   - Supports Python 3.8-3.13 (not compatible with Python 3.14+)
   - May have installation issues on some platforms
   - Excellent accuracy for complex documents

The application will use EasyOCR if available, otherwise PaddleOCR.

### Install from source

**Option 1: Install with EasyOCR (recommended)**

```bash
pip install -e ".[ocr]"
```

**Option 2: Install with PaddleOCR (Python < 3.14 only)**

```bash
pip install -e ".[paddle]"
```

**Option 3: Install both engines**

```bash
pip install -e ".[ocr,paddle]"
```

**Option 4: Install from requirements.txt**

```bash
pip install -r requirements.txt
```

This installs EasyOCR by default. To use PaddleOCR, uncomment the paddle lines in `requirements.txt`.

## Usage

### Install the CLI

**With EasyOCR (recommended):**

```bash
pip install -e ".[ocr]"
```

**With PaddleOCR (Python < 3.14 only):**

```bash
pip install -e ".[paddle]"
```

**With both engines:**

```bash
pip install -e ".[ocr,paddle]"
```

### Run the CLI

```bash
bill-extract --help
```

### CLI Options

```
 Usage: bill-extract [OPTIONS]

 Extract information from bills and invoices.

╭─ Options ──────────────────────────────────────────────────────╮
│ --input PATH      -i  Input file or folder path              │
│ --output PATH    -o  Output directory                     │
│ --lang TEXT      -l  OCR language (default: fr)             │
│ --preprocess    -p  Enable image preprocessing           │
│ --verbose       -v  Enable verbose output               │
│ --debug         -d  Enable debug output                 │
│ --help          -h  Show this message and exit            │
╰───────────────────────────────────────────────────────────╯
```

### Extract from a single image

```bash
bill-extract --input invoice.jpg --output results/
```

### Extract from multiple images in a folder

```bash
bill-extract --input ./invoices/ --output ./output/
```

### Extract with preprocessing

```bash
bill-extract --input receipt.png --preprocess --verbose
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

### Core Dependencies
- **opencv-python** - Image processing
- **pillow** - Image handling
- **typer** - CLI framework
- **pydantic** - Data validation
- **rich** - Terminal rendering
- **tqdm** - Progress bars

### OCR Engines (at least one required)
- **easyocr** - Default OCR engine (Python 3.8+)
- **paddleocr** - Optional OCR engine (Python < 3.14 only)
- **paddlepaddle** - Deep learning framework for PaddleOCR

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
