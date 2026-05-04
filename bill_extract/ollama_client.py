"""Ollama client for post-processing extracted data."""

import json
import logging
import os
import subprocess
from typing import Any, Optional
from dataclasses import dataclass

from bill_extract.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama post-processing."""
    enabled: bool = False
    model: str = "llama3.2:latest"
    base_url: str = "http://localhost:11434"
    confidence_threshold: float = 0.95
    timeout: int = 30
    max_retries: int = 2


class OllamaClient:
    """Client for Ollama API for post-processing extraction results."""

    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama client.
        
        Args:
            config: Optional Ollama configuration. If None, uses defaults (disabled).
        """
        self.config = config or OllamaConfig()
        self._available = None
        self._perf_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "accuracy_improvements": 0,
        }

    @property
    def is_available(self) -> bool:
        """Check if Ollama is available and responding."""
        if self._available is not None:
            return self._available
        
        if not self.config.enabled:
            self._available = False
            return False
        
        self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Check if Ollama service is available."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and self.config.model.split(":")[0] in result.stdout:
                logger.info(f"Ollama is available with model {self.config.model}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Ollama not available: {e}")
        
        logger.warning(f"Ollama not available, using rule-based extraction only")
        return False

    def post_process(
        self,
        ocr_text: str,
        extracted_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Post-process extracted data using Ollama.
        
        Args:
            ocr_text: Raw OCR text.
            extracted_data: Extracted data from rule-based extraction.
        
        Returns:
            Improved extraction data or original if Ollama fails.
        """
        if not self.is_available or not self.config.enabled:
            return extracted_data
        
        if self._is_high_confidence(extracted_data):
            logger.debug(f"High confidence ({self.config.confidence_threshold}), skipping Ollama post-processing")
            return extracted_data
        
        prompt = self._build_prompt(ocr_text, extracted_data)
        
        for attempt in range(self.config.max_retries):
            try:
                result = self._call_ollama(prompt)
                if result:
                    improved = self._parse_ollama_response(result, extracted_data)
                    if improved:
                        self._perf_stats["successful_requests"] += 1
                        if self._is_high_confidence(improved):
                            self._perf_stats["accuracy_improvements"] += 1
                        return improved
            except Exception as e:
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                self._perf_stats["failed_requests"] += 1
        
        logger.warning("Ollama post-processing failed, using rule-based extraction")
        return extracted_data

    def _is_high_confidence(self, data: dict[str, Any]) -> bool:
        """Check if extraction has high confidence."""
        confidence_score = data.get("_confidence", 0.0)
        return confidence_score >= self.config.confidence_threshold

    def _build_prompt(self, ocr_text: str, extracted_data: dict[str, Any]) -> str:
        """Build prompt for Ollama."""
        return f"""You are a bill/invoice data extraction expert. Given the OCR text from a bill and 
extracted fields, verify and correct any errors.

OCR Text:
{ocr_text}

Current Extracted Data:
{json.dumps(extracted_data, indent=2, default=str)}

Respond with a JSON object containing:
- date: Verified/corrected date (YYYY-MM-DD format) or null if not found
- amount: Verified/corrected total amount as number or null if not found  
- invoice_number: Verified/corrected invoice number or null if not found
- confidence: Confidence score (0-1) for the extraction
- corrections: List of any corrections made

If no corrections needed, just return the original data with confidence: 1.0.
Only respond with valid JSON, no explanations."""

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["ollama", "run", self.config.model, prompt],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._perf_stats["total_requests"] += 1
            self._perf_stats["total_latency_ms"] += elapsed_ms
            
            if result.returncode == 0 and result.stdout:
                logger.debug(f"Ollama response in {elapsed_ms:.0f}ms")
                return result.stdout
        except subprocess.TimeoutExpired:
            logger.warning(f"Ollama request timed out after {self.config.timeout}s")
        except FileNotFoundError:
            logger.warning("ollama command not found")
        
        return None

    def _parse_ollama_response(
        self,
        response: str,
        original: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Parse Ollama response into extraction data."""
        import re
        
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                improved = json.loads(json_match.group(0))
                improved["_post_processed"] = True
                improved["_model"] = self.config.model
                return improved
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse Ollama response: {e}")
        
        return None

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance monitoring statistics."""
        stats = self._perf_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_requests"]
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["improvement_rate"] = stats["accuracy_improvements"] / stats["total_requests"]
        else:
            stats["avg_latency_ms"] = 0.0
            stats["success_rate"] = 0.0
            stats["improvement_rate"] = 0.0
        
        return stats

    def reset_stats(self):
        """Reset performance statistics."""
        self._perf_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "accuracy_improvements": 0,
        }


def load_ollama_config(config_dict: Optional[dict] = None) -> OllamaConfig:
    """Load Ollama configuration from dict.
    
    Args:
        config_dict: Optional configuration dict (from YAML).
    
    Returns:
        OllamaConfig instance.
    """
    if config_dict is None:
        return OllamaConfig()
    
    return OllamaConfig(
        enabled=config_dict.get("enabled", False),
        model=config_dict.get("model", "llama3.2:latest"),
        base_url=config_dict.get("base_url", "http://localhost:11434"),
        confidence_threshold=config_dict.get("confidence_threshold", 0.95),
        timeout=config_dict.get("timeout", 30),
        max_retries=config_dict.get("max_retries", 2),
    )