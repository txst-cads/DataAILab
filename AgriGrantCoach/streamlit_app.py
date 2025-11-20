#!/usr/bin/env python3
"""
AgriGrantCoach-AFRI Streamlit Web Interface

A user-friendly web interface for analyzing USDA AFRI grant proposal competitiveness.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import Config
from src.data_loader import DataLoader
from src.rubric_analyzer import RubricAnalyzer
from src.semantic_analyzer import SemanticAnalyzer
from src.team_analyzer import TeamAnalyzer
from src.report_generator import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="AgriGrantCoach-AFRI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2e7d32;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #856404;
    }
    .danger-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'report_content' not in st.session_state:
        st.session_state.report_content = None
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None


def save_uploaded_file(uploaded_file, destination_dir):
    """Save an uploaded file to the destination directory."""
    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    file_path = destination_dir / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def clear_data_directory():
    """Clear the data directory before new analysis."""
    data_dir = Config.DATA_DIR
    if data_dir.exists():
        for subdir in ['solicitation', 'narrative', 'biosketches', 'cps']:
            subdir_path = data_dir / subdir
            if subdir_path.exists():
                shutil.rmtree(subdir_path)
            subdir_path.mkdir(parents=True, exist_ok=True)


def run_analysis(progress_bar, status_text):
    """Run the complete analysis pipeline with progress updates."""
    try:
        # Initialize components
        data_loader = DataLoader(Config)
        rubric_analyzer = RubricAnalyzer(Config)
        semantic_analyzer = SemanticAnalyzer(Config)
        team_analyzer = TeamAnalyzer(Config)
        report_generator = ReportGenerator(Config)

        # Phase 1: Data Loading (20%)
        status_text.text("📄 Phase 1/5: Loading documents...")
        progress_bar.progress(10)
        all_data = data_loader.load_all()
        progress_bar.progress(20)

        # Phase 2: Rubric Extraction (40%)
        status_text.text("🔍 Phase 2/5: Extracting evaluation rubric...")
        progress_bar.progress(25)
        rubric = rubric_analyzer.extract_rubric(all_data['solicitation']['text'])
        progress_bar.progress(40)

        # Phase 3: Semantic Alignment (60%)
        status_text.text("🎯 Phase 3/5: Analyzing proposal alignment...")
        progress_bar.progress(45)
        alignment_analysis = semantic_analyzer.analyze_proposal_alignment(
            rubric,
            all_data['narrative']['chunks']
        )
        progress_bar.progress(60)

        # Phase 4: Team Analysis (80%)
        status_text.text("👥 Phase 4/5: Evaluating team expertise...")
        progress_bar.progress(65)

        personnel_profiles = {}
        for name, personnel_data_dict in all_data['personnel'].items():
            from src.data_loader import PersonnelData
            personnel_data = PersonnelData(
                name=name,
                biosketch_text=personnel_data_dict['biosketch_text'],
                cps_text=personnel_data_dict['cps_text'],
                biosketch_chunks=personnel_data_dict['biosketch_chunks'],
                cps_chunks=personnel_data_dict['cps_chunks']
            )
            personnel_profiles[name] = team_analyzer.extract_pi_profile(
                name,
                personnel_data
            )

        team_analysis = team_analyzer.analyze_team_composition(
            personnel_profiles,
            rubric,
            all_data['narrative']['text']
        )
        progress_bar.progress(80)

        # Phase 5: Report Generation (100%)
        status_text.text("📝 Phase 5/5: Generating comprehensive report...")
        progress_bar.progress(85)

        metadata = {
            'analysis_date': datetime.now().isoformat(),
            'total_chunks_analyzed': all_data['metadata']['total_chunks'],
            'team_size': all_data['metadata']['team_size'],
            'alignment_score': alignment_analysis['overall_score'],
            'team_score': team_analysis['overall_score']
        }

        report = report_generator.generate_report(
            rubric=rubric,
            alignment_analysis=alignment_analysis,
            team_analysis=team_analysis,
            personnel_profiles=personnel_profiles,
            metadata=metadata
        )

        report_path = report_generator.save_report(report)
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")

        # Read the report
        with open(report_path, 'r') as f:
            report_content = f.read()

        return {
            'success': True,
            'report_content': report_content,
            'report_path': report_path,
            'alignment_score': alignment_analysis['overall_score'],
            'team_score': team_analysis['overall_score'],
            'requirements_count': len(rubric.get('requirements', [])),
            'strong_alignments': len(alignment_analysis.get('strong_alignments', [])),
            'gaps': len(alignment_analysis.get('gaps', [])),
            'team_size': all_data['metadata']['team_size']
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def display_report(report_content, results):
    """Display the analysis report in a formatted way."""

    # Display key metrics
    st.markdown("## 📊 Key Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        alignment_score = results['alignment_score']
        color = "🟢" if alignment_score >= 70 else "🟡" if alignment_score >= 40 else "🔴"
        st.metric(
            label="Alignment Score",
            value=f"{alignment_score:.1f}%",
            delta=None
        )
        st.markdown(f"{color} {'Highly Competitive' if alignment_score >= 70 else 'Needs Improvement' if alignment_score >= 40 else 'Major Revision Needed'}")

    with col2:
        team_score = results['team_score']
        color = "🟢" if team_score >= 8 else "🟡" if team_score >= 6 else "🔴"
        st.metric(
            label="Team Strength",
            value=f"{team_score:.1f}/10",
            delta=None
        )
        st.markdown(f"{color} {'Excellent' if team_score >= 8 else 'Good' if team_score >= 6 else 'Needs Strengthening'}")

    with col3:
        st.metric(
            label="Requirements Analyzed",
            value=results['requirements_count'],
            delta=None
        )
        st.metric(
            label="Strong Alignments",
            value=results['strong_alignments'],
            delta=None
        )

    with col4:
        st.metric(
            label="Team Size",
            value=results['team_size'],
            delta=None
        )
        st.metric(
            label="Identified Gaps",
            value=results['gaps'],
            delta=None
        )

    st.markdown("---")

    # Display the full report
    st.markdown("## 📄 Comprehensive Analysis Report")
    st.markdown(report_content)


def main():
    """Main application function."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🌾 AgriGrantCoach-AFRI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced AI-Powered Competitiveness Assessment for USDA AFRI Proposals</div>', unsafe_allow_html=True)

    # Sidebar for file uploads
    with st.sidebar:
        st.header("📁 Document Upload")
        st.markdown("Upload your grant proposal documents below:")

        # Solicitation upload
        st.subheader("1. Solicitation")
        solicitation_file = st.file_uploader(
            "Upload USDA AFRI Solicitation (PDF)",
            type=['pdf'],
            key='solicitation',
            help="Upload the USDA AFRI program solicitation PDF"
        )

        # Narrative upload
        st.subheader("2. Project Narrative")
        narrative_file = st.file_uploader(
            "Upload Project Narrative (DOCX)",
            type=['docx'],
            key='narrative',
            help="Upload your project narrative document"
        )

        # Biosketches upload
        st.subheader("3. Biosketches")
        biosketch_files = st.file_uploader(
            "Upload Team Biosketches (DOCX)",
            type=['docx'],
            key='biosketches',
            accept_multiple_files=True,
            help="Upload biographical sketches for all team members"
        )

        # Current & Pending Support upload
        st.subheader("4. Current & Pending Support")
        cps_files = st.file_uploader(
            "Upload Current & Pending Support (DOCX)",
            type=['docx'],
            key='cps',
            accept_multiple_files=True,
            help="Upload current and pending support documents"
        )

        st.markdown("---")

        # Analyze button
        analyze_button = st.button(
            "🚀 Analyze Proposal",
            type="primary",
            use_container_width=True,
            disabled=not (solicitation_file and narrative_file and biosketch_files and cps_files)
        )

        if not (solicitation_file and narrative_file and biosketch_files and cps_files):
            st.warning("⚠️ Please upload all required documents to enable analysis")

    # Main content area
    if analyze_button:
        st.session_state.analysis_complete = False

        # Clear previous data
        clear_data_directory()

        # Save uploaded files
        with st.spinner("Uploading files..."):
            try:
                # Save solicitation
                save_uploaded_file(solicitation_file, Config.SOLICITATION_DIR)

                # Save narrative
                save_uploaded_file(narrative_file, Config.NARRATIVE_DIR)

                # Save biosketches
                for bio_file in biosketch_files:
                    save_uploaded_file(bio_file, Config.BIOSKETCHES_DIR)

                # Save CPS files
                for cps_file in cps_files:
                    save_uploaded_file(cps_file, Config.CPS_DIR)

                st.success("✅ All files uploaded successfully!")
            except Exception as e:
                st.error(f"❌ Error uploading files: {e}")
                return

        # Run analysis
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = run_analysis(progress_bar, status_text)

        if results['success']:
            st.session_state.analysis_complete = True
            st.session_state.report_content = results['report_content']
            st.session_state.report_path = results['report_path']
            st.session_state.analysis_results = results

            st.balloons()
            st.success("🎉 Analysis completed successfully!")
        else:
            st.error(f"❌ Analysis failed: {results['error']}")
            st.exception(results['error'])

    # Display results if analysis is complete
    if st.session_state.analysis_complete:
        # Download button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="📥 Download Report (Markdown)",
                data=st.session_state.report_content,
                file_name=f"competitiveness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
                type="primary"
            )

        st.markdown("---")

        # Display the report
        display_report(st.session_state.report_content, st.session_state.analysis_results)

    else:
        # Welcome message when no analysis has been run
        st.markdown("""
        ## Welcome to AgriGrantCoach-AFRI! 👋

        This tool provides **comprehensive, AI-powered assessment** of your USDA AFRI grant proposal competitiveness.

        ### 🎯 What We Analyze

        1. **Solicitation Alignment** - How well does your proposal match the program requirements?
        2. **Team Expertise** - Does your team have the right skills and experience?
        3. **Proposal Strengths** - What are your competitive advantages?
        4. **Critical Gaps** - What must be addressed before submission?
        5. **Actionable Recommendations** - Specific steps to improve your proposal

        ### 📋 Required Documents

        To get started, upload the following documents in the sidebar:

        - ✅ **USDA AFRI Solicitation** (PDF) - The program announcement
        - ✅ **Project Narrative** (DOCX) - Your proposal narrative
        - ✅ **Biosketches** (DOCX) - NSF-style biographical sketches for all PIs/Co-PIs
        - ✅ **Current & Pending Support** (DOCX) - For all team members

        ### ⚡ Quick Start

        1. Upload all required documents using the sidebar
        2. Click the **"Analyze Proposal"** button
        3. Wait for the analysis to complete (~1-2 minutes)
        4. Review your comprehensive competitiveness report
        5. Download the report for your records

        ---

        ### 🔒 Privacy & Security

        - All analysis is performed locally
        - Documents are processed in temporary directories
        - No data is stored permanently without your permission

        ### 💡 Tips for Best Results

        - Ensure all documents are complete and final versions
        - Use the latest version of the solicitation
        - Include all team members' biosketches and CPS documents

        ---

        **Ready to assess your proposal? Upload your documents in the sidebar to begin!**
        """)

        # Show example metrics
        st.markdown("### 📊 Sample Analysis Output")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("**Alignment Score**\n\nMeasures how well your proposal addresses solicitation requirements (0-100%)")

        with col2:
            st.info("**Team Strength**\n\nEvaluates your team's expertise and qualifications (0-10 scale)")

        with col3:
            st.info("**Gap Analysis**\n\nIdentifies missing requirements and areas for improvement")


if __name__ == "__main__":
    main()
