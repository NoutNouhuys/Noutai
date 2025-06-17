#!/usr/bin/env python3
"""
Test script for Repository Summary Generator

This script tests the repository summary generator functionality
to ensure it works correctly before integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repository_summary_generator import RepositorySummaryGenerator


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_project_structure_analysis():
    """Test the project structure analysis functionality."""
    print("🔍 Testing project structure analysis...")
    
    generator = RepositorySummaryGenerator(".")
    structure = generator.analyze_project_structure()
    
    print(f"✅ Found {structure['total_files']} files in {structure['total_directories']} directories")
    print(f"✅ Code files: {len(structure['code_files'])}")
    print(f"✅ Documentation files: {len(structure['documentation_files'])}")
    print(f"✅ Configuration files: {len(structure['config_files'])}")
    
    # Print file types
    print("📊 File types:")
    for ext, count in sorted(structure['file_types'].items()):
        print(f"   {ext or 'no extension'}: {count}")
    
    return structure


def test_key_files_reading():
    """Test reading of key project files."""
    print("\n📖 Testing key files reading...")
    
    generator = RepositorySummaryGenerator(".")
    key_files = generator.read_key_files()
    
    print(f"✅ Read {len(key_files)} key files:")
    for filename, content in key_files.items():
        content_length = len(content)
        print(f"   {filename}: {content_length:,} characters")
    
    return key_files


def test_prompt_generation():
    """Test the AI prompt generation."""
    print("\n🤖 Testing AI prompt generation...")
    
    generator = RepositorySummaryGenerator(".")
    structure = generator.analyze_project_structure()
    key_files = generator.read_key_files()
    
    prompt = generator.generate_summary_prompt(structure, key_files)
    prompt_length = len(prompt)
    
    print(f"✅ Generated prompt with {prompt_length:,} characters")
    
    # Show a preview of the prompt
    preview_length = 500
    if prompt_length > preview_length:
        print(f"📝 Prompt preview (first {preview_length} chars):")
        print(prompt[:preview_length] + "...")
    else:
        print("📝 Full prompt:")
        print(prompt)
    
    return prompt


def test_fallback_summary():
    """Test the fallback summary generation."""
    print("\n🔄 Testing fallback summary generation...")
    
    generator = RepositorySummaryGenerator(".")
    structure = generator.analyze_project_structure()
    key_files = generator.read_key_files()
    
    fallback_summary = generator._generate_fallback_summary(structure, key_files)
    summary_length = len(fallback_summary)
    
    print(f"✅ Generated fallback summary with {summary_length:,} characters")
    
    # Show a preview
    preview_length = 300
    if summary_length > preview_length:
        print(f"📝 Summary preview (first {preview_length} chars):")
        print(fallback_summary[:preview_length] + "...")
    else:
        print("📝 Full fallback summary:")
        print(fallback_summary)
    
    return fallback_summary


def test_file_operations():
    """Test file save and load operations."""
    print("\n💾 Testing file operations...")
    
    test_content = """# Test Repository Summary

This is a test summary to verify file operations work correctly.

## Test Sections
- Project Overview
- File Structure
- Dependencies

Generated for testing purposes.
"""
    
    generator = RepositorySummaryGenerator(".")
    test_filename = "test_summary.txt"
    
    # Test saving
    save_success = generator.save_summary(test_content, test_filename)
    if save_success:
        print(f"✅ Successfully saved test summary to {test_filename}")
    else:
        print(f"❌ Failed to save test summary")
        return False
    
    # Test file exists
    test_path = Path(".") / test_filename
    if test_path.exists():
        print(f"✅ Test file exists: {test_path}")
        
        # Read back and verify
        with open(test_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("✅ File content matches original")
        else:
            print("❌ File content doesn't match original")
            return False
        
        # Clean up
        test_path.unlink()
        print("✅ Test file cleaned up")
    else:
        print(f"❌ Test file not found: {test_path}")
        return False
    
    return True


def test_full_generation():
    """Test the full summary generation process."""
    print("\n🚀 Testing full summary generation...")
    
    generator = RepositorySummaryGenerator(".")
    
    # This will use the fallback method since we don't have AI configured in test
    print("⚠️  Note: This will use fallback generation (no AI)")
    
    try:
        summary_content = generator.generate_repository_summary()
        summary_length = len(summary_content)
        
        print(f"✅ Generated summary with {summary_length:,} characters")
        
        # Show preview
        preview_length = 400
        if summary_length > preview_length:
            print(f"📝 Summary preview (first {preview_length} chars):")
            print(summary_content[:preview_length] + "...")
        
        return summary_content
        
    except Exception as e:
        print(f"❌ Failed to generate summary: {e}")
        return None


def main():
    """Run all tests."""
    print("🧪 Repository Summary Generator Test Suite")
    print("=" * 50)
    
    setup_logging()
    
    tests = [
        ("Project Structure Analysis", test_project_structure_analysis),
        ("Key Files Reading", test_key_files_reading),
        ("Prompt Generation", test_prompt_generation),
        ("Fallback Summary", test_fallback_summary),
        ("File Operations", test_file_operations),
        ("Full Generation", test_full_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result is not False and result is not None:
                print(f"✅ {test_name}: PASSED")
                results.append((test_name, True))
            else:
                print(f"❌ {test_name}: FAILED")
                results.append((test_name, False))
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 Test Results Summary")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Repository Summary Generator is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit(main())