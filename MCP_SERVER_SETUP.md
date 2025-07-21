# Content Scorecard MCP Server

A Model Context Protocol (MCP) server that exposes Content Scorecard functionality to AI assistants. This server allows AI systems to submit content for analysis and receive detailed feedback on content quality metrics.

## 🌟 Features

The Content Scorecard MCP Server provides:

- **Content Analysis**: Submit text content for comprehensive evaluation across multiple quality dimensions
- **Detailed Scoring**: Receive scores and feedback on clarity, accuracy, engagement, completeness, and readability
- **Report Management**: Save, retrieve, and export evaluation reports
- **LLM Integration**: Test connections with different LLM providers (OpenAI, Ollama, LM Studio)
- **Guideline Access**: View evaluation categories and metrics
- **Flexible Configuration**: Customize evaluation parameters per request

## 📋 Prerequisites

- Python 3.9+
- Content Scorecard application (this repository)
- MCP library (`mcp>=1.0.0`) - already included in requirements.txt
- LLM Provider access (OpenAI API key, or local Ollama/LM Studio)

## 🚀 Quick Start

### 1. Installation

The MCP server is included with the Content Scorecard application. Ensure you have installed all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configuration

The server uses the same configuration as the main Content Scorecard application:

**config.toml:**
```toml
[llm]
provider = "openai"
model_name = "gpt-4"
temperature = 0.3
# api_key will be read from environment variable OPENAI_API_KEY

[app]
guidelines_path = "guidelines.yaml"
reports_dir = "reports"
ui_theme = "light"
```

### 3. Set Environment Variables

For OpenAI:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

For Ollama (if using local models):
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 4. Start the MCP Server

```bash
python3 mcp_server.py
```

The server will start and listen for MCP client connections via stdio.

## 🔌 Connecting to AI Assistants

### Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "content-scorecard": {
      "command": "python3",
      "args": ["/absolute/path/to/your/workspace/mcp_server.py"],
      "cwd": "/absolute/path/to/your/workspace"
    }
  }
}
```

**Important:** Use absolute paths and ensure Python can find all dependencies.

### Other MCP Clients

The server follows the standard MCP protocol and should work with any compliant MCP client. Configure the client to:

1. Use stdio transport
2. Run `python3 mcp_server.py` as the server command
3. Set the working directory to your Content Scorecard installation

## 🛠️ Available Tools

### `analyze_content`
Analyze content using the Content Scorecard evaluation system.

**Parameters:**
- `content` (string, required): The text content to analyze
- `custom_llm_provider` (string, optional): LLM provider to use (openai, ollama, lmstudio)
- `custom_llm_model` (string, optional): Specific model name
- `custom_temperature` (float, optional): Temperature for analysis (0.0-2.0)
- `save_report` (boolean, optional): Whether to save the report (default: true)

**Example:**
```json
{
  "content": "Your content here...",
  "custom_llm_provider": "openai",
  "custom_llm_model": "gpt-4",
  "save_report": true
}
```

### `get_report`
Retrieve a previously saved evaluation report.

**Parameters:**
- `report_id` (string, required): ID of the report to retrieve

### `test_llm_connection`
Test connection to an LLM provider.

**Parameters:**
- `provider` (string): LLM provider (default: "openai")
- `model_name` (string): Model to test (default: "gpt-4")
- `api_key` (string, optional): API key for testing
- `base_url` (string, optional): Custom base URL
- `temperature` (float): Temperature setting (default: 0.3)

### `get_evaluation_guidelines`
Get the complete evaluation guidelines structure.

**Returns:** Complete guidelines with categories, metrics, descriptions, and weights.

### `export_report`
Export a saved report in the specified format.

**Parameters:**
- `report_id` (string, required): ID of the report to export
- `format` (string): Export format - "json" or "markdown" (default: "json")

## 📊 Available Resources

### `config://current`
Returns the current server configuration in JSON format.

### `guidelines://categories`
Returns all evaluation categories and their metrics.

### `reports://list`
Lists all available saved reports with previews.

## 💬 Usage Examples

### Analyzing Content with Claude

Once connected to Claude Desktop, you can use natural language:

```
"Please analyze this blog post for content quality: [paste your content here]"
```

Claude will use the `analyze_content` tool to evaluate your content and provide detailed feedback.

### Getting Guidelines Information

```
"What are the evaluation criteria used by the Content Scorecard?"
```

