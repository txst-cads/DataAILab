# CADS Research Data Pipeline

## 🎯 Overview

The CADS (Computer Science Department) Research Data Pipeline is a comprehensive system for processing, analyzing, and visualizing research data from Texas State University's Computer Science Department. This pipeline extracts research works from the OpenAlex database, generates semantic embeddings, performs clustering analysis, and creates interactive visualizations.

## 🏗️ Architecture

```
CADS Pipeline Architecture
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Core Pipeline  │    │   Outputs       │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • OpenAlex API  │───▶│ • Data Loader    │───▶│ • JSON Files    │
│ • Supabase DB   │    │ • Embeddings     │    │ • Visualizations│
│ • CADS Faculty  │    │ • UMAP Reduction │    │ • Search Index  │
│                 │    │ • HDBSCAN Cluster│    │ • Cluster Themes│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
cads/
├── README.md                 # This documentation
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
├── .env                     # Environment variables (create from .env.example)
│
├── Core Pipeline Files:
├── data_loader.py           # 🔧 Data loading and embedding generation
├── process_data.py          # 🎯 Main pipeline orchestration
│
├── data/                    # 📊 Generated data files
│   ├── cluster_themes.json  # AI-generated cluster descriptions
│   ├── clustering_results.json # HDBSCAN clustering results
│   └── umap_coordinates.json   # 2D UMAP coordinates
│
├── models/                  # 🤖 Trained ML models
│   ├── hdbscan_model.pkl    # Saved HDBSCAN clustering model
│   └── umap_model.pkl       # Saved UMAP dimensionality reduction model
│
└── tests/                   # 🧪 Test suite
    ├── test_full_pipeline.py      # Complete pipeline test
    ├── test_connection.py         # Database connection test
    ├── test_data_processing.py    # Data processing tests
    └── [additional test files]
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: DATABASE_URL, OPENALEX_EMAIL
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Test Connection

```bash
# Test database connection
python3 tests/test_connection.py
```

### 4. Run Pipeline

```bash
# Run complete data processing pipeline
python3 process_data.py
```

## 🔧 Core Components

### 1. Data Loader (`data_loader.py`)

**Purpose**: Handles all data loading and preprocessing operations.

**Key Features**:
- 🔗 **Database Connection**: Connects to Supabase PostgreSQL database
- 📊 **Data Loading**: Loads CADS research works with researcher information
- 🧮 **Embedding Generation**: Creates semantic embeddings using SentenceTransformers
- ✅ **Data Validation**: Ensures data quality and completeness
- 🔄 **Embedding Processing**: Handles pgvector format parsing and generation

**Main Class**: `DataProcessor`

**Key Methods**:
- `load_cads_data_with_researchers()`: Load works with researcher info
- `process_embeddings()`: Generate/process semantic embeddings
- `process_production_dataset()`: Complete data processing workflow

### 2. Process Data (`process_data.py`)

**Purpose**: Main pipeline orchestration and clustering analysis.

**Key Features**:
- 🎯 **Pipeline Orchestration**: Coordinates the entire processing workflow
- 📐 **UMAP Reduction**: Reduces embeddings to 2D for visualization
- 🎪 **HDBSCAN Clustering**: Groups similar research works
- 🎨 **Theme Generation**: Creates AI-generated cluster descriptions
- 💾 **Result Saving**: Exports processed data to JSON files

**Main Functions**:
- `load_and_process_data()`: Load and preprocess data
- `compute_clusters()`: Perform UMAP + HDBSCAN clustering
- `save_results()`: Export results to files

## 📊 Data Flow

### Input Data Sources

1. **CADS Researchers** (`cads_researchers` table)
   - Faculty information from Texas State CS Department
   - OpenAlex IDs for API integration
   - Department and H-index information

2. **Research Works** (`cads_works` table)
   - Academic papers and publications
   - Titles, abstracts, keywords
   - Citation counts and publication years
   - Semantic embeddings (384-dimensional vectors)

3. **Topics** (`cads_topics` table)
   - Research topic classifications
   - OpenAlex topic assignments
   - Topic scores and hierarchies

### Processing Steps

1. **Data Loading** 📥
   ```python
   # Load research works with researcher information
   df = processor.load_cads_data_with_researchers()
   ```

2. **Embedding Processing** 🧮
   ```python
   # Generate/process semantic embeddings
   df, embeddings = processor.process_embeddings(df)
   ```

3. **Dimensionality Reduction** 📐
   ```python
   # Reduce to 2D using UMAP
   umap_coords = umap_model.fit_transform(embeddings)
   ```

4. **Clustering** 🎪
   ```python
   # Group similar works using HDBSCAN
   cluster_labels = hdbscan_model.fit_predict(umap_coords)
   ```

5. **Theme Generation** 🎨
   ```python
   # Generate AI descriptions for clusters
   themes = generate_cluster_themes(clusters)
   ```

### Output Files

1. **`umap_coordinates.json`** - 2D coordinates for visualization
2. **`clustering_results.json`** - Cluster assignments for each work
3. **`cluster_themes.json`** - AI-generated cluster descriptions
4. **`processing_summary.json`** - Pipeline execution summary

## 🧪 Testing

### Test Suite Overview

The pipeline includes comprehensive tests to ensure reliability:

- **`test_connection.py`** - Database connectivity and basic queries
- **`test_full_pipeline.py`** - End-to-end pipeline testing
- **`test_data_processing.py`** - Data loading and processing validation
- **`test_embedding_generation.py`** - Embedding generation testing
- **`test_clustering_integration.py`** - UMAP/HDBSCAN integration testing

### Running Tests

```bash
# Test database connection
python3 tests/test_connection.py

