"""
Repository analyzer module for generating repository summaries.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    """Analyzes repository structure and generates summaries."""
    
    # File extensions to include in analysis
    INCLUDE_EXTENSIONS = {
        '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', 
        '.txt', '.md', '.rst', '.ini', '.cfg', '.conf',
        '.sh', '.bat', '.ps1', '.dockerfile', '.gitignore',
        '.env', '.env.example', '.sql', '.xml', '.toml'
    }
    
    # Directories to exclude from analysis
    EXCLUDE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.pytest_cache', '.mypy_cache',
        'htmlcov', '.coverage', '.tox', 'egg-info', '.idea', '.vscode'
    }
    
    # Maximum file size to analyze (in bytes)
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize the repository analyzer.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        
    def analyze_repository(self) -> Dict[str, any]:
        """
        Analyze the repository structure and content.
        
        Returns:
            Dictionary containing repository analysis
        """
        logger.info(f"Analyzing repository at: {self.repo_path}")
        
        # Collect all files
        files_by_dir = self._collect_files()
        
        # Analyze files
        file_analyses = self._analyze_files(files_by_dir)
        
        # Generate summary
        summary = self._generate_summary(file_analyses)
        
        return {
            'repo_path': str(self.repo_path),
            'files_by_directory': file_analyses,
            'summary': summary,
            'total_files': sum(len(files) for files in file_analyses.values()),
            'total_directories': len(file_analyses)
        }
    
    def _collect_files(self) -> Dict[str, List[Path]]:
        """
        Collect all relevant files in the repository.
        
        Returns:
            Dictionary mapping directory paths to lists of files
        """
        files_by_dir = {}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            root_path = Path(root)
            relative_root = root_path.relative_to(self.repo_path)
            
            # Skip if no relevant files
            relevant_files = []
            for file in files:
                file_path = root_path / file
                if self._should_include_file(file_path):
                    relevant_files.append(file_path)
            
            if relevant_files:
                dir_key = str(relative_root) if str(relative_root) != '.' else 'root'
                files_by_dir[dir_key] = relevant_files
                
        return files_by_dir
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included in the analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be included
        """
        # Check extension
        if file_path.suffix.lower() not in self.INCLUDE_EXTENSIONS:
            # Also include files without extension that might be important
            if file_path.name not in ['Makefile', 'Dockerfile', 'LICENSE', 'README']:
                return False
        
        # Check file size
        try:
            if file_path.stat().st_size > self.MAX_FILE_SIZE:
                return False
        except OSError:
            return False
            
        return True
    
    def _analyze_files(self, files_by_dir: Dict[str, List[Path]]) -> Dict[str, List[Dict]]:
        """
        Analyze individual files.
        
        Args:
            files_by_dir: Dictionary of files organized by directory
            
        Returns:
            Dictionary with file analysis data
        """
        analyzed = {}
        
        for dir_name, files in files_by_dir.items():
            analyzed[dir_name] = []
            
            for file_path in sorted(files):
                try:
                    file_info = self._analyze_file(file_path)
                    analyzed[dir_name].append(file_info)
                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {e}")
                    
        return analyzed
    
    def _analyze_file(self, file_path: Path) -> Dict[str, any]:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        relative_path = file_path.relative_to(self.repo_path)
        
        # Get file stats
        stats = file_path.stat()
        size = stats.st_size
        
        # Determine file type and purpose
        file_type = self._determine_file_type(file_path)
        description = self._generate_file_description(file_path, file_type)
        
        return {
            'path': str(relative_path),
            'name': file_path.name,
            'size': size,
            'type': file_type,
            'description': description
        }
    
    def _determine_file_type(self, file_path: Path) -> str:
        """
        Determine the type of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String describing the file type
        """
        # Special cases
        name_lower = file_path.name.lower()
        
        if name_lower == 'dockerfile':
            return 'Docker configuration'
        elif name_lower == 'makefile':
            return 'Build configuration'
        elif name_lower.startswith('readme'):
            return 'Documentation'
        elif name_lower == 'requirements.txt':
            return 'Python dependencies'
        elif name_lower == 'package.json':
            return 'Node.js configuration'
        elif name_lower == 'setup.py':
            return 'Python package setup'
        
        # By extension
        ext = file_path.suffix.lower()
        
        ext_types = {
            '.py': 'Python module',
            '.js': 'JavaScript module',
            '.html': 'HTML template',
            '.css': 'Stylesheet',
            '.json': 'JSON data',
            '.yaml': 'YAML configuration',
            '.yml': 'YAML configuration',
            '.txt': 'Text file',
            '.md': 'Markdown documentation',
            '.sh': 'Shell script',
            '.sql': 'SQL script',
            '.env': 'Environment configuration'
        }
        
        return ext_types.get(ext, 'File')
    
    def _generate_file_description(self, file_path: Path, file_type: str) -> str:
        """
        Generate a description for a file based on its content and context.
        
        Args:
            file_path: Path to the file
            file_type: Type of the file
            
        Returns:
            Description string
        """
        name = file_path.stem
        
        # Try to read first few lines for Python files
        if file_path.suffix == '.py':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]
                    
                # Look for docstring
                for i, line in enumerate(lines):
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        # Found docstring start
                        docstring = line.strip().strip('"""').strip("'''").strip()
                        if docstring:
                            return docstring
                        # Look for continuation
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if '"""' in lines[j] or "'''" in lines[j]:
                                break
                            docstring = lines[j].strip()
                            if docstring:
                                return docstring
                                
            except Exception:
                pass
        
        # Common patterns
        patterns = {
            'test_': 'Unit tests for',
            '_test': 'Unit tests for',
            'config': 'Configuration for',
            'setup': 'Setup configuration',
            'utils': 'Utility functions',
            'models': 'Data models',
            'views': 'View handlers',
            'routes': 'Route definitions',
            'api': 'API endpoints',
            'auth': 'Authentication logic',
            'database': 'Database operations',
            'migrations': 'Database migrations'
        }
        
        name_lower = name.lower()
        for pattern, desc_prefix in patterns.items():
            if pattern in name_lower:
                return f"{desc_prefix} {name.replace('_', ' ').replace('-', ' ')}"
        
        # Default description
        return f"{file_type} for {name.replace('_', ' ').replace('-', ' ')}"
    
    def _generate_summary(self, file_analyses: Dict[str, List[Dict]]) -> str:
        """
        Generate a summary of the repository structure.
        
        Args:
            file_analyses: Analyzed file data
            
        Returns:
            Summary text
        """
        lines = []
        lines.append("# Repository Summary\n")
        lines.append(f"Total directories: {len(file_analyses)}")
        lines.append(f"Total files analyzed: {sum(len(files) for files in file_analyses.values())}\n")
        
        # Identify main components
        components = self._identify_components(file_analyses)
        if components:
            lines.append("## Main Components\n")
            for component, description in components.items():
                lines.append(f"- **{component}**: {description}")
            lines.append("")
        
        # File structure
        lines.append("## File Structure\n")
        
        # Sort directories for consistent output
        for dir_name in sorted(file_analyses.keys()):
            files = file_analyses[dir_name]
            if not files:
                continue
                
            if dir_name == 'root':
                lines.append("### Root Directory")
            else:
                lines.append(f"### {dir_name}/")
            
            lines.append("")
            
            # Sort files by name
            for file_info in sorted(files, key=lambda x: x['name']):
                size_kb = file_info['size'] / 1024
                lines.append(f"- **{file_info['name']}** ({size_kb:.1f} KB) - {file_info['description']}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _identify_components(self, file_analyses: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        Identify main components of the application.
        
        Args:
            file_analyses: Analyzed file data
            
        Returns:
            Dictionary of component names to descriptions
        """
        components = {}
        
        # Check for common patterns
        all_files = []
        for files in file_analyses.values():
            all_files.extend(files)
        
        file_names = {f['name'].lower() for f in all_files}
        
        # Web application patterns
        if 'app.py' in file_names or 'main.py' in file_names:
            if 'flask' in str(file_names) or 'routes' in str(file_names):
                components['Web Application'] = 'Flask-based web application'
            elif 'django' in str(file_names) or 'settings.py' in file_names:
                components['Web Application'] = 'Django-based web application'
            else:
                components['Application'] = 'Python application'
        
        # API patterns
        if any('api' in f for f in file_names):
            components['API'] = 'REST API endpoints'
        
        # Database patterns
        if any(db in str(file_names) for db in ['database', 'models', 'migrations']):
            components['Database'] = 'Database models and operations'
        
        # Authentication
        if any('auth' in f for f in file_names):
            components['Authentication'] = 'User authentication system'
        
        # Testing
        if any('test' in f for f in file_names):
            components['Testing'] = 'Unit and integration tests'
        
        # Frontend
        if any(f.endswith('.js') or f.endswith('.css') for f in file_names):
            components['Frontend'] = 'Client-side interface'
        
        return components

def generate_repository_summary(repo_path: str = ".") -> str:
    """
    Generate a repository summary for the given path.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Repository summary as a string
    """
    analyzer = RepositoryAnalyzer(repo_path)
    analysis = analyzer.analyze_repository()
    return analysis['summary']