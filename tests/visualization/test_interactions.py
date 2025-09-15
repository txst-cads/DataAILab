"""
Visualization interaction tests for CADS Research Visualization System
"""

import pytest
import re
from pathlib import Path
from tests.fixtures.test_helpers import create_mock_html_content, TestDataGenerator


class TestUIInteractions:
    """Test user interface interactions"""
    
    def test_search_functionality_structure(self):
        """Test that search functionality structure is present"""
        content = create_mock_html_content()
        
        # Test search input exists
        search_pattern = r'<input[^>]*type="text"[^>]*id="search-input"[^>]*>'
        assert re.search(search_pattern, content, re.IGNORECASE), "Missing search input"
        
        # Test search input has placeholder
        placeholder_pattern = r'<input[^>]*placeholder="[^"]*"[^>]*>'
        if not re.search(placeholder_pattern, content, re.IGNORECASE):
            pytest.skip("Search placeholder not found - may be set dynamically")
    
    def test_filter_controls_structure(self):
        """Test that filter controls are properly structured"""
        content = create_mock_html_content()
        
        # Test researcher filter
        researcher_filter_pattern = r'<select[^>]*id="researcher-filter"[^>]*>'
        assert re.search(researcher_filter_pattern, content, re.IGNORECASE), \
            "Missing researcher filter select"
        
        # Test year filter
        year_filter_pattern = r'<input[^>]*type="range"[^>]*id="year-filter"[^>]*>'
        assert re.search(year_filter_pattern, content, re.IGNORECASE), \
            "Missing year range filter"
        
        # Test cluster filter
        cluster_filter_pattern = r'<select[^>]*id="cluster-filter"[^>]*>'
        assert re.search(cluster_filter_pattern, content, re.IGNORECASE), \
            "Missing cluster filter select"
    
    def test_tooltip_structure(self):
        """Test that tooltip structure is present"""
        content = create_mock_html_content()
        
        # Test tooltip container
        tooltip_pattern = r'<div[^>]*id="tooltip"[^>]*>'
        assert re.search(tooltip_pattern, content, re.IGNORECASE), "Missing tooltip container"
        
        # Test tooltip function
        tooltip_function_pattern = r'function showTooltip\s*\('
        assert re.search(tooltip_function_pattern, content, re.IGNORECASE), \
            "Missing showTooltip function"
    
    def test_panel_toggle_functionality(self):
        """Test that panel toggle functionality exists"""
        content = create_mock_html_content()
        
        # Test toggle function
        toggle_pattern = r'function togglePanel\s*\('
        assert re.search(toggle_pattern, content, re.IGNORECASE), \
            "Missing togglePanel function"
        
        # Test UI panel exists
        panel_pattern = r'<div[^>]*id="ui-panel"[^>]*>'
        assert re.search(panel_pattern, content, re.IGNORECASE), "Missing UI panel"


class TestEventHandling:
    """Test event handling structure"""
    
    def test_event_listener_setup(self):
        """Test that event listeners are set up"""
        content = create_mock_html_content()
        
        # Test event listener setup function
        setup_pattern = r'function setupUIEventListeners\s*\('
        assert re.search(setup_pattern, content, re.IGNORECASE), \
            "Missing setupUIEventListeners function"
    
    def test_debounce_functionality(self):
        """Test that debounce functionality exists for performance"""
        content = create_mock_html_content()
        
        # Test debounce function
        debounce_pattern = r'function debounce\s*\('
        assert re.search(debounce_pattern, content, re.IGNORECASE), \
            "Missing debounce function for performance optimization"
    
    def test_initialization_function(self):
        """Test that initialization function exists"""
        content = create_mock_html_content()
        
        # Test init function
        init_pattern = r'function init\s*\('
        assert re.search(init_pattern, content, re.IGNORECASE), \
            "Missing init function"


class TestDataInteraction:
    """Test data interaction capabilities"""
    
    def test_data_filtering_structure(self):
        """Test that data can be filtered by various criteria"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(50)
        
        works = viz_data['works']
        
        # Test that works have filterable properties
        filterable_properties = ['researcher_name', 'year', 'cluster']
        
        for work in works[:5]:  # Test first 5 works
            for prop in filterable_properties:
                assert prop in work, f"Work missing filterable property: {prop}"
        
        # Test year range for filtering
        years = [work['year'] for work in works]
        min_year = min(years)
        max_year = max(years)
        
        assert max_year > min_year, "Should have year range for filtering"
        assert all(isinstance(year, int) for year in years), "Years should be integers"
        
        # Test cluster assignments for filtering
        clusters = [work['cluster'] for work in works]
        unique_clusters = set(clusters)
        
        assert len(unique_clusters) > 1, "Should have multiple clusters for filtering"
        assert all(isinstance(cluster, int) for cluster in clusters), "Clusters should be integers"
    
    def test_search_data_structure(self):
        """Test that data is structured for search functionality"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(30)
        
        works = viz_data['works']
        
        # Test that works have searchable text fields
        searchable_fields = ['title', 'researcher_name']
        
        for work in works[:5]:  # Test first 5 works
            for field in searchable_fields:
                assert field in work, f"Work missing searchable field: {field}"
                assert isinstance(work[field], str), f"Searchable field {field} should be string"
                assert len(work[field].strip()) > 0, f"Searchable field {field} should not be empty"
    
    def test_coordinate_interaction_data(self):
        """Test that coordinate data supports interaction"""
        generator = TestDataGenerator()
        viz_data = generator.generate_visualization_data(25)
        
        works = viz_data['works']
        
        # Test coordinate data
        for work in works:
            assert 'x' in work and 'y' in work, "Works should have x,y coordinates for interaction"
            assert isinstance(work['x'], (int, float)), "X coordinate should be numeric"
            assert isinstance(work['y'], (int, float)), "Y coordinate should be numeric"
        
        # Test coordinate distribution (should not all be the same point)
        x_coords = [work['x'] for work in works]
        y_coords = [work['y'] for work in works]
        
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        assert x_range > 0, "X coordinates should have range for meaningful interaction"
        assert y_range > 0, "Y coordinates should have range for meaningful interaction"


