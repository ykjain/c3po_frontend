"""
FastMCP Client Framework
Handles connections to FastMCP servers using the official FastMCP client library.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import MCP_SERVERS, DEBUG_CHAT

# Set up logging
logging.basicConfig(level=logging.INFO if DEBUG_CHAT else logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class FastMCPTool:
    """Represents an available FastMCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str


class FastMCPClient:
    """Client for FastMCP servers using the official FastMCP client library."""
    
    def __init__(self):
        self.tools: Dict[str, FastMCPTool] = {}
        self.clients: Dict[str, Any] = {}  # Will hold FastMCP Client instances
        self.initialized = False
        
    async def initialize(self):
        """Initialize FastMCP tools and clients."""
        try:
            # Import FastMCP client here to avoid import errors if not installed
            from fastmcp import Client as FastMCPClient
            
            # Initialize all FinnGen tools
            finngen_tools = [
                FastMCPTool(
                    name="finngen:query_credible_sets",
                    description="Query the FinnGen Credible Sets API for genetic association data. Can search by gene name, phenotype, or genomic region to find genetic variants and their disease associations.",
                    parameters={
                        "query": {
                            "type": "string",
                            "description": "Gene name (e.g., 'IL7', 'ACTA2') or search query for genetic associations."
                        }
                    },
                    server_name="finngen"
                ),
                FastMCPTool(
                    name="finngen:get_api_info",
                    description="Get information about the FinnGen Credible Sets API endpoints and usage documentation.",
                    parameters={
                        "query": {
                            "type": "string", 
                            "description": "Optional query for specific API information (can be empty)."
                        }
                    },
                    server_name="finngen"
                ),
                FastMCPTool(
                    name="finngen:health_check",
                    description="Check if the FinnGen Credible Sets API is accessible and working properly.",
                    parameters={
                        "query": {
                            "type": "string",
                            "description": "Optional query for health check (can be empty)."
                        }
                    },
                    server_name="finngen"
                ),
                FastMCPTool(
                    name="finngen:identify_phenotype_ids",
                    description="Identify phenotype IDs in the FinnGen database for any biological concept using RAG. Use this to find relevant phenotypes based on genes, functions, processes, or disease mechanisms.",
                    parameters={
                        "query": {
                            "type": "string",
                            "description": "Biological concept description (e.g., 'cholesterol metabolism', 'inflammation', 'PCSK9', 'diabetes')."
                        }
                    },
                    server_name="finngen"
                ),
                FastMCPTool(
                    name="finngen:search_phenotypes_by_description",
                    description="Search for phenotypes in the FinnGen database using natural language descriptions of medical conditions, symptoms, or biological processes.",
                    parameters={
                        "query": {
                            "type": "string",
                            "description": "Natural language description of phenotype, condition, or symptom (e.g., 'diabetes and blood sugar', 'heart disease')."
                        }
                    },
                    server_name="finngen"
                )
            ]
            
            # Register all tools
            for tool in finngen_tools:
                self.tools[tool.name] = tool
            
            # Initialize FastMCP clients for each server
            for server_config in MCP_SERVERS:
                if server_config.get('transport') == 'http' and server_config.get('enabled', False):
                    server_name = server_config['name']
                    server_url = server_config['url']
                    
                    # Create FastMCP client instance
                    client = FastMCPClient(server_url)
                    self.clients[server_name] = client
                    
                    if DEBUG_CHAT:
                        logger.info(f"Initialized FastMCP client for {server_name}: {server_url}")
            
            self.initialized = True
            
            if DEBUG_CHAT:
                logger.info("FastMCP client initialized successfully")
                
        except ImportError:
            logger.error("FastMCP library not installed. Run: uv add fastmcp")
            raise
        except Exception as e:
            logger.error(f"Error initializing FastMCP client: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool using the appropriate FastMCP client."""
        if DEBUG_CHAT:
            logger.info(f"FastMCP call_tool: {tool_name} with arguments: {arguments}")
        
        if tool_name not in self.tools:
            available_tools = list(self.tools.keys())
            if DEBUG_CHAT:
                logger.error(f"Tool {tool_name} not found. Available tools: {available_tools}")
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        
        if tool.server_name == "finngen":
            query = arguments.get("query", "")
            
            # Route to appropriate FinnGen tool based on tool name
            if tool_name == "finngen:query_credible_sets":
                if not query:
                    if DEBUG_CHAT:
                        logger.warning(f"Empty query passed to FinnGen query_credible_sets. Arguments: {arguments}")
                    query = "Please provide a gene name or search query"
                return await self.call_finngen_search(query)
            elif tool_name == "finngen:get_api_info":
                return await self.call_finngen_tool("get_api_info", {})
            elif tool_name == "finngen:health_check":
                return await self.call_finngen_tool("health_check", {})
            elif tool_name == "finngen:identify_phenotype_ids":
                if not query:
                    query = "Please provide a biological concept"
                return await self.call_finngen_tool("identify_phenotype_ids", {"biological_concept": query})
            elif tool_name == "finngen:search_phenotypes_by_description":
                if not query:
                    query = "Please provide a phenotype description"
                return await self.call_finngen_tool("search_phenotypes_by_description", {"description": query})
            else:
                raise ValueError(f"Unknown FinnGen tool: {tool_name}")
        else:
            raise ValueError(f"Unsupported FastMCP server: {tool.server_name}")
    
    async def call_finngen_search(self, query: str) -> Dict[str, Any]:
        """Call FinnGen search using the official FastMCP client."""
        try:
            if DEBUG_CHAT:
                logger.info(f"Searching FinnGen for: '{query}'")
            
            # Get the FinnGen client
            if 'finngen' not in self.clients:
                raise ValueError("FinnGen client not initialized")
            
            client = self.clients['finngen']
            
            # Extract gene name from query if it looks like a gene query
            gene_match = re.search(r'\b([A-Z][A-Z0-9]+)\b', query)
            if gene_match:
                identifier = gene_match.group(1)
                query_type = "gene"
            else:
                # For non-gene queries, use the whole query as identifier
                identifier = query.strip()
                query_type = "gene"  # Default to gene for now
            
            if DEBUG_CHAT:
                logger.info(f"Calling FinnGen with query_type='{query_type}', identifier='{identifier}'")
            
            # Use the official FastMCP client
            async with client:
                result = await client.call_tool("query_credible_sets", {
                    "query_type": query_type,
                    "identifier": identifier,
                    "format_output": "summary",
                    "max_results": 50
                })
                
                if DEBUG_CHAT:
                    logger.info(f"FinnGen result: {str(result)[:500]}...")
                
                # Extract the result data
                if hasattr(result, 'data'):
                    return {'content': str(result.data)}
                else:
                    return {'content': str(result)}
            
        except Exception as e:
            logger.error(f"Error calling FinnGen search: {e}")
            raise
    
    async def call_finngen_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call any FinnGen tool using the official FastMCP client."""
        try:
            if DEBUG_CHAT:
                logger.info(f"Calling FinnGen tool '{tool_name}' with arguments: {arguments}")
            
            # Get the FinnGen client
            if 'finngen' not in self.clients:
                raise ValueError("FinnGen client not initialized")
            
            client = self.clients['finngen']
            
            if DEBUG_CHAT:
                logger.info(f"Calling FinnGen tool: {tool_name}")
            
            # Use the official FastMCP client
            async with client:
                result = await client.call_tool(tool_name, arguments)
                
                if DEBUG_CHAT:
                    logger.info(f"FinnGen {tool_name} result: {str(result)[:500]}...")
                
                # Extract the result data
                if hasattr(result, 'data'):
                    return {'content': str(result.data)}
                else:
                    return {'content': str(result)}
            
        except Exception as e:
            logger.error(f"Error calling FinnGen tool {tool_name}: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available FastMCP tools for Claude function calling."""
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
            print(f"Formatting {len(self.tools)} FastMCP tools for Claude")
        
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
                print(f"Added FastMCP tool: {claude_tool['name']} - {claude_tool['description']}")
        
        return claude_tools
    
    async def cleanup(self):
        """Clean up FastMCP connections."""
        if DEBUG_CHAT:
            logger.info("FastMCP client cleanup completed")


# Global FastMCP client instance
fastmcp_client = FastMCPClient()
