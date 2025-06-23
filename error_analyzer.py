"""
Error Analyzer Module

This module provides core functionality for analyzing code errors in repositories.
It can locate errors, extract context, and classify different types of errors.
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import traceback
import ast
import subprocess


class ErrorAnalyzer:
    """
    Core error analysis functionality for locating and analyzing code errors.
    """
    
    # Supported file extensions for analysis
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript', 
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text'
    }
    
    # Common error patterns for different languages
    ERROR_PATTERNS = {
        'python': [
            r'File "([^"]+)", line (\d+)',
            r'(\w+Error): (.+)',
            r'SyntaxError: (.+)',
            r'IndentationError: (.+)',
            r'NameError: (.+)',
            r'TypeError: (.+)',
            r'ValueError: (.+)',
            r'ImportError: (.+)',
            r'ModuleNotFoundError: (.+)',
            r'AttributeError: (.+)',
            r'KeyError: (.+)',
            r'IndexError: (.+)'
        ],
        'javascript': [
            r'(\w+Error): (.+)',
            r'SyntaxError: (.+)',
            r'ReferenceError: (.+)',
            r'TypeError: (.+)',
            r'RangeError: (.+)',
            r'at (.+):(\d+):(\d+)',
            r'Uncaught (.+)',
            r'Cannot read property (.+)',
            r'is not defined',
            r'is not a function'
        ],
        'typescript': [
            r'error TS(\d+): (.+)',
            r'Type \'(.+)\' is not assignable to type \'(.+)\'',
            r'Property \'(.+)\' does not exist on type \'(.+)\'',
            r'Cannot find name \'(.+)\'',
            r'Expected (\d+) arguments, but got (\d+)'
        ]
    }
    
    def __init__(self, repo_path: str):
        """
        Initialize the ErrorAnalyzer with a repository path.
        
        Args:
            repo_path: Path to the repository to analyze
        """
        self.repo_path = Path(repo_path)
        self.files_cache = {}
        self.analysis_results = {}
        
    def analyze_error(self, error_message: str, error_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to analyze an error message and locate it in the codebase.
        
        Args:
            error_message: The error message to analyze
            error_type: Optional error type hint (e.g., 'python', 'javascript')
            
        Returns:
            Dictionary containing error analysis results
        """
        try:
            # Parse the error message
            parsed_error = self._parse_error_message(error_message, error_type)
            
            # Locate the error in files
            error_locations = self._locate_error_in_files(parsed_error)
            
            # Extract context around error locations
            context_data = self._extract_error_context(error_locations)
            
            # Classify the error
            error_classification = self._classify_error(parsed_error, context_data)
            
            # Generate analysis summary
            analysis_result = {
                'success': True,
                'error_message': error_message,
                'parsed_error': parsed_error,
                'locations': error_locations,
                'context': context_data,
                'classification': error_classification,
                'severity': self._determine_severity(error_classification),
                'suggestions': self._generate_basic_suggestions(error_classification)
            }
            
            return analysis_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error analysis failed: {str(e)}",
                'traceback': traceback.format_exc()
            }
    
    def _parse_error_message(self, error_message: str, error_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse the error message to extract structured information.
        
        Args:
            error_message: Raw error message
            error_type: Optional language/error type hint
            
        Returns:
            Parsed error information
        """
        parsed = {
            'raw_message': error_message,
            'error_type': error_type,
            'file_path': None,
            'line_number': None,
            'column_number': None,
            'error_name': None,
            'error_description': None,
            'detected_language': None
        }
        
        # Try to detect language from error patterns
        if not error_type:
            for lang, patterns in self.ERROR_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, error_message, re.IGNORECASE):
                        parsed['detected_language'] = lang
                        break
                if parsed['detected_language']:
                    break
        else:
            parsed['detected_language'] = error_type
        
        # Extract file path and line number
        file_line_patterns = [
            r'File "([^"]+)", line (\d+)',  # Python
            r'at (.+):(\d+):(\d+)',         # JavaScript
            r'([^:]+):(\d+):(\d+)',         # General format
            r'in (.+) on line (\d+)',       # PHP-style
            r'([^(]+)\((\d+),(\d+)\)'       # C#-style
        ]
        
        for pattern in file_line_patterns:
            match = re.search(pattern, error_message)
            if match:
                if len(match.groups()) >= 2:
                    parsed['file_path'] = match.group(1)
                    parsed['line_number'] = int(match.group(2))
                if len(match.groups()) >= 3:
                    parsed['column_number'] = int(match.group(3))
                break
        
        # Extract error name and description
        error_name_patterns = [
            r'(\w+Error): (.+)',
            r'(\w+Exception): (.+)',
            r'Error: (.+)',
            r'(\w+): (.+)'
        ]
        
        for pattern in error_name_patterns:
            match = re.search(pattern, error_message)
            if match:
                if len(match.groups()) >= 2:
                    parsed['error_name'] = match.group(1)
                    parsed['error_description'] = match.group(2)
                else:
                    parsed['error_description'] = match.group(1)
                break
        
        return parsed
    
    def _locate_error_in_files(self, parsed_error: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Locate the error in repository files.
        
        Args:
            parsed_error: Parsed error information
            
        Returns:
            List of potential error locations
        """
        locations = []
        
        # If we have a specific file path, check that first
        if parsed_error.get('file_path'):
            file_path = self._resolve_file_path(parsed_error['file_path'])
            if file_path and file_path.exists():
                location = self._analyze_file_location(file_path, parsed_error)
                if location:
                    locations.append(location)
        
        # If no specific file or file not found, search all relevant files
        if not locations:
            relevant_files = self._find_relevant_files(parsed_error)
            for file_path in relevant_files:
                location = self._analyze_file_location(file_path, parsed_error)
                if location:
                    locations.append(location)
        
        return locations
    
    def _resolve_file_path(self, file_path: str) -> Optional[Path]:
        """
        Resolve a file path relative to the repository.
        
        Args:
            file_path: File path from error message
            
        Returns:
            Resolved Path object or None
        """
        # Try absolute path first
        abs_path = Path(file_path)
        if abs_path.exists():
            return abs_path
        
        # Try relative to repo root
        rel_path = self.repo_path / file_path
        if rel_path.exists():
            return rel_path
        
        # Try finding file by name in repo
        file_name = Path(file_path).name
        for root, dirs, files in os.walk(self.repo_path):
            if file_name in files:
                return Path(root) / file_name
        
        return None
    
    def _find_relevant_files(self, parsed_error: Dict[str, Any]) -> List[Path]:
        """
        Find files that might contain the error.
        
        Args:
            parsed_error: Parsed error information
            
        Returns:
            List of relevant file paths
        """
        relevant_files = []
        detected_lang = parsed_error.get('detected_language')
        
        # Get appropriate file extensions
        target_extensions = []
        if detected_lang == 'python':
            target_extensions = ['.py']
        elif detected_lang in ['javascript', 'typescript']:
            target_extensions = ['.js', '.jsx', '.ts', '.tsx']
        elif detected_lang == 'html':
            target_extensions = ['.html', '.htm']
        elif detected_lang == 'css':
            target_extensions = ['.css', '.scss', '.sass']
        else:
            # If unknown, check all supported extensions
            target_extensions = list(self.SUPPORTED_EXTENSIONS.keys())
        
        # Walk through repository and find matching files
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in target_extensions:
                    relevant_files.append(file_path)
        
        return relevant_files
    
    def _analyze_file_location(self, file_path: Path, parsed_error: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific file for the error.
        
        Args:
            file_path: Path to the file to analyze
            parsed_error: Parsed error information
            
        Returns:
            Location information if error found, None otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            location = {
                'file_path': str(file_path),
                'relative_path': str(file_path.relative_to(self.repo_path)),
                'file_type': self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), 'unknown'),
                'total_lines': len(lines),
                'matches': []
            }
            
            # Check specific line number if provided
            if parsed_error.get('line_number'):
                line_num = parsed_error['line_number']
                if 1 <= line_num <= len(lines):
                    location['matches'].append({
                        'line_number': line_num,
                        'line_content': lines[line_num - 1],
                        'match_type': 'line_number',
                        'confidence': 0.9
                    })
            
            # Search for error patterns in content
            error_desc = parsed_error.get('error_description', '')
            if error_desc:
                # Look for similar patterns or keywords
                keywords = self._extract_keywords(error_desc)
                for i, line in enumerate(lines, 1):
                    for keyword in keywords:
                        if keyword.lower() in line.lower():
                            location['matches'].append({
                                'line_number': i,
                                'line_content': line,
                                'match_type': 'keyword',
                                'keyword': keyword,
                                'confidence': 0.5
                            })
            
            # Syntax check for Python files
            if file_path.suffix == '.py':
                syntax_errors = self._check_python_syntax(file_path, content)
                for error in syntax_errors:
                    location['matches'].append({
                        'line_number': error.get('line_number'),
                        'line_content': error.get('line_content'),
                        'match_type': 'syntax_error',
                        'error_type': error.get('error_type'),
                        'confidence': 0.8
                    })
            
            return location if location['matches'] else None
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': f"Failed to analyze file: {str(e)}"
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from error description.
        
        Args:
            text: Error description text
            
        Returns:
            List of keywords
        """
        # Remove common words and extract meaningful terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'cannot', 'not'}
        
        # Extract words and identifiers
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        # Also extract quoted strings and identifiers
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", text)
        for match in quoted:
            for group in match:
                if group:
                    keywords.append(group)
        
        return list(set(keywords))
    
    def _check_python_syntax(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """
        Check Python file for syntax errors.
        
        Args:
            file_path: Path to Python file
            content: File content
            
        Returns:
            List of syntax errors found
        """
        errors = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append({
                'line_number': e.lineno,
                'line_content': content.splitlines()[e.lineno - 1] if e.lineno and e.lineno <= len(content.splitlines()) else '',
                'error_type': 'SyntaxError',
                'message': str(e),
                'column': e.offset
            })
        except Exception as e:
            errors.append({
                'line_number': None,
                'line_content': '',
                'error_type': type(e).__name__,
                'message': str(e)
            })
        
        return errors
    
    def _extract_error_context(self, error_locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract context around error locations.
        
        Args:
            error_locations: List of error locations
            
        Returns:
            List of context data for each location
        """
        context_data = []
        
        for location in error_locations:
            if 'error' in location:
                continue
                
            try:
                file_path = Path(location['file_path'])
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for match in location.get('matches', []):
                    line_num = match.get('line_number')
                    if not line_num:
                        continue
                    
                    # Extract context (10 lines before and after)
                    context_start = max(1, line_num - 10)
                    context_end = min(len(lines), line_num + 10)
                    
                    context_lines = []
                    for i in range(context_start, context_end + 1):
                        context_lines.append({
                            'line_number': i,
                            'content': lines[i - 1].rstrip(),
                            'is_error_line': i == line_num
                        })
                    
                    context_data.append({
                        'file_path': location['file_path'],
                        'relative_path': location['relative_path'],
                        'file_type': location['file_type'],
                        'error_line': line_num,
                        'context_start': context_start,
                        'context_end': context_end,
                        'context_lines': context_lines,
                        'match_info': match
                    })
                    
            except Exception as e:
                context_data.append({
                    'file_path': location['file_path'],
                    'error': f"Failed to extract context: {str(e)}"
                })
        
        return context_data
    
    def _classify_error(self, parsed_error: Dict[str, Any], context_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify the error type and characteristics.
        
        Args:
            parsed_error: Parsed error information
            context_data: Context data around error locations
            
        Returns:
            Error classification
        """
        classification = {
            'primary_type': 'unknown',
            'secondary_types': [],
            'language': parsed_error.get('detected_language', 'unknown'),
            'category': 'unknown',
            'is_syntax_error': False,
            'is_runtime_error': False,
            'is_logic_error': False,
            'is_import_error': False,
            'affected_files': len(context_data),
            'complexity': 'unknown'
        }
        
        error_name = parsed_error.get('error_name', '').lower()
        error_desc = parsed_error.get('error_description', '').lower()
        
        # Classify by error name
        if 'syntax' in error_name:
            classification['primary_type'] = 'syntax_error'
            classification['is_syntax_error'] = True
            classification['category'] = 'compile_time'
        elif 'import' in error_name or 'module' in error_name:
            classification['primary_type'] = 'import_error'
            classification['is_import_error'] = True
            classification['category'] = 'dependency'
        elif any(x in error_name for x in ['name', 'reference', 'undefined']):
            classification['primary_type'] = 'name_error'
            classification['is_runtime_error'] = True
            classification['category'] = 'runtime'
        elif 'type' in error_name:
            classification['primary_type'] = 'type_error'
            classification['is_runtime_error'] = True
            classification['category'] = 'runtime'
        elif any(x in error_name for x in ['value', 'range', 'index', 'key']):
            classification['primary_type'] = 'value_error'
            classification['is_runtime_error'] = True
            classification['category'] = 'runtime'
        elif 'attribute' in error_name:
            classification['primary_type'] = 'attribute_error'
            classification['is_runtime_error'] = True
            classification['category'] = 'runtime'
        
        # Classify by error description patterns
        if any(x in error_desc for x in ['not defined', 'is not defined']):
            classification['secondary_types'].append('undefined_variable')
        if any(x in error_desc for x in ['cannot read property', 'has no attribute']):
            classification['secondary_types'].append('missing_attribute')
        if any(x in error_desc for x in ['is not a function', 'not callable']):
            classification['secondary_types'].append('wrong_type_usage')
        if any(x in error_desc for x in ['indentation', 'indent']):
            classification['secondary_types'].append('indentation_error')
        
        # Determine complexity
        if classification['is_syntax_error']:
            classification['complexity'] = 'simple'
        elif classification['is_import_error']:
            classification['complexity'] = 'medium'
        elif len(context_data) > 3:
            classification['complexity'] = 'complex'
        else:
            classification['complexity'] = 'medium'
        
        return classification
    
    def _determine_severity(self, classification: Dict[str, Any]) -> str:
        """
        Determine error severity level.
        
        Args:
            classification: Error classification
            
        Returns:
            Severity level (critical, high, medium, low)
        """
        if classification['is_syntax_error']:
            return 'high'  # Prevents code from running
        elif classification['is_import_error']:
            return 'critical'  # Prevents application from starting
        elif classification['primary_type'] in ['name_error', 'reference_error']:
            return 'high'  # Causes runtime crashes
        elif classification['primary_type'] in ['type_error', 'attribute_error']:
            return 'medium'  # May cause runtime issues
        elif classification['complexity'] == 'complex':
            return 'high'  # Complex errors are harder to fix
        else:
            return 'medium'
    
    def _generate_basic_suggestions(self, classification: Dict[str, Any]) -> List[str]:
        """
        Generate basic suggestions for fixing the error.
        
        Args:
            classification: Error classification
            
        Returns:
            List of basic suggestions
        """
        suggestions = []
        
        if classification['is_syntax_error']:
            suggestions.extend([
                "Check for missing parentheses, brackets, or quotes",
                "Verify proper indentation (especially in Python)",
                "Look for typos in keywords or operators",
                "Ensure all opened brackets/parentheses are properly closed"
            ])
        
        if classification['is_import_error']:
            suggestions.extend([
                "Check if the module is installed (pip install <module>)",
                "Verify the module name spelling",
                "Check if the module path is correct",
                "Ensure the module is in your Python path"
            ])
        
        if classification['primary_type'] == 'name_error':
            suggestions.extend([
                "Check if the variable is defined before use",
                "Verify variable name spelling",
                "Check variable scope (local vs global)",
                "Ensure imports are correct"
            ])
        
        if classification['primary_type'] == 'type_error':
            suggestions.extend([
                "Check if you're using the correct data type",
                "Verify function arguments match expected types",
                "Check if object has the expected methods/properties",
                "Consider type conversion if needed"
            ])
        
        if classification['primary_type'] == 'attribute_error':
            suggestions.extend([
                "Check if the object has the attribute you're trying to access",
                "Verify object initialization",
                "Check for typos in attribute names",
                "Ensure the object is of the expected type"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Review the error message carefully for specific details",
            "Check the documentation for the relevant functions/modules",
            "Consider using debugging tools to trace the issue",
            "Look for similar issues in online resources"
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Get a summary of a file's structure and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File summary information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {'error': 'File not found'}
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            summary = {
                'file_path': str(path),
                'file_type': self.SUPPORTED_EXTENSIONS.get(path.suffix.lower(), 'unknown'),
                'size_bytes': len(content),
                'line_count': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'functions': [],
                'classes': [],
                'imports': []
            }
            
            # Analyze Python files more deeply
            if path.suffix == '.py':
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            summary['functions'].append({
                                'name': node.name,
                                'line_number': node.lineno,
                                'args': [arg.arg for arg in node.args.args]
                            })
                        elif isinstance(node, ast.ClassDef):
                            summary['classes'].append({
                                'name': node.name,
                                'line_number': node.lineno
                            })
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    summary['imports'].append({
                                        'module': alias.name,
                                        'alias': alias.asname,
                                        'line_number': node.lineno
                                    })
                            else:  # ImportFrom
                                for alias in node.names:
                                    summary['imports'].append({
                                        'module': node.module,
                                        'name': alias.name,
                                        'alias': alias.asname,
                                        'line_number': node.lineno
                                    })
                except:
                    pass  # If AST parsing fails, continue with basic info
            
            return summary
            
        except Exception as e:
            return {'error': f"Failed to analyze file: {str(e)}"}