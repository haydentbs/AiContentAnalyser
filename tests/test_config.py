"""Unit tests for configuration management system."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import toml

from config.settings import (
    ConfigurationManager,
    load_config_from_toml,
    create_default_config_toml,
    load_app_config,
    validate_config
)
from config.models import AppConfig, LLMConfig


class TestConfigurationManager:
    """Test the ConfigurationManager class."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = ConfigurationManager()
        
        assert config.llm_provider == "openai"
        assert config.llm_model_name == "gpt-3.5-turbo"
        assert config.llm_temperature == 0.3
        assert config.guidelines_path == "guidelines.yaml"
        assert config.reports_dir == "reports"
        assert config.ui_theme == "light"
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'ollama',
            'LLM_MODEL_NAME': 'llama2',
            'LLM_TEMPERATURE': '0.7',
            'OPENAI_API_KEY': 'test-key-123',
            'GUIDELINES_PATH': 'custom_guidelines.yaml'
        }):
            config = ConfigurationManager()
            
            assert config.llm_provider == "ollama"
            assert config.llm_model_name == "llama2"
            assert config.llm_temperature == 0.7
            assert config.openai_api_key == "test-key-123"
            assert config.guidelines_path == "custom_guidelines.yaml"
    
    def test_to_app_config_openai(self):
        """Test conversion to AppConfig for OpenAI provider."""
        config = ConfigurationManager(
            llm_provider="openai",
            llm_model_name="gpt-4",
            openai_api_key="test-key"
        )
        
        app_config = config.to_app_config()
        
        assert isinstance(app_config, AppConfig)
        assert app_config.llm.provider == "openai"
        assert app_config.llm.model_name == "gpt-4"
        assert app_config.llm.api_key == "test-key"
        assert app_config.llm.base_url is None
    
    def test_to_app_config_ollama(self):
        """Test conversion to AppConfig for Ollama provider."""
        config = ConfigurationManager(
            llm_provider="ollama",
            llm_model_name="llama2",
            ollama_base_url="http://localhost:11434"
        )
        
        app_config = config.to_app_config()
        
        assert app_config.llm.provider == "ollama"
        assert app_config.llm.model_name == "llama2"
        assert app_config.llm.api_key is None
        assert app_config.llm.base_url == "http://localhost:11434"
    
    def test_to_app_config_lmstudio(self):
        """Test conversion to AppConfig for LM Studio provider."""
        config = ConfigurationManager(
            llm_provider="lmstudio",
            llm_model_name="local-model",
            lmstudio_base_url="http://localhost:1234"
        )
        
        app_config = config.to_app_config()
        
        assert app_config.llm.provider == "lmstudio"
        assert app_config.llm.model_name == "local-model"
        assert app_config.llm.api_key is None
        assert app_config.llm.base_url == "http://localhost:1234"


