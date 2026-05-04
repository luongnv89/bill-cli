"""Invoice/bill data extraction."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import date


class BillItem(BaseModel):
    """Individual line item from a bill."""
    description: str
    quantity: float = 1.0
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedBill(BaseModel):
    """Extracted bill/invoice information."""
    vendor: Optional[str] = None
    date: Optional[date] = None
    invoice_number: Optional[str] = None
    items: list[BillItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    currency: str = "USD"


class BillExtractor:
    """Extract structured data from bill images."""

    def __init__(self):
        self.vendor_patterns = {}
        self.field_patterns = {}

    def extract(self, ocr_results: list[dict[str, Any]]) -> ExtractedBill:
        """Extract bill data from OCR results."""
        bill = ExtractedBill()

        text_lines = [r["text"] for r in ocr_results]

        for i, line in enumerate(text_lines):
            if not bill.vendor and self._is_vendor(line):
                bill.vendor = line

            if not bill.date and self._extract_date(line):
                bill.date = self._extract_date(line)

            if not bill.invoice_number and self._is_invoice_number(line):
                bill.invoice_number = line

        bill.total = self._find_total(text_lines)
        bill.subtotal = self._find_subtotal(text_lines)
        bill.tax = self._find_tax(text_lines)

        return bill

    def _is_vendor(self, text: str) -> bool:
        """Check if text looks like a vendor name."""
        return len(text) > 3 and text[:1].isupper()

    def _is_invoice_number(self, text: str) -> bool:
        """Check if text is an invoice number."""
        text_upper = text.upper()
        return "INVOICE" in text_upper or "BILL" in text_upper or "INV" in text_upper

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract date from text."""
        import re
        patterns = [
            r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
            r"(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return date.today()
                except:
                    pass
        return None

    def _find_total(self, text_lines: list[str]) -> Optional[float]:
        """Find total amount."""
        keywords = ["TOTAL", "GRAND TOTAL", "AMOUNT DUE", "BALANCE"]
        for line in reversed(text_lines):
            for kw in keywords:
                if kw in line.upper():
                    return self._extract_amount(line)
        return None

    def _find_subtotal(self, text_lines: list[str]) -> Optional[float]:
        """Find subtotal amount."""
        for line in text_lines:
            if "SUBTOTAL" in line.upper() or "SUB TOTAL" in line.upper():
                return self._extract_amount(line)
        return None

    def _find_tax(self, text_lines: list[str]) -> Optional[float]:
        """Find tax amount."""
        for line in text_lines:
            if "TAX" in line.upper() and "TOTAL" not in line.upper():
                return self._extract_amount(line)
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract numeric amount from text."""
        import re
        matches = re.findall(r"[\d,]+\.?\d*", text)
        if matches:
            try:
                return float(matches[-1].replace(",", ""))
            except ValueError:
                pass
        return None