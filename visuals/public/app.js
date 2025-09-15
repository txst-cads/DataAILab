// CADS Research Visualization Application
console.log('🎯 CADS Research Visualization - Initializing...');

// Application state
const app = {
    data: null,
    filteredData: null,
    searchIndex: null,
    clusterThemes: null,
    clusterCenters: null,
    deckgl: null,
    isLoading: true,
    currentZoom: 8,
    labelSizeCache: new Map(), // Cache for calculated label sizes
    
    // Performance monitoring
    performance: {
        loadStartTime: performance.now(),
        dataLoadTime: null,
        renderTime: null,
        interactionCount: 0,
        errorCount: 0
    },
    
    // Filter state tracking
    filterState: {
        researcher: '',
        themes: new Set(),
        keywords: [],
        keywordsLogic: 'AND',
        year: 2010
    },

    // UI elements
    elements: {
        loading: document.getElementById('loading'),
        loadingProgress: document.getElementById('loading-progress'),
        errorMessage: document.getElementById('error-message'),
        errorDetails: document.getElementById('error-details'),
        mapContainer: document.getElementById('map-container'),
        uiPanel: document.getElementById('ui-panel'),
        // panelToggle removed - sidebar is now permanent
        researcherInput: document.getElementById('researcher-input'),
        themeChecklist: document.getElementById('theme-checklist'),
        keywordsInput: document.getElementById('keywords-input'),
        addKeywordBtn: document.getElementById('add-keyword-btn'),
        keywordsLogic: document.getElementById('keywords-logic'),
        keywordsTags: document.getElementById('keywords-tags'),
        yearFilter: document.getElementById('year-filter'),
        yearDisplay: document.getElementById('year-display'),
        tooltip: document.getElementById('tooltip'),
        tooltipTitle: document.getElementById('tooltip-title'),
        tooltipAuthors: document.getElementById('tooltip-authors'),
        tooltipYear: document.getElementById('tooltip-year'),
        tooltipDetails: document.getElementById('tooltip-details'),
        tooltipAbstract: document.getElementById('tooltip-abstract'),
        tooltipMeta: document.getElementById('tooltip-meta'),
        visiblePapers: document.getElementById('visible-papers'),
        totalPapers: document.getElementById('total-papers'),
        totalResearchers: document.getElementById('total-researchers'),
        totalClusters: document.getElementById('total-clusters'),
        zoomIn: document.getElementById('zoom-in'),
        zoomOut: document.getElementById('zoom-out'),
        onboardingInfo: document.getElementById('onboarding-info'),
        onboardingClose: document.getElementById('onboarding-close')
    }
};

