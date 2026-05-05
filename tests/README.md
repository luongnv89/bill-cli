# Bill Extract Test Suite

Automated testing suite for the `bill-extract` CLI tool using pytest and snapshot testing.

## Setup

### Install Dependencies
```bash
# Create and activate virtual environment (if not already active)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dev dependencies
pip install -e ".[dev,ocr]"
```

### Verify Installation
```bash
pytest --version
python -m bill_extract --help
```

## Running Tests

### Run All Tests
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_extract.py -v
pytest tests/test_snapshot.py -v
```

### Run With Coverage
```bash
pytest --cov=bill_extract --cov-report=term-missing
```

## Sample Invoices

- Location: `tests/samples/`
- Format: PNG images named `facture1.png` to `facture10.png`
- Count: 5-10 anonymized sample invoices
- Guidelines:
  - Anonymize all personal/company data
  - Use realistic but fake invoice layouts
  - Keep file sizes reasonable (<2MB per image)
  - Name sequentially: `facture1.png`, `facture2.png`, etc.

### Adding New Samples
1. Add PNG image to `tests/samples/`
2. Run tests to generate initial snapshot:
   ```bash
   pytest tests/test_extract.py::TestSnapshotValidation -v
   ```
3. Verify snapshot JSON in `tests/snapshots/`

## Snapshot Testing

We use `pytest-snapshot` (optional) and manual JSON snapshot comparison to validate extraction output consistency.

### Update Snapshots
If extraction logic changes intentionally:
```bash
# Remove old snapshots to regenerate
rm tests/snapshots/*.json

# Run tests to create new snapshots
pytest tests/test_extract.py -v
```

### Snapshot Files
- Location: `tests/snapshots/`
- Format: JSON files named after sample images (e.g., `facture1.json`)
- Contain structured extraction output for regression testing

## Test Structure

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Shared fixtures for samples, snapshots, CLI runner |
| `tests/test_extract.py` | Main test suite for module import, snapshots, CLI |
| `tests/test_snapshot.py` | Additional snapshot validation tests |
| `tests/samples/` | Anonymized sample invoice images |
| `tests/snapshots/` | Saved JSON output snapshots for regression testing |

## Troubleshooting

- **OCR errors**: Sample tests skip if OCR fails (missing model, etc.)
- **Missing samples**: Ensure 5-10 PNG images in `tests/samples/`
- **Import errors**: Verify virtual environment is activated and package is installed
