#!/usr/bin/env python3
"""
Content Scorecard MCP Server

A Model Context Protocol server that exposes Content Scorecard functionality
to AI assistants. This server allows AI systems to submit content for analysis
and receive detailed feedback on content quality metrics.

This server implements the MCP specification and provides tools for:
- Submitting content for analysis
- Retrieving analysis results
- Getting available evaluation categories and metrics
- Testing LLM provider connections
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, TextContent

# Import Content Scorecard components
from core.config.settings import load_app_config
from core.config.models import AppConfig, EvaluationResult, LLMConfig
from core.storage.guidelines import load_guidelines
from core.storage.reports import ReportStorage
from core.agents.llm_client import create_llm_client, ConnectionTestResult
from core.agents.coordinator_agent import CoordinatorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("content-scorecard")

# Global variables for application state
app_config: Optional[AppConfig] = None
guidelines = None
report_storage = None

def initialize_app():
    """Initialize the Content Scorecard application components."""
    global app_config, guidelines, report_storage
    
    try:
        # Load configuration
        config_path = "config.toml"
        app_config = load_app_config(config_path)
        logger.info(f"Loaded configuration from {config_path}")
        
        # Load guidelines
        guidelines = load_guidelines(app_config.guidelines_path)
        logger.info(f"Loaded guidelines from {app_config.guidelines_path}")
        
        # Initialize report storage
        report_storage = ReportStorage(app_config.reports_dir)
        logger.info(f"Initialized report storage in {app_config.reports_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        return False

@mcp.resource("config://current")
async def get_current_config() -> str:
    """Get the current application configuration."""
    if not app_config:
        return json.dumps({"error": "Application not initialized"})
    
    config_dict = {
        "llm": {
            "provider": app_config.llm.provider,
            "model_name": app_config.llm.model_name,
            "temperature": app_config.llm.temperature,
            "base_url": app_config.llm.base_url
        },
        "guidelines_path": app_config.guidelines_path,
        "reports_dir": app_config.reports_dir
    }
    return json.dumps(config_dict, indent=2)

@mcp.resource("guidelines://categories")
async def get_evaluation_categories() -> str:
    """Get all available evaluation categories and their metrics."""
    if not guidelines:
        return json.dumps({"error": "Guidelines not loaded"})
    
    categories_info = {}
    for category_name, category in guidelines.categories.items():
        metrics_info = {}
        for metric_name, metric in category.metrics.items():
            metrics_info[metric_name] = {
                "description": metric.description,
                "weight": metric.weight
            }
        
        categories_info[category_name] = {
            "description": category.description,
            "weight": category.weight,
            "metrics": metrics_info
        }
    
    return json.dumps(categories_info, indent=2)

@mcp.resource("reports://list")
async def list_reports() -> str:
    """List all available evaluation reports."""
    if not report_storage:
        return json.dumps({"error": "Report storage not initialized"})
    
    try:
        reports = report_storage.list_reports()
        reports_info = []
        for report_id in reports:
            try:
                report = report_storage.load_report(report_id)
                if report:
                    reports_info.append({
                        "id": report_id,
                        "timestamp": report.timestamp.isoformat(),
                        "overall_score": report.overall_score,
                        "content_preview": report.content[:100] + "..." if len(report.content) > 100 else report.content
                    })
            except Exception as e:
                logger.warning(f"Failed to load report {report_id}: {e}")
        
        return json.dumps(reports_info, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to list reports: {e}"})

@mcp.tool()
async def analyze_content(
    content: str,
    custom_llm_provider: Optional[str] = None,
    custom_llm_model: Optional[str] = None,
    custom_temperature: Optional[float] = None,
    save_report: bool = True
) -> Dict[str, Any]:
    """
    Analyze content using the Content Scorecard evaluation system.
    
    Args:
        content: The content to analyze (text to be evaluated)
        custom_llm_provider: Optional custom LLM provider (openai, ollama, lmstudio)
        custom_llm_model: Optional custom model name to use
        custom_temperature: Optional custom temperature for analysis (0.0-2.0)
        save_report: Whether to save the analysis report for later retrieval
    
    Returns:
        Dictionary containing the analysis results with overall score, category scores,
        detailed metric evaluations, and improvement recommendations.
    """
    if not app_config or not guidelines:
        return {"error": "Application not properly initialized"}
    
    try:
        # Determine LLM configuration
        llm_config = app_config.llm
        if custom_llm_provider or custom_llm_model or custom_temperature is not None:
            llm_config = LLMConfig(
                provider=custom_llm_provider or app_config.llm.provider,
                model_name=custom_llm_model or app_config.llm.model_name,
                temperature=custom_temperature if custom_temperature is not None else app_config.llm.temperature,
                api_key=app_config.llm.api_key,
                base_url=custom_llm_provider and app_config.llm.base_url or app_config.llm.base_url
            )
        
        # Create LLM client
        llm_client = create_llm_client(llm_config)
        
        # Create coordinator agent
        coordinator = CoordinatorAgent(llm_client)
        
        # Perform evaluation
        result = await coordinator.evaluate_content(content, guidelines)
        
        # Save report if requested
        if save_report and report_storage:
            try:
                report_id = report_storage.save_report(result)
                result_dict = result.model_dump()
                result_dict["report_id"] = report_id
            except Exception as e:
                logger.warning(f"Failed to save report: {e}")
                result_dict = result.model_dump()
                result_dict["warning"] = "Report generated but not saved"
        else:
            result_dict = result.model_dump()
        
        return result_dict
        
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

@mcp.tool()
async def get_report(report_id: str) -> Dict[str, Any]:
    """
    Retrieve a previously saved evaluation report.
    
    Args:
        report_id: The ID of the report to retrieve
    
    Returns:
        Dictionary containing the full evaluation report data.
    """
    if not report_storage:
        return {"error": "Report storage not initialized"}
    
    try:
        report = report_storage.load_report(report_id)
        if not report:
            return {"error": f"Report {report_id} not found"}
        
        return report.model_dump()
    except Exception as e:
        logger.error(f"Failed to retrieve report {report_id}: {e}")
        return {"error": f"Failed to retrieve report: {str(e)}"}

@mcp.tool()
async def test_llm_connection(
    provider: str = "openai",
    model_name: str = "gpt-4",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Test connection to an LLM provider.
    
    Args:
        provider: LLM provider to test (openai, ollama, lmstudio)
        model_name: Model name to test
        api_key: API key for the provider (if required)
        base_url: Base URL for the provider API
        temperature: Temperature setting for the test
    
    Returns:
        Dictionary containing connection test results and status.
    """
    try:
        # Create test LLM configuration
        test_config = LLMConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key or (app_config.llm.api_key if app_config else None),
            base_url=base_url,
            temperature=temperature
        )
        
        # Create LLM client
        llm_client = create_llm_client(test_config)
        
        # Test connection
        result = await llm_client.test_connection()
        
        # Convert result to dict if it's a Pydantic model
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        else:
            return {
                "success": True,
                "message": "Connection test completed",
                "details": str(result)
            }
        
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "details": "Failed to create or test LLM client"
        }