// Initialize the application
function init() {
    console.log('🚀 Starting CADS Research Visualization...');
    
    // Debug: Check if all required elements exist (development only)
    if (window.location.hostname === 'localhost') {
        const requiredElements = ['loading', 'mapContainer', 'uiPanel', 'researcherInput', 'themeChecklist'];
        for (const elementName of requiredElements) {
            if (!app.elements[elementName]) {
                console.error(`❌ Missing required element: ${elementName}`);
            }
        }
    }

    // Track application initialization
    trackEvent('App Initialization', {
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`
    });

    // Clear any existing label size cache to ensure fresh calculations
    clearLabelCacheIfNeeded();

    // Set up UI event listeners
    setupUIEventListeners();

    // Initialize onboarding info visibility
    initializeOnboarding();

    // Update loading progress
    updateLoadingProgress('Setting up interface...');

    // Load the visualization data and initialize
    loadVisualization();
}

// Initialize onboarding info visibility
function initializeOnboarding() {
    try {
        if (app.elements.onboardingInfo) {
            // Check if user has previously dismissed the onboarding
            const dismissed = localStorage.getItem('cads-onboarding-dismissed');
            if (dismissed === 'true') {
                app.elements.onboardingInfo.classList.add('hidden');
            }
            // If not dismissed, it will show by default

        } else {
            console.warn('Onboarding element not found');
        }
    } catch (error) {
        console.error('Error initializing onboarding:', error);
    }
}

// Set up UI event listeners
function setupUIEventListeners() {
    // Panel toggle removed - sidebar is now permanent

    // Year filter
    app.elements.yearFilter.addEventListener('input', (e) => {
        app.elements.yearDisplay.textContent = e.target.value;
        applyFilters();
    });

    // Researcher input (real-time filtering)
    app.elements.researcherInput.addEventListener('input', debounce((e) => {
        applyFilters();
    }, 300));

    // Keywords input and add button
    app.elements.keywordsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addKeywordTag();
        }
    });

    app.elements.addKeywordBtn.addEventListener('click', addKeywordTag);

    // Keywords logic toggle
    app.elements.keywordsLogic.addEventListener('change', (e) => {
        const toggleText = e.target.parentElement.querySelector('.toggle-text');
        toggleText.textContent = e.target.checked ? 'Match ALL keywords' : 'Match ANY keyword';
        applyFilters();
    });

    // Zoom controls
    if (app.elements.zoomIn) {
        app.elements.zoomIn.addEventListener('click', () => {
            zoomMap(1);
        });
    }

    if (app.elements.zoomOut) {
        app.elements.zoomOut.addEventListener('click', () => {
            zoomMap(-1);
        });
    }

    // Onboarding info close
    if (app.elements.onboardingClose && app.elements.onboardingInfo) {
        app.elements.onboardingClose.addEventListener('click', () => {
            try {
                app.elements.onboardingInfo.classList.add('hidden');
                // Store preference to not show again
                localStorage.setItem('cads-onboarding-dismissed', 'true');
            } catch (error) {
                console.error('Error closing onboarding:', error);
            }
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideTooltip();
            // Also hide onboarding if visible
            if (app.elements.onboardingInfo && !app.elements.onboardingInfo.classList.contains('hidden')) {
                app.elements.onboardingInfo.classList.add('hidden');
            }
        }
        if (e.key === '/' && !e.target.matches('input')) {
            e.preventDefault();
            if (app.elements.researcherInput) {
                app.elements.researcherInput.focus();
            }
        }
        // Zoom shortcuts
        if (e.key === '+' || e.key === '=') {
            e.preventDefault();
            if (app.elements.zoomIn) {
                app.elements.zoomIn.click();
            }
        }
        if (e.key === '-') {
            e.preventDefault();
            if (app.elements.zoomOut) {
                app.elements.zoomOut.click();
            }
        }
    });
}

// Toggle UI panel - REMOVED (sidebar is now permanent)
// function togglePanel() {
//     // Sidebar is now permanent, no toggle functionality needed
// }

// Update loading progress
function updateLoadingProgress(message) {
    app.elements.loadingProgress.textContent = message;
}

// Show error message
function showError(title, details) {
    app.elements.errorMessage.querySelector('.error-title').textContent = title;
    app.elements.errorDetails.textContent = details;
    app.elements.errorMessage.style.display = 'block';

    // Track error occurrence
    app.performance.errorCount++;
    trackEvent('Application Error', {
        error_title: title,
        error_details: details,
        error_count: app.performance.errorCount,
        timestamp: new Date().toISOString()
    });

    // Report to Sentry if available
    if (typeof Sentry !== 'undefined') {
        Sentry.captureMessage(`${title}: ${details}`, 'error');
    }

    // Auto-hide after 10 seconds
    setTimeout(() => {
        app.elements.errorMessage.style.display = 'none';
    }, 10000);
}

// Hide loading screen
function hideLoading() {
    app.elements.loading.classList.add('hidden');
    app.isLoading = false;

    // Remove loading element after transition
    setTimeout(() => {
        app.elements.loading.style.display = 'none';
    }, 300);
}

// Show simple tooltip first, then enhance
function showTooltip(x, y, workData) {
    // console.log('Showing tooltip for:', workData.title);
    
    const tooltip = app.elements.tooltip;
    if (!tooltip) {
        console.error('Tooltip element not found');
        return;
    }

    // Simple approach - just show basic info first
    const title = workData.title || 'Untitled Work';
    const authors = workData.authors || 'Unknown Authors';
    const year = workData.year || 'Unknown Year';
    
    // Set basic content
    tooltip.innerHTML = `
        <div style="color: #D7BD8A; font-weight: bold; font-size: 16px; margin-bottom: 8px;">
            ${title}
        </div>
        <div style="color: white; font-size: 13px; margin-bottom: 4px;">
            ${authors}
        </div>
        <div style="color: #AC9155; font-size: 12px;">
            ${year}
        </div>
    `;

    // Show tooltip with direct styling
    tooltip.style.display = 'block';
    tooltip.style.visibility = 'visible';
    tooltip.style.opacity = '1';
    tooltip.style.background = '#501214';
    tooltip.style.border = '2px solid #AC9155';
    tooltip.style.borderRadius = '8px';
    tooltip.style.padding = '16px';
    tooltip.style.position = 'fixed';
    tooltip.style.top = '80px';
    tooltip.style.right = '350px';
    tooltip.style.width = '300px';
    tooltip.style.zIndex = '1000';
    
    // console.log('Simple tooltip should be visible now');
}

// Hide tooltip
function hideTooltip() {
    const tooltip = app.elements.tooltip;
    if (tooltip) {
        tooltip.style.display = 'none';
        tooltip.style.visibility = 'hidden';
        tooltip.classList.remove('visible');
    }
}

// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load and initialize the visualization
async function loadVisualization() {
    try {
        updateLoadingProgress('Loading research data...');

        // Try to load data - start with uncompressed for local development
        let response;
        let dataUrl = '';
        let data;

        try {
            // Try uncompressed first for local development
            dataUrl = '/data/visualization-data.json?v=' + Date.now();
            response = await fetch(dataUrl);
            if (response.ok) {
                console.log('✅ Loading uncompressed data from:', dataUrl);
                data = await response.json();
            } else {
                throw new Error('Uncompressed data not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed data failed, trying compressed...');
            try {
                dataUrl = '/data/visualization-data.json.gz?v=' + Date.now();
                response = await fetch(dataUrl);
                if (!response.ok) throw new Error('Compressed data not available');
                console.log('✅ Loading compressed data from:', dataUrl);
                data = await response.json();
            } catch (gzError) {
                throw new Error(`Failed to load data from both sources. Uncompressed: ${e.message}, Compressed: ${gzError.message}`);
            }
        }

        // Validate data structure
        if (!data.p || !Array.isArray(data.p)) {
            throw new Error('Invalid data format: missing publications array');
        }
        if (!data.r || !Array.isArray(data.r)) {
            throw new Error('Invalid data format: missing researchers array');
        }
        if (!data.c || !Array.isArray(data.c)) {
            throw new Error('Invalid data format: missing clusters array');
        }

        console.log(`📊 Loaded ${data.p.length} publications, ${data.r.length} researchers, ${data.c.length} clusters`);
        app.data = data;

        updateLoadingProgress('Loading cluster themes...');

        // Load cluster themes and centers
        await loadClusterData();

        updateLoadingProgress('Processing data...');

        // Update UI with metadata
        app.elements.totalPapers.textContent = data.meta.totalPapers.toLocaleString();
        app.elements.totalResearchers.textContent = data.meta.totalResearchers;
        app.elements.totalClusters.textContent = data.meta.totalClusters;

        // Populate filter dropdowns
        populateFilters(data);

        updateLoadingProgress('Initializing visualization...');

        // Initialize Deck.gl visualization
        initializeDeckGL(data);

        updateLoadingProgress('Ready!');

        setTimeout(() => {
            hideLoading();
            
            // Track successful load
            app.performance.dataLoadTime = performance.now() - app.performance.loadStartTime;
            trackEvent('Data Load Complete', {
                load_time_ms: Math.round(app.performance.dataLoadTime),
                publications_count: data.p.length,
                researchers_count: data.r.length,
                clusters_count: data.c.length,
                timestamp: new Date().toISOString()
            });
            
            console.log('✅ CADS Research Visualization - Loaded successfully!');
            console.log(`📊 Displaying ${data.p.length} publications from ${data.r.length} researchers`);
            console.log(`⏱️ Load time: ${Math.round(app.performance.dataLoadTime)}ms`);
        }, 300);

    } catch (error) {
        console.error('Failed to load visualization:', error);
        
        // Track load failure
        trackEvent('Data Load Failed', {
            error_message: error.message,
            load_time_ms: Math.round(performance.now() - app.performance.loadStartTime),
            timestamp: new Date().toISOString()
        });
        
        // Report to Sentry if available
        if (typeof Sentry !== 'undefined') {
            Sentry.captureException(error, {
                tags: {
                    component: 'data-loading'
                },
                extra: {
                    loadTime: performance.now() - app.performance.loadStartTime
                }
            });
        }
        
        showError('Loading Failed', `Could not load visualization data: ${error.message}`);
        hideLoading();
    }
}

// Generate consistent color for a cluster ID
function generateClusterColor(clusterId) {
    // Use a simple hash function to generate consistent colors
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
        '#A3E4D7', '#F9E79F', '#D5A6BD', '#AED6F1', '#A9DFBF',
        '#F5B7B1', '#D2B4DE', '#A9CCE3', '#A3E4D7', '#F7DC6F',
        '#D7BDE2', '#AED6F1', '#A9DFBF', '#F5B7B1', '#D2B4DE',
        '#A9CCE3', '#A3E4D7', '#F7DC6F'
    ];
    
    return colors[clusterId % colors.length];
}

// Populate filter UI with data
function populateFilters(data) {
    // Populate theme checklist
    const themeChecklist = app.elements.themeChecklist;
    themeChecklist.innerHTML = ''; // Clear existing items
    
    data.c.forEach(cluster => {
        const themeItem = document.createElement('div');
        themeItem.className = 'theme-item';
        
        // Generate consistent color for this cluster
        const themeColor = generateClusterColor(cluster.i);
        
        themeItem.innerHTML = `
            <input type="checkbox" class="theme-checkbox" id="theme-${cluster.i}" value="${cluster.i}" checked>
            <div class="theme-color-swatch" style="background-color: ${themeColor}"></div>
            <label class="theme-name" for="theme-${cluster.i}">${cluster.n}</label>
        `;
        
        // Add event listener for theme checkbox
        const checkbox = themeItem.querySelector('.theme-checkbox');
        checkbox.addEventListener('change', applyFilters);
        
        themeChecklist.appendChild(themeItem);
    });
}

// Load cluster data (themes and centers)
async function loadClusterData() {
    try {
        console.log('🎨 Loading cluster themes...');
        // Try uncompressed first for local development
        let themesResponse;
        let themesUrl = '';
        try {
            themesUrl = '/data/cluster_themes.json';
            themesResponse = await fetch(themesUrl);
            if (themesResponse.ok) {
                const themesData = await themesResponse.json();
                app.clusterThemes = themesData.themes || themesData;
                console.log(`✅ Loaded ${Object.keys(app.clusterThemes).length} cluster themes from ${themesUrl}`);
            } else {
                throw new Error('Uncompressed themes not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed themes failed, trying compressed...');
            try {
                themesUrl = '/data/cluster_themes.json.gz';
                themesResponse = await fetch(themesUrl);
                if (themesResponse.ok) {
                    const themesData = await themesResponse.json();
                    app.clusterThemes = themesData.themes || themesData;
                    console.log(`✅ Loaded ${Object.keys(app.clusterThemes).length} cluster themes from ${themesUrl}`);
                } else {
                    throw new Error('Compressed themes not available');
                }
            } catch (gzError) {
                console.warn(`⚠️ Failed to load cluster themes from both sources:`, e.message, gzError.message);
            }
        }

        console.log('📍 Loading cluster centers...');
        // Try uncompressed first for local development
        let centersResponse;
        let centersUrl = '';
        try {
            centersUrl = '/data/clustering_results.json';
            centersResponse = await fetch(centersUrl);
            if (centersResponse.ok) {
                const centersData = await centersResponse.json();
                app.clusterCenters = centersData.cluster_info || centersData;
                console.log(`✅ Loaded ${Object.keys(app.clusterCenters).length} cluster centers from ${centersUrl}`);
            } else {
                throw new Error('Uncompressed centers not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed centers failed, trying compressed...');
            try {
                centersUrl = '/data/clustering_results.json.gz';
                centersResponse = await fetch(centersUrl);
                if (centersResponse.ok) {
                    const centersData = await centersResponse.json();
                    app.clusterCenters = centersData.cluster_info || centersData;
                    console.log(`✅ Loaded ${Object.keys(app.clusterCenters).length} cluster centers from ${centersUrl}`);
                } else {
                    throw new Error('Compressed centers not available');
                }
            } catch (gzError) {
                console.warn(`⚠️ Failed to load cluster centers from both sources:`, e.message, gzError.message);
            }
        }
    } catch (error) {
        console.warn('⚠️ Could not load cluster data:', error);
        // Continue without cluster labels if data is not available
        app.clusterThemes = {};
        app.clusterCenters = {};
    }
}

// Calculate optimal view state from publication coordinates
function calculateOptimalViewState(publications) {
    if (!publications || publications.length === 0) {
        console.warn('No publications data available for view state calculation');
        return {
            longitude: 0,
            latitude: 0,
            zoom: 8
        };
    }

    // Extract all publication positions
    const positions = publications.map(p => p.p).filter(pos => pos && pos.length >= 2);

    if (positions.length === 0) {
        console.warn('No valid position data found in publications');
        return {
            longitude: 0,
            latitude: 0,
            zoom: 8
        };
    }

    // Calculate bounds
    const bounds = {
        minX: Math.min(...positions.map(pos => pos[0])),
        maxX: Math.max(...positions.map(pos => pos[0])),
        minY: Math.min(...positions.map(pos => pos[1])),
        maxY: Math.max(...positions.map(pos => pos[1]))
    };

    // Calculate center point
    const centerX = (bounds.minX + bounds.maxX) / 2;
    const centerY = (bounds.minY + bounds.maxY) / 2;

    // Calculate optimal zoom level based on data spread
    const dataWidth = bounds.maxX - bounds.minX;
    const dataHeight = bounds.maxY - bounds.minY;
    const maxSpread = Math.max(dataWidth, dataHeight);

    // Determine zoom level - smaller spread needs higher zoom, larger spread needs lower zoom
    // Add some padding by using a factor less than 1.0
    let optimalZoom;
    if (maxSpread === 0) {
        optimalZoom = 8; // Default zoom for single point
    } else if (maxSpread < 5) {
        optimalZoom = 7; // High zoom for tightly clustered data
    } else if (maxSpread < 15) {
        optimalZoom = 6; // Medium zoom for moderate spread
    } else if (maxSpread < 25) {
        optimalZoom = 5; // Lower zoom for wide spread
    } else {
        optimalZoom = 4; // Very low zoom for very wide spread
    }

    // Removed logging for better performance

    return {
        longitude: centerX,
        latitude: centerY,
        zoom: optimalZoom,
        bounds: bounds
    };
}

// Initialize Deck.gl visualization
function initializeDeckGL(data) {
    console.log(`🎯 Initializing DeckGL with ${data.p.length} publications`);

    // Calculate optimal view state from publication coordinates
    const optimalViewState = calculateOptimalViewState(data.p);

    // Removed logging for better performance

    // Store initial zoom level
    app.currentZoom = optimalViewState.zoom;

    // Create the Deck.gl instance
    app.deckgl = new deck.DeckGL({
        container: 'map-container',
        initialViewState: {
            longitude: optimalViewState.longitude,
            latitude: optimalViewState.latitude,
            zoom: optimalViewState.zoom,
            pitch: 0,
            bearing: 0
        },
        controller: true,
        layers: createAllLayers(data, data.p),
        onHover: handleHover,
        onClick: handleClick,
        onViewStateChange: handleViewStateChange,
        getCursor: () => 'crosshair'
    });

    // Update visible papers count
    app.elements.visiblePapers.textContent = data.p.length.toLocaleString();
}

// Handle view state changes (zoom, pan)
// Throttled layer update to prevent performance issues
let layerUpdateTimeout = null;

function handleViewStateChange({ viewState }) {
    const previousZoom = app.currentZoom;
    app.currentZoom = viewState.zoom;

    // Clear any pending updates
    if (layerUpdateTimeout) {
        clearTimeout(layerUpdateTimeout);
    }

    // Check if we've crossed a significant zoom threshold (simplified check)
    const zoomDifference = Math.abs(app.currentZoom - previousZoom);
    const crossedMajorThreshold = Math.floor(previousZoom) !== Math.floor(app.currentZoom);

    // Only update if we've made a significant zoom change
    if (crossedMajorThreshold && zoomDifference > 0.5) {
        // Throttle updates to prevent excessive re-rendering
        layerUpdateTimeout = setTimeout(() => {
            if (app.deckgl && app.data) {
                const currentData = getCurrentFilteredData();
                app.deckgl.setProps({
                    layers: createAllLayers(app.data, currentData)
                });
            }
        }, 100); // 100ms throttle
    }
}

// Zoom map function for zoom controls
function zoomMap(direction) {
    if (!app.deckgl) {
        console.warn('Deck.gl not initialized');
        return;
    }

    try {
        // Simulate mouse wheel event to trigger zoom
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            const wheelEvent = new WheelEvent('wheel', {
                deltaY: direction > 0 ? -100 : 100, // Negative for zoom in, positive for zoom out
                bubbles: true,
                cancelable: true
            });
            mapContainer.dispatchEvent(wheelEvent);
    
        }
    } catch (error) {
        console.error('Error in zoomMap:', error);
    }
}

// Get currently filtered data
function getCurrentFilteredData() {
    if (!app.data) return [];

    let filteredData = app.data.p;

    // Update filter state and apply researcher name filtering
    const researcherQuery = app.elements.researcherInput.value.trim().toLowerCase();
    app.filterState.researcher = researcherQuery;
    
    if (researcherQuery) {
        filteredData = filteredData.filter(p => {
            const researcher = app.data.r.find(r => r.i === p.r);
            return researcher && researcher.n.toLowerCase().includes(researcherQuery);
        });
    }

    // Update filter state and apply research theme filtering
    const checkedThemes = Array.from(app.elements.themeChecklist.querySelectorAll('.theme-checkbox:checked'))
        .map(checkbox => parseInt(checkbox.value));
    app.filterState.themes = new Set(checkedThemes);
    
    if (checkedThemes.length > 0 && checkedThemes.length < app.data.c.length) {
        filteredData = filteredData.filter(p => checkedThemes.includes(p.c));
    }

    // Update filter state and apply keywords filtering
    const keywordTags = Array.from(app.elements.keywordsTags.querySelectorAll('.keyword-tag'));
    const keywords = keywordTags.map(tag => tag.dataset.keyword.toLowerCase());
    const useAndLogic = app.elements.keywordsLogic.checked;
    
    app.filterState.keywords = keywords;
    app.filterState.keywordsLogic = useAndLogic ? 'AND' : 'OR';
    
    if (keywords.length > 0) {
        filteredData = filteredData.filter(p => {
            // Search in paper title (assuming p.t is title)
            const title = (p.t || '').toLowerCase();
            
            if (useAndLogic) {
                // ALL keywords must match
                return keywords.every(keyword => title.includes(keyword));
            } else {
                // ANY keyword can match
                return keywords.some(keyword => title.includes(keyword));
            }
        });
    }

    // Update filter state and apply publication year filtering
    const yearFilter = parseInt(app.elements.yearFilter.value);
    app.filterState.year = yearFilter;
    
    if (yearFilter) {
        filteredData = filteredData.filter(p => p.y >= yearFilter);
    }

    // Store filtered data for reference
    app.filteredData = filteredData;

    return filteredData;
}

// Create all layers (scatterplot + text labels)
function createAllLayers(fullData, publications) {
    const layers = [createScatterplotLayerWithData(fullData, publications)];

    // Add cluster theme labels if data is available and zoom level is appropriate
    if (app.clusterThemes && app.clusterCenters && shouldShowLabels()) {
        try {
            const labelLayer = createClusterLabelsLayer(fullData, publications);
            if (labelLayer) {
                layers.push(labelLayer);
            }
        } catch (error) {
            console.error('Error creating cluster labels layer:', error);
        }
    }

    return layers;
}

// Progressive disclosure configuration for zoom-based label visibility
const ZOOM_DISCLOSURE_CONFIG = {
    // Simplified zoom thresholds for better performance
    showLabelsZoom: 4,       // Minimum zoom to show any labels (lowered from 6)
    showAllZoom: 6,          // Zoom level to show all clusters (lowered from 8)
    majorClusterSize: 40,    // Major clusters (lowered from 50)
    minClusterSize: 20       // Minimum cluster size (lowered from 30)
};

// Simplified label visibility check
function shouldShowLabels() {
    const shouldShow = app.currentZoom >= ZOOM_DISCLOSURE_CONFIG.showLabelsZoom;
    // console.log(`🔍 shouldShowLabels: zoom=${app.currentZoom.toFixed(1)}, threshold=${ZOOM_DISCLOSURE_CONFIG.showLabelsZoom}, result=${shouldShow}`);
    return shouldShow;
}

// Simplified cluster size threshold
function getClusterSizeThresholdForZoom(zoomLevel) {
    if (zoomLevel >= ZOOM_DISCLOSURE_CONFIG.showAllZoom) {
        return ZOOM_DISCLOSURE_CONFIG.minClusterSize;
    } else if (zoomLevel >= ZOOM_DISCLOSURE_CONFIG.showLabelsZoom) {
        return ZOOM_DISCLOSURE_CONFIG.majorClusterSize;
    } else {
        return Infinity;
    }
}

// Dynamic label sizing configuration
const LABEL_SIZE_CONFIG = {
    minSize: 8,          // Minimum readable label size (px) - for small clusters
    maxSize: 18,         // Maximum label size (px) - for major clusters
    scalingFactor: 1.2,  // Logarithmic scaling factor - slightly increased for better tier differentiation
    sizeThreshold: 25    // Minimum cluster size to show label (used as fallback)
};

// Calculate dynamic label size based on cluster paper count
function calculateLabelSize(clusterSize, minSize = LABEL_SIZE_CONFIG.minSize, maxSize = LABEL_SIZE_CONFIG.maxSize) {
    // Input validation
    if (!clusterSize || clusterSize < 1) {
        return minSize;
    }

    // Check cache first for performance
    const cacheKey = `${clusterSize}-${minSize}-${maxSize}`;
    if (app.labelSizeCache.has(cacheKey)) {
        return app.labelSizeCache.get(cacheKey);
    }

    // Logarithmic scaling algorithm
    // Use natural log to create smooth scaling curve
    const logSize = Math.log(clusterSize);
    const scaledSize = minSize + (logSize * LABEL_SIZE_CONFIG.scalingFactor);

    // Apply min/max constraints
    const constrainedSize = Math.max(minSize, Math.min(maxSize, scaledSize));

    // Round to nearest integer for pixel-perfect rendering
    const finalSize = Math.round(constrainedSize);

    // Cache the result for performance
    app.labelSizeCache.set(cacheKey, finalSize);

    return finalSize;
}

// Clear label size cache (called when configuration changes)
function clearLabelSizeCache() {
    app.labelSizeCache.clear();
}

// Invalidate cache entries for clusters that are no longer visible
// Simplified cache management
function clearLabelCacheIfNeeded() {
    if (app.labelSizeCache.size > 500) {
        app.labelSizeCache.clear();
    }
}

// Create cluster theme labels layer
function createClusterLabelsLayer(fullData, publications) {
    // Get unique clusters from current publications
    const visibleClusters = new Set(publications.map(p => p.c).filter(c => c !== -1));

    // Get the appropriate cluster size threshold for current zoom level
    const zoomThreshold = getClusterSizeThresholdForZoom(app.currentZoom);

    // Create label data for visible clusters (simplified for performance)
    const labelData = [];
    visibleClusters.forEach(clusterId => {
        const clusterInfo = app.clusterCenters[clusterId.toString()];
        const themeName = app.clusterThemes[clusterId.toString()];

        // Only show clusters that meet the zoom-based size threshold
        if (clusterInfo && themeName && clusterInfo.size >= zoomThreshold) {
            labelData.push({
                position: clusterInfo.center,
                text: themeName,
                clusterId: clusterId,
                size: clusterInfo.size
            });
        }
    });

    // Debug logging to check label creation
    console.log(`🏷️ Labels: ${labelData.length} created (zoom: ${app.currentZoom.toFixed(1)}, threshold: ${zoomThreshold})`);
    if (labelData.length === 0) {
        console.log(`🔍 Debug: visibleClusters=${visibleClusters.size}, clusterThemes=${!!app.clusterThemes}, clusterCenters=${!!app.clusterCenters}`);
    }

    // Check if TextLayer is available
    if (!deck.TextLayer) {
        console.warn('TextLayer not available in this Deck.gl version');
        return null;
    }

    return new deck.TextLayer({
        id: 'cluster-labels-layer',
        data: labelData,

        // Position
        getPosition: d => [d.position[0], d.position[1], 1], // Slightly elevated

        // Text properties
        getText: d => d.text,
        getSize: d => calculateLabelSize(d.size), // Dynamic size based on cluster size
        getColor: [255, 255, 255, 200], // White text with slight transparency

        // Font and styling
        fontFamily: 'Arial, sans-serif',
        fontWeight: 'bold',

        // Alignment
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'center',

        // Interaction
        pickable: false,

        // Performance
        updateTriggers: {
            getPosition: publications,
            getText: app.clusterThemes
        }
    });
}

// Create scatterplot layer with optimized data
function createScatterplotLayerWithData(fullData, publications) {
    return new deck.ScatterplotLayer({
        id: 'publications-layer',
        data: publications,

        // Position from pre-computed UMAP coordinates
        getPosition: d => [d.p[0], d.p[1], 0],

        // Size and color
        getRadius: 3,
        getFillColor: d => {
            const researcher = fullData.r.find(r => r.i === d.r);
            return researcher ? researcher.col : [128, 128, 128];
        },

        // Interaction
        pickable: true,
        autoHighlight: true,

        // Performance optimizations
        radiusMinPixels: 1,
        radiusMaxPixels: 12,

        // Update triggers for efficient re-rendering
        updateTriggers: {
            getFillColor: publications,
            getPosition: publications
        }
    });
}

// Handle hover events
function handleHover(info) {
    if (info.object && info.x !== undefined && info.y !== undefined) {
        const publication = info.object;
        const researcher = app.data.r.find(r => r.i === publication.r);
        const cluster = app.data.c.find(c => c.i === publication.c);

        // Create enhanced work data object for tooltip
        const workData = {
            title: publication.t || 'Untitled Work',
            authors: researcher ? researcher.n : 'Unknown Author',
            year: publication.y || 'Unknown Year',
            abstract: publication.a || 'No abstract available for this work.',
            cit: publication.cit || 0,
            doi: publication.doi || 'Not available',
            venue: publication.v || publication.j || '', // venue or journal
            cluster: publication.c,
            researcher: researcher ? researcher.n : 'Unknown'
        };

        showTooltip(info.x, info.y, workData);
    } else {
        hideTooltip();
    }
}

// Handle click events
function handleClick(info) {
    if (info.object) {
        const publication = info.object;
        const researcher = app.data.r.find(r => r.i === publication.r);
        
        // Track paper click interaction
        trackUserInteraction('Paper Click', {
            paper_title: publication.t || 'Untitled',
            researcher_name: researcher ? researcher.n : 'Unknown',
            publication_year: publication.y || 'Unknown',
            has_doi: !!publication.d,
            cluster_id: publication.c
        });

        // Could implement paper details modal here
        if (publication.d) {
            // Open DOI link if available
            window.open(`https://doi.org/${publication.d}`, '_blank');
        }
    }
}

