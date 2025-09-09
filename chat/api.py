"""
Chat API Routes
Flask routes for chat functionality including message sending and streaming.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any

from .config import CHAT_ENABLED, DEBUG_CHAT
from .session_manager import session_manager
from .streaming import stream_chat_response, create_error_sse_response

# Create blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Send a message and initiate streaming response."""
    
    if not CHAT_ENABLED:
        return jsonify({'error': 'Chat service is disabled'}), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', '').strip()
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(message) > 10000:  # Reasonable limit
            return jsonify({'error': 'Message too long'}), 400
        
        # Create or validate session
        if not session_id:
            session_id = session_manager.create_session()
        else:
            session_manager.create_session(session_id)  # Creates if doesn't exist
        
        # Add user message to history
        session_manager.add_message(session_id, 'user', message, context)
        
        if DEBUG_CHAT:
            print(f"Received message for session {session_id}: {message[:100]}...")
            print(f"Context: {context}")
        
        # Return session ID for streaming connection
        return jsonify({
            'session_id': session_id,
            'stream_url': f'/api/chat/stream/{session_id}'
        })
    
    except Exception as e:
        if DEBUG_CHAT:
            print(f"Error in send_message: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_bp.route('/stream/<session_id>')
def stream_response(session_id: str):
    """SSE endpoint for streaming chat responses."""
    
    if not CHAT_ENABLED:
        return create_error_sse_response('Chat service is disabled')
    
    if not session_id:
        return create_error_sse_response('Session ID is required')
    
    if not session_manager.session_exists(session_id):
        return create_error_sse_response('Invalid session ID')
    
    try:
        # Get the last user message and its context
        messages = session_manager.get_messages(session_id)
        if not messages:
            return create_error_sse_response('No messages found in session')
        
        # Find the last user message
        last_user_message = None
        last_context = None
        
        for msg in reversed(messages):
            if msg['role'] == 'user':
                last_user_message = msg['content']
                last_context = msg.get('context')
                break
        
        if not last_user_message:
            return create_error_sse_response('No user message found')
        
        # Update session activity
        session_manager.update_activity(session_id)
        
        if DEBUG_CHAT:
            print(f"Starting stream for session {session_id}")
        
        # Return streaming response
        return stream_chat_response(session_id, last_user_message, last_context)
    
    except Exception as e:
        if DEBUG_CHAT:
            print(f"Error in stream_response: {e}")
        return create_error_sse_response('Internal server error')


@chat_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """Get conversation history for a session."""
    
    if not CHAT_ENABLED:
        return jsonify({'error': 'Chat service is disabled'}), 503
    
    if not session_id:
        return jsonify({'error': 'Session ID is required'}), 400
    
    if not session_manager.session_exists(session_id):
        return jsonify({'messages': []})
    
    try:
        messages = session_manager.get_messages(session_id)
        
        # Format messages for frontend (remove internal context)
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp']
            })
        
        return jsonify({'messages': formatted_messages})
    
    except Exception as e:
        if DEBUG_CHAT:
            print(f"Error in get_history: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_bp.route('/status')
def chat_status():
    """Get chat service status."""
    
    from .claude_client import claude_client
    
    status = {
        'enabled': CHAT_ENABLED,
        'claude_available': claude_client is not None,
        'active_sessions': session_manager.get_session_count()
    }
    
    return jsonify(status)
