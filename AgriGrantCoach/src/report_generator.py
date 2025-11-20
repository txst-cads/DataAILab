"""
AgriGrantCoach Report Generator Module

Synthesizes all analyses into a comprehensive, evidence-based
competitiveness report with actionable recommendations.
"""

import json
from typing import Dict
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from config import Config


class ReportGenerator:
    """Generates final comprehensive analysis reports."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.client = OpenAI(api_key=config.GROQ_API_KEY)

    def generate_report(
        self,
        rubric: Dict,
        alignment_analysis: Dict,
        team_analysis: Dict,
        personnel_profiles: Dict[str, Dict],
        metadata: Dict = None
    ) -> str:
        """
        Generate comprehensive competitiveness report.

        Args:
            rubric: Extracted solicitation rubric
            alignment_analysis: Proposal-solicitation alignment results
            team_analysis: Team composition analysis
            personnel_profiles: Individual PI profiles
            metadata: Additional metadata (optional)

        Returns:
            Markdown-formatted report
        """
        print("\n📝 Generating comprehensive analysis report...")

        prompt = self._build_report_generation_prompt(
            rubric,
            alignment_analysis,
            team_analysis,
            personnel_profiles
        )

        try:
            response = self.client.chat.completions.create(
                model=self.config.GROQ_ANALYSIS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are 'GrantCoach-AFRI', an expert USDA grant reviewer and consultant.

You provide honest, evidence-based assessments that help researchers improve their proposals.
Your reports are:
- Evidence-based (cite specific sections and quote directly from the proposal when possible)
- Personalized (mention PI/Co-PI names and their specific expertise throughout the analysis)
- Balanced (acknowledge strengths AND weaknesses)
- Actionable (provide specific, implementable recommendations)
- Professional but encouraging

IMPORTANT: Always mention the PIs/Co-PIs by name when discussing team expertise, publications, or contributions. This helps users understand who brings which expertise to the project."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Slightly higher for more natural writing
                max_tokens=self.config.GROQ_ANALYSIS_MAX_TOKENS,  # Use config value for max tokens
            )

            report_markdown = response.choices[0].message.content

            # Add header and footer
            report_markdown = self._add_report_header(report_markdown, metadata)

            print("✅ Report generated successfully")

            return report_markdown

        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return self._generate_fallback_report(alignment_analysis, team_analysis)

    def _build_report_generation_prompt(
        self,
        rubric: Dict,
        alignment_analysis: Dict,
        team_analysis: Dict,
        personnel_profiles: Dict[str, Dict]
    ) -> str:
        """Build the prompt for report generation."""

        # Format alignment data
        alignment_summary = self._format_alignment_summary(alignment_analysis)

        # Format team data
        team_summary = self._format_team_summary(team_analysis, personnel_profiles)

        # Format rubric
        rubric_summary = self._format_rubric_summary(rubric)

        return f"""Generate a comprehensive competitiveness assessment report for a USDA AFRI Data Science for Food and Agricultural Systems proposal.

**ANALYSIS DATA PROVIDED:**

{rubric_summary}

{alignment_summary}

{team_summary}

**YOUR TASK:**

Write a professional, evidence-based assessment report in Markdown format. The report should help the PIs understand their proposal's competitiveness and provide actionable guidance for improvement.

**REQUIRED STRUCTURE:**

# Executive Summary

Provide:
- Overall competitiveness rating: **Highly Competitive** | **Competitive** | **Moderately Competitive** | **Needs Significant Revision**
- 3-4 sentence justification with key strengths and concerns
- Bottom-line recommendation

# Proposal-Solicitation Alignment Analysis

## Strong Alignments
For each strong alignment (score ≥ 0.80):
- Requirement name
- Direct quote from the narrative showing how it's addressed (use the matched_text provided)
- Citation (paragraph number from the analysis)
- Why this demonstrates strong alignment

## Areas of Concern
For weak alignments and gaps:
- What's missing or weak
- Quote the solicitation requirement verbatim
- Explain why this is critical for proposal success
- Provide specific, actionable recommendation with example language

