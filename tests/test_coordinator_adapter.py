"""Tests for the CoordinatorAdapter."""

import pytest
from unittest.mock import MagicMock, patch

from core.mcp.coordinator_adapter import CoordinatorAdapter
from core.config.models import EvaluationResult, MetricResult, Metric


@pytest.fixture
def mock_coordinator():
    """Mock coordinator agent for testing."""
    mock_coord = MagicMock()
    
    # Create a mock evaluation result
    metric = Metric(
        name="test_metric",
        description="Test metric",
        weight=1.0,
        category="test_category"
    )
    
    metric_result = MetricResult(
        metric=metric,
        score=4,
        reasoning="Test reasoning",
        improvement_advice="Test advice",
        positive_examples=["Example 1", "Example 2"],
        improvement_examples=["Example 3", "Example 4"]
    )
    
    eval_result = EvaluationResult(
        content_hash="test_hash",
        overall_score=4.0,
        category_scores={"test_category": 4.0},
        metric_results=[metric_result]
    )
    
    mock_coord.evaluate_content.return_value = eval_result
    return mock_coord


@pytest.fixture
def mock_guidelines():
    """Mock guidelines for testing."""
    mock_guide = MagicMock()
    
    # Create a mock metric
    metric = Metric(
        name="test_metric",
        description="Test metric",
        weight=1.0,
        category="test_category"
    )
    
    mock_guide.to_metrics_list.return_value = [metric]
    return mock_guide


@pytest.fixture
def adapter(mock_coordinator):
    """Create a coordinator adapter for testing."""
    return CoordinatorAdapter(mock_coordinator)


@pytest.mark.asyncio
async def test_evaluate_content(adapter, mock_guidelines):
    """Test evaluating content through the adapter."""
    # Test with valid content
    result = await adapter.evaluate_content(
        content="Test content",
        guidelines=mock_guidelines
    )
    
    # Verify the coordinator was called
    adapter.coordinator.evaluate_content.assert_called_once()
    
    # Verify the result
    assert result.overall_score == 4.0
    assert "test_category" in result.category_scores
    assert len(result.metric_results) == 1


@pytest.mark.asyncio
async def test_evaluate_content_with_progress_tracking(adapter, mock_guidelines):
    """Test evaluating content with progress tracking."""
    # Create a mock progress callback
    progress_callback = MagicMock()
    
    # Register the callback
    request_id = "test_request"
    adapter.register_progress_callback(request_id, progress_callback)
    
    # Test with valid content
    result = await adapter.evaluate_content(
        content="Test content",
        guidelines=mock_guidelines,
        request_id=request_id
    )
    
    # Verify the coordinator was called
    adapter.coordinator.evaluate_content.assert_called_once()
    
    # Verify the result
    assert result.overall_score == 4.0
    
    # Unregister the callback
    adapter.unregister_progress_callback(request_id)
    
    # Verify the callback was removed
    assert request_id not in adapter.progress_callbacks


@pytest.mark.asyncio
async def test_evaluate_metric(adapter, mock_guidelines):
    """Test evaluating a single metric through the adapter."""
    # Test with valid metric
    result = await adapter.evaluate_metric(
        content="Test content",
        metric_name="test_metric",
        guidelines=mock_guidelines
    )
    
    # Verify the coordinator was called
    adapter.coordinator.evaluate_content.assert_called_once()
    
    # Verify the result is a MetricResult
    assert isinstance(result, MetricResult)
    assert result.metric.name == "test_metric"
    assert result.score == 4


@pytest.mark.asyncio
async def test_evaluate_invalid_metric(adapter, mock_guidelines):
    """Test evaluating an invalid metric."""
    # Test with invalid metric
    result = await adapter.evaluate_metric(
        content="Test content",
        metric_name="invalid_metric",
        guidelines=mock_guidelines
    )
    
    # Verify the result is an error dictionary
    assert isinstance(result, dict)
    assert "error" in result
    assert "invalid_metric" in result["error"]


@pytest.mark.asyncio
async def test_error_handling(adapter, mock_guidelines):
    """Test error handling in the adapter."""
    # Make the coordinator raise an exception
    adapter.coordinator.evaluate_content.side_effect = ValueError("Test error")
    
    # Test with valid content
    result = await adapter.evaluate_content(
        content="Test content",
        guidelines=mock_guidelines
    )
    
    # Verify the result is an error dictionary
    assert isinstance(result, dict)
    assert "error" in result
    assert "Test error" in result["error"]