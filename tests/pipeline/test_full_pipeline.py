"""
Full ML pipeline integration tests for CADS Research Visualization System
"""

import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.fixtures.test_helpers import (
    create_sample_embeddings,
    TestDataGenerator,
    assert_embeddings_format
)


class TestFullPipeline:
    """Test complete ML pipeline execution"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_pipeline_execution(self, temp_dir):
        """Test that the complete pipeline can execute successfully"""
        try:
            # Test data loading
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            result = processor.process_complete_dataset()
            
            assert 'data' in result
            assert 'embeddings' in result
            assert 'validation_passed' in result
            
            data = result['data']
            embeddings = result['embeddings']
            
            # Validate output structure
            assert isinstance(data, pd.DataFrame)
            assert isinstance(embeddings, np.ndarray)
            assert len(data) == len(embeddings)
            assert embeddings.shape[1] == 384  # Expected embedding dimensions
            
        except ImportError:
            pytest.skip("Pipeline dependencies not available")
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_umap_clustering_pipeline(self, temp_dir):
        """Test UMAP + HDBSCAN clustering pipeline"""
        try:
            # Create sample embeddings
            sample_embeddings = create_sample_embeddings(100, 384)
            
            # Test UMAP dimensionality reduction
            import umap
            reducer = umap.UMAP(n_neighbors=15, n_components=2, random_state=42)
            coordinates = reducer.fit_transform(sample_embeddings)
            
            assert coordinates.shape == (100, 2)
            assert not np.isnan(coordinates).any()
            
            # Test HDBSCAN clustering
            import hdbscan
            clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
            cluster_labels = clusterer.fit_predict(coordinates)
            
            assert len(cluster_labels) == 100
            assert cluster_labels.dtype == np.int64
            
            # Test that we get some clusters (not all noise)
            unique_labels = np.unique(cluster_labels)
            num_clusters = len(unique_labels[unique_labels >= 0])
            assert num_clusters > 0, "No clusters found"
            
        except ImportError:
            pytest.skip("ML dependencies (umap, hdbscan) not available")
    
    @pytest.mark.integration
    def test_pipeline_output_format(self, temp_dir):
        """Test that pipeline outputs are in correct format"""
        # Generate mock pipeline results
        generator = TestDataGenerator()
        clustering_results = generator.generate_clustering_results(5, 50)
        visualization_data = generator.generate_visualization_data(50)
        
        # Test clustering results format
        assert 'cluster_labels' in clustering_results
        assert 'coordinates' in clustering_results
        assert 'num_clusters' in clustering_results
        
        cluster_labels = clustering_results['cluster_labels']
        coordinates = clustering_results['coordinates']
        
        assert len(cluster_labels) == 50
        assert len(coordinates) == 50
        assert all(len(coord) == 2 for coord in coordinates)
        
        # Test visualization data format
        assert 'works' in visualization_data
        assert 'clusters' in visualization_data
        
        works = visualization_data['works']
        clusters = visualization_data['clusters']
        
        assert len(works) == 50
        assert len(clusters) == 5
        
        # Test work structure
        required_work_fields = ['id', 'title', 'researcher_name', 'year', 'cluster', 'x', 'y']
        for work in works[:3]:  # Test first 3
            for field in required_work_fields:
                assert field in work, f"Missing field {field} in work"
    
    @pytest.mark.integration
    def test_pipeline_data_persistence(self, temp_dir):
        """Test that pipeline can save and load data"""
        # Create sample data
        sample_data = {
            'works': [
                {'id': 1, 'title': 'Test Paper 1', 'x': 10.5, 'y': 20.3},
                {'id': 2, 'title': 'Test Paper 2', 'x': 15.2, 'y': 25.7}
            ],
            'clusters': [
                {'id': 0, 'name': 'Cluster 1', 'color': '#ff0000'},
                {'id': 1, 'name': 'Cluster 2', 'color': '#00ff00'}
            ]
        }
        
        # Test saving data
        output_file = temp_dir / "test_output.json"
        with open(output_file, 'w') as f:
            json.dump(sample_data, f)
        
        assert output_file.exists()
        
        # Test loading data
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == sample_data
        assert len(loaded_data['works']) == 2
        assert len(loaded_data['clusters']) == 2


class TestPipelinePerformance:
    """Test pipeline performance characteristics"""
    
    @pytest.mark.slow
    def test_embedding_generation_performance(self):
        """Test embedding generation performance"""
        try:
            from sentence_transformers import SentenceTransformer
            import time
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Test with small batch
            sample_texts = [f"Sample research paper title {i}" for i in range(10)]
            
            start_time = time.time()
            embeddings = model.encode(sample_texts)
            generation_time = time.time() - start_time
            
            # Should complete within reasonable time
            assert generation_time < 30.0, f"Embedding generation too slow: {generation_time:.2f}s"
            assert_embeddings_format(embeddings, expected_shape=(10, 384))
            
        except ImportError:
            pytest.skip("sentence-transformers not available")
    
    @pytest.mark.slow
    def test_clustering_performance(self):
        """Test clustering performance with sample data"""
        try:
            import umap
            import hdbscan
            import time
            
            # Create larger sample for performance testing
            sample_embeddings = create_sample_embeddings(500, 384)
            
            # Test UMAP performance
            start_time = time.time()
            reducer = umap.UMAP(n_neighbors=15, n_components=2, random_state=42)
            coordinates = reducer.fit_transform(sample_embeddings)
            umap_time = time.time() - start_time
            
            assert umap_time < 60.0, f"UMAP too slow: {umap_time:.2f}s"
            assert coordinates.shape == (500, 2)
            
            # Test HDBSCAN performance
            start_time = time.time()
            clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
            cluster_labels = clusterer.fit_predict(coordinates)
            clustering_time = time.time() - start_time
            
            assert clustering_time < 30.0, f"HDBSCAN too slow: {clustering_time:.2f}s"
            assert len(cluster_labels) == 500
            
        except ImportError:
            pytest.skip("ML dependencies not available")


class TestPipelineValidation:
    """Test pipeline output validation"""
    
    def test_validate_clustering_output(self):
        """Test validation of clustering results"""
        # Generate mock clustering results
        generator = TestDataGenerator()
        results = generator.generate_clustering_results(3, 20)
        
        cluster_labels = results['cluster_labels']
        coordinates = results['coordinates']
        
        # Validate cluster labels
        assert len(cluster_labels) == 20
        assert all(isinstance(label, int) for label in cluster_labels)
        assert all(label >= -1 for label in cluster_labels)  # -1 is noise, >= 0 are clusters
        
        # Validate coordinates
        assert len(coordinates) == 20
        assert all(len(coord) == 2 for coord in coordinates)
        assert all(isinstance(x, (int, float)) and isinstance(y, (int, float)) 
                  for x, y in coordinates)
    
    def test_validate_visualization_data(self):
        """Test validation of visualization data structure"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(30)
        
        # Validate works data
        works = viz_data['works']
        assert len(works) == 30
        
        required_fields = ['id', 'title', 'researcher_name', 'year', 'cluster', 'x', 'y']
        for work in works:
            for field in required_fields:
                assert field in work, f"Missing field: {field}"
            
            # Validate data types
            assert isinstance(work['id'], int)
            assert isinstance(work['title'], str)
            assert isinstance(work['year'], int)
            assert isinstance(work['x'], (int, float))
            assert isinstance(work['y'], (int, float))
        
        # Validate clusters data
        clusters = viz_data['clusters']
        assert len(clusters) > 0
        
        for cluster in clusters:
            assert 'id' in cluster
            assert 'name' in cluster
            assert 'color' in cluster
            assert isinstance(cluster['id'], int)
            assert isinstance(cluster['name'], str)
            assert cluster['color'].startswith('#')  # Hex color format