## Alignment Score Interpretation
- Overall alignment: {alignment_analysis.get('overall_score', 0):.1f}%
- What this means in context of typical AFRI proposals

# Team & Expertise Evaluation

## Team Strengths
Based on the team analysis, highlight:
- Key expertise areas well-covered
- Particularly strong qualifications (cite specific PIs)
- Evidence of successful track record
- Interdisciplinary coverage

## Team Gaps & Concerns
- Missing expertise areas
- Workload concerns
- Potential redundancies or overlaps

## Team Composition Score
- Score: {team_analysis.get('overall_score', 0)}/10
- Interpretation

# Critical Success Factors

Identify 3-5 factors that will most impact competitiveness:
1. Factor name: explanation and current status
2. ...

# Prioritized Recommendations

Provide 5-10 specific, actionable recommendations, prioritized by impact:

## High Priority (Must Address)
1. **Recommendation**: Specific action to take
   - **Rationale**: Why this matters
   - **Implementation**: How to address this

## Medium Priority (Should Address)
...

## Low Priority (Consider if Space Permits)
...

# Conclusion

Final assessment and encouragement.

**IMPORTANT GUIDELINES:**
- Be specific and evidence-based
- Cite actual evidence from the analysis (e.g., "The narrative's discussion of data sharing [para 15] adequately addresses...")
- Be constructive - frame weaknesses as opportunities for improvement
- Prioritize recommendations by impact
- Use the alignment scores and team scores provided
- Don't just summarize the data - synthesize insights

