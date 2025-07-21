"""Tests for the Tool Registry."""

import pytest
from typing import Dict, Any

from core.mcp.tool_registry import ToolRegistry, MCPToolDefinition


@pytest.fixture
def registry():
    """Create a tool registry for testing."""
    return ToolRegistry()


@pytest.fixture
def sample_tools():
    """Sample tool definitions for testing."""
    async def handler1(content: str):
        return {"result": f"Processed: {content}"}
    
    async def handler2(metric: str, content: str):
        return {"result": f"Evaluated {metric}: {content}"}
    
    async def handler3():
        return {"result": "Guidelines retrieved"}
    
    return [
        {
            "name": "evaluate_content",
            "description": "Evaluate content against all metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to evaluate"
                    }
                },
                "required": ["content"]
            },
            "handler": handler1,
            "group": "evaluation"
        },
        {
            "name": "evaluate_metric",
            "description": "Evaluate content against a specific metric",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Metric to evaluate"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to evaluate"
                    }
                },
                "required": ["metric", "content"]
            },
            "handler": handler2,
            "group": "evaluation"
        },
        {
            "name": "get_guidelines",
            "description": "Get evaluation guidelines",
            "parameters": {
                "type": "object",
                "properties": {}
            },
            "handler": handler3,
            "group": "configuration"
        }
    ]


def test_register_tool(registry):
    """Test registering a tool."""
    async def handler(content: str):
        return {"result": content}
    
    registry.register_tool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to process"
                }
            },
            "required": ["content"]
        },
        handler_func=handler
    )
    
    # Check that the tool was registered
    assert "test_tool" in registry.list_tools()
    
    # Check that we can retrieve the tool
    tool = registry.get_tool("test_tool")
    assert tool is not None
    assert tool.name == "test_tool"
    assert tool.description == "Test tool"
    assert tool.handler is not None


def test_register_tool_with_group(registry):
    """Test registering a tool with a group."""
    async def handler(content: str):
        return {"result": content}
    
    # Register a tool with a non-existent group
    registry.register_tool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to process"
                }
            },
            "required": ["content"]
        },
        handler_func=handler,
        group="test_group"
    )
    
    # Check that the group was created
    assert "test_group" in registry.list_groups()
    
    # Check that the tool was added to the group
    assert "test_tool" in registry.get_tools_by_group("test_group")
    
    # Check that the tool-to-group mapping was updated
    assert registry.tool_to_group["test_tool"] == "test_group"


def test_create_group(registry):
    """Test creating a group."""
    registry.create_group("test_group", "Test group description")
    
    # Check that the group was created
    assert "test_group" in registry.list_groups()
    
    # Check group info
    group_info = registry.get_group_info("test_group")
    assert group_info is not None
    assert group_info["name"] == "test_group"
    assert group_info["description"] == "Test group description"
    assert group_info["tools"] == []


def test_add_tool_to_group(registry):
    """Test adding a tool to a group."""
    async def handler(content: str):
        return {"result": content}
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to process"
                }
            },
            "required": ["content"]
        },
        handler_func=handler
    )
    
    # Create a group
    registry.create_group("test_group", "Test group description")
    
    # Add the tool to the group
    result = registry.add_tool_to_group("test_tool", "test_group")
    assert result is True
    
    # Check that the tool was added to the group
    assert "test_tool" in registry.get_tools_by_group("test_group")
    
    # Try adding a non-existent tool
    result = registry.add_tool_to_group("non_existent_tool", "test_group")
    assert result is False
    
    # Try adding to a non-existent group
    result = registry.add_tool_to_group("test_tool", "non_existent_group")
    assert result is False


def test_load_from_config(registry, sample_tools):
    """Test loading tool configuration from a dictionary."""
    # Register the sample tools
    for tool in sample_tools:
        registry.register_tool(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
            handler_func=tool["handler"]
        )
    
    # Create a configuration
    config = {
        "groups": {
            "evaluation": {
                "description": "Content evaluation tools"
            },
            "configuration": {
                "description": "Configuration tools"
            }
        },
        "tool_groups": {
            "evaluate_content": "evaluation",
            "evaluate_metric": "evaluation",
            "get_guidelines": "configuration"
        }
    }
    
    # Load the configuration
    registry.load_from_config(config)
    
    # Check that the groups were created
    assert "evaluation" in registry.list_groups()
    assert "configuration" in registry.list_groups()
    
    # Check that the tools were added to the groups
    assert "evaluate_content" in registry.get_tools_by_group("evaluation")
    assert "evaluate_metric" in registry.get_tools_by_group("evaluation")
    assert "get_guidelines" in registry.get_tools_by_group("configuration")


def test_validate_tool_parameters(registry):
    """Test validating tool parameters."""
    async def handler(content: str):
        return {"result": content}
    
    # Register a tool
    registry.register_tool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to process"
                }
            },
            "required": ["content"]
        },
        handler_func=handler
    )
    
    # Valid parameters
    result = registry.validate_tool_parameters("test_tool", {"content": "Test content"})
    assert "error" not in result
    
    # Missing required parameter
    result = registry.validate_tool_parameters("test_tool", {})
    assert "error" in result
    
    # Wrong parameter type
    result = registry.validate_tool_parameters("test_tool", {"content": 123})
    assert "error" in result
    
    # Non-existent tool
    result = registry.validate_tool_parameters("non_existent_tool", {"content": "Test content"})
    assert "error" in result


def test_get_tool_schemas(registry, sample_tools):
    """Test getting tool schemas."""
    # Register the sample tools
    for tool in sample_tools:
        registry.register_tool(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
            handler_func=tool["handler"]
        )
    
    # Get the schemas
    schemas = registry.get_tool_schemas()
    
    # Check that all tools have schemas
    for tool in sample_tools:
        assert tool["name"] in schemas
        assert schemas[tool["name"]]["name"] == tool["name"]
        assert schemas[tool["name"]]["description"] == tool["description"]
        assert schemas[tool["name"]]["parameters"] == tool["parameters"]