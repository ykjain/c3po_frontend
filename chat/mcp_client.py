"""
MCP Client Framework
Handles connections to MCP servers and tool calling capabilities.
"""

import asyncio
import json
import subprocess
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import MCP_SERVERS, DEBUG_CHAT

# Set up logging
logging.basicConfig(level=logging.INFO if DEBUG_CHAT else logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an available MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str


class MCPClient:
    """Simplified MCP client for Perplexity search."""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize MCP tools configuration."""
        try:
            # For now, we'll hardcode the Perplexity tools since we know what they are
            # This is a simplified approach that works with the perplexity-ask server
            
            perplexity_tool = MCPTool(
                name="perplexity-ask:perplexity_ask",
                description="Search the web using Perplexity AI to get current information and research. Use this when you need current information, recent papers, or want to verify facts.",
                parameters={
                    "query": {
                        "type": "string", 
                        "description": "The search query to find information about. Be specific and include relevant keywords."
                    }
                },
                server_name="perplexity-ask"
            )
            
            self.tools["perplexity-ask:perplexity_ask"] = perplexity_tool
            self.initialized = True
            
            if DEBUG_CHAT:
                logger.info("MCP client initialized with Perplexity search tool")
                
        except Exception as e:
            logger.error(f"Error initializing MCP client: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool using subprocess communication with MCP server."""
        if DEBUG_CHAT:
            logger.info(f"MCP call_tool: {tool_name} with arguments: {arguments}")
        
        if tool_name not in self.tools:
            available_tools = list(self.tools.keys())
            if DEBUG_CHAT:
                logger.error(f"Tool {tool_name} not found. Available tools: {available_tools}")
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        
        if tool.server_name == "perplexity-ask":
            query = arguments.get("query", "")
            if not query:
                if DEBUG_CHAT:
                    logger.warning(f"Empty query passed to Perplexity. Arguments: {arguments}")
                query = "Please provide a search query"
            return await self.call_perplexity_search(query)
        else:
            raise ValueError(f"Unsupported server: {tool.server_name}")
    
    async def call_perplexity_search(self, query: str) -> Dict[str, Any]:
        """Call Perplexity search using the MCP server."""
        try:
            if DEBUG_CHAT:
                logger.info(f"Searching Perplexity for: '{query}'")
            
            # Find the server config
            server_config = None
            for config in MCP_SERVERS:
                if config['name'] == 'perplexity-ask' and config.get('enabled', False):
                    server_config = config
                    break
            
            if not server_config:
                raise ValueError("Perplexity server not configured or not enabled")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(server_config.get('env', {}))
            
            # Create the MCP request - Perplexity expects messages format
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "perplexity_ask",
                    "arguments": {
                        "messages": [
                            {
                                "role": "user",
                                "content": query
                            }
                        ]
                    }
                }
            }
            
            # Start the MCP server process
            command = [server_config['command']] + server_config['args']
            
            if DEBUG_CHAT:
                logger.info(f"Running command: {' '.join(command)}")
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Send the request
            request_json = json.dumps(request) + '\n'
            stdout, stderr = await process.communicate(request_json.encode())
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"MCP server error: {error_msg}")
            
            # Parse the response
            response_text = stdout.decode().strip()
            if DEBUG_CHAT:
                logger.info(f"MCP server response: {response_text[:500]}...")
            
            # The response might be multiple JSON objects, get the last one
            lines = response_text.strip().split('\n')
            for line in reversed(lines):
                if line.strip():
                    try:
                        response = json.loads(line)
                        if 'result' in response:
                            return {
                                'content': response['result']['content'][0]['text'] if response['result'].get('content') else str(response['result'])
                            }
                    except json.JSONDecodeError:
                        continue
            
            return {'content': response_text}
            
        except Exception as e:
            logger.error(f"Error calling Perplexity search: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools for Claude function calling."""
        tools_list = []
        
        for tool_key, tool in self.tools.items():
            tools_list.append({
                "name": tool_key,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys())
                }
            })
        
        return tools_list
    
    def get_tools_for_claude(self) -> List[Dict[str, Any]]:
        """Format tools for Claude's function calling API."""
        claude_tools = []
        
        if DEBUG_CHAT:
            print(f"Formatting {len(self.tools)} tools for Claude")
        
        for tool_key, tool in self.tools.items():
            claude_tool = {
                "name": tool_key.replace(':', '_'),  # Claude doesn't like colons in function names
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": ["query"]  # Make query required
                }
            }
            claude_tools.append(claude_tool)
            
            if DEBUG_CHAT:
                print(f"Added tool: {claude_tool['name']} - {claude_tool['description']}")
        
        return claude_tools
    
    async def cleanup(self):
        """Clean up MCP connections and processes."""
        # For our simplified implementation, no persistent connections to clean up
        if DEBUG_CHAT:
            logger.info("MCP client cleanup completed")


# Global MCP client instance
mcp_client = MCPClient()
