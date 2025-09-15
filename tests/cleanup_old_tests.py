#!/usr/bin/env python3
"""
Cleanup script to remove old duplicate test files
Consolidates tests into the new unified test structure
"""

import os
import shutil
from pathlib import Path


def cleanup_old_tests():
    """Remove old duplicate test files"""
    print("🧹 Cleaning up old duplicate test files...")
    
    # Directories with old tests to clean up
    old_test_dirs = [
        Path("cads/tests"),
        Path("visuals/tests")
    ]
    
    # Files to preserve (have unique functionality)
    preserve_files = [
        "test_local.py"  # Has unique local server functionality
    ]
    
    removed_files = []
    preserved_files = []
    
    for old_dir in old_test_dirs:
        if old_dir.exists():
            print(f"\n📂 Processing {old_dir}...")
            
            for test_file in old_dir.glob("test_*.py"):
                if test_file.name in preserve_files:
                    print(f"   ⚠️  Preserving {test_file.name} (unique functionality)")
                    preserved_files.append(test_file)
                else:
                    print(f"   🗑️  Removing {test_file.name} (consolidated)")
                    test_file.unlink()
                    removed_files.append(test_file)
            
            # Remove empty test directories
            remaining_files = list(old_dir.glob("*"))
            if len(remaining_files) == 0:
                print(f"   📁 Removing empty directory {old_dir}")
                old_dir.rmdir()
            elif len(remaining_files) == len([f for f in remaining_files if f.name in preserve_files]):
                print(f"   📁 Keeping {old_dir} (has preserved files)")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   🗑️  Removed {len(removed_files)} duplicate test files")
    print(f"   ⚠️  Preserved {len(preserved_files)} unique test files")
    
    if removed_files:
        print(f"\n📋 Removed files:")
        for file in removed_files:
            print(f"   - {file}")
    
    if preserved_files:
        print(f"\n📋 Preserved files:")
        for file in preserved_files:
            print(f"   - {file}")
    
    print(f"\n✅ Cleanup completed!")
    print(f"   📁 New unified test structure: tests/")
    print(f"   🧪 Run tests with: python tests/run_tests.py")


def create_migration_note():
    """Create a note about the test migration"""
    note_content = """# Test Structure Migration

The test suite has been consolidated and reorganized for better maintainability.

## Old Structure (Removed)
- `cads/tests/` - Duplicate tests removed
- `visuals/tests/` - Duplicate tests removed

## New Structure
- `tests/` - Unified test suite
  - `database/` - Database connection and integrity tests
  - `pipeline/` - ML pipeline and data processing tests
  - `visualization/` - Frontend and visualization tests
  - `fixtures/` - Test data and utilities

## Running Tests
```bash
# Run all tests
python tests/run_tests.py --all

# Run specific test categories
python tests/run_tests.py --database
python tests/run_tests.py --pipeline
python tests/run_tests.py --visualization

# Run fast unit tests only
python tests/run_tests.py --unit

# Run specific test
python tests/run_tests.py --test tests/database/test_connection.py
```

## Test Configuration
- `pytest.ini` - Pytest configuration
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/fixtures/` - Test data and helper utilities

## Benefits
- ✅ Eliminated duplicate tests
- ✅ Better organization by functionality
- ✅ Shared fixtures and utilities
- ✅ Proper pytest configuration
- ✅ Multiple test execution modes
- ✅ Better error handling and output
"""
    
    with open("tests/MIGRATION_NOTES.md", "w") as f:
        f.write(note_content)
    
    print("📝 Created migration notes: tests/MIGRATION_NOTES.md")


if __name__ == "__main__":
    cleanup_old_tests()
    create_migration_note()
    
    print("\n🎯 Next Steps:")
    print("1. Run tests: python tests/run_tests.py --unit")
    print("2. Check database tests: python tests/run_tests.py --database")
    print("3. Review migration notes: tests/MIGRATION_NOTES.md")