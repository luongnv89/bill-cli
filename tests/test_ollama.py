"""Tests for Ollama client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date

from bill_extract.ollama_client import (
    OllamaClient,
    OllamaConfig,
    load_ollama_config,
)


class TestOllamaConfig:
    """Tests for OllamaConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = OllamaConfig()
        assert config.enabled is False
        assert config.model == "llama3.2:latest"
        assert config.confidence_threshold == 0.95

    def test_custom_config(self):
        """Test custom configuration."""
        config = OllamaConfig(
            enabled=True,
            model="llama3.2:1b",
            confidence_threshold=0.90,
        )
        assert config.enabled is True
        assert config.model == "llama3.2:1b"
        assert config.confidence_threshold == 0.90


class TestOllamaClient:
    """Tests for OllamaClient."""

    def test_client_disabled_by_default(self):
        """Test client is disabled by default."""
        client = OllamaClient()
        assert client.is_available is False

    def test_client_not_available_when_disabled(self):
        """Test client not available when disabled."""
        config = OllamaConfig(enabled=False)
        client = OllamaClient(config)
        assert client.is_available is False

    @patch("subprocess.run")
    def test_client_available_when_enabled(self, mock_run):
        """Test client available when enabled and model present."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="llama3.2:latest\n",
        )
        config = OllamaConfig(enabled=True)
        client = OllamaClient(config)
        assert client.is_available is True

    @patch("subprocess.run")
    def test_client_not_available_when_ollama_missing(self, mock_run):
        """Test client not available when Ollama not installed."""
        mock_run.side_effect = FileNotFoundError()
        config = OllamaConfig(enabled=True)
        client = OllamaClient(config)
        assert client.is_available is False

    def test_is_high_confidence(self):
        """Test confidence check."""
        client = OllamaClient(OllamaConfig(confidence_threshold=0.95))
        high_conf = {"_confidence": 0.96}
        low_conf = {"_confidence": 0.80}
        assert client._is_high_confidence(high_conf) is True
        assert client._is_high_confidence(low_conf) is False

    def test_is_high_confidence_no_score(self):
        """Test confidence with no score."""
        client = OllamaClient(OllamaConfig(confidence_threshold=0.95))
        assert client._is_high_confidence({}) is False

    @patch("subprocess.run")
    def test_post_process_skips_high_confidence(self, mock_run):
        """Test post-process skips high confidence extraction."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="llama3.2:latest\n",
        )
        config = OllamaConfig(enabled=True, confidence_threshold=0.95)
        client = OllamaClient(config)
        _ = client.is_available
        
        high_conf_data = {"date": "2026-01-15", "amount": 100.0, "_confidence": 0.96}
        result = client.post_process("some text", high_conf_data)
        
        assert result == high_conf_data
        mock_run.assert_called

    def test_performance_stats_empty(self):
        """Test performance stats when no requests."""
        client = OllamaClient()
        stats = client.get_performance_stats()
        
        assert stats["total_requests"] == 0
        assert stats["avg_latency_ms"] == 0.0
        assert stats["success_rate"] == 0.0

    def test_reset_stats(self):
        """Test stats reset."""
        client = OllamaClient()
        client._perf_stats["total_requests"] = 5
        client.reset_stats()
        
        assert client._perf_stats["total_requests"] == 0


class TestLoadOllamaConfig:
    """Tests for load_ollama_config."""

    def test_load_from_none(self):
        """Test loading from None returns default."""
        config = load_ollama_config(None)
        assert config.enabled is False
        assert config.model == "llama3.2:latest"

    def test_load_from_dict(self):
        """Test loading from dict."""
        config_dict = {
            "enabled": True,
            "model": "custom-model:latest",
            "confidence_threshold": 0.85,
        }
        config = load_ollama_config(config_dict)
        
        assert config.enabled is True
        assert config.model == "custom-model:latest"
        assert config.confidence_threshold == 0.85

    def test_load_with_defaults(self):
        """Test loading uses defaults for missing keys."""
        config_dict = {"enabled": True}
        config = load_ollama_config(config_dict)
        
        assert config.enabled is True
        assert config.model == "llama3.2:latest"
        assert config.timeout == 30