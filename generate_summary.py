#!/usr/bin/env python3
"""
CLI Script for Repository Summary Generation

This script provides a simple command-line interface for generating repository summaries.
It can be used standalone or integrated into development workflows.
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repository_summary_generator import RepositorySummaryGenerator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate comprehensive repository summary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_summary.py                    # Generate summary for current directory
  python generate_summary.py --repo-path /path/to/repo
  python generate_summary.py --output my_summary.txt --verbose
        """
    )
    
    parser.add_argument(
        "--repo-path", 
        default=".", 
        help="Path to repository (default: current directory)"
    )
    parser.add_argument(
        "--output", 
        default="repository_summary.txt", 
        help="Output filename (default: repository_summary.txt)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing summary file without confirmation"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate repository path
        repo_path = Path(args.repo_path).resolve()
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return 1
        
        if not repo_path.is_dir():
            logger.error(f"Repository path is not a directory: {repo_path}")
            return 1
        
        # Check if output file exists
        output_path = repo_path / args.output
        if output_path.exists() and not args.force:
            response = input(f"Output file '{output_path}' already exists. Overwrite? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                logger.info("Operation cancelled by user")
                return 0
        
        # Generate summary
        logger.info(f"Generating repository summary for: {repo_path}")
        logger.info(f"Output file: {output_path}")
        
        generator = RepositorySummaryGenerator(str(repo_path))
        success = generator.generate_and_save_summary(args.output)
        
        if success:
            print(f"\n✅ Repository summary generated successfully!")
            print(f"📄 Output file: {output_path}")
            
            # Show file size
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"📊 File size: {file_size:,} bytes")
            
            return 0
        else:
            print("\n❌ Failed to generate repository summary")
            print("Check the logs above for error details")
            return 1
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())