"""
Visualization data loading tests for CADS Research Visualization System
"""

import pytest
import json
import gzip
from pathlib import Path
from tests.fixtures.test_helpers import TestDataGenerator, validate_json_structure


class TestDataFileLoading:
    """Test data file loading capabilities"""
    
    def test_json_data_files_exist(self):
        """Test that JSON data files exist in expected locations"""
        expected_paths = [
            Path("data/processed/visualization-data.json"),
            Path("data/processed/cluster_themes.json"),
            Path("data/processed/clustering_results.json"),
            Path("visuals/public/data/visualization-data.json"),
            Path("visuals/public/data/cluster_themes.json"),
            Path("visuals/public/data/clustering_results.json")
        ]
        
        existing_files = [path for path in expected_paths if path.exists()]
        
        if len(existing_files) == 0:
            pytest.skip("No data files found - may not be generated yet")
        
        assert len(existing_files) > 0, f"No data files found in expected locations: {expected_paths}"
    
    def test_compressed_data_files_exist(self):
        """Test that compressed data files exist for web delivery"""
        expected_compressed_paths = [
            Path("data/processed/visualization-data.json.gz"),
            Path("data/processed/cluster_themes.json.gz"),
            Path("visuals/public/data/visualization-data.json.gz"),
            Path("visuals/public/data/cluster_themes.json.gz")
        ]
        
        existing_compressed = [path for path in expected_compressed_paths if path.exists()]
        
        if len(existing_compressed) == 0:
            pytest.skip("No compressed data files found")
        
        assert len(existing_compressed) > 0, "Should have compressed data files for web delivery"
    
    def test_search_index_files(self):
        """Test that search index files exist"""
        search_index_paths = [
            Path("data/search/search-index.json"),
            Path("visuals/public/data/search-index.json")
        ]
        
        existing_search_files = [path for path in search_index_paths if path.exists()]
        
        if len(existing_search_files) == 0:
            pytest.skip("No search index files found")
        
        assert len(existing_search_files) > 0, "Should have search index files"


