"""
GrantScout: AI Competency Coach
================================
Main Streamlit Application

Orchestrates the complete proposal evaluation workflow:
1. Document Upload (Solicitation + Narrative)
2. Faculty Data Fetching (URLs)
3. Competency Analysis
4. Report Generation
"""

import os
import sys
from pathlib import Path
import streamlit as st
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingester import DocumentIngester
from src.faculty_bot import FacultyBot
from src.evaluator import CompetencyEngine
from src.reporter import ReportGenerator
from src.services.coach_service import CoachService


# Page configuration
st.set_page_config(
    page_title="GrantScout: AI Competency Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'evaluation_complete' not in st.session_state:
        st.session_state.evaluation_complete = False
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    if 'report_markdown' not in st.session_state:
        st.session_state.report_markdown = None
    if 'augmentation_complete' not in st.session_state:
        st.session_state.augmentation_complete = False
    if 'augmentation_report' not in st.session_state:
        st.session_state.augmentation_report = None


def save_uploaded_file(uploaded_file, directory="temp_uploads"):
    """Save uploaded file and return path."""
    save_dir = Path(directory)
    save_dir.mkdir(exist_ok=True)

    file_path = save_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path)


def main():
    """Main application logic."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🎯 GrantScout: AI Competency Coach</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Transform your grant proposals from compliant to highly competitive</div>',
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.header("📋 About GrantScout")
        st.markdown("""
        **GrantScout** evaluates your grant proposal using:

        - **Smart Document Parsing**: Extracts requirements with citation tracking
        - **Polymorphic Faculty Fetcher**: Builds team profiles from any source
        - **RAG-Powered Analysis**: Validates narrative strength
        - **Evidence-Based Coaching**: Provides specific recommendations

        **Output:**
        - Win probability score
        - Deep-dive criterion analysis
        - Team alignment matrix
        - Prioritized action plan
        """)

        st.divider()

        st.header("⚙️ Configuration")
        st.info("Using OpenAI GPT-4o-mini + FAISS")

        if st.button("🗑️ Clear All Data"):
            st.session_state.evaluation_complete = False
            st.session_state.report_data = None
            st.session_state.report_markdown = None
            st.session_state.augmentation_complete = False
            st.session_state.augmentation_report = None
            st.success("Session cleared!")
            st.rerun()

    # Main Content
    tabs = st.tabs(["📤 Upload & Analyze", "📊 Results", "👥 Team Augmentation", "💾 Export"])

    # ==================== TAB 1: UPLOAD & ANALYZE ====================
    with tabs[0]:
        st.header("Step 1: Upload Documents")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            st.subheader("📄 Solicitation Document")
            st.caption("Upload the grant solicitation/RFP (PDF or DOCX)")
            solicitation_file = st.file_uploader(
                "Solicitation",
                type=['pdf', 'docx'],
                key="solicitation",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            st.subheader("📝 Draft Narrative")
            st.caption("Upload your draft proposal narrative (PDF or DOCX)")
            narrative_file = st.file_uploader(
                "Narrative",
                type=['pdf', 'docx'],
                key="narrative",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        st.header("Step 2: Team Information")
        st.caption("Upload faculty profiles or enter URLs. Supported formats: HTML webpages (saved), DOCX biosketches (NSF-style), or URLs")

        # File upload for faculty
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("👥 Upload Faculty Files")
        st.caption("Upload saved HTML profiles, DOCX biosketches (e.g., NSF Biographical Sketch), or PDF CVs")

        faculty_files = st.file_uploader(
            "Faculty Files",
            type=['html', 'htm', 'docx', 'pdf'],
            accept_multiple_files=True,
            key="faculty_files",
            help="Upload one or more files: HTML pages (saved faculty profiles), DOCX biosketches, or PDF CVs"
        )

        if faculty_files:
            st.success(f"✅ {len(faculty_files)} file(s) uploaded")
            for file in faculty_files:
                st.caption(f"  • {file.name}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Optional: URLs as alternative/additional input
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("🔗 Or Enter URLs (Optional)")
        st.caption("Enter faculty profile URLs if you prefer URLs over file uploads")

        faculty_urls_text = st.text_area(
            "Faculty URLs",
            height=100,
            placeholder="https://example.edu/~faculty1/profile.html\nhttps://example.edu/faculty2/cv.pdf\n...",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # Analyze Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button(
                "🚀 Analyze Proposal",
                type="primary",
                use_container_width=True,
                disabled=not (solicitation_file and narrative_file)
            )

        # Processing Logic
        if analyze_button:
            with st.spinner("🔄 Processing your proposal..."):
                try:
                    # Save uploaded files
                    solicitation_path = save_uploaded_file(solicitation_file)
                    narrative_path = save_uploaded_file(narrative_file)

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: Fetch Faculty Data
                    status_text.text("👥 Processing faculty data...")
                    progress_bar.progress(20)

                    team_data = {"team_members": []}
                    faculty_paths_and_urls = []

                    # Process uploaded files
                    if faculty_files:
                        status_text.text(f"👥 Processing {len(faculty_files)} uploaded faculty file(s)...")
                        for faculty_file in faculty_files:
                            file_path = save_uploaded_file(faculty_file)
                            faculty_paths_and_urls.append(file_path)

                    # Process URLs
                    if faculty_urls_text.strip():
                        faculty_urls = [url.strip() for url in faculty_urls_text.split('\n') if url.strip()]
                        faculty_paths_and_urls.extend(faculty_urls)

                    # Fetch faculty data if any sources provided
                    if faculty_paths_and_urls:
                        bot = FacultyBot()
                        team_data = bot.process_faculty_list(faculty_paths_and_urls)
                    else:
                        st.warning("⚠️ No faculty information provided. Analysis will proceed without team data.")

                    # Step 2: Ingest Documents
                    status_text.text("📚 Parsing documents and creating vector indices...")
                    progress_bar.progress(40)

                    ingester = DocumentIngester()
                    ingester.ingest_multiple({
                        "solicitation": solicitation_path,
                        "narrative": narrative_path
                    })

                    # Step 3: Run Evaluation
                    status_text.text("🧠 Analyzing proposal competencies...")
                    progress_bar.progress(60)

                    engine = CompetencyEngine(ingester=ingester, team_data=team_data)
                    report_data = engine.run_full_evaluation()

                    # Step 4: Generate Report
                    status_text.text("📄 Generating coaching report...")
                    progress_bar.progress(80)

                    reporter = ReportGenerator()
                    report_markdown = reporter.generate_markdown_report(report_data)

                    # Save to session state
                    st.session_state.report_data = report_data
                    st.session_state.report_markdown = report_markdown
                    st.session_state.evaluation_complete = True

                    progress_bar.progress(100)
                    status_text.text("✅ Analysis complete!")

                    st.success("🎉 Proposal analysis complete! View results in the 'Results' tab.")

                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    # ==================== TAB 2: RESULTS ====================
    with tabs[1]:
        if not st.session_state.evaluation_complete:
            st.info("📋 Upload documents and run analysis to view results.")
        else:
            data = st.session_state.report_data

            # Executive Summary
            st.header("📊 Executive Dashboard")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                win_prob = data.get("win_probability", 0)
                if win_prob >= 80:
                    st.metric("Win Probability", f"{win_prob}%", delta="Strong", delta_color="normal")
                elif win_prob >= 60:
                    st.metric("Win Probability", f"{win_prob}%", delta="Good", delta_color="normal")
                else:
                    st.metric("Win Probability", f"{win_prob}%", delta="Needs Work", delta_color="inverse")

            with col2:
                st.metric("Criteria Evaluated", data.get("total_criteria", 0))

            with col3:
                st.metric("Team Members", data.get("team_summary", {}).get("total_members", 0))

            st.divider()

            # Team Analysis Section
            st.header("👥 Team Analysis")
            team_summary = data.get("team_summary", {})
            team_members = team_summary.get("members", [])

            if team_members:
                st.subheader(f"Current Team ({len(team_members)} members)")

                for member in team_members:
                    with st.expander(f"**{member.get('name', 'Unknown')}** - {member.get('title', 'N/A')}", expanded=False):
                        st.markdown(f"**Title:** {member.get('title', 'Not specified')}")

                        expertise = member.get('expertise_areas', [])
                        if expertise:
                            st.markdown("**Key Expertise Areas:**")
                            for area in expertise[:5]:  # Show top 5
                                st.markdown(f"  - {area}")
                        else:
                            st.info("No expertise areas extracted")
            else:
                st.info("No team data available. Upload faculty files or enter URLs to analyze team composition.")

            st.divider()

            # Full Markdown Report
            st.header("📄 Detailed Coaching Report")
            st.markdown(st.session_state.report_markdown)

    # ==================== TAB 3: TEAM AUGMENTATION ====================
    with tabs[2]:
        st.header("👥 Team Augmentation & Collaborator Recommendations")

        st.markdown("""
        **Find optimal collaborators to strengthen your grant proposal team.**

        This tool analyzes your proposal and current team, then suggests researchers who:
        - Fill critical skill gaps
        - Maximize team coverage of proposal requirements
        - Have relevant publications and expertise
        """)

        st.divider()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📝 Grant Proposal Text")
            proposal_text = st.text_area(
                "Paste your grant proposal text here",
                height=200,
                placeholder="Enter the main content of your grant proposal...",
                help="The system will analyze this text to extract required skills and expertise areas"
            )

        with col2:
            st.subheader("⚙️ Settings")
            max_suggestions = st.slider(
                "Number of collaborators to suggest",
                min_value=1,
                max_value=5,
                value=3,
                help="How many new collaborators should we recommend?"
            )

            candidate_pool_size = st.slider(
                "Candidate pool size",
                min_value=50,
                max_value=200,
                value=100,
                step=10,
                help="Size of the initial candidate pool to consider"
            )

        st.subheader("👥 Current Team Members")
        st.caption("Enter the names of your current team members (one per line)")

        current_team_text = st.text_area(
            "Current team member names",
            height=150,
            placeholder="Jane Doe\nJohn Smith\nMaria Garcia",
            label_visibility="collapsed",
            help="Enter full names as they appear in OpenAlex database"
        )

        st.divider()

        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            augment_button = st.button(
                "🔍 Find Collaborators",
                type="primary",
                use_container_width=True,
                disabled=not (proposal_text and current_team_text)
            )

        # Processing Logic
        if augment_button:
            with st.spinner("🔄 Analyzing team and finding optimal collaborators..."):
                try:
                    # Parse current team names
                    current_team_names = [name.strip() for name in current_team_text.split('\n') if name.strip()]

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Initialize Coach Service
                    status_text.text("🚀 Initializing Grant Coach Service...")
                    progress_bar.progress(10)

                    coach = CoachService()

                    # Run full coaching analysis
                    status_text.text("🧠 Running team augmentation analysis...")
                    progress_bar.progress(30)

                    report = coach.run_full_coaching_analysis(
                        proposal_text=proposal_text,
                        current_team_names=current_team_names,
                        max_suggestions=max_suggestions
                    )

                    # Save to session state
                    st.session_state.augmentation_report = report
                    st.session_state.augmentation_complete = True

                    progress_bar.progress(100)
                    status_text.text("✅ Analysis complete!")

                    st.success("🎉 Team augmentation analysis complete!")

                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

        # Display Results
        if st.session_state.augmentation_complete and st.session_state.augmentation_report:
            st.divider()
            st.header("📊 Analysis Results")

            report = st.session_state.augmentation_report
            summary = report['summary']

            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Current Coverage",
                    f"{summary['baseline_coverage']:.1%}",
                    help="How well current team covers required skills"
                )

            with col2:
                st.metric(
                    "Projected Coverage",
                    f"{summary['projected_coverage']:.1%}",
                    delta=f"+{summary['coverage_improvement']:.1%}",
                    help="Coverage after adding suggested collaborators"
                )

            with col3:
                st.metric(
                    "Current Team Size",
                    summary.get('current_coverage', 0),
                    help="Number of current team members found in database"
                )

            with col4:
                st.metric(
                    "Suggested Additions",
                    summary['suggested_collaborators'],
                    help="Number of new collaborators recommended"
                )

            st.divider()

            # Current Team Analysis
            st.subheader("👥 Current Team Analysis")
            current_team = report['current_team']

            if current_team.get('unresolved_members'):
                st.warning(f"⚠️ Could not find {len(current_team['unresolved_members'])} team members in database:")
                for name in current_team['unresolved_members']:
                    st.caption(f"  • {name}")

            if current_team['coverage_analysis']['team_members']:
                team_df_data = []
                for name, metrics in current_team['coverage_analysis']['team_members'].items():
                    team_df_data.append({
                        'Name': name,
                        'Expertise Score': f"{metrics['academic_expertise_score']:.3f}",
                        'Affinity Score': f"{metrics['final_affinity_score']:.3f}",
                        'Publications': metrics['total_papers']
                    })

                import pandas as pd
                st.dataframe(pd.DataFrame(team_df_data), use_container_width=True)

            st.divider()

            # Recommended Collaborators
            st.subheader("🎯 Recommended Collaborators")

            recommendations = report['augmentation_recommendations']['recommendations']

            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"#{i}: {rec['name']} - {rec['institution']}", expanded=True):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.markdown(f"**Institution:** {rec['institution']}")
                            st.markdown(f"**Rationale:** {rec['rationale']}")
                            st.markdown(f"**OpenAlex ID:** `{rec['researcher_id']}`")

                        with col2:
                            st.metric("Affinity Score", f"{rec['final_affinity_score']:.3f}")
                            st.metric("Marginal Gain", f"{rec['marginal_gain']:.1%}")
                            st.metric("Publications", rec['total_papers'])
            else:
                st.info("No additional collaborators recommended. Current team has excellent coverage!")

            st.divider()

            # Required Skills
            with st.expander("📋 View Required Skills Extracted from Proposal"):
                skills = report['proposal_analysis']['required_skills']
                st.write(f"**Total Skills Identified:** {len(skills)}")

                # Display in columns
                cols = st.columns(3)
                for i, skill in enumerate(skills):
                    cols[i % 3].write(f"• {skill}")

    # ==================== TAB 4: EXPORT ====================
    with tabs[3]:
        st.header("💾 Export Options")

        # Proposal Evaluation Export
        if st.session_state.evaluation_complete:
            st.subheader("📊 Proposal Evaluation Reports")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📄 Markdown Report**")
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=st.session_state.report_markdown,
                    file_name=f"grant_scout_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="export_md"
                )

            with col2:
                st.markdown("**📊 JSON Data**")
                json_str = json.dumps(st.session_state.report_data, indent=2)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=f"grant_scout_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="export_json"
                )

            st.divider()

        # Team Augmentation Export
        if st.session_state.augmentation_complete:
            st.subheader("👥 Team Augmentation Reports")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📊 Augmentation JSON**")
                augment_json = json.dumps(st.session_state.augmentation_report, indent=2)
                st.download_button(
                    label="⬇️ Download Augmentation Report",
                    data=augment_json,
                    file_name=f"team_augmentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="export_augment_json"
                )

            with col2:
                st.markdown("**📋 Recommendations CSV**")
                if st.session_state.augmentation_report:
                    recommendations = st.session_state.augmentation_report['augmentation_recommendations']['recommendations']
                    if recommendations:
                        import pandas as pd
                        rec_df = pd.DataFrame(recommendations)
                        csv = rec_df.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download Recommendations CSV",
                            data=csv,
                            file_name=f"collaborator_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="export_rec_csv"
                        )

            st.divider()

        # Quick Actions
        if st.session_state.evaluation_complete or st.session_state.augmentation_complete:
            st.subheader("📋 Quick Actions")
            if st.button("🖨️ Print Report"):
                st.info("Use your browser's print function (Ctrl/Cmd + P) to print or save as PDF.")
        else:
            st.info("📋 Complete analysis to export results.")


if __name__ == "__main__":
    main()
