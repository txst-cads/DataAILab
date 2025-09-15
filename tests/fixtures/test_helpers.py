"""
Test helper utilities for CADS Research Visualization System tests
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_sample_data() -> Dict[str, Any]:
    """Load sample test data from JSON file"""
    fixtures_dir = Path(__file__).parent
    sample_data_path = fixtures_dir / "sample_data.json"
    
    with open(sample_data_path, 'r') as f:
        return json.load(f)

def create_sample_embeddings(num_samples: int = 10, dimensions: int = 384) -> np.ndarray:
    """Create sample embeddings for testing"""
    np.random.seed(42)  # For reproducible tests
    return np.random.rand(num_samples, dimensions).astype(np.float32)

def create_sample_dataframe(data_type: str = "works") -> pd.DataFrame:
    """Create sample pandas DataFrame for testing"""
    sample_data = load_sample_data()
    
    if data_type == "works":
        return pd.DataFrame(sample_data["sample_works"])
    elif data_type == "researchers":
        return pd.DataFrame(sample_data["sample_researchers"])
    elif data_type == "topics":
        return pd.DataFrame(sample_data["sample_topics"])
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def mock_database_connection():
    """Create a mock database connection for testing"""
    class MockConnection:
        def __init__(self):
            self.closed = False
            
        def cursor(self):
            return MockCursor()
            
        def close(self):
            self.closed = True
            
        def commit(self):
            pass
            
    class MockCursor:
        def __init__(self):
            self.closed = False
            
        def execute(self, query, params=None):
            # Mock successful execution
            pass
            
        def fetchone(self):
            return (100,)  # Mock count result
            
        def fetchall(self):
            return [(1, "Sample Title", 1)]  # Mock query result
            
        def close(self):
            self.closed = True
            
    return MockConnection()

def assert_dataframe_structure(df: pd.DataFrame, expected_columns: List[str], 
                             min_rows: int = 1) -> None:
    """Assert that a DataFrame has the expected structure"""
    assert isinstance(df, pd.DataFrame), "Expected pandas DataFrame"
    assert len(df) >= min_rows, f"Expected at least {min_rows} rows, got {len(df)}"
    
    missing_columns = set(expected_columns) - set(df.columns)
    assert not missing_columns, f"Missing columns: {missing_columns}"

def assert_embeddings_format(embeddings: np.ndarray, expected_shape: tuple = None) -> None:
    """Assert that embeddings have the correct format"""
    assert isinstance(embeddings, np.ndarray), "Expected numpy array"
    assert embeddings.dtype == np.float32, f"Expected float32, got {embeddings.dtype}"
    
    if expected_shape:
        assert embeddings.shape == expected_shape, f"Expected shape {expected_shape}, got {embeddings.shape}"
    
    # Check that embeddings are not all zeros
    assert not np.allclose(embeddings, 0), "Embeddings should not be all zeros"

def create_mock_html_content() -> str:
    """Create mock HTML content for testing"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CADS Research Visualization</title>
        <meta name="description" content="Interactive visualization of CADS research">
    </head>
    <body>
        <div id="loading">Loading CADS Research Visualization...</div>
        <div id="map-container"></div>
        <div id="ui-panel">
            <input type="text" id="search-input" placeholder="Search...">
            <select id="researcher-filter"></select>
            <input type="range" id="year-filter">
            <select id="cluster-filter"></select>
        </div>
        <div id="tooltip"></div>
        <div id="error-message"></div>
        
        <script src="https://unpkg.com/deck.gl@latest/dist.min.js"></script>
        <script>
            function init() { }
            function setupUIEventListeners() { }
            function togglePanel() { }
            function showTooltip() { }
            function debounce() { }
        </script>
    </body>
    </html>
    """

def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate that JSON data has required structure"""
    for key in required_keys:
        if key not in data:
            return False
    return True

def create_test_environment_file(temp_dir: Path) -> Path:
    """Create a test .env file"""
    env_content = """
DATABASE_URL=postgresql://test:test@localhost:5432/test_db
OPENALEX_EMAIL=test@example.com
GROQ_API_KEY=test_key
EMBEDDING_MODEL=all-MiniLM-L6-v2
UMAP_N_NEIGHBORS=15
HDBSCAN_MIN_CLUSTER_SIZE=5
"""
    env_file = temp_dir / ".env"
    env_file.write_text(env_content.strip())
    return env_file

class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_clustering_results(num_clusters: int = 5, num_points: int = 100) -> Dict[str, Any]:
        """Generate mock clustering results"""
        np.random.seed(42)
        
        # Generate cluster labels
        cluster_labels = np.random.randint(-1, num_clusters, num_points)
        
        # Generate 2D coordinates
        coordinates = np.random.rand(num_points, 2) * 100
        
        return {
            "cluster_labels": cluster_labels.tolist(),
            "coordinates": coordinates.tolist(),
            "num_clusters": num_clusters,
            "noise_points": np.sum(cluster_labels == -1)
        }
    
    @staticmethod
    def generate_visualization_data(num_works: int = 50) -> Dict[str, Any]:
        """Generate mock visualization data"""
        np.random.seed(42)
        
        works = []
        for i in range(num_works):
            works.append({
                "id": i + 1,
                "title": f"Research Paper {i + 1}",
                "researcher_name": f"Researcher {(i % 10) + 1}",
                "year": 2020 + (i % 4),
                "cluster": i % 5,
                "x": np.random.rand() * 100,
                "y": np.random.rand() * 100
            })
        
        return {
            "works": works,
            "clusters": [
                {"id": i, "name": f"Cluster {i}", "color": f"#{i*50:02x}{i*30:02x}{i*70:02x}"}
                for i in range(5)
            ]
        }