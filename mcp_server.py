#!/usr/bin/env python3
"""CLI script to start the Content Scorecard MCP server."""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from core.mcp.server import ContentScoreCardMCPServer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Start the Content Scorecard MCP server")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file",
        default="config.toml"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        help="Host to listen on",
        default="localhost"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        help="Port to listen on",
        default=8000
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.warning(f"Config file {args.config} not found, using default configuration")
    
    try:
        # Create and start the MCP server
        server = ContentScoreCardMCPServer(config_path=args.config)
        
        # Test LLM connection
        connection_test = await server.test_connection()
        if connection_test["success"]:
            logger.info(f"LLM connection test successful: {connection_test['message']}")
        else:
            logger.warning(f"LLM connection test failed: {connection_test['error']}")
            logger.warning("The server will start, but content evaluation may not work correctly")
        
        # Start the server
        logger.info(f"Starting MCP server on {args.host}:{args.port}")
        await server.start(host=args.host, port=args.port)
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server")
        if 'server' in locals():
            await server.stop()
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())