#!/usr/bin/env python3
"""
System Integrity Verification Script
Automated checks to verify system state after reorganization changes.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a critical file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - MISSING")
        return False

def check_directory_structure():
    """Verify core directory structure is intact."""
    print("\n🔍 Checking Directory Structure...")
    
    required_dirs = [
        ("cads/", "Core data processing pipeline"),
        ("visuals/public/", "Visualization dashboard"),
        ("database/schema/", "Database schema definitions"),
        ("scripts/migration/", "Database migration scripts"),
        ("scripts/processing/", "Data processing scripts"),
        ("scripts/utilities/", "Utility scripts"),
        ("data/processed/", "Processed data storage"),
        ("tests/database/", "Database tests"),
        ("tests/visualization/", "Visualization tests"),
        ("docs/setup/", "Setup documentation")
    ]
    
    all_good = True
    for dir_path, description in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✅ {description}: {dir_path}")
        else:
            print(f"❌ {description}: {dir_path} - MISSING")
            all_good = False
    
    return all_good

def check_critical_files():
    """Verify critical files are present."""
    print("\n🔍 Checking Critical Files...")
    
    critical_files = [
        ("cads/data_loader.py", "Core data processing module"),
        ("cads/process_data.py", "ML pipeline orchestration"),
        ("visuals/public/app.js", "Visualization application"),
        ("visuals/public/index.html", "Web interface"),
        ("database/schema/create_cads_tables.sql", "Database schema"),
        ("scripts/migration/execute_cads_migration.py", "Database migration"),
        (".github/workflows/ci.yml", "CI/CD configuration"),
        ("requirements.txt", "Root Python dependencies"),
        ("cads/requirements.txt", "CADS Python dependencies"),
        ("vercel.json", "Deployment configuration")
    ]
    
    all_good = True
    for filepath, description in critical_files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    return all_good

def check_data_files():
    """Verify data files are accessible."""
    print("\n🔍 Checking Data Files...")
    
    data_files = [
        ("data/processed/visualization-data.json", "Main visualization dataset"),
        ("data/processed/cluster_themes.json", "Cluster themes"),
        ("data/processed/clustering_results.json", "Clustering results"),
        ("visuals/public/data/visualization-data.json", "Web visualization data")
    ]
    
    all_good = True
    for filepath, description in data_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                print(f"✅ {description}: {filepath} ({len(data)} items)")
            except json.JSONDecodeError:
                print(f"⚠️  {description}: {filepath} - INVALID JSON")
                all_good = False
            except Exception as e:
                print(f"❌ {description}: {filepath} - ERROR: {e}")
                all_good = False
        else:
            print(f"❌ {description}: {filepath} - MISSING")
            all_good = False
    
    return all_good

def check_python_imports():
    """Verify Python modules can be imported."""
    print("\n🔍 Checking Python Imports...")
    
    modules_to_test = [
        ("cads.data_loader", "DataProcessor class"),
        ("tests.conftest", "Test configuration"),
        ("tests.fixtures.test_helpers", "Test helpers")
    ]
    
    all_good = True
    original_path = sys.path.copy()
    
    try:
        # Add current directory to path for imports
        sys.path.insert(0, os.getcwd())
        
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ {description}: {module_name}")
            except ImportError as e:
                print(f"❌ {description}: {module_name} - IMPORT ERROR: {e}")
                all_good = False
            except Exception as e:
                print(f"⚠️  {description}: {module_name} - ERROR: {e}")
                all_good = False
    finally:
        sys.path = original_path
    
    return all_good

def check_git_status():
    """Check git repository status."""
    print("\n🔍 Checking Git Status...")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️  Git repository has uncommitted changes:")
            print(result.stdout)
        else:
            print("✅ Git repository is clean")
        
        # Check for untracked files that might be important
        untracked = [line for line in result.stdout.split('\n') 
                    if line.startswith('??') and not line.endswith('.pyc')]
        
        if untracked:
            print("📝 Untracked files detected:")
            for line in untracked:
                print(f"   {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git status check failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Git not found or not in a git repository")
        return False

def run_quick_tests():
    """Run a subset of tests to verify basic functionality."""
    print("\n🔍 Running Quick Functionality Tests...")
    
    test_commands = [
        (["python3", "-m", "pytest", "tests/test_project_structure.py", "-q"], 
         "Project structure validation"),
        (["python3", "-c", "import cads.data_loader; print('DataProcessor import OK')"], 
         "Core module import test")
    ]
    
    all_good = True
    for cmd, description in test_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=30, check=True)
            print(f"✅ {description}: PASSED")
        except subprocess.CalledProcessError as e:
            print(f"❌ {description}: FAILED")
            print(f"   Error: {e.stderr.strip()}")
            all_good = False
        except subprocess.TimeoutExpired:
            print(f"❌ {description}: TIMEOUT")
            all_good = False
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")
            all_good = False
    
    return all_good

def main():
    """Run complete system integrity verification."""
    print("🔧 CADS System Integrity Verification")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Critical Files", check_critical_files),
        ("Data Files", check_data_files),
        ("Python Imports", check_python_imports),
        ("Git Status", check_git_status),
        ("Quick Tests", run_quick_tests)
    ]
    
    results = {}
    overall_status = True
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            results[check_name] = result
            if not result:
                overall_status = False
        except Exception as e:
            print(f"❌ {check_name}: EXCEPTION - {e}")
            results[check_name] = False
            overall_status = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
    
    print("\n" + "=" * 50)
    if overall_status:
        print("🎉 SYSTEM INTEGRITY: ALL CHECKS PASSED")
        print("✅ System is ready for continued operation")
        return 0
    else:
        print("⚠️  SYSTEM INTEGRITY: ISSUES DETECTED")
        print("❌ Review failed checks and consider rollback if critical")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)