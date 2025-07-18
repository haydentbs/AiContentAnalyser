"""Configuration management system using TOML and environment variables."""

import os
from pathlib import Path
from typing import Optional
import toml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import LLMConfig, AppConfig


class ConfigurationManager(BaseSettings):
    """Main configuration manager that loads from TOML files and environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai")
    llm_model_name: str = Field(default="gpt-3.5-turbo")
    llm_api_key: Optional[str] = Field(default=None)
    llm_base_url: Optional[str] = Field(default=None)
    llm_temperature: float = Field(default=0.3)
    
    # OpenAI specific
    openai_api_key: Optional[str] = Field(default=None)
    
    # Ollama specific
    ollama_base_url: str = Field(default="http://localhost:11434")
    
    # LM Studio specific
    lmstudio_base_url: str = Field(default="http://localhost:1234")
    
    # Application Configuration
    guidelines_path: str = Field(default="guidelines.yaml")
    reports_dir: str = Field(default="reports")
    ui_theme: str = Field(default="light")
    
    def to_app_config(self) -> AppConfig:
        """Convert to AppConfig model."""
        # Determine API key based on provider
        api_key = None
        base_url = None
        
        if self.llm_provider == "openai":
            api_key = self.llm_api_key or self.openai_api_key
        elif self.llm_provider == "ollama":
            base_url = self.llm_base_url or self.ollama_base_url
        elif self.llm_provider == "lmstudio":
            base_url = self.llm_base_url or self.lmstudio_base_url
        
        llm_config = LLMConfig(
            provider=self.llm_provider,
            model_name=self.llm_model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=self.llm_temperature
        )
        
        return AppConfig(
            llm=llm_config,
            guidelines_path=self.guidelines_path,
            reports_dir=self.reports_dir,
            ui_theme=self.ui_theme
        )


def load_config_from_toml(config_path: str = "config.toml") -> dict:
    """Load configuration from TOML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except (toml.TomlDecodeError, IOError) as e:
        raise ValueError(f"Failed to load configuration from {config_path}: {e}")


def create_default_config_toml(config_path: str = "config.toml") -> None:
    """Create a default config.toml file."""
    default_config = {
        "llm": {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.3
        },
        "app": {
            "guidelines_path": "guidelines.yaml",
            "reports_dir": "reports",
            "ui_theme": "light"
        }
    }
    
    config_file = Path(config_path)
    with open(config_file, 'w', encoding='utf-8') as f:
        toml.dump(default_config, f)


def load_app_config(config_path: str = "config.toml") -> AppConfig:
    """Load complete application configuration from TOML file and environment variables."""
    # Load TOML configuration
    toml_config = load_config_from_toml(config_path)
    
    # Create configuration manager (this loads from environment variables first)
    config_manager = ConfigurationManager()
    
    # Only override with TOML values if environment variables are not set
    if "llm" in toml_config:
        llm_section = toml_config["llm"]
        if "provider" in llm_section and not os.getenv("LLM_PROVIDER"):
            config_manager.llm_provider = llm_section["provider"]
        if "model_name" in llm_section and not os.getenv("LLM_MODEL_NAME"):
            config_manager.llm_model_name = llm_section["model_name"]
        if "api_key" in llm_section and not os.getenv("LLM_API_KEY"):
            config_manager.llm_api_key = llm_section["api_key"]
        if "base_url" in llm_section and not os.getenv("LLM_BASE_URL"):
            config_manager.llm_base_url = llm_section["base_url"]
        if "temperature" in llm_section and not os.getenv("LLM_TEMPERATURE"):
            config_manager.llm_temperature = llm_section["temperature"]
    
    if "app" in toml_config:
        app_section = toml_config["app"]
        if "guidelines_path" in app_section and not os.getenv("GUIDELINES_PATH"):
            config_manager.guidelines_path = app_section["guidelines_path"]
        if "reports_dir" in app_section and not os.getenv("REPORTS_DIR"):
            config_manager.reports_dir = app_section["reports_dir"]
        if "ui_theme" in app_section and not os.getenv("UI_THEME"):
            config_manager.ui_theme = app_section["ui_theme"]
    
    # Provider-specific TOML overrides (only if env vars not set)
    if "openai" in toml_config and "api_key" in toml_config["openai"] and not os.getenv("OPENAI_API_KEY"):
        config_manager.openai_api_key = toml_config["openai"]["api_key"]
    
    if "ollama" in toml_config and "base_url" in toml_config["ollama"] and not os.getenv("OLLAMA_BASE_URL"):
        config_manager.ollama_base_url = toml_config["ollama"]["base_url"]
    
    if "lmstudio" in toml_config and "base_url" in toml_config["lmstudio"] and not os.getenv("LMSTUDIO_BASE_URL"):
        config_manager.lmstudio_base_url = toml_config["lmstudio"]["base_url"]
    
    return config_manager.to_app_config()


def load_test_api_key(config_path: str = "config.toml") -> Optional[str]:
    """Load the test API key from TOML configuration for unit tests."""
    toml_config = load_config_from_toml(config_path)
    
    if "openai" in toml_config and "api_key_test" in toml_config["openai"]:
        return toml_config["openai"]["api_key_test"]
    
    return None


def validate_config(config: AppConfig) -> list[str]:
    """Validate configuration and return list of validation errors."""
    errors = []
    
    # Validate LLM configuration
    if config.llm.provider == "openai" and not config.llm.api_key:
        errors.append("OpenAI API key is required when using OpenAI provider")
    
    if config.llm.provider in ["ollama", "lmstudio"] and not config.llm.base_url:
        errors.append(f"{config.llm.provider.title()} base URL is required")
    
    # Validate file paths
    guidelines_path = Path(config.guidelines_path)
    if not guidelines_path.exists() and config.guidelines_path != "guidelines.yaml":
        errors.append(f"Guidelines file not found: {config.guidelines_path}")
    
    # Validate reports directory
    reports_dir = Path(config.reports_dir)
    if reports_dir.exists() and not reports_dir.is_dir():
        errors.append(f"Reports path exists but is not a directory: {config.reports_dir}")
    
    return errors