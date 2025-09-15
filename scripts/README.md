# CADS Scripts Directory

## 🔧 Overview

This directory contains organized scripts for CADS data processing, migration, and maintenance tasks. Scripts are categorized by function for easy discovery and maintenance.

## 📁 Directory Structure

```
scripts/
├── README.md                    # This documentation
├── migration/                   # Database migration scripts
│   ├── execute_cads_migration.py    # ✅ MAIN MIGRATION SCRIPT
│   └── legacy/                      # 📁 Archived migration attempts
│       ├── execute_cads_migration_direct.py
│       ├── execute_cads_migration_alternative.py
│       ├── execute_cads_migration_fixed.py
│       ├── execute_cads_migration_ipv6.py
│       ├── execute_cads_migration_port_6543.py
│       ├── execute_cads_migration_retry.py
│       └── execute_cads_migration.py
├── processing/                  # Data processing scripts
│   ├── process_cads_with_openalex_ids.py    # ✅ RECOMMENDED
│   └── migrate_cads_data_to_cads_tables.py  # ✅ ESSENTIAL
└── utilities/                   # Utility and verification scripts
    ├── check_cads_data_location.py
    ├── check_existing_cads_data.py
    ├── test_cads_parsing.py
    └── [other utility scripts]
```

## 🚀 Quick Start Workflow

### For Fresh CADS Database Setup:

```bash
# Step 1: Create CADS tables and basic structure
python3 scripts/migration/execute_cads_migration.py

# Step 2: Process all CADS professors with OpenAlex IDs  
python3 scripts/processing/process_cads_with_openalex_ids.py

# Step 3: Migrate data to CADS-specific tables
python3 scripts/processing/migrate_cads_data_to_cads_tables.py

# Step 4: Verify data location and completeness
python3 scripts/utilities/check_cads_data_location.py
```

## 📂 Script Categories

### 🚀 Migration Scripts (`migration/`)

#### Main Migration Script ✅
- **`execute_cads_migration.py`** - **WORKING VERSION**
  - Uses IPv4 pooler connection (recommended)
  - Creates CADS tables and migrates data
  - Handles SQL syntax issues properly
  - **Status**: ✅ Tested and working

#### Legacy Scripts 📁
Located in `migration/legacy/` - These are archived versions with various connection approaches:
- `execute_cads_migration_direct.py` - Direct DATABASE_URL (has IPv6 issues)
- `execute_cads_migration_alternative.py` - Multiple connection methods
- `execute_cads_migration_fixed.py` - DNS resolution fix attempt
- `execute_cads_migration_ipv6.py` - IPv6 specific approach
- `execute_cads_migration_port_6543.py` - Port 6543 testing
- `execute_cads_migration_retry.py` - Retry logic implementation
- `execute_cads_migration.py` - Original migration script

### 📊 Processing Scripts (`processing/`)

#### OpenAlex Integration ✅
- **`process_cads_with_openalex_ids.py`** - **RECOMMENDED**
  - Processes all 42 CADS professors using known OpenAlex IDs
  - Most reliable approach for data collection
  - Handles all professors with confirmed OpenAlex profiles
  - **Status**: ✅ Tested and working

#### Data Migration ✅
- **`migrate_cads_data_to_cads_tables.py`** - **ESSENTIAL**
  - Migrates data from main tables to CADS-specific tables
  - Fixes data location issues
  - Required after running main processing scripts
  - **Status**: ✅ Tested and working

### 🔍 Utility Scripts (`utilities/`)

#### Data Verification
- **`check_cads_data_location.py`** - Verify where CADS data is stored
- **`check_existing_cads_data.py`** - Analyze existing CADS data
- **`test_cads_parsing.py`** - Test CADS data parsing functionality

## 🎯 Script Details

### Migration Script

**File**: `scripts/migration/execute_cads_migration.py`

**Purpose**: Creates CADS database tables and initial structure

**Features**:
- IPv4 pooler connection (resolves DNS issues)
- Complete CADS schema creation
- Error handling and logging
- Verification of table creation

**Usage**:
```bash
python3 scripts/migration/execute_cads_migration.py
```

**Expected Output**:
- Creates `cads_researchers`, `cads_works`, `cads_topics` tables
- Sets up indexes and relationships
- Enables vector extension for embeddings

### Processing Script

**File**: `scripts/processing/process_cads_with_openalex_ids.py`

**Purpose**: Fetches and processes research data for all CADS faculty

