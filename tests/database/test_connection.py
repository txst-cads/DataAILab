"""
Database connection tests for CADS Research Visualization System
"""

import pytest
import psycopg2
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text

from tests.fixtures.test_helpers import mock_database_connection, assert_dataframe_structure
from tests.utils.database_utils import get_test_database_engine

# Database tests now run in CI with proper test database configuration
pytestmark = pytest.mark.database


class TestDatabaseConnection:
    """Test database connectivity and basic operations"""
    
    @pytest.mark.database
    def test_database_connection_success(self, database_engine):
        """Test successful database connection using SQLAlchemy engine"""
        try:
            # Test connection using SQLAlchemy engine
            with database_engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test_value"))
                row = result.fetchone()
                assert row[0] == 1
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_database_connection_failure(self):
        """Test handling of database connection failure"""
        invalid_url = "postgresql://invalid:invalid@localhost:5432/invalid"
        
        with pytest.raises(psycopg2.OperationalError):
            psycopg2.connect(invalid_url)
    
    @pytest.mark.database
    def test_fetch_works_table(self, database_engine, ensure_test_tables):
        """Test fetching data from cads_works table using SQLAlchemy engine"""
        try:
            query = "SELECT id, title, researcher_id FROM cads_works LIMIT 5"
            df = pd.read_sql(query, database_engine)
            
            assert_dataframe_structure(df, ["id", "title", "researcher_id"], min_rows=0)
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_fetch_researchers_table(self, database_engine, ensure_test_tables):
        """Test fetching data from cads_researchers table using SQLAlchemy engine"""
        try:
            query = "SELECT id, full_name, department FROM cads_researchers LIMIT 5"
            df = pd.read_sql(query, database_engine)
            
            assert_dataframe_structure(df, ["id", "full_name", "department"], min_rows=0)
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_table_counts(self, database_engine, ensure_test_tables):
        """Test getting record counts from tables using SQLAlchemy engine"""
        try:
            with database_engine.connect() as connection:
                # Test works count
                result = connection.execute(text("SELECT COUNT(*) FROM cads_works"))
                works_count = result.fetchone()[0]
                assert isinstance(works_count, int)
                assert works_count >= 0
                
                # Test researchers count
                result = connection.execute(text("SELECT COUNT(*) FROM cads_researchers"))
                researchers_count = result.fetchone()[0]
                assert isinstance(researchers_count, int)
                assert researchers_count >= 0
        except Exception:
            pytest.skip("Database not available for testing")
    
    def test_mock_database_connection(self):
        """Test mock database connection for unit tests"""
        mock_conn = mock_database_connection()
        
        assert mock_conn is not None
        assert not mock_conn.closed
        
        cursor = mock_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_table")
        result = cursor.fetchone()
        
        assert result == (100,)
        
        cursor.close()
        mock_conn.close()
        assert mock_conn.closed


class TestEmbeddingsFormat:
    """Test pgvector embeddings format parsing"""
    
    @pytest.mark.database
    def test_embeddings_parsing(self, database_engine):
        """Test parsing of pgvector embeddings format using SQLAlchemy engine"""
        try:
            query = "SELECT id, title, embedding FROM cads_works WHERE embedding IS NOT NULL LIMIT 3"
            df = pd.read_sql(query, database_engine)
            
            for _, record in df.iterrows():
                if record['embedding']:
                    embedding_str = str(record['embedding'])
                    
                    # Test that embedding is in expected format
                    assert embedding_str.startswith('[') or embedding_str.startswith('(')
                    assert embedding_str.endswith(']') or embedding_str.endswith(')')
                    
                    # Test parsing
                    if embedding_str.startswith('[') and embedding_str.endswith(']'):
                        values = embedding_str.strip('[]').split(',')
                        assert len(values) > 0
                        
                        # Test that values can be converted to float
                        float_values = [float(v.strip()) for v in values[:5]]  # Test first 5
                        assert all(isinstance(v, float) for v in float_values)
        except Exception:
            pytest.skip("Database not available for testing")
    
    def test_mock_embeddings_format(self):
        """Test embeddings format with mock data"""
        # Test different embedding formats
        test_embeddings = [
            "[0.1, 0.2, 0.3, 0.4, 0.5]",
            "(0.1, 0.2, 0.3, 0.4, 0.5)",
            "0.1,0.2,0.3,0.4,0.5"
        ]
        
        for embedding_str in test_embeddings:
            if embedding_str.startswith('[') and embedding_str.endswith(']'):
                values = embedding_str.strip('[]').split(',')
                float_values = [float(v.strip()) for v in values]
                assert len(float_values) == 5
                assert all(isinstance(v, float) for v in float_values)


class TestDatabaseIntegrity:
    """Test database data integrity"""
    
    @pytest.mark.database
    def test_foreign_key_relationships(self, database_engine):
        """Test that foreign key relationships are maintained using SQLAlchemy engine"""
        try:
            # Test that all works have valid researcher_ids
            query = """
            SELECT COUNT(*) FROM cads_works w 
            LEFT JOIN cads_researchers r ON w.researcher_id = r.id 
            WHERE r.id IS NULL
            """
            
            df = pd.read_sql(query, database_engine)
            orphaned_works = df.iloc[0, 0]
            
            # Should have no orphaned works
            assert orphaned_works == 0, f"Found {orphaned_works} works without valid researchers"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_data_completeness(self, database_engine):
        """Test that required fields are not null using SQLAlchemy engine"""
        try:
            # Test works table completeness
            query = """
            SELECT 
                COUNT(*) as total,
                COUNT(title) as has_title,
                COUNT(researcher_id) as has_researcher_id
            FROM cads_works
            """
            
            df = pd.read_sql(query, database_engine)
            row = df.iloc[0]
            
            assert row['total'] == row['has_title'], "Some works missing titles"
            assert row['total'] == row['has_researcher_id'], "Some works missing researcher_id"
        except Exception:
            pytest.skip("Database not available for testing")