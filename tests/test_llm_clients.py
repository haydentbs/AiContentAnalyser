"""Unit tests for LLM client implementations."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from agents.llm_client import (
    BaseLLMClient,
    LLMResponse,
    ConnectionTestResult,
    LLMClientError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    create_llm_client
)
from agents.openai_client import OpenAIClient
from agents.ollama_client import OllamaClient
from agents.lmstudio_client import LMStudioClient
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


class TestOpenAIClient:
    """Test OpenAI client implementation."""
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.3
        )
    
    def test_init_without_openai_package(self, config):
        """Test initialization when OpenAI package is not available."""
        with patch('agents.openai_client.openai', None):
            with pytest.raises(LLMClientError, match="OpenAI package not installed"):
                OpenAIClient(config)
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        config = LLMConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key=None,
            temperature=0.3
        )
        
        with pytest.raises(LLMClientError, match="OpenAI API key is required"):
            OpenAIClient(config)
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, config):
        """Test successful response generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            response = await client.generate_response("Test prompt", system_prompt="System prompt")
            
            assert response.content == "Test response"
            assert response.model == "gpt-3.5-turbo"
            assert response.usage["total_tokens"] == 15
            assert response.metadata["finish_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, config):
        """Test handling of rate limit errors."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            # Import the actual openai module to get the real exception
            import openai
            mock_client.chat.completions.create.side_effect = openai.RateLimitError(
                "Rate limit exceeded", response=Mock(), body={}
            )
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            
            with pytest.raises(LLMRateLimitError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Rate limit exceeded" in str(excinfo.value)
            assert "Try again later" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, config):
        """Test handling of connection errors."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            import openai
            mock_client.chat.completions.create.side_effect = openai.APIConnectionError("Connection failed")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Connection failed" in str(excinfo.value)
            assert "check your internet connection" in str(excinfo.value).lower()
    
    @pytest.mark.asyncio
    async def test_generate_response_authentication_error(self, config):
        """Test handling of authentication errors."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            import openai
            mock_client.chat.completions.create.side_effect = openai.AuthenticationError("Invalid API key")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Invalid API key" in str(excinfo.value)
            assert "api key is valid" in str(excinfo.value).lower()
    
    @pytest.mark.asyncio
    async def test_generate_response_bad_request_error(self, config):
        """Test handling of bad request errors."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            import openai
            mock_client.chat.completions.create.side_effect = openai.BadRequestError("Invalid request")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            
            with pytest.raises(LLMInvalidResponseError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Invalid request" in str(excinfo.value)
            assert "request parameters may be invalid" in str(excinfo.value).lower()
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Connection successful"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890
        mock_response.usage = None
        
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message
            assert result.response_time is not None


class TestOllamaClient:
    """Test Ollama client implementation."""
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="ollama",
            model_name="llama2",
            base_url="http://localhost:11434",
            temperature=0.3
        )
    
    def test_init_without_aiohttp_package(self, config):
        """Test initialization when aiohttp package is not available."""
        with patch('agents.ollama_client.aiohttp', None):
            with pytest.raises(LLMClientError, match="aiohttp package not installed"):
                OllamaClient(config)
    
    def test_init_without_base_url(self):
        """Test initialization without base URL."""
        config = LLMConfig(
            provider="ollama",
            model_name="llama2",
            base_url=None,
            temperature=0.3
        )
        
        with pytest.raises(LLMClientError, match="Ollama base URL is required"):
            OllamaClient(config)
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, config):
        """Test successful response generation."""
        mock_response_data = {
            "response": "Test response",
            "model": "llama2",
            "done": True,
            "eval_count": 5,
            "prompt_eval_count": 10,
            "total_duration": 1000000,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = OllamaClient(config)
            response = await client.generate_response("Test prompt", system_prompt="System prompt")
            
            assert response.content == "Test response"
            assert response.model == "llama2"
            assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_generate_response_model_not_found(self, config):
        """Test handling when model is not found."""
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = OllamaClient(config)
            
            with pytest.raises(LLMConnectionError, match="Model 'llama2' not found"):
                await client.generate_response("Test prompt")
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        # Mock the /api/tags endpoint
        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json.return_value = {
            "models": [{"name": "llama2"}]
        }
        
        # Mock the generate endpoint
        mock_generate_response = AsyncMock()
        mock_generate_response.status = 200
        mock_generate_response.json.return_value = {
            "response": "Connection successful",
            "model": "llama2",
            "done": True
        }
        
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.get.return_value.__aenter__.return_value = mock_tags_response
            mock_session_instance.post.return_value.__aenter__.return_value = mock_generate_response
            
            client = OllamaClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message


class TestLMStudioClient:
    """Test LM Studio client implementation."""
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="lmstudio",
            model_name="local-model",
            base_url="http://localhost:1234",
            temperature=0.3
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, config):
        """Test successful response generation."""
        mock_response_data = {
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "model": "local-model",
            "created": 1234567890,
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = LMStudioClient(config)
            response = await client.generate_response("Test prompt")
            
            assert response.content == "Test response"
            assert response.model == "local-model"
            assert response.usage["total_tokens"] == 15


class TestLLMClientFactory:
    """Test the LLM client factory function."""
    
    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        config = LLMConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key="test-key"
        )
        
        client = create_llm_client(config)
        assert isinstance(client, OpenAIClient)
    
    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        config = LLMConfig(
            provider="ollama",
            model_name="llama2",
            base_url="http://localhost:11434"
        )
        
        client = create_llm_client(config)
        assert isinstance(client, OllamaClient)
    
    def test_create_lmstudio_client(self):
        """Test creating LM Studio client."""
        config = LLMConfig(
            provider="lmstudio",
            model_name="local-model",
            base_url="http://localhost:1234"
        )
        
        client = create_llm_client(config)
        assert isinstance(client, LMStudioClient)
    
    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        # Since Pydantic validates the provider field, we need to test the factory directly
        # with a mock config that bypasses validation
        mock_config = Mock()
        mock_config.provider = "unsupported"
        mock_config.model_name = "test-model"
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client(mock_config)
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


