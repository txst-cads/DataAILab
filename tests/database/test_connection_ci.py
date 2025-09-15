"""CI-friendly database connection tests"""

import pytest
import psycopg2
import os
from sqlalchemy import text
from tests.utils.database_utils import get_test_database_engine


class TestDatabaseConnectionCI:
    """Basic database connection tests for CI environment"""
    
    def test_database_connection_available(self):
        """Test that database connection is available in CI using SQLAlchemy engine"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not set - this test only runs in CI environment")
        
        try:
            engine = get_test_database_engine(database_url)
            
            # Test basic query using SQLAlchemy engine
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test_value"))
                row = result.fetchone()
                assert row[0] == 1
            
            engine.dispose()
            
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")
    
    def test_database_can_create_table(self):
        """Test that we can create and drop a test table using SQLAlchemy engine"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not set")
        
        try:
            engine = get_test_database_engine(database_url)
            
            with engine.connect() as connection:
                # Create test table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_ci_table (
                        id SERIAL PRIMARY KEY,
                        test_data VARCHAR(100)
                    )
                """))
                
                # Insert test data
                connection.execute(
                    text("INSERT INTO test_ci_table (test_data) VALUES (:test_data)"),
                    {"test_data": "CI test data"}
                )
                
                # Query test data
                result = connection.execute(
                    text("SELECT test_data FROM test_ci_table WHERE test_data = :test_data"), 
                    {"test_data": "CI test data"}
                )
                row = result.fetchone()
                assert row[0] == "CI test data"
                
                # Clean up
                connection.execute(text("DROP TABLE test_ci_table"))
                connection.commit()
            
            engine.dispose()
            
        except Exception as e:
            pytest.fail(f"Database operation failed: {e}")
    
    def test_database_environment_variables(self):
        """Test that required database environment variables are set"""
        # Only run in CI
        if not (os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"):
            pytest.skip("This test only runs in CI environment")
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not set - this test only runs in CI environment")
            
        assert "postgresql://" in database_url, "DATABASE_URL should be PostgreSQL"
        assert "test_db" in database_url, "Should be using test database"