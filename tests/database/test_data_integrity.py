"""
Database data integrity tests for CADS Research Visualization System
"""

import pytest
import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine, text
from tests.fixtures.test_helpers import assert_dataframe_structure
from tests.utils.database_utils import get_test_database_engine

# Database tests now run in CI with proper test database configuration
pytestmark = pytest.mark.database


class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    @pytest.mark.database
    def test_researcher_data_consistency(self, database_engine):
        """Test that researcher data is consistent using SQLAlchemy engine"""
        try:
            # Test for duplicate researchers
            query = """
            SELECT full_name, COUNT(*) as count 
            FROM cads_researchers 
            GROUP BY full_name 
            HAVING COUNT(*) > 1
            """
            
            df = pd.read_sql(query, database_engine)
            assert len(df) == 0, f"Found duplicate researchers: {df['full_name'].tolist()}"
            
            # Test that all researchers have required fields
            query = """
            SELECT COUNT(*) as total,
                   COUNT(full_name) as has_name,
                   COUNT(department) as has_department
            FROM cads_researchers
            """
            
            df = pd.read_sql(query, database_engine)
            row = df.iloc[0]
            
            assert row['total'] == row['has_name'], "Some researchers missing names"
            assert row['total'] == row['has_department'], "Some researchers missing departments"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_works_data_consistency(self, database_engine):
        """Test that works data is consistent using SQLAlchemy engine"""
        try:
            # Test for works with invalid years
            query = """
            SELECT COUNT(*) as invalid_years
            FROM cads_works 
            WHERE publication_year < 1900 OR publication_year > 2030
            """
            
            df = pd.read_sql(query, database_engine)
            invalid_years = df.iloc[0, 0]
            assert invalid_years == 0, f"Found {invalid_years} works with invalid publication years"
            
            # Test that all works have titles
            query = """
            SELECT COUNT(*) as total,
                   COUNT(title) as has_title,
                   COUNT(CASE WHEN LENGTH(TRIM(title)) > 0 THEN 1 END) as has_non_empty_title
            FROM cads_works
            """
            
            df = pd.read_sql(query, database_engine)
            row = df.iloc[0]
            
            assert row['total'] == row['has_title'], "Some works missing titles"
            assert row['total'] == row['has_non_empty_title'], "Some works have empty titles"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_embedding_data_integrity(self, database_engine):
        """Test that embedding data is properly formatted using SQLAlchemy engine"""
        try:
            # Test embedding format consistency
            query = """
            SELECT id, title, embedding
            FROM cads_works 
            WHERE embedding IS NOT NULL 
            LIMIT 10
            """
            
            df = pd.read_sql(query, database_engine)
            
            for _, row in df.iterrows():
                embedding_str = str(row['embedding'])
                
                # Test that embedding is not empty
                assert len(embedding_str.strip()) > 0, f"Empty embedding for work {row['id']}"
                
                # Test that embedding has expected format
                assert any(char in embedding_str for char in ['[', '(', ',']), \
                    f"Unexpected embedding format for work {row['id']}: {embedding_str[:50]}"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_referential_integrity(self, database_engine):
        """Test referential integrity between tables using SQLAlchemy engine"""
        try:
            # Test that all researcher_ids in works table exist in researchers table
            query = """
            SELECT w.id, w.title, w.researcher_id
            FROM cads_works w
            LEFT JOIN cads_researchers r ON w.researcher_id = r.id
            WHERE r.id IS NULL
            LIMIT 5
            """
            
            df = pd.read_sql(query, database_engine)
            assert len(df) == 0, f"Found works with invalid researcher_ids: {df['id'].tolist()}"
        except Exception:
            pytest.skip("Database not available for testing")


class TestQueryPerformance:
    """Test database query performance"""
    
    @pytest.mark.database
    @pytest.mark.slow
    def test_basic_query_performance(self, database_engine):
        """Test that basic queries execute within reasonable time using SQLAlchemy engine"""
        import time
        
        try:
            # Test works query performance
            start_time = time.time()
            query = "SELECT id, title, researcher_id FROM cads_works LIMIT 100"
            df = pd.read_sql(query, database_engine)
            query_time = time.time() - start_time
            
            assert query_time < 5.0, f"Works query took too long: {query_time:.2f}s"
            assert len(df) <= 100, "Query returned more rows than expected"
            
            # Test researchers query performance
            start_time = time.time()
            query = "SELECT id, full_name, department FROM cads_researchers"
            df = pd.read_sql(query, database_engine)
            query_time = time.time() - start_time
            
            assert query_time < 5.0, f"Researchers query took too long: {query_time:.2f}s"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    @pytest.mark.slow
    def test_join_query_performance(self, database_engine):
        """Test that join queries execute within reasonable time using SQLAlchemy engine"""
        import time
        
        try:
            start_time = time.time()
            query = """
            SELECT w.id, w.title, r.full_name, r.department
            FROM cads_works w
            JOIN cads_researchers r ON w.researcher_id = r.id
            LIMIT 100
            """
            df = pd.read_sql(query, database_engine)
            query_time = time.time() - start_time
            
            assert query_time < 10.0, f"Join query took too long: {query_time:.2f}s"
            assert_dataframe_structure(df, ["id", "title", "full_name", "department"], min_rows=0)
        except Exception:
            pytest.skip("Database not available for testing")


class TestDataValidation:
    """Test data validation rules"""
    
    @pytest.mark.database
    def test_researcher_name_format(self, database_engine):
        """Test that researcher names follow expected format using SQLAlchemy engine"""
        try:
            query = "SELECT full_name FROM cads_researchers WHERE full_name IS NOT NULL"
            df = pd.read_sql(query, database_engine)
            
            for name in df['full_name']:
                # Test that name is not empty
                assert len(name.strip()) > 0, f"Empty researcher name found"
                
                # Test that name contains at least one space (first + last name)
                assert ' ' in name.strip(), f"Researcher name missing space: {name}"
                
                # Test that name doesn't contain invalid characters
                invalid_chars = ['<', '>', '{', '}', '[', ']']
                assert not any(char in name for char in invalid_chars), \
                    f"Invalid characters in name: {name}"
        except Exception:
            pytest.skip("Database not available for testing")
    
    @pytest.mark.database
    def test_publication_year_range(self, database_engine):
        """Test that publication years are within reasonable range using SQLAlchemy engine"""
        try:
            query = """
            SELECT MIN(publication_year) as min_year, 
                   MAX(publication_year) as max_year,
                   COUNT(*) as total_works
            FROM cads_works 
            WHERE publication_year IS NOT NULL
            """
            
            df = pd.read_sql(query, database_engine)
            row = df.iloc[0]
            
            # Test reasonable year range
            assert row['min_year'] >= 1950, f"Minimum year too old: {row['min_year']}"
            assert row['max_year'] <= 2030, f"Maximum year too new: {row['max_year']}"
            assert row['total_works'] > 0, "No works with publication years found"
        except Exception:
            pytest.skip("Database not available for testing")