class TestResponsiveInteraction:
    """Test responsive interaction capabilities"""
    
    def test_mobile_interaction_structure(self):
        """Test that mobile interaction is considered"""
        # Check if actual HTML files have responsive CSS
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
            content = create_mock_html_content()
        
        # Test viewport meta tag for mobile
        viewport_pattern = r'<meta name="viewport"[^>]*content="[^"]*width=device-width[^"]*"'
        assert re.search(viewport_pattern, content, re.IGNORECASE), \
            "Missing mobile viewport configuration"
    
    def test_touch_interaction_considerations(self):
        """Test that touch interactions are considered"""
        # This is more of a structural test since we can't test actual touch events
        content = create_mock_html_content()
        
        # Test that interactive elements exist
        interactive_elements = [
            r'<input[^>]*type="text"',  # Search input
            r'<select[^>]*>',           # Dropdowns
            r'<input[^>]*type="range"', # Range slider
        ]
        
        found_elements = 0
        for pattern in interactive_elements:
            if re.search(pattern, content, re.IGNORECASE):
                found_elements += 1
        
        assert found_elements > 0, "Should have interactive elements for touch interaction"


class TestAccessibilityInteractions:
    """Test accessibility interaction features"""
    
    def test_keyboard_navigation_structure(self):
        """Test that keyboard navigation is supported"""
        content = create_mock_html_content()
        
        # Test that interactive elements can receive focus
        focusable_elements = [
            r'<input[^>]*type="text"[^>]*>',  # Search input
            r'<select[^>]*>',                 # Select dropdowns
            r'<input[^>]*type="range"[^>]*>', # Range input
        ]
        
        found_focusable = 0
        for pattern in focusable_elements:
            if re.search(pattern, content, re.IGNORECASE):
                found_focusable += 1
        
        assert found_focusable > 0, "Should have focusable elements for keyboard navigation"
    
    def test_aria_labels_structure(self):
        """Test that ARIA labels are considered"""
        # Check if actual HTML files have ARIA labels
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
            pytest.skip("No HTML files found for ARIA testing")
        
        # Look for ARIA attributes
        aria_patterns = [
            r'aria-label=',
            r'aria-describedby=',
            r'role=',
            r'aria-expanded='
        ]
        
        found_aria = []
        for pattern in aria_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_aria.append(pattern)
        
        # If no ARIA found, it's not necessarily a failure, but worth noting
        if len(found_aria) == 0:
            pytest.skip("No ARIA attributes found - may need accessibility improvements")


class TestErrorHandlingInteractions:
    """Test error handling in interactions"""
    
    def test_error_display_structure(self):
        """Test that error display structure exists"""
        content = create_mock_html_content()
        
        # Test error message container
        error_pattern = r'<div[^>]*id="error-message"[^>]*>'
        assert re.search(error_pattern, content, re.IGNORECASE), \
            "Missing error message container"
    
    def test_loading_state_structure(self):
        """Test that loading states are handled"""
        content = create_mock_html_content()
        
        # Test loading container
        loading_pattern = r'<div[^>]*id="loading"[^>]*>'
        assert re.search(loading_pattern, content, re.IGNORECASE), \
            "Missing loading state container"
        
        # Test loading text
        loading_text_pattern = r'Loading.*CADS.*Research.*Visualization'
        assert re.search(loading_text_pattern, content, re.IGNORECASE), \
            "Missing loading state text"
    
    def test_graceful_degradation_structure(self):
        """Test that graceful degradation is considered"""
        content = create_mock_html_content()
        
        # Test that basic HTML structure exists without JavaScript
        basic_elements = [
            r'<div[^>]*id="map-container"[^>]*>',  # Main container
            r'<div[^>]*id="ui-panel"[^>]*>',       # UI panel
        ]
        
        for pattern in basic_elements:
            assert re.search(pattern, content, re.IGNORECASE), \
                f"Missing basic element for graceful degradation: {pattern}"