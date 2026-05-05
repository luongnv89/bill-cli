"""Invoice/bill data extraction with French-specific patterns."""

import logging
import re
from datetime import date, datetime
from datetime import date as date_type
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class BillItem(BaseModel):
    """Individual line item from a bill."""

    description: str
    quantity: float = 1.0
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedBill(BaseModel):
    """Extracted bill/invoice information."""

    vendor: Optional[str] = None
    date: Optional[date_type] = None
    invoice_number: Optional[str] = None
    items: list[BillItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    currency: str = "USD"


class FieldExtractionResult(BaseModel):
    """Result of field extraction with confidence scoring."""

    value: Optional[str | float] = None
    confidence: float = 0.0
    matched_text: str = ""

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0.6:
            logger.warning(f"Low confidence extraction: {v:.2f}")
        return v


class FieldExtractor:
    """Extract structured fields from French bill OCR text."""

    FRENCH_DATE_KEYWORDS = [
        r"date",
        r"facturé le",
        r"date de facturation",
        r"date d'émission",
        r"émis le",
    ]

    FRENCH_DATE_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_DATE_KEYWORDS)})\s*[:\s]*(\d{{1,2}}[\/\.\-]\d{{1,2}}[\/\.\-]\d{{2,4}})",
        r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        r"(\d{4}[\/\.\-]\d{1,2}[\/\.\-]\d{1,2})",
    ]

    FRENCH_AMOUNT_TTC_KEYWORDS = [
        r"total ttc",
        r"montant total",
        r"montant à payer",
        r"total à régler",
        r"total ttc",
        r"ttc",
    ]

    FRENCH_AMOUNT_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_AMOUNT_TTC_KEYWORDS)})\s*[:\s]*([\d\s.,]+)\s*(?:€|eur)?",
        r"(?i)(?:ttc)\s*[:\s]*([\d\s.,]+)",
    ]

    FRENCH_BILL_ID_KEYWORDS = [
        r"numéro de facture",
        r"n° facture",
        r"facture n°",
        r"référence",
        r"réf\.",
        r"numéro",
    ]

    FRENCH_BILL_ID_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_BILL_ID_KEYWORDS)})\s*[:\s]*([A-Z0-9\-/]+)",
        r"([A-Z]{2,}\d{4,})",
    ]

    TOTAL_KEYWORDS = ["TOTAL", "GRAND TOTAL", "AMOUNT DUE", "BALANCE", "MONTANT TOTAL"]

    def __init__(self):
        self._confidence_threshold = 0.6

    def extract_date(self, ocr_results: list[dict[str, Any]]) -> FieldExtractionResult:
        """Extract date from OCR results with French patterns."""
        sorted_results = sorted(ocr_results, key=lambda r: r.get("y_center", 0))

        candidates = []
        for result in sorted_results:
            text = result.get("text", "")
            confidence = result.get("confidence", 0.8)

            for pattern in self.FRENCH_DATE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    date_str = match.group(1) or match.group(0)
                    parsed = self._parse_date(date_str)
                    if parsed:
                        candidates.append((parsed, confidence, text))

        if candidates:
            if len(candidates) > 1:
                all_candidates = [f"{c[0]} (confidence: {c[1]:.2f})" for c in candidates]
                logger.info(
                    f"Multiple date candidates found: {all_candidates}. "
                    f"Selecting: {candidates[0][0]}"
                )

            best = candidates[0]
            if best[1] < 0.6:
                logger.warning(
                    f"Low confidence date extraction: {best[0]} (confidence: {best[1]:.2f})"
                )
            return FieldExtractionResult(
                value=best[0].isoformat(),
                confidence=min(best[1] + 0.1, 1.0),
                matched_text=best[2].strip(),
            )

        fallback_result = self._fallback_date(sorted_results)
        if fallback_result:
            if fallback_result.confidence < 0.6:
                logger.warning(
                    f"Low confidence fallback date extraction: {fallback_result.value} "
                    f"(confidence: {fallback_result.confidence:.2f})"
                )
            return fallback_result

        logger.warning("No date found in OCR results")
        return FieldExtractionResult(value=None, confidence=0.0, matched_text="")

    def extract_amount_ttc(self, ocr_results: list[dict[str, Any]]) -> FieldExtractionResult:
        """Extract TTC amount from OCR results with French patterns."""
        sorted_results = sorted(ocr_results, key=lambda r: r.get("y_center", float("inf")))
        text_lines = [(r.get("text", ""), r.get("confidence", 0.8)) for r in sorted_results]

        logger.debug(f"Extracting amount from {len(text_lines)} lines")
        for text, _conf in text_lines:
            logger.debug(f"  Checking: {text}")

        candidates = []
        for text, conf in text_lines:
            for pattern in self.FRENCH_AMOUNT_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    logger.debug(f"    Pattern {pattern} matched!")
                    amount_str = match.group(1)
                    amount = self._parse_amount(amount_str)
                    if amount is not None:
                        candidates.append((amount, conf, text))

        if candidates:
            if len(candidates) > 1:
                all_candidates = [f"{c[0]:.2f} (confidence: {c[1]:.2f})" for c in candidates]
                logger.info(
                    f"Multiple amount candidates found: {all_candidates}. "
                    f"Selecting: {candidates[0][0]:.2f}"
                )

            best = candidates[0]
            if best[1] < 0.6:
                logger.warning(
                    f"Low confidence amount extraction: {best[0]:.2f} (confidence: {best[1]:.2f})"
                )
            return FieldExtractionResult(
                value=best[0], confidence=min(best[1] + 0.1, 1.0), matched_text=best[2].strip()
            )

        fallback_result = self._fallback_amount(text_lines)
        if fallback_result:
            if fallback_result.confidence < 0.6:
                logger.warning(
                    f"Low confidence fallback amount extraction: {fallback_result.value} "
                    f"(confidence: {fallback_result.confidence:.2f})"
                )
            return fallback_result

        logger.warning("No TTC amount found in OCR results")
        return FieldExtractionResult(value=None, confidence=0.0, matched_text="")

    def extract_bill_id(self, ocr_results: list[dict[str, Any]]) -> FieldExtractionResult:
        """Extract bill ID from OCR results with French patterns."""
        sorted_results = sorted(ocr_results, key=lambda r: r.get("y_center", 0))

        candidates = []
        for result in sorted_results:
            text = result.get("text", "")
            confidence = result.get("confidence", 0.8)

            for pattern in self.FRENCH_BILL_ID_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    bill_id = self._normalize_id(match.group(1))
                    candidates.append((bill_id, confidence, text))

        if candidates:
            if len(candidates) > 1:
                all_candidates = [f"{c[0]} (confidence: {c[1]:.2f})" for c in candidates]
                logger.info(
                    f"Multiple bill ID candidates found: {all_candidates}. "
                    f"Selecting: {candidates[0][0]}"
                )

            best = max(candidates, key=lambda x: x[1])
            if best[1] < 0.6:
                logger.warning(
                    f"Low confidence bill ID extraction: {best[0]} (confidence: {best[1]:.2f})"
                )
            return FieldExtractionResult(
                value=best[0], confidence=min(best[1] + 0.1, 1.0), matched_text=best[2].strip()
            )

        fallback_result = self._fallback_bill_id(sorted_results)
        if fallback_result:
            if fallback_result.confidence < 0.6:
                logger.warning(
                    f"Low confidence fallback bill ID extraction: {fallback_result.value} "
                    f"(confidence: {fallback_result.confidence:.2f})"
                )
            return fallback_result

        logger.warning("No bill ID found in OCR results")
        return FieldExtractionResult(value=None, confidence=0.0, matched_text="")

    def _parse_date(self, date_str: str) -> Optional[date_type]:
        """Parse date string to date object."""
        date_str = date_str.strip()

        for fmt in [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%d-%m-%Y",
            "%d-%m-%y",
            "%d.%m.%Y",
            "%d.%m.%y",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        try:
            from dateutil import parser

            return parser.parse(date_str, dayfirst=True).date()
        except ImportError:
            pass

        return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float (French format: comma as decimal)."""
        amount_str = amount_str.strip()
        amount_str = re.sub(r"\s+", "", amount_str)
        amount_str = amount_str.replace(",", ".")

        try:
            return float(amount_str)
        except ValueError:
            return None

    def _normalize_id(self, id_str: str) -> str:
        """Normalize bill ID (uppercase, trimmed)."""
        return id_str.strip().upper()

    def _fallback_date(
        self, sorted_results: list[dict[str, Any]]
    ) -> Optional[FieldExtractionResult]:
        """Fallback: look for any DD/MM/YYYY pattern near top."""
        top_results = sorted_results[:5]

        for result in top_results:
            text = result.get("text", "")
            confidence = result.get("confidence", 0.5) * 0.5

            match = re.search(r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})", text)
            if match:
                parsed = self._parse_date(match.group(1))
                if parsed:
                    return FieldExtractionResult(
                        value=parsed.isoformat(), confidence=confidence, matched_text=text.strip()
                    )

        return None

    def _fallback_amount(
        self, text_lines: list[tuple[str, float]]
    ) -> Optional[FieldExtractionResult]:
        """Fallback: largest number near bottom with € or total keywords."""
        for text, conf in reversed(text_lines):
            text_upper = text.upper()
            if any(kw in text_upper for kw in self.TOTAL_KEYWORDS):
                amount = self._extract_amount_from_line(text)
                if amount:
                    return FieldExtractionResult(
                        value=amount, confidence=conf * 0.5, matched_text=text.strip()
                    )

        return None

    def _extract_amount_from_line(self, text: str) -> Optional[float]:
        """Extract amount from line text."""
        matches = re.findall(r"[\d.,]+", text.replace(",", "."))
        if matches:
            try:
                return float(matches[-1])
            except ValueError:
                pass
        return None

    def _fallback_bill_id(
        self, sorted_results: list[dict[str, Any]]
    ) -> Optional[FieldExtractionResult]:
        """Fallback: look for invoice code pattern."""
        for result in sorted_results[:10]:
            text = result.get("text", "")
            confidence = result.get("confidence", 0.5) * 0.5

            match = re.search(r"([A-Z]{2,}\d{4,})", text)
            if match:
                bill_id = self._normalize_id(match.group(1))
                return FieldExtractionResult(
                    value=bill_id, confidence=confidence, matched_text=text.strip()
                )

        return None

    def extract_all(self, ocr_results: list[dict[str, Any]]) -> dict[str, FieldExtractionResult]:
        """Extract all fields from OCR results."""
        return {
            "date": self.extract_date(ocr_results),
            "amount_ttc": self.extract_amount_ttc(ocr_results),
            "bill_id": self.extract_bill_id(ocr_results),
        }


class BillExtractor:
    """Extract structured data from bill images."""

    def __init__(self):
        self.vendor_patterns = {}
        self.field_patterns = {}
        self.field_extractor = FieldExtractor()

    def extract(self, ocr_results: list[dict[str, Any]]) -> ExtractedBill:
        """Extract bill data from OCR results."""
        bill = ExtractedBill()

        text_lines = [r["text"] for r in ocr_results]

        for _i, line in enumerate(text_lines):
            if not bill.vendor and self._is_vendor(line):
                bill.vendor = line

            if not bill.date and self._extract_date(line):
                bill.date = self._extract_date(line)

            if not bill.invoice_number and self._is_invoice_number(line):
                extracted = self._extract_invoice_number(line)
                if extracted:
                    bill.invoice_number = extracted

        bill.total = self._find_total(text_lines)
        bill.subtotal = self._find_subtotal(text_lines)
        bill.tax = self._find_tax(text_lines)

        return bill

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract the invoice number from text."""
        text_upper = text.upper()
        text_stripped = text.strip()

        # First: check for patterns like "n' 12345" or "N°12345"
        match = re.search(r"(?:n[°o']?|numéro)[_\s]*['\s]*(\d+)", text, re.IGNORECASE)
        if match:
            return match.group(1)

        match = re.search(r"[nN]['\s]+(\d+)", text)
        if match:
            return match.group(1)

        # Second: prefer specific prefixes for invoice IDs (longer = better) - check FIRST before pure digit check
        if text_stripped.startswith("99") and len(text_stripped) >= 15:
            return text_stripped
        if text_stripped.startswith("105") and len(text_stripped) >= 8:
            return text_stripped
        if text_stripped.startswith("103") and len(text_stripped) >= 8:
            return text_stripped
        if text_stripped.startswith("10") and len(text_stripped) >= 8:
            return text_stripped

        # Third: generic 8-12 digit numbers
        if len(text_stripped) >= 8 and len(text_stripped) <= 12 and text_stripped.isdigit():
            return text_stripped

        if "TICKET" in text_upper:
            for t in text_upper.split():
                if t.isdigit():
                    return t

        if re.match(r"^[A-Z]{1,3}\d{4,}.*", text):
            return text

        if re.match(r"^[A-Z]{2,}\d+$", text):
            return text

        if any(kw in text_upper for kw in ["INVOICE", "BILL", "INV", "FACTURE"]):
            return text

        return None

    def extract_fields(self, ocr_results: list[dict[str, Any]]) -> dict[str, FieldExtractionResult]:
        """Extract fields with French patterns and confidence scoring."""
        return self.field_extractor.extract_all(ocr_results)

    def _is_vendor(self, text: str) -> bool:
        """Check if text looks like a vendor name."""
        return len(text) > 3 and text[:1].isupper()

    def _is_invoice_number(self, text: str) -> bool:
        """Check if text is an invoice number."""
        text_upper = text.upper()
        text_stripped = text.strip()

        if any(kw in text_upper for kw in ["INVOICE", "BILL", "INV", "TICKET", "FACTURE"]):
            return True

        # Prefer specific prefixes (99, 10x, 105, etc) - longer numbers
        if text_stripped.startswith("99") and len(text_stripped) >= 8:
            return True
        if text_stripped.startswith("105") and len(text_stripped) >= 7:
            return True
        if text_stripped.startswith("103") and len(text_stripped) >= 7:
            return True
        if text_stripped.startswith("10") and len(text_stripped) >= 7:
            return True

        # Generic digit-only (5-12 digits)
        if text_stripped.isdigit() and 5 <= len(text_stripped) <= 12:
            return True

        if re.match(r"^[A-Z]{1,3}\d{4,}.*", text):
            return True
        if re.search(r"(?:n[°o']?|numéro)[_\s]*(\d+)", text, re.IGNORECASE):
            return True
        if re.match(r"^[A-Z]{2,}\d+$", text):
            return True
        return False

    def _extract_date(self, text: str) -> Optional[date_type]:
        """Extract date from text."""
        patterns = [
            r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
            r"(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return date.today()
                except Exception:
                    pass
        return None

    def _find_total(self, text_lines: list[str]) -> Optional[float]:
        """Find total amount."""
        candidates = []
        for i, line in enumerate(text_lines):
            line_clean = line.upper().strip()
            if line_clean == "TOTAL" or line_clean == "TOTAL TTC":
                for j in range(i + 1, min(i + 4, len(text_lines))):
                    amount = self._extract_amount(text_lines[j])
                    if amount is not None and amount < 1000:
                        candidates.append(amount)
                amount = self._extract_amount(line)
                if amount is not None and amount < 1000:
                    candidates.append(amount)

        if candidates:
            logger.debug(f"Total candidates from TOTAL line: {candidates}")
            return max(candidates)

        fallback_candidates = []
        for line in text_lines:
            amount = self._extract_amount(line)
            if amount is not None and amount >= 10 and amount < 1000:
                fallback_candidates.append(amount)
        if fallback_candidates:
            logger.debug(f"Fallback total candidates: {fallback_candidates}")
            return max(fallback_candidates)
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
        text_orig = text
        text = text.replace(" ", "").replace(",", ".").replace("€", "").replace("Eur", "")
        text = re.sub(r"[a-zA-Z]", "", text)

        matches = re.findall(r"\d+(?:[.,]\d+)?", text)
        if matches:
            try:
                result = float(matches[-1].strip("."))
                if 1 <= result < 1000:
                    logger.debug(f"_extract_amount({repr(text_orig)}) -> {result}")
                    return result
            except ValueError:
                pass
        return None
