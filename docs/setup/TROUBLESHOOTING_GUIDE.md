# Troubleshooting Guide

This comprehensive troubleshooting guide covers common issues, solutions, and debugging procedures for the CADS Research Visualization System.

## 🚨 Quick Diagnostic Commands

Before diving into specific issues, run these diagnostic commands to get an overview of system status:

```bash
# Check system status
python3 tests/run_tests.py --health-check

# Test database connection
python3 tests/database/test_connection.py

# Verify data files
python3 scripts/utilities/check_cads_data_location.py

# Test visualization
python3 tests/visualization/test_visual_integration.py
```

## 🗄️ Database Issues

### Issue 1: Database Connection Failed

**Symptoms:**
- `psycopg2.OperationalError: could not connect to server`
- `Connection refused` errors
- Tests failing with database connection errors

**Diagnostic Steps:**
```bash
# Check environment variables
echo $DATABASE_URL
env | grep DATABASE

# Test basic connection
python3 -c "import psycopg2; conn = psycopg2.connect('$DATABASE_URL'); print('✅ Connection successful')"

# Check if database is accessible
ping your-database-host.com
```

**Solutions:**

1. **Verify Database URL Format:**
```bash
# Correct format
DATABASE_URL=postgresql://username:password@host:port/database

# Common mistakes to avoid
# ❌ Missing protocol: username:password@host:port/database
# ❌ Wrong protocol: mysql://username:password@host:port/database
# ❌ Missing port: postgresql://username:password@host/database
```

2. **Check Supabase Project Status:**
- Go to Supabase dashboard
- Verify project is active (not paused)
- Check connection pooler settings
- Ensure IP allowlist includes your IP

3. **Test with Different Connection Methods:**
```bash
# Try direct connection
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='your-host',
    port=5432,
    database='postgres',
    user='postgres',
    password='your-password'
)
print('✅ Direct connection works')
"

# Try with connection pooler
DATABASE_URL=postgresql://username:password@host:6543/postgres
```

### Issue 2: Database Tables Missing

**Symptoms:**
- `relation "cads_researchers" does not exist`
- `Table not found` errors
- Empty query results

**Diagnostic Steps:**
```bash
# Check if tables exist
python3 -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
cur = conn.cursor()
cur.execute(\"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'cads_%'\")
tables = cur.fetchall()
print('CADS tables:', tables)
"
```

**Solutions:**

1. **Run Database Migration:**
```bash
python3 scripts/migration/execute_cads_migration.py
```

2. **Check Migration Logs:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 scripts/migration/execute_cads_migration.py
```

3. **Manual Table Creation:**
```bash
# Connect to database and run SQL manually
psql $DATABASE_URL -f database/schema/create_cads_tables.sql
```

### Issue 3: Data Not Found in Database

**Symptoms:**
- Empty visualization
- "No data found" messages
- Zero results from queries

**Diagnostic Steps:**
```bash
# Check data location
python3 scripts/utilities/check_cads_data_location.py

# Count records in each table
python3 -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
cur = conn.cursor()
for table in ['cads_researchers', 'cads_works', 'cads_topics']:
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    count = cur.fetchone()[0]
    print(f'{table}: {count} records')
"
```

**Solutions:**

1. **Run Data Collection:**
```bash
# Collect data from OpenAlex
python3 scripts/processing/process_cads_with_openalex_ids.py

# Migrate to CADS tables
python3 scripts/processing/migrate_cads_data_to_cads_tables.py
```

2. **Check CADS Faculty List:**
```bash
# Verify faculty list exists
ls -la data/cads.txt
head -5 data/cads.txt
```

3. **Test OpenAlex API:**
```bash
# Test API access
curl "https://api.openalex.org/works?filter=author.display_name:john+smith&mailto=$OPENALEX_EMAIL"
```

## 🐍 Python and Dependencies Issues

### Issue 4: Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'pandas'`
- `ImportError: cannot import name 'SentenceTransformer'`
- Missing library errors

**Diagnostic Steps:**
```bash
# Check Python version
python3 --version

# Check installed packages
pip list | grep -E "(pandas|numpy|sklearn|sentence-transformers|umap|hdbscan)"

# Test imports individually
python3 -c "import pandas; print('✅ pandas:', pandas.__version__)"
python3 -c "import numpy; print('✅ numpy:', numpy.__version__)"
python3 -c "import sklearn; print('✅ sklearn:', sklearn.__version__)"
```

**Solutions:**

1. **Reinstall Dependencies:**
```bash
cd cads
pip install -r requirements.txt --force-reinstall
```

2. **Use Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r cads/requirements.txt
```

3. **Install System Dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# macOS
xcode-select --install
brew install python@3.9
```

### Issue 5: Memory Issues During ML Processing

**Symptoms:**
- `MemoryError` during UMAP or HDBSCAN
- Process killed by system
- Extremely slow processing

