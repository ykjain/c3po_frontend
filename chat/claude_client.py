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


class ClaudeClient:
    """Client for interacting with Claude API."""
    
    def __init__(self):
        if not Anthropic:
            raise ImportError("anthropic package is required")
        
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
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
        """Stream a response from Claude."""
        
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
        
        if DEBUG_CHAT:
            print(f"Sending to Claude: {len(messages)} messages")
            print(f"Last message: {user_message[:200]}...")
        
        try:
            # Create streaming response
            with self.client.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=messages
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield text
                
                if DEBUG_CHAT:
                    print(f"Claude response length: {len(full_response)}")
        
        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            if DEBUG_CHAT:
                print(error_msg)
            yield f"I apologize, but I encountered an error: {error_msg}"
    
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
