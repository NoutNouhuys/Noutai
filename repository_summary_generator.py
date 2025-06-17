#!/usr/bin/env python3
"""
Repository Summary Generator

This module generates comprehensive repository summaries by analyzing the project structure,
code files, documentation, and project information. It integrates with the existing
Anthropic API to provide intelligent analysis and summary generation.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from anthropic_api import get_api_instance

# Setup logger
logger = logging.getLogger(__name__)


class RepositorySummaryGenerator:
    """
    Generates comprehensive repository summaries by analyzing project structure,
    code files, and documentation.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize the repository summary generator.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.anthropic_api = get_api_instance()
        
        # File extensions to analyze
        self.code_extensions = {
            '.py', '.js', '.html', '.css', '.txt', '.md', '.json', '.yml', '.yaml',
            '.sh', '.bat', '.sql', '.xml', '.ini', '.cfg', '.conf'
        }
        
        # Directories to skip
        self.skip_dirs = {
            '__pycache__', '.git', '.vscode', '.idea', 'node_modules', 
            '.pytest_cache', '.coverage', 'venv', 'env', '.env',
            'migrations', 'instance'
        }
        
        # Files to skip
        self.skip_files = {
            '.gitignore', '.DS_Store', 'Thumbs.db', '.coverage',
            'requirements.txt', 'package-lock.json'
        }
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """
        Analyze the project structure and return a comprehensive overview.
        
        Returns:
            Dictionary containing project structure analysis
        """
        structure = {
            'root_path': str(self.repo_path),
            'directories': [],
            'files': [],
            'file_types': {},
            'total_files': 0,
            'total_directories': 0,
            'code_files': [],
            'documentation_files': [],
            'config_files': []
        }
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip unwanted directories
                dirs[:] = [d for d in dirs if d not in self.skip_dirs]
                
                root_path = Path(root)
                relative_root = root_path.relative_to(self.repo_path)
                
                if relative_root != Path('.'):
                    structure['directories'].append(str(relative_root))
                    structure['total_directories'] += 1
                
                for file in files:
                    if file in self.skip_files:
                        continue
                    
                    file_path = root_path / file
                    relative_file = file_path.relative_to(self.repo_path)
                    
                    # Get file extension
                    ext = file_path.suffix.lower()
                    
                    # Count file types
                    if ext in structure['file_types']:
                        structure['file_types'][ext] += 1
                    else:
                        structure['file_types'][ext] = 1
                    
                    structure['files'].append(str(relative_file))
                    structure['total_files'] += 1
                    
                    # Categorize files
                    if ext in self.code_extensions:
                        if ext in ['.py', '.js', '.html', '.css']:
                            structure['code_files'].append(str(relative_file))
                        elif ext in ['.md', '.txt']:
                            structure['documentation_files'].append(str(relative_file))
                        elif ext in ['.json', '.yml', '.yaml', '.ini', '.cfg', '.conf']:
                            structure['config_files'].append(str(relative_file))
        
        except Exception as e:
            logger.error(f"Error analyzing project structure: {e}")
            structure['error'] = str(e)
        
        return structure
    
    def read_key_files(self) -> Dict[str, str]:
        """
        Read key project files for analysis.
        
        Returns:
            Dictionary containing content of key files
        """
        key_files = {}
        
        # Important files to read
        important_files = [
            'project_info.txt',
            'README.md',
            'app.py',
            'config.py',
            'anthropic_api.py',
            'requirements.txt',
            'package.json'
        ]
        
        for filename in important_files:
            file_path = self.repo_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Limit content size to avoid overwhelming the AI
                        if len(content) > 10000:
                            content = content[:10000] + "\n... (truncated)"
                        key_files[filename] = content
                except Exception as e:
                    logger.error(f"Error reading {filename}: {e}")
                    key_files[filename] = f"Error reading file: {e}"
        
        return key_files
    
    def generate_summary_prompt(self, structure: Dict[str, Any], key_files: Dict[str, str]) -> str:
        """
        Generate a prompt for the AI to create a repository summary.
        
        Args:
            structure: Project structure analysis
            key_files: Content of key files
            
        Returns:
            Formatted prompt for AI analysis
        """
        prompt = f"""
Analyseer deze repository en genereer een uitgebreide repository_summary.txt.

## Project Structuur:
- Totaal bestanden: {structure['total_files']}
- Totaal directories: {structure['total_directories']}
- Code bestanden: {len(structure['code_files'])}
- Documentatie bestanden: {len(structure['documentation_files'])}
- Configuratie bestanden: {len(structure['config_files'])}

## Bestandstypes:
{json.dumps(structure['file_types'], indent=2)}

## Belangrijke bestanden:
"""
        
        for filename, content in key_files.items():
            prompt += f"\n### {filename}:\n```\n{content}\n```\n"
        
        prompt += """

## Opdracht:
Genereer een uitgebreide repository_summary.txt die het volgende bevat:

1. **Project Overzicht**: Korte beschrijving van wat dit project doet
2. **Architectuur**: Hoofdcomponenten en hun relaties
3. **Technologie Stack**: Gebruikte technologieën en frameworks
4. **Bestandsstructuur**: Overzicht van belangrijke directories en bestanden
5. **Functionaliteiten**: Lijst van hoofdfunctionaliteiten
6. **Configuratie**: Belangrijke configuratie-aspecten
7. **Dependencies**: Belangrijke afhankelijkheden
8. **Development**: Informatie voor ontwikkelaars
9. **API Endpoints**: Als van toepassing
10. **Database Schema**: Als van toepassing

Maak de samenvatting uitgebreid maar wel overzichtelijk. Gebruik markdown formatting voor betere leesbaarheid.
"""
        
        return prompt
    
    def generate_repository_summary(self) -> str:
        """
        Generate a comprehensive repository summary.
        
        Returns:
            Generated repository summary content
        """
        logger.info("Starting repository summary generation...")
        
        try:
            # Analyze project structure
            logger.info("Analyzing project structure...")
            structure = self.analyze_project_structure()
            
            # Read key files
            logger.info("Reading key files...")
            key_files = self.read_key_files()
            
            # Generate prompt
            logger.info("Generating AI prompt...")
            prompt = self.generate_summary_prompt(structure, key_files)
            
            # Send to AI for analysis
            logger.info("Sending to AI for analysis...")
            response = self.anthropic_api.send_prompt(
                prompt=prompt,
                model_id="claude-3-5-sonnet-20241022",
                temperature=0.3,
                max_tokens=4000,
                include_project_info=False  # Don't include project_info to avoid circular reference
            )
            
            if response.get('success'):
                summary_content = response['message']
                logger.info("Repository summary generated successfully")
                return summary_content
            else:
                error_msg = f"AI analysis failed: {response.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return self._generate_fallback_summary(structure, key_files)
        
        except Exception as e:
            logger.error(f"Error generating repository summary: {e}")
            return self._generate_fallback_summary(structure if 'structure' in locals() else {}, 
                                                 key_files if 'key_files' in locals() else {})
    
    def _generate_fallback_summary(self, structure: Dict[str, Any], key_files: Dict[str, str]) -> str:
        """
        Generate a basic fallback summary when AI analysis fails.
        
        Args:
            structure: Project structure analysis
            key_files: Content of key files
            
        Returns:
            Basic repository summary
        """
        summary = f"""# Repository Summary

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Repository Path:** {self.repo_path}

## Project Overview
This repository contains a software project with {structure.get('total_files', 0)} files across {structure.get('total_directories', 0)} directories.

## File Structure
- **Code Files:** {len(structure.get('code_files', []))}
- **Documentation Files:** {len(structure.get('documentation_files', []))}
- **Configuration Files:** {len(structure.get('config_files', []))}

## File Types Distribution
"""
        
        for ext, count in structure.get('file_types', {}).items():
            summary += f"- {ext or 'no extension'}: {count} files\n"
        
        summary += "\n## Key Files Found\n"
        for filename in key_files.keys():
            summary += f"- {filename}\n"
        
        summary += """
## Note
This is a basic summary generated as a fallback. For a more detailed analysis, 
ensure the AI service is properly configured and accessible.
"""
        
        return summary
    
    def save_summary(self, content: str, filename: str = "repository_summary.txt") -> bool:
        """
        Save the repository summary to a file.
        
        Args:
            content: Summary content to save
            filename: Output filename
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            output_path = self.repo_path / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Repository summary saved to: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving repository summary: {e}")
            return False
    
    def generate_and_save_summary(self, filename: str = "repository_summary.txt") -> bool:
        """
        Generate and save repository summary in one operation.
        
        Args:
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            summary_content = self.generate_repository_summary()
            return self.save_summary(summary_content, filename)
        except Exception as e:
            logger.error(f"Error in generate_and_save_summary: {e}")
            return False


def main():
    """
    Main function for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate repository summary")
    parser.add_argument("--repo-path", default=".", help="Path to repository (default: current directory)")
    parser.add_argument("--output", default="repository_summary.txt", help="Output filename")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Generate summary
    generator = RepositorySummaryGenerator(args.repo_path)
    success = generator.generate_and_save_summary(args.output)
    
    if success:
        print(f"Repository summary generated successfully: {args.output}")
        return 0
    else:
        print("Failed to generate repository summary")
        return 1


if __name__ == "__main__":
    exit(main())