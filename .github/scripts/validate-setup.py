#!/usr/bin/env python3
"""
GitHub Actions Setup Validation Script
Checks if all required files and configurations are in place
"""

import os
import sys
import yaml
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (missing)")
        return False

def check_workflow_syntax(filepath):
    """Validate YAML syntax in workflow files"""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load(f)
        print(f"✅ YAML syntax valid: {filepath}")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in {filepath}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating GitHub Actions CI/CD Setup...\n")
    
    all_good = True
    
    # Check required workflow files
    workflows = [
        ('.github/workflows/ci.yml', 'Main CI/CD workflow'),
        ('.github/workflows/security.yml', 'Security workflow'),
        ('.github/dependabot.yml', 'Dependabot configuration')
    ]
    
    for filepath, description in workflows:
        if not check_file_exists(filepath, description):
            all_good = False
        elif filepath.endswith('.yml'):
            if not check_workflow_syntax(filepath):
                all_good = False
    
    # Check documentation files
    docs = [
        ('.github/SETUP.md', 'Setup documentation'),
        ('.github/workflows/README.md', 'Workflow documentation'),
        ('.github/env.example', 'Environment template')
    ]
    
    for filepath, description in docs:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check test runner script
    if not check_file_exists('.github/scripts/run-tests.sh', 'Test runner script'):
        all_good = False
    elif not os.access('.github/scripts/run-tests.sh', os.X_OK):
        print("❌ Test runner script is not executable")
        all_good = False
    else:
        print("✅ Test runner script is executable")
    
    # Check test directories
    test_dirs = [
        ('cads/tests', 'CADS test directory'),
        ('visuals/tests', 'Visuals test directory')
    ]
    
    for dirpath, description in test_dirs:
        if not Path(dirpath).is_dir():
            print(f"❌ {description}: {dirpath} (missing)")
            all_good = False
        else:
            test_files = list(Path(dirpath).glob('test_*.py'))
            print(f"✅ {description}: {len(test_files)} test files found")
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 All CI/CD setup validation checks passed!")
        print("\nNext steps:")
        print("1. Configure GitHub secrets (see .github/SETUP.md)")
        print("2. Push to main branch to trigger first CI run")
        print("3. Monitor workflow execution in GitHub Actions tab")
        return 0
    else:
        print("⚠️  Some validation checks failed!")
        print("Please fix the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())