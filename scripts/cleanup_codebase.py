#!/usr/bin/env python3
"""
CADS Research Visualization - Codebase Cleanup Script

This script consolidates data directories and removes duplication
while preserving unique files and maintaining production functionality.
"""

import os
import shutil
import json
from pathlib import Path


def backup_current_state():
    """Create a backup of current state before cleanup"""
    print("📦 Creating backup of current state...")
    
    backup_dir = Path("backup_before_cleanup")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    backup_dir.mkdir()
    
    # Backup data directories
    dirs_to_backup = [
        "cads/data",
        "visuals/data", 
        "visuals/models",
        "cads/models"
    ]
    
    for dir_path in dirs_to_backup:
        src = Path(dir_path)
        if src.exists():
            dst = backup_dir / dir_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            print(f"   ✅ Backed up {dir_path}")
    
    print(f"📦 Backup created in: {backup_dir}")


def create_models_directory():
    """Create centralized models directory"""
    models_dir = Path("data/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created centralized models directory: {models_dir}")


def move_unique_files():
    """Move unique files from cads/data to data/processed"""
    print("🔄 Moving unique files to centralized location...")
    
    # Ensure target directory exists
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Move unique files from cads/data
    unique_files = [
        "cads/data/umap_coordinates.json",
        "cads/data/processing_summary.json"
    ]
    
    for file_path in unique_files:
        src = Path(file_path)
        if src.exists():
            dst = processed_dir / src.name
            shutil.move(str(src), str(dst))
            print(f"   ✅ Moved {src} → {dst}")
        else:
            print(f"   ⚠️  File not found: {src}")
    
    # Move backup files if they exist
    backup_files = [
        "cads/data/clustering_results.json.backup",
        "cads/data/umap_coordinates.json.backup"
    ]
    
    for file_path in backup_files:
        src = Path(file_path)
        if src.exists():
            dst = processed_dir / src.name
            shutil.move(str(src), str(dst))
            print(f"   ✅ Moved backup {src} → {dst}")


def consolidate_models():
    """Consolidate model files into data/models"""
    print("🤖 Consolidating model files...")
    
    models_dir = Path("data/models")
    
    # Model directories to consolidate
    model_sources = [
        "cads/models",
        "visuals/models"
    ]
    
    for source_dir in model_sources:
        src_path = Path(source_dir)
        if src_path.exists():
            for model_file in src_path.glob("*.pkl"):
                dst = models_dir / model_file.name
                if not dst.exists():
                    shutil.move(str(model_file), str(dst))
                    print(f"   ✅ Moved {model_file} → {dst}")
                else:
                    print(f"   ⚠️  Model already exists: {dst}")
                    # Keep the newer file
                    if model_file.stat().st_mtime > dst.stat().st_mtime:
                        shutil.move(str(model_file), str(dst))
                        print(f"   ✅ Updated with newer version: {dst}")


def remove_duplicate_directories():
    """Remove duplicate data directories"""
    print("🗑️  Removing duplicate directories...")
    
    dirs_to_remove = [
        "cads/data",
        "cads/models", 
        "visuals/data",
        "visuals/models"
    ]
    
    for dir_path in dirs_to_remove:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            print(f"   ✅ Removed {dir_path}")
        else:
            print(f"   ⚠️  Directory not found: {dir_path}")


def update_gitignore():
    """Update .gitignore to prevent future duplication"""
    print("📝 Updating .gitignore...")
    
    gitignore_additions = [
        "",
        "# Prevent data duplication",
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
        "",
        "# Centralized data - don't duplicate",
        "cads/data/",
        "cads/models/",
        "visuals/data/",
        "visuals/models/",
        "",
        "# Keep production data",
        "!visuals/public/data/",
    ]
    
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            current_content = f.read()
    else:
        current_content = ""
    
    # Check if our additions are already there
    if "# Prevent data duplication" not in current_content:
        with open(gitignore_path, 'a') as f:
            f.write('\n'.join(gitignore_additions))
        print("   ✅ Updated .gitignore")
    else:
        print("   ⚠️  .gitignore already updated")


