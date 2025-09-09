# HCA Lung Atlas Tree - Chatbot Design Document

## Overview

This document outlines the design and implementation plan for integrating a Claude 3.5 Sonnet-powered chatbot into the HCA Lung Atlas Tree web application. The chatbot will provide context-aware assistance for exploring and understanding the lung atlas data.

## Requirements

- **Backend**: Claude 3.5 Sonnet integration with streaming responses
- **Frontend**: Sliding chat panel from the right side
- **Configuration**: Backend-controlled system prompt and MCP server configuration
- **Sessions**: Persistent conversation history per session
- **Context**: Awareness of current node, program, and displayed data
- **MCP Ready**: Framework prepared for future MCP server integration
- **Authentication**: None required (open access)

## Architecture

### Backend Structure

```
chat/
├── __init__.py              # Chat module initialization
├── api.py                   # Flask routes and endpoints
├── claude_client.py         # Claude API integration and streaming
├── session_manager.py       # Conversation history management
├── config.py                # System prompt and MCP configuration
└── streaming.py             # Server-Sent Events utilities
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/message` | POST | Send message and initiate streaming response |
| `/api/chat/stream/{session_id}` | GET | SSE endpoint for streaming responses |

### Configuration System

**File**: `chat/config.py`

```python
# System Prompt (Backend controlled only)
SYSTEM_PROMPT = """
You are an AI assistant specialized in helping researchers explore and understand 
lung atlas data. You have access to cellular programs, gene expression data, 
UMAP visualizations, and cell type distributions.
"""

# Claude Configuration
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 4096
TEMPERATURE = 0.7
STREAM_CHUNK_SIZE = 1024

# MCP Server Configuration (Future use)
MCP_SERVERS = [
    {
        "name": "data_analysis",
        "endpoint": "http://localhost:8001",
        "enabled": False,
        "description": "Data analysis and statistical tools"
    },
    {
        "name": "gene_search",
        "endpoint": "http://localhost:8002", 
        "enabled": False,
        "description": "Gene database search and annotation"
    }
]

# Session Management
SESSION_TIMEOUT_HOURS = 1
MAX_HISTORY_LENGTH = 50
CLEANUP_INTERVAL_MINUTES = 15
```

## Session Management

### Session Lifecycle

1. **Creation**: Client generates UUID4 session ID on first chat interaction
2. **Storage**: Session ID stored in browser's sessionStorage
3. **History**: Backend maintains conversation history in memory
4. **Context**: Each message includes current page context
5. **Cleanup**: Automatic cleanup after 1 hour of inactivity

### Session Data Structure

```python
{
    "session_id": "uuid4-string",
    "created_at": "timestamp",
    "last_activity": "timestamp", 
    "messages": [
        {
            "role": "user|assistant",
            "content": "message text",
            "context": {...},
            "timestamp": "timestamp"
        }
    ]
}
```

### Context Information

```python
context = {
    "current_node": "root_cluster_L1C02",
    "current_program": "program_15",  # if viewing program
    "page_type": "node_overview|program_detail|tree_navigation",
    "visible_data": [
        "program_labels",
        "correlation_heatmap", 
        "cell_type_counts",
        "summary_heatmaps"
    ],
    "node_info": {
        "cell_count": 38334,
        "gene_count": 17840,
        "program_count": 48
    }
}
```

## Frontend Implementation

### UI Components

**Chat Toggle Button**
- Location: Main application header
- Icon: Chat bubble or message icon
- Behavior: Toggles chat panel visibility

**Chat Panel**
- Position: Fixed, slides from right edge
- Width: 400px (desktop), 100% (mobile)
- Animation: Smooth CSS transition (0.3s ease)
- Z-index: High value to overlay content

**Chat Interface**
- Message history: Scrollable container
- Input area: Text input + send button
- Streaming indicator: Typing animation during responses
- Error handling: Retry mechanisms for failed messages

### File Structure

```
static/
├── js/
│   └── chat.js              # Chat UI component and logic
└── css/
    └── chat.css             # Chat panel styling and animations

templates/
└── index.html               # Modified to include chat toggle button
```

### JavaScript Architecture

