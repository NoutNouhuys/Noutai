"""
Platform Management Module

This module handles multi-platform support for Git repositories,
including GitHub and Bitbucket integration via MCP servers.
"""

from .platform_manager import PlatformManager
from .mcp_bitbucket_connector import MCPBitbucketConnector

__all__ = ['PlatformManager', 'MCPBitbucketConnector']