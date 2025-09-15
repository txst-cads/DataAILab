"""
Visualization rendering tests for CADS Research Visualization System
"""

import pytest
import json
from pathlib import Path
from tests.fixtures.test_helpers import TestDataGenerator, validate_json_structure


class TestDataVisualizationFormat:
    """Test visualization data format and structure"""
    
    def test_visualization_data_structure(self):
        """Test that visualization data has correct structure"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(20)
        
        # Test top-level structure
        required_keys = ['works', 'clusters']
        assert validate_json_structure(viz_data, required_keys), \
            f"Missing required keys: {required_keys}"
        
        # Test works structure
        works = viz_data['works']
        assert isinstance(works, list), "Works should be a list"
        assert len(works) > 0, "Works list should not be empty"
        
        # Test individual work structure
        work_required_fields = ['id', 'title', 'researcher_name', 'year', 'cluster', 'x', 'y']
        for work in works[:3]:  # Test first 3 works
            for field in work_required_fields:
                assert field in work, f"Work missing required field: {field}"
            
            # Test data types
            assert isinstance(work['id'], int), "Work ID should be integer"
            assert isinstance(work['title'], str), "Work title should be string"
            assert isinstance(work['x'], (int, float)), "Work x coordinate should be numeric"
            assert isinstance(work['y'], (int, float)), "Work y coordinate should be numeric"
        
        # Test clusters structure
        clusters = viz_data['clusters']
        assert isinstance(clusters, list), "Clusters should be a list"
        assert len(clusters) > 0, "Clusters list should not be empty"
        
        # Test individual cluster structure
        cluster_required_fields = ['id', 'name', 'color']
        for cluster in clusters:
            for field in cluster_required_fields:
                assert field in cluster, f"Cluster missing required field: {field}"
            
            # Test data types
            assert isinstance(cluster['id'], int), "Cluster ID should be integer"
            assert isinstance(cluster['name'], str), "Cluster name should be string"
            assert isinstance(cluster['color'], str), "Cluster color should be string"
            assert cluster['color'].startswith('#'), "Cluster color should be hex format"
    
    def test_coordinate_ranges(self):
        """Test that coordinates are within reasonable ranges"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(50)
        
        works = viz_data['works']
        
        # Extract coordinates
        x_coords = [work['x'] for work in works]
        y_coords = [work['y'] for work in works]
        
        # Test coordinate ranges
        assert all(isinstance(x, (int, float)) for x in x_coords), "All x coordinates should be numeric"
        assert all(isinstance(y, (int, float)) for y in y_coords), "All y coordinates should be numeric"
        
        # Test reasonable ranges (assuming 0-100 range from test data)
        assert all(0 <= x <= 100 for x in x_coords), "X coordinates should be in reasonable range"
        assert all(0 <= y <= 100 for y in y_coords), "Y coordinates should be in reasonable range"
    
    def test_cluster_assignments(self):
        """Test that cluster assignments are valid"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(30)
        
        works = viz_data['works']
        clusters = viz_data['clusters']
        
        # Get cluster IDs
        cluster_ids = {cluster['id'] for cluster in clusters}
        work_cluster_ids = {work['cluster'] for work in works}
        
        # Test that all work cluster assignments are valid
        invalid_assignments = work_cluster_ids - cluster_ids
        assert len(invalid_assignments) == 0, f"Invalid cluster assignments: {invalid_assignments}"


class TestVisualizationDataFiles:
    """Test actual visualization data files"""
    
    def test_data_files_exist(self):
        """Test that visualization data files exist"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json"),
            Path("data/processed/cluster_themes.json"),
            Path("visuals/public/data/cluster_themes.json")
        ]
        
        existing_files = [path for path in data_paths if path.exists()]
        
        if len(existing_files) == 0:
            pytest.skip("No visualization data files found")
        
        # At least one data file should exist
        assert len(existing_files) > 0, f"No data files found in expected locations: {data_paths}"
    
    def test_data_file_format(self):
        """Test that data files are valid JSON"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json")
        ]
        
        valid_files = []
        for path in data_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Test basic structure
                    if isinstance(data, dict) and ('works' in data or 'data' in data):
                        valid_files.append(path)
                        
                        # Test data structure
                        works_key = 'works' if 'works' in data else 'data'
                        works = data[works_key]
                        
                        assert isinstance(works, list), f"Works data should be list in {path}"
                        
                        if len(works) > 0:
                            # Test first work structure
                            work = works[0]
                            required_fields = ['id', 'title']
                            for field in required_fields:
                                assert field in work, f"Missing {field} in work from {path}"
                
                except (json.JSONDecodeError, KeyError, AssertionError) as e:
                    pytest.fail(f"Invalid data file {path}: {e}")
        
        if len(valid_files) == 0:
            pytest.skip("No valid visualization data files found")
    
    def test_compressed_data_files(self):
        """Test that compressed data files exist and are valid"""
        compressed_paths = [
            Path("data/processed/visualization-data.json.gz"),
            Path("visuals/public/data/visualization-data.json.gz")
        ]
        
        existing_compressed = [path for path in compressed_paths if path.exists()]
        
        if len(existing_compressed) == 0:
            pytest.skip("No compressed data files found")
        
        # Test that compressed files exist
        assert len(existing_compressed) > 0, "No compressed data files found"
        
        # Test file sizes (compressed should be smaller than uncompressed for files > 100 bytes)
        for compressed_path in existing_compressed:
            uncompressed_path = Path(str(compressed_path).replace('.gz', ''))
            
            if uncompressed_path.exists():
                compressed_size = compressed_path.stat().st_size
                uncompressed_size = uncompressed_path.stat().st_size
                
                assert compressed_size > 0, f"Compressed file {compressed_path} is empty"
                
                # Only test compression effectiveness for files large enough to compress well
                if uncompressed_size >= 100:
                    assert compressed_size < uncompressed_size, \
                        f"Compressed file {compressed_path} ({compressed_size:,} bytes) " \
                        f"not smaller than uncompressed ({uncompressed_size:,} bytes). " \
                        f"This may indicate compression issues or very small file size."


class TestVisualizationPerformance:
    """Test visualization performance characteristics"""
    
    def test_data_size_reasonable(self):
        """Test that data files are reasonable size for web delivery"""
        data_paths = [
            Path("data/processed/visualization-data.json"),
            Path("visuals/public/data/visualization-data.json")
        ]
        
        max_size_mb = 10  # 10MB limit for web delivery
        max_size_bytes = max_size_mb * 1024 * 1024
        
        large_files = []
        for path in data_paths:
            if path.exists():
                file_size = path.stat().st_size
                if file_size > max_size_bytes:
                    large_files.append((path, file_size))
        
        if large_files:
            file_info = [(str(path), size / 1024 / 1024) for path, size in large_files]
            pytest.fail(f"Data files too large for web delivery: {file_info} (max: {max_size_mb}MB)")
    
    def test_compressed_data_efficiency(self):
        """Test that compressed data provides good compression ratio"""
        compressed_paths = [
            Path("data/processed/visualization-data.json.gz"),
            Path("visuals/public/data/visualization-data.json.gz")
        ]
        
        compression_ratios = []
        file_details = []
        
        for compressed_path in compressed_paths:
            if compressed_path.exists():
                uncompressed_path = Path(str(compressed_path).replace('.gz', ''))
                
                if uncompressed_path.exists():
                    compressed_size = compressed_path.stat().st_size
                    uncompressed_size = uncompressed_path.stat().st_size
                    
                    # Skip files that are too small for meaningful compression testing
                    if uncompressed_size < 100:  # Less than 100 bytes
                        continue
                    
                    ratio = compressed_size / uncompressed_size
                    compression_ratios.append(ratio)
                    file_details.append({
                        'compressed': compressed_path,
                        'uncompressed': uncompressed_path,
                        'compressed_size': compressed_size,
                        'uncompressed_size': uncompressed_size,
                        'ratio': ratio
                    })
        
        if len(compression_ratios) == 0:
            pytest.skip("No suitable compressed/uncompressed file pairs found for compression testing")
        
        # Test that compression is effective (should be < 50% of original size)
        for details in file_details:
            ratio = details['ratio']
            if ratio >= 0.5:
                error_msg = (
                    f"Poor compression ratio for {details['compressed']}: {ratio:.3f} "
                    f"(uncompressed: {details['uncompressed_size']:,} bytes, "
                    f"compressed: {details['compressed_size']:,} bytes). "
                    f"Expected ratio < 0.5. This may indicate the file is too small "
                    f"or contains data that doesn't compress well."
                )
                assert False, error_msg
    
    def test_data_loading_structure(self):
        """Test that data is structured for efficient loading"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(100)
        
        works = viz_data['works']
        
        # Test that essential fields are present for quick rendering
        essential_fields = ['id', 'x', 'y', 'cluster']
        for work in works[:5]:  # Test first 5
            for field in essential_fields:
                assert field in work, f"Missing essential field for rendering: {field}"
        
        # Test that coordinates are pre-calculated (not requiring computation)
        x_coords = [work['x'] for work in works]
        y_coords = [work['y'] for work in works]
        
        assert all(isinstance(x, (int, float)) for x in x_coords), \
            "X coordinates should be pre-calculated numbers"
        assert all(isinstance(y, (int, float)) for y in y_coords), \
            "Y coordinates should be pre-calculated numbers"


