# Optimized Data Format for CADS Research Visualization

This directory contains the optimized, compressed data files for the CADS Research Visualization System.

## Files

### `visualization-data.json.gz` (152,922 bytes)
Main visualization dataset containing all publications, researchers, and clusters in optimized format.

**Structure:**
```json
{
  "p": [  // Publications array
    {
      "i": 0,           // index (sequential)
      "t": "Title",     // title (truncated to 200 chars)
      "y": 2023,        // publication year
      "p": [x, y],      // UMAP position coordinates
      "r": 5,           // researcher index
      "c": 2,           // cluster index
      "cit": 15,        // citation count
      "d": "doi"        // DOI (optional)
    }
  ],
  "r": [  // Researchers array
    {
      "i": 0,           // index
      "n": "Name",      // full name
      "d": "Dept",      // department
      "col": [r,g,b]    // RGB color for visualization
    }
  ],
  "c": [  // Clusters array
    {
      "i": 0,           // cluster index
      "n": "Theme",     // AI-generated theme name
      "pos": [x, y],    // cluster center position
      "s": 45           // cluster size (number of papers)
    }
  ],
  "v": {  // View state for initial map view
    "longitude": 4.24,
    "latitude": 5.61,
    "zoom": 3.56
  },
  "meta": {  // Metadata
    "version": "1.0.0",
    "generated": "2025-07-31T19:46:01.900409",
    "totalPapers": 2454,
    "totalResearchers": 31,
    "totalClusters": 33
  }
}
```

### `search-index.json.gz` (111,820 bytes)
Pre-built search index for instant full-text search across all content.

**Structure:**
```json
{
  "entries": [  // Searchable entries
    {
      "id": 0,
      "type": "publication",  // or "researcher" or "cluster"
      "title": "Paper Title",
      "year": 2023,
      "researcher": "Author Name",
      "cluster": "Theme Name"
    }
  ],
  "meta": {
    "totalEntries": 2518,
    "generated": "2025-07-31T19:46:01.900409"
  }
}
```

## Data Optimization Features

- **Minimal Keys**: Short property names (i, t, y, p, r, c, cit) to reduce payload size
- **Integer Indices**: Uses sequential integers instead of UUIDs for references
- **Coordinate Precision**: UMAP coordinates rounded to 3 decimal places
- **Title Truncation**: Paper titles limited to 200 characters
- **Gzip Compression**: 3.2:1 compression ratio for fast loading
- **Total Payload**: 264,742 bytes (259 KB) for entire dataset

## Performance Targets

- **Loading Time**: <500ms to interactive
- **Bundle Size**: <200KB total JavaScript
- **Data Payload**: <300KB compressed (achieved: 259KB)
- **Search Response**: <50ms for any query
- **Rendering**: 60fps interactions with WebGL

## Usage

Load the data in your web application:

```javascript
// Load main visualization data
const response = await fetch('/data/visualization-data.json.gz');
const data = await response.json();

// Load search index
const searchResponse = await fetch('/data/search-index.json.gz');
const searchIndex = await searchResponse.json();

// Initialize visualization
const publications = data.p;
const researchers = data.r;
const clusters = data.c;
const viewState = data.v;
```

## Data Sources

- **Publications**: 2,454 research papers from CADS database
- **Researchers**: 31 faculty members with department affiliations
- **Clusters**: 33 AI-generated research themes using HDBSCAN clustering
- **Coordinates**: UMAP dimensionality reduction from 384D embeddings
- **Citations**: Citation counts from OpenAlex database
- **Themes**: Generated using Groq LLM (Llama3-8B model)

## Generation

Data generated using `create_optimized_data.py` on 2025-07-31.
To regenerate: `python create_optimized_data.py`