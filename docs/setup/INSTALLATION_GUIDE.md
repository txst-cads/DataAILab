# CADS Research Visualization System - Installation Guide

This comprehensive guide will walk you through setting up the CADS Research Visualization System from scratch. Follow these steps carefully to ensure a successful installation.

## 📋 Prerequisites

Before starting the installation, ensure you have the following prerequisites:

### System Requirements
- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: Version 3.8 or higher
- **Node.js**: Version 16 or higher (for development tools)
- **Git**: For repository management
- **Modern Web Browser**: Chrome, Firefox, Safari, or Edge

### Required Accounts and Services
- **Supabase Account**: For PostgreSQL database hosting
- **OpenAlex API Access**: Free with email registration
- **Groq API Key**: Optional, for AI-powered theme generation
- **Sentry Account**: Optional, for error monitoring

### Hardware Requirements
- **RAM**: Minimum 8GB, recommended 16GB
- **Storage**: At least 5GB free space
- **CPU**: Multi-core processor recommended for ML processing

## 🚀 Step-by-Step Installation

### Step 1: Repository Setup

```bash
# Clone the repository
git clone https://github.com/your-org/cads-research-visualization.git
cd cads-research-visualization

# Verify repository structure
ls -la
```

Expected output:
```
drwxr-xr-x  cads/           # Core data processing pipeline
drwxr-xr-x  visuals/        # Interactive visualization dashboard
drwxr-xr-x  database/       # Database schema and migrations
drwxr-xr-x  scripts/        # Utility scripts
drwxr-xr-x  docs/           # Documentation
drwxr-xr-x  data/           # Data storage
drwxr-xr-x  tests/          # Test suite
-rw-r--r--  README.md       # Main documentation
-rw-r--r--  .env            # Environment variables
```

### Step 2: Python Environment Setup

```bash
# Check Python version (must be 3.8+)
python3 --version

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Navigate to CADS directory
cd cads

# Install Python dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
# Test imports
python3 -c "import pandas, numpy, sklearn, sentence_transformers, umap, hdbscan; print('✅ All ML libraries installed successfully')"
```

### Step 3: Database Setup

#### 3.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project
3. Wait for the project to be ready (2-3 minutes)
4. Go to Settings → Database
5. Copy the connection string

#### 3.2 Configure Database Connection

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env  # or use your preferred editor
```

**Required environment variables:**
```bash
# Database Connection (from Supabase)
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres

# API Configuration
OPENALEX_EMAIL=your_email@domain.com

# Optional: AI Theme Generation
GROQ_API_KEY=your_groq_api_key

# Optional: ML Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
UMAP_N_NEIGHBORS=15
HDBSCAN_MIN_CLUSTER_SIZE=5
```

#### 3.3 Create Database Tables

```bash
# Run database migration
python3 ../scripts/migration/execute_cads_migration.py
```

Expected output:
```
🗄️  Creating CADS database tables...
✅ Connected to database successfully
✅ Created cads_researchers table
✅ Created cads_works table  
✅ Created cads_topics table
✅ Database setup completed successfully
```

**Verify database setup:**
```bash
# Check database connection
python3 ../scripts/utilities/check_cads_data_location.py
```

### Step 4: Data Processing Setup

#### 4.1 Initial Data Collection

```bash
# Process CADS research data from OpenAlex
python3 ../scripts/processing/process_cads_with_openalex_ids.py
```

This will:
- Read CADS faculty list from `data/cads.txt`
- Search OpenAlex for matching researchers
- Collect research papers and metadata
- Store data in the database

Expected processing time: 5-10 minutes

#### 4.2 Data Migration

```bash
# Migrate data to CADS-specific tables
python3 ../scripts/processing/migrate_cads_data_to_cads_tables.py
```

This creates CADS-specific copies of the data for processing.

#### 4.3 Run ML Pipeline

```bash
# Execute the complete ML pipeline
python3 process_data.py
```

This will:
- Generate semantic embeddings (384-dimensional vectors)
- Perform UMAP dimensionality reduction
- Execute HDBSCAN clustering
- Generate AI-powered cluster themes
- Create visualization data files

Expected processing time: 5-10 minutes

### Step 5: Visualization Setup

```bash
# Navigate to visualization directory
cd ../visuals/public

# Verify data files exist
ls -la data/
```

Expected files:
```
-rw-r--r--  visualization-data.json     # Complete dataset
-rw-r--r--  visualization-data.json.gz  # Compressed version
-rw-r--r--  cluster_themes.json         # AI-generated themes
-rw-r--r--  cluster_themes.json.gz      # Compressed version
-rw-r--r--  clustering_results.json     # Clustering results
-rw-r--r--  clustering_results.json.gz  # Compressed version
-rw-r--r--  search-index.json           # Search index
-rw-r--r--  search-index.json.gz        # Compressed version
```

### Step 6: Launch Application

```bash
# Start local web server
python3 -m http.server 8000

