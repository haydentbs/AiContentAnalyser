"""Unit tests for MetricEvaluator agent.

Tests the functionality of the MetricEvaluator agent for evaluating content
against specific metrics using structured LLM calls.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from config.models import Metric, MetricResult
from agents.llm_client import LLMResponse, LLMClientError
from agents.metric_evaluator import MetricEvaluator, EvaluationPromptTemplate


class TestMetricEvaluator:
    """Test MetricEvaluator agent implementation."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock_client = AsyncMock()
        mock_client.generate_response_with_retry = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def test_metric(self):
        """Create a test metric."""
        return Metric(
            name="clarity",
            description="How clear and understandable is the content?",
            weight=0.5,
            category="readability"
        )
    
    @pytest.fixture
    def test_content(self):
        """Create test content for evaluation."""
        return """# Sample Article
        
This is a sample article that will be used for testing the MetricEvaluator agent.
It contains multiple paragraphs with varying levels of clarity and structure.

## Section 1

This section is quite clear and well-structured. It uses simple language and
has a logical flow that's easy to follow.

## Section 2

This section is more complex and uses technical jargon without proper explanation.
The sentences are also quite long and convoluted, making it difficult to understand
the main points being conveyed in this particular section of the document.
"""
    
    def test_initialization(self, mock_llm_client):
        """Test that the MetricEvaluator initializes correctly."""
        # Default initialization
        evaluator = MetricEvaluator(mock_llm_client)
        assert evaluator.llm == mock_llm_client
        assert evaluator.prompt_template is not None
        
        # Custom prompt template
        custom_template = EvaluationPromptTemplate(
            system_prompt="Custom system prompt",
            user_prompt_template="Custom user prompt {{ metric.name }}"
        )
        evaluator = MetricEvaluator(mock_llm_client, prompt_template=custom_template)
        assert evaluator.prompt_template == custom_template
    
    def test_create_focused_prompt(self, mock_llm_client, test_metric, test_content):
        """Test that focused prompts are created correctly."""
        evaluator = MetricEvaluator(mock_llm_client)
        prompt = evaluator._create_focused_prompt(test_content, test_metric)
        
        # Check that the prompt contains the metric information
        assert test_metric.name in prompt
        assert test_metric.description in prompt
        assert test_metric.category in prompt
        
        # Check that the content is included
        assert test_content in prompt
        
        # Test content truncation
        long_content = "x" * 10000
        prompt = evaluator._create_focused_prompt(long_content, test_metric)
        assert "[Content truncated due to length...]" in prompt
        assert len(prompt) < len(long_content)
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_success(self, mock_llm_client, test_metric, test_content):
        """Test successful metric evaluation with valid JSON response."""
        # Mock the LLM response with valid JSON
        mock_response = LLMResponse(
            content="""```json
{
  "score": 4,
  "reasoning": "The content is generally clear and well-structured.",
  "improvement_advice": "Consider simplifying Section 2 by breaking down complex sentences.",
  "positive_examples": [
    "This section is quite clear and well-structured.",
    "It uses simple language and has a logical flow that's easy to follow."
  ],
  "improvement_examples": [
    "This section is more complex and uses technical jargon without proper explanation.",
    "The sentences are also quite long and convoluted, making it difficult to understand the main points being conveyed in this particular section of the document."
  ]
}
```""",
            model="gpt-4.1-nano-2025-04-14",
            usage={"total_tokens": 500}
        )
        mock_llm_client.generate_response_with_retry.return_value = mock_response
        
        evaluator = MetricEvaluator(mock_llm_client)
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify the result
        assert isinstance(result, MetricResult)
        assert result.metric == test_metric
        assert result.score == 4
        assert "generally clear and well-structured" in result.reasoning
        assert "simplifying Section 2" in result.improvement_advice
        assert len(result.positive_examples) == 2
        assert len(result.improvement_examples) == 2
        assert result.confidence > 0.9  # High confidence for complete response
        
        # Verify the LLM was called with the correct parameters
        mock_llm_client.generate_response_with_retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_direct_json(self, mock_llm_client, test_metric, test_content):
        """Test evaluation with direct JSON response (no code block)."""
        # Mock the LLM response with direct JSON
        mock_response = LLMResponse(
            content="""
{
  "score": 3,
  "reasoning": "The content has mixed clarity levels.",
  "improvement_advice": "Improve Section 2 readability.",
  "positive_examples": ["This section is quite clear and well-structured."],
  "improvement_examples": ["This section is more complex and uses technical jargon without proper explanation."]
}
""",
            model="gpt-4.1-nano-2025-04-14",
            usage={"total_tokens": 400}
        )
        mock_llm_client.generate_response_with_retry.return_value = mock_response
        
        evaluator = MetricEvaluator(mock_llm_client)
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify the result
        assert result.score == 3
        assert "mixed clarity levels" in result.reasoning
        assert len(result.positive_examples) == 1
        assert len(result.improvement_examples) == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_invalid_json(self, mock_llm_client, test_metric, test_content):
        """Test evaluation with non-JSON response that requires manual parsing."""
        # Mock the LLM response with non-JSON format
        mock_response = LLMResponse(
            content="""
Score: 2

Reasoning: The content has significant clarity issues, particularly in Section 2.

Improvement Advice: 
- Break down complex sentences
- Define technical terms
- Improve paragraph structure

Positive Examples:
- "This section is quite clear and well-structured."
- "It uses simple language and has a logical flow that's easy to follow."

Improvement Examples:
- "This section is more complex and uses technical jargon without proper explanation."
- "The sentences are also quite long and convoluted, making it difficult to understand the main points being conveyed in this particular section of the document."
""",
            model="gpt-4.1-nano-2025-04-14",
            usage={"total_tokens": 450}
        )
        mock_llm_client.generate_response_with_retry.return_value = mock_response
        
        evaluator = MetricEvaluator(mock_llm_client)
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify the result
        assert result.score == 2
        assert "clarity issues" in result.reasoning
        assert len(result.positive_examples) > 0
        assert len(result.improvement_examples) > 0
        assert result.confidence < 1.0  # Lower confidence due to manual parsing
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_llm_error(self, mock_llm_client, test_metric, test_content):
        """Test handling of LLM client errors."""
        # Mock the LLM client to raise an error
        mock_llm_client.generate_response_with_retry.side_effect = LLMClientError("LLM service unavailable")
        
        evaluator = MetricEvaluator(mock_llm_client)
        
        # Verify that the error is propagated
        with pytest.raises(LLMClientError, match="LLM service unavailable"):
            await evaluator.evaluate_metric(test_content, test_metric)
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_empty_content(self, mock_llm_client, test_metric):
        """Test handling of empty content."""
        evaluator = MetricEvaluator(mock_llm_client)
        
        # Verify that empty content raises a ValueError
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await evaluator.evaluate_metric("", test_metric)
        
        # Verify that whitespace-only content also raises a ValueError
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await evaluator.evaluate_metric("   \n   ", test_metric)
    
    @pytest.mark.asyncio
    async def test_parse_response_invalid_score(self, mock_llm_client, test_metric, test_content):
        """Test handling of responses with invalid scores."""
        # Mock the LLM response with an invalid score
        mock_response = LLMResponse(
            content="""
{
  "score": 10,
  "reasoning": "The content is excellent.",
  "improvement_advice": "No improvements needed.",
  "positive_examples": ["Good example"],
  "improvement_examples": []
}
""",
            model="gpt-4.1-nano-2025-04-14",
            usage={"total_tokens": 300}
        )
        mock_llm_client.generate_response_with_retry.return_value = mock_response
        
        evaluator = MetricEvaluator(mock_llm_client)
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify the score is clamped to the valid range
        assert result.score == 5  # Clamped to maximum
        
        # Test with a score below the valid range
        mock_response.content = '{"score": -1, "reasoning": "Poor content", "improvement_advice": "Rewrite everything", "positive_examples": [], "improvement_examples": ["Bad example"]}'
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify the score is clamped to the valid range
        assert result.score == 1  # Clamped to minimum
    
    @pytest.mark.asyncio
    async def test_parse_response_missing_fields(self, mock_llm_client, test_metric, test_content):
        """Test handling of responses with missing fields."""
        # Mock the LLM response with missing fields
        mock_response = LLMResponse(
            content="""
{
  "score": 3
}
""",
            model="gpt-4.1-nano-2025-04-14",
            usage={"total_tokens": 200}
        )
        mock_llm_client.generate_response_with_retry.return_value = mock_response
        
        evaluator = MetricEvaluator(mock_llm_client)
        result = await evaluator.evaluate_metric(test_content, test_metric)
        
        # Verify default values are used for missing fields
        assert result.score == 3
        assert result.reasoning == "No reasoning provided"
        assert result.improvement_advice == "No improvement advice provided"
        assert result.positive_examples == []
        assert result.improvement_examples == []
        assert result.confidence < 0.5  # Low confidence due to missing fields