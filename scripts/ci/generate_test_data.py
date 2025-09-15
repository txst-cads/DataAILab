#!/usr/bin/env python3
"""
Generate proper test data for CI environment
Resolves compression ratio and missing file issues in GitHub Actions
"""

import json
import gzip
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

from tests.fixtures.test_helpers import TestDataGenerator


def create_directories():
    """Create required data directories"""
    directories = [
        "data/processed",
        "data/search", 
        "visuals/public/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def generate_visualization_data():
    """Generate realistic visualization data for testing"""
    generator = TestDataGenerator()
    
    # Generate substantial test data (not minimal) for proper compression
    viz_data = generator.generate_visualization_data(num_works=500)
    
    # Add more realistic data structure
    viz_data.update({
        "metadata": {
            "total_works": len(viz_data["works"]),
            "total_clusters": len(viz_data["clusters"]),
            "generated_for": "ci_testing",
            "version": "1.0"
        },
        "researchers": [
            {
                "id": i + 1,
                "name": f"Dr. Test Researcher {i + 1}",
                "department": "Computer Science",
                "works_count": len([w for w in viz_data["works"] if w["researcher_name"] == f"Researcher {(i % 10) + 1}"])
            }
            for i in range(10)
        ]
    })
    
    return viz_data


def generate_cluster_themes():
    """Generate cluster themes data"""
    return {
        "0": {
            "theme": "Machine Learning and AI",
            "description": "Research focused on artificial intelligence and machine learning algorithms",
            "keywords": ["machine learning", "artificial intelligence", "neural networks"],
            "color": "#FF6B6B"
        },
        "1": {
            "theme": "Software Engineering", 
            "description": "Software development methodologies and engineering practices",
            "keywords": ["software engineering", "development", "programming"],
            "color": "#4ECDC4"
        },
        "2": {
            "theme": "Data Science and Analytics",
            "description": "Data analysis, visualization, and statistical methods",
            "keywords": ["data science", "analytics", "statistics"],
            "color": "#45B7D1"
        },
        "3": {
            "theme": "Computer Systems and Networks",
            "description": "Computer systems, networking, and distributed computing",
            "keywords": ["systems", "networks", "distributed computing"],
            "color": "#96CEB4"
        },
        "4": {
            "theme": "Human-Computer Interaction",
            "description": "User interface design and human-computer interaction research",
            "keywords": ["HCI", "user interface", "usability"],
            "color": "#FFEAA7"
        }
    }


def generate_clustering_results():
    """Generate clustering results data"""
    generator = TestDataGenerator()
    return generator.generate_clustering_results(num_clusters=5, num_points=500)


def generate_search_index():
    """Generate search index data"""
    viz_data = generate_visualization_data()
    
    search_index = []
    for work in viz_data["works"]:
        search_index.append({
            "id": work["id"],
            "title": work["title"],
            "researcher": work["researcher_name"],
            "year": work["year"],
            "cluster": work["cluster"],
            "content": f"{work['title']} by {work['researcher_name']} ({work['year']})",
            "searchable_text": f"{work['title']} {work['researcher_name']} {work['year']}"
        })
    
    return {"index": search_index, "total_items": len(search_index)}


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    elif hasattr(obj, 'item'):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def write_json_file(data, filepath):
    """Write JSON data to file"""
    # Convert numpy types to native Python types
    serializable_data = convert_numpy_types(data)
    
    with open(filepath, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    file_size = Path(filepath).stat().st_size
    print(f"✅ Generated {filepath} ({file_size:,} bytes)")
    return file_size


def compress_file(filepath):
    """Compress JSON file with gzip"""
    compressed_path = f"{filepath}.gz"
    
    with open(filepath, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            f_out.writelines(f_in)
    
    original_size = Path(filepath).stat().st_size
    compressed_size = Path(compressed_path).stat().st_size
    ratio = compressed_size / original_size
    
    print(f"✅ Compressed {filepath}.gz (ratio: {ratio:.3f})")
    return compressed_size, ratio


def main():
    """Main function to generate all test data"""
    print("🔧 Generating comprehensive test data for CI environment...")
    
    # Create directories
    create_directories()
    
    # Generate data
    print("\n📊 Generating visualization data...")
    viz_data = generate_visualization_data()
    
    print("🎨 Generating cluster themes...")
    cluster_themes = generate_cluster_themes()
    
    print("🔍 Generating clustering results...")
    clustering_results = generate_clustering_results()
    
    print("🔎 Generating search index...")
    search_index = generate_search_index()
    
    # File paths for data
    files_to_generate = [
        ("data/processed/visualization-data.json", viz_data),
        ("data/processed/cluster_themes.json", cluster_themes),
        ("data/processed/clustering_results.json", clustering_results),
        ("data/search/search-index.json", search_index),
        ("visuals/public/data/visualization-data.json", viz_data),
        ("visuals/public/data/cluster_themes.json", cluster_themes),
        ("visuals/public/data/clustering_results.json", clustering_results),
        ("visuals/public/data/search-index.json", search_index)
    ]
    
    print(f"\n📝 Writing {len(files_to_generate)} JSON files...")
    total_uncompressed = 0
    total_compressed = 0
    
    for filepath, data in files_to_generate:
        # Write JSON file
        file_size = write_json_file(data, filepath)
        total_uncompressed += file_size
        
        # Compress file
        compressed_size, ratio = compress_file(filepath)
        total_compressed += compressed_size
    
    # Summary
    overall_ratio = total_compressed / total_uncompressed
    print(f"\n📈 Summary:")
    print(f"   Total uncompressed: {total_uncompressed:,} bytes")
    print(f"   Total compressed: {total_compressed:,} bytes") 
    print(f"   Overall compression ratio: {overall_ratio:.3f}")
    print(f"   Space saved: {((1 - overall_ratio) * 100):.1f}%")
    
    if overall_ratio < 0.8:
        print("✅ Compression ratio is good (< 0.8)")
    else:
        print("⚠️  Compression ratio could be better")
    
    print("\n🎉 Test data generation completed successfully!")


if __name__ == "__main__":
    main()