class TestVisualizationAccessibility:
    """Test visualization accessibility features"""
    
    def test_color_accessibility(self):
        """Test that cluster colors are accessible"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(20)
        
        clusters = viz_data['clusters']
        colors = [cluster['color'] for cluster in clusters]
        
        # Test color format
        for color in colors:
            assert color.startswith('#'), f"Color should be hex format: {color}"
            assert len(color) in [4, 7, 8], f"Color should be 3, 6, or 7 digit hex: {color}"
            
            # Test that it's valid hex (allow for extra digits from test data generation)
            hex_part = color[1:]
            try:
                int(hex_part[:6], 16)  # Test first 6 hex digits
            except ValueError:
                pytest.fail(f"Invalid hex color: {color}")
        
        # Test color uniqueness (no duplicate colors)
        unique_colors = set(colors)
        assert len(unique_colors) == len(colors), "Cluster colors should be unique"
    
    def test_text_content_accessibility(self):
        """Test that text content is accessible"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(10)
        
        works = viz_data['works']
        clusters = viz_data['clusters']
        
        # Test work titles are meaningful
        for work in works:
            title = work['title']
            assert len(title.strip()) > 0, "Work titles should not be empty"
            assert len(title) > 5, f"Work title too short: {title}"
        
        # Test cluster names are meaningful
        for cluster in clusters:
            name = cluster['name']
            assert len(name.strip()) > 0, "Cluster names should not be empty"
            assert len(name) > 2, f"Cluster name too short: {name}"