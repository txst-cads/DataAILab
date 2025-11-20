# AgriGrantCoach-AFRI Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Setup Environment (2 min)

```bash
cd AgriGrantCoach
./setup.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Verify Configuration (1 min)

```bash
python main.py --show-config
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║           AgriGrantCoach Configuration                       ║
╠══════════════════════════════════════════════════════════════╣
║ API Keys:
║   - Groq API Key: ✓ Set
║   - OpenAlex Email: xcm15@txstate.edu
...
```

### Step 3: Run Analysis (2 min)

```bash
python main.py
```

**This will:**
1. ✅ Load 12 documents (1 solicitation, 1 narrative, 5 bios, 5 CPS)
2. ✅ Extract evaluation rubric from solicitation
3. ✅ Analyze alignment using FAISS semantic search
4. ✅ Evaluate team expertise
5. ✅ Generate comprehensive report

## 📊 Understanding Your Results

### Output Location
```
output/
├── competitiveness_report_20241113_HHMMSS.md  ← Main report (READ THIS!)
├── solicitation_rubric.json                   ← Extracted requirements
├── alignment_analysis.json                    ← Semantic matches
├── team_analysis.json                         ← Team evaluation
└── document_chunks.json                       ← Parsed documents
```

### Competitiveness Ratings

**Highly Competitive** (Alignment ≥80%, Team ≥8/10)
- ✅ Strong evidence for most requirements
- ✅ Excellent team fit
- ✅ Minor refinements needed

**Competitive** (Alignment 60-79%, Team 6-7/10)
- ⚠️ Good coverage with some gaps
- ⚠️ Solid team with minor weaknesses
- 🔧 Address medium-priority recommendations

**Moderately Competitive** (Alignment 40-59%, Team 4-5/10)
- ⚠️ Significant gaps in coverage
- ⚠️ Team has notable weaknesses
- 🔧 Major revisions needed

**Needs Significant Revision** (Alignment <40%, Team <4/10)
- ❌ Missing critical requirements
- ❌ Insufficient team qualifications
- 🔧 Substantial rework required

## 🎯 What to Do Next

### If Highly Competitive
1. Review high-priority recommendations
2. Strengthen any weak alignments
3. Polish and refine

### If Competitive
1. Address all high-priority recommendations
2. Fill identified gaps in narrative
3. Consider adding missing expertise to team
4. Re-run analysis to verify improvements

### If Moderately Competitive or Below
1. Focus on critical gaps (High priority items)
2. Consider significant restructuring
3. May need to add team members
4. Schedule multiple revision cycles
5. Re-run analysis after each major revision

## 🔄 Iterative Improvement Workflow

```
1. Run Analysis
   ↓
2. Review Report
   ↓
3. Address High Priority Items
   ↓
4. Update Documents
   ↓
5. Re-run Analysis ← [Repeat until Highly Competitive]
   ↓
6. Submit!
```

## 💡 Pro Tips

1. **Run Early**: Use this during drafting, not just before deadline
2. **Track Progress**: Compare alignment scores across versions
3. **Check Citations**: Verify evidence actually supports claims
4. **Focus on Gaps**: Missing high-priority requirements kill proposals
5. **Use JSON Files**: Deep dive into `alignment_analysis.json` for details

## 🆘 Common Issues

### Low Alignment Despite Good Proposal
- May be using different terminology than solicitation
- Try adding exact phrases from solicitation
- Check `solicitation_rubric.json` for expected keywords

### Missing Personnel
- Ensure filenames contain PI names (case-insensitive)
- Check files are DOCX, not PDF
- Verify files are in correct subdirectories

### "GROQ_API_KEY not set"
- Check `.env` file in parent directory (`../env`)
- Ensure no quotes around the key
- Verify key is valid

## 📞 Need Help?

1. Check `README.md` for detailed documentation
2. Review intermediate JSON files for insights
3. Run individual modules for testing:
   ```bash
   cd src
   python data_loader.py
   python rubric_analyzer.py
   ```

---

**Ready to get started?**

```bash
cd AgriGrantCoach
source venv/bin/activate
python main.py
```

**Your comprehensive analysis will be ready in ~3-5 minutes!** ⚡
