# Content Scorecard

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-FF4B4B.svg)](https://streamlit.io/)

Content Scorecard is an AI-powered content evaluation tool that helps writers, marketers, and content creators improve their content quality through comprehensive analysis and scoring. The application evaluates content against configurable guidelines using Large Language Models (LLMs) and provides detailed feedback with actionable recommendations.

## 🌟 Features

- **📊 Comprehensive Content Analysis**: Evaluate content across multiple dimensions including clarity, accuracy, engagement, completeness, and readability
- **🤖 Multiple LLM Providers**: Support for OpenAI, Ollama (local), and LM Studio (local) for flexible AI model usage
- **📈 Visual Reporting**: Interactive charts, gauges, and detailed breakdowns of content scores
- **⚙️ Configurable Guidelines**: Customizable evaluation criteria via YAML configuration files
- **💾 Report Export**: Generate reports in JSON and Markdown formats for documentation and sharing
- **🎨 Dual Frontend Options**: Choose between a modern React web interface or a Streamlit-based interface
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **🔒 Privacy-First**: Run completely local with offline LLM options - no data leaves your machine
- **🧪 Sample Content**: Built-in sample content for testing and demonstration

## 🏗️ Architecture

Content Scorecard features a modular architecture with:

- **Frontend**: React.js with TypeScript, Vite, Tailwind CSS, and Radix UI components
- **Alternative Frontend**: Streamlit-based interface for rapid prototyping and data science workflows
- **Backend**: FastAPI with Python for LLM orchestration and content processing
- **Storage**: File-based storage for configurations, guidelines, and reports
- **AI Integration**: Pluggable LLM providers with unified interface

## 📋 Prerequisites

Before installing Content Scorecard, ensure you have:

- **Python 3.9+** with pip
- **Node.js 16+** with npm
- **Git** for cloning the repository

### LLM Provider Requirements

Choose one or more providers:

- **OpenAI**: API key required ([Get one here](https://platform.openai.com/api-keys))
- **Ollama**: [Install Ollama](https://ollama.ai/) for local models
- **LM Studio**: [Install LM Studio](https://lmstudio.ai/) for local model hosting

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/contentScorecard.git
cd contentScorecard
```

### 2. Set Up Python Environment

```bash
# Create virtual environment (recommended)
python -m venv content-scorecard-env
source content-scorecard-env/bin/activate  # On Windows: content-scorecard-env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Node.js Dependencies

```bash
npm install
```

### 4. Configure the Application

Create a configuration file:

```bash
# Generate default config.toml
python examples/config_example.py
```

Edit `config.toml` with your settings:

```toml
[llm]
provider = "openai"  # Options: "openai", "ollama", "lmstudio"
model_name = "gpt-4"
temperature = 0.3
# api_key = "your-api-key-here"  # Or set via environment variable

[app]
guidelines_path = "guidelines.yaml"
reports_dir = "reports"
ui_theme = "light"
```

### 5. Set Environment Variables

For OpenAI:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

For Ollama (if different from default):
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
```

For LM Studio (if different from default):
```bash
export LMSTUDIO_BASE_URL="http://localhost:1234"
```

### 6. Choose Your Frontend

#### Option A: React Frontend (Recommended)

Start both backend and frontend:
```bash
npm run dev
```

This will:
- Start the FastAPI backend on `http://localhost:8000`
- Start the React frontend on `http://localhost:5173`

#### Option B: Streamlit Frontend

Start the Streamlit interface:
```bash
streamlit run main.py
```

Access at `http://localhost:8501`

## 🎯 Usage Guide

### React Frontend Usage

1. **Navigate to Analyze**: Click "Analyze Content" in the navigation
2. **Input Content**: 
   - Type or paste content into the text area
   - Upload `.md` or `.txt` files
   - Select from sample content
3. **Analyze**: Click "Analyze Content" to start evaluation
4. **Review Results**: 
   - View overall score and category breakdowns
   - Explore detailed metric results
   - Download reports in JSON or Markdown

### Streamlit Frontend Usage

1. **Open Application**: Navigate to `http://localhost:8501`
2. **Configure LLM**: Use sidebar to test LLM connection
3. **Input Content**: 
   - Use text area for direct input
   - Upload files via file uploader
4. **Evaluate**: Click "Evaluate Content" button
5. **View Results**: 
   - Interactive gauge for overall score
   - Radar chart for category visualization
   - Expandable sections for detailed feedback

## ⚙️ Configuration

### Configuration File Structure

The `config.toml` file supports the following sections:

```toml
[llm]
provider = "openai"           # LLM provider: "openai", "ollama", "lmstudio"
model_name = "gpt-4"          # Model name
temperature = 0.3             # Response creativity (0.0-2.0)
api_key = "sk-..."           # API key (optional, prefer env vars)
base_url = "http://..."      # Custom base URL for providers

[openai]
api_key = "sk-..."           # OpenAI-specific API key

[ollama]
base_url = "http://localhost:11434"  # Ollama server URL

[lmstudio]
base_url = "http://localhost:1234"   # LM Studio server URL

[app]
guidelines_path = "guidelines.yaml"  # Path to evaluation guidelines
reports_dir = "reports"              # Directory for saving reports
ui_theme = "light"                   # UI theme preference
```

### Environment Variables

All configuration can be overridden with environment variables:

```bash
# LLM Configuration
export LLM_PROVIDER="ollama"
export LLM_MODEL_NAME="llama2"
export LLM_API_KEY="your-key"
export LLM_BASE_URL="http://localhost:11434"
export LLM_TEMPERATURE="0.7"

# Provider-specific
export OPENAI_API_KEY="sk-your-openai-key"
export OLLAMA_BASE_URL="http://localhost:11434"
export LMSTUDIO_BASE_URL="http://localhost:1234"

# Application
export GUIDELINES_PATH="custom_guidelines.yaml"
export REPORTS_DIR="custom_reports"
export UI_THEME="dark"
```

### Guidelines Configuration

Guidelines are defined in YAML format. The system automatically creates default guidelines, but you can customize them:

```yaml
categories:
  clarity:
    weight: 1.0
    description: "How clear and understandable is the content?"
    metrics:
      conciseness:
        description: "Is the writing free of unnecessary filler words and redundancy?"
        weight: 0.3
      jargon_usage:
        description: "Is technical jargon properly defined or avoided when appropriate?"
        weight: 0.4
      logical_structure:
        description: "Does the content follow a logical flow with clear headings and transitions?"
        weight: 0.3

  accuracy:
    weight: 1.2
    description: "How factually correct and well-supported is the content?"
    metrics:
      data_support:
        description: "Are claims backed by credible data, sources, or evidence?"
        weight: 0.6
      fact_verification:
        description: "Are there any apparent factual errors or unsupported claims?"
        weight: 0.4

  # Additional categories: engagement, completeness, readability
```

## 🔧 Development

### Running Tests

#### Backend Tests
```bash
# Run all Python tests
pytest

# Run specific test modules
pytest tests/test_config.py
pytest tests/test_guidelines.py
pytest tests/test_llm_clients.py

# Run with coverage
pytest --cov=core tests/
```

#### Frontend Tests
```bash
# Run React unit tests
npm test

# Run React tests in watch mode
npm run test:watch

# Run end-to-end tests
npm run test:e2e
```

#### Integration Tests
```bash
# Run Playwright e2e tests
npx playwright test

# Run with UI
npx playwright test --ui
```

### Code Quality

```bash
# Frontend linting
npm run lint

# Format code
npm run format

# Type checking
npm run type-check
```

### Building for Production

```bash
# Build React frontend
npm run build

# Preview production build
npm run preview
```

## 📊 API Reference

The FastAPI backend provides the following endpoints:

### Core Evaluation
- `POST /api/evaluate` - Evaluate content against guidelines
- `GET /api/reports/{report_id}` - Retrieve evaluation report
- `GET /api/reports/{report_id}/export?format={json|markdown}` - Export report

### Configuration
- `GET /api/settings` - Get current application settings
- `PUT /api/settings` - Update application settings
- `POST /api/settings/test` - Test LLM provider connection

### Sample Content
- `GET /api/samples` - List available sample content
- `GET /api/samples/{sample_id}` - Get specific sample content

### API Documentation

When running the backend, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🛠️ LLM Provider Setup

### OpenAI Setup

1. **Get API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Set Environment Variable**:
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   ```
3. **Configure Model**:
   ```toml
   [llm]
   provider = "openai"
   model_name = "gpt-4"  # or "gpt-3.5-turbo", "gpt-4-turbo"
   ```

### Ollama Setup (Local)

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai/)
2. **Pull Models**:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ollama pull codellama
   ```
3. **Configure**:
   ```toml
   [llm]
   provider = "ollama"
   model_name = "llama2"
   
   [ollama]
   base_url = "http://localhost:11434"
   ```

### LM Studio Setup (Local)

1. **Install LM Studio**: Download from [lmstudio.ai](https://lmstudio.ai/)
2. **Load Model**: Use LM Studio interface to download and load a model
3. **Start Server**: Enable "Local Server" in LM Studio
4. **Configure**:
   ```toml
   [llm]
   provider = "lmstudio"
   model_name = "your-loaded-model-name"
   
   [lmstudio]
   base_url = "http://localhost:1234"
   ```

## 📁 Project Structure

```
contentScorecard/
├── 📂 backend/              # FastAPI backend
│   └── main.py             # API server entry point
├── 📂 core/                # Core application logic
│   ├── 📂 agents/          # LLM client implementations
│   ├── 📂 config/          # Configuration management
│   └── 📂 storage/         # Data persistence
├── 📂 src/                 # React frontend
│   ├── 📂 components/      # UI components
│   ├── 📂 pages/           # Application pages
│   ├── 📂 api/             # API client
│   └── 📂 types/           # TypeScript types
├── 📂 tests/               # Test suites
├── 📂 examples/            # Example scripts and configs
├── 📂 reports/             # Generated evaluation reports
├── main.py                 # Streamlit frontend entry point
├── config.toml             # Application configuration
├── guidelines.yaml         # Evaluation guidelines
├── samples.yaml            # Sample content
└── requirements.txt        # Python dependencies
```

## 🚨 Troubleshooting

### Common Issues

#### "Configuration errors" on startup
- **Cause**: Missing API keys or invalid configuration
- **Solution**: Check `config.toml` and environment variables
- **Debug**: Run `python examples/config_example.py` to validate config

#### "Connection failed" when testing LLM
- **OpenAI**: Verify API key and internet connection
- **Ollama**: Ensure Ollama is running (`ollama serve`)
- **LM Studio**: Check server is enabled and model is loaded

#### Frontend won't start
- **Solution**: Ensure Node.js 16+ is installed
- **Check**: Run `npm install` to install dependencies
- **Ports**: Verify ports 5173 and 8000 are available

#### Backend API errors
- **Solution**: Check Python dependencies with `pip install -r requirements.txt`
- **Logs**: Check console output for detailed error messages
- **Permissions**: Ensure write access to `reports/` directory

### Performance Optimization

#### Large Content Analysis
- Use local models (Ollama/LM Studio) for better privacy and speed
- Adjust `temperature` setting for faster responses
- Consider chunking very large documents

#### Development Speed
- Use mock client during development: Set `USE_MOCK_API=true`
- Enable hot reloading: Use `npm run dev:instant`

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Follow the coding standards
4. **Add Tests**: Include tests for new functionality
5. **Run Tests**: Ensure all tests pass
6. **Commit Changes**: `git commit -m 'feat: Add amazing feature'`
7. **Push Branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**: Submit for review

### Development Guidelines

- **Code Style**: Follow existing patterns and use linting tools
- **Testing**: Maintain >80% test coverage
- **Documentation**: Update README and docstrings for new features
- **Commits**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API
- **Ollama** for local LLM hosting
- **LM Studio** for local model management
- **FastAPI** for the backend framework
- **React** and **Streamlit** for frontend frameworks
- **Plotly** for data visualizations

## 📞 Support

- **Issues**: Report bugs via [GitHub Issues](https://github.com/your-username/contentScorecard/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/your-username/contentScorecard/discussions)
- **Documentation**: Check the `core/config/README.md` for detailed configuration help

---

**Made with ❤️ for content creators everywhere**
