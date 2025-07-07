"""
Platform detection module for automatic GitHub/Bitbucket identification.
Provides intelligent platform detection based on repository identifiers and URLs.
"""
import re
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detects platform (GitHub/Bitbucket) from various repository identifiers."""
    
    PLATFORM_GITHUB = "github"
    PLATFORM_BITBUCKET = "bitbucket"
    
    # URL patterns for platform detection
    GITHUB_PATTERNS = [
        r'github\.com',
        r'api\.github\.com',
        r'raw\.githubusercontent\.com'
    ]
    
    BITBUCKET_PATTERNS = [
        r'bitbucket\.org',
        r'api\.bitbucket\.org'
    ]
    
    def __init__(self, default_platform: str = PLATFORM_GITHUB):
        """
        Initialize platform detector.
        
        Args:
            default_platform: Default platform to use when detection fails
        """
        self.default_platform = default_platform
    
    def detect_from_url(self, url: str) -> Optional[str]:
        """
        Detect platform from URL.
        
        Args:
            url: Repository or API URL
            
        Returns:
            Platform name or None if cannot be detected
        """
        if not url:
            return None
        
        url_lower = url.lower()
        
        # Check GitHub patterns
        for pattern in self.GITHUB_PATTERNS:
            if re.search(pattern, url_lower):
                logger.debug(f"Detected GitHub from URL pattern: {pattern}")
                return self.PLATFORM_GITHUB
        
        # Check Bitbucket patterns
        for pattern in self.BITBUCKET_PATTERNS:
            if re.search(pattern, url_lower):
                logger.debug(f"Detected Bitbucket from URL pattern: {pattern}")
                return self.PLATFORM_BITBUCKET
        
        logger.debug(f"Could not detect platform from URL: {url}")
        return None
    
    def detect_from_repo_identifier(self, repo_identifier: str) -> Optional[str]:
        """
        Detect platform from repository identifier.
        
        Args:
            repo_identifier: Repository identifier (owner/repo, workspace/repo_slug, etc.)
            
        Returns:
            Platform name or None if cannot be detected
        """
        if not repo_identifier:
            return None
        
        # This is a heuristic approach - in practice, both platforms use similar formats
        # We'll use additional context clues or default to configured platform
        
        # Check for Bitbucket-specific patterns
        if self._looks_like_bitbucket_identifier(repo_identifier):
            logger.debug(f"Detected Bitbucket from identifier pattern: {repo_identifier}")
            return self.PLATFORM_BITBUCKET
        
        # Check for GitHub-specific patterns
        if self._looks_like_github_identifier(repo_identifier):
            logger.debug(f"Detected GitHub from identifier pattern: {repo_identifier}")
            return self.PLATFORM_GITHUB
        
        logger.debug(f"Could not detect platform from identifier: {repo_identifier}")
        return None
    
    def detect_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Detect platform from context information.
        
        Args:
            context: Context dictionary with various clues
            
        Returns:
            Platform name or None if cannot be detected
        """
        # Check for explicit platform specification
        if 'platform' in context:
            platform = context['platform'].lower()
            if platform in [self.PLATFORM_GITHUB, self.PLATFORM_BITBUCKET]:
                return platform
        
        # Check for URL in context
        for url_key in ['url', 'clone_url', 'html_url', 'api_url']:
            if url_key in context:
                platform = self.detect_from_url(context[url_key])
                if platform:
                    return platform
        
        # Check for platform-specific fields
        if 'workspace' in context and 'repo_slug' in context:
            logger.debug("Detected Bitbucket from workspace/repo_slug fields")
            return self.PLATFORM_BITBUCKET
        
        if 'owner' in context and 'repo' in context and 'workspace' not in context:
            logger.debug("Detected GitHub from owner/repo fields (no workspace)")
            return self.PLATFORM_GITHUB
        
        return None
    
    def detect_from_tool_name(self, tool_name: str) -> Optional[str]:
        """
        Detect platform from tool name.
        
        Args:
            tool_name: Name of the tool being used
            
        Returns:
            Platform name or None if cannot be detected
        """
        if not tool_name:
            return None
        
        tool_name_lower = tool_name.lower()
        
        # Check for explicit platform prefixes
        if tool_name_lower.startswith('bitbucket_') or 'bitbucket' in tool_name_lower:
            return self.PLATFORM_BITBUCKET
        
        # GitHub tools typically don't have a prefix (they're the default)
        github_tools = [
            'get_file_contents', 'create_issue', 'list_issues', 'update_issue',
            'create_pull_request', 'list_pull_requests', 'merge_pull_request',
            'create_repository', 'fork_repository', 'list_repositories',
            'create_branch', 'list_branches', 'create_or_update_file', 'push_files',
            'list_commits', 'get_commit', 'add_issue_comment'
        ]
        
        if tool_name_lower in github_tools:
            return self.PLATFORM_GITHUB
        
        return None
    
    def detect_platform(self, **kwargs) -> str:
        """
        Comprehensive platform detection using multiple methods.
        
        Args:
            **kwargs: Various detection parameters
            
        Returns:
            Detected platform name (falls back to default if detection fails)
        """
        # Try different detection methods in order of reliability
        
        # 1. Explicit platform specification
        if 'platform' in kwargs:
            platform = kwargs['platform'].lower()
            if platform in [self.PLATFORM_GITHUB, self.PLATFORM_BITBUCKET]:
                logger.debug(f"Platform explicitly specified: {platform}")
                return platform
        
        # 2. Tool name detection
        if 'tool_name' in kwargs:
            platform = self.detect_from_tool_name(kwargs['tool_name'])
            if platform:
                return platform
        
        # 3. URL detection
        for url_key in ['url', 'clone_url', 'html_url', 'api_url']:
            if url_key in kwargs:
                platform = self.detect_from_url(kwargs[url_key])
                if platform:
                    return platform
        
        # 4. Context detection
        platform = self.detect_from_context(kwargs)
        if platform:
            return platform
        
        # 5. Repository identifier detection
        if 'repo_identifier' in kwargs:
            platform = self.detect_from_repo_identifier(kwargs['repo_identifier'])
            if platform:
                return platform
        
        # 6. Argument pattern detection
        if self._has_bitbucket_args(kwargs):
            logger.debug("Detected Bitbucket from argument patterns")
            return self.PLATFORM_BITBUCKET
        
        if self._has_github_args(kwargs):
            logger.debug("Detected GitHub from argument patterns")
            return self.PLATFORM_GITHUB
        
        # Fall back to default platform
        logger.debug(f"Could not detect platform, using default: {self.default_platform}")
        return self.default_platform
    
    def normalize_repo_args(self, platform: str, **kwargs) -> Dict[str, Any]:
        """
        Normalize repository arguments for the target platform.
        
        Args:
            platform: Target platform
            **kwargs: Repository arguments
            
        Returns:
            Normalized arguments for the target platform
        """
        normalized = kwargs.copy()
        
        if platform == self.PLATFORM_BITBUCKET:
            # Convert GitHub-style args to Bitbucket-style
            if 'owner' in normalized and 'workspace' not in normalized:
                normalized['workspace'] = normalized.pop('owner')
            if 'repo' in normalized and 'repo_slug' not in normalized:
                normalized['repo_slug'] = normalized.pop('repo')
            if 'issue_number' in normalized and 'issue_id' not in normalized:
                normalized['issue_id'] = normalized.pop('issue_number')
            if 'pull_number' in normalized and 'pull_request_id' not in normalized:
                normalized['pull_request_id'] = normalized.pop('pull_number')
            if 'body' in normalized and 'content' not in normalized:
                normalized['content'] = normalized.pop('body')
        
        elif platform == self.PLATFORM_GITHUB:
            # Convert Bitbucket-style args to GitHub-style
            if 'workspace' in normalized and 'owner' not in normalized:
                normalized['owner'] = normalized.pop('workspace')
            if 'repo_slug' in normalized and 'repo' not in normalized:
                normalized['repo'] = normalized.pop('repo_slug')
            if 'issue_id' in normalized and 'issue_number' not in normalized:
                normalized['issue_number'] = normalized.pop('issue_id')
            if 'pull_request_id' in normalized and 'pull_number' not in normalized:
                normalized['pull_number'] = normalized.pop('pull_request_id')
            if 'content' in normalized and 'body' not in normalized:
                normalized['body'] = normalized.pop('content')
        
        return normalized
    
    def get_platform_specific_tool_name(self, tool_name: str, target_platform: str) -> str:
        """
        Convert tool name to platform-specific version.
        
        Args:
            tool_name: Original tool name
            target_platform: Target platform
            
        Returns:
            Platform-specific tool name
        """
        if target_platform == self.PLATFORM_BITBUCKET:
            # Add bitbucket prefix if not already present
            if not tool_name.startswith('bitbucket_') and 'bitbucket' not in tool_name:
                # Map common GitHub tools to Bitbucket equivalents
                tool_mapping = {
                    'get_file_contents': 'get_bitbucket_file_contents',
                    'create_issue': 'create_bitbucket_issue',
                    'update_issue': 'update_bitbucket_issue',
                    'list_issues': 'list_bitbucket_issues',
                    'create_pull_request': 'create_bitbucket_pull_request',
                    'list_pull_requests': 'list_bitbucket_pull_requests',
                    'merge_pull_request': 'merge_bitbucket_pull_request',
                    'create_repository': 'create_bitbucket_repository',
                    'list_repositories': 'list_bitbucket_repositories',
                    'create_branch': 'create_bitbucket_branch',
                    'list_branches': 'list_bitbucket_branches',
                    'create_or_update_file': 'create_or_update_bitbucket_file',
                    'add_issue_comment': 'add_bitbucket_issue_comment'
                }
                return tool_mapping.get(tool_name, f"bitbucket_{tool_name}")
        
        elif target_platform == self.PLATFORM_GITHUB:
            # Remove bitbucket prefix if present
            if tool_name.startswith('bitbucket_'):
                return tool_name[10:]  # Remove 'bitbucket_' prefix
            elif tool_name.startswith('get_bitbucket_'):
                return tool_name.replace('get_bitbucket_', 'get_')
            elif tool_name.startswith('create_bitbucket_'):
                return tool_name.replace('create_bitbucket_', 'create_')
            elif tool_name.startswith('list_bitbucket_'):
                return tool_name.replace('list_bitbucket_', 'list_')
            elif tool_name.startswith('update_bitbucket_'):
                return tool_name.replace('update_bitbucket_', 'update_')
            elif tool_name.startswith('merge_bitbucket_'):
                return tool_name.replace('merge_bitbucket_', 'merge_')
            elif tool_name.startswith('add_bitbucket_'):
                return tool_name.replace('add_bitbucket_', 'add_')
        
        return tool_name
    
    def _looks_like_bitbucket_identifier(self, identifier: str) -> bool:
        """Check if identifier looks like a Bitbucket repository identifier."""
        # This is a heuristic - both platforms use similar formats
        # We could check against known Bitbucket workspaces or use other clues
        return False  # For now, rely on other detection methods
    
    def _looks_like_github_identifier(self, identifier: str) -> bool:
        """Check if identifier looks like a GitHub repository identifier."""
        # This is a heuristic - both platforms use similar formats
        # We could check against known GitHub organizations or use other clues
        return False  # For now, rely on other detection methods
    
    def _has_bitbucket_args(self, kwargs: Dict[str, Any]) -> bool:
        """Check if arguments contain Bitbucket-specific fields."""
        bitbucket_fields = ['workspace', 'repo_slug', 'issue_id', 'pull_request_id']
        return any(field in kwargs for field in bitbucket_fields)
    
    def _has_github_args(self, kwargs: Dict[str, Any]) -> bool:
        """Check if arguments contain GitHub-specific fields."""
        # GitHub args are more generic, so we check for absence of Bitbucket-specific fields
        github_fields = ['owner', 'repo', 'issue_number', 'pull_number']
        bitbucket_fields = ['workspace', 'repo_slug', 'issue_id', 'pull_request_id']
        
        has_github_fields = any(field in kwargs for field in github_fields)
        has_bitbucket_fields = any(field in kwargs for field in bitbucket_fields)
        
        return has_github_fields and not has_bitbucket_fields