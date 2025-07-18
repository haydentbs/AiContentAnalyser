"""Unit tests for OpenAI client implementation.

References:
- https://platform.openai.com/docs/api-reference/chat
- https://platform.openai.com/docs/models
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import openai
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice, ChatCompletion

from agents.llm_client import (
    LLMResponse,
    LLMClientError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError
)
from agents.openai_client import OpenAIClient
from config.models import LLMConfig
from config.settings import load_test_api_key


class TestOpenAIClient:
    """Test OpenAI client implementation."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration using gpt-4.1-nano-2025-04-14 model and test API key."""
        # Load the test API key from config.toml
        test_api_key = load_test_api_key()
        if not test_api_key:
            test_api_key = "test-key-fallback"  # Fallback for tests
        
        return LLMConfig(
            provider="openai",
            model_name="gpt-4.1-nano-2025-04-14",  # Using the specified model
            api_key=test_api_key,
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
            model_name="gpt-4.1-nano-2025-04-14",
            api_key=None,
            temperature=0.3
        )
        
        with pytest.raises(LLMClientError, match="OpenAI API key is required"):
            OpenAIClient(config)
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, config):
        """Test successful response generation with gpt-4.1-nano-2025-04-14."""
        # Create a mock response that matches the OpenAI API structure
        mock_message = Mock(spec=ChatCompletionMessage)
        mock_message.content = "Test response"
        
        mock_choice = Mock(spec=Choice)
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock(spec=ChatCompletion)
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4.1-nano-2025-04-14"
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
            
            # Verify the client used the correct model
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-4.1-nano-2025-04-14"
            
            # Verify the response
            assert response.content == "Test response"
            assert response.model == "gpt-4.1-nano-2025-04-14"
            assert response.usage["total_tokens"] == 15
            assert response.metadata["finish_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, config):
        """Test handling of rate limit errors."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            # Create a real RateLimitError instance
            rate_limit_error = openai.RateLimitError("Rate limit exceeded", response=Mock(), body={})
            mock_client.chat.completions.create.side_effect = rate_limit_error
            
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
            
            # Create a mock for APIConnectionError since it doesn't take a message parameter
            class MockAPIConnectionError(Exception):
                def __str__(self):
                    return "Connection failed"
            
            connection_error = MockAPIConnectionError()
            
            # Patch the exception type check in the client
            with patch('agents.openai_client.openai.APIConnectionError', MockAPIConnectionError):
                mock_client.chat.completions.create.side_effect = connection_error
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
            
            # Create a real AuthenticationError instance
            auth_error = openai.AuthenticationError("Invalid API key", response=Mock(), body={})
            mock_client.chat.completions.create.side_effect = auth_error
            
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
            
            # Create a real BadRequestError instance
            bad_request_error = openai.BadRequestError("Invalid request", response=Mock(), body={})
            mock_client.chat.completions.create.side_effect = bad_request_error
            
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            
            with pytest.raises(LLMInvalidResponseError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Invalid request" in str(excinfo.value)
            assert "request parameters may be invalid" in str(excinfo.value).lower()
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test with gpt-4.1-nano-2025-04-14."""
        # Mock the models.list response
        mock_model = Mock()
        mock_model.id = "gpt-4.1-nano-2025-04-14"
        mock_models_response = Mock()
        mock_models_response.data = [mock_model]
        
        # Mock the chat completion response
        mock_message = Mock(spec=ChatCompletionMessage)
        mock_message.content = "Connection successful"
        
        mock_choice = Mock(spec=Choice)
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_completion_response = Mock(spec=ChatCompletion)
        mock_completion_response.choices = [mock_choice]
        mock_completion_response.model = "gpt-4.1-nano-2025-04-14"
        mock_completion_response.created = 1234567890
        mock_completion_response.usage = None
        
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.models.list.return_value = mock_models_response
            mock_client.chat.completions.create.return_value = mock_completion_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message
            assert "gpt-4.1-nano-2025-04-14" in result.message
            assert result.response_time is not None
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, config):
        """Test connection test failure."""
        with patch('agents.openai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            
            # Create a mock for APIConnectionError since it doesn't take a message parameter
            class MockAPIConnectionError(Exception):
                def __str__(self):
                    return "Connection failed"
            
            connection_error = MockAPIConnectionError()
            
            # Patch the exception type check in the client
            with patch('agents.openai_client.openai.APIConnectionError', MockAPIConnectionError):
                mock_client.chat.completions.create.side_effect = connection_error
                
                # Mock the models.list method to also raise an error
                mock_client.models.list.side_effect = connection_error
                
                mock_openai.return_value = mock_client
                
                client = OpenAIClient(config)
                result = await client.test_connection()
                
                assert result.success is False
                assert "Failed to connect" in result.message
                assert "Connection failed" in result.error