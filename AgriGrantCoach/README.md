# AgriGrantCoach-AFRI

**Advanced AI-Powered Competitiveness Assessment for USDA AFRI Data Science Proposals**

AgriGrantCoach-AFRI is a sophisticated analysis tool that provides evidence-based assessments of research proposal competitiveness for USDA Agriculture and Food Research Initiative (AFRI) Data Science for Food and Agricultural Systems (DSFAS) programs. It combines semantic search with LLM verification to provide accurate, actionable feedback.

## 🌟 Key Features

- **Hybrid Semantic + LLM Verification**: Combines FAISS vector search with LLM judgment for accurate requirement detection
- **Dynamic Rubric Extraction**: Uses LLMs to extract evaluation criteria directly from solicitations (no hard-coded rubrics)
- **Smart Text Chunking**: Sentence-level splitting with sliding windows preserves context and creates focused embeddings
- **Evidence-Based Citations**: Every finding backed by specific paragraph numbers and direct quotes
- **Personalized Analysis**: Mentions PI/Co-PI names and their specific expertise throughout reports
- **Streamlit Web Interface**: User-friendly UI for document upload and interactive analysis
- **Actionable Recommendations**: Prioritized, specific guidance with example language
- **OpenAI & Groq Support**: Flexible LLM backend configuration

## 🎯 What's New (v2.0)

✨ **Major Accuracy Improvements**:
- **32.6% alignment detection** (up from 10.2%) using hybrid LLM verification
- **Smart chunking** splits long paragraphs (1600+ chars) into focused semantic units
- **LLM verification** confirms matches that semantic search might miss
- **Direct evidence extraction** with verbatim quotes from narrative

✨ **User Experience**:
- **Streamlit web interface** for easy document upload and analysis
- **Progress tracking** through 5 analysis phases
- **Visual dashboards** with color-coded metrics
- **One-click report download** in Markdown format

✨ **Team Analysis**:
- **PI names mentioned throughout** (Ekin, Dey, OChen, qasem)
- **Specific expertise highlighted** (e.g., "Ekin's Bayesian modeling expertise")
- **Publication analysis** linked to team members

## 🏗️ Architecture

```
AgriGrantCoach-AFRI/
│
├── main.py                    # CLI orchestrator
├── streamlit_app.py          # Web interface (NEW!)
├── src/
│   ├── config.py             # Centralized configuration
│   ├── data_loader.py        # Multi-format document parsing
│   ├── smart_chunker.py      # Intelligent text chunking (NEW!)
│   ├── rubric_analyzer.py    # LLM-based requirement extraction
│   ├── semantic_analyzer.py  # Hybrid FAISS + LLM verification (NEW!)
│   ├── team_analyzer.py      # Personnel expertise evaluation
│   └── report_generator.py   # Final synthesis with PI names
│
├── data/
│   ├── solicitation/         # USDA AFRI solicitation PDF
│   ├── narrative/            # Project narrative DOCX
│   ├── biosketches/          # Team member biosketches
│   └── cps/                  # Current & Pending Support docs
│
└── output/                   # Generated reports and analyses
```

## 📋 Prerequisites

- Python 3.9+ (tested on 3.13)
- OpenAI or Groq API key
- Documents:
  - 1 USDA AFRI solicitation (PDF)
  - 1 project narrative (DOCX)
  - N biosketches (DOCX) - one per team member
  - N Current & Pending Support documents (DOCX)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and navigate
cd AgriGrantCoach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Edit the parent `.env` file (`DataAILab/.env`):

```bash
# Use OpenAI (recommended)
GROQ_API_KEY=sk-proj-your-openai-key-here
GROQ_ANALYSIS_MODEL=gpt-4o-mini

# OR use Groq
GROQ_API_KEY=gsk_your-groq-key-here
GROQ_ANALYSIS_MODEL=llama-3.3-70b-versatile

# Analysis parameters
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
SEMANTIC_SIMILARITY_THRESHOLD=0.60
```

### 3. Upload Documents

Place your documents in `data/` subdirectories:

