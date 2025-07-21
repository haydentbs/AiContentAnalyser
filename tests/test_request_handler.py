"""Tests for the Request Handler."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from core.mcp.request_handler import RequestHandler
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
    
    # Mock the categories attribute
    mock_guide.categories = {
        "test_category": MagicMock(
            description="Test category",
            weight=1.0
        )
    }
    
    return mock_guide


@pytest.fixture
def handler(mock_coordinator, mock_guidelines):
    """Create a request handler for testing."""
    return RequestHandler(
        coordinator=mock_coordinator,
        guidelines=mock_guidelines,
        cache_size=10,
        request_timeout=5.0
    )


@pytest.mark.asyncio
async def test_handle_evaluate_content(handler):
    """Test handling content evaluation."""
    # Test with valid content
    result = await handler.handle_evaluate_content("Test content")
    assert result.overall_score == 4.0
    assert "test_category" in result.category_scores
    assert len(result.metric_results) == 1
    
    # Test with empty content
    result = await handler.handle_evaluate_content("")
    assert "error" in result
    
    # Test with invalid metrics
    result = await handler.handle_evaluate_content("Test content", ["invalid_metric"])
    assert "error" in result
    assert "available_metrics" in result


@pytest.mark.asyncio
async def test_handle_evaluate_metric(handler):
    """Test handling single metric evaluation."""
    # Test with valid metric
    result = await handler.handle_evaluate_metric("Test content", "test_metric")
    assert result["metric"] == "test_metric"
    assert result["score"] == 4
    assert result["reasoning"] == "Test reasoning"
    
    # Test with empty content
    result = await handler.handle_evaluate_metric("", "test_metric")
    assert "error" in result
    
    # Test with invalid metric
    result = await handler.handle_evaluate_metric("Test content", "invalid_metric")
    assert "error" in result
    assert "available_metrics" in result


@pytest.mark.asyncio
async def test_handle_get_guidelines(handler):
    """Test handling guidelines retrieval."""
    result = await handler.handle_get_guidelines()
    assert "categories" in result
    assert "metrics_by_category" in result
    assert "test_category" in result["categories"]
    assert "test_category" in result["metrics_by_category"]


@pytest.mark.asyncio
async def test_caching(handler):
    """Test result caching."""
    # First request should not be cached
    result1 = await handler.handle_evaluate_content("Test content")
    
    # Reset the mock to verify it's not called again
    handler.coordinator.evaluate_content.reset_mock()
    
    # Second request with same content should use cache
    result2 = await handler.handle_evaluate_content("Test content")
    
    # Verify the coordinator was not called again
    handler.coordinator.evaluate_content.assert_not_called()


@pytest.mark.asyncio
async def test_request_tracking(handler):
    """Test request progress tracking."""
    # Start a request
    content = "Test content"
    request_id = handler._generate_request_id(content)
    
    # Manually track the request
    handler._track_request_progress(request_id, 5)
    
    # Check initial status
    status = await handler.get_request_status(request_id)
    assert status["status"] == "in_progress"
    assert status["progress"] == 0
    assert status["total_metrics"] == 5
    
    # Update progress
    handler._update_request_progress(request_id, 3)
    
    # Check updated status
    status = await handler.get_request_status(request_id)
    assert status["status"] == "in_progress"
    assert status["progress"] == 60  # 3/5 * 100
    assert status["completed_metrics"] == 3
    
    # Complete the request
    handler._complete_request(request_id)
    
    # Check final status
    status = await handler.get_request_status(request_id)
    assert status["status"] == "completed"
    
    # Check non-existent request
    status = await handler.get_request_status("non_existent")
    assert "error" in status


@pytest.mark.asyncio
async def test_handle_request_status(handler):
    """Test handling request status checks."""
    # Start a request
    content = "Test content"
    request_id = handler._generate_request_id(content)
    
    # Manually track the request
    handler._track_request_progress(request_id, 5)
    
    # Check status through the handler
    status = await handler.handle_request_status(request_id)
    assert status["request_id"] == request_id
    assert status["status"] == "in_progress"
    
    # Check non-existent request
    status = await handler.handle_request_status("non_existent")
    assert "error" in status


@pytest.mark.asyncio
async def test_timeout_handling(handler):
    """Test handling request timeouts."""
    # Make the coordinator take longer than the timeout
    async def slow_evaluate(*args, **kwargs):
        await asyncio.sleep(10)
        return MagicMock()
    
    handler.coordinator.evaluate_content.side_effect = slow_evaluate
    
    # Request should timeout
    result = await handler.handle_evaluate_content("Test content")
    assert "error" in result
    assert "timeout" in result["error"]