def create_data_sync_script():
    """Create script to sync data to production"""
    print("🔄 Creating data sync script...")
    
    sync_script = '''#!/usr/bin/env python3
"""
Data sync script - copies processed data to production directory
Run this after processing pipeline to update web data
"""

import shutil
from pathlib import Path

def sync_data_to_production():
    """Sync data/processed to visuals/public/data"""
    
    source_dir = Path("data/processed")
    target_dir = Path("visuals/public/data")
    
    if not source_dir.exists():
        print("❌ Source directory not found: data/processed")
        return False
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to sync
    files_to_sync = [
        "visualization-data.json",
        "visualization-data.json.gz",
        "cluster_themes.json", 
        "cluster_themes.json.gz",
        "clustering_results.json",
        "clustering_results.json.gz"
    ]
    
    # Also sync search index
    search_source = Path("data/search")
    if search_source.exists():
        for search_file in search_source.glob("search-index.json*"):
            dst = target_dir / search_file.name
            shutil.copy2(search_file, dst)
            print(f"✅ Synced {search_file} → {dst}")
    
    # Sync main data files
    for filename in files_to_sync:
        src = source_dir / filename
        if src.exists():
            dst = target_dir / filename
            shutil.copy2(src, dst)
            print(f"✅ Synced {src} → {dst}")
        else:
            print(f"⚠️  File not found: {src}")
    
    print("🎉 Data sync completed!")
    return True

if __name__ == "__main__":
    sync_data_to_production()
'''
    
    with open("sync_data_to_production.py", "w") as f:
        f.write(sync_script)
    
    # Make it executable
    os.chmod("sync_data_to_production.py", 0o755)
    print("   ✅ Created sync_data_to_production.py")


def verify_cleanup():
    """Verify the cleanup was successful"""
    print("🔍 Verifying cleanup...")
    
    # Check that centralized directories exist
    required_dirs = [
        "data/processed",
        "data/models",
        "visuals/public/data"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            file_count = len(list(path.glob("*")))
            print(f"   ✅ {dir_path} exists with {file_count} files")
        else:
            print(f"   ❌ Missing required directory: {dir_path}")
    
    # Check that duplicate directories are gone
    should_not_exist = [
        "cads/data",
        "cads/models",
        "visuals/data", 
        "visuals/models"
    ]
    
    for dir_path in should_not_exist:
        path = Path(dir_path)
        if not path.exists():
            print(f"   ✅ Removed duplicate directory: {dir_path}")
        else:
            print(f"   ⚠️  Directory still exists: {dir_path}")
    
    # Check unique files were moved
    unique_files = [
        "data/processed/umap_coordinates.json",
        "data/processed/processing_summary.json"
    ]
    
    for file_path in unique_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ Unique file preserved: {file_path}")
        else:
            print(f"   ❌ Missing unique file: {file_path}")


def main():
    """Main cleanup process"""
    print("🧹 CADS Research Visualization - Codebase Cleanup")
    print("=" * 60)
    
    # Confirm with user
    response = input("This will reorganize your data directories. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    try:
        # Step 1: Backup
        backup_current_state()
        
        # Step 2: Create centralized directories
        create_models_directory()
        
        # Step 3: Move unique files
        move_unique_files()
        
        # Step 4: Consolidate models
        consolidate_models()
        
        # Step 5: Remove duplicates
        remove_duplicate_directories()
        
        # Step 6: Update gitignore
        update_gitignore()
        
        # Step 7: Create sync script
        create_data_sync_script()
        
        # Step 8: Verify
        verify_cleanup()
        
        print("\n" + "=" * 60)
        print("🎉 Cleanup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Test that cads/process_data.py still works")
        print("2. Update any hardcoded paths in your code")
        print("3. Run sync_data_to_production.py to update web data")
        print("4. Remove backup_before_cleanup/ when satisfied")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        print("💡 Restore from backup_before_cleanup/ if needed")


if __name__ == "__main__":
    main()