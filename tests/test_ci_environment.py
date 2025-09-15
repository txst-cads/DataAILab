"""
CI Environment Tests - Basic tests to verify CI setup is working
"""

import pytest
import os
import sys
from pathlib import Path


class TestCIEnvironment:
    """Test CI environment setup"""
    
    def test_python_version(self):
        """Test that Python version is acceptable"""
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 8, f"Python 3.8+ required, got {version.major}.{version.minor}"
    
    def test_project_structure_exists(self):
        """Test that basic project structure exists"""
        project_root = Path(__file__).parent.parent
        
        # Check key directories exist
        assert (project_root / "cads").exists(), "cads directory missing"
        assert (project_root / "tests").exists(), "tests directory missing"
        assert (project_root / "visuals").exists(), "visuals directory missing"
        
        # Check key files exist
        assert (project_root / "cads" / "requirements.txt").exists(), "cads/requirements.txt missing"
        assert (project_root / "README.md").exists(), "README.md missing"
    
    def test_environment_variables(self):
        """Test that required environment variables are set"""
        # Skip if not in CI environment
        if not os.getenv("CI") and not os.getenv("GITHUB_ACTIONS"):
            pytest.skip("Not in CI environment - environment variables not required")
        
        # These should be set by CI
        database_url = os.getenv("DATABASE_URL")
        openalex_email = os.getenv("OPENALEX_EMAIL")
        
        assert database_url is not None, "DATABASE_URL not set"
        assert openalex_email is not None, "OPENALEX_EMAIL not set"
        
        # Basic validation
        assert "postgresql://" in database_url, "DATABASE_URL should be PostgreSQL"
        assert "@" in openalex_email, "OPENALEX_EMAIL should be valid email format"
    
    def test_imports_work(self):
        """Test that basic imports work"""
        # Test standard library imports
        import json
        import os
        import sys
        
        # Test third-party imports that should be available
        import pandas as pd
        import numpy as np
        import pytest
        
        # Test that we can import from our project
        sys.path.insert(0, str(Path(__file__).parent.parent / "cads"))
        
        # This should work if the environment is set up correctly
        try:
            from tests.fixtures.test_helpers import create_sample_dataframe
            assert create_sample_dataframe is not None
        except ImportError as e:
            pytest.fail(f"Could not import test helpers: {e}")
    
    def test_database_connection_possible(self):
        """Test that database connection is possible"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not set")
        
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            assert conn is not None
            assert not conn.closed
            conn.close()
        except psycopg2.OperationalError:
            pytest.skip("Database not available - this is expected in some CI environments")
        except ImportError:
            pytest.fail("psycopg2 not available - check requirements.txt installation")


class TestBasicFunctionality:
    """Test basic functionality works"""
    
    def test_pandas_basic_operations(self):
        """Test pandas basic operations work"""
        import pandas as pd
        import numpy as np
        
        # Create a simple DataFrame
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [1.0, 2.0, 3.0]
        })
        
        assert len(df) == 3
        assert list(df.columns) == ['id', 'name', 'value']
        assert df['value'].sum() == 6.0
    
    def test_numpy_basic_operations(self):
        """Test numpy basic operations work"""
        import numpy as np
        
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.sum() == 15
        assert arr.mean() == 3.0
        assert arr.shape == (5,)
    
    def test_json_operations(self):
        """Test JSON operations work"""
        import json
        
        data = {"test": "value", "number": 42}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        
        assert parsed == data
        assert parsed["test"] == "value"
        assert parsed["number"] == 42