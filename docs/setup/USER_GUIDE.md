# User Guide - CADS Research Visualization System

This comprehensive user guide explains how to use the CADS Research Visualization System to explore research data, discover patterns, and analyze academic collaborations.

## 🎯 Getting Started

### Accessing the Visualization

1. **Local Development:**
   ```bash
   cd visuals/public
   python3 -m http.server 8000
   open http://localhost:8000
   ```

2. **Production Deployment:**
   - Visit your deployed Vercel URL
   - The system loads automatically with the latest data

### First Time Setup

When you first access the visualization:

1. **Wait for Data Loading**: The system loads ~2,454 research works and metadata
2. **Initial View**: You'll see a scatter plot of research papers positioned by similarity
3. **UI Panel**: The control panel on the right provides filtering and search options
4. **Statistics**: Live counters show total papers, researchers, and clusters

## 🗺️ Understanding the Visualization

### Main Components

#### Interactive Research Map
- **Dots/Points**: Each point represents a research paper
- **Position**: Similar research is positioned closer together
- **Colors**: Different colors represent research clusters/themes
- **Size**: Point size may indicate citation count or recency

#### Control Panel (Right Side)
- **Search Box**: Find papers by title, abstract, or keywords
- **Researcher Filter**: Filter by specific CADS faculty members
- **Year Range**: Filter papers by publication year
- **Cluster Filter**: Focus on specific research themes
- **Statistics**: Live counts of visible data

#### Information Display
- **Tooltips**: Hover over points to see paper details
- **Paper Details**: Click points for full paper information
- **Researcher Profiles**: Click researcher names for their work overview

### Navigation Controls

#### Zoom and Pan
- **Mouse Wheel**: Zoom in/out
- **Click and Drag**: Pan around the visualization
- **Double Click**: Zoom to fit all visible data
- **Reset Button**: Return to default view

#### Keyboard Shortcuts
- **Space**: Reset view to show all data
- **Escape**: Clear current selection
- **Enter**: Apply current filters
- **Tab**: Navigate between UI elements

## 🔍 Search and Discovery Features

### Semantic Search

The system provides powerful semantic search capabilities:

#### Basic Search
```
Type: "machine learning"
Result: Finds papers about ML, AI, neural networks, etc.
```

#### Advanced Search Patterns
```
# Exact phrase search
"deep learning neural networks"

# Multiple keywords (AND logic)
machine learning computer vision

# Research area exploration
natural language processing

# Methodology search
statistical analysis survey
```

#### Search Tips
- **Semantic Understanding**: Search finds conceptually related papers, not just keyword matches
- **Fuzzy Matching**: Handles typos and variations in terminology
- **Context Aware**: Understands academic terminology and abbreviations
- **Real-time Results**: Search results update as you type

### Filtering Options

#### Researcher Filter
- **Purpose**: Focus on specific faculty members' work
- **Usage**: Select one or more researchers from dropdown
- **Effect**: Shows only papers by selected researchers
- **Tip**: Use to explore individual research profiles

#### Year Range Filter
- **Purpose**: Analyze research trends over time
- **Usage**: Drag slider endpoints to set date range
- **Effect**: Shows papers published within selected years
- **Tip**: Compare research focus changes over time

#### Cluster Filter
- **Purpose**: Explore specific research themes
- **Usage**: Select clusters from dropdown menu
- **Effect**: Highlights papers in selected research areas
- **Tip**: Discover interdisciplinary connections

### Advanced Discovery Features

#### Research Cluster Exploration
1. **Identify Clusters**: Different colored regions represent research themes
2. **Cluster Names**: AI-generated descriptive names for each cluster
3. **Cluster Details**: Click cluster names for detailed descriptions
4. **Cross-Cluster Papers**: Papers at cluster boundaries show interdisciplinary work

#### Collaboration Discovery
1. **Co-author Networks**: Papers with multiple CADS authors
2. **Research Connections**: Similar papers by different researchers
3. **Temporal Patterns**: How collaborations evolve over time
4. **External Collaborations**: CADS researchers working with external authors

## 📊 Data Analysis Features

### Research Statistics

#### Live Counters
- **Visible Papers**: Number of papers matching current filters
- **Total Papers**: Complete dataset size (~2,454 papers)
- **Active Researchers**: Number of CADS faculty with visible papers
- **Research Clusters**: Number of identified research themes

#### Detailed Analytics
- **Publication Trends**: Papers published per year
- **Research Distribution**: Papers per researcher
- **Cluster Sizes**: Number of papers in each research theme
- **Collaboration Metrics**: Co-authorship statistics

### Research Insights

#### Trend Analysis
1. **Temporal Patterns**: Use year filter to see research evolution
2. **Emerging Areas**: Identify new research clusters
3. **Declining Areas**: Spot research areas with fewer recent papers
4. **Cyclical Patterns**: Recurring research themes

#### Collaboration Analysis
1. **Research Groups**: Identify researchers working on similar topics
2. **Interdisciplinary Work**: Papers spanning multiple clusters
3. **External Partnerships**: Collaborations with non-CADS researchers
4. **Research Networks**: Connected researchers and topics

## 🎨 Customization and Preferences

### Display Options

#### Visual Preferences
- **Color Schemes**: Different color palettes for clusters
- **Point Sizes**: Adjust point sizes for better visibility
- **Opacity**: Control transparency for overlapping points
- **Animation**: Enable/disable smooth transitions

#### Information Display
- **Tooltip Detail Level**: Choose amount of information in tooltips
- **Label Visibility**: Show/hide cluster labels
- **Statistics Panel**: Expand/collapse statistics display
- **Legend**: Show/hide color legend

### Performance Settings

