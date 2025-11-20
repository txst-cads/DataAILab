"""
AgriGrantCoach Team Analyzer Module

Analyzes team biosketches and CPS documents to evaluate expertise,
capacity, and fit with proposal requirements.
"""

import json
from typing import Dict, List
from pathlib import Path
from openai import OpenAI

from config import Config
from data_loader import PersonnelData


class TeamAnalyzer:
    """Analyzes team composition, expertise, and capacity."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.client = OpenAI(api_key=config.GROQ_API_KEY)

    def extract_pi_profile(self, name: str, personnel_data: PersonnelData) -> Dict:
        """
        Extract structured profile from a PI's biosketch and CPS.

        Args:
            name: PI name
            personnel_data: PersonnelData object with bio and CPS text

        Returns:
            Dictionary with extracted expertise, publications, grants, etc.
        """
        print(f"  📋 Extracting profile for {name}...")

        prompt = self._build_profile_extraction_prompt(
            name,
            personnel_data.biosketch_text,
            personnel_data.cps_text
        )

        try:
            response = self.client.chat.completions.create(
                model=self.config.GROQ_ANALYSIS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing academic CVs and biosketches. Extract structured information with precision."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.GROQ_ANALYSIS_TEMPERATURE,
                max_tokens=self.config.GROQ_ANALYSIS_MAX_TOKENS,
            )

            profile_json_str = response.choices[0].message.content

            # Extract JSON from markdown
            if "```json" in profile_json_str:
                profile_json_str = profile_json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in profile_json_str:
                profile_json_str = profile_json_str.split("```")[1].split("```")[0].strip()

            profile = json.loads(profile_json_str)
            profile['name'] = name

            return profile

        except Exception as e:
            print(f"    ⚠️  Warning: Failed to extract profile for {name}: {e}")
            return {
                'name': name,
                'expertise_areas': [],
                'relevant_publications': [],
                'active_projects': [],
                'pending_projects': [],
                'error': str(e)
            }

    def _build_profile_extraction_prompt(
        self,
        name: str,
        biosketch_text: str,
        cps_text: str
    ) -> str:
        """Build prompt for extracting PI profile."""

        # Truncate if too long
        bio_truncated = biosketch_text[:8000] if len(biosketch_text) > 8000 else biosketch_text
        cps_truncated = cps_text[:4000] if len(cps_text) > 4000 else cps_text

        return f"""Extract a structured profile for PI: {name}

**BIOSKETCH:**
{bio_truncated}

**CURRENT AND PENDING SUPPORT (CPS):**
{cps_truncated}

**YOUR TASK:**
Extract the following information and return as JSON:

1. **Expertise Areas**: Key research domains, techniques, and methodologies (e.g., "Machine Learning", "Agricultural Systems", "Computer Vision")
2. **Key Relevant Publications**: 3-5 most relevant publications with impact
3. **Active Projects**: Current funded projects (title, funder, role, relevance to data science/agriculture)
4. **Pending Projects**: Pending grant applications (to assess workload)
5. **Unique Strengths**: What makes this PI particularly valuable for data science in agriculture

**OUTPUT FORMAT (JSON):**
{{
  "expertise_areas": [
    {{
      "domain": "Domain name",
      "description": "Brief description",
      "relevance_to_project": "How this relates to AgriGrantCoach proposal"
    }}
  ],
  "relevant_publications": [
    {{
      "title": "Publication title",
      "year": "YYYY",
      "venue": "Conference/Journal",
      "impact": "Why this is relevant/impactful"
    }}
  ],
  "active_projects": [
    {{
      "title": "Project title",
      "funder": "Funding agency",
      "role": "PI/Co-PI/Senior Personnel",
      "relevance": "How this relates to proposed work"
    }}
  ],
  "pending_projects": [
    {{
      "title": "Project title",
      "funder": "Funding agency",
      "role": "PI/Co-PI"
    }}
  ],
  "unique_strengths": "2-3 sentences on what makes this PI uniquely qualified",
  "potential_concerns": "Any workload or overlap concerns (or 'None identified')"
}}

**IMPORTANT:**
- Be selective - quality over quantity
- Focus on items relevant to data science, AI/ML, and agricultural applications
- For pending projects, note if there's potential overlap with this proposal

