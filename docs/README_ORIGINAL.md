# CADS Research Visualization

An interactive web-based visualization tool for exploring research publications from the Center of Analytics and Data Science (CADS) at Texas State University. This project provides an intuitive interface to discover research patterns, collaborations, and thematic clusters across the CADS research landscape.

![CADS Research Visualization](https://img.shields.io/badge/Status-Active-green)  ![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow) ![Deck.gl](https://img.shields.io/badge/Deck.gl-8.9+-orange)

## 🎯 Overview

The CADS Research Visualization transforms complex research data into an interactive, explorable map that reveals:
- **Research Themes**: Automatically clustered topics using machine learning
- **Publication Patterns**: Temporal and thematic distribution of research output
- **Researcher Networks**: Faculty expertise and collaboration patterns
- **Content Discovery**: Keyword-based search and filtering capabilities

## ✨ Features

### 🔍 Advanced Filtering System
- **Researcher Search**: Real-time filtering by faculty names with partial matching
- **Theme Selection**: Visual checklist with color-coded research themes
- **Keyword Filtering**: Tag-based search with AND/OR logic options
- **Temporal Filtering**: Publication year range selection (2010-2024)

### 🗺️ Interactive Visualization
- **Zoomable Map**: Smooth zoom controls with mouse wheel and button controls
- **Cluster Labels**: Dynamic theme labels that appear based on zoom level
- **Hover Details**: Rich tooltips showing publication information
- **Responsive Design**: Optimized for desktop and mobile viewing

### 🎛️ User Interface
- **Compact Side Panel**: Scrollable filter controls with organized sections
- **Onboarding Guide**: Interactive tutorial for new users
- **Keyboard Shortcuts**: Quick navigation and control options
- **Dark Theme**: Professional, eye-friendly interface

### 📊 Data Processing Pipeline
- **UMAP Dimensionality Reduction**: Projects high-dimensional embeddings to 2D space
- **HDBSCAN Clustering**: Automatically identifies research themes
- **Real-time Statistics**: Live updates of visible papers and filter states

## 🚀 Quick Start

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Python 3.7+ (for local development server)
- Internet connection (for Deck.gl CDN)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/CADS-Visualizer.git
   cd CADS-Visualizer
   ```

2. **Start a local server**
   ```bash
   cd visuals/public
   python3 -m http.server 8000
   ```

3. **Open in browser**
   ```
   http://localhost:8000
   ```

### Alternative Setup
For production deployment, serve the files from `visuals/public/` using any web server (Apache, Nginx, etc.).

## 📁 Project Structure

```
CADS-Visualizer/
├── visuals/
│   ├── data/                    # Raw data files
│   │   ├── cluster_themes.json  # Research theme definitions
│   │   ├── clustering_results.json # Cluster centers and metadata
│   │   └── umap_coordinates.json   # 2D coordinate mappings
│   ├── models/                  # Machine learning models
│   │   ├── hdbscan_model.pkl   # Clustering model
│   │   └── umap_model.pkl      # Dimensionality reduction model
│   ├── public/                 # Web application files
│   │   ├── data/              # Processed data for visualization
│   │   ├── app.js             # Main application logic
│   │   ├── index.html         # Application interface
│   │   └── app.min.js         # Minified production version
│   ├── tests/                 # Test suite
│   └── vercel.json           # Deployment configuration
├── .kiro/                     # Development specifications
└── README.md                  # This file
```

## 🎮 Usage Guide

### Basic Navigation
- **Pan**: Click and drag to move around the visualization
- **Zoom**: Use mouse wheel or zoom buttons (+/-) in top-right corner
- **Filter**: Use the left panel to refine what research is displayed
- **Details**: Hover over points to see publication information

### Filtering Options

#### 1. Researcher Filter
- Type faculty names in the search box
- Supports partial matching (e.g., "tahir" finds "Tahir Ekin")
- Real-time filtering as you type

#### 2. Research Theme Filter
- Check/uncheck themes in the scrollable list
- Color swatches match theme colors on the map
- All themes selected by default

#### 3. Keywords Filter
- Add multiple keyword tags using the input field
- Toggle between "Match ALL" and "Match ANY" logic
- Remove tags by clicking the × button

#### 4. Publication Year Filter
- Drag the slider to set minimum publication year
- Default shows all papers from 2010 onwards
- Real-time updates as you adjust

### Keyboard Shortcuts
- **ESC**: Close tooltips and onboarding
- **+/-**: Zoom in/out
- **/**: Focus researcher search field

## 🛠️ Technical Details

### Architecture
- **Frontend**: Vanilla JavaScript (ES6+)
- **Visualization**: Deck.gl WebGL framework
- **Data Format**: Compressed JSON with optimized structure
- **Styling**: CSS3 with custom properties and responsive design

### Data Processing
The visualization uses a sophisticated data pipeline:

1. **Text Embedding**: Research abstracts converted to high-dimensional vectors
2. **Dimensionality Reduction**: UMAP projects embeddings to 2D coordinates
3. **Clustering**: HDBSCAN identifies thematic groups
4. **Theme Generation**: LLM-generated descriptive names for clusters
5. **Optimization**: Data compressed and optimized for web delivery

### Performance Features
- **Lazy Loading**: Data loaded progressively
- **Viewport Culling**: Only visible elements rendered
- **Debounced Filtering**: Smooth real-time updates
- **Cached Calculations**: Optimized label sizing and positioning

## 🧪 Testing

The project includes comprehensive tests covering:

```bash
# Run all tests
cd visuals/tests
python3 -m pytest

# Specific test categories
python3 test_data_processing.py      # Data pipeline tests
python3 test_clustering_integration.py # ML model tests
python3 test_html_structure.py      # Frontend tests
python3 test_performance.py         # Performance benchmarks
```

## 📊 Data Sources

The visualization processes research data from:
- **Publications**: Academic papers and conference proceedings
- **Authors**: Faculty and researcher information
- **Abstracts**: Full-text content for semantic analysis
- **Metadata**: Publication dates, venues, and classifications

Data is automatically updated and reprocessed to maintain current research representation.

## 🎨 Customization

### Themes and Colors
Modify theme colors in `visuals/public/app.js`:
```javascript
function generateClusterColor(clusterId) {
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', // Add your colors
        // ... more colors
    ];
    return colors[clusterId % colors.length];
}
```

### Filter Behavior
Adjust filtering logic in the `getCurrentFilteredData()` function:
```javascript
// Example: Change keyword matching behavior
if (useAndLogic) {
    return keywords.every(keyword => title.includes(keyword));
} else {
    return keywords.some(keyword => title.includes(keyword));
}
```

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Manual Deployment
1. Copy `visuals/public/` contents to your web server
2. Ensure proper MIME types for `.json` and `.gz` files
3. Configure HTTPS for optimal performance

### Environment Variables
No environment variables required for basic deployment.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit a pull request**

### Development Guidelines
- Follow existing code style and patterns
- Add comments for complex logic
- Test across different browsers
- Optimize for performance
- Maintain accessibility standards

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

**Built by Saksham Adhikari for CADS**

- **Lead Developer**: Saksham Adhikari
- **Research Director**: [CADS Faculty]
- **Institution**: Texas State University

## 🙏 Acknowledgments

- **CADS Faculty**: For providing research data and domain expertise
- **Deck.gl Team**: For the powerful WebGL visualization framework
- **UMAP/HDBSCAN**: For excellent dimensionality reduction and clustering algorithms
- **Texas State University**: For supporting this research visualization initiative

## 📞 Support

For questions, issues, or feature requests:

- **Issues**: [GitHub Issues](https://github.com/your-org/CADS-Visualizer/issues)
- **Email**: [pqo14@txstate.edu]
- **Documentation**: [Project Wiki](https://github.com/your-org/CADS-Visualizer/wiki)

## 🔄 Changelog

### Version 2.0.0 (Current)
- ✅ Advanced filtering system with multiple filter types
- ✅ Zoom controls and improved navigation
- ✅ Onboarding system for new users
- ✅ Compact, scrollable side panel
- ✅ Real-time filter state management
- ✅ Enhanced performance and responsiveness

### Version 1.0.0
- 🎯 Initial release with basic visualization
- 📊 UMAP/HDBSCAN clustering pipeline
- 🗺️ Interactive research map
- 🔍 Basic search and filter capabilities

---

**Made with ❤️ for the research community at Texas State University**