class TestLMStudioClientErrors:
    """Test LM Studio client error handling."""
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="lmstudio",
            model_name="local-model",
            base_url="http://localhost:1234",
            temperature=0.3
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_endpoint_not_found(self, config):
        """Test handling when endpoint is not found."""
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = LMStudioClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "LM Studio endpoint not found" in str(excinfo.value)
            assert "Start Server" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_server_busy(self, config):
        """Test handling when server is busy."""
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 429
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = LMStudioClient(config)
            
            with pytest.raises(LLMRateLimitError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "LM Studio server is busy" in str(excinfo.value)
            assert "reducing the complexity" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_server_error(self, config):
        """Test handling when server returns an error."""
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal server error")
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = LMStudioClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "LM Studio server error (500)" in str(excinfo.value)
            assert "restarting LM Studio" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, config):
        """Test handling of connection errors."""
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = \
                aiohttp.ClientConnectorError(Mock(), OSError("Connection refused"))
            
            client = LMStudioClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Cannot connect to LM Studio server" in str(excinfo.value)
            assert "Make sure LM Studio is running" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        # Mock the /v1/models endpoint
        mock_models_response = AsyncMock()
        mock_models_response.status = 200
        mock_models_response.json.return_value = {
            "data": [{"id": "local-model"}]
        }
        
        # Mock the generate endpoint
        mock_generate_response = AsyncMock()
        mock_generate_response.status = 200
        mock_generate_response.json.return_value = {
            "choices": [{
                "message": {"content": "Connection successful"},
                "finish_reason": "stop"
            }],
            "model": "local-model"
        }
        
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.get.return_value.__aenter__.return_value = mock_models_response
            mock_session_instance.post.return_value.__aenter__.return_value = mock_generate_response
            
            client = LMStudioClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message
    
    @pytest.mark.asyncio
    async def test_test_connection_no_models(self, config):
        """Test connection test when no models are loaded."""
        # Mock the /v1/models endpoint with empty data
        mock_models_response = AsyncMock()
        mock_models_response.status = 200
        mock_models_response.json.return_value = {"data": []}
        
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.get.return_value.__aenter__.return_value = mock_models_response
            
            client = LMStudioClient(config)
            result = await client.test_connection()
            
            assert result.success is False
            assert "No models loaded" in result.message
            assert "Load a model" in result.error


class TestOllamaClientErrors:
    """Test Ollama client error handling."""
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="ollama",
            model_name="llama2",
            base_url="http://localhost:11434",
            temperature=0.3
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_model_not_found(self, config):
        """Test handling when model is not found."""
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = OllamaClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert f"Model '{config.model_name}' not found" in str(excinfo.value)
            assert "ollama pull" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_server_busy(self, config):
        """Test handling when server is busy."""
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 429
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = OllamaClient(config)
            
            with pytest.raises(LLMRateLimitError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Ollama server is busy" in str(excinfo.value)
            assert "under heavy load" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response_server_error(self, config):
        """Test handling when server returns an error."""
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal server error")
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = OllamaClient(config)
            
            with pytest.raises(LLMConnectionError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Ollama server error (500)" in str(excinfo.value)
            assert "restarting the Ollama service" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_test_connection_no_models(self, config):
        """Test connection test when no models are available."""
        # Mock the /api/tags endpoint with empty models
        mock_tags_response = AsyncMock()
        mock_tags_response.status = 200
        mock_tags_response.json.return_value = {"models": []}
        
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.get.return_value.__aenter__.return_value = mock_tags_response
            
            client = OllamaClient(config)
            result = await client.test_connection()
            
            assert result.success is False
            assert "No models found" in result.message
            assert "ollama pull" in result.error