# Test complete pipeline
python3 tests/test_full_pipeline.py

# Run all tests
python3 -m pytest tests/
```

## 📈 Expected Results

### Data Volume
- **~32 CADS Researchers**: Faculty from CS Department
- **~2,454 Research Works**: Academic papers and publications
- **~6,834 Research Topics**: Topic classifications
- **384-dimensional embeddings**: Semantic representations

### Clustering Results
- **15-25 Research Clusters**: Grouped by semantic similarity
- **2D Visualization Coordinates**: UMAP-reduced positions
- **AI-Generated Themes**: Descriptive cluster names and summaries

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration (Required)
DATABASE_URL=postgresql://user:pass@host:port/db

# OpenAlex API (Required)
OPENALEX_EMAIL=your-email@domain.com

# Optional: Groq API for theme generation
GROQ_API_KEY=your-groq-api-key

# Optional: ML Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
UMAP_N_NEIGHBORS=15
UMAP_MIN_DIST=0.1
HDBSCAN_MIN_CLUSTER_SIZE=5
```

### Dependencies

**Core Dependencies**:
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `psycopg2-binary` - PostgreSQL connection
- `sqlalchemy` - Database ORM
- `sentence-transformers` - Embedding generation

**ML Dependencies**:
- `umap-learn` - Dimensionality reduction
- `hdbscan` - Clustering algorithm
- `scikit-learn` - Machine learning utilities

**API Dependencies**:
- `requests` - HTTP requests
- `groq` - AI theme generation

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Test connection
   python3 tests/test_connection.py
   
   # Check .env configuration
   cat .env
   ```

2. **Missing Dependencies**
   ```bash
   # Install all requirements
   pip install -r requirements.txt
   ```

3. **Import Errors**
   ```bash
   # Run from cads directory
   cd cads
   python3 process_data.py
   ```

4. **Memory Issues with Large Datasets**
   ```bash
   # Process in batches (modify BATCH_SIZE in .env)
   BATCH_SIZE=50
   ```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python3 process_data.py
```

## 🔄 Integration with Visualization

The CADS pipeline generates data files that integrate with the visualization dashboard:

1. **Data Export**: Pipeline exports JSON files to `data/` directory
2. **Visualization Import**: Dashboard reads JSON files for interactive display
3. **Search Integration**: Processed data enables semantic search functionality
4. **Real-time Updates**: Pipeline can be re-run to update visualizations

## 📝 Development

### Adding New Features

1. **Data Sources**: Extend `DataProcessor` class in `data_loader.py`
2. **Processing Steps**: Add functions to `process_data.py`
3. **Tests**: Create corresponding test files in `tests/`
4. **Documentation**: Update this README

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters
- Include docstrings for all classes and functions
- Add logging for important operations

## 🎯 Performance

### Optimization Tips

1. **Embedding Caching**: Embeddings are cached in database to avoid regeneration
2. **Batch Processing**: Large datasets processed in configurable batches
3. **Model Persistence**: UMAP/HDBSCAN models saved to avoid retraining
4. **Parallel Processing**: Multi-threading for embedding generation

### Benchmarks

- **Data Loading**: ~30 seconds for 2,454 works
- **Embedding Generation**: ~2 minutes for missing embeddings
- **UMAP Reduction**: ~45 seconds for 2,454 embeddings
- **HDBSCAN Clustering**: ~15 seconds for 2D coordinates
- **Total Pipeline**: ~5-10 minutes for complete processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📄 License

This project is part of the Texas State University research infrastructure.

---

**🎉 Ready to explore CADS research data!**

For questions or issues, please check the troubleshooting section or create an issue in the repository.