"""
Server-Sent Events (SSE) Streaming Utilities
Handles real-time streaming of chat responses to the frontend.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from flask import Response
import time

from .config import DEBUG_CHAT


def create_sse_response(data: Dict[str, Any]) -> str:
    """Create a properly formatted SSE message."""
    return f"data: {json.dumps(data)}\n\n"


def stream_chat_response(
    session_id: str,
    message: str,
    context: Optional[Dict] = None
) -> Response:
    """Create a Flask Response that streams Claude's response via SSE."""
    
    def generate():
        from .claude_client import claude_client
        from .session_manager import session_manager
        
        if not claude_client:
            yield create_sse_response({
                "type": "error",
                "error": "Chat service is not available. Please check configuration."
            })
            return
        
        try:
            # Send start event
            yield create_sse_response({
                "type": "start",
                "session_id": session_id
            })
            
            # Get conversation history
            history = session_manager.get_conversation_history(session_id)
            
            if DEBUG_CHAT:
                print(f"Streaming response for session {session_id}")
                print(f"History length: {len(history)}")
            
            # Stream the response
            full_response = ""
            
            # Create async event loop for streaming
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                async def stream_async():
                    nonlocal full_response
                    async for chunk in claude_client.stream_response(message, history, context):
                        full_response += chunk
                        yield create_sse_response({
                            "type": "chunk",
                            "content": chunk
                        })
                
                # Run async streaming
                async_gen = stream_async()
                while True:
                    try:
                        chunk_response = loop.run_until_complete(async_gen.__anext__())
                        yield chunk_response
                    except StopAsyncIteration:
                        break
                
            finally:
                loop.close()
            
            # Add the complete response to session history
            session_manager.add_message(session_id, 'assistant', full_response, context)
            
            # Send end event
            yield create_sse_response({
                "type": "end",
                "message_id": f"msg_{int(time.time())}"
            })
            
            if DEBUG_CHAT:
                print(f"Completed streaming for session {session_id}")
        
        except Exception as e:
            error_msg = str(e)
            if DEBUG_CHAT:
                print(f"Streaming error: {error_msg}")
            
            yield create_sse_response({
                "type": "error", 
                "error": f"An error occurred while processing your message: {error_msg}"
            })
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )


def create_error_sse_response(error_message: str) -> Response:
    """Create an SSE response for errors."""
    def generate():
        yield create_sse_response({
            "type": "error",
            "error": error_message
        })
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )
