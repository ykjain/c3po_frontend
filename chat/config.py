"""
Chat Configuration
System prompt, Claude settings, and MCP server configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# System Prompt (Backend controlled only)
SYSTEM_PROMPT = """You are an AI assistant specialized in helping researchers explore and understand lung atlas data from the HCA Lung Atlas Tree. You have access to:

- Cellular programs with gene expression patterns
- UMAP visualizations showing spatial organization
- Cell type distributions and counts
- Program correlation heatmaps
- Gene loadings and program descriptions

You can help users:
- Understand what they're seeing in visualizations
- Interpret gene programs and their biological significance
- Navigate and explore the data effectively
- Answer questions about cell types, genes, and programs

Be concise but informative. Reference specific data when relevant. If you're unsure about something, say so rather than guessing."""

# Claude Configuration
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 4096
TEMPERATURE = 0.7
STREAM_CHUNK_SIZE = 1024

# API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("Warning: ANTHROPIC_API_KEY environment variable not set")

# Session Management
SESSION_TIMEOUT_HOURS = 1
MAX_HISTORY_LENGTH = 50
CLEANUP_INTERVAL_MINUTES = 15

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

# Feature Flags
CHAT_ENABLED = os.getenv('CHAT_ENABLED', 'true').lower() == 'true'
DEBUG_CHAT = os.getenv('DEBUG_CHAT', 'false').lower() == 'true'