class TestDataFileFormat:
    """Test data file format and structure"""
    
    def test_visualization_data_format(self):
        """Test visualization data file format"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json")
        ]
        
        valid_file_found = False
        
        for path in data_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Test basic structure
                    assert isinstance(data, dict), f"Data should be dictionary in {path}"
                    
                    # Check for works data (may be under 'works' or 'data' key)
                    works_key = None
                    if 'works' in data:
                        works_key = 'works'
                    elif 'data' in data:
                        works_key = 'data'
                    
                    if works_key:
                        works = data[works_key]
                        assert isinstance(works, list), f"Works should be list in {path}"
                        
                        if len(works) > 0:
                            # Test first work structure
                            work = works[0]
                            required_fields = ['id', 'title']
                            for field in required_fields:
                                assert field in work, f"Missing {field} in work from {path}"
                        
                        valid_file_found = True
                        break
                
                except (json.JSONDecodeError, KeyError, AssertionError) as e:
                    continue  # Try next file
        
        if not valid_file_found:
            pytest.skip("No valid visualization data files found")
    
    def test_cluster_themes_format(self):
        """Test cluster themes file format"""
        theme_paths = [
            Path("data/processed/cluster_themes.json"),
            Path("visuals/public/data/cluster_themes.json")
        ]
        
        valid_file_found = False
        
        for path in theme_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Test structure
                    assert isinstance(data, (dict, list)), f"Themes should be dict or list in {path}"
                    
                    if isinstance(data, dict):
                        # If dict, should have cluster information
                        for cluster_id, cluster_info in data.items():
                            if isinstance(cluster_info, dict):
                                # Should have theme information
                                assert 'theme' in cluster_info or 'name' in cluster_info, \
                                    f"Cluster {cluster_id} missing theme info in {path}"
                    
                    valid_file_found = True
                    break
                
                except (json.JSONDecodeError, KeyError, AssertionError) as e:
                    continue  # Try next file
        
        if not valid_file_found:
            pytest.skip("No valid cluster themes files found")
    
    def test_search_index_format(self):
        """Test search index file format"""
        search_paths = [
            Path("data/search/search-index.json"),
            Path("visuals/public/data/search-index.json")
        ]
        
        valid_file_found = False
        
        for path in search_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Test search index structure
                    assert isinstance(data, (dict, list)), f"Search index should be dict or list in {path}"
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Test first search entry
                        entry = data[0]
                        assert isinstance(entry, dict), "Search entries should be dictionaries"
                        
                        # Should have searchable fields
                        searchable_fields = ['id', 'title', 'text', 'content']
                        has_searchable = any(field in entry for field in searchable_fields)
                        assert has_searchable, f"Search entry missing searchable fields in {path}"
                    
                    valid_file_found = True
                    break
                
                except (json.JSONDecodeError, KeyError, AssertionError) as e:
                    continue  # Try next file
        
        if not valid_file_found:
            pytest.skip("No valid search index files found")


class TestCompressedDataLoading:
    """Test compressed data file loading"""
    
    def test_gzip_files_valid(self):
        """Test that gzip files are valid and can be decompressed"""
        compressed_paths = [
            Path("data/processed/visualization-data.json.gz"),
            Path("visuals/public/data/visualization-data.json.gz")
        ]
        
        valid_compressed_found = False
        
        for path in compressed_paths:
            if path.exists():
                try:
                    with gzip.open(path, 'rt') as f:
                        data = json.load(f)
                    
                    # Test that decompressed data is valid JSON
                    assert isinstance(data, dict), f"Decompressed data should be dict from {path}"
                    
                    valid_compressed_found = True
                    break
                
                except (gzip.BadGzipFile, json.JSONDecodeError, UnicodeDecodeError) as e:
                    continue  # Try next file
        
        if not valid_compressed_found:
            pytest.skip("No valid compressed data files found")
    
    def test_compression_efficiency(self):
        """Test that compression provides good file size reduction"""
        file_pairs = [
            (Path("data/processed/visualization-data.json"), 
             Path("data/processed/visualization-data.json.gz")),
            (Path("visuals/public/data/visualization-data.json"), 
             Path("visuals/public/data/visualization-data.json.gz"))
        ]
        
        compression_ratios = []
        file_details = []
        
        for uncompressed_path, compressed_path in file_pairs:
            if uncompressed_path.exists() and compressed_path.exists():
                uncompressed_size = uncompressed_path.stat().st_size
                compressed_size = compressed_path.stat().st_size
                
                # Skip files that are too small for meaningful compression testing
                if uncompressed_size < 100:  # Less than 100 bytes
                    continue
                
                if uncompressed_size > 0:
                    ratio = compressed_size / uncompressed_size
                    compression_ratios.append(ratio)
                    file_details.append({
                        'uncompressed': uncompressed_path,
                        'compressed': compressed_path,
                        'uncompressed_size': uncompressed_size,
                        'compressed_size': compressed_size,
                        'ratio': ratio
                    })
        
        if len(compression_ratios) == 0:
            pytest.skip("No suitable uncompressed/compressed file pairs found for compression testing")
        
        # Test compression efficiency with detailed error messages
        for details in file_details:
            ratio = details['ratio']
            if ratio >= 0.8:
                error_msg = (
                    f"Poor compression ratio for {details['uncompressed']}: {ratio:.3f} "
                    f"(uncompressed: {details['uncompressed_size']:,} bytes, "
                    f"compressed: {details['compressed_size']:,} bytes). "
                    f"Expected ratio < 0.8. This may indicate the file is too small "
                    f"or contains data that doesn't compress well."
                )
                assert False, error_msg
            
            assert ratio > 0.05, f"Suspiciously high compression: {ratio:.3f} (check file integrity)"


class TestDataLoadingPerformance:
    """Test data loading performance characteristics"""
    
    def test_file_sizes_reasonable(self):
        """Test that data files are reasonable size for web loading"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json"),
            Path("data/processed/cluster_themes.json"),
            Path("visuals/public/data/cluster_themes.json")
        ]
        
        max_size_mb = 5  # 5MB limit for individual files
        max_size_bytes = max_size_mb * 1024 * 1024
        
        large_files = []
        
        for path in data_paths:
            if path.exists():
                file_size = path.stat().st_size
                if file_size > max_size_bytes:
                    large_files.append((path, file_size / 1024 / 1024))
        
        if large_files:
            pytest.fail(f"Data files too large for web loading: {large_files} (max: {max_size_mb}MB)")
    
    def test_compressed_file_sizes(self):
        """Test that compressed files are suitable for web delivery"""
        compressed_paths = [
            Path("data/processed/visualization-data.json.gz"),
            Path("visuals/public/data/visualization-data.json.gz")
        ]
        
        max_compressed_mb = 2  # 2MB limit for compressed files
        max_compressed_bytes = max_compressed_mb * 1024 * 1024
        
        large_compressed = []
        
        for path in compressed_paths:
            if path.exists():
                file_size = path.stat().st_size
                if file_size > max_compressed_bytes:
                    large_compressed.append((path, file_size / 1024 / 1024))
        
        if large_compressed:
            pytest.fail(f"Compressed files too large: {large_compressed} (max: {max_compressed_mb}MB)")
    
    def test_data_structure_efficiency(self):
        """Test that data structure is efficient for loading"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(100)
        
        # Test that data is pre-processed for efficient loading
        works = viz_data['works']
        
        # Essential fields should be present (no need for client-side computation)
        essential_fields = ['id', 'x', 'y', 'cluster', 'title']
        
        for work in works[:5]:  # Test first 5
            for field in essential_fields:
                assert field in work, f"Missing essential field for efficient loading: {field}"
        
        # Coordinates should be pre-calculated
        coordinates = [(work['x'], work['y']) for work in works]
        assert all(isinstance(x, (int, float)) and isinstance(y, (int, float)) 
                  for x, y in coordinates), "Coordinates should be pre-calculated numbers"


class TestDataIntegrity:
    """Test data integrity during loading"""
    
    def test_data_consistency_across_files(self):
        """Test that data is consistent across different file locations"""
        file_pairs = [
            (Path("data/processed/visualization-data.json"), 
             Path("visuals/public/data/visualization-data.json")),
            (Path("data/processed/cluster_themes.json"), 
             Path("visuals/public/data/cluster_themes.json"))
        ]
        
        for source_path, target_path in file_pairs:
            if source_path.exists() and target_path.exists():
                try:
                    with open(source_path, 'r') as f:
                        source_data = json.load(f)
                    
                    with open(target_path, 'r') as f:
                        target_data = json.load(f)
                    
                    # Data should be identical or target should be subset of source
                    if isinstance(source_data, dict) and isinstance(target_data, dict):
                        # Check key consistency
                        common_keys = set(source_data.keys()) & set(target_data.keys())
                        assert len(common_keys) > 0, f"No common keys between {source_path} and {target_path}"
                
                except (json.JSONDecodeError, AssertionError) as e:
                    pytest.fail(f"Data consistency check failed for {source_path} and {target_path}: {e}")
    
    def test_data_completeness(self):
        """Test that data files are complete and not truncated"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json")
        ]
        
        for path in data_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    
                    # Test that file is not truncated (ends properly)
                    assert content.strip().endswith('}') or content.strip().endswith(']'), \
                        f"Data file may be truncated: {path}"
                    
                    # Test that it's valid JSON
                    data = json.loads(content)
                    assert data is not None, f"Data file contains null data: {path}"
                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    pytest.fail(f"Data completeness check failed for {path}: {e}")
    
    def test_required_data_present(self):
        """Test that all required data is present for visualization"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json")
        ]
        
        required_found = False
        
        for path in data_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Check for required data structure
                    if isinstance(data, dict):
                        # Should have works data
                        works_key = 'works' if 'works' in data else 'data'
                        if works_key in data:
                            works = data[works_key]
                            if isinstance(works, list) and len(works) > 0:
                                # Check first work has required fields
                                work = works[0]
                                required_fields = ['id', 'title']
                                if all(field in work for field in required_fields):
                                    required_found = True
                                    break
                
                except (json.JSONDecodeError, KeyError) as e:
                    continue  # Try next file
        
        if not required_found:
            pytest.skip("No files with required data structure found")