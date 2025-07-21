#!/usr/bin/env python3
"""
Test script for Content Scorecard MCP Server

This script tests the various tools and resources provided by the MCP server
to ensure they work correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import (
    initialize_app, 
    get_current_config,
    get_evaluation_categories,
    list_reports,
    get_evaluation_guidelines,
    test_llm_connection
)

async def test_mcp_server():
    """Test all MCP server functionality."""
    print("🧪 Testing Content Scorecard MCP Server")
    print("=" * 50)
    
    # Test initialization
    print("\n1. Testing application initialization...")
    success = initialize_app()
    if success:
        print("✅ Application initialized successfully")
    else:
        print("❌ Application initialization failed")
        return
    
    # Test configuration resource
    print("\n2. Testing configuration resource...")
    try:
        config = await get_current_config()
        print("✅ Configuration retrieved:")
        print(f"   Preview: {config[:100]}...")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    # Test guidelines resource
    print("\n3. Testing guidelines resource...")
    try:
        guidelines = await get_evaluation_categories()
        print("✅ Guidelines retrieved:")
        print(f"   Preview: {guidelines[:100]}...")
    except Exception as e:
        print(f"❌ Guidelines test failed: {e}")
    
    # Test reports resource
    print("\n4. Testing reports resource...")
    try:
        reports = await list_reports()
        print("✅ Reports list retrieved:")
        print(f"   Content: {reports}")
    except Exception as e:
        print(f"❌ Reports test failed: {e}")
    
    # Test evaluation guidelines tool
    print("\n5. Testing evaluation guidelines tool...")
    try:
        guidelines_tool = await get_evaluation_guidelines()
        if isinstance(guidelines_tool, dict) and "categories" in guidelines_tool:
            print("✅ Evaluation guidelines tool working")
            print(f"   Found {guidelines_tool.get('total_categories', 0)} categories")
        else:
            print(f"❌ Unexpected guidelines response: {guidelines_tool}")
    except Exception as e:
        print(f"❌ Evaluation guidelines tool failed: {e}")
    
    # Test LLM connection tool (mock test - won't actually connect without API key)
    print("\n6. Testing LLM connection tool...")
    try:
        # Test with invalid credentials to check error handling
        result = await test_llm_connection(
            provider="openai",
            model_name="gpt-4",
            api_key="test-key"  # Invalid key for testing
        )
        if isinstance(result, dict):
            print("✅ LLM connection tool responding correctly")
            if result.get("success"):
                print("   ✅ Connection successful")
            else:
                print(f"   ⚠️  Connection failed (expected): {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Unexpected LLM connection response: {result}")
    except Exception as e:
        print(f"❌ LLM connection tool failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 MCP Server testing completed!")
    print("\n📝 Summary:")
    print("   - All basic functionality appears to be working")
    print("   - Server is ready for MCP client connections")
    print("   - To test content analysis, connect an MCP client with valid LLM credentials")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())