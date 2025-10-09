"""
Report Generator Module

Handles generation of structured reports with actionable recommendations.
Follows Single Responsibility Principle by focusing only on report generation.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from llm_evaluator import EvaluationResult


@dataclass
class ReportSection:
    """Represents a section of the generated report."""
    title: str
    content: str
    priority: str = "medium"  # "high", "medium", "low"
    actionable: bool = True


@dataclass
class Recommendation:
    """Represents a specific recommendation."""
    text: str
    priority: str = "medium"  # "high", "medium", "low"
    category: str = "general"  # "alignment", "content", "structure", "format"
    estimated_effort: str = "moderate"  # "low", "moderate", "high"


class ReportGenerator:
    """
    Generates structured, actionable reports for grant proposal evaluation.
    """

    def __init__(self):
        self.report_template = self._load_report_template()

    def _load_report_template(self) -> Dict:
        """
        Load the report template structure.

        Returns:
            Dictionary with report template structure
        """
        return {
            "header": {
                "title": "Grant Coach Evaluation Report",
                "sections": [
                    "executive_summary",
                    "overall_assessment",
                    "alignment_analysis",
                    "quality_evaluation",
                    "faculty_suitability",
                    "detailed_recommendations",
                    "alternative_funding"
                ]
            },
            "scoring": {
                "excellent": {"min": 8.0, "description": "Excellent proposal with minor improvements suggested"},
                "good": {"min": 7.0, "description": "Competitive proposal with some areas for enhancement"},
                "fair": {"min": 6.0, "description": "Moderate proposal requiring significant improvements"},
                "needs_improvement": {"min": 0.0, "description": "Major revisions required before submission"}
            }
        }

    def generate_comprehensive_report(self,
                                    processed_data: Dict,
                                    alignment_results: Dict,
                                    evaluation_results: List[EvaluationResult],
                                    faculty_info: Dict,
                                    gaps_analysis: Optional[Dict] = None) -> Dict:
        """
        Generate a comprehensive evaluation report.

        Args:
            processed_data: Processed document data
            alignment_results: Alignment analysis results
            evaluation_results: LLM evaluation results
            faculty_info: Extracted faculty information
            gaps_analysis: Optional gaps analysis results

        Returns:
            Complete report dictionary
        """
        # Calculate overall metrics
        overall_score = self._calculate_overall_score(evaluation_results)
        alignment_score = self._calculate_alignment_score(alignment_results)

        # Generate report sections
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "solicitation_file": processed_data["metadata"]["solicitation_file"],
                "proposal_file": processed_data["metadata"]["proposal_file"],
                "overall_score": overall_score,
                "alignment_score": alignment_score
            },
            "executive_summary": self._generate_executive_summary(
                overall_score, alignment_score, evaluation_results, faculty_info
            ),
            "overall_assessment": self._generate_overall_assessment(
                overall_score, alignment_score, evaluation_results
            ),
            "alignment_analysis": self._generate_alignment_section(alignment_results),
            "quality_evaluation": self._generate_quality_section(evaluation_results),
            "faculty_suitability": self._generate_faculty_section(faculty_info),
            "detailed_recommendations": self._generate_recommendations_section(
                evaluation_results, alignment_results, gaps_analysis
            ),
            "alternative_funding": self._generate_alternative_funding_section(
                processed_data, alignment_score
            ),
            "appendices": {
                "detailed_scores": self._generate_detailed_scores(evaluation_results),
                "document_statistics": processed_data.get("statistics", {}),
                "nsf_compliance_check": self._check_nsf_compliance(processed_data)
            }
        }

        return report

    def _calculate_overall_score(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate overall score from evaluation results."""
        if not evaluation_results:
            return 0.0

        # Simple average for now (could be weighted)
        return sum(result.score for result in evaluation_results) / len(evaluation_results)

    def _calculate_alignment_score(self, alignment_results: Dict) -> float:
        """Calculate overall alignment score."""
        if not alignment_results:
            return 0.0

        scores = [result['score'] for result in alignment_results.values()]
        return sum(scores) / len(scores) if scores else 0.0

    def _generate_executive_summary(self, overall_score: float, alignment_score: float,
                                   evaluation_results: List[EvaluationResult],
                                   faculty_info: Dict) -> Dict:
        """Generate executive summary section."""
        # Determine overall assessment
        if overall_score >= 8.0:
            category = "Excellent"
            readiness = "Ready for submission with minor improvements"
        elif overall_score >= 7.0:
            category = "Good"
            readiness = "Competitive, recommended enhancements before submission"
        elif overall_score >= 6.0:
            category = "Fair"
            readiness = "Moderate, significant improvements needed"
        else:
            category = "Needs Improvement"
            readiness = "Major revisions required before submission"

        # Extract key insights
        top_strengths = []
        critical_issues = []

        for result in evaluation_results:
            if result.score >= 7.0:
                top_strengths.append(result.criterion)
            elif result.score < 5.0:
                critical_issues.append(result.criterion)

        return {
            "overall_assessment": category,
            "readiness_for_submission": readiness,
            "key_metrics": {
                "overall_score": round(overall_score, 2),
                "alignment_score": round(alignment_score, 2),
                "strengths_count": len(top_strengths),
                "issues_count": len(critical_issues)
            },
            "key_strengths": top_strengths[:3],
            "critical_issues": critical_issues[:3],
            "faculty_summary": self._generate_faculty_summary(faculty_info)
        }

    def _generate_faculty_summary(self, faculty_info: Dict) -> str:
        """Generate brief faculty summary."""
        pi_name = faculty_info.get("pi", {}).get("name", "Unknown PI")
        co_pi_name = faculty_info.get("co_pi", {}).get("name", "No Co-PI specified")

        expertise = faculty_info.get("expertise_areas", [])
        expertise_str = ", ".join(expertise[:3]) if expertise else "Not specified"

        return f"PI: {pi_name}, Co-PI: {co_pi_name}. Expertise areas: {expertise_str}"

    def _generate_overall_assessment(self, overall_score: float, alignment_score: float,
                                   evaluation_results: List[EvaluationResult]) -> List[ReportSection]:
        """Generate overall assessment section."""
        sections = []

        # Overall scoring section
        scoring_text = f"""
**Overall Score: {overall_score:.2f}/10.0**

This proposal is categorized as: {self._get_score_category(overall_score)}

**Alignment Score: {alignment_score:.2f}/10.0**
The proposal demonstrates {"strong" if alignment_score >= 0.5 else "moderate" if alignment_score >= 0.3 else "weak"} alignment with solicitation requirements.

**Criterion Breakdown:**
"""
        for result in evaluation_results:
            status = "✓" if result.score >= 7.0 else "⚠" if result.score >= 5.0 else "✗"
            scoring_text += f"- {status} **{result.criterion}**: {result.score:.1f}/10.0\n"

        sections.append(ReportSection(
            title="Scoring Overview",
            content=scoring_text,
            priority="high"
        ))

        # Assessment narrative
        if overall_score >= 8.0:
            narrative = "This is a strong proposal that demonstrates good understanding of the solicitation requirements and presents a compelling case for funding."
        elif overall_score >= 7.0:
            narrative = "This is a competitive proposal with several strengths, though there are areas that could be enhanced to improve competitiveness."
        elif overall_score >= 6.0:
            narrative = "This proposal shows potential but requires significant improvements in key areas to be competitive."
        else:
            narrative = "This proposal requires major revisions across multiple areas before being ready for submission."

        sections.append(ReportSection(
            title="Overall Assessment",
            content=narrative,
            priority="high"
        ))

        return sections

    def _generate_alignment_section(self, alignment_results: Dict) -> List[ReportSection]:
        """Generate alignment analysis section."""
        sections = []

        alignment_text = "**Proposal-Solicitation Alignment Analysis:**\n\n"

        for section_name, result in alignment_results.items():
            score = result['score']
            status_icon = "✓" if score >= 0.5 else "⚠" if score >= 0.3 else "✗"

            alignment_text += f"**{status_icon} {section_name}:** {score:.3f}\n"

            if result['similar_solicitation_sections']:
                alignment_text += f"  - Aligns with: {', '.join(result['similar_solicitation_sections'])}\n"
            else:
                alignment_text += "  - No clear alignment with solicitation sections\n"

            alignment_text += "\n"

        sections.append(ReportSection(
            title="Alignment Analysis",
            content=alignment_text,
            priority="high"
        ))

        return sections

    def _generate_quality_section(self, evaluation_results: List[EvaluationResult]) -> List[ReportSection]:
        """Generate quality evaluation section."""
        sections = []

        for result in evaluation_results:
            section_text = f"**{result.criterion}: {result.score:.1f}/10.0**\n\n"
            section_text += f"**Assessment:** {result.justification}\n\n"

            if result.strengths:
                section_text += "**Strengths:**\n"
                for strength in result.strengths:
                    section_text += f"- {strength}\n"
                section_text += "\n"

            if result.weaknesses:
                section_text += "**Areas for Improvement:**\n"
                for weakness in result.weaknesses:
                    section_text += f"- {weakness}\n"
                section_text += "\n"

            if result.recommendations:
                section_text += "**Recommendations:**\n"
                for rec in result.recommendations:
                    section_text += f"- {rec}\n"

            priority = "high" if result.score < 5.0 else "medium" if result.score < 7.0 else "low"

            sections.append(ReportSection(
                title=result.criterion,
                content=section_text,
                priority=priority
            ))

        return sections

    def _generate_faculty_section(self, faculty_info: Dict) -> List[ReportSection]:
        """Generate faculty suitability section."""
        sections = []

        faculty_text = f"""
**Principal Investigator:** {faculty_info.get('pi', {}).get('name', 'Not specified')}

**Co-Principal Investigator:** {faculty_info.get('co_pi', {}).get('name', 'Not specified')}

**Areas of Expertise:**
"""

        expertise = faculty_info.get("expertise_areas", [])
        if expertise:
            for area in expertise:
                faculty_text += f"- {area}\n"
        else:
            faculty_text += "- Not clearly specified in proposal\n"

        faculty_text += "\n**Prior Funding Experience:**\n"
        funding = faculty_info.get("prior_funding", [])
        if funding:
            for fund in funding[:3]:  # Show top 3
                faculty_text += f"- {fund}\n"
        else:
            faculty_text += "- Limited prior funding information provided\n"

        faculty_text += "\n**Publication Record:**\n"
        publications = faculty_info.get("publications", [])
        if publications:
            for pub in publications:
                faculty_text += f"- {pub}\n"
        else:
            faculty_text += "- Publication details not provided\n"

        sections.append(ReportSection(
            title="Faculty Suitability Assessment",
            content=faculty_text,
            priority="medium"
        ))

        return sections

    def _generate_recommendations_section(self, evaluation_results: List[EvaluationResult],
                                         alignment_results: Dict,
                                         gaps_analysis: Optional[Dict] = None) -> List[Recommendation]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Collect all recommendations from evaluation results
        for result in evaluation_results:
            if result.score < 7.0:  # Only for areas needing improvement
                for rec in result.recommendations:
                    priority = "high" if result.score < 5.0 else "medium"
                    recommendations.append(Recommendation(
                        text=f"{result.criterion}: {rec}",
                        priority=priority,
                        category="content",
                        estimated_effort="high" if priority == "high" else "moderate"
                    ))

        # Add alignment-based recommendations
        low_alignment_sections = [
            section for section, result in alignment_results.items()
            if result['score'] < 0.3
        ]

        if low_alignment_sections:
            recommendations.append(Recommendation(
                text=f"Improve alignment with solicitation requirements in: {', '.join(low_alignment_sections)}",
                priority="high",
                category="alignment",
                estimated_effort="high"
            ))

        # Add gap analysis recommendations if available
        if gaps_analysis:
            for gap_section, gap_info in gaps_analysis.items():
                if gap_info.get('recommendation'):
                    recommendations.append(Recommendation(
                        text=gap_info['recommendation'],
                        priority=gap_info.get('gap_severity', 'medium'),
                        category="alignment",
                        estimated_effort="high" if gap_info.get('gap_severity') == 'high' else "moderate"
                    ))

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 2))

        return recommendations[:10]  # Return top 10 recommendations

    def _generate_alternative_funding_section(self, processed_data: Dict,
                                            alignment_score: float) -> List[ReportSection]:
        """Generate alternative funding suggestions."""
        sections = []

        # Extract keywords from solicitation for funding suggestions
        solicitation_text = processed_data["raw_texts"]["solicitation"].lower()

        funding_opportunities = []

        # Simple keyword-based funding suggestions
        if any(keyword in solicitation_text for keyword in ['ai', 'artificial intelligence', 'machine learning']):
            funding_opportunities.append("AI/ML-focused programs")

        if any(keyword in solicitation_text for keyword in ['education', 'stem', 'teaching']):
            funding_opportunities.append("STEM Education programs")

        if any(keyword in solicitation_text for keyword in ['diversity', 'underrepresented', 'inclusion']):
            funding_opportunities.append("Diversity and Inclusion initiatives")

        if any(keyword in solicitation_text for keyword in ['research', 'infrastructure', 'equipment']):
            funding_opportunities.append("Research Infrastructure programs")

        if not funding_opportunities:
            funding_opportunities.append("General research funding opportunities")

        alt_text = "**Alternative Funding Suggestions:**\n\n"
        alt_text += f"Based on the solicitation content and alignment score of {alignment_score:.2f}, consider these alternative funding opportunities:\n\n"

        for opportunity in funding_opportunities:
            alt_text += f"- **{opportunity}**\n"

        alt_text += "\n**Recommendation:** If alignment with current solicitation is below 0.5, consider targeting more closely aligned funding opportunities."

        sections.append(ReportSection(
            title="Alternative Funding Options",
            content=alt_text,
            priority="low"
        ))

        return sections

    def _generate_detailed_scores(self, evaluation_results: List[EvaluationResult]) -> Dict:
        """Generate detailed scoring information."""
        return {
            "criteria_scores": [
                {
                    "criterion": result.criterion,
                    "score": result.score,
                    "justification": result.justification,
                    "strengths": result.strengths,
                    "weaknesses": result.weaknesses,
                    "recommendations": result.recommendations
                }
                for result in evaluation_results
            ]
        }

    def _check_nsf_compliance(self, processed_data: Dict) -> Dict:
        """Check NSF proposal compliance."""
        proposal_sections = processed_data["sections"]["proposal"]

        required_sections = [
            "Project Summary",
            "Intellectual Merit",
            "Broader Impacts"
        ]

        compliance = {}
        for section in required_sections:
            compliance[section] = {
                "present": section in proposal_sections,
                "word_count": len(proposal_sections.get(section, "").split()) if section in proposal_sections else 0
            }

        return {
            "required_sections": compliance,
            "compliance_status": all(c["present"] for c in compliance.values())
        }

    def _get_score_category(self, score: float) -> str:
        """Get category description for score."""
        if score >= 8.0:
            return "Excellent"
        elif score >= 7.0:
            return "Good"
        elif score >= 6.0:
            return "Fair"
        else:
            return "Needs Improvement"

    def save_report_to_file(self, report: Dict, filepath: str, format: str = "json"):
        """
        Save report to file.

        Args:
            report: Report dictionary
            filepath: Output file path
            format: Output format ('json' or 'txt')
        """
        if format == "json":
            # Convert non-serializable objects to dictionaries
            serializable_report = self._make_serializable(report)
            with open(filepath, 'w') as f:
                json.dump(serializable_report, f, indent=2)
        elif format == "txt":
            with open(filepath, 'w') as f:
                f.write(self._format_report_as_text(report))
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _make_serializable(self, obj):
        """
        Convert non-JSON-serializable objects to dictionaries.
        """
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, ReportSection):
            return {
                "title": obj.title,
                "content": obj.content,
                "priority": obj.priority,
                "actionable": obj.actionable
            }
        elif isinstance(obj, Recommendation):
            return {
                "text": obj.text,
                "priority": obj.priority,
                "category": obj.category,
                "estimated_effort": obj.estimated_effort
            }
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return obj

    def _format_report_as_text(self, report: Dict) -> str:
        """Format report as plain text."""
        text = f"GRANT COACH EVALUATION REPORT\n"
        text += f"Generated: {report['metadata']['generated_at']}\n"
        text += f"Solicitation: {report['metadata']['solicitation_file'].split('/')[-1]}\n"
        text += f"Proposal: {report['metadata']['proposal_file'].split('/')[-1]}\n"
        text += f"Overall Score: {report['metadata']['overall_score']:.2f}/10.0\n\n"

        # Executive Summary
        exec_summary = report['executive_summary']
        text += "EXECUTIVE SUMMARY\n"
        text += f"Overall Assessment: {exec_summary['overall_assessment']}\n"
        text += f"Readiness for Submission: {exec_summary['readiness_for_submission']}\n\n"

        # Key Recommendations
        text += "KEY RECOMMENDATIONS\n"
        for rec in report['detailed_recommendations'][:5]:
            text += f"- {rec.text} (Priority: {rec.priority})\n"
        text += "\n"

        # Detailed sections
        for section_name, section_content in report.items():
            if section_name not in ['metadata', 'executive_summary', 'detailed_recommendations', 'appendices']:
                text += f"{section_name.upper().replace('_', ' ')}\n"
                if isinstance(section_content, list):
                    for section in section_content:
                        text += f"{section.title}\n"
                        text += f"{section.content}\n\n"
                else:
                    text += f"{section_content}\n\n"

        return text

    def generate_quick_summary(self, report: Dict) -> str:
        """
        Generate a quick summary of the report for console output.

        Args:
            report: Complete report dictionary

        Returns:
            Summary text for console display
        """
        metadata = report['metadata']
        exec_summary = report['executive_summary']

        summary = f"""
{'='*60}
GRANT COACH EVALUATION SUMMARY
{'='*60}

Overall Score: {metadata['overall_score']:.2f}/10.0 ({exec_summary['overall_assessment']})
Alignment Score: {metadata['alignment_score']:.2f}/10.0

Key Strengths:
{chr(10).join(f'  - {strength}' for strength in exec_summary['key_strengths'])}

Critical Issues:
{chr(10).join(f'  - {issue}' for issue in exec_summary['critical_issues'])}

Top 3 Recommendations:
{chr(10).join(f'  {i+1}. {rec.text}' for i, rec in enumerate(report['detailed_recommendations'][:3]))}

Readiness: {exec_summary['readiness_for_submission']}
{'='*60}
"""
        return summary