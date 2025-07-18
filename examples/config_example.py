#!/usr/bin/env python3
"""Example demonstrating the configuration management system."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import load_app_config, validate_config, create_default_config_toml


def main():
    """Demonstrate configuration loading and validation."""
    print("Content Scorecard Configuration Example")
    print("=" * 40)
    
    # Create a default config.toml if it doesn't exist
    config_path = "config.toml"
    if not Path(config_path).exists():
        print(f"Creating default {config_path}...")
        create_default_config_toml(config_path)
        print(f"✓ Created {config_path}")
    
    # Load configuration
    print(f"\nLoading configuration from {config_path}...")
    config = load_app_config(config_path)
    
    print(f"✓ Configuration loaded successfully")
    print(f"  LLM Provider: {config.llm.provider}")
    print(f"  Model Name: {config.llm.model_name}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Guidelines Path: {config.guidelines_path}")
    print(f"  Reports Directory: {config.reports_dir}")
    
    # Validate configuration
    print(f"\nValidating configuration...")
    errors = validate_config(config)
    
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration is valid")
    
    # Demonstrate environment variable override
    print(f"\nDemonstrating environment variable override...")
    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["LLM_MODEL_NAME"] = "llama2"
    
    config_with_env = load_app_config(config_path)
    print(f"  With env vars - Provider: {config_with_env.llm.provider}")
    print(f"  With env vars - Model: {config_with_env.llm.model_name}")
    
    # Clean up environment variables
    del os.environ["LLM_PROVIDER"]
    del os.environ["LLM_MODEL_NAME"]
    
    print(f"\n✓ Configuration system demonstration complete!")


if __name__ == "__main__":
    main()