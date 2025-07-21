"""Tests for the MCP server."""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch

from core.mcp.server import ContentScoreCardMCPServer
from core.mcp.tool_registry import ToolRegistry
from core.mcp.request_handler import RequestHandler
from core.mcp.response_formatter import ResponseFormatter
from core.config.models import EvaluationResult, MetricResult, Metric


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client.test_connection.return_value = MagicMock(
        success=True,
        message="Connection successful",
        response_time=0.1,
        error=None
    )
    return mock_client


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


@pytest.mark.asyncio
async def test_tool_registry():
    """Test the tool registry."""
    registry = ToolRegistry()
    
    # Register a test tool
    async def test_handler(param1, param2):
        return {"result": f"{param1} {param2}"}
    
    registry.register_tool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"}
            },
            "required": ["param1", "param2"]
        },
        handler_func=test_handler
    )
    
    # Test tool retrieval
    tool = registry.get_tool("test_tool")
    assert tool is not None
    assert tool.name == "test_tool"
    assert tool.description == "Test tool"
    
    # Test tool listing
    tools = registry.list_tools()
    assert "test_tool" in tools
    
    # Test schema generation
    schemas = registry.get_tool_schemas()
    assert "test_tool" in schemas
    assert schemas["test_tool"]["name"] == "test_tool"
    assert schemas["test_tool"]["description"] == "Test tool"


@pytest.mark.asyncio
async def test_request_handler(mock_coordinator, mock_guidelines):
    """Test the request handler."""
    handler = RequestHandler(mock_coordinator, mock_guidelines)
    
    # Test evaluate_content
    result = await handler.handle_evaluate_content("Test content")
    assert result.overall_score == 4.0
    assert "test_category" in result.category_scores
    assert len(result.metric_results) == 1
    
    # Test with empty content
    result = await handler.handle_evaluate_content("")
    assert "error" in result
    
    # Test get_guidelines
    result = await handler.handle_get_guidelines()
    assert "categories" in result
    assert "metrics_by_category" in result
    
    # Test evaluate_metric
    result = await handler.handle_evaluate_metric("Test content", "test_metric")
    assert result["metric"] == "test_metric"
    assert result["score"] == 4
    
    # Test with invalid metric
    result = await handler.handle_evaluate_metric("Test content", "invalid_metric")
    assert "error" in result


def test_response_formatter():
    """Test the response formatter."""
    # Create test data
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
    
    # Test format_evaluation_result
    formatted = ResponseFormatter.format_evaluation_result(eval_result)
    assert formatted["overall_score"] == 4.0
    assert len(formatted["category_scores"]) == 1
    assert len(formatted["metric_results"]) == 1
    
    # Test format_metric_result
    formatted = ResponseFormatter.format_metric_result(metric_result)
    assert formatted["metric"] == "test_metric"
    assert formatted["score"] == 4
    assert formatted["reasoning"] == "Test reasoning"
    
    # Test format_error
    formatted = ResponseFormatter.format_error("Test error")
    assert formatted["error"] == "Test error"