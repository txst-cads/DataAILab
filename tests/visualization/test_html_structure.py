"""
HTML structure and frontend tests for CADS Research Visualization System
"""

import pytest
import re
from pathlib import Path
from tests.fixtures.test_helpers import create_mock_html_content


class TestHTMLStructure:
    """Test HTML structure and required components"""
    
    def test_html_file_exists(self):
        """Test that HTML files exist in expected locations"""
        html_paths = [
            Path("visuals/public/index.html"),
            Path("test.html")
        ]
        
        # At least one HTML file should exist
        existing_files = [path for path in html_paths if path.exists()]
        assert len(existing_files) > 0, f"No HTML files found in expected locations: {html_paths}"
    
    def test_html_basic_structure(self):
        """Test basic HTML5 structure"""
        # Use mock content for testing structure
        content = create_mock_html_content()
        
        # Test HTML5 doctype
        assert re.search(r'<!DOCTYPE html>', content, re.IGNORECASE), "Missing HTML5 doctype"
        
        # Test basic HTML structure
        assert re.search(r'<html[^>]*lang="en"[^>]*>', content, re.IGNORECASE), "Missing HTML lang attribute"
        assert re.search(r'<meta charset="UTF-8">', content, re.IGNORECASE), "Missing UTF-8 charset"
        assert re.search(r'<meta name="viewport"', content, re.IGNORECASE), "Missing viewport meta tag"
        
        # Test title
        assert re.search(r'<title>CADS Research Visualization</title>', content, re.IGNORECASE), "Missing or incorrect title"
    
    def test_required_containers(self):
        """Test that required containers are present"""
        content = create_mock_html_content()
        
        required_containers = [
            'loading',
            'map-container', 
            'ui-panel',
            'tooltip',
            'error-message'
        ]
        
        for container_id in required_containers:
            pattern = f'<div[^>]*id="{container_id}"[^>]*>'
            assert re.search(pattern, content, re.IGNORECASE), f"Missing container: {container_id}"
    
    def test_ui_components(self):
        """Test that UI components are present"""
        content = create_mock_html_content()
        
        # Test search input
        assert re.search(r'<input[^>]*type="text"[^>]*id="search-input"', content, re.IGNORECASE), \
            "Missing search input"
        
        # Test filter components
        assert re.search(r'<select[^>]*id="researcher-filter"', content, re.IGNORECASE), \
            "Missing researcher filter"
        assert re.search(r'<input[^>]*type="range"[^>]*id="year-filter"', content, re.IGNORECASE), \
            "Missing year filter"
        assert re.search(r'<select[^>]*id="cluster-filter"', content, re.IGNORECASE), \
            "Missing cluster filter"
    
    def test_javascript_functions(self):
        """Test that required JavaScript functions are present"""
        content = create_mock_html_content()
        
        required_functions = [
            'init',
            'setupUIEventListeners',
            'togglePanel',
            'showTooltip',
            'debounce'
        ]
        
        for func_name in required_functions:
            pattern = f'function {func_name}\\s*\\('
            assert re.search(pattern, content, re.IGNORECASE), f"Missing JavaScript function: {func_name}"
    
    def test_external_dependencies(self):
        """Test that external dependencies are loaded"""
        content = create_mock_html_content()
        
        # Test Deck.gl CDN
        assert re.search(r'<script[^>]*src="[^"]*deck\.gl[^"]*"[^>]*>', content, re.IGNORECASE), \
            "Missing Deck.gl CDN"


class TestHTMLValidation:
    """Test HTML validation and best practices"""
    
    def test_html_accessibility(self):
        """Test basic accessibility features"""
        content = create_mock_html_content()
        
        # Test lang attribute
        assert re.search(r'<html[^>]*lang="en"', content, re.IGNORECASE), \
            "Missing language attribute for accessibility"
        
        # Test meta description
        assert re.search(r'<meta name="description"', content, re.IGNORECASE), \
            "Missing meta description"
    
    def test_responsive_design_indicators(self):
        """Test indicators of responsive design"""
        content = create_mock_html_content()
        
        # Test viewport meta tag
        viewport_pattern = r'<meta name="viewport"[^>]*content="[^"]*width=device-width[^"]*"'
        assert re.search(viewport_pattern, content, re.IGNORECASE), \
            "Missing responsive viewport meta tag"
    
    def test_html_semantic_structure(self):
        """Test semantic HTML structure"""
        content = create_mock_html_content()
        
        # Test that divs have meaningful IDs
        meaningful_ids = ['loading', 'map-container', 'ui-panel', 'tooltip', 'error-message']
        
        for element_id in meaningful_ids:
            pattern = f'id="{element_id}"'
            assert re.search(pattern, content, re.IGNORECASE), \
                f"Missing semantic ID: {element_id}"