// Add keyword tag
function addKeywordTag() {
    const input = app.elements.keywordsInput;
    const keyword = input.value.trim();
    
    if (!keyword) return;
    
    // Check if keyword already exists
    const existingTags = Array.from(app.elements.keywordsTags.querySelectorAll('.keyword-tag'));
    const existingKeywords = existingTags.map(tag => tag.dataset.keyword.toLowerCase());
    
    if (existingKeywords.includes(keyword.toLowerCase())) {
        input.value = '';
        return;
    }
    
    // Track keyword addition
    trackUserInteraction('Keyword Added', {
        keyword: keyword,
        existing_keywords_count: existingKeywords.length
    });
    
    // Create keyword tag
    const tag = document.createElement('div');
    tag.className = 'keyword-tag';
    tag.dataset.keyword = keyword;
    tag.innerHTML = `
        <span>${keyword}</span>
        <button class="keyword-tag-remove" type="button" title="Remove keyword">×</button>
    `;
    
    // Add remove functionality
    tag.querySelector('.keyword-tag-remove').addEventListener('click', () => {
        trackUserInteraction('Keyword Removed', {
            keyword: keyword
        });
        tag.remove();
        applyFilters();
    });
    
    app.elements.keywordsTags.appendChild(tag);
    input.value = '';
    
    // Apply filters with new keyword
    applyFilters();
}

