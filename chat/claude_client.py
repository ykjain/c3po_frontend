"""
Claude API Client
Handles communication with Anthropic's Claude API including streaming responses.
"""

import asyncio
from typing import Dict, List, Optional, AsyncGenerator
import json

try:
    from anthropic import Anthropic
    import anthropic
except ImportError:
    print("Warning: anthropic package not installed. Install with: uv add anthropic")
    Anthropic = None

from .config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    SYSTEM_PROMPT,
    DEBUG_CHAT
)
from .mcp_client import mcp_client


class ClaudeClient:
    """Client for interacting with Claude API."""
    
    def __init__(self):
        if not Anthropic:
            raise ImportError("anthropic package is required")
        
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.mcp_initialized = False
    
    async def ensure_mcp_initialized(self):
        """Ensure MCP client is initialized."""
        if not self.mcp_initialized:
            try:
                await mcp_client.initialize()
                self.mcp_initialized = True
                if DEBUG_CHAT:
                    print("MCP client initialized successfully")
            except Exception as e:
                if DEBUG_CHAT:
                    print(f"MCP initialization failed: {e}")
                # Continue without MCP if it fails
    
    def format_context_for_prompt(self, context: Dict) -> str:
        """Format page context into a readable prompt addition."""
        if not context:
            return ""
        
        context_parts = []
        
        # Current location
        if context.get('current_node'):
            context_parts.append(f"Current node: {context['current_node']}")
        
        if context.get('current_program'):
            context_parts.append(f"Current program: {context['current_program']}")
        
        # Page type
        if context.get('page_type'):
            context_parts.append(f"Page type: {context['page_type']}")
        
        # Node info
        if context.get('node_info'):
            info = context['node_info']
            info_parts = []
            if info.get('cell_count'):
                info_parts.append(f"{info['cell_count']:,} cells")
            if info.get('gene_count'):
                info_parts.append(f"{info['gene_count']:,} genes")
            if info.get('program_count'):
                info_parts.append(f"{info['program_count']} programs")
            
            if info_parts:
                context_parts.append(f"Node contains: {', '.join(info_parts)}")
        
        # Visible data
        if context.get('visible_data'):
            visible = ', '.join(context['visible_data'])
            context_parts.append(f"Currently visible: {visible}")
        
        if context_parts:
            return f"\n\nCurrent context: {' | '.join(context_parts)}"
        
        return ""
    
    async def stream_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a response from Claude with MCP tool support."""
        
        # Ensure MCP is initialized
        await self.ensure_mcp_initialized()
        
        # Build messages for the API
        messages = conversation_history.copy()
        
        # Add context to the user message if provided
        user_message = message
        if context:
            context_info = self.format_context_for_prompt(context)
            if context_info:
                user_message += context_info
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # Get available MCP tools
        tools = mcp_client.get_tools_for_claude() if self.mcp_initialized else []
        
        if DEBUG_CHAT:
            print(f"Sending to Claude: {len(messages)} messages")
            print(f"Available tools: {len(tools)}")
            if tools:
                print(f"Tools: {[tool['name'] for tool in tools]}")
                print(f"First tool details: {tools[0] if tools else 'None'}")
            print(f"Last message: {user_message[:200]}...")
        
        try:
            # Create message with tools if available
            message_params = {
                "model": CLAUDE_MODEL,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": SYSTEM_PROMPT,
                "messages": messages
            }
            
            if tools:
                message_params["tools"] = tools
            
            # Create streaming response
            with self.client.messages.stream(**message_params) as stream:
                full_response = ""
                
                if DEBUG_CHAT:
                    print("Starting stream processing...")
                
                # Track tool use state
                current_tool_block = None
                tool_input_json = ""
                
                for event in stream:
                    if DEBUG_CHAT:
                        print(f"Stream event: {type(event).__name__} - {getattr(event, 'type', 'no type')}")
                        if hasattr(event, 'delta') and hasattr(event.delta, 'partial_json'):
                            print(f"  Partial JSON: {event.delta.partial_json}")
                    
                    if hasattr(event, 'type'):
                        if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
                            text = event.delta.text
                            full_response += text
                            yield text
                        elif event.type == "content_block_delta" and hasattr(event.delta, 'partial_json'):
                            # Accumulate tool input JSON
                            if current_tool_block:
                                tool_input_json += event.delta.partial_json
                                if DEBUG_CHAT:
                                    print(f"Accumulating tool input: {tool_input_json}")
                        elif event.type == "content_block_start" and hasattr(event.content_block, 'type'):
                            if event.content_block.type == "tool_use":
                                current_tool_block = event.content_block
                                tool_input_json = ""
                                if DEBUG_CHAT:
                                    print(f"Tool use detected: {event.content_block.name}")
                        elif event.type == "content_block_stop" and current_tool_block:
                            # Tool use is complete, process it
                            if DEBUG_CHAT:
                                print(f"Tool input complete: {tool_input_json}")
                            
                            # Parse the accumulated JSON input
                            try:
                                import json as json_module
                                tool_input = json_module.loads(tool_input_json) if tool_input_json else {}
                            except:
                                tool_input = {}
                            
                            # Create a complete tool block with input
                            current_tool_block.input = tool_input
                            
                            # Handle tool use
                            tool_result = await self.handle_tool_use(current_tool_block)
                            if tool_result:
                                yield f"\n\n[Using {current_tool_block.name}...]\n\n"
                                yield tool_result
                            
                            current_tool_block = None
                            tool_input_json = ""
                
                if DEBUG_CHAT:
                    print(f"Claude response length: {len(full_response)}")
                    print("Stream processing completed")
        
        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            if DEBUG_CHAT:
                print(error_msg)
            yield f"I apologize, but I encountered an error: {error_msg}"
    
    async def handle_tool_use(self, tool_use_block) -> Optional[str]:
        """Handle tool use requests from Claude."""
        try:
            tool_name = tool_use_block.name
            arguments = tool_use_block.input
            
            if DEBUG_CHAT:
                print(f"Claude wants to use tool: {tool_name} with args: {arguments}")
            
            # Convert Claude tool name back to MCP format
            # Claude tool name: perplexity-ask_perplexity_ask
            # MCP tool name: perplexity-ask:perplexity_ask
            mcp_tool_name = tool_name.replace('_', ':', 1)  # Only replace first underscore
            
            # Call the MCP tool
            result = await mcp_client.call_tool(mcp_tool_name, arguments)
            
            # Format the result for display
            if isinstance(result, dict):
                if 'content' in result:
                    content = str(result['content'])
                    return self.format_markdown_response(content)
                else:
                    return json.dumps(result, indent=2)
            else:
                return self.format_markdown_response(str(result))
                
        except Exception as e:
            error_msg = f"Error using tool {tool_use_block.name}: {str(e)}"
            if DEBUG_CHAT:
                print(error_msg)
            return f"Tool error: {error_msg}"
    
    def format_markdown_response(self, content: str) -> str:
        """Format markdown content for better readability in chat."""
        import re
        
        # Convert **bold** to actual bold formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'**\1**', content)
        
        # Improve citation formatting - make them more readable
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        
        # Add line breaks before bullet points for better formatting
        content = re.sub(r'(?<!\n)\n- ', r'\n\n- ', content)
        content = re.sub(r'(?<!\n)\n• ', r'\n\n• ', content)
        
        # Add spacing around section headers
        content = re.sub(r'\n([A-Z][^:\n]*:)\n', r'\n\n**\1**\n\n', content)
        
        # Format URLs to be more readable
        content = re.sub(r'(https?://[^\s\]]+)', r'[\1](\1)', content)
        
        # Clean up multiple consecutive newlines
        content = re.sub(r'\n{3,}', r'\n\n', content)
        
        return content.strip()
    
    def get_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[Dict] = None
    ) -> str:
        """Get a complete response from Claude (non-streaming)."""
        
        # Build messages for the API
        messages = conversation_history.copy()
        
        # Add context to the user message if provided
        user_message = message
        if context:
            context_info = self.format_context_for_prompt(context)
            if context_info:
                user_message += context_info
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=messages
            )
            
            return response.content[0].text
        
        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            if DEBUG_CHAT:
                print(error_msg)
            return f"I apologize, but I encountered an error: {error_msg}"


# Global Claude client instance
claude_client = ClaudeClient() if Anthropic and ANTHROPIC_API_KEY else None
