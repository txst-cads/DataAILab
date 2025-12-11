"""
Report Generator
================
Generates comprehensive coaching reports in Markdown format.

Features:
- Executive dashboard with win probability
- Deep-dive criterion analysis with citations
- Team alignment matrix
- Specific, actionable recommendations
"""

import os
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generates formatted coaching reports from evaluation data."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_markdown_report(self, evaluation_data: Dict, output_path: str = None) -> str:
        """
        Generate a comprehensive markdown report.

        Args:
            evaluation_data: Output from CompetencyEngine.run_full_evaluation()
            output_path: Optional path to save the report

        Returns:
            Markdown report as string
        """
        sections = []

        # Header
        sections.append(self._generate_header(evaluation_data))

        # Executive Dashboard
        sections.append(self._generate_executive_dashboard(evaluation_data))

        # Deep-Dive Criterion Analysis (Focus on this - no compliance clutter)
        sections.append(self._generate_criterion_analysis(evaluation_data))

        # Team Alignment Matrix
        sections.append(self._generate_team_matrix(evaluation_data))

        # Action Plan
        sections.append(self._generate_action_plan(evaluation_data))

        # Footer
        sections.append(self._generate_footer())

        # Combine all sections
        report = "\n\n".join(sections)

        # Save if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Report saved to: {output_path}")

        return report

    def _generate_header(self, data: Dict) -> str:
        """Generate report header."""
        return f"""# 🎯 GrantScout: Competency Coaching Report

**Generated:** {self.timestamp}

---
"""

    def _generate_executive_dashboard(self, data: Dict) -> str:
        """Generate executive summary dashboard."""
        win_prob = data.get("win_probability", 0)

        # Determine status emoji and message
        if win_prob >= 80:
            status_emoji = "🟢"
            status_msg = "**HIGHLY COMPETITIVE** - Strong proposal"
        elif win_prob >= 60:
            status_emoji = "🟡"
            status_msg = "**COMPETITIVE** - Good foundation, needs refinement"
        else:
            status_emoji = "🔴"
            status_msg = "**NEEDS WORK** - Significant gaps identified"

        api_cost = data.get('api_cost', 0)

        return f"""## 📊 Executive Dashboard

### Overall Assessment

| Metric | Value |
|--------|-------|
| **Win Probability** | {status_emoji} **{win_prob}%** |
| **Status** | {status_msg} |
| **Criteria Evaluated** | {data.get('total_criteria', 0)} |
| **Team Size** | {data.get('team_summary', {}).get('total_members', 0)} members |
| **Analysis Cost** | ${api_cost:.3f} |

---
"""



    def _generate_criterion_analysis(self, data: Dict) -> str:
        """Generate deep-dive analysis for each criterion."""
        evaluations = data.get("criterion_evaluations", [])

        section = """## 🔍 Deep-Dive Criterion Analysis

The following sections analyze each evaluation criterion in detail.

---

"""

        for idx, eval_item in enumerate(evaluations, 1):
            section += self._format_criterion_evaluation(idx, eval_item)

        return section

    def _format_criterion_evaluation(self, idx: int, eval_item: Dict) -> str:
        """Format a single criterion evaluation."""
        title = eval_item.get("title", "Untitled")
        score = eval_item.get("score", 0)
        weight = eval_item.get("weight", 0)
        gaps = eval_item.get("gaps", [])
        recommendations = eval_item.get("recommendations", [])
        evidence_count = eval_item.get("evidence_count", 0)

        # Score bar visualization
        score_bar = self._create_score_bar(score)

        section = f"""### {idx}. {title}

**Score:** {score}/10 {score_bar}
**Weight:** {weight} points
**Evidence Found:** {evidence_count} relevant section(s) in narrative

"""

        # Gaps (including hidden weaknesses and missing synergies)
        if gaps:
            section += "#### 🚨 Identified Gaps & Hidden Weaknesses\n\n"
            for gap in gaps:
                # Add icons based on gap type
                if "Hidden Weakness:" in gap:
                    section += f"- 🔍 {gap.replace('Hidden Weakness: ', '')}\n"
                elif "Missing Synergy:" in gap:
                    section += f"- 🔗 {gap.replace('Missing Synergy: ', '')}\n"
                else:
                    section += f"- ⚠️ {gap}\n"
            section += "\n"

        # Recommendations
        if recommendations:
            section += "#### 💡 Coaching Recommendations\n\n"
            for i, rec in enumerate(recommendations, 1):
                section += f"{i}. {rec}\n"
            section += "\n"

        # Team alignment
        team_alignment = eval_item.get("team_alignment", {})
        if team_alignment:
            section += "#### 👥 Team Members with Relevant Expertise\n\n"
            for member, skills in team_alignment.items():
                section += f"**{member}:**\n"
                for skill in skills[:3]:  # Show top 3
                    section += f"  - {skill}\n"
                section += "\n"

        section += "---\n\n"
        return section

    def _create_score_bar(self, score: float) -> str:
        """Create a visual score bar using emojis."""
        filled = int(score)
        empty = 10 - filled

        if score >= 8:
            bar = "🟢" * filled + "⚪" * empty
        elif score >= 5:
            bar = "🟡" * filled + "⚪" * empty
        else:
            bar = "🔴" * filled + "⚪" * empty

        return bar

    def _generate_team_matrix(self, data: Dict) -> str:
        """Generate team alignment matrix."""
        team_summary = data.get("team_summary", {})
        members = team_summary.get("members", [])

        if not members:
            return "## 👥 Team Alignment Matrix\n\n_No team data available._\n\n---\n"

        section = """## 👥 Team Alignment Matrix

This matrix shows which team members have expertise relevant to each evaluation criterion.

"""

        # Create a table
        section += "| Team Member | Title | Key Expertise Areas |\n"
        section += "|-------------|-------|--------------------|\n"

        for member in members:
            name = member.get("name", "Unknown")
            title = member.get("title", "N/A")
            expertise = ", ".join(member.get("expertise_areas", [])[:3])

            section += f"| {name} | {title} | {expertise or 'Not specified'} |\n"

        section += "\n---\n\n"
        return section

    def _generate_action_plan(self, data: Dict) -> str:
        """Generate prioritized action plan."""
        evaluations = data.get("criterion_evaluations", [])

        # Collect all recommendations with their criterion scores
        actions = []
        for eval_item in evaluations:
            score = eval_item.get("score", 10)
            title = eval_item.get("title", "Unknown")
            recommendations = eval_item.get("recommendations", [])

            for rec in recommendations:
                actions.append({
                    "priority": 10 - score,  # Lower scores = higher priority
                    "criterion": title,
                    "action": rec
                })

        # Sort by priority
        actions.sort(key=lambda x: x["priority"], reverse=True)

        section = """## 📋 Prioritized Action Plan

Address these items in order to maximize your win probability:

"""

        for idx, action in enumerate(actions[:10], 1):  # Top 10 actions
            priority_label = self._get_priority_label(action["priority"])
            section += f"{idx}. **[{priority_label}]** *{action['criterion']}*\n"
            section += f"   {action['action']}\n\n"

        if len(actions) > 10:
            section += f"_...and {len(actions) - 10} more recommendations in the detailed analysis above._\n\n"

        section += "---\n\n"
        return section

    def _get_priority_label(self, priority: float) -> str:
        """Convert priority score to label."""
        if priority >= 7:
            return "🔥 CRITICAL"
        elif priority >= 5:
            return "⚠️ HIGH"
        elif priority >= 3:
            return "🟡 MEDIUM"
        else:
            return "🟢 LOW"

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""---

