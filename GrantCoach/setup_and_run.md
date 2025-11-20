# GrantCoach Streamlit Interface - Setup and Running Guide

## 🚀 Quick Start

This guide will help you set up and run the GrantCoach Streamlit interface for your demo.

## 📋 Prerequisites

### System Requirements
- Python 3.8 or higher
- macOS/Linux/Windows
- At least 4GB RAM (8GB recommended)
- Internet connection for API calls

### Required Files
Make sure you have these files in the `data/` directory:
- `ExpandAI_Solicitation.pdf` - Solicitation document
- `TXST_NSFExpandAI_2334268 Project Description.pdf` - Project description

## 🔧 Setup Instructions

### 1. Install Dependencies

Open a terminal in the GrantCoach directory and run:

```bash
# Install all required packages
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Create environment file
touch .env
```

Add your GROQ API key to the `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_MAX_TOKENS=2000
GROQ_TEMPERATURE=0.3
```

### 3. Download NLP Models

The system requires spaCy and sentence transformer models:

```bash
# Download spaCy model
python -m spacy download en_core_web_sm

# Download sentence transformer models (will download automatically on first run)
```

## 🎯 Running the Application

### Method 1: Direct Run (Recommended for Demo)

```bash
# Navigate to the GrantCoach directory
cd /Users/quamos/Desktop/CADS/DataAILab/GrantCoach

# Run the Streamlit app
streamlit run streamlit_app.py
```

### Method 2: Python Run

```bash
# Run with Python
python streamlit_app.py
```

## 🌐 Using the Interface

### 1. Demo Mode (For Your Manager Demo)

1. Open the web interface (usually http://localhost:8501)
2. Click the "🔧 Demo Mode" button in the sidebar
3. Click "🎯 Use Sample Files"
4. Click "🚀 Run Demo Analysis"
5. Wait for processing (takes 30-60 seconds)
6. Review the comprehensive results

### 2. Custom Upload Mode

1. Upload your own solicitation PDF
2. Upload your own project description PDF
3. Click "🚀 Start Analysis"
4. Wait for processing
5. Review results and download reports

## 📊 Interface Features

### Main Dashboard
- **Executive Summary**: Overall score and competitive position
- **Research Team Analysis**: Team member verification and expertise
- **Requirement Analysis**: Solicitation requirement matching
- **Strengths & Weaknesses**: Proposal assessment
- **Scoring Breakdown**: Detailed scoring methodology

### Key Features
- **Real-time Progress**: Shows analysis steps
- **Tabbed Interface**: Organized results display
- **Download Reports**: Markdown and JSON formats
- **Mobile Responsive**: Works on all devices
- **Error Handling**: User-friendly error messages

## 🔍 Demo Results

When running with the sample files, you should see:

### Expected Scores
- **Overall Score**: ~0.81/1.0
- **Competitive Position**: "Strong Competitive Position"
- **Alignment Score**: ~75%
- **Verified Researchers**: 5/5 team members

### Key Insights
- Strong AI capacity building alignment
- Excellent educational impact
- Solid research infrastructure
- Interdisciplinary collaboration strengths

## 🚨 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Model Download Issues**
   ```bash
   python -c "import spacy; spacy.load('en_core_web_sm')"
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

3. **API Key Issues**
   - Verify GROQ_API_KEY in .env file
   - Check API key validity at https://console.groq.com/

4. **Memory Issues**
   - Close other applications
   - Increase system memory if possible

5. **File Not Found Errors**
   - Verify sample files exist in `data/` directory
   - Check file permissions

### Performance Tips
- Run on a machine with good internet connection
- Ensure sufficient RAM (8GB+ recommended)
- First run may be slower due to model downloads

## 📱 Demo Preparation

### For Your Manager Demo

1. **Pre-test the Demo**
   ```bash
   # Run the demo once before your meeting
   streamlit run streamlit_app.py
   # Click demo mode and run analysis
   ```

2. **Demo Talking Points**
   - "GrantCoach uses AI to analyze proposals against solicitations"
   - "It verifies researcher expertise through OpenAlex"
   - "Provides comprehensive scoring and recommendations"
   - "Generates professional reports for download"

3. **Demo Flow**
   - Show the clean interface
   - Activate demo mode
   - Run analysis (explain the progress steps)
   - Showcase the comprehensive results
   - Demonstrate report download
   - Highlight key insights and recommendations

## 🎯 Success Metrics

A successful demo should show:
- ✅ Clean, professional interface
- ✅ Smooth processing with progress indicators
- ✅ Comprehensive analysis results
- ✅ Professional report generation
- ✅ Clear actionable insights

## 📞 Support

If you encounter any issues during setup or demo:

1. Check the troubleshooting section above
2. Verify all files are in the correct locations
3. Ensure all dependencies are properly installed
4. Check internet connection for API calls

---

**Good luck with your demo!** 🚀