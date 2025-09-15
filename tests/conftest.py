"""
Pytest configuration and shared fixtures for CADS Research Visualization System tests
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import Engine

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "cads"))

# Load environment variables
load_dotenv()

# Import database utilities
from tests.utils.database_utils import get_test_database_engine, get_supabase_engine, create_test_tables_if_needed

@pytest.fixture(scope="session")
def database_url():
    """Provide database URL from environment with CI/local handling"""
    # In CI, prefer local PostgreSQL for unit tests
    if os.getenv("CI") == "true":
        local_url = "postgresql://postgres:postgres@localhost:5432/test_db"
        return local_url
    
    # For local development, use configured DATABASE_URL
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not configured")
    return url

@pytest.fixture(scope="session")
def supabase_url():
    """Provide Supabase URL for integration tests"""
    url = os.getenv("SUPABASE_URL")
    if not url:
        pytest.skip("SUPABASE_URL not configured for integration tests")
    return url

@pytest.fixture(scope="session")
def database_engine(database_url) -> Engine:
    """
    Provide SQLAlchemy engine for database connections.
    
    This fixture replaces direct psycopg2 connections to resolve pandas
    deprecation warnings when using pd.read_sql().
    """
    engine = get_test_database_engine(database_url)
    create_test_tables_if_needed(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def supabase_engine(supabase_url) -> Engine:
    """Provide SQLAlchemy engine for Supabase integration tests"""
    engine = get_supabase_engine(supabase_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def test_database_connection(database_engine):
    """
    Provide database connection with proper error handling.
    
    Note: This fixture is deprecated. Use database_engine fixture instead
    for pandas operations to avoid deprecation warnings.
    """
    import psycopg2
    
    try:
        # Extract connection URL from engine
        url = str(database_engine.url)
        conn = psycopg2.connect(url)
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")

@pytest.fixture(scope="session")
def ensure_test_tables(database_engine):
    """Ensure test tables exist for CI testing"""
    create_test_tables_if_needed(database_engine)

@pytest.fixture(scope="session")
def sample_data_dir():
    """Provide path to sample test data"""
    return Path(__file__).parent / "fixtures" / "sample_data"

@pytest.fixture
def temp_dir():
    """Provide temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="session")
def sample_embeddings():
    """Provide sample embedding data for testing"""
    # Create a small sample of 384-dimensional embeddings
    import numpy as np
    np.random.seed(42)  # For reproducible tests
    return np.random.rand(10, 384).astype(np.float32)

@pytest.fixture(scope="session")
def sample_works_data():
    """Provide sample works data for testing"""
    return [
        {
            "id": 1,
            "title": "Sample Research Paper 1",
            "researcher_id": 1,
            "publication_year": 2023,
            "embedding": "[0.1, 0.2, 0.3]"  # Simplified for testing
        },
        {
            "id": 2,
            "title": "Sample Research Paper 2", 
            "researcher_id": 2,
            "publication_year": 2022,
            "embedding": "[0.4, 0.5, 0.6]"
        }
    ]

@pytest.fixture(scope="session")
def sample_researchers_data():
    """Provide sample researchers data for testing"""
    return [
        {
            "id": 1,
            "full_name": "Dr. Jane Smith",
            "department": "Computer Science"
        },
        {
            "id": 2,
            "full_name": "Dr. John Doe",
            "department": "Computer Science"
        }
    ]

@pytest.fixture
def mock_data_processor(sample_works_data, sample_researchers_data):
    """Provide a mock DataProcessor for testing"""
    class MockDataProcessor:
        def __init__(self):
            self.connected = True
            
        def load_cads_data_with_researchers(self):
            # Return a DataFrame that matches the expected structure
            import pandas as pd
            works_df = pd.DataFrame(sample_works_data)
            researchers_df = pd.DataFrame(sample_researchers_data)
            
            # Merge to match the expected joined structure
            return works_df.merge(researchers_df, left_on='researcher_id', right_on='id', suffixes=('', '_researcher'))
            
        def parse_embeddings(self, embeddings):
            import numpy as np
            # Mock parsing - return simple array
            return np.random.rand(len(embeddings), 384).astype(np.float32)
            
    return MockDataProcessor()

# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "database: marks tests as requiring database connection"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "visualization: marks tests as visualization tests"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and content"""
    for item in items:
        # Mark database tests
        if "database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        
        # Mark integration tests (tests that use Supabase)
        if ("integration" in str(item.fspath) or 
            "full_pipeline" in str(item.fspath) or
            "supabase" in item.name.lower()):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
            
        # Mark visualization tests
        if "visualization" in str(item.fspath) or "html" in str(item.fspath):
            item.add_marker(pytest.mark.visualization)

# Auto-use fixtures for CI environment
@pytest.fixture(autouse=True, scope="session")
def setup_ci_environment():
    """Automatically set up CI test environment using SQLAlchemy engine"""
    # Only set up test tables if we're in CI and have a database URL
    if os.getenv("CI") == "true" and os.getenv("DATABASE_URL"):
        try:
            database_url = os.getenv("DATABASE_URL")
            engine = get_test_database_engine(database_url)
            create_test_tables_if_needed(engine)
            engine.dispose()
        except Exception:
            pass  # Skip if database setup fails