# Open in browser
open http://localhost:8000  # macOS
# or visit http://localhost:8000 manually
```

## ✅ Verification and Testing

### Basic Functionality Test

```bash
# Navigate back to project root
cd ../../

# Run comprehensive test suite
python3 tests/run_tests.py --all
```

### Visual Integration Test

```bash
# Run visual integration test
python3 tests/visualization/test_visual_integration.py
```

This will:
- Test data file integrity
- Start a local server
- Verify visualization loads correctly
- Provide manual testing checklist

### Database Connection Test

```bash
# Test database connectivity
python3 tests/database/test_connection.py
```

### Pipeline Integration Test

```bash
# Test complete ML pipeline
python3 tests/pipeline/test_full_pipeline.py
```

## 🔧 Configuration Options

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `OPENALEX_EMAIL` | Yes | - | Email for OpenAlex API access |
| `GROQ_API_KEY` | No | - | API key for AI theme generation |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model |
| `UMAP_N_NEIGHBORS` | No | `15` | UMAP neighbors parameter |
| `HDBSCAN_MIN_CLUSTER_SIZE` | No | `5` | Minimum cluster size |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Performance Tuning

For better performance on large datasets:

```bash
# Increase UMAP neighbors for better global structure
export UMAP_N_NEIGHBORS=30

# Decrease minimum cluster size for more granular clusters
export HDBSCAN_MIN_CLUSTER_SIZE=3

# Enable debug logging for troubleshooting
export LOG_LEVEL=DEBUG
```

## 🚨 Troubleshooting

### Common Installation Issues

#### 1. Python Dependencies Failed

**Problem**: `pip install` fails with compilation errors

**Solution**:
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev build-essential

# Install system dependencies (macOS)
xcode-select --install
```

#### 2. Database Connection Failed

**Problem**: Cannot connect to Supabase database

**Solutions**:
```bash
# Test connection manually
python3 -c "import psycopg2; print('✅ psycopg2 working')"

# Check environment variables
echo $DATABASE_URL

# Verify Supabase project is active
# Go to Supabase dashboard and check project status
```

#### 3. OpenAlex API Issues

**Problem**: API requests failing or rate limited

**Solutions**:
```bash
# Verify email is set
echo $OPENALEX_EMAIL

# Test API access
curl "https://api.openalex.org/works?filter=author.display_name:john+smith&mailto=$OPENALEX_EMAIL"

# Add delays between requests if rate limited
export OPENALEX_DELAY=1  # 1 second delay between requests
```

#### 4. ML Pipeline Memory Issues

**Problem**: Out of memory during UMAP/HDBSCAN processing

**Solutions**:
```bash
# Reduce dataset size for testing
export MAX_WORKS=1000

# Use smaller embedding model
export EMBEDDING_MODEL=all-MiniLM-L6-v2

# Increase system swap space
sudo swapon --show
```

#### 5. Visualization Not Loading

**Problem**: Blank page or JavaScript errors

**Solutions**:
```bash
# Check data files exist
ls -la visuals/public/data/

# Test with simple HTTP server
cd visuals/public
python3 -m http.server 8001

# Check browser console for errors
# Open Developer Tools → Console
```

### Getting Help

1. **Check logs**: Enable debug logging with `export LOG_LEVEL=DEBUG`
2. **Run tests**: Use the test suite to identify specific issues
3. **Check documentation**: Review component-specific README files
4. **Verify prerequisites**: Ensure all system requirements are met

## 📚 Next Steps

After successful installation:

1. **Explore the visualization**: Open http://localhost:8000 and test all features
2. **Review documentation**: Read the [User Guide](USER_GUIDE.md) for detailed usage instructions
3. **Set up monitoring**: Configure [Sentry integration](../monitoring/MONITORING_SETUP.md) for production use
4. **Configure CI/CD**: Set up [GitHub Actions](../../.github/workflows/README.md) for automated testing
5. **Customize data**: Add your own research data or modify the CADS faculty list

## 🔄 Regular Maintenance

### Weekly Tasks
- Update research data: `python3 scripts/processing/process_cads_with_openalex_ids.py`
- Regenerate visualizations: `python3 cads/process_data.py`
- Run test suite: `python3 tests/run_tests.py --all`

### Monthly Tasks
- Update Python dependencies: `pip install -r requirements.txt --upgrade`
- Review database performance and optimize queries
- Check for new OpenAlex data and API changes

### As Needed
- Add new CADS faculty to `data/cads.txt`
- Update visualization themes and styling
- Scale database resources based on usage

---

**🎉 Installation Complete!**

Your CADS Research Visualization System is now ready for use. Visit http://localhost:8000 to start exploring research data and patterns.

For additional help, see the [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) or [User Guide](USER_GUIDE.md).