Write the report in clear, professional Markdown."""

    def _format_alignment_summary(self, alignment: Dict) -> str:
        """Format alignment analysis for the prompt."""
        parts = [
            "## ALIGNMENT ANALYSIS SUMMARY",
            f"Overall Score: {alignment.get('overall_score', 0):.1f}%",
            f"Strong Alignments: {len(alignment.get('strong_alignments', []))}",
            f"Weak Alignments: {len(alignment.get('weak_alignments', []))}",
            f"Gaps: {len(alignment.get('gaps', []))}",
            ""
        ]

        # Add strong alignments
        if alignment.get('strong_alignments'):
            parts.append("**Strong Alignments:**")
            for item in alignment['strong_alignments'][:5]:  # Top 5
                parts.append(f"- {item['requirement']}: {item['score']:.2f}")
                parts.append(f"  Evidence: {item['evidence']}")
                parts.append(f"  Citation: {item['citation']}")

        # Add gaps
        if alignment.get('gaps'):
            parts.append("\n**Identified Gaps:**")
            for gap in alignment['gaps']:
                parts.append(f"- {gap['requirement']} ({gap['weight']} priority)")
                parts.append(f"  {gap['description'][:100]}...")

        return "\n".join(parts)

    def _format_team_summary(self, team_analysis: Dict, personnel_profiles: Dict) -> str:
        """Format team analysis for the prompt."""
        parts = [
            "## TEAM ANALYSIS SUMMARY",
            f"Overall Team Score: {team_analysis.get('overall_score', 0)}/10",
            f"Team Synergy Score: {team_analysis.get('team_synergy', {}).get('score', 0)}/10",
            f"Interdisciplinary Score: {team_analysis.get('interdisciplinary_strength', {}).get('score', 0)}/10",
            ""
        ]

        # Add key strengths
        if team_analysis.get('key_strengths'):
            parts.append("**Key Team Strengths:**")
            for strength in team_analysis['key_strengths']:
                parts.append(f"- {strength.get('strength', 'N/A')}")
                parts.append(f"  {strength.get('description', '')}")

        # Add gaps
        if team_analysis.get('expertise_gaps'):
            parts.append("\n**Expertise Gaps:**")
            for gap in team_analysis['expertise_gaps']:
                parts.append(f"- {gap.get('gap', 'N/A')} ({gap.get('severity', 'Unknown')} severity)")
                parts.append(f"  Mitigation: {gap.get('mitigation', 'None suggested')}")

        # Add PI summaries
        parts.append("\n**Personnel Profiles:**")
        for name, profile in personnel_profiles.items():
            expertise = profile.get('expertise_areas', [])
            if expertise:
                domains = [e.get('domain', '') for e in expertise[:3]]
                parts.append(f"- {name}: {', '.join(domains)}")

        return "\n".join(parts)

    def _format_rubric_summary(self, rubric: Dict) -> str:
        """Format rubric summary for the prompt."""
        parts = [
            "## SOLICITATION REQUIREMENTS",
            f"Program: {rubric.get('program_name', 'AFRI DSFAS')}",
            f"Total Requirements: {len(rubric.get('requirements', []))}",
            ""
        ]

        # Group by category
        reqs_by_category = {}
        for req in rubric.get('requirements', []):
            cat = req.get('category', 'Other')
            if cat not in reqs_by_category:
                reqs_by_category[cat] = []
            reqs_by_category[cat].append(req)

        for category, reqs in reqs_by_category.items():
            parts.append(f"**{category} Requirements:**")
            for req in reqs:
                parts.append(f"- {req['title']} ({req.get('weight', 'N/A')} priority)")

        return "\n".join(parts)

    def _add_report_header(self, report_markdown: str, metadata: Dict = None) -> str:
        """Add header and footer to the report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = f"""---
title: AgriGrantCoach-AFRI Competitiveness Assessment
generated: {timestamp}
tool_version: 1.0.0
---

"""
        footer = """

---

## About This Report

This report was generated by **AgriGrantCoach-AFRI**, an AI-powered grant analysis tool that provides evidence-based assessments of proposal competitiveness for USDA AFRI programs.

**Methodology:**
- Solicitation analysis using LLM-based requirement extraction
- Semantic similarity analysis (FAISS + sentence-transformers)
- Team expertise evaluation from biosketches and CPS documents
- Multi-factor synthesis and recommendation generation

**Disclaimer:**
This is an analytical tool to support proposal development. Final funding decisions are made by USDA reviewers based on comprehensive evaluation criteria. This assessment should be used as one input among many in the proposal refinement process.

---

*Generated by AgriGrantCoach-AFRI v1.0.0*
"""

        return header + report_markdown + footer

    def _generate_fallback_report(self, alignment_analysis: Dict, team_analysis: Dict) -> str:
        """Generate a basic report if LLM generation fails."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""# AgriGrantCoach-AFRI Analysis Report

**Generated:** {timestamp}

## Summary

- **Alignment Score:** {alignment_analysis.get('overall_score', 0):.1f}%
- **Team Score:** {team_analysis.get('overall_score', 0)}/10

## Alignment Analysis

- Strong Alignments: {len(alignment_analysis.get('strong_alignments', []))}
- Gaps: {len(alignment_analysis.get('gaps', []))}

## Team Analysis

- Key Strengths: {len(team_analysis.get('key_strengths', []))}
- Expertise Gaps: {len(team_analysis.get('expertise_gaps', []))}

*Note: Full report generation failed. Please review the detailed JSON files for complete analysis.*
"""

    def save_report(self, report_markdown: str, output_path: Path = None):
        """Save the report to a markdown file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.OUTPUT_DIR / f'competitiveness_report_{timestamp}.md'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_markdown)

        print(f"\n📄 Report saved to: {output_path}")

        return output_path


if __name__ == "__main__":
    # Test report generation
    Config.validate()

    # Load analysis results
    rubric_path = Config.OUTPUT_DIR / 'solicitation_rubric.json'
    alignment_path = Config.OUTPUT_DIR / 'alignment_analysis.json'
    team_path = Config.OUTPUT_DIR / 'team_analysis.json'

    with open(rubric_path, 'r') as f:
        rubric = json.load(f)

    with open(alignment_path, 'r') as f:
        alignment = json.load(f)

    with open(team_path, 'r') as f:
        team_data = json.load(f)

    # Generate report
    generator = ReportGenerator()
    report = generator.generate_report(
        rubric=rubric,
        alignment_analysis=alignment,
        team_analysis=team_data['team_analysis'],
        personnel_profiles=team_data['personnel_profiles']
    )

    # Save report
    generator.save_report(report)

    print("\n" + "="*60)
    print("REPORT PREVIEW (first 1000 chars)")
    print("="*60)
    print(report[:1000])
    print("...")
