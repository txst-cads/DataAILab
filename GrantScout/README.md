# GrantScout: AI-Powered Grant Proposal Coach

**Version 2.1** - Workflow-Optimized Edition
**Last Updated:** December 11, 2025

---

## Overview

GrantScout is an AI-powered grant proposal evaluation and coaching tool that provides evidence-based feedback on narrative quality, team expertise utilization, and competitive positioning.

### Key Features

- **OCR-Enabled Document Processing:** Automatically extracts text from embedded table images in DOCX files
- **Forensic Evidence Extraction:** Identifies exact metrics, data points, and entities in your proposal
- **Evidence-Based Coaching:** Provides actionable recommendations based on what actually exists in your narrative
- **Team Expertise Analysis:** Maps team member credentials to proposal requirements
- **Cost-Effective:** <$0.75 per complete analysis using GPT-4o-mini with selective GPT-4o validation

---

## Quick Start

### 1. Installation

```bash
# Install Tesseract OCR (required for table extraction)
brew install tesseract  # macOS
# OR
sudo apt-get install tesseract-ocr  # Ubuntu/Debian

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file:
```bash
OPENAI_API_KEY=your_api_key_here
```

### 3. Run the App

```bash
streamlit run main.py
```

Navigate to http://localhost:8501 in your browser.

---

## How to Use

### Step 1: Upload Documents

- **Funding Opportunity:** Upload the grant solicitation (DOCX or PDF)
- **Your Narrative:** Upload your grant proposal narrative (DOCX preferred for table extraction)
- **Team CVs (Optional):** Upload team member CVs for expertise analysis

### Step 2: Run Analysis

Click "Run Evaluation" and wait for the analysis to complete (typically 30-60 seconds).

### Step 3: Review Report

The report includes:
- **Executive Dashboard:** Win probability and overall assessment
- **Deep-Dive Criterion Analysis:** Evidence-based coaching for each criterion
- **Team Alignment Matrix:** Which team members align with which requirements
- **Prioritized Action Plan:** Top recommendations ranked by impact

---

## What's New in Version 2.1

### Three Critical Workflow Improvements:

**1. Enhanced Retrieval**
- "Table Hunter" aggressively finds table content (1.5× score boost)
- "Proper Noun Hunter" extracts capitalized entities from criteria
- Retrieves 30-50 pieces of evidence (vs 8-10 previously)

**2. Forensic Evidence Extraction**
- Zero-temperature extraction for accuracy
- Structured output: metrics, entities, team references, table detection
- Finds what EXISTS (not what's missing)

**3. Negative Constraints in Coaching**
- Prevents budget/financial requests
- Prevents duplicate recommendations
- Prevents generic advice when data exists
- Baseline score ≥6 when content exists

### Result:
- ✅ No more false negatives (claiming metrics are missing when they exist)
- ✅ No more generic fallback advice
- ✅ Evidence-based coaching only
- ✅ 87.5% verification test pass rate

---

## Project Structure

```
GrantScout/
├── main.py                      # Streamlit web application
├── requirements.txt             # Python dependencies
├── .env                         # API keys (create this)
├── src/
│   ├── ingester.py             # Document parsing with OCR
│   ├── evaluator.py            # Evaluation engine (workflow-optimized)
│   └── reporter.py             # Report generation
├── temp_uploads/               # Uploaded files
├── data/                       # Generated reports
├── test_extraction.py          # Diagnostic test
├── test_workflow_fix.py        # Workflow verification
├── verify_ocr_fix.py           # OCR verification
├── INSTALLATION.md             # Detailed setup guide
└── WORKFLOW_FIX_SUMMARY.md     # Technical documentation
```

---

## Testing & Verification

### Test OCR Extraction
```bash
python verify_ocr_fix.py
```
Verifies that tables, metrics, and prior work examples are being extracted.

### Test Workflow Improvements
```bash
python test_workflow_fix.py
```
Verifies Table Hunter, Forensic Extraction, and Negative Constraints are working.

### Test Pass 1 & Pass 2
```bash
python test_extraction.py
```
Shows exactly what evidence is being found and what gaps are identified.

---

## Troubleshooting

### OCR Not Working?

**Check Tesseract:**
```bash
tesseract --version
```

**Install if missing:**
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt-get install tesseract-ocr`
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

### Low Score Despite Strong Content?

Run the workflow verification:
```bash
python test_workflow_fix.py
```

Check if retrieval is finding your content. If <30 evidence chunks, there may be a retrieval issue.

### Generic Recommendations?

This indicates retrieval failure. The tool falls back to generic advice when it can't find relevant evidence. Solutions:
1. Ensure DOCX format (better OCR quality than PDF)
2. Check that embedded images are clear (300+ DPI)
3. Run `test_extraction.py` to see what's being retrieved

---

## Best Practices

### For Best Results:

1. **Use DOCX Format**
   - Better OCR quality for embedded images
   - More reliable table extraction

2. **Use Native Tables When Possible**
   - Insert → Table in Word (not screenshots)
   - More accurate parsing

3. **Clear Image Quality**
   - 300+ DPI for embedded images
   - 11pt+ font size
   - Avoid handwritten content

4. **Upload Team CVs**
   - Enables team expertise analysis
   - Provides specific coaching on leveraging credentials

---

## Technical Details

### Evaluation Pipeline:

**Pass 1: Forensic Evidence Extraction**
- Model: GPT-4o-mini
- Temperature: 0.0 (extraction accuracy)
- Output: Structured metrics, entities, team refs, table detection
- Cost: ~$0.003

**Pass 2: Evidence-Based Coaching**
- Model: GPT-4o-mini
- Temperature: 0.2
- Input: Forensic findings from Pass 1
- Constraints: No budget, no duplicates, no generic advice
- Cost: ~$0.003

**Pass 3: Expert Validation (Selective)**
- Model: GPT-4o
- Triggered: Only if score <7 or many recommendations
- Output: Refined, high-impact coaching
- Cost: ~$0.03 (when triggered)

**Total Cost:** <$0.20 for 5 criteria analysis

### Retrieval Strategies:

1. Broad Context Search
2. **Table Hunter** (1.5× boost for table content)
3. **Proper Noun Hunter** (1.2× boost for entities)
4. Data & Statistics Search (1.2× boost)
5. Team/Personnel Search
6. Prior Work Search (1.3× boost)
7. Partnership Search
8. Keyword Search

Returns top k×5 pieces of evidence (50 chunks for k=10).

---

## Support & Documentation

- **Setup Guide:** See `INSTALLATION.md`
- **Technical Details:** See `WORKFLOW_FIX_SUMMARY.md`
- **Issues:** Check troubleshooting section above

---

## Version History

**v2.1 (Dec 11, 2025)** - Workflow-Optimized Edition
- Added Table Hunter & Proper Noun Hunter to retrieval
- Implemented Forensic Evidence Extraction (zero-temp)
- Added Negative Constraints to prevent hallucinations
- 87.5% verification test pass rate

**v2.0 (Dec 11, 2025)** - OCR-Enabled Edition
- Added OCR for embedded DOCX images
- Native DOCX table support
- Extracted 13,190 characters from 13 table images

**v1.0 (Nov 22, 2025)** - Initial Release
- Basic RAG-based evaluation
- Team expertise analysis
- Markdown report generation

---

## License

Proprietary - Texas State University, CADS Department

---

**Ready to use!** Run `streamlit run main.py` to get started.