```bash
data/
├── solicitation/
│   └── 7c_solicitation.pdf
├── narrative/
│   └── AI_agricultural_grant_narrative.docx
├── biosketches/
│   ├── BiographicalSketch_Ekin.docx
│   ├── BiographicalSketch_Dey.docx
│   └── ...
└── cps/
    ├── cps_Ekin.docx
    ├── cps_Dey.docx
    └── ...
```

### 4. Run Analysis

**Option A: Web Interface (Recommended)**

```bash
streamlit run streamlit_app.py
```

Then open http://localhost:8501 and upload your documents.

**Option B: Command Line**

```bash
python main.py
```

## 💻 Usage Modes

### Streamlit Web Interface

The easiest way to use AgriGrantCoach:

```bash
streamlit run streamlit_app.py
```

Features:
- ✅ Drag-and-drop document upload
- ✅ Real-time progress tracking (5 phases)
- ✅ Visual metrics dashboard
- ✅ Interactive report display
- ✅ One-click Markdown download

### Command Line Interface

For batch processing or automation:

```bash
# Full analysis
python main.py

# Display current configuration
python main.py --show-config

# Quick keyword-based analysis (legacy)
python main.py --quick
```

**Output**: `output/competitiveness_report_YYYYMMDD_HHMMSS.md`

## 📊 Understanding Results

### Alignment Score

Measures how well your narrative addresses solicitation requirements:

- **≥80%**: Highly competitive - strong evidence for most requirements
- **60-79%**: Competitive - good coverage with some gaps
- **40-59%**: Moderately competitive - significant improvements needed
- **<40%**: Needs major revision

**Note**: The hybrid LLM verification significantly improves accuracy over pure semantic matching.

### Team Score (0-10)

Evaluates team composition and expertise fit:

- **8-10**: Exceptionally strong team with excellent fit
- **6-7**: Solid team with minor gaps
- **4-5**: Adequate but with notable weaknesses
- **<4**: Team composition needs strengthening

### Strong Alignments

Requirements with score ≥0.80, showing:
- Direct quote from your narrative
- Citation (paragraph number)
- Why it demonstrates strong alignment

### Areas of Concern

Missing or weak requirements, with:
- Quote from solicitation requirement
- Why it's critical for success
- Specific recommendation with example language

## 🔍 How It Works

### Phase 1: Smart Document Loading

```python
# Documents are chunked intelligently:
- Short paragraphs: Kept whole
- Long paragraphs (>512 chars): Split into semantic units
- Sliding window with overlap preserves context
- Result: 152 focused chunks vs 97 paragraph chunks (57% more granular)
```

### Phase 2: Dynamic Rubric Extraction

```python
# LLM analyzes solicitation to identify:
- Mandatory requirements (FAIR, stakeholder letters, AFRI priorities)
- Evaluation criteria with weights
- Program priorities (6 AFRI focus areas)
- Constraints (budget, duration, page limits)
```

### Phase 3: Hybrid Semantic + LLM Alignment Analysis

```python
# For each requirement:
1. Semantic search finds top 10 candidate chunks (FAISS)
2. LLM verifies which candidates actually address requirement
3. LLM extracts direct evidence quotes
4. Scores adjusted based on LLM confidence:
   - High confidence: 0.85+
   - Medium: 0.70+
   - Low: 0.60+
```

**Why Hybrid?**
- Semantic search alone: 10.2% alignment (misses FAIR, priorities)
- Hybrid with LLM: 32.6% alignment (accurate detection)
- Improvement: +22.4 percentage points!

### Phase 4: Team Expertise Evaluation

```python
# For each team member (e.g., Ekin, Dey, OChen, qasem):
1. Extract expertise from biosketch
2. Identify relevant publications
3. Assess current workload from CPS
4. Evaluate fit with proposal needs
5. Mention by name in report with specific contributions
```

### Phase 5: Comprehensive Report Generation

Synthesizes all analyses with:
- PI names and expertise throughout
- Direct quotes from both narrative and solicitation
- Specific, actionable recommendations
- Example language for addressing gaps

