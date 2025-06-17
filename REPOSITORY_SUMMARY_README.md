# Repository Summary Generator

A comprehensive tool for automatically generating detailed repository summaries using AI analysis. This tool integrates with the existing Noutai system to provide intelligent project documentation.

## Features

- **Automated Analysis**: Scans project structure, files, and documentation
- **AI-Powered Summaries**: Uses Claude AI to generate comprehensive summaries
- **Web Interface**: Integrated with the existing web application
- **CLI Support**: Command-line interface for standalone usage
- **Fallback Generation**: Works even without AI when needed
- **Multiple Output Formats**: Supports various output options

## Components

### Core Module: `repository_summary_generator.py`

The main class `RepositorySummaryGenerator` provides:

- Project structure analysis
- Key file content extraction
- AI prompt generation
- Summary generation (with AI or fallback)
- File operations (save/load)

### CLI Script: `generate_summary.py`

Command-line interface for generating summaries:

```bash
# Generate summary for current directory
python generate_summary.py

# Generate for specific repository
python generate_summary.py --repo-path /path/to/repo

# Custom output filename
python generate_summary.py --output my_summary.txt

# Verbose logging
python generate_summary.py --verbose

# Force overwrite existing file
python generate_summary.py --force
```

### Web Integration

#### API Endpoints

- `POST /api/repository/summary` - Generate new summary
- `GET /api/repository/summary` - Retrieve existing summary

#### Frontend Components

- `static/js/repository-summary.js` - JavaScript functionality
- `templates/components/repository_summary.html` - HTML component

## Usage

### Web Interface

1. Navigate to the repository summary section in the web application
2. Click "Generate Summary" to create a new summary
3. Use "Refresh" to reload existing summary
4. Use "Download" to save summary locally

### Command Line

```bash
# Basic usage
python generate_summary.py

# With options
python generate_summary.py --repo-path . --output repo_summary.txt --verbose
```

### Programmatic Usage

```python
from repository_summary_generator import RepositorySummaryGenerator

# Initialize generator
generator = RepositorySummaryGenerator("/path/to/repo")

# Generate and save summary
success = generator.generate_and_save_summary("summary.txt")

# Or get summary content
summary_content = generator.generate_repository_summary()
```

## Configuration

The generator automatically detects and analyzes:

- **Code Files**: `.py`, `.js`, `.html`, `.css`, etc.
- **Documentation**: `.md`, `.txt` files
- **Configuration**: `.json`, `.yml`, `.yaml`, `.ini`, etc.

### Skipped Items

- **Directories**: `__pycache__`, `.git`, `.vscode`, `node_modules`, etc.
- **Files**: `.gitignore`, `.DS_Store`, `requirements.txt`, etc.

## AI Integration

The generator integrates with the existing Anthropic API system:

- Uses Claude models for intelligent analysis
- Includes project context and structure
- Generates comprehensive, well-formatted summaries
- Falls back to basic summaries if AI is unavailable

## Output Format

Generated summaries include:

1. **Project Overview** - Description and purpose
2. **Architecture** - Main components and relationships
3. **Technology Stack** - Frameworks and tools used
4. **File Structure** - Directory and file organization
5. **Functionalities** - Key features and capabilities
6. **Configuration** - Important settings and options
7. **Dependencies** - External libraries and services
8. **Development** - Setup and development information
9. **API Endpoints** - If applicable
10. **Database Schema** - If applicable

## Testing

Run the test suite to verify functionality:

```bash
python test_repository_summary.py
```

The test suite covers:
- Project structure analysis
- Key file reading
- Prompt generation
- Fallback summary generation
- File operations
- Full generation process

## Error Handling

The generator includes robust error handling:

- **File Access Errors**: Graceful handling of permission issues
- **AI Service Errors**: Automatic fallback to basic summaries
- **Network Issues**: Timeout and retry logic
- **Invalid Input**: Validation and user-friendly error messages

## Integration with Existing System

The repository summary generator integrates seamlessly with:

- **Anthropic API**: Uses existing AI configuration
- **Authentication**: Respects user permissions
- **CSRF Protection**: Includes security tokens
- **Logging**: Uses application logging system
- **Error Handling**: Consistent with application patterns

## Customization

### File Types

Modify `code_extensions` in the generator class to include additional file types:

```python
self.code_extensions = {
    '.py', '.js', '.html', '.css', '.txt', '.md', 
    '.json', '.yml', '.yaml', '.sh', '.bat', '.sql'
}
```

### Skip Patterns

Adjust `skip_dirs` and `skip_files` to change what gets analyzed:

```python
self.skip_dirs = {
    '__pycache__', '.git', '.vscode', 'node_modules'
}
```

### AI Parameters

Customize AI generation parameters:

```python
response = self.anthropic_api.send_prompt(
    prompt=prompt,
    model_id="claude-3-5-sonnet-20241022",
    temperature=0.3,
    max_tokens=4000
)
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure read access to repository files
2. **AI Service Unavailable**: Generator will use fallback mode
3. **Large Repositories**: May take longer to analyze
4. **Memory Issues**: Large files are automatically truncated

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python generate_summary.py --verbose
```

Or in code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements:

- **Incremental Updates**: Only analyze changed files
- **Custom Templates**: User-defined summary formats
- **Multiple Languages**: Support for different output languages
- **Integration Hooks**: Webhooks for automated generation
- **Caching**: Cache analysis results for faster regeneration

## Contributing

When contributing to the repository summary generator:

1. Run the test suite before submitting changes
2. Update documentation for new features
3. Follow existing code style and patterns
4. Test both AI and fallback modes
5. Verify web interface integration

## License

This component is part of the Noutai project and follows the same licensing terms.