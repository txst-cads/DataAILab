"""
Database connection utilities for testing
Provides SQLAlchemy engine connections to resolve pandas deprecation warnings
"""

import os
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import NullPool
import pytest


def get_test_database_engine(database_url: Optional[str] = None) -> Engine:
    """
    Create SQLAlchemy engine for database connections in tests.
    
    This utility ensures that all database connections use SQLAlchemy engines
    instead of raw DBAPI connections, which resolves pandas deprecation warnings
    when using pd.read_sql().
    
    Args:
        database_url: Database connection URL. If None, uses environment variables.
        
    Returns:
        SQLAlchemy engine object configured for testing
        
    Raises:
        pytest.skip: If database URL is not available
    """
    if database_url is None:
        # In CI, prefer local PostgreSQL for unit tests
        if os.getenv("CI") == "true":
            database_url = "postgresql://postgres:postgres@localhost:5432/test_db"
        else:
            # For local development, use configured DATABASE_URL
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                pytest.skip("DATABASE_URL not configured")
    
    # Create engine with appropriate configuration for testing
    engine = create_engine(
        database_url,
        # Use NullPool to avoid connection pooling issues in tests
        poolclass=NullPool,
        # Enable echo for debugging if needed
        echo=False,
        # Set connection timeout
        connect_args={
            "connect_timeout": 10,
            "application_name": "cads_test_suite"
        }
    )
    
    return engine


def get_supabase_engine(supabase_url: Optional[str] = None) -> Engine:
    """
    Create SQLAlchemy engine for Supabase connections in integration tests.
    
    Args:
        supabase_url: Supabase database connection URL
        
    Returns:
        SQLAlchemy engine object configured for Supabase
        
    Raises:
        pytest.skip: If Supabase URL is not available
    """
    if supabase_url is None:
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            pytest.skip("SUPABASE_URL not configured for integration tests")
    
    # Create engine with Supabase-specific configuration
    engine = create_engine(
        supabase_url,
        poolclass=NullPool,
        echo=False,
        connect_args={
            "connect_timeout": 30,  # Longer timeout for remote connections
            "application_name": "cads_integration_tests"
        }
    )
    
    return engine


def execute_sql_with_engine(engine: Engine, query: str, params: Optional[dict] = None):
    """
    Execute SQL query using SQLAlchemy engine with proper connection handling.
    
    Args:
        engine: SQLAlchemy engine
        query: SQL query to execute
        params: Optional query parameters
        
    Returns:
        Query result
    """
    with engine.connect() as connection:
        if params:
            result = connection.execute(query, params)
        else:
            result = connection.execute(query)
        return result.fetchall()


def create_test_tables_if_needed(engine: Engine) -> None:
    """
    Create minimal test tables for CI testing if they don't exist.
    
    Args:
        engine: SQLAlchemy engine
    """
    if os.getenv("CI") != "true":
        return  # Skip for local development
    
    try:
        with engine.connect() as connection:
            # Create minimal test tables for CI
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cads_researchers (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    department VARCHAR(255) NOT NULL
                )
            """)
            
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cads_works (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    researcher_id INTEGER REFERENCES cads_researchers(id),
                    publication_year INTEGER,
                    embedding TEXT
                )
            """)
            
            # Insert minimal test data
            connection.execute("""
                INSERT INTO cads_researchers (id, full_name, department) 
                VALUES (1, 'Test Researcher', 'Computer Science')
                ON CONFLICT (id) DO NOTHING
            """)
            
            connection.execute("""
                INSERT INTO cads_works (id, title, researcher_id, publication_year, embedding)
                VALUES (1, 'Test Paper', 1, 2023, '[0.1, 0.2, 0.3]')
                ON CONFLICT (id) DO NOTHING
            """)
            
            connection.commit()
            
    except Exception:
        pass  # Skip if database setup fails