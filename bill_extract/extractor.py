"""Invoice/bill data extraction with French-specific patterns."""

import logging
import re
from datetime import date, datetime
from datetime import date as date_type
from typing import Any, Optional, Union

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
    value: Optional[Union[str, float]] = None
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
        r"date", r"facturé le", r"date de facturation",
        r"date d'émission", r"émis le"
    ]

    FRENCH_DATE_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_DATE_KEYWORDS)})\s*[:\s]*(\d{{1,2}}[\/\.\-]\d{{1,2}}[\/\.\-]\d{{2,4}})",
        r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        r"(\d{4}[\/\.\-]\d{1,2}[\/\.\-]\d{1,2})",
    ]

    FRENCH_AMOUNT_TTC_KEYWORDS = [
        r"total ttc", r"montant total", r"montant à payer",
        r"total à régler", r"total ttc", r"ttc"
    ]

    FRENCH_AMOUNT_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_AMOUNT_TTC_KEYWORDS)})\s*[:\s]*([\d\s.,]+)\s*(?:€|eur)?",
        r"(?i)(?:ttc)\s*[:\s]*([\d\s.,]+)",
    ]

    FRENCH_BILL_ID_KEYWORDS = [
        r"numéro de facture", r"n° facture", r"facture n°",
        r"référence", r"réf\.", r"numéro"
    ]

    FRENCH_BILL_ID_PATTERNS = [
        rf"(?i)(?:{'|'.join(FRENCH_BILL_ID_KEYWORDS)})\s*[:\s]*([A-Z0-9\-/]+)",
        r"([A-Z]{2,}\d{4,})",
    ]

    TOTAL_KEYWORDS = ["TOTAL", "GRAND TOTAL", "AMOUNT DUE", "BALANCE", "MONTANT TOTAL"]

    def __init__(self):
        self._confidence_threshold = 0.6

    def extract_date(
        self, ocr_results: list[dict[str, Any]]
    ) -> FieldExtractionResult:
        """Extract date from OCR results with French patterns."""
        sorted_results = sorted(
            ocr_results, key=lambda r: r.get("y_center", 0)
        )

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
                matched_text=best[2].strip()
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

    def extract_amount_ttc(
        self, ocr_results: list[dict[str, Any]]
    ) -> FieldExtractionResult:
        """Extract TTC amount from OCR results with French patterns."""
        sorted_results = sorted(
            ocr_results, key=lambda r: r.get("y_center", float("inf"))
        )
        text_lines = [(r.get("text", ""), r.get("confidence", 0.8)) for r in sorted_results]

        candidates = []
        for text, conf in text_lines:
            for pattern in self.FRENCH_AMOUNT_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
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
                value=best[0],
                confidence=min(best[1] + 0.1, 1.0),
                matched_text=best[2].strip()
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

    def extract_bill_id(
        self, ocr_results: list[dict[str, Any]]
    ) -> FieldExtractionResult:
        """Extract bill ID from OCR results with French patterns."""
        sorted_results = sorted(
            ocr_results, key=lambda r: r.get("y_center", 0)
        )

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
                value=best[0],
                confidence=min(best[1] + 0.1, 1.0),
                matched_text=best[2].strip()
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

        for fmt in ["%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y",
                    "%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        try:
            from dateutil import parser  # type: ignore[import-untyped]
            return parser.parse(date_str, dayfirst=True).date()  # type: ignore[no-any-return]
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
                        value=parsed.isoformat(),
                        confidence=confidence,
                        matched_text=text.strip()
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
                        value=amount,
                        confidence=conf * 0.5,
                        matched_text=text.strip()
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
                    value=bill_id,
                    confidence=confidence,
                    matched_text=text.strip()
                )

        return None

    def extract_all(
        self, ocr_results: list[dict[str, Any]]
    ) -> dict[str, FieldExtractionResult]:
        """Extract all fields from OCR results."""
        return {
            "date": self.extract_date(ocr_results),
            "amount_ttc": self.extract_amount_ttc(ocr_results),
            "bill_id": self.extract_bill_id(ocr_results),
        }  # type: ignore[return-value]


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
                bill.invoice_number = line

        bill.total = self._find_total(text_lines)
        bill.subtotal = self._find_subtotal(text_lines)
        bill.tax = self._find_tax(text_lines)

        return bill

    def extract_fields(
        self, ocr_results: list[dict[str, Any]]
    ) -> dict[str, FieldExtractionResult]:
        """Extract fields with French patterns and confidence scoring."""
        return self.field_extractor.extract_all(ocr_results)  # type: ignore[no-any-return]

    def _is_vendor(self, text: str) -> bool:
        """Check if text looks like a vendor name."""
        return len(text) > 3 and text[:1].isupper()

    def _is_invoice_number(self, text: str) -> bool:
        """Check if text is an invoice number."""
        text_upper = text.upper()
        return "INVOICE" in text_upper or "BILL" in text_upper or "INV" in text_upper

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
        matches = re.findall(r"[\d,]+\.?\d*", text)
        if matches:
            try:
                return float(matches[-1].replace(",", ""))
            except ValueError:
                pass
        return None

