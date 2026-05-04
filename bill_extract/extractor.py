"""Invoice/bill data extraction."""

import re
import logging
from typing import Any, Optional
from datetime import date

from pydantic import BaseModel, Field

from bill_extract.logging import get_logger
from bill_extract.config import load_patterns, get_date_patterns, get_amount_patterns, get_id_patterns

logger = get_logger(__name__)


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

    def __init__(self, patterns_config: Optional[dict] = None):
        """Initialize extractor with optional custom patterns.
        
        Args:
            patterns_config: Optional dictionary of patterns loaded from YAML.
                             If None, loads default patterns.
        """
        if patterns_config:
            self.patterns = patterns_config
        else:
            self.patterns = load_patterns()
        
        self.date_patterns = get_date_patterns(self.patterns)
        self.amount_patterns = get_amount_patterns(self.patterns)
        self.id_patterns = get_id_patterns(self.patterns)
        
        logger.debug(f"Loaded {len(self.date_patterns)} date patterns")
        logger.debug(f"Loaded {len(self.amount_patterns)} amount patterns")
        logger.debug(f"Loaded {len(self.id_patterns)} id patterns")

    def extract(self, ocr_results: list[dict[str, Any]]) -> ExtractedBill:
        """Extract bill data from OCR results."""
        bill = ExtractedBill()

        text_lines = [r["text"] for r in ocr_results]

        for i, line in enumerate(text_lines):
            if not bill.vendor and self._is_vendor(line):
                bill.vendor = line

            if not bill.date and self._extract_date(line):
                bill.date = self._extract_date(line)

            if not bill.invoice_number and self._extract_id(line):
                bill.invoice_number = self._extract_id(line)

        bill.total = self._find_amount(text_lines, "total")
        bill.subtotal = self._find_amount(text_lines, "subtotal")
        bill.tax = self._find_amount(text_lines, "tax")

        return bill

    def _is_vendor(self, text: str) -> bool:
        """Check if text looks like a vendor name."""
        return len(text) > 3 and text[:1].isupper()

    def _extract_id(self, text: str) -> Optional[str]:
        """Extract invoice ID from text using configured patterns."""
        text_upper = text.upper()
        
        for pattern_config in self.id_patterns:
            pattern = pattern_config.get("pattern", "")
            keywords = pattern_config.get("keywords", [])
            
            if keywords and not any(kw.upper() in text_upper for kw in keywords):
                continue
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
                logger.debug(f"Found ID with pattern '{pattern_config.get('name')}': {value}")
                return value.upper().strip()
        
        if "INVOICE" in text_upper or "BILL" in text_upper or "INV" in text_upper:
            return text.strip()
        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract date from text using configured patterns."""
        text_upper = text.upper()
        
        for pattern_config in self.date_patterns:
            pattern = pattern_config.get("pattern", "")
            keywords = pattern_config.get("keywords", [])
            
            if keywords and not any(kw.upper() in text_upper for kw in keywords):
                continue
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1) if match.lastindex else match.group(0)
                parsed = self._parse_date(date_str)
                if parsed:
                    logger.debug(f"Found date with pattern '{pattern_config.get('name')}': {parsed}")
                    return parsed
        
        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        import sys
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
            "%Y/%m/%d", "%Y-%m-%d",
            "%d %b %Y", "%d %B %Y",
        ]
        
        month_fr = {
            "jan": 1, "janvier": 1,
            "fév": 2, "février": 2,
            "mar": 3, "mars": 3,
            "avr": 4, "avril": 4,
            "mai": 5,
            "juin": 6,
            "juil": 7, "juillet": 7,
            "aoû": 8, "août": 8,
            "sep": 9, "septembre": 9,
            "oct": 10, "octobre": 10,
            "nov": 11, "novembre": 11,
            "déc": 12, "décembre": 12,
        }
        
        for fmt in formats:
            try:
                return date.fromisoformat(date_str)
            except (ValueError, TypeError):
                pass
            
            try:
                return date.strptime(date_str.replace(" ", "-"), fmt)
            except ValueError:
                pass
        
        date_lower = date_str.lower()
        for month_name, month_num in month_fr.items():
            if month_name in date_lower:
                import re
                m = re.search(r"(\d{1,2})[- ]?" + month_name + r"[- ]?(\d{2,4})", date_lower)
                if m:
                    try:
                        return date(int(m.group(2)), month_num, int(m.group(1)))
                    except ValueError:
                        pass
        
        return None

    def _find_amount(self, text_lines: list[str], amount_type: str) -> Optional[float]:
        """Find amount from text lines using configured patterns."""
        lines_to_search = text_lines if amount_type != "total" else reversed(text_lines)
        
        for line in lines_to_search:
            line_upper = line.upper()
            
            for pattern_config in self.amount_patterns:
                pattern = pattern_config.get("pattern", "")
                keywords = pattern_config.get("keywords", [])
                
                if keywords:
                    kw_match = any(kw.upper() in line_upper for kw in keywords)
                    if amount_type == "total" and not any(kw.upper() in line_upper for kw in ["TOTAL", "BALANCE", "PAYER"]):
                        continue
                    if amount_type == "subtotal" and "SUBTOTAL" not in line_upper and "SUB TOTAL" not in line_upper:
                        continue
                    if amount_type == "tax" and "TAX" not in line_upper:
                        continue
                    if not kw_match:
                        continue
                
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    amount_str = match.group(1) if match.lastindex else match.group(0)
                    try:
                        value = float(amount_str.replace(",", ".").replace(" ", ""))
                        if value > 0:
                            logger.debug(f"Found {amount_type} amount with pattern '{pattern_config.get('name')}': {value}")
                            return value
                    except ValueError:
                        pass
        
        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract numeric amount from text (legacy method)."""
        matches = re.findall(r"[\d,]+\.?\d*", text)
        if matches:
            try:
                return float(matches[-1].replace(",", "."))
            except ValueError:
                pass
        return None