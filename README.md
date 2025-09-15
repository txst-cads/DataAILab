# CADS Research Visualization System

A comprehensive research data processing and visualization system for the Computer Science Department at Texas State University. This project processes academic research data from OpenAlex, generates semantic embeddings, performs clustering analysis, and creates interactive visualizations to explore research patterns and collaborations.

## 🎯 System Overview

The CADS Research Visualization System is a complete end-to-end solution that transforms raw research data into interactive, explorable visualizations. It combines advanced machine learning techniques with modern web technologies to provide insights into research patterns, collaborations, and thematic clusters.

### Key Capabilities

- **🔄 Automated Data Processing**: Extract and process research data from OpenAlex API
- **🧠 Semantic Analysis**: Generate embeddings and perform clustering using UMAP/HDBSCAN
- **🎨 Interactive Visualization**: Web-based dashboard with advanced filtering and search
- **🔍 Semantic Search**: Find similar research works using vector similarity
- **👥 Researcher Profiles**: Detailed views of faculty research and collaborations
- **📊 Real-time Analytics**: Live statistics and data quality monitoring

## 🏗️ System Architecture

```
CADS Research Visualization System
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Core Pipeline  │    │   Visualization │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • OpenAlex API  │───▶│ • Data Loader    │───▶│ • Web Dashboard │
│ • Supabase DB   │    │ • Embeddings     │    │ • Search System │
│ • CADS Faculty  │    │ • UMAP/HDBSCAN   │    │ • Interactive   │
│ • Research Data │    │ • Theme Gen      │    │   Visualizations│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Repository Organization

```
CADS-Research-Visualization/
├── 📊 cads/                          # Core data processing pipeline
│   ├── README.md                    # Pipeline documentation
│   ├── data_loader.py               # Data loading and embeddings
│   ├── process_data.py              # Main pipeline orchestration
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment template
│   ├── data/                        # Generated data files
│   ├── models/                      # Trained ML models
│   └── tests/                       # Comprehensive test suite
│
├── 🎨 visuals/                       # Interactive visualization dashboard
│   ├── public/                      # Web interface files
│   │   ├── index.html              # Main dashboard interface
│   │   ├── app.js                  # Visualization logic
│   │   └── data/                   # Visualization data files
│   ├── data/                        # Raw visualization data
│   ├── models/                      # Visualization ML models
│   └── tests/                       # Visualization tests
│
├── 🗄️ database/                      # Database schema and migrations
│   ├── README.md                    # Database documentation
│   ├── schema/                      # Table definitions
│   │   ├── create_cads_tables.sql  # Complete CADS schema
│   │   └── create_cads_tables_simple.sql
│   └── migrations/                  # Database migrations
│
├── 🔧 scripts/                       # Organized utility scripts
│   ├── README.md                    # Scripts documentation
│   ├── migration/                   # Database setup scripts
│   │   ├── execute_cads_migration.py   # ✅ Main migration script
│   │   └── legacy/                     # Archived migration attempts
│   ├── processing/                  # Data processing scripts
│   │   ├── process_cads_with_openalex_ids.py  # ✅ Data collection
│   │   └── migrate_cads_data_to_cads_tables.py # ✅ Data migration
│   └── utilities/                   # Verification and maintenance
│       ├── check_cads_data_location.py
│       └── [other utility scripts]
│
├── 📚 docs/                          # Comprehensive documentation
│   ├── README.md                    # Documentation index
│   ├── setup/                       # Installation and configuration
│   ├── pipeline/                    # Technical documentation
│   └── migration/                   # Historical documentation
│
├── 📦 data/                          # Centralized data storage
│   ├── README.md                    # Data documentation
│   ├── raw/                         # Original data files
│   ├── processed/                   # Analyzed data
│   │   ├── cluster_themes.json     # AI-generated cluster themes
│   │   ├── clustering_results.json # HDBSCAN clustering results
│   │   └── visualization-data.json # Complete visualization dataset
│   └── search/                      # Search indexes
│       └── search-index.json       # Pre-built search index
│
├── README.md                        # This main documentation
├── CADS_REPOSITORY_ANALYSIS.md      # Repository organization analysis
├── .env                            # Environment variables
└── .gitignore                      # Git ignore rules
```

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+** with pip
- **PostgreSQL** with vector extension
- **Supabase account** for database hosting
- **OpenAlex API access** (free with email registration)
- **Modern web browser** for visualization

### 1. Repository Setup

```bash
# Clone the repository
git clone [repository-url]
cd cads-research-visualization

