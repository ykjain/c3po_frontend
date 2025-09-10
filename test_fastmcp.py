#!/usr/bin/env python3
"""
Test script for FastMCP integration
"""

import asyncio
import sys
import os

# Add the chat module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'chat'))

from chat.fastmcp_client import fastmcp_client
from chat.config import DEBUG_CHAT

async def test_finngen_integration():
    """Test the FinnGen FastMCP integration."""
    print("🧬 Testing FinnGen FastMCP Integration")
    print("=" * 50)
    
    try:
        # Initialize the client
        print("1. Initializing FastMCP client...")
        await fastmcp_client.initialize()
        print("✅ FastMCP client initialized successfully")
        
        # Get available tools
        print("\n2. Getting available tools...")
        tools = fastmcp_client.get_tools_for_claude()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:60]}...")
        
        # Test a simple gene query
        print("\n3. Testing gene query for IL7...")
        result = await fastmcp_client.call_tool("finngen:query_credible_sets", {"query": "IL7"})
        
        print("✅ FinnGen query successful!")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and 'content' in result:
            content = str(result['content'])
            print(f"Content length: {len(content)} characters")
            print(f"Content preview: {content[:200]}...")
        else:
            print(f"Raw result: {str(result)[:200]}...")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if DEBUG_CHAT:
            import traceback
            traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_finngen_integration())
    sys.exit(0 if success else 1)
