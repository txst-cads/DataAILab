"""
GrantCoach Streamlit Interface
A user-friendly web interface for grant proposal analysis
"""

import streamlit as st
import os
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the parent directory to the path to import GrantCoach modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_grant_coach import ComprehensiveGrantCoach

# Set page config
st.set_page_config(
    page_title="GrantCoach - Grant Proposal Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    .progress-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .section-title {
        color: #2a5298;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

def create_header():
    """Create the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🎯 GrantCoach</h1>
        <p><em>AI-Powered Grant Proposal Analysis System</em></p>
        <p>Upload your solicitation and project description for comprehensive analysis</p>
    </div>
    """, unsafe_allow_html=True)

def create_upload_section():
    """Create file upload section"""
    st.markdown("""
    <div class="upload-section">
        <h2>📁 Upload Documents</h2>
        <p>Please upload the solicitation document and project description PDFs for analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        solicitation_file = st.file_uploader(
            "📄 Solicitation Document",
            type=['pdf'],
            key="solicitation",
            help="Upload the solicitation/RFP document"
        )

    with col2:
        proposal_file = st.file_uploader(
            "📝 Project Description",
            type=['pdf'],
            key="proposal",
            help="Upload the project proposal description"
        )

    return solicitation_file, proposal_file

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary location"""
    if uploaded_file is None:
        return None

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

def show_progress_progress():
    """Show processing progress"""
    st.markdown("""
    <div class="progress-container">
        <h3>🔄 Processing Your Documents</h3>
        <p>Please wait while we analyze your grant proposal...</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    steps = [
        "Extracting text from PDFs...",
        "Analyzing research team...",
        "Processing AI-powered analysis...",
        "Building semantic index...",
        "Calculating alignment scores...",
        "Generating comprehensive report...",
        "Finalizing results..."
    ]

    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)
        progress_bar.progress(progress)
        status_text.text(f"Step {i+1}/{len(steps)}: {step}")
        time.sleep(1)  # Simulate processing time

    progress_bar.progress(1.0)
    status_text.text("✅ Analysis Complete!")

    time.sleep(1)
    return True

def display_results(report: Dict[str, Any]):
    """Display analysis results"""
    if not report:
        st.error("No analysis results available")
        return

    scores = report['scores']

    # Executive Summary
    st.markdown('<div class="section-title">📊 Executive Summary</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Overall Score</h3>
            <h2>{scores['overall_score']}/1.0</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Competitive Position</h3>
            <h4>{scores['competitive_assessment']}</h4>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Alignment Score</h3>
            <h2>{scores['alignment_percentage']}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        verified_count = len([r for r in report['researchers'] if r['found_in_openalex']])
        st.markdown(f"""
        <div class="metric-card">
            <h3>Verified Researchers</h3>
            <h2>{verified_count}/{len(report['researchers'])}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Tabbed interface for detailed results
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Research Team", "🎯 Requirements", "💡 Insights", "📈 Scoring"])

    with tab1:
        display_research_team_analysis(report)

    with tab2:
        display_requirement_analysis(report)

    with tab3:
        display_strengths_weaknesses(report)

    with tab4:
        display_scoring_breakdown(report)

def display_research_team_analysis(report: Dict[str, Any]):
    """Display research team analysis"""
    st.subheader("👥 Research Team Analysis")

    for researcher in report['researchers']:
        with st.expander(f"{researcher['name']} ({researcher['role']})"):
            col1, col2 = st.columns(2)

            with col1:
                verification_status = "✅ Verified" if researcher['found_in_openalex'] else "⚠️ Not found"
                st.write(f"**Department:** {researcher['department']}")
                st.write(f"**Status:** {verification_status}")

            with col2:
                if researcher['found_in_openalex']:
                    publications = researcher['profile']['works_count'] if researcher['profile'] else 0
                    citations = researcher['profile']['cited_by_count'] if researcher['profile'] else 0
                    st.write(f"**Publications:** {publications}")
                    st.write(f"**Citations:** {citations}")
                    st.write(f"**Alignment:** {researcher['alignment_score']:.2f}")
                else:
                    st.write("No profile data available")

def display_requirement_analysis(report: Dict[str, Any]):
    """Display requirement analysis"""
    st.subheader("🎯 Requirement Analysis")

    # Strong matches
    strong_matches = [m for m in report['requirement_matches'] if m['match_strength'] >= 0.5]
    if strong_matches:
        st.markdown("### ✅ Strong Matches")
        for match in strong_matches:
            st.metric(
                label=match['requirement'],
                value=f"{match['match_strength']:.0%}",
                delta=None
            )
            with st.expander("View Details"):
                st.write(f"**Evidence:** {match['evidence']}")
                if match.get('supporting_researchers'):
                    st.write("**Supporting Researchers:**")
                    for researcher in match['supporting_researchers']:
                        st.write(f"- {researcher['name']} ({researcher['role']})")

    # Weak matches
    weak_matches = [m for m in report['requirement_matches'] if m['match_strength'] < 0.5]
    if weak_matches:
        st.markdown("### ⚠️ Areas Needing Attention")
        for match in weak_matches:
            st.metric(
                label=match['requirement'],
                value=f"{match['match_strength']:.0%}",
                delta=None
            )
            with st.expander("View Details"):
                st.write(f"**Evidence:** {match['evidence']}")

def display_strengths_weaknesses(report: Dict[str, Any]):
    """Display strengths, weaknesses, and recommendations"""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💪 Strengths")
        for strength in report['strengths']:
            st.markdown(f"- {strength}")

    with col2:
        st.subheader("⚠️ Areas for Improvement")
        for weakness in report['weaknesses']:
            st.markdown(f"- {weakness}")

    st.subheader("🎯 Recommendations")
    for i, rec in enumerate(report['recommendations'][:10], 1):
        priority = "🔥" if i <= 3 else "📋"
        st.markdown(f"{priority} **{i}. {rec}**")

def display_scoring_breakdown(report: Dict[str, Any]):
    """Display detailed scoring breakdown"""
    st.subheader("📈 Scoring Breakdown")

    scores = report['scores']

    # Create a simple breakdown
    st.markdown("### 🎯 Scoring Components")
    st.metric("Requirement Alignment (50%)", f"{scores['requirement_alignment_score']:.2f}")
    st.metric("Team Strength (30%)", f"{scores['team_strength_score']:.2f}")
    st.metric("Expertise Quality (20%)", f"{scores['expertise_quality_score']:.2f}")

    # AI Analysis if available
    if 'ai_analysis' in report:
        st.subheader("🤖 AI Analysis Insights")
        ai_insights = report['ai_analysis']['ai_insights']

        col1, col2 = st.columns(2)
        with col1:
            st.metric("LLM Confidence", f"{ai_insights['llm_confidence']:.2f}")
        with col2:
            st.metric("Semantic Confidence", f"{ai_insights['semantic_confidence']:.2f}")

        if ai_insights['ai_consensus']:
            st.markdown("✅ **AI Consensus:** Strong agreement between LLM and semantic analysis")
        else:
            st.markdown("⚠️ **AI Consensus:** Limited agreement between analysis methods")

def create_download_section(report: Dict[str, Any]):
    """Create download section for the report"""
    st.markdown("""
    <div class="section-title">📥 Download Report</div>
    """, unsafe_allow_html=True)

    # Generate markdown content
    markdown_content = generate_markdown_report(report)

    # Create download button
    st.download_button(
        label="📄 Download Markdown Report",
        data=markdown_content,
        file_name="grant_coach_report.md",
        mime="text/markdown"
    )

    # Also provide JSON download
    json_content = json.dumps(report, indent=2, default=str)
    st.download_button(
        label="💾 Download JSON Data",
        data=json_content,
        file_name="grant_coach_analysis.json",
        mime="application/json"
    )

def generate_markdown_report(report: Dict[str, Any]) -> str:
    """Generate markdown report from analysis data"""
    scores = report['scores']
    researchers = report['researchers']
    verified_count = len([r for r in researchers if r['found_in_openalex']])

    markdown = f"""# 🎯 COMPREHENSIVE GRANT COACH ANALYSIS
**Generated**: {report['analysis_timestamp']}

## 📊 EXECUTIVE SUMMARY
**Overall Score**: {scores['overall_score']}/1.0
**Competitive Position**: {scores['competitive_assessment']}
**Alignment Score**: {scores['alignment_percentage']}%
**Verified Researchers**: {verified_count}/{len(researchers)}

## 👥 RESEARCH TEAM ANALYSIS

**Verified Researchers**: {verified_count}/{len(researchers)}

### 🏆 Leadership Team
"""

    # Add researchers
    for researcher in researchers:
        verification_status = "✅ Verified" if researcher['found_in_openalex'] else "⚠️ Not found"
        publications = researcher['profile']['works_count'] if researcher['profile'] else 0
        citations = researcher['profile']['cited_by_count'] if researcher['profile'] else 0

        markdown += f"\n{verification_status} **{researcher['name']}** ({researcher['role']})\n"
        markdown += f"- Department: {researcher['department']}\n"
        markdown += f"- Publications: {publications} ({citations} citations)\n"
        if researcher['found_in_openalex']:
            markdown += f"- Expertise: {', '.join(researcher['expertise_keywords'][:5])}\n"

    # Add requirement analysis
    markdown += "\n## 🎯 REQUIREMENT ANALYSIS\n\n"
    markdown += "### ✅ Strong Matches\n" if any(m['match_strength'] >= 0.5 for m in report['requirement_matches']) else "### ✅ Strong Matches\nNone found\n"

    for match in report['requirement_matches']:
        if match['match_strength'] >= 0.5:
            markdown += f"**{match['requirement']}** - Match Strength: {match['match_strength']:.0%}\n"
            markdown += f"- Evidence: {match['evidence']}\n\n"

    markdown += "### ⚠️ Weak Matches\n"
    for match in report['requirement_matches']:
        if match['match_strength'] < 0.5:
            markdown += f"**{match['requirement']}** - Match Strength: {match['match_strength']:.0%}\n"
            markdown += f"- Evidence: {match['evidence']}\n\n"

    # Add strengths and weaknesses
    markdown += "\n## 💪 STRENGTHS AND WEAKNESSES\n\n"

    markdown += "### ✅ Proposal Strengths\n"
    for strength in report['strengths']:
        markdown += f"- {strength}\n"

    markdown += "\n### ⚠️ Areas for Improvement\n"
    for weakness in report['weaknesses']:
        markdown += f"- {weakness}\n"

    # Add recommendations
    markdown += "\n## 🎯 COACHING RECOMMENDATIONS\n\n"

    for i, rec in enumerate(report['recommendations'][:10], 1):
        priority = "🔥" if i <= 3 else "📋"
        markdown += f"{priority} **{i}. {rec}**\n"

    # Add scoring breakdown
    markdown += "\n## 🏆 COMPETITIVE ASSESSMENT\n\n"

    markdown += "### 📈 Scoring Breakdown\n"
    markdown += "```\n"
    markdown += f"Overall Score (1.0):      {scores['overall_score']}\n"
    markdown += f"├─ Requirement Alignment (50%):  {scores['requirement_alignment_score']}\n"
    markdown += f"├─ Team Strength (30%):       {scores['team_strength_score']}\n"
    markdown += f"└─ Expertise Quality (20%):    {scores['expertise_quality_score']}\n"
    markdown += "```\n"

    markdown += "\n### 🎯 Key Success Factors\n"
    markdown += f"- **Team Verification**: {verified_count} researchers with OpenAlex profiles\n"
    markdown += f"- **Alignment Quality**: {scores['alignment_percentage']}% match with solicitation\n"
    markdown += f"- **Capability Coverage**: {len(report['proposal_capabilities'])} proposed initiatives\n"

    return markdown

def main():
    """Main application logic"""
    create_header()

    # Check for demo mode
    if 'demo_mode' not in st.session_state:
        st.session_state['demo_mode'] = False

    # Create upload section
    solicitation_file, proposal_file = create_upload_section()

    # Process button
    if st.button("🚀 Start Analysis", type="primary", disabled=not (solicitation_file and proposal_file and not st.session_state['demo_mode'])):
        if solicitation_file and proposal_file:
            # Save uploaded files
            with st.spinner("Saving uploaded files..."):
                solicitation_path = save_uploaded_file(solicitation_file)
                proposal_path = save_uploaded_file(proposal_file)

            try:
                # Show progress
                show_progress_progress()

                # Run analysis
                with st.spinner("Running comprehensive analysis..."):
                    coach = ComprehensiveGrantCoach()
                    report = coach.analyze_grant_proposal(solicitation_path, proposal_path)

                # Display results
                st.success("✅ Analysis Complete!")
                display_results(report)

                # Create download section
                create_download_section(report)

                # Clean up temporary files
                try:
                    os.unlink(solicitation_path)
                    os.unlink(proposal_path)
                except:
                    pass

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.error("Please check your files and try again.")
        else:
            st.warning("⚠️ Please upload both files before starting analysis.")

    # Demo mode functionality
    if st.session_state['demo_mode']:
        st.markdown("""
        <div class="success-message">
            <h3>🎯 Demo Mode Active</h3>
            <p>Using sample files: ExpandAI_Solicitation.pdf and TXST_NSFExpandAI_2334268 Project Description.pdf</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Run Demo Analysis", type="primary"):
            # Use sample files
            sample_solicitation = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
            sample_proposal = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/TXST_NSFExpandAI_2334268 Project Description.pdf"

            if os.path.exists(sample_solicitation) and os.path.exists(sample_proposal):
                try:
                    # Show progress
                    show_progress_progress()

                    # Run analysis with sample files
                    with st.spinner("Running demo analysis..."):
                        coach = ComprehensiveGrantCoach()
                        report = coach.analyze_grant_proposal(sample_solicitation, sample_proposal)

                    # Display results
                    st.success("✅ Demo Analysis Complete!")
                    display_results(report)

                    # Create download section
                    create_download_section(report)

                    # Clear demo mode
                    st.session_state['demo_mode'] = False

                except Exception as e:
                    st.error(f"❌ Error during demo analysis: {str(e)}")
            else:
                st.error("❌ Sample files not found. Please check the file paths.")

    # Sample data section for demo
    with st.sidebar:
        st.header("🔧 Demo Mode")
        st.markdown("---")

        if st.button("🎯 Use Sample Files"):
            st.session_state['demo_mode'] = True
            st.success("Demo mode activated! Using sample files for analysis.")

        st.markdown("---")
        st.subheader("ℹ️ About GrantCoach")
        st.markdown("""
        GrantCoach is an AI-powered system that analyzes grant proposals against solicitation requirements.

        **Features:**
        - AI-powered content analysis
        - Semantic similarity matching
        - Research team verification
        - Competitive scoring
        - Comprehensive recommendations
        """)

        st.markdown("---")
        st.subheader("📋 Instructions")
        st.markdown("""
        1. Upload your solicitation and project description PDFs
        2. Click "Start Analysis" to begin processing
        3. Review the comprehensive results
        4. Download the report for your records
        """)

if __name__ == "__main__":
    main()