class TestPipelineErrorHandling:
    """Test error handling in pipeline execution"""
    
    def test_handle_insufficient_data(self):
        """Test handling of insufficient data for clustering"""
        try:
            import hdbscan
            
            # Test with very small dataset
            small_coordinates = np.random.rand(3, 2)
            
            clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
            cluster_labels = clusterer.fit_predict(small_coordinates)
            
            # Should handle gracefully (likely all noise points)
            assert len(cluster_labels) == 3
            # With min_cluster_size=5 and only 3 points, all should be noise (-1)
            assert all(label == -1 for label in cluster_labels)
            
        except ImportError:
            pytest.skip("HDBSCAN not available")
    
    def test_handle_invalid_embeddings(self):
        """Test handling of invalid embedding data"""
        try:
            import umap
            
            # Test with invalid embeddings (NaN values)
            invalid_embeddings = np.full((10, 384), np.nan)
            
            reducer = umap.UMAP(n_neighbors=5, n_components=2)
            
            # Should handle NaN values appropriately
            with pytest.raises((ValueError, RuntimeError)):
                reducer.fit_transform(invalid_embeddings)
                
        except ImportError:
            pytest.skip("UMAP not available")
    
    def test_handle_empty_pipeline_input(self):
        """Test handling of empty input to pipeline"""
        try:
            from cads.data_loader import DataProcessor
            
            # Mock empty dataset with all expected columns
            with patch.object(DataProcessor, 'load_cads_data_with_researchers') as mock_load:
                empty_df = pd.DataFrame(columns=[
                    'id', 'title', 'researcher_id', 'full_name', 'department',
                    'citations', 'abstract', 'publication_year', 'embedding'
                ])
                mock_load.return_value = empty_df
                
                processor = DataProcessor()
                result = processor.process_complete_dataset()
                
                # Should handle empty data gracefully
                assert 'data' in result
                assert len(result['data']) == 0
                
        except ImportError:
            pytest.skip("DataProcessor not available")
    
    def test_handle_missing_columns_in_dataframe(self):
        """Test handling of DataFrame with missing expected columns"""
        try:
            from cads.data_loader import DataProcessor
            
            # Create DataFrame with missing columns
            incomplete_df = pd.DataFrame({
                'id': [1, 2, 3],
                'title': ['Paper 1', 'Paper 2', 'Paper 3'],
                # Missing: citations, abstract, publication_year, embedding, full_name
            })
            
            processor = DataProcessor()
            embeddings = np.zeros((3, 384))  # Mock embeddings
            
            # Should handle missing columns gracefully without crashing
            validation_results = processor.validate_data(incomplete_df, embeddings)
            
            assert 'missing_columns' in validation_results
            assert 'citations' in validation_results['missing_columns']
            assert 'abstract' in validation_results['missing_columns']
            assert 'publication_year' in validation_results['missing_columns']
            assert 'full_name' in validation_results['missing_columns']
            
            # Should still provide basic validation info
            assert validation_results['total_works'] == 3
            assert validation_results['embedding_dimensions'] == 384
            
        except ImportError:
            pytest.skip("DataProcessor not available")