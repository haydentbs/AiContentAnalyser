"""Unit tests for LLM client factory."""

import pytest
from unittest.mock import Mock, patch

from agents.llm_client import create_llm_client
from agents.openai_client import OpenAIClient
from agents.ollama_client import OllamaClient
from agents.lmstudio_client import LMStudioClient
from config.models import LLMConfig


class TestLLMClientFactory:
    """Test the LLM client factory function."""
    
    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        with patch('agents.openai_client.OpenAIClient') as mock_openai_client:
            config = LLMConfig(
                provider="openai",
                model_name="gpt-4o-mini",
                api_key="test-key"
            )
            
            create_llm_client(config)
            mock_openai_client.assert_called_once_with(config)
    
    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        with patch('agents.ollama_client.OllamaClient') as mock_ollama_client:
            config = LLMConfig(
                provider="ollama",
                model_name="llama2",
                base_url="http://localhost:11434"
            )
            
            create_llm_client(config)
            mock_ollama_client.assert_called_once_with(config)
    
    def test_create_lmstudio_client(self):
        """Test creating LM Studio client."""
        with patch('agents.lmstudio_client.LMStudioClient') as mock_lmstudio_client:
            config = LLMConfig(
                provider="lmstudio",
                model_name="local-model",
                base_url="http://localhost:1234"
            )
            
            create_llm_client(config)
            mock_lmstudio_client.assert_called_once_with(config)
    
    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        # Since Pydantic validates the provider field, we need to test the factory directly
        # with a mock config that bypasses validation
        mock_config = Mock()
        mock_config.provider = "unsupported"
        mock_config.model_name = "test-model"
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client(mock_config)