"""Unit tests for Ollama client implementation."""

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
from agents.ollama_client import OllamaClient
from config.models import LLMConfig


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
            
            client = OllamaClient(config)
            response = await client.generate_response("Test prompt", system_prompt="System prompt")
            
            assert response.content == "Test response"
            assert response.model == "llama2"
            assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_generate_response_model_not_found(self, config):
        """Test handling when model is not found."""
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
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
            
            client = OllamaClient(config)
            
            with pytest.raises(LLMRateLimitError) as excinfo:
                await client.generate_response("Test prompt")
            
            # Check that the error message contains troubleshooting information
            assert "Ollama server is busy" in str(excinfo.value)
            assert "under heavy load" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        # Mock data for the /api/tags endpoint
        mock_tags_data = {
            "models": [{"name": "llama2"}]
        }
        
        # Mock data for the generate endpoint
        mock_generate_data = {
            "response": "Connection successful",
            "model": "llama2",
            "done": True
        }
        
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Mock the GET response for /api/tags
            mock_tags_response = AsyncMock()
            mock_tags_response.status = 200
            mock_tags_response.json = AsyncMock(return_value=mock_tags_data)
            mock_get_context = AsyncMock()
            mock_get_context.__aenter__.return_value = mock_tags_response
            mock_session_instance.get.return_value = mock_get_context
            
            # Mock the POST response for generate
            mock_generate_response = AsyncMock()
            mock_generate_response.status = 200
            mock_generate_response.json = AsyncMock(return_value=mock_generate_data)
            mock_post_context = AsyncMock()
            mock_post_context.__aenter__.return_value = mock_generate_response
            mock_session_instance.post.return_value = mock_post_context
            
            client = OllamaClient(config)
            result = await client.test_connection()
            
            assert result.success is True
            assert "Successfully connected" in result.message
    
    @pytest.mark.asyncio
    async def test_test_connection_no_models(self, config):
        """Test connection test when no models are available."""
        # Mock data for the /api/tags endpoint with empty models
        mock_tags_data = {
            "models": []
        }
        
        with patch('agents.ollama_client.aiohttp.ClientSession') as mock_session:
            # Set up the mock session
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__.return_value = mock_session_instance
            mock_session.return_value = mock_session_instance
            
            # Mock the GET response for /api/tags
            mock_tags_response = AsyncMock()
            mock_tags_response.status = 200
            mock_tags_response.json = AsyncMock(return_value=mock_tags_data)
            mock_get_context = AsyncMock()
            mock_get_context.__aenter__.return_value = mock_tags_response
            mock_session_instance.get.return_value = mock_get_context
            
            client = OllamaClient(config)
            result = await client.test_connection()
            
            assert result.success is False
            assert "not found" in result.message.lower()
            assert "pull" in result.error.lower()