**Features**:
- Uses known OpenAlex IDs for reliable data retrieval
- Processes ~42 CADS professors
- Generates semantic embeddings
- Handles API rate limiting

**Usage**:
```bash
python3 scripts/processing/process_cads_with_openalex_ids.py
```

**Expected Output**:
- ~32 researchers in database
- ~2,454 research works
- ~6,834 research topics
- Complete embeddings for all works

### Data Migration Script

**File**: `scripts/processing/migrate_cads_data_to_cads_tables.py`

**Purpose**: Moves data from main tables to CADS-specific tables

**Features**:
- Transfers data between table structures
- Maintains relationships and integrity
- Handles duplicate prevention
- Provides migration summary

**Usage**:
```bash
python3 scripts/processing/migrate_cads_data_to_cads_tables.py
```

**Expected Output**:
- Data moved to `cads_*` tables
- Verification of successful migration
- Summary of migrated records

## ⚙️ Configuration

### Environment Requirements

All scripts require these environment variables:

```bash
# IPv4 Pooler Connection (Required)
user=postgres.zsezliiffdcgqekwggjq
password=cadstxst2025
host=aws-0-us-east-2.pooler.supabase.com
port=5432
dbname=postgres

# OpenAlex API (Required)
OPENALEX_EMAIL=test@texasstate.edu

# Optional: Groq API for theme generation
GROQ_API_KEY=your-groq-api-key
```

### Dependencies

Scripts require these Python packages:
- `psycopg2-binary` - PostgreSQL connection
- `requests` - HTTP requests for APIs
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable loading

## 📈 Success Metrics

### Expected Results After Full Workflow:

| Metric | Expected Value | Description |
|--------|---------------|-------------|
| **CADS Researchers** | ~32 | Faculty from CS Department |
| **Research Works** | ~2,454 | Academic papers and publications |
| **Research Topics** | ~6,834 | Topic classifications |
| **Embeddings** | 100% | All works have semantic vectors |
| **Citations** | Complete | Citation data for all works |

## 🚨 Troubleshooting

### Common Issues

#### 1. **IPv6 Connection Errors**
```bash
# Solution: Use IPv4 pooler scripts only
python3 scripts/migration/execute_cads_migration.py
```

#### 2. **Data in Wrong Tables**
```bash
# Solution: Run migration script
python3 scripts/processing/migrate_cads_data_to_cads_tables.py
```

#### 3. **Missing OpenAlex Data**
- Check API rate limits (10 requests/second)
- Verify network connectivity
- Check OPENALEX_EMAIL configuration

#### 4. **SQL Syntax Errors**
- Use the main migration script (handles syntax properly)
- Avoid legacy scripts unless debugging

### Debug Commands

```bash
# Check data location
python3 scripts/utilities/check_cads_data_location.py

# Verify existing data
python3 scripts/utilities/check_existing_cads_data.py

# Test parsing functionality
python3 scripts/utilities/test_cads_parsing.py
```

## 📝 Logging

All scripts generate detailed logs:
- **Execution logs**: Saved to console and log files
- **Error tracking**: Full stack traces for debugging
- **Progress monitoring**: Real-time status updates
- **Performance metrics**: Timing and success rates

## 🔄 Maintenance

### Regular Tasks

1. **Data Updates**: Re-run processing scripts monthly
2. **Schema Updates**: Apply new migrations as needed
3. **Performance Monitoring**: Check script execution times
4. **Error Monitoring**: Review logs for issues

### Script Updates

When updating scripts:
1. Test in development environment first
2. Backup database before major changes
3. Update documentation
4. Archive old versions to legacy folder

## 🎯 Script Status Summary

| Script | Status | Purpose | Recommended |
|--------|--------|---------|-------------|
| `migration/execute_cads_migration.py` | ✅ Working | Database setup | **Yes** |
| `processing/process_cads_with_openalex_ids.py` | ✅ Working | Data collection | **Yes** |
| `processing/migrate_cads_data_to_cads_tables.py` | ✅ Working | Data organization | **Yes** |
| `utilities/check_cads_data_location.py` | ✅ Working | Verification | **Yes** |
| `migration/legacy/*` | ⚠️ Archived | Alternative approaches | **No** |

## 🔗 Integration

### With CADS Pipeline
- Scripts prepare data for pipeline processing
- Pipeline reads from tables created by migration scripts
- Processing scripts generate data consumed by pipeline

### With Visualization
- Scripts create data structure for visualization
- Migration ensures proper table relationships
- Processing provides complete dataset for display

---

**🎯 Scripts organized and ready for reliable CADS database management!**