# Verify repository structure
ls -la
```

### 2. Database Setup

```bash
# Create CADS database tables
python3 scripts/migration/execute_cads_migration.py

# Verify table creation
python3 scripts/utilities/check_cads_data_location.py
```

### 3. Environment Configuration

```bash
# Copy environment template
cp cads/.env.example cads/.env

# Edit with your credentials
nano cads/.env
```

Required environment variables:
```bash
# Database Connection
DATABASE_URL=postgresql://user:pass@host:port/db

# API Configuration
OPENALEX_EMAIL=your_email@domain.com
GROQ_API_KEY=your_groq_api_key  # Optional for theme generation

# ML Configuration (optional)
EMBEDDING_MODEL=all-MiniLM-L6-v2
UMAP_N_NEIGHBORS=15
HDBSCAN_MIN_CLUSTER_SIZE=5
```

### 4. Dependencies Installation

```bash
# Install Python dependencies
cd cads
pip install -r requirements.txt
```

### 5. Data Processing

```bash
# Process CADS research data
python3 scripts/processing/process_cads_with_openalex_ids.py

# Migrate data to CADS tables
python3 scripts/processing/migrate_cads_data_to_cads_tables.py

# Run the complete pipeline
python3 cads/process_data.py
```

### 6. Launch Visualization

```bash
# Start local web server
cd visuals/public
python3 -m http.server 8000

# Open in browser
open http://localhost:8000
```

## 📊 System Components

### 🔧 CADS Pipeline (`cads/`)

**Purpose**: Core data processing and machine learning pipeline

**Key Features**:
- **Data Loading**: Connects to Supabase and loads research data
- **Embedding Generation**: Creates 384-dimensional semantic vectors
- **UMAP Reduction**: Projects embeddings to 2D coordinates
- **HDBSCAN Clustering**: Groups similar research works
- **Theme Generation**: AI-powered cluster descriptions
- **Data Validation**: Comprehensive quality checks

**Main Files**:
- `data_loader.py` - Database connection and data processing
- `process_data.py` - Pipeline orchestration and clustering
- `tests/` - Complete test suite with 10+ test files

### 🎨 Visualization Dashboard (`visuals/`)

**Purpose**: Interactive web-based research exploration interface

**Key Features**:
- **Interactive Map**: Zoomable, pannable research visualization
- **Advanced Filtering**: Multi-criteria filtering system
- **Semantic Search**: Find similar research works
- **Researcher Profiles**: Faculty research overviews
- **Real-time Statistics**: Live data updates
- **Responsive Design**: Desktop and mobile optimized

**Technologies**:
- **Deck.gl**: WebGL-powered visualization framework
- **Vanilla JavaScript**: No framework dependencies
- **CSS3**: Modern styling with custom properties

### 🗄️ Database Layer (`database/`)

**Purpose**: PostgreSQL schema with vector extensions

**Key Tables**:
- `cads_researchers` - Faculty information and profiles
- `cads_works` - Research papers with embeddings
- `cads_topics` - Research topic classifications

**Features**:
- **Vector Storage**: pgvector extension for embeddings
- **Full-text Search**: Optimized text search indexes
- **Relationship Management**: Foreign key constraints
- **Performance Optimization**: Strategic indexing

### 🔧 Scripts Collection (`scripts/`)

**Purpose**: Organized utility scripts for system management

**Categories**:
- **Migration**: Database setup and schema creation
- **Processing**: Data collection and transformation
- **Utilities**: Verification and maintenance tools

**Key Scripts**:
- `migration/execute_cads_migration.py` - Database setup
- `processing/process_cads_with_openalex_ids.py` - Data collection
- `utilities/check_cads_data_location.py` - Data verification

## 📈 Expected Results

### Data Volume
- **~32 CADS Researchers**: Faculty from CS Department
- **~2,454 Research Works**: Academic papers with full metadata
- **~6,834 Research Topics**: Hierarchical topic classifications
- **384-dimensional embeddings**: Semantic representations for all works

### Processing Performance
- **Data Loading**: ~30 seconds for complete dataset
- **Embedding Generation**: ~2 minutes for missing embeddings
- **UMAP Reduction**: ~45 seconds for 2,454 works
- **HDBSCAN Clustering**: ~15 seconds for 2D coordinates
- **Complete Pipeline**: ~5-10 minutes total processing time

### Clustering Results
- **15-25 Research Clusters**: Automatically identified themes
- **AI-Generated Themes**: Descriptive cluster names and summaries
- **2D Coordinates**: Optimized for visualization layout
- **Quality Metrics**: >95% of works successfully clustered

## 🧪 Testing and Validation

### Comprehensive Test Suite

```bash
# Test repository structure
python3 cads/tests/test_basic_structure.py

