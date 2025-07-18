# Design Document

## Overview

The Content Scorecard is a local web application built with Streamlit that provides AI-powered content evaluation using configurable guidelines. The system employs an agent-based architecture using LangChain to orchestrate LLM-powered evaluation agents that score content across multiple metrics and provide detailed feedback.

The application follows a simple three-layer architecture: a Streamlit web interface, an agent orchestration layer, and local file system storage. All processing happens in-process without external dependencies beyond LLM API calls.

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────┐
│                Streamlit UI Layer                   │
│  • Content input (textarea/file upload)            │
│  • Scoring trigger and progress display             │
│  • Results visualization (charts, metrics)         │
│  • Export functionality                            │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ HTTP/Function calls
                  │
┌─────────────────┴───────────────────────────────────┐
│              Agent Orchestration Layer              │
│  • Coordinator Agent (workflow management)         │
│  • MetricEvaluator Agents (individual scoring)     │
│  • Guidelines loader and parser                    │
│  • Score aggregation and weighting                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ File I/O
                  │
┌─────────────────┴───────────────────────────────────┐
│                Local File System                    │
│  • guidelines.yaml (evaluation criteria)           │
│  • config.toml (LLM and app configuration)         │
│  • reports/ (JSON and Markdown outputs)            │
│  • tests/fixtures/ (sample content)                │
└─────────────────────────────────────────────────────┘
```

### Agent Architecture

The system uses a coordinator-worker pattern with LangChain agents, emphasizing **individual LLM calls per metric** for maximum accuracy:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Coordinator    │───▶│ MetricEvaluator │───▶│   LLM Service   │
│     Agent       │    │   Agent #1      │    │ (OpenAI/Local)  │
│                 │    │ (Clarity)       │    │                 │
│ • Load guidelines│    │ • Score ONE     │    │ • Focused       │
│ • Manage workflow│    │   metric only   │    │   evaluation    │
│ • Aggregate scores│   │ • Detailed      │    │ • Specific      │
│ • Generate report│    │   reasoning     │    │   reasoning     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ├─────────────▶┌─────────────────┐    ┌─────────────────┐
         │              │ MetricEvaluator │───▶│   LLM Service   │
         │              │   Agent #2      │    │ (OpenAI/Local)  │
         │              │ (Accuracy)      │    │                 │
         │              │ • Score ONE     │    │ • Focused       │
         │              │   metric only   │    │   evaluation    │
         │              │ • Detailed      │    │ • Specific      │
         │              │   reasoning     │    │   reasoning     │
         │              └─────────────────┘    └─────────────────┘
         │
         └─────────────▶ ... (Additional MetricEvaluator Agents)
```

**Key Agentic Design Principles:**
- **One Agent Per Metric**: Each metric gets its own dedicated agent and LLM call
- **Focused Evaluation**: Agents concentrate on single aspects for higher accuracy
- **Independent Assessment**: No cross-contamination between metric evaluations
- **Detailed Reasoning**: Each agent provides specific, focused feedback
- **Parallel Processing**: Multiple agents can run concurrently for efficiency

## Components and Interfaces

### 1. User Interface Layer (Streamlit)

**Main Application (`main.py`)**
- Content input interface with textarea and file upload
- Configuration panel for LLM settings
- Scoring trigger button with progress indication
- Results display with interactive visualizations
- Export functionality for reports

**Key UI Components:**
- `st.text_area()` for draft input
- `st.file_uploader()` for .md/.txt files
- `st.button()` for scoring trigger
- `plotly.graph_objects.Scatterpolar` for radar charts
- `st.expander()` for detailed metric results
- `st.download_button()` for report exports

### 2. Agent Orchestration Layer

**Coordinator Agent (`agents/scorer.py`)**
```python
class CoordinatorAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        self.guidelines = load_guidelines()
        
    async def evaluate_content(self, content: str) -> EvaluationResult:
        # Load and validate guidelines
        # Create individual MetricEvaluator agent for EACH metric
        # Execute ONE LLM call per metric for maximum accuracy
        # Each agent focuses on single metric evaluation only
        # Aggregate weighted scores from individual results
        # Generate comprehensive report from all metric evaluations
        
    async def orchestrate_metric_evaluations(self, content: str) -> List[MetricResult]:
        # Iterate through each metric individually
        # Create dedicated agent instance per metric
        # Execute separate LLM calls for focused evaluation
        # Collect all individual metric results
        # Return comprehensive list of metric evaluations
```

**MetricEvaluator Agent (`agents/scorer.py`)**
```python
class MetricEvaluatorAgent:
    def __init__(self, llm_client: LLMClient, prompt_template: str):
        self.llm = llm_client
        self.prompt = prompt_template
        
    async def evaluate_single_metric(self, content: str, metric: Metric) -> MetricResult:
        # Format focused prompt for ONLY this specific metric
        # Make dedicated LLM call for this metric alone
        # Parse response for score, reasoning, and improvement advice
        # Return structured result with confidence score
        
    def create_focused_prompt(self, content: str, metric: Metric) -> str:
        # Generate highly specific prompt focusing solely on one metric
        # Include clear scoring criteria (1-5 scale)
        # Request specific reasoning and improvement suggestions
```

