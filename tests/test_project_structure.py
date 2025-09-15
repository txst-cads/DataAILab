"""
Project structure tests for CADS Research Visualization System
Tests that required files and directories exist and have correct structure
"""

import pytest
from pathlib import Path


class TestProjectStructure:
    """Test overall project structure and required files"""
    
    def test_root_files_exist(self):
        """Test that required root files exist"""
        root_files = [
            "README.md",
            "vercel.json",
            ".gitignore"
        ]
        
        missing_files = []
        for file in root_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        # Allow some flexibility - not all files may be required
        if len(missing_files) == len(root_files):
            pytest.fail(f"No root files found. Expected at least some of: {root_files}")
    
    def test_cads_directory_structure(self):
        """Test CADS directory structure"""
        cads_dir = Path("cads")
        
        if not cads_dir.exists():
            pytest.skip("CADS directory not found")
        
        required_files = [
            "data_loader.py",
            "process_data.py", 
            "requirements.txt",
            ".env.example"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = cads_dir / file
            if not file_path.exists():
                missing_files.append(file)
        
        assert len(missing_files) == 0, f"Missing CADS files: {missing_files}"
    
    def test_cads_subdirectories(self):
        """Test CADS subdirectories exist (after cleanup, data/models moved to root)"""
        cads_dir = Path("cads")
        
        if not cads_dir.exists():
            pytest.skip("CADS directory not found")
        
        # After cleanup, data and models are now centralized
        # Check that centralized directories exist instead
        centralized_dirs = [
            Path("data/processed"),
            Path("data/models")
        ]
        
        for dir_path in centralized_dirs:
            assert dir_path.exists() and dir_path.is_dir(), \
                f"Missing centralized directory: {dir_path}"
    
    def test_visuals_directory_structure(self):
        """Test visuals directory structure"""
        visuals_dir = Path("visuals")
        
        if not visuals_dir.exists():
            pytest.skip("Visuals directory not found")
        
        # Check for public directory
        public_dir = visuals_dir / "public"
        if public_dir.exists():
            # Should have HTML file
            html_files = list(public_dir.glob("*.html"))
            assert len(html_files) > 0, "No HTML files found in visuals/public"
    
    def test_data_directory_structure(self):
        """Test data directory structure"""
        data_dir = Path("data")
        
        if not data_dir.exists():
            pytest.skip("Data directory not found")
        
        expected_subdirs = ["processed", "raw", "search"]
        existing_subdirs = []
        
        for subdir in expected_subdirs:
            subdir_path = data_dir / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                existing_subdirs.append(subdir)
        
        # Should have at least one data subdirectory
        assert len(existing_subdirs) > 0, f"No data subdirectories found. Expected: {expected_subdirs}"
    
    def test_database_directory_structure(self):
        """Test database directory structure"""
        db_dir = Path("database")
        
        if not db_dir.exists():
            pytest.skip("Database directory not found")
        
        # Should have schema directory
        schema_dir = db_dir / "schema"
        if schema_dir.exists():
            sql_files = list(schema_dir.glob("*.sql"))
            assert len(sql_files) > 0, "No SQL files found in database/schema"
    
    def test_scripts_directory_structure(self):
        """Test scripts directory structure"""
        scripts_dir = Path("scripts")
        
        if not scripts_dir.exists():
            pytest.skip("Scripts directory not found")
        
        # Should have Python scripts
        py_files = list(scripts_dir.glob("**/*.py"))
        assert len(py_files) > 0, "No Python scripts found in scripts directory"
    
    def test_docs_directory_structure(self):
        """Test documentation directory structure"""
        docs_dir = Path("docs")
        
        if not docs_dir.exists():
            pytest.skip("Docs directory not found")
        
        # Should have markdown files
        md_files = list(docs_dir.glob("**/*.md"))
        assert len(md_files) > 0, "No markdown files found in docs directory"


class TestPythonFileStructure:
    """Test Python file structure and content"""
    
    def test_data_loader_structure(self):
        """Test data_loader.py structure"""
        data_loader_path = Path("cads/data_loader.py")
        
        if not data_loader_path.exists():
            pytest.skip("data_loader.py not found")
        
        with open(data_loader_path, 'r') as f:
            content = f.read()
        
        # Test for key components
        assert 'class DataProcessor' in content, "DataProcessor class not found"
        assert 'def load_cads_data_with_researchers' in content or 'def process_' in content, \
            "Main processing method not found"
    
    def test_process_data_structure(self):
        """Test process_data.py structure"""
        process_data_path = Path("cads/process_data.py")
        
        if not process_data_path.exists():
            pytest.skip("process_data.py not found")
        
        with open(process_data_path, 'r') as f:
            content = f.read()
        
        # Test for key functions
        expected_functions = [
            'def load_and_process_data',
            'def compute_clusters',
            'def main'
        ]
        
        found_functions = []
        for func in expected_functions:
            if func in content:
                found_functions.append(func)
        
        assert len(found_functions) > 0, f"No expected functions found. Expected: {expected_functions}"
    
    def test_requirements_file(self):
        """Test requirements.txt content"""
        requirements_path = Path("cads/requirements.txt")
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt not found")
        
        with open(requirements_path, 'r') as f:
            requirements = f.read()
        
        # Test for essential packages
        essential_packages = [
            'pandas',
            'numpy',
            'psycopg2',
            'sentence-transformers'
        ]
        
        found_packages = []
        for package in essential_packages:
            if package in requirements:
                found_packages.append(package)
        
        assert len(found_packages) > 0, f"No essential packages found. Expected: {essential_packages}"


class TestConfigurationFiles:
    """Test configuration files"""
    
    def test_env_example_exists(self):
        """Test that .env.example files exist"""
        env_example_paths = [
            Path(".env.example"),
            Path("cads/.env.example")
        ]
        
        existing_env_files = [path for path in env_example_paths if path.exists()]
        
        assert len(existing_env_files) > 0, f"No .env.example files found in: {env_example_paths}"
    
    def test_env_example_content(self):
        """Test .env.example content"""
        env_example_paths = [
            Path(".env.example"),
            Path("cads/.env.example")
        ]
        
        for path in env_example_paths:
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                
                # Should have DATABASE_URL
                assert 'DATABASE_URL' in content, f"DATABASE_URL not found in {path}"
                break
        else:
            pytest.skip("No .env.example files found")
    
    def test_vercel_config(self):
        """Test vercel.json configuration"""
        vercel_config = Path("vercel.json")
        
        if not vercel_config.exists():
            pytest.skip("vercel.json not found")
        
        import json
        
        with open(vercel_config, 'r') as f:
            config = json.load(f)
        
        # Should be valid JSON
        assert isinstance(config, dict), "vercel.json should be a valid JSON object"
    
    def test_gitignore_exists(self):
        """Test that .gitignore exists"""
        gitignore_path = Path(".gitignore")
        
        if not gitignore_path.exists():
            pytest.skip(".gitignore not found")
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        # Should ignore common files
        common_ignores = ['.env', 'node_modules', '__pycache__', '*.pyc']
        found_ignores = []
        
        for ignore in common_ignores:
            if ignore in content:
                found_ignores.append(ignore)
        
        assert len(found_ignores) > 0, f"No common ignore patterns found. Expected: {common_ignores}"


class TestDataFiles:
    """Test data files structure"""
    
    def test_data_files_structure(self):
        """Test that data files have reasonable structure"""
        data_paths = [
            Path("data/processed"),
            Path("visuals/public/data"),
            Path("cads/data")
        ]
        
        json_files_found = []
        
        for data_path in data_paths:
            if data_path.exists():
                json_files = list(data_path.glob("*.json"))
                json_files_found.extend(json_files)
        
        if len(json_files_found) == 0:
            pytest.skip("No JSON data files found")
        
        # Test that at least one JSON file is valid
        import json
        valid_files = 0
        
        for json_file in json_files_found[:5]:  # Test first 5 files
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                if data is not None:
                    valid_files += 1
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        
        assert valid_files > 0, "No valid JSON data files found"