```javascript
class ChatBot {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.eventSource = null;
        this.isOpen = false;
    }
    
    // Core methods
    togglePanel()           // Show/hide chat panel
    sendMessage(message)    // Send user message
    streamResponse()        // Handle SSE streaming
    addMessage()           // Add message to UI
    getCurrentContext()    // Get page context
    
    // Session management
    getOrCreateSessionId() // Generate or retrieve session ID
    loadHistory()          // Load conversation history
    
    // UI methods
    renderMessage()        // Render individual message
    showTyping()          // Show typing indicator
    handleError()         // Error handling and retry
}
```

## Streaming Implementation

### Server-Sent Events (SSE)

**Advantages**:
- Reliable streaming over HTTP
- Automatic reconnection
- Works through firewalls/proxies
- Simple implementation

**Flow**:
1. Client sends POST to `/api/chat/message`
2. Server responds with session_id and starts streaming
3. Client connects to `/api/chat/stream/{session_id}` 
4. Server streams Claude response chunks
5. Client renders text progressively

### Streaming Protocol

```
data: {"type": "start", "session_id": "uuid"}
data: {"type": "chunk", "content": "Hello"}
data: {"type": "chunk", "content": " there!"}
data: {"type": "end", "message_id": "msg_uuid"}
data: {"type": "error", "error": "error message"}
```

## Error Handling

### Backend Error Scenarios
- Claude API failures
- Rate limiting
- Network timeouts
- Invalid session IDs
- Context parsing errors

### Frontend Error Handling
- Connection failures
- SSE disconnections
- Message send failures
- Automatic retry with exponential backoff
- User-friendly error messages

## Security Considerations

### Rate Limiting
- Per-session message limits
- Time-based throttling
- Claude API quota management

### Input Validation
- Message length limits
- Content filtering
- Context data validation
- SQL injection prevention

### Session Security
- Session ID validation
- Memory cleanup
- No persistent storage of conversations

## Performance Optimization

### Backend
- Connection pooling for Claude API
- Async request handling
- Memory-efficient session storage
- Periodic cleanup routines

### Frontend
- Debounced input handling
- Virtual scrolling for long histories
- Lazy loading of chat history
- Efficient DOM updates

## Future Enhancements

### MCP Integration
- Tool discovery and registration
- Dynamic function calling
- Multi-server orchestration
- Error handling and fallbacks

### Advanced Features
- Message search within history
- Export conversation functionality
- Conversation branching
- Multi-language support

## Implementation Phases

### Phase 1: Core Chat (Week 1)
- [ ] Basic Claude integration
- [ ] SSE streaming setup
- [ ] Session management
- [ ] Basic UI components

### Phase 2: Context Integration (Week 2)
- [ ] Page context detection
- [ ] Context-aware responses
- [ ] Data reference capabilities
- [ ] Enhanced system prompts

### Phase 3: MCP Preparation (Week 3)
- [ ] MCP client framework
- [ ] Configuration management
- [ ] Tool calling infrastructure
- [ ] Testing and documentation

## Dependencies

### Backend
```
anthropic>=0.28.0           # Claude API client
flask-sse>=1.0              # Server-Sent Events support
```

### Frontend
- Native EventSource API
- CSS Grid/Flexbox for layout
- No additional JavaScript libraries required

## Testing Strategy

### Backend Testing
- Unit tests for Claude integration
- Session management tests
- SSE streaming tests
- Error handling validation

### Frontend Testing
- UI component testing
- SSE connection testing
- Error scenario testing
- Cross-browser compatibility

### Integration Testing
- End-to-end conversation flow
- Context passing validation
- Performance under load
- Memory leak detection

## Deployment Considerations

### Environment Variables
```bash
ANTHROPIC_API_KEY=your_claude_api_key
CHAT_ENABLED=true
SESSION_TIMEOUT_HOURS=1
```

### Monitoring
- Claude API usage tracking
- Session count monitoring
- Error rate tracking
- Response time metrics

---

**Document Version**: 1.0  
**Created**: 2024  
**Last Updated**: 2024  
**Author**: AI Assistant  
**Status**: Design Phase