## 📚 How to Use This Report

1. **Start with Critical Actions:** Address all 🔥 CRITICAL items first
2. **Cite Team Expertise:** When recommendations mention team members, add specific citations to their CVs
3. **Strengthen Evidence:** For weak sections, add concrete examples and quantitative data
4. **Verify Compliance:** Check off all compliance requirements before submission
5. **Iterate:** Re-run GrantScout after making changes to track improvements

---

*Report generated by **GrantScout: AI Competency Coach** on {self.timestamp}*
"""

    def export_json(self, evaluation_data: Dict, output_path: str):
        """
        Export evaluation data as JSON for further processing.

        Args:
            evaluation_data: Evaluation data dict
            output_path: Path to save JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

        print(f"💾 JSON data exported to: {output_path}")


# CLI Interface for testing
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("📄 GrantScout: Report Generator")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUsage: python reporter.py <evaluation_json_path> [output_md_path]")
        print("\nExample:")
        print("  python reporter.py data/evaluation_report.json data/coach_report.md")
        sys.exit(1)

    eval_json_path = sys.argv[1]
    output_md_path = sys.argv[2] if len(sys.argv) > 2 else "data/coach_report.md"

    # Load evaluation data
    with open(eval_json_path, 'r') as f:
        eval_data = json.load(f)

    # Generate report
    reporter = ReportGenerator()
    report = reporter.generate_markdown_report(eval_data, output_path=output_md_path)

    print(f"\n✅ Report generated successfully!")
    print(f"📄 Markdown: {output_md_path}")
