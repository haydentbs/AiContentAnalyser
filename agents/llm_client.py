"""LLM client abstraction layer for different providers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
import random

from config.models import LLMConfig


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConnectionTestResult:
    """Result of testing LLM connection."""
    success: bool
    message: str
    response_time: Optional[float] = None
    error: Optional[str] = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    
    def __init__(self, message: str, troubleshooting: str = None):
        self.message = message
        self.troubleshooting = troubleshooting or "Check the LLM configuration and ensure the service is available."
        super().__init__(f"{message} | Troubleshooting: {self.troubleshooting}")


class LLMConnectionError(LLMClientError):
    """Exception for connection-related errors."""
    
    def __init__(self, message: str, troubleshooting: str = None):
        default_help = (
            "Verify that the LLM service is running and accessible. "
            "Check your network connection and ensure the base URL is correct."
        )
        super().__init__(message, troubleshooting or default_help)


class LLMRateLimitError(LLMClientError):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str, troubleshooting: str = None):
        default_help = (
            "The LLM service is currently rate limited. Wait before retrying, "
            "or consider upgrading your service tier for higher rate limits."
        )
        super().__init__(message, troubleshooting or default_help)


class LLMInvalidResponseError(LLMClientError):
    """Exception for invalid response errors."""
    
    def __init__(self, message: str, troubleshooting: str = None):
        default_help = (
            "The LLM service returned an invalid or unexpected response. "
            "Check your prompt format and parameters, or try a different model."
        )
        super().__init__(message, troubleshooting or default_help)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """Test the connection to the LLM provider."""
        pass
    
    async def generate_response_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ) -> LLMResponse:
        """Generate response with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    **kwargs
                )
            except LLMRateLimitError as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Rate limited, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                raise
            except (LLMConnectionError, LLMInvalidResponseError) as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(f"Request failed, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                # For unexpected errors, don't retry
                self.logger.error(f"Unexpected error in LLM request: {e}")
                raise LLMClientError(f"Unexpected error: {e}") from e
        
        # This should never be reached, but just in case
        raise last_exception or LLMClientError("Max retries exceeded")


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """Factory function to create appropriate LLM client based on configuration."""
    if config.provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient(config)
    elif config.provider == "ollama":
        from .ollama_client import OllamaClient
        return OllamaClient(config)
    elif config.provider == "lmstudio":
        from .lmstudio_client import LMStudioClient
        return LMStudioClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")