// Check if any filters are currently active
function hasActiveFilters() {
    return app.filterState.researcher !== '' ||
           app.filterState.themes.size < app.data.c.length ||
           app.filterState.keywords.length > 0 ||
           app.filterState.year > 2010; // Assuming 2010 is the minimum year
}

// Get filter summary for debugging/logging
function getFilterSummary() {
    return {
        researcher: app.filterState.researcher || 'All',
        themes: app.filterState.themes.size === app.data.c.length ? 'All' : `${app.filterState.themes.size} selected`,
        keywords: app.filterState.keywords.length === 0 ? 'None' : `${app.filterState.keywords.length} (${app.filterState.keywordsLogic})`,
        year: `>= ${app.filterState.year}`,
        hasFilters: hasActiveFilters()
    };
}

// Apply filters to the visualization
function applyFilters() {
    if (!app.deckgl || !app.data) return;

    const startTime = performance.now();
    const filteredData = getCurrentFilteredData();

    // Update layers with filtered data
    app.deckgl.setProps({
        layers: createAllLayers(app.data, filteredData)
    });

    // Update visible papers count
    app.elements.visiblePapers.textContent = filteredData.length.toLocaleString();

    // Track filter performance and usage
    const filterTime = performance.now() - startTime;
    if (hasActiveFilters()) {
        const filterSummary = getFilterSummary();
        trackUserInteraction('Filter Applied', {
            filter_time_ms: Math.round(filterTime),
            results_count: filteredData.length,
            total_count: app.data.p.length,
            filter_summary: filterSummary
        });
        
        // Development logging only
        if (window.location.hostname === 'localhost') {
            console.log('🔍 Active filters:', filterSummary);
            console.log(`📊 Filtered results: ${filteredData.length}/${app.data.p.length} papers`);
        }
    }
}

