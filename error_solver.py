"""
Error Solver Module

This module provides AI-powered error solving functionality using Claude.
It generates solutions, code fixes, and recommendations based on error analysis.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import traceback
from error_analyzer import ErrorAnalyzer
from anthropic_api import anthropic_api


class ErrorSolver:
    """
    AI-powered error solving service that generates solutions and code fixes.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the ErrorSolver with a repository path.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = Path(repo_path)
        self.error_analyzer = ErrorAnalyzer(repo_path)
        
        # Solution templates for common error types
        self.solution_templates = {
            'syntax_error': {
                'priority': 'high',
                'approach': 'fix_syntax',
                'common_fixes': [
                    'Check for missing parentheses, brackets, or quotes',
                    'Verify proper indentation',
                    'Look for typos in keywords',
                    'Ensure all opened brackets are properly closed'
                ]
            },
            'import_error': {
                'priority': 'critical',
                'approach': 'fix_imports',
                'common_fixes': [
                    'Install missing packages',
                    'Check module names and paths',
                    'Verify Python path configuration',
                    'Check for circular imports'
                ]
            },
            'name_error': {
                'priority': 'high',
                'approach': 'fix_variables',
                'common_fixes': [
                    'Define variables before use',
                    'Check variable name spelling',
                    'Verify variable scope',
                    'Check imports and function definitions'
                ]
            },
            'type_error': {
                'priority': 'medium',
                'approach': 'fix_types',
                'common_fixes': [
                    'Check data types and conversions',
                    'Verify function arguments',
                    'Check object methods and properties',
                    'Add type checking or validation'
                ]
            }
        }
    
    def solve_error(self, error_message: str, error_type: Optional[str] = None, 
                   include_code_fixes: bool = True, include_explanations: bool = True) -> Dict[str, Any]:
        """
        Main method to solve an error using AI analysis.
        
        Args:
            error_message: The error message to solve
            error_type: Optional error type hint
            include_code_fixes: Whether to generate code fixes
            include_explanations: Whether to include detailed explanations
            
        Returns:
            Dictionary containing solution information
        """
        try:
            # First analyze the error
            analysis_result = self.error_analyzer.analyze_error(error_message, error_type)
            
            if not analysis_result.get('success'):
                return analysis_result
            
            # Generate AI-powered solutions
            ai_solutions = self._generate_ai_solutions(analysis_result, include_code_fixes, include_explanations)
            
            # Combine with template-based solutions
            template_solutions = self._generate_template_solutions(analysis_result)
            
            # Generate final solution response
            solution_result = {
                'success': True,
                'error_analysis': analysis_result,
                'ai_solutions': ai_solutions,
                'template_solutions': template_solutions,
                'recommended_actions': self._generate_recommended_actions(analysis_result, ai_solutions),
                'prevention_tips': self._generate_prevention_tips(analysis_result),
                'resources': self._generate_helpful_resources(analysis_result)
            }
            
            return solution_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error solving failed: {str(e)}",
                'traceback': traceback.format_exc()
            }
    
    def _generate_ai_solutions(self, analysis_result: Dict[str, Any], 
                              include_code_fixes: bool, include_explanations: bool) -> Dict[str, Any]:
        """
        Generate AI-powered solutions using Claude.
        
        Args:
            analysis_result: Error analysis results
            include_code_fixes: Whether to generate code fixes
            include_explanations: Whether to include explanations
            
        Returns:
            AI-generated solutions
        """
        try:
            # Prepare context for Claude
            context = self._prepare_ai_context(analysis_result)
            
            # Generate the prompt
            prompt = self._create_solution_prompt(context, include_code_fixes, include_explanations)
            
            # Call Claude API
            response = anthropic_api.send_prompt(
                prompt=prompt,
                model_id='claude-3-opus-20240229',  # Use Opus for better code analysis
                system_prompt=self._get_error_solving_system_prompt(),
                temperature=0.1,  # Low temperature for more consistent solutions
                max_tokens=4000
            )
            
            if response.get('success'):
                # Parse Claude's response
                ai_response = response.get('content', '')
                parsed_solutions = self._parse_ai_response(ai_response)
                
                return {
                    'success': True,
                    'raw_response': ai_response,
                    'parsed_solutions': parsed_solutions,
                    'model_used': 'claude-3-opus-20240229',
                    'token_count': response.get('token_count', 0)
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'AI solution generation failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"AI solution generation failed: {str(e)}"
            }
    
    def _prepare_ai_context(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context information for AI analysis.
        
        Args:
            analysis_result: Error analysis results
            
        Returns:
            Prepared context for AI
        """
        context = {
            'error_message': analysis_result.get('error_message', ''),
            'error_classification': analysis_result.get('classification', {}),
            'error_locations': [],
            'file_contexts': [],
            'repository_info': {
                'path': str(self.repo_path),
                'type': 'unknown'
            }
        }
        
        # Add error locations and context
        for location in analysis_result.get('locations', []):
            if 'error' not in location:
                context['error_locations'].append({
                    'file': location.get('relative_path', location.get('file_path', '')),
                    'file_type': location.get('file_type', 'unknown'),
                    'matches': location.get('matches', [])
                })
        
        # Add file contexts with code snippets
        for ctx in analysis_result.get('context', []):
            if 'error' not in ctx:
                context['file_contexts'].append({
                    'file': ctx.get('relative_path', ctx.get('file_path', '')),
                    'error_line': ctx.get('error_line'),
                    'context_lines': ctx.get('context_lines', []),
                    'file_type': ctx.get('file_type', 'unknown')
                })
        
        # Try to detect repository type
        if (self.repo_path / 'requirements.txt').exists() or (self.repo_path / 'setup.py').exists():
            context['repository_info']['type'] = 'python'
        elif (self.repo_path / 'package.json').exists():
            context['repository_info']['type'] = 'javascript'
        elif (self.repo_path / 'pom.xml').exists():
            context['repository_info']['type'] = 'java'
        
        return context
    
    def _create_solution_prompt(self, context: Dict[str, Any], 
                               include_code_fixes: bool, include_explanations: bool) -> str:
        """
        Create a prompt for Claude to generate solutions.
        
        Args:
            context: Prepared context information
            include_code_fixes: Whether to request code fixes
            include_explanations: Whether to request explanations
            
        Returns:
            Generated prompt string
        """
        prompt_parts = [
            "# Code Error Analysis and Solution Request",
            "",
            "I need help solving a code error. Here's the information:",
            "",
            f"**Error Message:**",
            f"```",
            f"{context['error_message']}",
            f"```",
            "",
            f"**Error Classification:**",
            f"- Type: {context['error_classification'].get('primary_type', 'unknown')}",
            f"- Language: {context['error_classification'].get('language', 'unknown')}",
            f"- Category: {context['error_classification'].get('category', 'unknown')}",
            f"- Severity: {context['error_classification'].get('severity', 'unknown')}",
            ""
        ]
        
        # Add file contexts
        if context['file_contexts']:
            prompt_parts.extend([
                "**Code Context:**",
                ""
            ])
            
            for i, file_ctx in enumerate(context['file_contexts'][:3]):  # Limit to 3 files
                prompt_parts.extend([
                    f"File: {file_ctx['file']} (Line {file_ctx['error_line']})",
                    f"```{file_ctx['file_type']}",
                ])
                
                # Add context lines
                for line in file_ctx['context_lines']:
                    marker = ">>> " if line['is_error_line'] else "    "
                    prompt_parts.append(f"{marker}{line['line_number']:3d}: {line['content']}")
                
                prompt_parts.extend(["```", ""])
        
        # Add repository information
        if context['repository_info']['type'] != 'unknown':
            prompt_parts.extend([
                f"**Repository Type:** {context['repository_info']['type']}",
                ""
            ])
        
        # Add request specifications
        prompt_parts.extend([
            "**Please provide:**",
            ""
        ])
        
        if include_explanations:
            prompt_parts.extend([
                "1. **Root Cause Analysis**: Explain what's causing this error and why it occurs",
                "2. **Impact Assessment**: Describe how this error affects the application",
                ""
            ])
        
        if include_code_fixes:
            prompt_parts.extend([
                "3. **Code Fixes**: Provide specific code changes to fix the error",
                "4. **Alternative Solutions**: Suggest different approaches if applicable",
                ""
            ])
        
        prompt_parts.extend([
            "5. **Step-by-Step Solution**: Provide clear instructions to resolve the issue",
            "6. **Prevention Tips**: How to avoid this error in the future",
            "7. **Testing Recommendations**: How to verify the fix works",
            "",
            "Please format your response in clear sections and include code examples where helpful."
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_error_solving_system_prompt(self) -> str:
        """
        Get the system prompt for error solving.
        
        Returns:
            System prompt string
        """
        return """You are an expert software developer and debugging specialist. Your role is to analyze code errors and provide comprehensive, actionable solutions.

When analyzing errors:
1. Always start with the root cause - what exactly is causing the error
2. Consider the broader context - how does this fit into the application architecture
3. Provide multiple solution approaches when possible
4. Include specific code examples and fixes
5. Explain the reasoning behind your recommendations
6. Consider edge cases and potential side effects
7. Provide prevention strategies to avoid similar issues

Your responses should be:
- Clear and well-structured
- Technically accurate
- Practical and actionable
- Educational (help the developer understand the underlying concepts)
- Comprehensive but concise

Focus on providing solutions that not only fix the immediate problem but also improve code quality and maintainability."""
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured solutions.
        
        Args:
            ai_response: Raw response from Claude
            
        Returns:
            Parsed solutions
        """
        parsed = {
            'root_cause': '',
            'impact_assessment': '',
            'code_fixes': [],
            'alternative_solutions': [],
            'step_by_step': [],
            'prevention_tips': [],
            'testing_recommendations': []
        }
        
        try:
            # Simple parsing - look for common section headers
            sections = {
                'root cause': 'root_cause',
                'impact': 'impact_assessment',
                'code fix': 'code_fixes',
                'alternative': 'alternative_solutions',
                'step': 'step_by_step',
                'prevention': 'prevention_tips',
                'testing': 'testing_recommendations'
            }
            
            current_section = None
            current_content = []
            
            for line in ai_response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line starts a new section
                found_section = None
                for keyword, section_key in sections.items():
                    if keyword.lower() in line.lower() and any(marker in line for marker in ['#', '**', '*', '1.', '2.', '3.']):
                        found_section = section_key
                        break
                
                if found_section:
                    # Save previous section content
                    if current_section and current_content:
                        if isinstance(parsed[current_section], list):
                            parsed[current_section].extend(current_content)
                        else:
                            parsed[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = found_section
                    current_content = []
                else:
                    # Add to current section
                    if current_section:
                        current_content.append(line)
            
            # Save final section
            if current_section and current_content:
                if isinstance(parsed[current_section], list):
                    parsed[current_section].extend(current_content)
                else:
                    parsed[current_section] = '\n'.join(current_content)
            
            # If no structured parsing worked, put everything in root_cause
            if not any(parsed.values()):
                parsed['root_cause'] = ai_response
            
        except Exception:
            # Fallback: put entire response in root_cause
            parsed['root_cause'] = ai_response
        
        return parsed
    
    def _generate_template_solutions(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate template-based solutions for common error types.
        
        Args:
            analysis_result: Error analysis results
            
        Returns:
            Template-based solutions
        """
        classification = analysis_result.get('classification', {})
        primary_type = classification.get('primary_type', 'unknown')
        
        template = self.solution_templates.get(primary_type, {
            'priority': 'medium',
            'approach': 'general_debugging',
            'common_fixes': ['Review error message carefully', 'Check documentation', 'Search for similar issues online']
        })
        
        return {
            'error_type': primary_type,
            'priority': template['priority'],
            'approach': template['approach'],
            'common_fixes': template['common_fixes'],
            'quick_checks': self._generate_quick_checks(classification),
            'debugging_steps': self._generate_debugging_steps(classification)
        }
    
    def _generate_quick_checks(self, classification: Dict[str, Any]) -> List[str]:
        """
        Generate quick checks based on error classification.
        
        Args:
            classification: Error classification
            
        Returns:
            List of quick checks
        """
        checks = []
        
        if classification.get('is_syntax_error'):
            checks.extend([
                "Check for missing or extra parentheses, brackets, or quotes",
                "Verify indentation is consistent (especially in Python)",
                "Look for typos in keywords or variable names",
                "Check for missing colons after if/for/while statements"
            ])
        
        if classification.get('is_import_error'):
            checks.extend([
                "Verify the module is installed (pip list | grep module_name)",
                "Check if the module name is spelled correctly",
                "Ensure the module is in your Python path",
                "Check for virtual environment activation"
            ])
        
        if classification.get('is_runtime_error'):
            checks.extend([
                "Check if variables are defined before use",
                "Verify function arguments match expected parameters",
                "Check for None values where objects are expected",
                "Ensure proper error handling is in place"
            ])
        
        # Add language-specific checks
        language = classification.get('language', '')
        if language == 'python':
            checks.extend([
                "Check Python version compatibility",
                "Verify virtual environment is activated",
                "Check for circular imports"
            ])
        elif language in ['javascript', 'typescript']:
            checks.extend([
                "Check for undefined variables or functions",
                "Verify async/await usage is correct",
                "Check for proper event handling"
            ])
        
        return checks[:6]  # Limit to 6 checks
    
    def _generate_debugging_steps(self, classification: Dict[str, Any]) -> List[str]:
        """
        Generate debugging steps based on error classification.
        
        Args:
            classification: Error classification
            
        Returns:
            List of debugging steps
        """
        steps = [
            "Read the error message carefully and identify the exact line causing the issue",
            "Check the file and line number mentioned in the error",
            "Review the code context around the error location"
        ]
        
        if classification.get('is_syntax_error'):
            steps.extend([
                "Use a code editor with syntax highlighting to spot issues",
                "Check for matching brackets, parentheses, and quotes",
                "Verify proper indentation and code structure"
            ])
        
        if classification.get('is_import_error'):
            steps.extend([
                "Check if the required package is installed",
                "Verify the import statement syntax",
                "Check the module path and availability"
            ])
        
        if classification.get('is_runtime_error'):
            steps.extend([
                "Add print statements or use a debugger to trace execution",
                "Check variable values at the point of error",
                "Verify object types and method availability"
            ])
        
        steps.extend([
            "Test the fix with a minimal example",
            "Run tests to ensure the fix doesn't break other functionality",
            "Document the solution for future reference"
        ])
        
        return steps
    
    def _generate_recommended_actions(self, analysis_result: Dict[str, Any], 
                                    ai_solutions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommended actions.
        
        Args:
            analysis_result: Error analysis results
            ai_solutions: AI-generated solutions
            
        Returns:
            List of recommended actions with priorities
        """
        actions = []
        classification = analysis_result.get('classification', {})
        severity = analysis_result.get('severity', 'medium')
        
        # High priority actions based on error type
        if classification.get('is_syntax_error'):
            actions.append({
                'priority': 'immediate',
                'action': 'Fix syntax errors',
                'description': 'Resolve syntax issues to allow code to run',
                'estimated_time': '5-15 minutes'
            })
        
        if classification.get('is_import_error'):
            actions.append({
                'priority': 'immediate',
                'action': 'Resolve import issues',
                'description': 'Install missing packages or fix import paths',
                'estimated_time': '10-30 minutes'
            })
        
        # Medium priority actions
        if classification.get('is_runtime_error'):
            actions.append({
                'priority': 'high',
                'action': 'Debug runtime error',
                'description': 'Trace and fix the runtime issue',
                'estimated_time': '15-60 minutes'
            })
        
        # Add AI-suggested actions if available
        if ai_solutions.get('success') and ai_solutions.get('parsed_solutions'):
            parsed = ai_solutions['parsed_solutions']
            if parsed.get('step_by_step'):
                actions.append({
                    'priority': 'high',
                    'action': 'Follow AI-generated solution steps',
                    'description': 'Implement the detailed solution provided by AI analysis',
                    'estimated_time': '20-90 minutes'
                })
        
        # General actions
        actions.extend([
            {
                'priority': 'medium',
                'action': 'Add error handling',
                'description': 'Implement proper error handling to prevent similar issues',
                'estimated_time': '15-45 minutes'
            },
            {
                'priority': 'low',
                'action': 'Add tests',
                'description': 'Create tests to catch this type of error in the future',
                'estimated_time': '30-120 minutes'
            },
            {
                'priority': 'low',
                'action': 'Update documentation',
                'description': 'Document the solution and prevention strategies',
                'estimated_time': '10-30 minutes'
            }
        ])
        
        return actions
    
    def _generate_prevention_tips(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        Generate tips to prevent similar errors in the future.
        
        Args:
            analysis_result: Error analysis results
            
        Returns:
            List of prevention tips
        """
        tips = []
        classification = analysis_result.get('classification', {})
        
        if classification.get('is_syntax_error'):
            tips.extend([
                "Use a code editor with syntax highlighting and error detection",
                "Enable linting tools (pylint, eslint, etc.) in your development environment",
                "Use consistent indentation (configure your editor to show whitespace)",
                "Set up pre-commit hooks to catch syntax errors before committing"
            ])
        
        if classification.get('is_import_error'):
            tips.extend([
                "Use virtual environments to manage dependencies",
                "Maintain a requirements.txt or package.json file",
                "Use dependency management tools (pip-tools, npm, yarn)",
                "Document installation and setup procedures clearly"
            ])
        
        if classification.get('is_runtime_error'):
            tips.extend([
                "Add comprehensive error handling and logging",
                "Use type hints and static type checking tools",
                "Write unit tests to catch errors early",
                "Use debugging tools and profilers during development"
            ])
        
        # General prevention tips
        tips.extend([
            "Follow coding standards and best practices for your language",
            "Use version control and make small, focused commits",
            "Code review processes can catch errors before they reach production",
            "Keep dependencies up to date and monitor for security issues",
            "Use continuous integration to run tests automatically",
            "Document your code and maintain clear README files"
        ])
        
        return tips[:8]  # Limit to 8 tips
    
    def _generate_helpful_resources(self, analysis_result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate helpful resources based on the error type.
        
        Args:
            analysis_result: Error analysis results
            
        Returns:
            List of helpful resources
        """
        resources = []
        classification = analysis_result.get('classification', {})
        language = classification.get('language', 'unknown')
        
        # Language-specific resources
        if language == 'python':
            resources.extend([
                {
                    'title': 'Python Official Documentation',
                    'url': 'https://docs.python.org/',
                    'description': 'Official Python documentation and tutorials'
                },
                {
                    'title': 'Python Error Handling Guide',
                    'url': 'https://docs.python.org/3/tutorial/errors.html',
                    'description': 'Official guide to handling exceptions in Python'
                },
                {
                    'title': 'Python Debugging with pdb',
                    'url': 'https://docs.python.org/3/library/pdb.html',
                    'description': 'Python debugger documentation'
                }
            ])
        
        elif language in ['javascript', 'typescript']:
            resources.extend([
                {
                    'title': 'MDN JavaScript Documentation',
                    'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
                    'description': 'Comprehensive JavaScript documentation'
                },
                {
                    'title': 'JavaScript Error Handling',
                    'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling',
                    'description': 'Guide to error handling in JavaScript'
                }
            ])
        
        # Error-type specific resources
        if classification.get('is_syntax_error'):
            resources.append({
                'title': 'Common Syntax Errors Guide',
                'url': 'https://stackoverflow.com/questions/tagged/syntax-error',
                'description': 'Community discussions about syntax errors'
            })
        
        if classification.get('is_import_error'):
            resources.append({
                'title': 'Package Management Best Practices',
                'url': 'https://packaging.python.org/tutorials/managing-dependencies/',
                'description': 'Guide to managing Python dependencies'
            })
        
        # General resources
        resources.extend([
            {
                'title': 'Stack Overflow',
                'url': 'https://stackoverflow.com/',
                'description': 'Community-driven Q&A for programming questions'
            },
            {
                'title': 'GitHub Issues Search',
                'url': 'https://github.com/search?type=issues',
                'description': 'Search for similar issues in open source projects'
            }
        ])
        
        return resources[:6]  # Limit to 6 resources