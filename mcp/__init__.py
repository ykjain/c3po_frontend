"""
HCA Lung Atlas Tree FastMCP Server

This package provides a FastMCP server that wraps all the API functionality
of the HCA Lung Atlas Tree Flask application.
"""

from .config import get_config, FASTMCP_CONFIG

__version__ = "1.0.0"
__all__ = ["get_config", "FASTMCP_CONFIG"]