// Perform search (placeholder - would need search index implementation)
function performSearch(query) {
    if (!query.trim()) {
        // Reset to show all data
        applyFilters();
        return;
    }

    // Apply current filters (search functionality integrated)
    applyFilters();
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        try {
            init();
        } catch (error) {
            console.error('❌ Initialization error:', error);
            if (window.showError) {
                window.showError('Initialization Error', error.message);
            }
        }
    });
} else {
    try {
        init();
    } catch (error) {
        console.error('❌ Initialization error:', error);
        if (window.showError) {
            window.showError('Initialization Error', error.message);
        }
    }
}

// Monitoring and Analytics Functions
function trackEvent(eventName, properties = {}) {
    try {
        // Track with Vercel Analytics
        if (window.va) {
            window.va('track', eventName, properties);
        }
        
        // Track with Sentry (for performance events)
        if (typeof Sentry !== 'undefined' && eventName.includes('Performance')) {
            Sentry.addBreadcrumb({
                message: eventName,
                category: 'performance',
                data: properties,
                level: 'info'
            });
        }
        
        // Console log for development
        if (window.location.hostname === 'localhost') {
            console.log(`📊 Event: ${eventName}`, properties);
        }
    } catch (error) {
        console.warn('Failed to track event:', error);
    }
}

