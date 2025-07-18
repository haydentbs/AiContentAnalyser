# Implementation Plan

- [x] 1. Set up project structure and core data models
  - Create directory structure for agents, config, storage, and tests
  - Implement Pydantic data models for Metric, MetricResult, and EvaluationResult
  - Include fields for positive_examples and improvement_examples in MetricResult
  - Create base configuration classes with type validation
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2. Implement configuration management system
  - Create TOML configuration parser with Pydantic-Settings
  - Implement LLM provider configuration (OpenAI, Ollama, LM Studio)
  - Add environment variable support for API keys
  - Write unit tests for configuration loading and validation
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 3. Create guidelines management system
  - Implement YAML parser for guidelines configuration
  - Create default guidelines with 5 categories and multiple metrics
  - Add validation for metric weights and category structure
  - Implement fallback to default guidelines when file is missing
  - Write unit tests for guidelines loading and validation
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 4. Build LLM client abstraction layer
  - Create base LLM client interface for different providers
  - Implement OpenAI client with error handling and retries
  - Implement Ollama/local model client support
  - Add connection testing and validation methods
  - Write unit tests with mocked LLM responses
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 5. Implement MetricEvaluator agent for single metric evaluation
  - Create MetricEvaluator agent class with focused prompt generation
  - Implement single metric evaluation with structured LLM calls
  - Add response parsing for score (1-5), reasoning, improvement advice, and specific examples
  - Create Jinja2 prompt templates that request specific quotes and examples from the content
  - Ensure prompts ask for both positive examples (what works well) and areas for improvement with specific text references
  - Write unit tests with deterministic mock responses including example extraction
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6. Build Coordinator agent for orchestrating multiple evaluations
  - Create CoordinatorAgent class for managing evaluation workflow
  - Implement individual agent creation for each metric
  - Add parallel processing support for multiple metric evaluations
  - Implement weighted score aggregation across categories
  - Write integration tests for complete evaluation pipeline
  - _Requirements: 2.1, 3.4_

- [x] 7. Create report generation and storage system
  - Implement JSON report serialization with structured data
  - Create Markdown report generator with formatted output
  - Add file naming with timestamps and content hashes
  - Implement local file system storage in reports directory
  - Write unit tests for report generation and file operations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 8. Build basic Streamlit UI foundation
  - Create main.py with Streamlit app structure
  - Implement content input textarea with validation
  - Add file upload functionality for .md and .txt files
  - Create basic scoring trigger button
  - Add input validation and error messaging
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 9. Implement results visualization components
  - Create overall score display with gauge visualization
  - Implement Plotly radar chart for category scores
  - Add expandable sections for individual metric results
  - Display score, reasoning, improvement advice, and specific examples for each metric
  - Show positive examples (what works well) and improvement examples with specific text quotes
  - Write UI component tests for visualization rendering including example display
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 10. Add export functionality to UI
  - Implement JSON download button with file generation
  - Add Markdown report download functionality
  - Create file location notifications for saved reports
  - Add error handling for export operations
  - Test export functionality with various result formats
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 11. Integrate LLM configuration into UI
  - Add LLM provider selection interface
  - Implement configuration loading from config.toml
  - Add connection testing UI with status indicators
  - Display clear error messages for LLM connection failures
  - Test configuration switching between providers
  - _Requirements: 7.3, 7.4_

- [ ] 12. Create sample content system
  - Implement sample draft content in test fixtures
  - Add "Load Example" buttons for different content types
  - Create sample content covering various quality levels
  - Integrate sample loading into main UI
  - Test complete workflow with sample content
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 13. Add comprehensive error handling and user feedback
  - Implement error boundaries for LLM service failures
  - Add retry mechanisms with exponential backoff
  - Create user-friendly error messages with troubleshooting
  - Add loading states and progress indicators during evaluation
  - Test error scenarios and recovery workflows
  - _Requirements: 2.5, 7.4_

- [ ] 14. Implement end-to-end integration and testing
  - Create integration tests for complete evaluation workflow
  - Test with actual LLM providers using test API keys
  - Validate score aggregation and weighting calculations
  - Test file operations and report generation
  - Verify UI functionality with real content evaluation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

- [ ] 15. Add performance optimization and final polish
  - Implement async processing for parallel metric evaluations
  - Add caching for repeated evaluations of same content
  - Optimize UI responsiveness during long evaluations
  - Add session state management for better user experience
  - Create comprehensive documentation and usage examples
  - _Requirements: 6.1, 6.2, 6.3_