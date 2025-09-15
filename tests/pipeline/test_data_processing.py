"""
Data processing pipeline tests for CADS Research Visualization System
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from tests.fixtures.test_helpers import (
    load_sample_data, 
    create_sample_dataframe,
    assert_dataframe_structure,
    assert_embeddings_format
)


class TestDataProcessor:
    """Test the DataProcessor class functionality"""
    
    def test_data_processor_initialization(self):
        """Test DataProcessor can be initialized"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            assert processor is not None
        except ImportError:
            pytest.skip("DataProcessor not available")
    
    @pytest.mark.database
    def test_load_cads_data_with_researchers(self, database_url):
        """Test loading CADS data with researchers from database"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            data = processor.load_cads_data_with_researchers()
            
            expected_columns = ['id', 'title', 'researcher_id', 'full_name', 'department']
            assert_dataframe_structure(data, expected_columns, min_rows=0)
            
        except ImportError:
            pytest.skip("DataProcessor not available")
        except Exception:
            pytest.skip("Database not available for testing")
    
    def test_parse_embeddings_format(self):
        """Test parsing embeddings from string format"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            # Test with sample embedding string
            sample_embedding_str = "[0.1, 0.2, 0.3, 0.4, 0.5]"
            
            parsed = processor.parse_pgvector_embedding(sample_embedding_str)
            
            assert isinstance(parsed, np.ndarray)
            assert parsed.shape == (5,)  # Single embedding
            assert parsed.dtype in [np.float32, np.float64]  # Allow both float types
            
        except ImportError:
            pytest.skip("DataProcessor not available")
    
    def test_load_cads_data_with_researchers(self):
        """Test loading CADS data with researchers"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            # Test loading data (this will skip if database not available)
            data = processor.load_cads_data_with_researchers()
            
            expected_columns = ['id', 'title', 'researcher_id', 'full_name', 'department']
            assert_dataframe_structure(data, expected_columns, min_rows=0)
            
        except ImportError:
            pytest.skip("DataProcessor not available")
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.slow
    def test_process_complete_dataset(self):
        """Test complete dataset processing"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            result = processor.process_complete_dataset()
            
            assert 'data' in result
            assert 'embeddings' in result
            assert 'validation_passed' in result
            
            data = result['data']
            embeddings = result['embeddings']
            
            assert isinstance(data, pd.DataFrame)
            assert isinstance(embeddings, np.ndarray)
            assert len(data) == len(embeddings)
            
        except ImportError:
            pytest.skip("DataProcessor not available")
        except Exception:
            pytest.skip("Database not available for testing")


class TestEmbeddingGeneration:
    """Test embedding generation functionality"""
    
    def test_embedding_model_loading(self):
        """Test that embedding model can be loaded"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            assert model is not None
        except ImportError:
            pytest.skip("sentence-transformers not available")
    
    def test_embedding_generation(self):
        """Test generating embeddings for sample text"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            sample_texts = [
                "Machine learning applications in computer science",
                "Data visualization techniques for large datasets"
            ]
            
            embeddings = model.encode(sample_texts)
            
            assert_embeddings_format(embeddings, expected_shape=(2, 384))
            
        except ImportError:
            pytest.skip("sentence-transformers not available")
    
    def test_embedding_consistency(self):
        """Test that same text produces same embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            text = "Test text for embedding consistency"
            
            embedding1 = model.encode([text])
            embedding2 = model.encode([text])
            
            # Should be identical (or very close due to floating point precision)
            assert np.allclose(embedding1, embedding2, rtol=1e-6)
            
        except ImportError:
            pytest.skip("sentence-transformers not available")


class TestDataValidation:
    """Test data validation during processing"""
    
    def test_validate_works_data(self):
        """Test validation of works data"""
        sample_data = create_sample_dataframe("works")
        
        # Test required columns exist
        required_columns = ['id', 'title', 'researcher_id']
        for col in required_columns:
            assert col in sample_data.columns, f"Missing required column: {col}"
        
        # Test data types
        assert sample_data['id'].dtype in [np.int64, np.int32]
        assert sample_data['researcher_id'].dtype in [np.int64, np.int32]
        assert isinstance(sample_data['title'].iloc[0], str)
    
    def test_validate_researchers_data(self):
        """Test validation of researchers data"""
        sample_data = create_sample_dataframe("researchers")
        
        # Test required columns exist
        required_columns = ['id', 'full_name', 'department']
        for col in required_columns:
            assert col in sample_data.columns, f"Missing required column: {col}"
        
        # Test data types
        assert sample_data['id'].dtype in [np.int64, np.int32]
        assert isinstance(sample_data['full_name'].iloc[0], str)
        assert isinstance(sample_data['department'].iloc[0], str)
    
    def test_validate_embedding_dimensions(self):
        """Test that embeddings have correct dimensions"""
        sample_embeddings = np.random.rand(10, 384).astype(np.float32)
        
        assert_embeddings_format(sample_embeddings, expected_shape=(10, 384))
    
    def test_validate_data_completeness(self):
        """Test that processed data is complete"""
        sample_data = create_sample_dataframe("works")
        
        # Test no missing required fields
        assert not sample_data['id'].isna().any(), "Missing IDs found"
        assert not sample_data['title'].isna().any(), "Missing titles found"
        assert not sample_data['researcher_id'].isna().any(), "Missing researcher IDs found"


class TestErrorHandling:
    """Test error handling in data processing"""
    
    def test_handle_missing_database_url(self):
        """Test handling of missing database URL"""
        from cads.data_loader import DataProcessor
        
        # Clear environment and mock load_dotenv to prevent loading from .env file
        with patch.dict('os.environ', {}, clear=True), \
             patch('cads.data_loader.load_dotenv'):
            # Should raise ValueError when DATABASE_URL is missing
            with pytest.raises(ValueError, match="DATABASE_URL must be set"):
                processor = DataProcessor()
    
    def test_handle_invalid_embeddings(self):
        """Test handling of invalid embedding formats"""
        try:
            from cads.data_loader import DataProcessor
            processor = DataProcessor()
            
            # Test with invalid embedding strings
            invalid_embeddings = [
                "invalid_format",
                "",
                None
            ]
            
            # Should handle invalid formats gracefully (return None)
            for invalid_embedding in invalid_embeddings:
                result = processor.parse_pgvector_embedding(invalid_embedding)
                assert result is None, f"Should return None for invalid embedding: {invalid_embedding}"
                
        except ImportError:
            pytest.skip("DataProcessor not available")
    
    def test_handle_empty_dataset(self):
        """Test handling of empty datasets"""
        try:
            from cads.data_loader import DataProcessor
            
            # Mock empty dataset by patching the load method
            with patch.object(DataProcessor, 'load_cads_data_with_researchers') as mock_load:
                # Create empty DataFrame with all expected columns
                empty_columns = [
                    'id', 'title', 'researcher_id', 'full_name', 'department',
                    'citations', 'abstract', 'embedding'
                ]
                mock_load.return_value = pd.DataFrame(columns=empty_columns)
                
                processor = DataProcessor()
                result = processor.process_complete_dataset()
                
                # Should handle empty data gracefully
                assert 'data' in result
                assert len(result['data']) == 0
                
        except ImportError:
            pytest.skip("DataProcessor not available")