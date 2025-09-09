/**
 * HCA Lung Atlas Tree - Chat Component
 * Provides Claude-powered chatbot functionality with context awareness.
 */

class ChatBot {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.eventSource = null;
        this.isOpen = false;
        this.isStreaming = false;
        this.currentStreamingMessage = null;
        
        this.init();
    }

    init() {
        this.createChatUI();
        this.bindEvents();
        this.loadHistory();
        this.checkChatStatus();
    }

    getOrCreateSessionId() {
        let sessionId = sessionStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = this.generateUUID();
            sessionStorage.setItem('chat_session_id', sessionId);
        }
        return sessionId;
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    createChatUI() {
        // Create chat toggle button
        const toggleButton = document.createElement('button');
        toggleButton.className = 'chat-toggle';
        toggleButton.innerHTML = '<i class="fas fa-comment"></i>';
        toggleButton.id = 'chat-toggle';
        toggleButton.title = 'Open Chat Assistant';
        document.body.appendChild(toggleButton);

        // Create chat panel
        const chatPanel = document.createElement('div');
        chatPanel.className = 'chat-panel';
        chatPanel.id = 'chat-panel';
        chatPanel.innerHTML = `
            <div class="chat-header">
                <h3><i class="fas fa-robot"></i> Atlas Assistant</h3>
                <button class="chat-close" id="chat-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="chat-status" id="chat-status">
                Connecting...
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="chat-message assistant">
                    <div class="chat-message-bubble">
                        Hello! I'm here to help you explore the HCA Lung Atlas data. I can explain visualizations, interpret gene programs, and answer questions about what you're seeing. What would you like to know?
                    </div>
                </div>
            </div>
            <div class="chat-input-area">
                <div class="chat-input-container">
                    <textarea 
                        class="chat-input" 
                        id="chat-input" 
                        placeholder="Ask me about the data you're exploring..."
                        rows="1"
                    ></textarea>
                    <button class="chat-send" id="chat-send" disabled>
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(chatPanel);
    }

    bindEvents() {
        // Toggle button
        document.getElementById('chat-toggle').addEventListener('click', () => {
            this.togglePanel();
        });

        // Close button
        document.getElementById('chat-close').addEventListener('click', () => {
            this.closePanel();
        });

        // Send button
        document.getElementById('chat-send').addEventListener('click', () => {
            this.sendMessage();
        });

        // Input events
        const input = document.getElementById('chat-input');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        input.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        // Close panel when clicking outside (on mobile)
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('chat-panel');
            const toggle = document.getElementById('chat-toggle');
            
            if (this.isOpen && !panel.contains(e.target) && !toggle.contains(e.target)) {
                if (window.innerWidth <= 768) {
                    this.closePanel();
                }
            }
        });
    }

    togglePanel() {
        if (this.isOpen) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }

    openPanel() {
        const panel = document.getElementById('chat-panel');
        const toggle = document.getElementById('chat-toggle');
        
        panel.classList.add('open');
        toggle.classList.add('active');
        toggle.innerHTML = '<i class="fas fa-times"></i>';
        toggle.title = 'Close Chat';
        
        this.isOpen = true;
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chat-input').focus();
        }, 300);
        
        // Scroll to bottom
        this.scrollToBottom();
    }

    closePanel() {
        const panel = document.getElementById('chat-panel');
        const toggle = document.getElementById('chat-toggle');
        
        panel.classList.remove('open');
        toggle.classList.remove('active');
        toggle.innerHTML = '<i class="fas fa-comment"></i>';
        toggle.title = 'Open Chat Assistant';
        
        this.isOpen = false;
        
        // Close any active event source
        this.closeEventSource();
    }

    autoResizeTextarea() {
        const textarea = document.getElementById('chat-input');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    updateSendButton() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');
        
        sendBtn.disabled = !input.value.trim() || this.isStreaming;
    }

    getCurrentContext() {
        // Get current page context from the main app
        const context = {
            current_node: window.hcaApp?.currentNode || null,
            page_type: 'node_overview', // Default, could be enhanced
            visible_data: []
        };

        // Detect visible elements
        const visibleElements = [];
        
        if (document.querySelector('.program-labels-section')) {
            visibleElements.push('program_labels');
        }
        
        if (document.querySelector('[data-image-title="Program Correlation Heatmap"]')) {
            visibleElements.push('correlation_heatmap');
        }
        
        if (document.querySelector('.cell-type-distribution')) {
            visibleElements.push('cell_type_counts');
        }
        
        if (document.querySelector('.heatmap-grid')) {
            visibleElements.push('summary_heatmaps');
        }

        context.visible_data = visibleElements;

        // Get node info if available
        if (window.hcaApp?.currentNodeInfo) {
            const nodeInfo = window.hcaApp.currentNodeInfo;
            context.node_info = {
                cell_count: nodeInfo.cells?.number,
                gene_count: nodeInfo.genes?.number,
                program_count: nodeInfo.programs_summary?.number_of_programs
            };
        }

        return context;
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isStreaming) return;

        // Clear input
        input.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();

        // Add user message to UI
        this.addMessage('user', message);

        // Show typing indicator
        this.showTyping();

        try {
            // Get current context
            const context = this.getCurrentContext();

            // Send message to backend
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    context: context
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Start streaming response
            this.startStreaming(data.session_id);

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTyping();
            this.showError('Failed to send message. Please try again.');
        }
    }

    startStreaming(sessionId) {
        this.isStreaming = true;
        this.updateSendButton();

        // Close any existing event source
        this.closeEventSource();

        // Create new event source
        this.eventSource = new EventSource(`/api/chat/stream/${sessionId}`);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleStreamEvent(data);
            } catch (error) {
                console.error('Error parsing stream event:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('Stream error:', error);
            this.handleStreamError();
        };
    }

    handleStreamEvent(data) {
        switch (data.type) {
            case 'start':
                this.hideTyping();
                this.currentStreamingMessage = this.addMessage('assistant', '');
                break;
                
            case 'chunk':
                if (this.currentStreamingMessage) {
                    this.appendToMessage(this.currentStreamingMessage, data.content);
                }
                break;
                
            case 'end':
                this.finishStreaming();
                break;
                
            case 'error':
                this.hideTyping();
                this.showError(data.error);
                this.finishStreaming();
                break;
        }
    }

    handleStreamError() {
        this.hideTyping();
        this.showError('Connection lost. Please try again.');
        this.finishStreaming();
    }

    finishStreaming() {
        this.isStreaming = false;
        this.currentStreamingMessage = null;
        this.updateSendButton();
        this.closeEventSource();
        this.scrollToBottom();
    }

    closeEventSource() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'chat-message-bubble';
        bubble.innerHTML = this.renderMarkdown(content);
        
        const time = document.createElement('div');
        time.className = 'chat-message-time';
        time.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(time);
        messagesContainer.appendChild(messageDiv);
        
        this.scrollToBottom();
        
        return bubble; // Return bubble for streaming updates
    }

    appendToMessage(bubble, content) {
        // For streaming, we need to accumulate text content and re-render
        const currentText = bubble.getAttribute('data-raw-content') || '';
        const newText = currentText + content;
        bubble.setAttribute('data-raw-content', newText);
        bubble.innerHTML = this.renderMarkdown(newText);
        this.scrollToBottom();
    }

    showTyping() {
        const messagesContainer = document.getElementById('chat-messages');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-typing';
        typingDiv.id = 'chat-typing-indicator';
        typingDiv.innerHTML = `
            <div class="chat-typing-dots">
                <div class="chat-typing-dot"></div>
                <div class="chat-typing-dot"></div>
                <div class="chat-typing-dot"></div>
            </div>
            <span class="chat-typing-text">Assistant is thinking...</span>
        `;
        
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTyping() {
        const typingIndicator = document.getElementById('chat-typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    showError(message) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-error';
        errorDiv.innerHTML = `
            ${message}
            <button class="chat-error-retry" onclick="chatBot.retryLastMessage()">
                Retry
            </button>
        `;
        
        messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }

    retryLastMessage() {
        // Remove error message
        const errors = document.querySelectorAll('.chat-error');
        errors.forEach(error => error.remove());
        
        // Get last user message and resend
        const messages = document.querySelectorAll('.chat-message.user');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const messageText = lastMessage.querySelector('.chat-message-bubble').textContent;
            
            // Set input and send
            document.getElementById('chat-input').value = messageText;
            this.sendMessage();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }

    async loadHistory() {
        try {
            const response = await fetch(`/api/chat/history/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                this.displayHistory(data.messages);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    displayHistory(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Clear existing messages except welcome message
        const existingMessages = messagesContainer.querySelectorAll('.chat-message:not(:first-child)');
        existingMessages.forEach(msg => msg.remove());
        
        // Add historical messages
        messages.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'assistant') {
                this.addMessage(msg.role, msg.content);
            }
        });
    }

    async checkChatStatus() {
        try {
            const response = await fetch('/api/chat/status');
            const status = await response.json();
            this.updateStatus(status);
        } catch (error) {
            console.error('Error checking chat status:', error);
            this.updateStatus({ enabled: false, claude_available: false });
        }
    }

    updateStatus(status) {
        const statusDiv = document.getElementById('chat-status');
        const sendBtn = document.getElementById('chat-send');
        const input = document.getElementById('chat-input');
        
        if (status.enabled && status.claude_available) {
            statusDiv.textContent = 'Connected';
            statusDiv.className = 'chat-status';
            input.disabled = false;
            input.placeholder = 'Ask me about the data you\'re exploring...';
        } else {
            statusDiv.textContent = 'Chat service unavailable';
            statusDiv.className = 'chat-status offline';
            input.disabled = true;
            input.placeholder = 'Chat service is currently unavailable';
            sendBtn.disabled = true;
        }
        
        this.updateSendButton();
    }

    renderMarkdown(text) {
        if (!text) return '';
        
        // Escape HTML to prevent XSS
        text = text.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;');
        
        // Convert **bold** text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* text
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Convert bullet points
        text = text.replace(/^[\s]*[-•]\s+(.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Convert numbered lists
        text = text.replace(/^[\s]*\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // First, temporarily mark existing links to protect them
        const linkPlaceholder = '___LINK_PLACEHOLDER___';
        const linkMap = [];
        
        // Convert links [text](url) format FIRST
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
            const placeholder = `${linkPlaceholder}${linkMap.length}${linkPlaceholder}`;
            linkMap.push(`<a href="${url}" target="_blank" rel="noopener">${text}</a>`);
            return placeholder;
        });
        
        // Convert plain URLs (but avoid double-converting)
        text = text.replace(/(^|[^"'>])(https?:\/\/[^\s<>"]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
        
        // Convert citations [1], [2], etc.
        text = text.replace(/\[(\d+)\]/g, '<sup class="citation">[$1]</sup>');
        
        // Restore the protected links
        linkMap.forEach((link, index) => {
            text = text.replace(`${linkPlaceholder}${index}${linkPlaceholder}`, link);
        });
        
        return text;
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Make sure chat CSS is loaded
    if (!document.querySelector('link[href*="chat.css"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/css/chat.css';
        document.head.appendChild(link);
    }
    
    // Initialize chat bot
    window.chatBot = new ChatBot();
});
