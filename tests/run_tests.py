#!/usr/bin/env python3
"""
Test runner script for CADS Research Visualization System
Provides different test execution modes with proper output management
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print("STDERR:", result.stderr)
            if result.stdout.strip():
                print("STDOUT:", result.stdout)
            return False
    
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False
    
    return True


def run_database_tests():
    """Run database-related tests"""
    cmd = "python3 -m pytest tests/database/ -q --tb=short -m database"
    return run_command(cmd, "Database Tests")


def run_pipeline_tests():
    """Run ML pipeline tests"""
    cmd = "python3 -m pytest tests/pipeline/ -q --tb=short"
    return run_command(cmd, "ML Pipeline Tests")


def run_visualization_tests():
    """Run visualization tests"""
    cmd = "python3 -m pytest tests/visualization/ -q --tb=short -m visualization"
    return run_command(cmd, "Visualization Tests")


def run_unit_tests():
    """Run fast unit tests only"""
    cmd = "python3 -m pytest tests/ -q --tb=short -m 'not slow and not integration'"
    return run_command(cmd, "Unit Tests (Fast)")


def run_integration_tests():
    """Run integration tests"""
    cmd = "python3 -m pytest tests/ -q --tb=short -m integration"
    return run_command(cmd, "Integration Tests")


def run_all_tests():
    """Run all tests"""
    cmd = "python3 -m pytest tests/ -q --tb=short"
    return run_command(cmd, "All Tests")


def run_specific_test(test_path):
    """Run a specific test file or test"""
    cmd = f"python3 -m pytest {test_path} -v --tb=short"
    return run_command(cmd, f"Specific Test: {test_path}")


def main():
    parser = argparse.ArgumentParser(description="CADS Research Visualization Test Runner")
    parser.add_argument("--database", action="store_true", help="Run database tests only")
    parser.add_argument("--pipeline", action="store_true", help="Run pipeline tests only")
    parser.add_argument("--visualization", action="store_true", help="Run visualization tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only (fast)")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", type=str, help="Run specific test file or test")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list:
        print("📋 Available Test Categories:")
        print("  --database      : Database connection and integrity tests")
        print("  --pipeline      : ML pipeline and data processing tests")
        print("  --visualization : Frontend and visualization tests")
        print("  --unit          : Fast unit tests only")
        print("  --integration   : Slow integration tests")
        print("  --all           : All tests")
        print("  --test <path>   : Specific test file or test")
        return
    
    success = True
    
    if args.database:
        success &= run_database_tests()
    elif args.pipeline:
        success &= run_pipeline_tests()
    elif args.visualization:
        success &= run_visualization_tests()
    elif args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.test:
        success &= run_specific_test(args.test)
    elif args.all:
        success &= run_all_tests()
    else:
        # Default: run unit tests (fast)
        print("🚀 Running default test suite (unit tests)")
        print("Use --help to see all options")
        success &= run_unit_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()