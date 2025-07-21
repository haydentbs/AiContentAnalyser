"""Tests for the Response Formatter."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from core.mcp.response_formatter import ResponseFormatter, ResponseFormat, FormattingError
from core.config.models import EvaluationResult, MetricResult, Metric


@pytest.fixture
def sample_evaluation_result():
    """Create a sample evaluation result for testing."""
    # Create metrics
    metric1 = Metric(
        name="clarity",
        description="How clear is the content",
        weight=0.5,
        category="readability"
    )
    
    metric2 = Metric(
        name="structure",
        description="How well structured is the content",
        weight=0.5,
        category="readability"
    )
    
    metric3 = Metric(
        name="accuracy",
        description="How accurate is the content",
        weight=1.0,
        category="quality"
    )
    
    # Create metric results
    metric_result1 = MetricResult(
        metric=metric1,
        score=4,
        reasoning="The content is generally clear and easy to understand.",
        improvement_advice="Consider simplifying some technical terms for broader audience.",
        positive_examples=["The introduction clearly states the purpose.", "Key concepts are well explained."],
        improvement_examples=["The section on implementation could be clearer.", "Some technical jargon could be simplified."],
        confidence=0.9
    )
    
    metric_result2 = MetricResult(
        metric=metric2,
        score=3,
        reasoning="The structure is adequate but could be improved.",
        improvement_advice="Consider adding more subheadings and bullet points for better organization.",
        positive_examples=["The conclusion effectively summarizes the main points."],
        improvement_examples=["The middle section feels disorganized.", "Related concepts are scattered throughout."],
        confidence=0.8
    )
    
    metric_result3 = MetricResult(
        metric=metric3,
        score=5,
        reasoning="The content is highly accurate with well-supported claims.",
        improvement_advice="No major improvements needed for accuracy.",
        positive_examples=["All statistics are properly cited.", "Technical details are correct."],
        improvement_examples=[],
        confidence=0.95
    )
    
    # Create evaluation result
    return EvaluationResult(
        content_hash="abc123",
        timestamp=datetime(2025, 7, 21, 10, 30, 0),
        overall_score=4.0,
        category_scores={"readability": 3.5, "quality": 5.0},
        metric_results=[metric_result1, metric_result2, metric_result3],
        metadata={"evaluation_time": "2025-07-21T10:30:00", "metrics_evaluated": 3}
    )


def test_format_evaluation_result_default(sample_evaluation_result):
    """Test formatting an evaluation result with default options."""
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result)
    
    # Check basic structure
    assert "overall_score" in formatted
    assert "category_scores" in formatted
    assert "metric_results" in formatted
    assert "timestamp" in formatted
    assert "content_hash" in formatted
    
    # Check metric results
    assert len(formatted["metric_results"]) == 3
    
    # Check examples are included by default
    assert "positive_examples" in formatted["metric_results"][0]
    assert "improvement_examples" in formatted["metric_results"][0]
    
    # Check confidence is not included by default
    assert "confidence" not in formatted["metric_results"][0]


def test_format_evaluation_result_compact(sample_evaluation_result):
    """Test formatting an evaluation result with compact format."""
    format_options = ResponseFormat(format_type="compact")
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result, format_options)
    
    # Check that text fields are truncated
    assert len(formatted["metric_results"][0]["reasoning"]) <= 100
    assert len(formatted["metric_results"][0]["improvement_advice"]) <= 100
    
    # Check that examples are limited
    assert len(formatted["metric_results"][0]["positive_examples"]) <= 1
    assert len(formatted["metric_results"][0]["improvement_examples"]) <= 1


def test_format_evaluation_result_detailed(sample_evaluation_result):
    """Test formatting an evaluation result with detailed format."""
    format_options = ResponseFormat(format_type="detailed")
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result, format_options)
    
    # Check additional fields for detailed format
    assert "summary" in formatted
    assert "recommendations" in formatted
    
    # Check summary content
    assert "Overall score: 4.0/5.0" in formatted["summary"]
    assert "Strongest in quality (5.0/5.0)" in formatted["summary"]
    
    # Check recommendations
    assert len(formatted["recommendations"]) > 0
    assert "Improve structure (3/5)" in formatted["recommendations"][0]


def test_format_evaluation_result_no_examples(sample_evaluation_result):
    """Test formatting an evaluation result without examples."""
    format_options = ResponseFormat(include_examples=False)
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result, format_options)
    
    # Check examples are not included
    assert "positive_examples" not in formatted["metric_results"][0]
    assert "improvement_examples" not in formatted["metric_results"][0]


def test_format_evaluation_result_with_confidence(sample_evaluation_result):
    """Test formatting an evaluation result with confidence scores."""
    format_options = ResponseFormat(include_confidence=True)
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result, format_options)
    
    # Check confidence is included
    assert "confidence" in formatted["metric_results"][0]
    assert formatted["metric_results"][0]["confidence"] == 0.9


def test_format_evaluation_result_no_metadata(sample_evaluation_result):
    """Test formatting an evaluation result without metadata."""
    format_options = ResponseFormat(include_metadata=False)
    formatted = ResponseFormatter.format_evaluation_result(sample_evaluation_result, format_options)
    
    # Check metadata is not included
    assert "timestamp" not in formatted
    assert "content_hash" not in formatted
    assert "metadata" not in formatted


def test_format_metric_result(sample_evaluation_result):
    """Test formatting a single metric result."""
    metric_result = sample_evaluation_result.metric_results[0]
    
    # Test with default options
    formatted = ResponseFormatter.format_metric_result(metric_result)
    assert formatted["metric"] == "clarity"
    assert formatted["score"] == 4
    assert "positive_examples" in formatted
    assert "confidence" not in formatted
    
    # Test with custom options
    format_options = ResponseFormat(include_examples=False, include_confidence=True)
    formatted = ResponseFormatter.format_metric_result(metric_result, format_options)
    assert "positive_examples" not in formatted
    assert "confidence" in formatted


def test_format_error():
    """Test formatting an error response."""
    # Test with just an error message
    formatted = ResponseFormatter.format_error("Test error")
    assert formatted["error"] == "Test error"
    
    # Test with additional details
    formatted = ResponseFormatter.format_error("Test error", {"code": 404, "details": "Not found"})
    assert formatted["error"] == "Test error"
    assert formatted["code"] == 404
    assert formatted["details"] == "Not found"


def test_truncate_text():
    """Test text truncation."""
    # Test with text shorter than max length
    assert ResponseFormatter._truncate_text("Short text", 20) == "Short text"
    
    # Test with text longer than max length
    assert ResponseFormatter._truncate_text("This is a long text that needs truncation", 20) == "This is a long te..."


def test_generate_summary(sample_evaluation_result):
    """Test generating a summary."""
    summary = ResponseFormatter._generate_summary(sample_evaluation_result)
    
    # Check that the summary contains key information
    assert "Overall score: 4.0/5.0" in summary
    assert "Strongest in quality" in summary
    assert "Areas for improvement include readability" in summary


def test_generate_recommendations(sample_evaluation_result):
    """Test generating recommendations."""
    recommendations = ResponseFormatter._generate_recommendations(sample_evaluation_result)
    
    # Check that recommendations are generated for the lowest scoring metrics
    assert len(recommendations) > 0
    assert "Improve structure (3/5)" in recommendations[0]