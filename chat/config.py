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

You also have access to external tools that can:
- Search the web for current research and information
- Look up recent publications and scientific findings
- Access real-time data and current knowledge

You can help users:
- Understand what they're seeing in visualizations
- Interpret gene programs and their biological significance
- Navigate and explore the data effectively
- Answer questions about cell types, genes, and programs
- Find relevant research papers and current scientific context
- Search for additional information when needed

When you need current information or want to verify something with recent research, use the perplexity-ask_perplexity_ask function. ALWAYS extract the specific search terms from the user's request and pass them as the "query" parameter. Examples:

- User asks: "Can you find the HCA lung atlas paper?" 
  → Use function with: {"query": "HCA Human Lung Cell Atlas paper Nature Medicine"}

- User asks: "What's the latest research on lung fibrosis?"
  → Use function with: {"query": "latest lung fibrosis research 2024"}

- User asks: "Find information about ACTA2 gene in lung disease"
  → Use function with: {"query": "ACTA2 gene lung disease research"}

CRITICAL: Never call the function with empty parameters {}. Always extract and include the search terms from the conversation.

Be concise but informative. Reference specific data when relevant. If you're unsure about something, say so rather than guessing, and consider searching for more information."""

# Claude Configuration
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Latest Sonnet 4 model
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
        "name": "perplexity-ask",
        "command": "npx",
        "args": [
            "-y",
            "server-perplexity-ask"
        ],
        "env": {
            "PERPLEXITY_API_KEY": os.getenv('PERPLEXITY_API_KEY')
        },
        "enabled": True,
        "description": "Perplexity search and research assistant"
    }
]

# Feature Flags
CHAT_ENABLED = os.getenv('CHAT_ENABLED', 'true').lower() == 'true'
DEBUG_CHAT = os.getenv('DEBUG_CHAT', 'false').lower() == 'true'  # Disable debug by default