function trackPerformance(metricName, value, unit = 'ms') {
    trackEvent('Performance Metric', {
        metric: metricName,
        value: value,
        unit: unit,
        timestamp: new Date().toISOString()
    });
}

function trackUserInteraction(interactionType, details = {}) {
    app.performance.interactionCount++;
    trackEvent('User Interaction', {
        interaction_type: interactionType,
        interaction_count: app.performance.interactionCount,
        ...details,
        timestamp: new Date().toISOString()
    });
}

// Enhanced error boundary for async operations
function withErrorBoundary(asyncFn, context = 'unknown') {
    return async (...args) => {
        try {
            const startTime = performance.now();
            const result = await asyncFn(...args);
            const duration = performance.now() - startTime;
            
            if (duration > 1000) { // Track slow operations
                trackPerformance(`${context}_duration`, Math.round(duration));
            }
            
            return result;
        } catch (error) {
            console.error(`Error in ${context}:`, error);
            
            // Track error
            trackEvent('Function Error', {
                context: context,
                error_message: error.message,
                error_stack: error.stack?.substring(0, 500), // Limit stack trace length
                timestamp: new Date().toISOString()
            });
            
            // Report to Sentry
            if (typeof Sentry !== 'undefined') {
                Sentry.captureException(error, {
                    tags: {
                        component: context
                    }
                });
            }
            
            throw error; // Re-throw to maintain original behavior
        }
    };
}

