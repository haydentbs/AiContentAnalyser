"""Unit tests for base LLM client functionality."""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from agents.llm_client import (
    BaseLLMClient,
    LLMResponse,
    ConnectionTestResult,
    LLMClientError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError
)
from config.models import LLMConfig


class TestBaseLLMClient:
    """Test the base LLM client functionality."""
    
    class MockLLMClient(BaseLLMClient):
        """Mock implementation for testing."""
        
        def __init__(self, config: LLMConfig, should_fail: bool = False, fail_type: str = "connection"):
            super().__init__(config)
            self.should_fail = should_fail
            self.fail_type = fail_type
            self.call_count = 0
        
        async def generate_response(self, prompt: str, system_prompt=None, max_tokens=None, **kwargs):
            self.call_count += 1
            
            if self.should_fail:
                if self.fail_type == "rate_limit":
                    raise LLMRateLimitError(
                        "Rate limit exceeded",
                        troubleshooting="Try again later or reduce request frequency"
                    )
                elif self.fail_type == "connection":
                    raise LLMConnectionError(
                        "Connection failed",
                        troubleshooting="Check your network connection and service status"
                    )
                elif self.fail_type == "invalid_response":
                    raise LLMInvalidResponseError(
                        "Invalid response",
                        troubleshooting="The response format was unexpected"
                    )
                else:
                    raise LLMClientError(
                        "Generic error",
                        troubleshooting="An unexpected error occurred"
                    )
            
            return LLMResponse(
                content="Test response",
                model="test-model",
                usage={"total_tokens": 10},
                metadata={"test": True}
            )
        
        async def test_connection(self):
            if self.should_fail:
                return ConnectionTestResult(
                    success=False, 
                    message="Test failed", 
                    error="Mock error with troubleshooting guidance"
                )
            return ConnectionTestResult(
                success=True, 
                message="Test passed", 
                response_time=0.1
            )
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.3
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, config):
        """Test successful response generation."""
        client = self.MockLLMClient(config)
        
        response = await client.generate_response("Test prompt")
        
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.usage["total_tokens"] == 10
        assert response.metadata["test"] is True
    
    @pytest.mark.asyncio
    async def test_generate_response_with_retry_success(self, config):
        """Test retry mechanism with eventual success."""
        client = self.MockLLMClient(config)
        
        response = await client.generate_response_with_retry("Test prompt")
        
        assert response.content == "Test response"
        assert client.call_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_response_with_retry_rate_limit(self, config):
        """Test retry mechanism with rate limiting."""
        client = self.MockLLMClient(config, should_fail=True, fail_type="rate_limit")
        
        with pytest.raises(LLMRateLimitError):
            await client.generate_response_with_retry("Test prompt", max_retries=2, base_delay=0.01)
        
        assert client.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_generate_response_with_retry_connection_error(self, config):
        """Test retry mechanism with connection errors."""
        client = self.MockLLMClient(config, should_fail=True, fail_type="connection")
        
        with pytest.raises(LLMConnectionError):
            await client.generate_response_with_retry("Test prompt", max_retries=1, base_delay=0.01)
        
        assert client.call_count == 2  # Initial + 1 retry
    
    @pytest.mark.asyncio
    async def test_generate_response_with_retry_no_retry_on_unexpected_error(self, config):
        """Test that unexpected errors don't trigger retries."""
        client = self.MockLLMClient(config, should_fail=True, fail_type="unexpected")
        
        with pytest.raises(LLMClientError):
            await client.generate_response_with_retry("Test prompt", max_retries=2, base_delay=0.01)
        
        assert client.call_count == 1  # No retries for unexpected errors


class TestLLMExceptions:
    """Test LLM exception classes and their troubleshooting information."""
    
    def test_llm_client_error_with_troubleshooting(self):
        """Test LLMClientError with custom troubleshooting."""
        error = LLMClientError("Test error", "Custom troubleshooting")
        assert "Test error" in str(error)
        assert "Custom troubleshooting" in str(error)
        assert error.message == "Test error"
        assert error.troubleshooting == "Custom troubleshooting"
    
    def test_llm_client_error_default_troubleshooting(self):
        """Test LLMClientError with default troubleshooting."""
        error = LLMClientError("Test error")
        assert "Test error" in str(error)
        assert "Check the LLM configuration" in str(error)
    
    def test_llm_connection_error_with_troubleshooting(self):
        """Test LLMConnectionError with custom troubleshooting."""
        error = LLMConnectionError("Connection failed", "Check your network")
        assert "Connection failed" in str(error)
        assert "Check your network" in str(error)
    
    def test_llm_connection_error_default_troubleshooting(self):
        """Test LLMConnectionError with default troubleshooting."""
        error = LLMConnectionError("Connection failed")
        assert "Connection failed" in str(error)
        assert "Verify that the LLM service is running" in str(error)
    
    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError."""
        error = LLMRateLimitError("Rate limited")
        assert "Rate limited" in str(error)
        assert "rate limited" in str(error).lower()
    
    def test_llm_invalid_response_error(self):
        """Test LLMInvalidResponseError."""
        error = LLMInvalidResponseError("Invalid response")
        assert "Invalid response" in str(error)
        assert "invalid or unexpected response" in str(error).lower()


class TestConnectionTestResult:
    """Test ConnectionTestResult functionality."""
    
    def test_successful_connection_result(self):
        """Test successful connection result."""
        result = ConnectionTestResult(
            success=True,
            message="Connection successful",
            response_time=0.5
        )
        assert result.success is True
        assert result.message == "Connection successful"
        assert result.response_time == 0.5
        assert result.error is None
    
    def test_failed_connection_result(self):
        """Test failed connection result."""
        result = ConnectionTestResult(
            success=False,
            message="Connection failed",
            error="Network error"
        )
        assert result.success is False
        assert result.message == "Connection failed"
        assert result.error == "Network error"
        assert result.response_time is None