#### Data Loading
- **Progressive Loading**: Load data in chunks for faster initial display
- **Caching**: Browser caches data for faster subsequent visits
- **Compression**: Automatic use of compressed data files
- **Lazy Loading**: Load detailed information only when needed

#### Rendering Options
- **Quality Settings**: Balance between visual quality and performance
- **Animation Speed**: Adjust transition speeds
- **Update Frequency**: Control how often statistics update
- **Memory Management**: Optimize for available system resources

## 🔧 Advanced Usage

### Research Workflows

#### Exploring a Research Area
1. **Start with Search**: Enter research area keywords
2. **Examine Clusters**: Identify relevant research clusters
3. **Filter by Cluster**: Focus on specific research themes
4. **Analyze Papers**: Read abstracts and details
5. **Find Researchers**: Identify key faculty in the area

#### Analyzing Researcher Profiles
1. **Select Researcher**: Use researcher filter
2. **View All Work**: See complete publication history
3. **Identify Themes**: Notice research cluster distribution
4. **Track Evolution**: Use year filter to see research progression
5. **Find Collaborators**: Look for co-authored papers

#### Discovering Collaborations
1. **Multi-Researcher Filter**: Select multiple researchers
2. **Find Overlaps**: Look for papers in same clusters
3. **Temporal Analysis**: See collaboration patterns over time
4. **Network Mapping**: Identify research networks
5. **Opportunity Identification**: Spot potential new collaborations

### Data Export and Sharing

#### Sharing Views
- **URL Sharing**: Current view state is saved in URL
- **Bookmark Views**: Save specific filter combinations
- **Screenshot Capture**: Use browser tools to capture visualizations
- **Print Views**: Print-friendly versions available

#### Data Access
- **Paper Details**: Full metadata available in tooltips
- **Researcher Information**: Faculty profiles and contact information
- **Citation Data**: Links to original papers and citations
- **Export Options**: Download filtered data sets (where available)

## 📱 Mobile and Accessibility

### Mobile Usage

#### Touch Controls
- **Pinch to Zoom**: Two-finger zoom in/out
- **Touch and Drag**: Pan around visualization
- **Tap**: Select points and access tooltips
- **Double Tap**: Zoom to fit view

#### Mobile Interface
- **Responsive Design**: UI adapts to screen size
- **Touch-Friendly**: Large touch targets for filters
- **Simplified View**: Reduced complexity on small screens
- **Performance Optimized**: Efficient rendering on mobile devices

### Accessibility Features

#### Screen Reader Support
- **Alt Text**: Descriptive text for all visual elements
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Indicators**: Clear focus states for all interactive elements
- **Semantic HTML**: Proper heading structure and landmarks

#### Visual Accessibility
- **High Contrast**: Color schemes for visual impairments
- **Large Text**: Scalable text sizes
- **Color Blind Friendly**: Alternative color schemes
- **Motion Reduction**: Respect user motion preferences

## 🚨 Troubleshooting Common Issues

### Display Issues

#### Blank or Loading Screen
1. **Check Internet Connection**: Ensure stable connection
2. **Clear Browser Cache**: Refresh with Ctrl+F5 (Cmd+Shift+R on Mac)
3. **Try Different Browser**: Test with Chrome, Firefox, or Safari
4. **Check JavaScript**: Ensure JavaScript is enabled
5. **Disable Extensions**: Try with browser extensions disabled

#### Slow Performance
1. **Close Other Tabs**: Free up browser memory
2. **Reduce Data Size**: Use filters to show fewer papers
3. **Lower Quality**: Reduce visual quality settings
4. **Update Browser**: Use latest browser version
5. **Check System Resources**: Ensure adequate RAM available

### Interaction Issues

#### Search Not Working
1. **Check Spelling**: Verify search terms are correct
2. **Try Broader Terms**: Use more general keywords
3. **Clear Filters**: Remove other filters that might conflict
4. **Refresh Page**: Reload to reset search index
5. **Try Different Terms**: Use synonyms or related concepts

#### Filters Not Responding
1. **Clear All Filters**: Reset to default state
2. **Refresh Browser**: Reload the page
3. **Check Data Loading**: Ensure all data has loaded
4. **Try One Filter**: Test filters individually
5. **Check Browser Console**: Look for JavaScript errors

### Data Issues

#### Missing or Incorrect Data
1. **Check Data Date**: Verify when data was last updated
2. **Report Issues**: Contact administrators about data problems
3. **Try Different View**: Use different filters or search terms
4. **Refresh Data**: Reload page to get latest data
5. **Check Source**: Verify data comes from expected sources

## 📚 Additional Resources

### Learning Resources
- **Video Tutorials**: Step-by-step usage videos (if available)
- **Example Workflows**: Common usage patterns and examples
- **Research Guides**: How to conduct specific types of analysis
- **Best Practices**: Tips for effective research exploration

### Technical Documentation
- **API Documentation**: For developers wanting to extend the system
- **Data Schema**: Understanding the data structure
- **Performance Guide**: Optimizing system performance
- **Integration Guide**: Connecting with other research tools

### Support and Community
- **User Forum**: Community discussions and questions
- **Feature Requests**: Suggest new features or improvements
- **Bug Reports**: Report issues or problems
- **Contact Information**: Direct support contact details

---

**🎉 Start Exploring!**

The CADS Research Visualization System provides powerful tools for exploring academic research. Start with simple searches and gradually explore more advanced features as you become familiar with the interface.

**Quick Start Checklist:**
- ✅ Access the visualization at your deployment URL
- ✅ Try searching for a research topic you're interested in
- ✅ Experiment with different filters
- ✅ Hover over papers to see details
- ✅ Explore different research clusters
- ✅ Filter by specific researchers
- ✅ Analyze trends over time

Happy exploring! 🔍📊