// Monitor visualization performance
function monitorVisualizationPerformance() {
    // Track render performance
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.name.includes('deck.gl') || entry.name.includes('webgl')) {
                trackPerformance('render_frame', Math.round(entry.duration));
            }
        }
    });
    
    try {
        observer.observe({ entryTypes: ['measure', 'navigation'] });
    } catch (error) {
        console.warn('Performance observer not supported:', error);
    }
    
    // Track memory usage periodically
    if (performance.memory) {
        setInterval(() => {
            const memoryInfo = {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
            
            trackEvent('Memory Usage', memoryInfo);
            
            // Alert if memory usage is high
            if (memoryInfo.used > memoryInfo.limit * 0.8) {
                console.warn('High memory usage detected:', memoryInfo);
                trackEvent('High Memory Usage', memoryInfo);
            }
        }, 30000); // Every 30 seconds
    }
}

// Initialize performance monitoring
function initializeMonitoring() {
    // Start performance monitoring
    monitorVisualizationPerformance();
    
    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
        trackEvent('Page Visibility', {
            visible: !document.hidden,
            timestamp: new Date().toISOString()
        });
    });
    
    // Track window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            trackEvent('Window Resize', {
                width: window.innerWidth,
                height: window.innerHeight,
                timestamp: new Date().toISOString()
            });
        }, 250);
    });
}

// Initialize monitoring when app loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMonitoring);
} else {
    initializeMonitoring();
}

// Expose functions and app object globally for error handling
window.CADSVisualization = app;
window.showError = showError;
window.trackEvent = trackEvent;
window.trackPerformance = trackPerformance;