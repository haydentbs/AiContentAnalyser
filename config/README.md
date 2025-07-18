# Configuration Management

The Content Scorecard uses a flexible configuration system that supports both TOML files and environment variables.

## Configuration Sources

Configuration is loaded in the following priority order:
1. **Environment Variables** (highest priority)
2. **TOML Configuration File** (config.toml)
3. **Default Values** (lowest priority)

## Configuration File Format

Create a `config.toml` file in the project root:

```toml
# Content Scorecard Configuration

[llm]
provider = "openai"  # Options: "openai", "ollama", "lmstudio"
model_name = "gpt-3.5-turbo"
temperature = 0.3
# api_key = "your-api-key-here"  # Can also be set via environment variable

[openai]
# api_key = "sk-your-openai-api-key-here"  # Alternative way to set OpenAI API key

[ollama]
base_url = "http://localhost:11434"

[lmstudio]
base_url = "http://localhost:1234"

[app]
guidelines_path = "guidelines.yaml"
reports_dir = "reports"
ui_theme = "light"
```

## Environment Variables

All configuration options can be overridden using environment variables:

### LLM Configuration
- `LLM_PROVIDER` - LLM provider (openai, ollama, lmstudio)
- `LLM_MODEL_NAME` - Model name to use
- `LLM_API_KEY` - API key for the provider
- `LLM_BASE_URL` - Base URL for local providers
- `LLM_TEMPERATURE` - Temperature for text generation (0.0-2.0)

### Provider-Specific
- `OPENAI_API_KEY` - OpenAI API key
- `OLLAMA_BASE_URL` - Ollama server URL (default: http://localhost:11434)
- `LMSTUDIO_BASE_URL` - LM Studio server URL (default: http://localhost:1234)

### Application Settings
- `GUIDELINES_PATH` - Path to guidelines YAML file
- `REPORTS_DIR` - Directory for saving reports
- `UI_THEME` - UI theme (light/dark)

## Usage Examples

### Basic Usage

```python
from config.settings import load_app_config

# Load configuration
config = load_app_config()

# Access configuration
print(f"Using {config.llm.provider} with model {config.llm.model_name}")
```

### Configuration Validation

```python
from config.settings import load_app_config, validate_config

config = load_app_config()
errors = validate_config(config)

if errors:
    for error in errors:
        print(f"Configuration error: {error}")
else:
    print("Configuration is valid!")
```

### Creating Default Configuration

```python
from config.settings import create_default_config_toml

# Create a default config.toml file
create_default_config_toml("config.toml")
```

## Provider Setup

### OpenAI
1. Set your API key via environment variable:
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   ```
2. Or add it to your config.toml:
   ```toml
   [openai]
   api_key = "sk-your-api-key-here"
   ```

### Ollama (Local)
1. Install and start Ollama
2. Configure the base URL if different from default:
   ```bash
   export OLLAMA_BASE_URL="http://localhost:11434"
   ```

### LM Studio (Local)
1. Install and start LM Studio
2. Configure the base URL if different from default:
   ```bash
   export LMSTUDIO_BASE_URL="http://localhost:1234"
   ```

## Configuration Validation

The system validates:
- Required API keys for cloud providers
- Required base URLs for local providers
- File path existence for guidelines
- Directory permissions for reports

Run the example script to test your configuration:
```bash
python examples/config_example.py
```