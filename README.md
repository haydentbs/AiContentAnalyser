# Content Scorecard

Content Scorecard is a local agentic prototype that provides AI-powered content evaluation against configurable guidelines. The application runs entirely locally without requiring external hosting or authentication, designed for single-user operation.

## Features

- Evaluate draft content against multiple metrics
- Receive detailed feedback and improvement suggestions
- Visualize results with intuitive charts
- Export reports in JSON and Markdown formats
- Configure LLM providers (OpenAI, Ollama, LM Studio)

## Getting Started

### Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your LLM provider in `config.toml` (see Configuration section)

### Running the Application

Start the Streamlit application:

```bash
streamlit run main.py
```

The application will be available at http://localhost:8501

### Configuration

Create a `config.toml` file in the root directory with the following structure:

```toml
[llm]
provider = "openai"  # Options: "openai", "ollama", "lmstudio"
model_name = "gpt-3.5-turbo"
temperature = 0.3

[openai]
api_key = "your-api-key-here"  # Or set OPENAI_API_KEY environment variable

[ollama]
base_url = "http://localhost:11434"  # Default Ollama URL

[lmstudio]
base_url = "http://localhost:1234"  # Default LM Studio URL

[app]
guidelines_path = "guidelines.yaml"
reports_dir = "reports"
ui_theme = "light"
```

## Usage

1. Enter or upload your content in the input area
2. Click "Evaluate Content" to analyze your text
3. Review the detailed feedback and scores
4. Export reports for future reference

## License

This project is licensed under the MIT License - see the LICENSE file for details.