**Diagnostic Steps:**
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Monitor memory usage during processing
top -p $(pgrep -f process_data.py)
```

**Solutions:**

1. **Reduce Dataset Size:**
```bash
# Process subset of data
export MAX_WORKS=1000
python3 cads/process_data.py
```

2. **Use Smaller Embedding Model:**
```bash
export EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller model
python3 cads/process_data.py
```

3. **Optimize UMAP Parameters:**
```bash
export UMAP_N_NEIGHBORS=10  # Reduce from default 15
export UMAP_MIN_DIST=0.1
python3 cads/process_data.py
```

4. **Increase System Swap:**
```bash
# Linux - create swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 🌐 Visualization Issues

### Issue 6: Blank Visualization Page

**Symptoms:**
- White/blank page when accessing visualization
- No error messages visible
- Browser shows "loading" indefinitely

**Diagnostic Steps:**
```bash
# Check data files exist
ls -la visuals/public/data/

# Test local server
cd visuals/public
python3 -m http.server 8000
# Visit http://localhost:8000

# Check browser console for errors
# Open Developer Tools → Console tab
```

**Solutions:**

1. **Verify Data Files:**
```bash
# Check all required files exist
cd visuals/public/data
for file in visualization-data.json cluster_themes.json clustering_results.json search-index.json; do
    if [ -f "$file" ]; then
        echo "✅ $file exists ($(wc -c < "$file") bytes)"
    else
        echo "❌ $file missing"
    fi
done
```

2. **Test Data File Validity:**
```bash
# Test JSON validity
python3 -c "
import json
for file in ['visualization-data.json', 'cluster_themes.json', 'clustering_results.json']:
    try:
        with open(f'visuals/public/data/{file}') as f:
            data = json.load(f)
        print(f'✅ {file} is valid JSON')
    except Exception as e:
        print(f'❌ {file} error: {e}')
"
```

3. **Regenerate Visualization Data:**
```bash
cd cads
python3 process_data.py
```

### Issue 7: JavaScript Errors

**Symptoms:**
- Console errors in browser
- Visualization partially working
- Interactive features not responding

**Diagnostic Steps:**
```bash
# Check browser console (F12 → Console)
# Look for errors like:
# - "deck is not defined"
# - "Cannot read property of undefined"
# - "Failed to fetch"

# Test with simple HTML page
cd visuals/public
python3 -m http.server 8001
# Visit http://localhost:8001/test_server_basic.html
```

**Solutions:**

1. **Check Deck.gl Loading:**
```html
<!-- Verify this script loads in HTML -->
<script src="https://unpkg.com/deck.gl@latest/dist.min.js"></script>
```

2. **Test Data Loading:**
```javascript
// Test in browser console
fetch('/data/visualization-data.json')
  .then(response => response.json())
  .then(data => console.log('Data loaded:', Object.keys(data)))
  .catch(error => console.error('Data loading failed:', error));
```

3. **Use Browser Compatibility Mode:**
```html
<!-- Add to HTML head for older browsers -->
<script src="https://polyfill.io/v3/polyfill.min.js"></script>
```

### Issue 8: Slow Visualization Performance

**Symptoms:**
- Long loading times (>10 seconds)
- Laggy interactions
- Browser becomes unresponsive

**Diagnostic Steps:**
```bash
# Check data file sizes
ls -lh visuals/public/data/

# Test with compressed files
curl -H "Accept-Encoding: gzip" http://localhost:8000/data/visualization-data.json.gz
```

**Solutions:**

1. **Use Compressed Data Files:**
```bash
# Ensure .gz files are being served
ls -la visuals/public/data/*.gz

# Test compression
gzip -t visuals/public/data/*.gz
```

2. **Optimize Data Size:**
```bash
# Reduce dataset for testing
export MAX_WORKS=500
python3 cads/process_data.py
```

3. **Enable Browser Caching:**
```html
<!-- Add cache headers in server configuration -->
Cache-Control: public, max-age=3600
```

## 🔧 API and External Service Issues

### Issue 9: OpenAlex API Failures

**Symptoms:**
- `HTTP 429: Too Many Requests`
- `HTTP 403: Forbidden`
- No data returned from API

**Diagnostic Steps:**
```bash
# Test API access
curl -I "https://api.openalex.org/works?mailto=$OPENALEX_EMAIL"

# Check rate limiting
curl -v "https://api.openalex.org/works?filter=author.display_name:test&mailto=$OPENALEX_EMAIL"
```

**Solutions:**

1. **Add Email to Requests:**
```bash
# Ensure email is set
export OPENALEX_EMAIL=your_email@domain.com
echo $OPENALEX_EMAIL
```

2. **Add Request Delays:**
```bash
# Add delay between requests
export OPENALEX_DELAY=1  # 1 second delay
python3 scripts/processing/process_cads_with_openalex_ids.py
```

3. **Use Polite Pool:**
```python
# In your API requests, use the polite pool
base_url = "https://api.openalex.org"
params = {
    "mailto": os.getenv("OPENALEX_EMAIL"),
    "per-page": 25  # Smaller batches
}
```

### Issue 10: Groq API Issues (Theme Generation)

**Symptoms:**
- Generic cluster themes instead of AI-generated ones
- `API key not found` errors
- Theme generation skipped