Claude will use the `get_evaluation_guidelines` tool to show you all categories and metrics.

### Retrieving Previous Reports

```
"Show me the report with ID abc123"
```

Claude will use the `get_report` tool to retrieve the specific report.

## 🔧 Advanced Configuration

### Custom LLM Providers

You can specify different LLM providers for each analysis:

```json
{
  "content": "Your content...",
  "custom_llm_provider": "ollama",
  "custom_llm_model": "llama2",
  "custom_temperature": 0.7
}
```

### Environment Variables

The server respects these environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `LMSTUDIO_BASE_URL`: LM Studio server URL (default: http://localhost:1234)

### Guidelines Customization

Modify `guidelines.yaml` to customize evaluation criteria:

```yaml
categories:
  clarity:
    weight: 1.0
    description: "How clear and understandable is the content?"
    metrics:
      conciseness:
        description: "Is the writing free of unnecessary filler words?"
        weight: 0.5
      # Add more metrics...
```

## 🚨 Troubleshooting

### Server Won't Start

1. **Check Python Path**: Ensure Python can import all required modules
2. **Verify Configuration**: Check `config.toml` syntax and file paths
3. **Dependencies**: Run `pip install -r requirements.txt`
4. **Guidelines File**: Ensure `guidelines.yaml` exists and is valid

### Connection Issues

1. **Absolute Paths**: Use absolute paths in MCP client configuration
2. **Working Directory**: Set correct working directory in client config
3. **Permissions**: Ensure Python script has execute permissions

### Analysis Failures

1. **API Keys**: Verify LLM provider credentials are set correctly
2. **Network**: Check internet connection for OpenAI API
3. **Local Models**: Ensure Ollama/LM Studio are running for local providers

### Common Error Messages

- **"Application not properly initialized"**: Configuration or guidelines loading failed
- **"Guidelines not loaded"**: Check `guidelines.yaml` file and path
- **"Report storage not initialized"**: Check `reports` directory exists and is writable

## 📈 Performance Considerations

### Response Times

- **OpenAI API**: Typically 2-10 seconds depending on content length
- **Local Models**: 5-30 seconds depending on hardware and model size
- **Analysis Complexity**: More detailed content may take longer

### Concurrent Requests

The server handles one analysis at a time. For multiple simultaneous requests, consider:

1. Running multiple server instances
2. Using a load balancer
3. Implementing request queuing

## 🔒 Security Notes

1. **API Keys**: Store securely in environment variables, never in config files
2. **Content Privacy**: Local models (Ollama/LM Studio) keep content private
3. **Network**: OpenAI API sends content over HTTPS
4. **Reports**: Stored locally in `reports/` directory

## 📝 Report Format

Analysis reports include:

```json
{
  "overall_score": 4.2,
  "category_scores": {
    "clarity": 4.5,
    "accuracy": 4.0,
    "engagement": 3.8,
    "completeness": 4.3,
    "readability": 4.1
  },
  "metric_results": [
    {
      "metric": {"name": "conciseness", "category": "clarity"},
      "score": 4,
      "reasoning": "The content is generally concise...",
      "improvement_advice": "Consider removing redundant phrases..."
    }
  ],
  "timestamp": "2025-01-01T12:00:00",
  "content": "Original content here...",
  "llm_model": "gpt-4"
}
```

## 🤝 Integration Examples

### Programmatic Usage

```python
import subprocess
import json

# Start MCP server process
server = subprocess.Popen(['python3', 'mcp_server.py'], 
                         stdin=subprocess.PIPE, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)

# Send MCP request (simplified example)
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "analyze_content",
        "arguments": {
            "content": "Your content here..."
        }
    }
}

# Handle response
# (Full MCP client implementation required)
```

### Webhook Integration

The MCP server can be wrapped in a web service for HTTP-based integrations:

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.post("/analyze")
async def analyze_content_api(content: str):
    # Initialize MCP client
    # Call analyze_content tool
    # Return results
    pass
```

## 📞 Support

For issues related to:

- **Content Scorecard Application**: Check the main README.md
- **MCP Protocol**: Visit [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **LLM Providers**: Consult provider-specific documentation

## 🔄 Updates

The MCP server follows the same versioning as the main Content Scorecard application. Update by pulling the latest code and restarting the server.

---

**🎉 You're now ready to use the Content Scorecard MCP Server with your AI assistant!**