# Test database connectivity
python3 cads/tests/test_connection.py

# Test complete pipeline (requires ML dependencies)
python3 cads/tests/test_full_pipeline.py

# Verify data integrity
python3 scripts/utilities/check_cads_data_location.py
```

### Test Categories
- **Structure Tests**: Repository organization and file presence
- **Connection Tests**: Database connectivity and basic queries
- **Pipeline Tests**: End-to-end data processing
- **Integration Tests**: Component interaction validation
- **Performance Tests**: Timing and resource usage benchmarks

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Errors
```bash
# Test connection
python3 cads/tests/test_connection.py

# Check environment variables
cat cads/.env

# Verify database URL format
echo $DATABASE_URL
```

#### 2. Missing Dependencies
```bash
# Install all requirements
pip install -r cads/requirements.txt

# Check Python version
python3 --version  # Should be 3.8+
```

#### 3. Data Location Issues
```bash
# Verify data location
python3 scripts/utilities/check_cads_data_location.py

# Run migration if needed
python3 scripts/processing/migrate_cads_data_to_cads_tables.py
```

#### 4. Pipeline Failures
```bash
# Check basic structure
python3 cads/tests/test_basic_structure.py

# Run with debug logging
export LOG_LEVEL=DEBUG
python3 cads/process_data.py
```

### Getting Help

1. **Check Documentation**: Review relevant README files
2. **Run Tests**: Use test suite to identify issues
3. **Check Logs**: Enable debug logging for detailed output
4. **Verify Environment**: Ensure all prerequisites are met

## 📚 Documentation

### 🚀 Getting Started
- **[Installation Guide](docs/setup/INSTALLATION_GUIDE.md)** - Complete setup instructions from scratch
- **[User Guide](docs/setup/USER_GUIDE.md)** - How to use the visualization system
- **[Troubleshooting Guide](docs/setup/TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

### 🔧 System Operation
- **[CI/CD Pipeline Guide](docs/setup/CICD_PIPELINE_GUIDE.md)** - Automated testing and deployment
- **[Monitoring Setup](docs/monitoring/MONITORING_SETUP.md)** - Error tracking and analytics
- **[Monitoring Interpretation](docs/monitoring/MONITORING_INTERPRETATION_GUIDE.md)** - Understanding metrics and alerts

### 📖 Component Documentation
- **[CADS Pipeline](cads/README.md)** - Core data processing system
- **[Database Schema](database/README.md)** - Table structure and relationships
- **[Scripts Guide](scripts/README.md)** - Utility scripts and workflows
- **[Data Organization](data/README.md)** - Data structure and formats

### 🧪 Testing and Quality
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive test suite documentation
- **[Test Results](tests/README.md)** - Current test status and coverage

### 📋 Technical References
- **[Repository Analysis](docs/CADS_REPOSITORY_ANALYSIS.md)** - Detailed organization analysis
- **[Migration Reports](docs/migration/)** - Historical context and migration records
- **[API Documentation](docs/api/)** - Function references and examples

## 🤝 Contributing

We welcome contributions to improve the CADS Research Visualization System!

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Submit a pull request**

### Contribution Guidelines

- **Code Quality**: Follow existing patterns and style
- **Testing**: Add tests for new features
- **Documentation**: Update relevant README files
- **Performance**: Consider impact on processing time
- **Compatibility**: Ensure cross-platform compatibility

## 📄 License

This project is part of the Texas State University research infrastructure. See individual component licenses for specific terms.

## 🙏 Acknowledgments

- **CADS Faculty**: For providing research data and domain expertise
- **Texas State University**: For supporting this research visualization initiative
- **OpenAlex**: For providing open access to scholarly data
- **Supabase**: For reliable database hosting and vector extensions
- **Open Source Community**: For the excellent ML and visualization libraries

## 📞 Support and Contact

### Getting Support

- **Documentation**: Check relevant README files first
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Testing**: Run the test suite to diagnose problems
- **Community**: Join discussions in GitHub Discussions

### Contact Information

- **Lead Developer**: Saksham Adhikari
- **Institution**: Texas State University
- **Email**: [contact information]
- **Project Repository**: [GitHub repository URL]

---

**🎉 Complete research data processing and visualization system ready for exploration!**

*Built with ❤️ for the research community at Texas State University*