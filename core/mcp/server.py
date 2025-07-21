"""MCP server implementation for Content Scorecard."""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from ..config.models import LLMConfig
from ..config.settings import load_config
from ..storage.guidelines import load_guidelines, Guidelines
from ..agents.coordinator_agent import CoordinatorAgent
from ..agents.llm_client import create_llm_client, BaseLLMClient

from .tool_registry import ToolRegistry
from .request_handler import RequestHandler
from .response_formatter import ResponseFormatter
from .coordinator_adapter import CoordinatorAdapter


logger = logging.getLogger(__name__)


class ContentScoreCardMCPServer:
    """MCP server for Content Scorecard."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Check if FastMCP is installed
        if FastMCP is None:
            raise ImportError(
                "FastMCP package not installed. Install with: pip install fastmcp"
            )
        
        # Load configuration
        self.config = load_config(config_path)
        self.logger.info(f"Loaded configuration from {config_path or 'default path'}")
        
        # Load guidelines
        self.guidelines = load_guidelines(self.config.guidelines_path)
        self.logger.info(f"Loaded guidelines from {self.config.guidelines_path}")
        
        # Create LLM client
        self.llm_client = create_llm_client(self.config.llm)
        self.logger.info(f"Created LLM client for provider: {self.config.llm.provider}")
        
        # Create coordinator agent
        self.coordinator = CoordinatorAgent(self.llm_client)
        self.logger.info("Created coordinator agent")
        
        # Create coordinator adapter
        self.coordinator_adapter = CoordinatorAdapter(self.coordinator)
        self.logger.info("Created coordinator adapter")
        
        # Create request handler
        self.request_handler = RequestHandler(self.coordinator_adapter, self.guidelines)
        self.logger.info("Created request handler")
        
        # Create tool registry
        self.tool_registry = ToolRegistry()
        self.logger.info("Created tool registry")
        
        # Create MCP server
        self.mcp_server = FastMCP()
        self.logger.info("Created MCP server")
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register content evaluation tools."""
        # Register evaluate_content tool
        self.tool_registry.register_tool(
            name="evaluate_content",
            description="Evaluate content against quality metrics and provide detailed feedback",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to evaluate"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of specific metrics to evaluate"
                    }
                },
                "required": ["content"]
            },
            handler_func=self.request_handler.handle_evaluate_content
        )
        
        # Register get_guidelines tool
        self.tool_registry.register_tool(
            name="get_guidelines",
            description="Get the current evaluation guidelines and available metrics",
            parameters={
                "type": "object",
                "properties": {}
            },
            handler_func=self.request_handler.handle_get_guidelines
        )
        
        # Register evaluate_metric tool
        self.tool_registry.register_tool(
            name="evaluate_metric",
            description="Evaluate content against a single specific metric",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to evaluate"
                    },
                    "metric": {
                        "type": "string",
                        "description": "The name of the metric to evaluate"
                    }
                },
                "required": ["content", "metric"]
            },
            handler_func=self.request_handler.handle_evaluate_metric
        )
        
        self.logger.info(f"Registered {len(self.tool_registry.list_tools())} tools")
    
    def _register_tools_with_mcp(self) -> None:
        """Register tools with the MCP server."""
        for name, tool in self.tool_registry.tools.items():
            self.mcp_server.register_tool(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                handler=self._create_tool_handler(tool.name)
            )
    
    def _create_tool_handler(self, tool_name: str) -> Callable:
        """Create a handler function for an MCP tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Handler function for the tool
        """
        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool or not tool.handler:
                return ResponseFormatter.format_error(f"Tool {tool_name} not found or has no handler")
            
            try:
                result = await tool.handler(**params)
                
                # Format the result based on its type
                if isinstance(result, dict) and "error" in result:
                    return result
                elif hasattr(result, "model_dump"):
                    # Handle Pydantic models
                    if isinstance(result, EvaluationResult):
                        return ResponseFormatter.format_evaluation_result(result)
                    else:
                        return result.model_dump()
                else:
                    return result
                    
            except Exception as e:
                self.logger.error(f"Error handling tool {tool_name}: {e}")
                return ResponseFormatter.format_error(f"Error: {str(e)}")
        
        return handler
    
    async def start(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the MCP server.
        
        Args:
            host: Host to listen on
            port: Port to listen on
        """
        self.logger.info(f"Starting MCP server on {host}:{port}")
        
        # Register tools with MCP
        self._register_tools_with_mcp()
        
        # Start the server
        await self.mcp_server.start(host=host, port=port)
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("Stopping MCP server")
        await self.mcp_server.stop()
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the LLM connection.
        
        Returns:
            Connection test result
        """
        self.logger.info("Testing LLM connection")
        result = await self.llm_client.test_connection()
        return {
            "success": result.success,
            "message": result.message,
            "response_time": result.response_time,
            "error": result.error
        }