## 📈 Example Analysis Results

### Strong Alignments Detected

✅ **AFRI Priorities** (0.85)
> "This framework demonstrates a scalable pathway for deploying modular, explainable, and equitable AI systems in U.S. agriculture..."
> *Citation: ¶63*

✅ **FAIR Data Standards** (0.85)
> "In adherence to the FAIR principles, all data products, metadata, and models developed under this project will be documented..."
> *Citation: ¶58*

✅ **CARE Data Principles** (0.85)
> "In alignment with the CARE principles, the project will ensure that data collected from farmers remain under their ownership..."
> *Citation: ¶58*

### Team Analysis Example

**Team Strengths:**
- **Ekin**: Bayesian modeling & machine learning expertise
- **Dey**: Consumer behavior analysis & aquaculture economics
- **OChen**: Stakeholder engagement & participatory research
- **qasem**: High-performance computing

**Team Score**: 8.5/10 (Strong interdisciplinary coverage)

## 🛠️ Advanced Configuration

### Tuning Similarity Threshold

Lower threshold = more lenient matching:

```bash
# .env file
SEMANTIC_SIMILARITY_THRESHOLD=0.60  # Default
# Try 0.55 for more matches, 0.70 for stricter
```

### Adjusting Chunk Size

Smaller chunks = more focused embeddings:

```bash
CHUNK_SIZE=512   # Default (balanced)
CHUNK_OVERLAP=50 # Context preservation
# Try 400 for finer granularity, 600 for broader context
```

### Switching LLM Models

```bash
# OpenAI (recommended)
GROQ_ANALYSIS_MODEL=gpt-4o-mini          # Fast, accurate, cheap
GROQ_ANALYSIS_MODEL=gpt-4-turbo          # Most accurate

# Groq (faster, free tier available)
GROQ_ANALYSIS_MODEL=llama-3.3-70b-versatile  # Latest, most capable
GROQ_ANALYSIS_MODEL=llama-3.1-8b-instant     # Fastest
```

## 📚 Output Files

### Main Report

**`competitiveness_report_YYYYMMDD_HHMMSS.md`**

Comprehensive Markdown report with:
- **Executive Summary**: Overall rating + bottom-line recommendation
- **Strong Alignments**: Requirements well-addressed (with quotes + citations)
- **Areas of Concern**: Missing/weak requirements (with solicitation quotes)
- **Team Evaluation**: PI names, expertise, strengths, gaps
- **Critical Success Factors**: Top 5 must-address items
- **Prioritized Recommendations**: High/Medium/Low priority actions

### Intermediate Analyses

- `solicitation_rubric.json` - Extracted 8+ requirements with descriptions
- `alignment_analysis.json` - Semantic scores + LLM verification results
- `team_analysis.json` - Personnel profiles with expertise areas
- `document_chunks.json` - All 152+ parsed chunks with metadata
- `narrative.faiss` - FAISS index (reusable for fast re-analysis)

## 🎯 Best Practices

1. **Run Early & Often**: Use during drafting, not just before submission
2. **Iterate**: Analyze → address gaps → re-analyze → verify improvements
3. **Trust the LLM Verification**: It catches content that pure similarity misses
4. **Read the Evidence Quotes**: Verify the system found the right content
5. **Address High Priority First**: Focus on critical gaps before polishing
6. **Use PI Names**: Reports mention your team by name - share with confidence
7. **Export & Share**: Download Markdown reports for team review

## 🔧 Troubleshooting

### "No matches found for FAIR/stakeholder/priorities"

✅ **Solution**: The new hybrid LLM verification should detect these automatically. If still missing:
- Check your OpenAI API key is valid
- Verify narrative actually discusses these topics
- Try lowering `SEMANTIC_SIMILARITY_THRESHOLD` to 0.55

### "Alignment score seems too low"

The hybrid system is more accurate but may reveal true gaps:
- Review "Areas of Concern" for specific missing content
- Check if solicitation requirements are actually addressed
- Semantic-only gave 10.2%, hybrid gives 32.6% (more accurate)