Return ONLY the JSON object."""

    def analyze_team_composition(
        self,
        personnel_profiles: Dict[str, Dict],
        rubric: Dict,
        narrative_text: str
    ) -> Dict:
        """
        Analyze overall team strength and fit with proposal requirements.

        Args:
            personnel_profiles: Dictionary of PI profiles from extract_pi_profile
            rubric: Solicitation rubric
            narrative_text: Proposal narrative text

        Returns:
            Dictionary with team analysis
        """
        print("\n👥 Analyzing team composition and fit...")

        # Build comprehensive team summary
        team_summary = self._build_team_summary(personnel_profiles)

        # Extract key requirements from rubric
        requirements_text = self._extract_key_requirements(rubric)

        prompt = self._build_team_analysis_prompt(
            team_summary,
            requirements_text,
            narrative_text[:6000]  # First part of narrative
        )

        try:
            response = self.client.chat.completions.create(
                model=self.config.GROQ_ANALYSIS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert grant reviewer for USDA AFRI programs. You evaluate team qualifications with a critical but fair eye."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.GROQ_ANALYSIS_TEMPERATURE,
                max_tokens=self.config.GROQ_ANALYSIS_MAX_TOKENS,
            )

            analysis_json_str = response.choices[0].message.content

            # Extract JSON
            if "```json" in analysis_json_str:
                analysis_json_str = analysis_json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_json_str:
                analysis_json_str = analysis_json_str.split("```")[1].split("```")[0].strip()

            analysis = json.loads(analysis_json_str)

            print(f"✅ Team strength score: {analysis.get('overall_score', 'N/A')}/10")
            print(f"   - Strengths identified: {len(analysis.get('key_strengths', []))}")
            print(f"   - Gaps identified: {len(analysis.get('expertise_gaps', []))}")

            return analysis

        except Exception as e:
            print(f"❌ Error analyzing team: {e}")
            return {
                'overall_score': 0,
                'key_strengths': [],
                'expertise_gaps': [],
                'concerns': [],
                'error': str(e)
            }

    def _build_team_summary(self, personnel_profiles: Dict[str, Dict]) -> str:
        """Build a text summary of team expertise."""
        summary_parts = []

        for name, profile in personnel_profiles.items():
            summary_parts.append(f"\n**{name}:**")

            # Expertise
            expertise = profile.get('expertise_areas', [])
            if expertise:
                domains = [e.get('domain', '') for e in expertise]
                summary_parts.append(f"  Expertise: {', '.join(domains)}")

            # Key pubs
            pubs = profile.get('relevant_publications', [])
            if pubs:
                summary_parts.append(f"  Notable publications: {len(pubs)}")

            # Active projects
            active = profile.get('active_projects', [])
            if active:
                summary_parts.append(f"  Active projects: {len(active)}")

            # Strengths
            strengths = profile.get('unique_strengths', '')
            if strengths:
                summary_parts.append(f"  Strengths: {strengths}")

        return "\n".join(summary_parts)

    def _extract_key_requirements(self, rubric: Dict) -> str:
        """Extract key requirements from rubric as text."""
        requirements_parts = []

        for req in rubric.get('requirements', []):
            if req.get('weight') == 'High':
                requirements_parts.append(
                    f"- {req['title']}: {req['description']}"
                )

        return "\n".join(requirements_parts)

    def _build_team_analysis_prompt(
        self,
        team_summary: str,
        requirements_text: str,
        narrative_excerpt: str
    ) -> str:
        """Build prompt for team analysis."""

        return f"""Analyze this research team for a USDA AFRI Data Science proposal.

**SOLICITATION REQUIREMENTS:**
{requirements_text}

**TEAM COMPOSITION:**
{team_summary}

**PROPOSAL EXCERPT:**
{narrative_excerpt}

**YOUR TASK:**
Evaluate the team's qualifications and provide constructive analysis.

**OUTPUT FORMAT (JSON):**
{{
  "overall_score": 8.5,  // Out of 10
  "key_strengths": [
    {{
      "strength": "Brief title",
      "description": "Detailed explanation with specific PI names and evidence",
      "impact": "Why this matters for the proposal"
    }}
  ],
  "expertise_gaps": [
    {{
      "gap": "Missing expertise area",
      "severity": "High|Medium|Low",
      "mitigation": "Possible ways to address this gap"
    }}
  ],
  "team_synergy": {{
    "score": 8.0,  // Out of 10
    "evidence": "How the team's skills complement each other"
  }},
  "workload_concerns": [
    {{
      "pi_name": "Name",
      "concern": "Description of concern",
      "recommendation": "Suggested action"
    }}
  ],
  "interdisciplinary_strength": {{
    "score": 7.5,  // Out of 10
    "description": "Assessment of interdisciplinary coverage"
  }},
  "recommendations": [
    "Specific actionable recommendation"
  ]
}}

**ANALYSIS CRITERIA:**
1. **Domain Coverage**: Data science + Agricultural systems expertise
2. **Track Record**: Publications and grants in relevant areas
3. **Complementarity**: Do skills overlap well or are there redundancies?
4. **Capacity**: Current workload vs. new project demands
5. **Agricultural Context**: Does anyone have deep agricultural domain knowledge?

Be honest and constructive. Identify both strengths and areas for improvement.

Return ONLY the JSON object."""

    def save_team_analysis(
        self,
        personnel_profiles: Dict[str, Dict],
        team_analysis: Dict,
        output_path: Path = None
    ):
        """Save team analysis to JSON."""
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / 'team_analysis.json'

        combined = {
            'personnel_profiles': personnel_profiles,
            'team_analysis': team_analysis
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Team analysis saved to: {output_path}")


if __name__ == "__main__":
    # Test the team analyzer
    from data_loader import DataLoader
    from rubric_analyzer import RubricAnalyzer

    Config.validate()

    # Load data
    loader = DataLoader()
    data = loader.load_all()

    # Load or generate rubric
    rubric_path = Config.OUTPUT_DIR / 'solicitation_rubric.json'
    if rubric_path.exists():
        with open(rubric_path, 'r') as f:
            rubric = json.load(f)
    else:
        analyzer = RubricAnalyzer()
        rubric = analyzer.extract_rubric(data['solicitation']['text'])

    # Analyze team
    team_analyzer = TeamAnalyzer()

    print("\n" + "="*60)
    print("EXTRACTING PERSONNEL PROFILES")
    print("="*60)

    personnel_profiles = {}
    for name, personnel_data in data['personnel'].items():
        # Convert dict back to PersonnelData object
        from data_loader import PersonnelData
        pd = PersonnelData(
            name=name,
            biosketch_text=personnel_data['biosketch_text'],
            cps_text=personnel_data['cps_text'],
            biosketch_chunks=personnel_data['biosketch_chunks'],
            cps_chunks=personnel_data['cps_chunks']
        )
        personnel_profiles[name] = team_analyzer.extract_pi_profile(name, pd)

    print("\n" + "="*60)
    print("ANALYZING TEAM COMPOSITION")
    print("="*60)

    team_analysis = team_analyzer.analyze_team_composition(
        personnel_profiles,
        rubric,
        data['narrative']['text']
    )

    # Save results
    team_analyzer.save_team_analysis(personnel_profiles, team_analysis)