### 3. Configuration Management

**Configuration Schema (`config/models.py`)**
```python
class LLMConfig(BaseModel):
    provider: Literal["openai", "ollama", "lmstudio"]
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3

class AppConfig(BaseModel):
    llm: LLMConfig
    guidelines_path: str = "guidelines.yaml"
    reports_dir: str = "reports"
    ui_theme: str = "light"
```

### 4. Data Models

**Core Data Structures**
```python
class Metric(BaseModel):
    name: str
    description: str
    weight: float
    category: str

class MetricResult(BaseModel):
    metric: Metric
    score: int  # 1-5
    reasoning: str
    improvement_advice: str
    confidence: float

class EvaluationResult(BaseModel):
    content_hash: str
    timestamp: datetime
    overall_score: float
    category_scores: Dict[str, float]
    metric_results: List[MetricResult]
    metadata: Dict[str, Any]
```

### 5. Storage Layer

**Guidelines Management (`storage/guidelines.py`)**
- YAML parser for guidelines configuration
- Validation of metric weights and structure
- Default guidelines fallback system

**Report Storage (`storage/reports.py`)**
- JSON serialization for structured data
- Markdown generation for human-readable reports
- File naming with timestamps and content hashes

## Data Models

### Guidelines Structure (YAML)
```yaml
categories:
  clarity:
    weight: 1.0
    description: "How clear and understandable is the content?"
    metrics:
      conciseness:
        description: "Is the writing free of unnecessary filler words?"
        weight: 0.3
      jargon_usage:
        description: "Is technical jargon properly defined or avoided?"
        weight: 0.4
      logical_structure:
        description: "Does the content follow a logical flow with clear headings?"
        weight: 0.3
  
  accuracy:
    weight: 1.2
    description: "How factually correct and well-supported is the content?"
    metrics:
      data_support:
        description: "Are claims backed by credible data or sources?"
        weight: 0.6
      fact_verification:
        description: "Are there any apparent factual errors?"
        weight: 0.4
```

### Report Output Structure (JSON)
```json
{
  "evaluation_id": "eval_20240118_143022_abc123",
  "timestamp": "2024-01-18T14:30:22Z",
  "content_preview": "First 200 characters...",
  "overall_score": 3.8,
  "category_scores": {
    "clarity": 4.2,
    "accuracy": 3.5,
    "engagement": 3.9
  },
  "metric_results": [
    {
      "metric": "conciseness",
      "category": "clarity",
      "score": 4,
      "reasoning": "The writing is generally concise with minimal filler words...",
      "improvement_advice": "Consider removing redundant phrases in paragraphs 2 and 5...",
      "confidence": 0.85
    }
  ],
  "metadata": {
    "word_count": 1250,
    "llm_model": "gpt-4",
    "evaluation_duration": 45.2
  }
}
```

## Error Handling

### LLM Service Errors
- **Connection failures**: Retry with exponential backoff, fallback to cached responses
- **Rate limiting**: Queue requests with appropriate delays
- **Invalid responses**: Parse error handling with request retry
- **Model unavailability**: Clear error messages with alternative model suggestions

### File System Errors
- **Missing guidelines**: Load default configuration with user notification
- **Permission errors**: Clear error messages with troubleshooting steps
- **Disk space**: Check available space before saving reports
- **Corrupted files**: Validation with recovery suggestions

### Input Validation
- **Empty content**: User-friendly prompts for content input
- **File format errors**: Clear messaging about supported formats
- **Content length limits**: Warnings for very long content with chunking options

### UI Error States
- **Loading states**: Progress indicators during LLM processing
- **Error boundaries**: Graceful degradation with retry options
- **Session management**: Proper cleanup of temporary data

## Testing Strategy

### Unit Testing
- **Agent Logic**: Mock LLM responses for deterministic testing
- **Configuration**: Validate YAML parsing and schema validation
- **Data Models**: Test serialization/deserialization
- **Utilities**: Score aggregation and weighting calculations

### Integration Testing
- **End-to-End Workflow**: Complete evaluation pipeline with test content
- **File Operations**: Guidelines loading and report generation
- **LLM Integration**: Test with actual API calls using test keys

### UI Testing
- **Streamlit Components**: Session state management and user interactions
- **File Upload**: Various file formats and edge cases
- **Visualization**: Chart rendering with different data sets

### Performance Testing
- **Response Times**: Measure evaluation duration for different content lengths
- **Memory Usage**: Monitor resource consumption during processing
- **Concurrent Users**: Test multiple simultaneous evaluations

### Test Data
- **Sample Content**: Curated examples covering different quality levels
- **Edge Cases**: Very short/long content, special characters, various formats
- **Golden Standards**: Expected outputs for regression testing

The testing approach emphasizes fast local execution with comprehensive mocking for external dependencies, ensuring reliable development and deployment workflows.