### "Team analysis shows 0/10"

API issue - check:
- OpenAI API key is set correctly
- You have API credits remaining
- Model name is correct (`gpt-4o-mini` or `llama-3.3-70b-versatile`)

### Streamlit app not loading

```bash
# Kill existing processes
pkill -f streamlit

# Restart
streamlit run streamlit_app.py
```

## 📚 Technical Details

### Key Dependencies

- **openai**: LLM API for analysis and verification
- **sentence-transformers**: all-MiniLM-L6-v2 for embeddings (384-dim)
- **faiss-cpu**: Fast vector similarity search
- **PyMuPDF**: PDF text extraction
- **python-docx**: DOCX parsing
- **streamlit**: Web interface framework

### System Architecture

**Two-Stage Verification**:
1. **Semantic Stage**: FAISS retrieves top 10 candidates (fast)
2. **LLM Stage**: GPT-4o-mini verifies actual matches (accurate)

**Smart Chunking**:
- Sentence-level splitting with regex
- Sliding window (512 chars, 50 overlap)
- Preserves context across chunk boundaries
- Creates focused embeddings for better matching

### Performance

- Full CLI analysis: ~2-3 minutes
- Streamlit web analysis: ~2-3 minutes
- LLM verification: ~15-20 seconds per requirement
- FAISS index build: ~5 seconds for 152 chunks

## 🔒 Privacy & Security

- ✅ All analysis performed locally (except LLM API calls)
- ✅ Documents uploaded to Streamlit are processed in-session only
- ✅ No permanent storage of uploaded documents
- ✅ API keys stored in local `.env` file
- ✅ Output reports saved locally in `output/` directory

## 📝 Example Use Cases

### Use Case 1: Pre-Submission Check

"Is my proposal ready to submit?"

```bash
streamlit run streamlit_app.py
# Upload documents → Analyze → Check alignment score
# If <60%, address high-priority gaps before submitting
```

### Use Case 2: Iterative Improvement

"Track improvements across drafts"

```bash
# Draft 1
python main.py  # Score: 32.6%
# Address gaps...

# Draft 2
python main.py  # Score: 58.3%
# Continue improving...

# Final
python main.py  # Score: 78.1% ✅ Ready!
```

### Use Case 3: Team Review

"Share analysis with PIs"

```bash
# Generate report
python main.py

# Report mentions each PI by name with their expertise
# Share output/competitiveness_report_*.md with team
# PIs see: "Ekin's Bayesian modeling expertise is particularly relevant..."
```

## 🚀 Future Enhancements

- [x] Streamlit web interface
- [x] Hybrid semantic + LLM verification
- [x] Smart text chunking
- [x] OpenAI API support
- [x] PI name personalization
- [ ] Comparative analysis (version tracking)
- [ ] Budget analysis module
- [ ] Timeline/Gantt chart evaluation
- [ ] Export to PDF with charts
- [ ] Multi-solicitation support (NSF, NIH)
- [ ] Real-time collaborative editing

## 🤝 Contributing

Internal tool for DataAILab @ Texas State University.

For questions: Contact the CADS development team

## 📄 License

Internal use only - DataAILab @ Texas State University

## 🙏 Acknowledgments

- Built with CADS (Center for Analytics and Data Science) support
- Uses OpenAI GPT-4o-mini for LLM verification
- FAISS by Meta AI for vector search
- Sentence-Transformers by UKP Lab

---

## ✅ Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API key configured in `.env` file
- [ ] Documents uploaded to `data/` subdirectories
- [ ] Run `streamlit run streamlit_app.py` OR `python main.py`
- [ ] Review report in browser or `output/` directory

**Ready to analyze? Launch the web interface and get evidence-based feedback in minutes!** 🚀

---

## 📞 Support

For technical issues or questions:
- Check troubleshooting section above
- Review implementation guide: `/Users/quamos/Documents/Obsidian Vault/Agri/Implementation.md`
- Contact DataAILab development team

**Last Updated**: 2025-11-14
**Version**: 2.0.0 (Hybrid LLM Verification)
