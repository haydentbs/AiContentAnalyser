"""Unit tests for LM Studio client implementation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

from agents.llm_client import (
    LLMResponse,
    LLMClientError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError
)
from agents.lmstudio_client import LMStudioClient
from config.models import LLMConfig


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
    
    def test_init_without_aiohttp_package(self, config):
        """Test initialization when aiohttp package is not available."""
        with patch('agents.lmstudio_client.aiohttp', None):
            with pytest.raises(LLMClientError, match="aiohttp package not installed"):
                LMStudioClient(config)
    
    def test_init_without_base_url(self):
        """Test initialization without base URL."""
        config = LLMConfig(
            provider="lmstudio",
            model_name="local-model",
            base_url=None,
            temperature=0.3
        )
        
        with pytest.raises(LLMClientError, match="LM Studio base URL is required"):
            LMStudioClient(config)
    
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
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Set up the mock post response
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_session_instance.post.return_value = mock_post_context
            
            client = LMStudioClient(config)
            response = await client.generate_response("Test prompt")
            
            assert response.content == "Test response"
            assert response.model == "local-model"
            assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_generate_response_endpoint_not_found(self, config):
        """Test handling when endpoint is not found."""
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.status = 404
            
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Set up the mock post response
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_session_instance.post.return_value = mock_post_context
            
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
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.status = 429
            
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Set up the mock post response
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_response
            mock_session_instance.post.return_value = mock_post_context
            
            client = LMStudioClient(config)
            
            with pytest.raises(LLMRateLimitError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "LM Studio server is busy" in str(excinfo.value)
            assert "reducing the complexity" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        # Mock data for the /v1/models endpoint
        mock_models_data = {
            "data": [{"id": "local-model"}]
        }
        
        # Mock data for the generate endpoint
        mock_generate_data = {
            "choices": [{
                "message": {"content": "Connection successful"},
                "finish_reason": "stop"
            }],
            "model": "local-model"
        }
        
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Mock the GET response for /v1/models
            mock_models_response = AsyncMock()
            mock_models_response.status = 200
            mock_models_response.json = AsyncMock(return_value=mock_models_data)
            mock_get_context = AsyncMock()
            mock_get_context.__aenter__.return_value = mock_models_response
            mock_session_instance.get.return_value = mock_get_context
            
            # Mock the POST response for generate
            mock_generate_response = AsyncMock()
            mock_generate_response.status = 200
            mock_generate_response.json = AsyncMock(return_value=mock_generate_data)
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_generate_response
            mock_session_instance.post.return_value = mock_post_context
            
            client = LMStudioClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message
    
    @pytest.mark.asyncio
    async def test_test_connection_no_models(self, config):
        """Test connection test when no models are loaded."""
        # Mock data for the /v1/models endpoint with empty data
        mock_models_data = {
            "data": []
        }
        
        with patch('agents.lmstudio_client.aiohttp.ClientSession') as mock_session:
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Mock the GET response for /v1/models
            mock_models_response = AsyncMock()
            mock_models_response.status = 200
            mock_models_response.json = AsyncMock(return_value=mock_models_data)
            mock_get_context = AsyncMock()
            mock_get_context.__aenter__.return_value = mock_models_response
            mock_session_instance.get.return_value = mock_get_context
            
            client = LMStudioClient(config)
            result = await client.test_connection()
            
            assert result.success is False
            assert "No models loaded" in result.message
            assert "Load a model" in result.error