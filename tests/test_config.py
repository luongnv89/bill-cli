"""Tests for pattern configuration loading."""

import tempfile
from pathlib import Path

import pytest

from bill_extract.config import (
    load_patterns,
    get_date_patterns,
    get_amount_patterns,
    get_id_patterns,
    DEFAULT_PATTERNS_PATH,
)


class TestLoadPatterns:
    """Tests for load_patterns function."""

    def test_load_default_patterns(self):
        """Test loading default patterns."""
        patterns = load_patterns()
        
        assert "date" in patterns
        assert "amount" in patterns
        assert "id" in patterns
        assert len(patterns["date"]) > 0
        assert len(patterns["amount"]) > 0
        assert len(patterns["id"]) > 0

    def test_load_custom_patterns(self):
        """Test loading custom patterns from file."""
        custom_yaml = """
patterns:
  date:
    - name: custom_date
      pattern: "2026-01-01"
      keywords: ["date"]
      confidence: 1.0
  amount:
    - name: custom_amount
      pattern: "100 EUR"
      keywords: ["total"]
      confidence: 1.0
  id:
    - name: custom_id
      pattern: "#123"
      keywords: ["invoice"]
      confidence: 1.0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(custom_yaml)
            temp_path = f.name
        
        try:
            patterns = load_patterns(temp_path)
            
            assert "date" in patterns
            assert len(patterns["date"]) == 1
            assert patterns["date"][0]["name"] == "custom_date"
        finally:
            Path(temp_path).unlink()

    def test_fallback_to_default_when_missing(self):
        """Test fallback to default when custom file doesn't exist."""
        patterns = load_patterns("/nonexistent/path.yaml")
        
        assert "date" in patterns
        assert "amount" in patterns
        assert "id" in patterns


class TestGetPatterns:
    """Tests for pattern getter functions."""

    def test_get_date_patterns(self):
        """Test get_date_patterns."""
        patterns = load_patterns()
        date_patterns = get_date_patterns(patterns)
        
        assert len(date_patterns) > 0
        assert all("pattern" in p for p in date_patterns)

    def test_get_amount_patterns(self):
        """Test get_amount_patterns."""
        patterns = load_patterns()
        amount_patterns = get_amount_patterns(patterns)
        
        assert len(amount_patterns) > 0
        assert all("pattern" in p for p in amount_patterns)

    def test_get_id_patterns(self):
        """Test get_id_patterns."""
        patterns = load_patterns()
        id_patterns = get_id_patterns(patterns)
        
        assert len(id_patterns) > 0
        assert all("pattern" in p for p in id_patterns)