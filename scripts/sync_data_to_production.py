#!/usr/bin/env python3
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
