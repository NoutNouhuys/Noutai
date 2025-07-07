"""
Bitbucket integration module for multi-platform repository management.
Provides Bitbucket API tools and functionality equivalent to GitHub MCP tools.
"""

from .bitbucket_api import BitbucketAPI
from .platform_detector import PlatformDetector
from .unified_interface import UnifiedInterface

__all__ = ['BitbucketAPI', 'PlatformDetector', 'UnifiedInterface']