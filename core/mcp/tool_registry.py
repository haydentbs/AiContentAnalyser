"""Tool registry for MCP server."""

import logging
import json
import jsonschema
from typing import Dict, Any, Callable, List, Optional, Union

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


class MCPToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""
    type: str
    description: str
    required: bool = False
    enum: Optional[List[Any]] = None
    
    class Config:
        extra = "allow"


class MCPToolDefinition(BaseModel):
    """Definition of an MCP tool."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for tool parameters")
    handler: Optional[Callable] = Field(None, description="Function to handle tool invocation")
    
    @validator('parameters')
    def validate_parameters_schema(cls, v):
        """Validate that parameters is a valid JSON schema."""
        try:
            # Validate that it's a proper JSON schema
            if not isinstance(v, dict):
                raise ValueError("Parameters must be a dictionary")
            
            # Check for required fields in a JSON schema
            if "type" not in v:
                raise ValueError("Parameters schema must have a 'type' field")
            
            # If it's an object type, it should have properties
            if v["type"] == "object" and "properties" not in v:
                raise ValueError("Object type parameters must have a 'properties' field")
            
            # Try to validate the schema itself
            jsonschema.Draft7Validator.check_schema(v)
            
            return v
        except Exception as e:
            raise ValueError(f"Invalid parameters schema: {str(e)}")
    
    def validate_parameters(self, params: Dict[str, Any]) -> Union[Dict[str, Any], Dict[str, str]]:
        """Validate parameters against the schema.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Validated parameters or error dictionary
        """
        try:
            jsonschema.validate(instance=params, schema=self.parameters)
            return params
        except jsonschema.exceptions.ValidationError as e:
            return {"error": f"Parameter validation failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error during parameter validation: {str(e)}"}


class ToolGroup(BaseModel):
    """Group of related tools."""
    name: str = Field(..., description="Name of the tool group")
    description: str = Field(..., description="Description of the tool group")
    tools: List[str] = Field(default_factory=list, description="List of tool names in this group")


class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.groups: Dict[str, ToolGroup] = {}
        self.tool_to_group: Dict[str, str] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register_tool(
        self, 
        name: str, 
        description: str, 
        parameters: Dict[str, Any], 
        handler_func: Callable,
        group: Optional[str] = None
    ) -> None:
        """Register a new tool with the registry.
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
            parameters: JSON schema for tool parameters
            handler_func: Function to handle tool invocation
            group: Optional group to add the tool to
        """
        self.logger.info(f"Registering tool: {name}")
        
        # Create the tool definition
        tool = MCPToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler_func
        )
        
        # Add to tools dictionary
        self.tools[name] = tool
        
        # Add to group if specified
        if group:
            if group not in self.groups:
                self.logger.warning(f"Group '{group}' not found, creating it")
                self.create_group(group, f"Tools related to {group}")
            
            self.add_tool_to_group(name, group)
    
    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get a tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            Tool definition or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all registered tools.
        
        Returns:
            Dictionary mapping tool names to their schemas
        """
        schemas = {}
        for name, tool in self.tools.items():
            schemas[name] = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        return schemas
        
    def create_group(self, name: str, description: str) -> None:
        """Create a new tool group.
        
        Args:
            name: Name of the group
            description: Description of the group
        """
        self.logger.info(f"Creating tool group: {name}")
        self.groups[name] = ToolGroup(
            name=name,
            description=description
        )
    
    def add_tool_to_group(self, tool_name: str, group_name: str) -> bool:
        """Add a tool to a group.
        
        Args:
            tool_name: Name of the tool
            group_name: Name of the group
            
        Returns:
            True if successful, False otherwise
        """
        if tool_name not in self.tools:
            self.logger.warning(f"Tool '{tool_name}' not found")
            return False
        
        if group_name not in self.groups:
            self.logger.warning(f"Group '{group_name}' not found")
            return False
        
        # Add tool to group
        if tool_name not in self.groups[group_name].tools:
            self.groups[group_name].tools.append(tool_name)
        
        # Update tool-to-group mapping
        self.tool_to_group[tool_name] = group_name
        
        self.logger.info(f"Added tool '{tool_name}' to group '{group_name}'")
        return True
    
    def get_tools_by_group(self, group_name: str) -> List[str]:
        """Get all tools in a group.
        
        Args:
            group_name: Name of the group
            
        Returns:
            List of tool names in the group
        """
        if group_name not in self.groups:
            self.logger.warning(f"Group '{group_name}' not found")
            return []
        
        return self.groups[group_name].tools
    
    def list_groups(self) -> List[str]:
        """List all tool groups.
        
        Returns:
            List of group names
        """
        return list(self.groups.keys())
    
    def get_group_info(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a group.
        
        Args:
            group_name: Name of the group
            
        Returns:
            Group information or None if not found
        """
        if group_name not in self.groups:
            return None
        
        group = self.groups[group_name]
        return {
            "name": group.name,
            "description": group.description,
            "tools": group.tools
        }
    
    def load_from_config(self, config: Dict[str, Any]) -> None:
        """Load tool configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
        """
        self.logger.info("Loading tool configuration")
        
        # Load groups
        if "groups" in config:
            for group_name, group_config in config["groups"].items():
                self.create_group(
                    name=group_name,
                    description=group_config.get("description", f"Tools related to {group_name}")
                )
        
        # Load tool-to-group mappings
        if "tool_groups" in config:
            for tool_name, group_name in config["tool_groups"].items():
                if tool_name in self.tools and group_name in self.groups:
                    self.add_tool_to_group(tool_name, group_name)
                else:
                    self.logger.warning(f"Cannot add tool '{tool_name}' to group '{group_name}': tool or group not found")
    
    def validate_tool_parameters(self, tool_name: str, params: Dict[str, Any]) -> Union[Dict[str, Any], Dict[str, str]]:
        """Validate parameters for a tool.
        
        Args:
            tool_name: Name of the tool
            params: Parameters to validate
            
        Returns:
            Validated parameters or error dictionary
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        
        return tool.validate_parameters(params)