class TestTOMLLoading:
    """Test TOML configuration loading functions."""
    
    def test_load_config_from_toml_success(self):
        """Test successful TOML loading."""
        toml_content = """
        [llm]
        provider = "openai"
        model_name = "gpt-4"
        temperature = 0.5
        
        [app]
        guidelines_path = "custom.yaml"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                config = load_config_from_toml(f.name)
                
                assert config["llm"]["provider"] == "openai"
                assert config["llm"]["model_name"] == "gpt-4"
                assert config["llm"]["temperature"] == 0.5
                assert config["app"]["guidelines_path"] == "custom.yaml"
            finally:
                os.unlink(f.name)
    
    def test_load_config_from_toml_missing_file(self):
        """Test loading from non-existent file returns empty dict."""
        config = load_config_from_toml("nonexistent.toml")
        assert config == {}
    
    def test_load_config_from_toml_invalid_toml(self):
        """Test loading invalid TOML raises ValueError."""
        invalid_toml = """
        [llm
        provider = "openai"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(invalid_toml)
            f.flush()
            
            try:
                with pytest.raises(ValueError, match="Failed to load configuration"):
                    load_config_from_toml(f.name)
            finally:
                os.unlink(f.name)
    
    def test_create_default_config_toml(self):
        """Test creating default config.toml file."""
        with tempfile.NamedTemporaryFile(suffix='.toml', delete=False) as f:
            try:
                create_default_config_toml(f.name)
                
                # Verify file was created and contains expected content
                with open(f.name, 'r') as created_file:
                    config = toml.load(created_file)
                
                assert config["llm"]["provider"] == "openai"
                assert config["llm"]["model_name"] == "gpt-3.5-turbo"
                assert config["app"]["guidelines_path"] == "guidelines.yaml"
            finally:
                os.unlink(f.name)


class TestLoadAppConfig:
    """Test the main load_app_config function."""
    
    def test_load_app_config_with_toml(self):
        """Test loading app config with TOML file."""
        toml_content = """
        [llm]
        provider = "ollama"
        model_name = "llama2"
        temperature = 0.8
        
        [ollama]
        base_url = "http://custom:11434"
        
        [app]
        reports_dir = "custom_reports"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                config = load_app_config(f.name)
                
                assert isinstance(config, AppConfig)
                assert config.llm.provider == "ollama"
                assert config.llm.model_name == "llama2"
                assert config.llm.temperature == 0.8
                assert config.llm.base_url == "http://custom:11434"
                assert config.reports_dir == "custom_reports"
            finally:
                os.unlink(f.name)
    
    def test_load_app_config_env_override(self):
        """Test that environment variables override TOML values."""
        toml_content = """
        [llm]
        provider = "openai"
        model_name = "gpt-3.5-turbo"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            try:
                with patch.dict(os.environ, {
                    'LLM_PROVIDER': 'ollama',
                    'LLM_MODEL_NAME': 'llama2'
                }):
                    config = load_app_config(f.name)
                    
                    # Environment variables should override TOML
                    assert config.llm.provider == "ollama"
                    assert config.llm.model_name == "llama2"
            finally:
                os.unlink(f.name)
    
    def test_load_app_config_no_file(self):
        """Test loading config when TOML file doesn't exist."""
        config = load_app_config("nonexistent.toml")
        
        assert isinstance(config, AppConfig)
        assert config.llm.provider == "openai"  # Default value
        assert config.llm.model_name == "gpt-3.5-turbo"  # Default value


class TestValidateConfig:
    """Test configuration validation."""
    
    def test_validate_config_valid_openai(self):
        """Test validation of valid OpenAI configuration."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model_name="gpt-3.5-turbo",
                api_key="test-key"
            )
        )
        
        errors = validate_config(config)
        assert errors == []
    
    def test_validate_config_missing_openai_key(self):
        """Test validation fails when OpenAI API key is missing."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model_name="gpt-3.5-turbo"
            )
        )
        
        errors = validate_config(config)
        assert len(errors) == 1
        assert "OpenAI API key is required" in errors[0]
    
    def test_validate_config_valid_ollama(self):
        """Test validation of valid Ollama configuration."""
        config = AppConfig(
            llm=LLMConfig(
                provider="ollama",
                model_name="llama2",
                base_url="http://localhost:11434"
            )
        )
        
        errors = validate_config(config)
        assert errors == []
    
    def test_validate_config_missing_ollama_url(self):
        """Test validation fails when Ollama base URL is missing."""
        config = AppConfig(
            llm=LLMConfig(
                provider="ollama",
                model_name="llama2"
            )
        )
        
        errors = validate_config(config)
        assert len(errors) == 1
        assert "Ollama base URL is required" in errors[0]
    
    def test_validate_config_missing_guidelines_file(self):
        """Test validation warns about missing guidelines file."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model_name="gpt-3.5-turbo",
                api_key="test-key"
            ),
            guidelines_path="nonexistent.yaml"
        )
        
        errors = validate_config(config)
        assert len(errors) == 1
        assert "Guidelines file not found" in errors[0]
    
    def test_validate_config_reports_dir_not_directory(self):
        """Test validation fails when reports_dir exists but is not a directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            try:
                config = AppConfig(
                    llm=LLMConfig(
                        provider="openai",
                        model_name="gpt-3.5-turbo",
                        api_key="test-key"
                    ),
                    reports_dir=f.name
                )
                
                errors = validate_config(config)
                assert len(errors) == 1
                assert "is not a directory" in errors[0]
            finally:
                os.unlink(f.name)