@mcp.tool()
async def get_evaluation_guidelines() -> Dict[str, Any]:
    """
    Get the complete evaluation guidelines including all categories and metrics.
    
    Returns:
        Dictionary containing the full guidelines structure with categories,
        metrics, descriptions, and weights.
    """
    if not guidelines:
        return {"error": "Guidelines not loaded"}
    
    try:
        guidelines_dict = {}
        
        for category_name, category in guidelines.categories.items():
            metrics_dict = {}
            for metric_name, metric in category.metrics.items():
                metrics_dict[metric_name] = {
                    "description": metric.description,
                    "weight": metric.weight
                }
            
            guidelines_dict[category_name] = {
                "description": category.description,
                "weight": category.weight,
                "metrics": metrics_dict
            }
        
        return {
            "version": getattr(guidelines, 'version', '1.0'),
            "categories": guidelines_dict,
            "total_categories": len(guidelines_dict)
        }
        
    except Exception as e:
        logger.error(f"Failed to get evaluation guidelines: {e}")
        return {"error": f"Failed to retrieve guidelines: {str(e)}"}

@mcp.tool()
async def export_report(report_id: str, format: str = "json") -> Dict[str, Any]:
    """
    Export a saved report in the specified format.
    
    Args:
        report_id: The ID of the report to export
        format: Export format (json or markdown)
    
    Returns:
        Dictionary containing the exported report data or file path.
    """
    if not report_storage:
        return {"error": "Report storage not initialized"}
    
    try:
        if format.lower() not in ["json", "markdown"]:
            return {"error": "Format must be 'json' or 'markdown'"}
        
        # Load the report
        report = report_storage.load_report(report_id)
        if not report:
            return {"error": f"Report {report_id} not found"}
        
        # Export the report
        export_path = report_storage.export_report(report_id, format.lower())
        
        if export_path and Path(export_path).exists():
            # Read the exported content
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_content = f.read()
            
            return {
                "success": True,
                "format": format.lower(),
                "file_path": str(export_path),
                "content": exported_content
            }
        else:
            return {"error": "Failed to export report"}
            
    except Exception as e:
        logger.error(f"Failed to export report {report_id}: {e}")
        return {"error": f"Export failed: {str(e)}"}

def main():
    """Main entry point for the MCP server."""
    # Initialize the application
    if not initialize_app():
        logger.error("Failed to initialize Content Scorecard application")
        sys.exit(1)
    
    logger.info("Content Scorecard MCP Server initialized successfully")
    logger.info("Available tools: analyze_content, get_report, test_llm_connection, get_evaluation_guidelines, export_report")
    logger.info("Available resources: config://current, guidelines://categories, reports://list")
    
    # Run the MCP server using sync method
    mcp.run()

if __name__ == "__main__":
    main()