**Diagnostic Steps:**
```bash
# Check API key
echo $GROQ_API_KEY

# Test API access
curl -H "Authorization: Bearer $GROQ_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.groq.com/openai/v1/models
```

**Solutions:**

1. **Set API Key:**
```bash
export GROQ_API_KEY=your_groq_api_key
# Add to .env file for persistence
```

2. **Skip AI Theme Generation:**
```bash
# Run without AI themes (uses generic themes)
unset GROQ_API_KEY
python3 cads/process_data.py
```

3. **Use Alternative Theme Generation:**
```python
# Modify process_data.py to use simple keyword-based themes
# This is automatically done when GROQ_API_KEY is not set
```

## 🧪 Testing Issues

### Issue 11: Tests Failing

**Symptoms:**
- Test suite reports failures
- Individual tests pass but full suite fails
- Inconsistent test results

**Diagnostic Steps:**
```bash
# Run tests with verbose output
python3 tests/run_tests.py --verbose

# Run individual failing test
python3 -m pytest tests/database/test_connection.py -v

# Check test environment
env | grep -E "(DATABASE|TEST|LOG)"
```

**Solutions:**

1. **Set Test Environment:**
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db
export LOG_LEVEL=ERROR  # Reduce noise
export OPENALEX_EMAIL=test@example.com
```

2. **Run Tests in Isolation:**
```bash
# Run each category separately
python3 tests/run_tests.py --database
python3 tests/run_tests.py --pipeline
python3 tests/run_tests.py --visualization
```

3. **Clean Test Environment:**
```bash
# Remove test artifacts
rm -rf tests/__pycache__/
rm -rf .pytest_cache/
rm -f test-results.xml
```

## 🔍 Performance Issues

### Issue 12: Slow Data Processing

**Symptoms:**
- Pipeline takes >30 minutes
- High CPU/memory usage
- Process appears stuck

**Diagnostic Steps:**
```bash
# Monitor process
top -p $(pgrep -f process_data.py)

# Check progress logs
tail -f logs/processing.log

# Profile memory usage
python3 -m memory_profiler cads/process_data.py
```

**Solutions:**

1. **Optimize Parameters:**
```bash
export UMAP_N_NEIGHBORS=10      # Reduce from 15
export HDBSCAN_MIN_CLUSTER_SIZE=3  # Reduce from 5
export MAX_WORKS=1000           # Limit dataset size
```

2. **Use Incremental Processing:**
```bash
# Process in batches
export BATCH_SIZE=100
python3 cads/process_data.py --incremental
```

3. **Enable Parallel Processing:**
```bash
export N_JOBS=4  # Use 4 CPU cores
python3 cads/process_data.py
```

## 🚨 Emergency Recovery Procedures

### Complete System Reset

If the system is completely broken, follow these steps:

```bash
# 1. Backup current state
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# 2. Reset database
python3 scripts/migration/execute_cads_migration.py --reset

# 3. Clear all data files
rm -rf data/processed/*
rm -rf visuals/public/data/*

# 4. Reinstall dependencies
cd cads
pip install -r requirements.txt --force-reinstall

# 5. Run complete pipeline
python3 ../scripts/processing/process_cads_with_openalex_ids.py
python3 ../scripts/processing/migrate_cads_data_to_cads_tables.py
python3 process_data.py

# 6. Test system
cd ..
python3 tests/run_tests.py --all
```

### Data Recovery

If data is corrupted or lost:

```bash
# 1. Check for backups
ls -la backup_before_cleanup/
ls -la data_backup_*/

# 2. Restore from backup
cp -r backup_before_cleanup/cads/data/* data/processed/
cp -r backup_before_cleanup/visuals/data/* visuals/public/data/

# 3. Verify data integrity
python3 scripts/utilities/check_cads_data_location.py

# 4. Regenerate if needed
python3 cads/process_data.py
```

## 📞 Getting Additional Help

### Diagnostic Information to Collect

When seeking help, collect this information:

```bash
# System information
uname -a
python3 --version
pip --version

# Environment variables (sanitized)
env | grep -E "(DATABASE|OPENALEX|GROQ)" | sed 's/=.*/=***/'

# Error logs
tail -50 logs/error.log

# Test results
python3 tests/run_tests.py --health-check > diagnostic_report.txt 2>&1
```

### Log Files Locations

```bash
# Application logs
logs/processing.log      # ML pipeline logs
logs/error.log          # Error logs
logs/api.log            # API request logs

# System logs
/var/log/syslog         # System logs (Linux)
/var/log/system.log     # System logs (macOS)

# Test logs
test-results.xml        # Test execution results
coverage.xml           # Test coverage report
```

### Support Channels

1. **Documentation**: Check component-specific README files
2. **GitHub Issues**: Create detailed issue reports
3. **Test Suite**: Use automated diagnostics
4. **Community**: Join discussions in GitHub Discussions

---

**🔧 Troubleshooting Complete**

This guide covers the most common issues and their solutions. For issues not covered here, use the diagnostic commands and log analysis to identify the root cause, then apply similar troubleshooting principles.