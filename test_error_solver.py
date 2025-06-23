"""
Unit Tests for Error Solving Functionality

Tests for the ErrorAnalyzer and ErrorSolver classes to ensure
proper error detection, analysis, and solution generation.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from error_analyzer import ErrorAnalyzer
from error_solver import ErrorSolver


class TestErrorAnalyzer(unittest.TestCase):
    """Test cases for the ErrorAnalyzer class."""
    
    def setUp(self):
        """Set up test environment with temporary repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create sample files for testing
        self.create_sample_files()
        
        self.analyzer = ErrorAnalyzer(str(self.repo_path))
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_files(self):
        """Create sample files for testing."""
        # Python file with syntax error
        python_file = self.repo_path / "test_script.py"
        python_file.write_text("""
def hello_world():
    print("Hello, World!"
    return "Hello"

def another_function():
    x = undefined_variable
    return x
""")
        
        # JavaScript file
        js_file = self.repo_path / "script.js"
        js_file.write_text("""
function greet(name) {
    console.log("Hello, " + name);
    return undefinedVariable;
}

greet("World");
""")
        
        # HTML file
        html_file = self.repo_path / "index.html"
        html_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
    <script src="script.js"></script>
</body>
</html>
""")
    
    def test_initialization(self):
        """Test ErrorAnalyzer initialization."""
        self.assertEqual(self.analyzer.repo_path, self.repo_path)
        self.assertIsInstance(self.analyzer.files_cache, dict)
        self.assertIsInstance(self.analyzer.analysis_results, dict)
    
    def test_supported_extensions(self):
        """Test that supported file extensions are properly defined."""
        self.assertIn('.py', ErrorAnalyzer.SUPPORTED_EXTENSIONS)
        self.assertIn('.js', ErrorAnalyzer.SUPPORTED_EXTENSIONS)
        self.assertIn('.html', ErrorAnalyzer.SUPPORTED_EXTENSIONS)
        self.assertEqual(ErrorAnalyzer.SUPPORTED_EXTENSIONS['.py'], 'python')
        self.assertEqual(ErrorAnalyzer.SUPPORTED_EXTENSIONS['.js'], 'javascript')
    
    def test_parse_error_message_python(self):
        """Test parsing Python error messages."""
        error_message = 'File "test_script.py", line 3, in hello_world\n    print("Hello, World!"\nSyntaxError: unexpected EOF while parsing'
        
        parsed = self.analyzer._parse_error_message(error_message)
        
        self.assertEqual(parsed['file_path'], 'test_script.py')
        self.assertEqual(parsed['line_number'], 3)
        self.assertEqual(parsed['error_name'], 'SyntaxError')
        self.assertIn('unexpected EOF', parsed['error_description'])
        self.assertEqual(parsed['detected_language'], 'python')
    
    def test_parse_error_message_javascript(self):
        """Test parsing JavaScript error messages."""
        error_message = 'ReferenceError: undefinedVariable is not defined\n    at greet (script.js:4:12)'
        
        parsed = self.analyzer._parse_error_message(error_message)
        
        self.assertEqual(parsed['error_name'], 'ReferenceError')
        self.assertIn('undefinedVariable', parsed['error_description'])
        self.assertEqual(parsed['detected_language'], 'javascript')
    
    def test_parse_error_message_no_file_info(self):
        """Test parsing error messages without file information."""
        error_message = 'TypeError: Cannot read property of undefined'
        
        parsed = self.analyzer._parse_error_message(error_message)
        
        self.assertIsNone(parsed['file_path'])
        self.assertIsNone(parsed['line_number'])
        self.assertIn('TypeError', parsed['error_name'])
    
    def test_resolve_file_path(self):
        """Test file path resolution."""
        # Test relative path
        relative_path = "test_script.py"
        resolved = self.analyzer._resolve_file_path(relative_path)
        self.assertEqual(resolved, self.repo_path / "test_script.py")
        
        # Test absolute path
        absolute_path = str(self.repo_path / "test_script.py")
        resolved = self.analyzer._resolve_file_path(absolute_path)
        self.assertEqual(resolved, Path(absolute_path))
        
        # Test non-existent file
        non_existent = "non_existent.py"
        resolved = self.analyzer._resolve_file_path(non_existent)
        self.assertIsNone(resolved)
    
    def test_find_relevant_files(self):
        """Test finding relevant files in repository."""
        parsed_error = {'detected_language': 'python'}
        relevant_files = self.analyzer._find_relevant_files(parsed_error)
        
        # Should find the Python file
        python_files = [f for f in relevant_files if f.suffix == '.py']
        self.assertEqual(len(python_files), 1)
        self.assertEqual(python_files[0].name, 'test_script.py')
    
    def test_extract_keywords(self):
        """Test keyword extraction from error descriptions."""
        text = "NameError: name 'undefined_variable' is not defined"
        keywords = self.analyzer._extract_keywords(text)
        
        self.assertIn('undefined_variable', keywords)
        self.assertIn('defined', keywords)
        self.assertNotIn('is', keywords)  # Common word should be filtered
    
    def test_check_python_syntax(self):
        """Test Python syntax checking."""
        # Test file with syntax error
        python_file = self.repo_path / "test_script.py"
        content = python_file.read_text()
        
        errors = self.analyzer._check_python_syntax(python_file, content)
        
        self.assertGreater(len(errors), 0)
        self.assertEqual(errors[0]['error_type'], 'SyntaxError')
        self.assertIsNotNone(errors[0]['line_number'])
    
    def test_analyze_error_success(self):
        """Test successful error analysis."""
        error_message = 'File "test_script.py", line 3, in hello_world\nSyntaxError: unexpected EOF while parsing'
        
        result = self.analyzer.analyze_error(error_message)
        
        self.assertTrue(result['success'])
        self.assertIn('parsed_error', result)
        self.assertIn('locations', result)
        self.assertIn('classification', result)
        self.assertEqual(result['parsed_error']['detected_language'], 'python')
    
    def test_analyze_error_with_type_hint(self):
        """Test error analysis with explicit type hint."""
        error_message = 'ReferenceError: undefinedVariable is not defined'
        
        result = self.analyzer.analyze_error(error_message, error_type='javascript')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['parsed_error']['error_type'], 'javascript')
    
    def test_classify_error_syntax(self):
        """Test error classification for syntax errors."""
        parsed_error = {
            'error_name': 'SyntaxError',
            'error_description': 'unexpected EOF while parsing',
            'detected_language': 'python'
        }
        
        classification = self.analyzer._classify_error(parsed_error, [])
        
        self.assertEqual(classification['primary_type'], 'syntax_error')
        self.assertTrue(classification['is_syntax_error'])
        self.assertEqual(classification['category'], 'compile_time')
    
    def test_classify_error_import(self):
        """Test error classification for import errors."""
        parsed_error = {
            'error_name': 'ImportError',
            'error_description': 'No module named requests',
            'detected_language': 'python'
        }
        
        classification = self.analyzer._classify_error(parsed_error, [])
        
        self.assertEqual(classification['primary_type'], 'import_error')
        self.assertTrue(classification['is_import_error'])
        self.assertEqual(classification['category'], 'dependency')
    
    def test_determine_severity(self):
        """Test severity determination."""
        # Syntax error should be high severity
        syntax_classification = {'is_syntax_error': True, 'primary_type': 'syntax_error'}
        severity = self.analyzer._determine_severity(syntax_classification)
        self.assertEqual(severity, 'high')
        
        # Import error should be critical
        import_classification = {'is_import_error': True, 'primary_type': 'import_error'}
        severity = self.analyzer._determine_severity(import_classification)
        self.assertEqual(severity, 'critical')
    
    def test_get_file_summary(self):
        """Test file summary generation."""
        python_file = str(self.repo_path / "test_script.py")
        summary = self.analyzer.get_file_summary(python_file)
        
        self.assertNotIn('error', summary)
        self.assertEqual(summary['file_type'], 'python')
        self.assertGreater(summary['line_count'], 0)
        self.assertIn('functions', summary)


class TestErrorSolver(unittest.TestCase):
    """Test cases for the ErrorSolver class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create a simple Python file
        python_file = self.repo_path / "test.py"
        python_file.write_text("""
def test_function():
    print("Hello, World!"
    return True
""")
        
        self.solver = ErrorSolver(str(self.repo_path))
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test ErrorSolver initialization."""
        self.assertEqual(self.solver.repo_path, self.repo_path)
        self.assertIsInstance(self.solver.error_analyzer, ErrorAnalyzer)
        self.assertIn('syntax_error', self.solver.solution_templates)
    
    def test_solution_templates(self):
        """Test that solution templates are properly defined."""
        templates = self.solver.solution_templates
        
        self.assertIn('syntax_error', templates)
        self.assertIn('import_error', templates)
        self.assertIn('name_error', templates)
        
        # Check template structure
        syntax_template = templates['syntax_error']
        self.assertIn('priority', syntax_template)
        self.assertIn('approach', syntax_template)
        self.assertIn('common_fixes', syntax_template)
    
    @patch('error_solver.anthropic_api')
    def test_generate_ai_solutions_success(self, mock_anthropic):
        """Test successful AI solution generation."""
        # Mock the anthropic API response
        mock_anthropic.send_prompt.return_value = {
            'success': True,
            'content': 'This is a syntax error caused by missing parentheses...',
            'token_count': 150
        }
        
        analysis_result = {
            'error_message': 'SyntaxError: unexpected EOF',
            'classification': {'primary_type': 'syntax_error'},
            'locations': [],
            'context': []
        }
        
        ai_solutions = self.solver._generate_ai_solutions(analysis_result, True, True)
        
        self.assertTrue(ai_solutions['success'])
        self.assertIn('parsed_solutions', ai_solutions)
        self.assertEqual(ai_solutions['model_used'], 'claude-3-opus-20240229')
    
    @patch('error_solver.anthropic_api')
    def test_generate_ai_solutions_failure(self, mock_anthropic):
        """Test AI solution generation failure."""
        # Mock the anthropic API failure
        mock_anthropic.send_prompt.return_value = {
            'success': False,
            'error': 'API error'
        }
        
        analysis_result = {
            'error_message': 'SyntaxError: unexpected EOF',
            'classification': {'primary_type': 'syntax_error'},
            'locations': [],
            'context': []
        }
        
        ai_solutions = self.solver._generate_ai_solutions(analysis_result, True, True)
        
        self.assertFalse(ai_solutions['success'])
        self.assertIn('error', ai_solutions)
    
    def test_prepare_ai_context(self):
        """Test AI context preparation."""
        analysis_result = {
            'error_message': 'SyntaxError: unexpected EOF',
            'classification': {
                'primary_type': 'syntax_error',
                'language': 'python'
            },
            'locations': [{
                'relative_path': 'test.py',
                'file_type': 'python',
                'matches': [{'line_number': 3, 'match_type': 'syntax_error'}]
            }],
            'context': [{
                'relative_path': 'test.py',
                'error_line': 3,
                'context_lines': [
                    {'line_number': 2, 'content': 'def test_function():', 'is_error_line': False},
                    {'line_number': 3, 'content': '    print("Hello, World!"', 'is_error_line': True}
                ]
            }]
        }
        
        context = self.solver._prepare_ai_context(analysis_result)
        
        self.assertEqual(context['error_message'], 'SyntaxError: unexpected EOF')
        self.assertEqual(len(context['error_locations']), 1)
        self.assertEqual(len(context['file_contexts']), 1)
        self.assertEqual(context['file_contexts'][0]['error_line'], 3)
    
    def test_create_solution_prompt(self):
        """Test solution prompt creation."""
        context = {
            'error_message': 'SyntaxError: unexpected EOF',
            'error_classification': {
                'primary_type': 'syntax_error',
                'language': 'python',
                'severity': 'high'
            },
            'file_contexts': [{
                'file': 'test.py',
                'error_line': 3,
                'file_type': 'python',
                'context_lines': [
                    {'line_number': 3, 'content': '    print("Hello, World!"', 'is_error_line': True}
                ]
            }],
            'repository_info': {'type': 'python'}
        }
        
        prompt = self.solver._create_solution_prompt(context, True, True)
        
        self.assertIn('SyntaxError: unexpected EOF', prompt)
        self.assertIn('test.py', prompt)
        self.assertIn('Root Cause Analysis', prompt)
        self.assertIn('Code Fixes', prompt)
    
    def test_parse_ai_response(self):
        """Test AI response parsing."""
        ai_response = """
        # Root Cause Analysis
        This error is caused by missing parentheses.
        
        # Code Fixes
        Add the missing closing parenthesis.
        
        # Step-by-Step Solution
        1. Locate line 3
        2. Add closing parenthesis
        3. Test the fix
        """
        
        parsed = self.solver._parse_ai_response(ai_response)
        
        self.assertIn('root_cause', parsed)
        self.assertIn('code_fixes', parsed)
        self.assertIn('step_by_step', parsed)
    
    def test_generate_template_solutions(self):
        """Test template-based solution generation."""
        analysis_result = {
            'classification': {
                'primary_type': 'syntax_error',
                'is_syntax_error': True,
                'language': 'python'
            }
        }
        
        template_solutions = self.solver._generate_template_solutions(analysis_result)
        
        self.assertEqual(template_solutions['error_type'], 'syntax_error')
        self.assertEqual(template_solutions['priority'], 'high')
        self.assertIn('common_fixes', template_solutions)
        self.assertIn('quick_checks', template_solutions)
    
    def test_generate_quick_checks(self):
        """Test quick checks generation."""
        classification = {
            'is_syntax_error': True,
            'language': 'python'
        }
        
        checks = self.solver._generate_quick_checks(classification)
        
        self.assertGreater(len(checks), 0)
        self.assertTrue(any('parentheses' in check.lower() for check in checks))
        self.assertTrue(any('python' in check.lower() for check in checks))
    
    def test_generate_debugging_steps(self):
        """Test debugging steps generation."""
        classification = {
            'is_syntax_error': True,
            'language': 'python'
        }
        
        steps = self.solver._generate_debugging_steps(classification)
        
        self.assertGreater(len(steps), 0)
        self.assertTrue(any('error message' in step.lower() for step in steps))
        self.assertTrue(any('syntax' in step.lower() for step in steps))
    
    def test_generate_recommended_actions(self):
        """Test recommended actions generation."""
        analysis_result = {
            'classification': {'is_syntax_error': True},
            'severity': 'high'
        }
        ai_solutions = {'success': True, 'parsed_solutions': {'step_by_step': ['Step 1', 'Step 2']}}
        
        actions = self.solver._generate_recommended_actions(analysis_result, ai_solutions)
        
        self.assertGreater(len(actions), 0)
        self.assertTrue(any(action['priority'] == 'immediate' for action in actions))
    
    def test_generate_prevention_tips(self):
        """Test prevention tips generation."""
        analysis_result = {
            'classification': {
                'is_syntax_error': True,
                'language': 'python'
            }
        }
        
        tips = self.solver._generate_prevention_tips(analysis_result)
        
        self.assertGreater(len(tips), 0)
        self.assertTrue(any('syntax highlighting' in tip.lower() for tip in tips))
    
    def test_generate_helpful_resources(self):
        """Test helpful resources generation."""
        analysis_result = {
            'classification': {
                'language': 'python',
                'is_syntax_error': True
            }
        }
        
        resources = self.solver._generate_helpful_resources(analysis_result)
        
        self.assertGreater(len(resources), 0)
        self.assertTrue(any('python' in resource['title'].lower() for resource in resources))
        self.assertTrue(all('url' in resource for resource in resources))
    
    @patch('error_solver.anthropic_api')
    def test_solve_error_integration(self, mock_anthropic):
        """Test complete error solving integration."""
        # Mock the anthropic API response
        mock_anthropic.send_prompt.return_value = {
            'success': True,
            'content': 'This is a comprehensive solution...',
            'token_count': 200
        }
        
        error_message = 'SyntaxError: unexpected EOF while parsing'
        
        result = self.solver.solve_error(error_message)
        
        self.assertTrue(result['success'])
        self.assertIn('error_analysis', result)
        self.assertIn('ai_solutions', result)
        self.assertIn('template_solutions', result)
        self.assertIn('recommended_actions', result)
        self.assertIn('prevention_tips', result)
        self.assertIn('resources', result)


class TestErrorSolverIntegration(unittest.TestCase):
    """Integration tests for the complete error solving workflow."""
    
    def setUp(self):
        """Set up test environment with a more complex repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create a more complex repository structure
        self.create_complex_repository()
        
        self.analyzer = ErrorAnalyzer(str(self.repo_path))
        self.solver = ErrorSolver(str(self.repo_path))
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_complex_repository(self):
        """Create a complex repository for integration testing."""
        # Main Python module
        main_py = self.repo_path / "main.py"
        main_py.write_text("""
import requests
from utils import helper_function

def main():
    data = helper_function()
    response = requests.get("https://api.example.com")
    print(response.json())

if __name__ == "__main__":
    main()
""")
        
        # Utils module with error
        utils_py = self.repo_path / "utils.py"
        utils_py.write_text("""
def helper_function():
    return {"key": "value"

def another_function():
    x = undefined_variable
    return x
""")
        
        # JavaScript file
        js_file = self.repo_path / "script.js"
        js_file.write_text("""
function processData(data) {
    if (data.length > 0) {
        return data.map(item => item.value);
    }
    return [];
}

// Error: missing variable declaration
result = processData(someData);
console.log(result);
""")
        
        # Requirements file
        requirements = self.repo_path / "requirements.txt"
        requirements.write_text("""
requests==2.28.1
flask==2.2.2
""")
    
    def test_end_to_end_python_syntax_error(self):
        """Test end-to-end workflow for Python syntax error."""
        error_message = 'File "utils.py", line 2, in helper_function\n    return {"key": "value"\nSyntaxError: unexpected EOF while parsing'
        
        # Analyze error
        analysis_result = self.analyzer.analyze_error(error_message)
        self.assertTrue(analysis_result['success'])
        
        # Check that error was located
        self.assertGreater(len(analysis_result['locations']), 0)
        self.assertEqual(analysis_result['classification']['primary_type'], 'syntax_error')
        
        # Check context extraction
        self.assertGreater(len(analysis_result['context']), 0)
        context = analysis_result['context'][0]
        self.assertEqual(context['error_line'], 2)
        self.assertIn('utils.py', context['file_path'])
    
    @patch('error_solver.anthropic_api')
    def test_end_to_end_with_ai_solutions(self, mock_anthropic):
        """Test end-to-end workflow with AI solution generation."""
        # Mock AI response
        mock_anthropic.send_prompt.return_value = {
            'success': True,
            'content': '''
            # Root Cause Analysis
            This is a syntax error caused by missing closing brace in dictionary definition.
            
            # Code Fixes
            Add the missing closing brace on line 2.
            
            # Step-by-Step Solution
            1. Open utils.py file
            2. Go to line 2
            3. Add closing brace after "value"
            4. Save and test
            ''',
            'token_count': 180
        }
        
        error_message = 'File "utils.py", line 2\nSyntaxError: unexpected EOF while parsing'
        
        # Solve error with AI
        solution_result = self.solver.solve_error(error_message)
        
        self.assertTrue(solution_result['success'])
        self.assertIn('error_analysis', solution_result)
        self.assertIn('ai_solutions', solution_result)
        
        # Check AI solutions
        ai_solutions = solution_result['ai_solutions']
        self.assertTrue(ai_solutions['success'])
        self.assertIn('parsed_solutions', ai_solutions)
        
        # Check template solutions
        template_solutions = solution_result['template_solutions']
        self.assertEqual(template_solutions['priority'], 'high')
        self.assertIn('common_fixes', template_solutions)
    
    def test_multiple_error_types(self):
        """Test handling of multiple different error types."""
        error_messages = [
            'SyntaxError: unexpected EOF while parsing',
            'NameError: name "undefined_variable" is not defined',
            'ImportError: No module named "nonexistent_module"',
            'ReferenceError: someData is not defined'
        ]
        
        for error_message in error_messages:
            with self.subTest(error_message=error_message):
                result = self.analyzer.analyze_error(error_message)
                self.assertTrue(result['success'])
                self.assertIn('classification', result)
                self.assertIn('severity', result)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestErrorAnalyzer))
    test_suite.addTest(unittest.makeSuite(TestErrorSolver))
    test_suite.addTest(unittest.makeSuite(TestErrorSolverIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)