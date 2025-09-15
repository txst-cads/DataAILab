# Database Schema and Migrations

## 🗄️ Overview

This directory contains all database-related files for the CADS Research Visualization project, including table schemas, migration scripts, and database documentation.

## 📁 Directory Structure

```
database/
├── README.md                    # This documentation
├── schema/                      # Database table definitions
│   ├── create_cads_tables.sql   # Complete CADS schema
│   └── create_cads_tables_simple.sql # Simplified version
└── migrations/                  # Database migration scripts
    └── [future migration files]
```

## 🏗️ Database Schema

### Core Tables

#### 1. **cads_researchers**
- **Purpose**: Faculty information from Texas State CS Department
- **Key Fields**: 
  - `openalex_id` - OpenAlex researcher identifier
  - `full_name` - Researcher full name
  - `h_index` - Citation impact metric
  - `department` - Academic department

#### 2. **cads_works**
- **Purpose**: Academic papers and publications
- **Key Fields**:
  - `openalex_id` - OpenAlex work identifier
  - `title` - Publication title
  - `abstract` - Publication abstract
  - `embedding` - 384-dimensional semantic vector
  - `citations` - Citation count
  - `publication_year` - Year of publication

#### 3. **cads_topics**
- **Purpose**: Research topic classifications
- **Key Fields**:
  - `name` - Topic name
  - `type` - Topic classification type
  - `score` - Topic relevance score

### Relationships

```
cads_researchers (1) ──── (N) cads_works (1) ──── (N) cads_topics
       │                           │
       └─── institution_id ────────┘
```

## 🚀 Setup Instructions

### 1. Create Tables

Run the main schema file in your Supabase SQL editor:

```sql
-- Execute this in Supabase SQL Editor
\i database/schema/create_cads_tables.sql
```

### 2. Verify Installation

```sql
-- Check table creation
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE 'cads_%';

-- Check record counts
SELECT 
  (SELECT COUNT(*) FROM cads_researchers) as researchers,
  (SELECT COUNT(*) FROM cads_works) as works,
  (SELECT COUNT(*) FROM cads_topics) as topics;
```

## 📊 Expected Data Volume

- **~32 CADS Researchers**: Faculty from CS Department
- **~2,454 Research Works**: Academic papers and publications  
- **~6,834 Research Topics**: Topic classifications
- **384-dimensional embeddings**: Semantic representations for all works

## 🔧 Database Configuration

### Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;      -- For embedding storage
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- For UUID generation
```

### Indexes

The schema includes optimized indexes for:
- **Text search**: Full-text search on titles and abstracts
- **Vector similarity**: Efficient embedding similarity queries
- **Filtering**: Fast filtering by year, citations, researcher
- **Joins**: Optimized relationship queries

## 🔍 Common Queries

### Research Overview
```sql
-- Get researcher summary with work counts
SELECT 
    r.full_name,
    r.department,
    r.h_index,
    COUNT(w.id) as total_works,
    SUM(w.citations) as total_citations
FROM cads_researchers r
LEFT JOIN cads_works w ON r.id = w.researcher_id
GROUP BY r.id, r.full_name, r.department, r.h_index
ORDER BY total_works DESC;
```

### Semantic Search
```sql
-- Find similar works using embeddings
SELECT 
    w.title,
    w.abstract,
    r.full_name,
    1 - (w.embedding <=> $1::vector) as similarity
FROM cads_works w
JOIN cads_researchers r ON w.researcher_id = r.id
WHERE w.embedding IS NOT NULL
ORDER BY w.embedding <=> $1::vector
LIMIT 10;
```

### Topic Analysis
```sql
-- Most common research topics
SELECT 
    t.name,
    COUNT(*) as work_count,
    AVG(t.score) as avg_score
FROM cads_topics t
GROUP BY t.name
ORDER BY work_count DESC
LIMIT 20;
```

## 🔄 Migration History

### Initial Schema (v1.0)
- Created core CADS tables
- Established relationships with main institution tables
- Added vector extension for embeddings
- Implemented full-text search indexes

### Future Migrations
- Additional indexes for performance optimization
- New tables for collaboration networks
- Enhanced topic hierarchies

## 🚨 Troubleshooting

### Common Issues

1. **Vector Extension Missing**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **UUID Extension Missing**
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

3. **Permission Issues**
   - Ensure your database user has CREATE privileges
   - Check that extensions can be installed

4. **Large Dataset Performance**
   - Monitor index usage with `EXPLAIN ANALYZE`
   - Consider partitioning for very large datasets

### Performance Optimization

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' AND tablename LIKE 'cads_%'
ORDER BY idx_scan DESC;

-- Analyze table statistics
ANALYZE cads_researchers;
ANALYZE cads_works;
ANALYZE cads_topics;
```

## 📝 Maintenance

### Regular Tasks

1. **Update Statistics**
   ```sql
   ANALYZE cads_researchers;
   ANALYZE cads_works; 
   ANALYZE cads_topics;
   ```

2. **Monitor Index Performance**
   ```sql
   SELECT * FROM pg_stat_user_indexes WHERE tablename LIKE 'cads_%';
   ```

3. **Check Data Quality**
   ```sql
   -- Works without embeddings
   SELECT COUNT(*) FROM cads_works WHERE embedding IS NULL;
   
   -- Researchers without works
   SELECT r.full_name FROM cads_researchers r
   LEFT JOIN cads_works w ON r.id = w.researcher_id
   WHERE w.id IS NULL;
   ```

## 🔗 Integration

### With CADS Pipeline
- Pipeline reads from these tables using `data_loader.py`
- Embeddings are generated and stored in `cads_works.embedding`
- Clustering results reference work IDs

### With Visualization
- Dashboard queries these tables for display data
- Search functionality uses full-text and vector indexes
- Real-time updates possible through database triggers

---

**🎯 Database schema ready for CADS research data processing and visualization!**