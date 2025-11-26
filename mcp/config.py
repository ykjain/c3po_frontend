#!/usr/bin/env python3
"""
Configuration for HCA Lung Atlas Tree FastMCP Server
"""

import os

# Server configuration
DEFAULT_BASE_URL = "http://localhost:12534"
BASE_URL = os.environ.get("HCA_ATLAS_BASE_URL", DEFAULT_BASE_URL)

# FastMCP Server configuration
FASTMCP_CONFIG = {
    "name": "hca-lung-atlas-tree",
    "description": "HCA Lung Atlas Tree API wrapper providing access to single-cell lung atlas data via FastMCP",
    "version": "1.0.0",
    "base_url": BASE_URL,
    "host": "0.0.0.0",
    "port": 8000,
    "tools": [
        {
            "name": "get_tree_structure",
            "description": "Get the complete tree structure for navigation",
            "category": "navigation"
        },
        {
            "name": "get_node_programs", 
            "description": "Get program list and summary for a specific node",
            "category": "data_access"
        },
        {
            "name": "get_program_description",
            "description": "Get detailed description for a specific program",
            "category": "data_access"
        },
        {
            "name": "get_program_genes",
            "description": "Get genes associated with a specific program", 
            "category": "data_access"
        },
        {
            "name": "get_program_loadings",
            "description": "Get loadings data for a specific program",
            "category": "data_access"
        },
        {
            "name": "get_node_summary",
            "description": "Get summary figures and program labels for a node",
            "category": "analysis"
        },
        {
            "name": "get_atlas_stats",
            "description": "Get overall statistics about the atlas",
            "category": "overview"
        },
        {
            "name": "search_programs_by_gene",
            "description": "Search for programs containing a specific gene",
            "category": "search"
        },
        {
            "name": "get_interactive_plot",
            "description": "Get interactive plot HTML content",
            "category": "visualization"
        },
        {
            "name": "analyze_node_composition",
            "description": "Comprehensive analysis of node composition",
            "category": "analysis"
        }
    ]
}

# Environment configurations
ENVIRONMENTS = {
    "local": {
        "base_url": "http://localhost:12534",
        "host": "127.0.0.1",
        "port": 8000,
        "description": "Local development server"
    },
    "production": {
        "base_url": "http://your-server:12534",
        "host": "0.0.0.0", 
        "port": 8000,
        "description": "Production server"
    }
}

def get_config(environment: str = "local") -> dict:
    """Get configuration for a specific environment."""
    env_config = ENVIRONMENTS.get(environment, ENVIRONMENTS["local"])
    config = FASTMCP_CONFIG.copy()
    config.update(env_config)
    return config