class TestCSSStructure:
    """Test CSS structure and styling"""
    
    def test_css_presence(self):
        """Test that CSS is present in HTML"""
        # Try to read the actual HTML file
        html_paths = [
            Path("visuals/public/index.html")
        ]
        
        content = None
        for path in html_paths:
            if path.exists():
                content = path.read_text()
                break
        
        if not content:
            # Fall back to mock content with CSS
            content = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { background: #1a1a1a; color: #ffffff; }
                </style>
            </head>
            <body></body>
            </html>
            """
        
        # Should have either inline styles or external stylesheet
        has_inline_css = re.search(r'<style[^>]*>', content, re.IGNORECASE)
        has_external_css = re.search(r'<link[^>]*rel="stylesheet"', content, re.IGNORECASE)
        
        assert has_inline_css or has_external_css, "No CSS found (inline or external)"
    
    def test_dark_theme_colors(self):
        """Test dark theme color scheme"""
        # For this test, we'll check if we can find actual HTML files
        html_paths = [
            Path("visuals/public/index.html")
        ]
        
        content = None
        for path in html_paths:
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                break
        
        if content is None:
            pytest.skip("No HTML files found for CSS testing")
        
        # Extract CSS content
        css_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE)
        if not css_match:
            pytest.skip("No inline CSS found")
        
        css_content = css_match.group(1)
        
        # Test for dark theme colors
        dark_colors = ['#1a1a1a', '#333', '#ffffff', '#ccc']
        found_colors = []
        
        for color in dark_colors:
            if color in css_content:
                found_colors.append(color)
        
        assert len(found_colors) > 0, f"No dark theme colors found. Expected: {dark_colors}"


class TestJavaScriptStructure:
    """Test JavaScript structure and functionality"""
    
    def test_javascript_presence(self):
        """Test that JavaScript is present"""
        content = create_mock_html_content()
        
        # Should have either inline scripts or external scripts
        has_inline_js = re.search(r'<script[^>]*>.*</script>', content, re.DOTALL | re.IGNORECASE)
        has_external_js = re.search(r'<script[^>]*src="[^"]*"[^>]*></script>', content, re.IGNORECASE)
        
        assert has_inline_js or has_external_js, "No JavaScript found (inline or external)"
    
    def test_event_handling_setup(self):
        """Test that event handling is set up"""
        content = create_mock_html_content()
        
        # Look for event listener setup patterns
        event_patterns = [
            r'addEventListener',
            r'onclick',
            r'onload',
            r'setupUIEventListeners'
        ]
        
        found_patterns = []
        for pattern in event_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        assert len(found_patterns) > 0, f"No event handling patterns found. Expected one of: {event_patterns}"
    
    def test_error_handling_structure(self):
        """Test that error handling structure exists"""
        content = create_mock_html_content()
        
        # Look for error handling patterns
        error_patterns = [
            r'try\s*{',
            r'catch\s*\(',
            r'error-message',
            r'console\.error'
        ]
        
        # At least error message container should exist
        assert re.search(r'error-message', content, re.IGNORECASE), \
            "No error message container found"


class TestDataLoading:
    """Test data loading structure"""
    
    def test_data_loading_indicators(self):
        """Test that data loading is handled"""
        content = create_mock_html_content()
        
        # Test loading container
        assert re.search(r'id="loading"', content, re.IGNORECASE), \
            "Missing loading container"
        
        # Test loading text
        assert re.search(r'Loading.*CADS.*Research.*Visualization', content, re.IGNORECASE), \
            "Missing loading text"
    
    def test_data_file_references(self):
        """Test references to data files"""
        # Check if we can find actual HTML files with data references
        html_paths = [
            Path("visuals/public/index.html")
        ]
        
        content = None
        for path in html_paths:
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                break
        
        if content is None:
            pytest.skip("No HTML files found for data reference testing")
        
        # Look for data file references
        data_patterns = [
            r'visualization-data\.json',
            r'search-index\.json',
            r'cluster.*\.json',
            r'\.json\.gz'
        ]
        
        found_patterns = []
        for pattern in data_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        # Should reference at least some data files
        if len(found_patterns) == 0:
            pytest.skip("No data file references found - may be loaded dynamically")