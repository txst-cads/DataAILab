"""
LLM Evaluator Module

Handles proposal quality assessment and faculty suitability analysis using LLM.
Follows Single Responsibility Principle by focusing only on LLM-based evaluation.
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import textstat
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv('/Users/quamos/Desktop/CADS/DataAILab/.env')


@dataclass
class EvaluationCriteria:
    """Defines evaluation criteria for proposals."""
    name: str
    description: str
    weight: float
    max_score: float = 10.0


@dataclass
class EvaluationResult:
    """Stores evaluation results for a specific criterion."""
    criterion: str
    score: float
    justification: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class LLMEvaluator:
    """
    Handles LLM-based evaluation of grant proposals and faculty suitability.
    Uses lightweight LLM for quality assessment and rule-based analysis.
    """

    def __init__(self, use_mock_llm: bool = False):
        """
        Initialize the LLM evaluator.

        Args:
            use_mock_llm: If True, uses mock LLM responses for testing
        """
        self.use_mock_llm = use_mock_llm
        self.evaluation_criteria = self._define_evaluation_criteria()

        # Initialize Groq client
        if not use_mock_llm:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = Groq(api_key=groq_api_key)
            self.model = "llama-3.1-8b-instant"  # Using a fast, capable model for evaluation

    def _define_evaluation_criteria(self) -> List[EvaluationCriteria]:
        """
        Define the evaluation criteria for grant proposals.

        Returns:
            List of evaluation criteria
        """
        return [
            EvaluationCriteria(
                name="alignment_with_solicitation",
                description="How well the proposal addresses solicitation requirements",
                weight=0.25
            ),
            EvaluationCriteria(
                name="intellectual_merit",
                description="Significance, innovation, and rigor of the proposed work",
                weight=0.20
            ),
            EvaluationCriteria(
                name="broader_impacts",
                description="Potential to benefit society and advance diversity",
                weight=0.20
            ),
            EvaluationCriteria(
                name="feasibility",
                description="Realistic timeline, budget, and methodology",
                weight=0.15
            ),
            EvaluationCriteria(
                name="faculty_expertise",
                description="PI/Co-PI qualifications and relevant experience",
                weight=0.10
            ),
            EvaluationCriteria(
                name="clarity_and_organization",
                description="Writing quality, structure, and presentation",
                weight=0.10
            )
        ]

    def extract_faculty_information(self, proposal_sections: Dict) -> Dict:
        """
        Extract faculty information from proposal sections.

        Args:
            proposal_sections: Dictionary of proposal sections

        Returns:
            Dictionary with extracted faculty information
        """
        faculty_info = {
            "pi": {},
            "co_pi": {},
            "expertise_areas": [],
            "prior_funding": [],
            "publications": [],
            "collaborations": []
        }

        # Extract from biographical sketches
        bio_text = proposal_sections.get("Biographical Sketches", "")

        # Extract PI information (simplified pattern matching)
        pi_patterns = [
            r'([A-Za-z\s]+)\s*\(\s*PI\s*\)',
            r'Principal\s*Investigator\s*:\s*([A-Za-z\s]+)',
            r'PI\s*:\s*([A-Za-z\s]+)'
        ]

        for pattern in pi_patterns:
            match = re.search(pattern, bio_text, re.IGNORECASE)
            if match:
                faculty_info["pi"]["name"] = match.group(1).strip()
                break

        # Extract Co-PI information
        co_pi_patterns = [
            r'([A-Za-z\s]+)\s*\(\s*Co-PI\s*\)',
            r'Co-Principal\s*Investigator\s*:\s*([A-Za-z\s]+)',
            r'Co-PI\s*:\s*([A-Za-z\s]+)'
        ]

        for pattern in co_pi_patterns:
            match = re.search(pattern, bio_text, re.IGNORECASE)
            if match:
                faculty_info["co_pi"]["name"] = match.group(1).strip()
                break

        # Extract expertise areas
        expertise_patterns = [
            r'expertise\s*[=:]\s*([^.\n]+)',
            r'research\s*interests?\s*[=:]\s*([^.\n]+)',
            r'specialization\s*[=:]\s*([^.\n]+)'
        ]

        for pattern in expertise_patterns:
            matches = re.findall(pattern, bio_text, re.IGNORECASE)
            for match in matches:
                expertise = match.strip()
                if expertise and expertise not in faculty_info["expertise_areas"]:
                    faculty_info["expertise_areas"].append(expertise)

        # Extract prior funding mentions
        funding_patterns = [
            r'NSF\s*grant\s*([^.\n]+)',
            r'funded\s*by\s*([^.\n]+)',
            r'prior\s*funding\s*([^.\n]+)'
        ]

        for pattern in funding_patterns:
            matches = re.findall(pattern, bio_text, re.IGNORECASE)
            faculty_info["prior_funding"].extend(matches)

        # Extract publication counts
        pub_patterns = [
            r'(\d+)\s*publications?',
            r'(\d+)\s*peer-reviewed\s*papers?',
            r'published\s*over\s*(\d+)\s*papers?'
        ]

        for pattern in pub_patterns:
            match = re.search(pattern, bio_text, re.IGNORECASE)
            if match:
                faculty_info["publications"].append(f"~{match.group(1)} publications")

        return faculty_info

    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Make a call to the Groq API.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in the response

        Returns:
            LLM response text
        """
        if self.use_mock_llm:
            return self._mock_llm_response(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert grant proposal evaluator with extensive experience in NSF and other funding agency reviews. Provide detailed, constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for more consistent evaluations
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API call failed: {e}")
            return self._mock_llm_response(prompt)

    def _mock_llm_response(self, prompt: str) -> str:
        """
        Generate a mock LLM response for testing purposes.

        Args:
            prompt: The original prompt

        Returns:
            Mock response text
        """
        return "This is a mock LLM response for testing purposes. In production, this would be replaced with actual LLM evaluation."

    def _evaluate_with_llm(self, criterion: EvaluationCriteria,
                          proposal_sections: Dict,
                          alignment_results: Dict = None) -> EvaluationResult:
        """
        Evaluate a criterion using the LLM.

        Args:
            criterion: The criterion to evaluate
            proposal_sections: Dictionary of proposal sections
            alignment_results: Optional alignment analysis results

        Returns:
            Evaluation result from LLM
        """
        # Prepare relevant text for the criterion
        relevant_sections = self._get_relevant_sections(criterion.name, proposal_sections)
        text_content = "\n\n".join([f"{section}: {content}" for section, content in relevant_sections.items()])

        # Create prompt based on criterion
        prompt = self._create_evaluation_prompt(criterion, text_content, alignment_results)

        # Get LLM evaluation
        llm_response = self._call_llm(prompt, max_tokens=1500)

        # Parse LLM response into structured evaluation
        return self._parse_llm_response(criterion.name, llm_response)

    def _get_relevant_sections(self, criterion_name: str, proposal_sections: Dict) -> Dict:
        """
        Get sections most relevant to a specific criterion.

        Args:
            criterion_name: Name of the criterion
            proposal_sections: All proposal sections

        Returns:
            Dictionary of relevant sections
        """
        criterion_lower = criterion_name.lower()

        # Define section mappings for different criteria
        section_mappings = {
            "alignment_with_solicitation": ["Project Description", "Project Summary", "Overview"],
            "intellectual_merit": ["Intellectual Merit", "Project Description", "Research Plan"],
            "broader_impacts": ["Broader Impacts", "Project Description", "Outreach"],
            "feasibility": ["Project Description", "Budget Justification", "Timeline", "Methodology"],
            "faculty_expertise": ["Biographical Sketches", "Facilities", "Resources"],
            "clarity_and_organization": ["Project Description", "Project Summary", "Overview"]
        }

        relevant_sections = {}
        for section_name in section_mappings.get(criterion_lower, list(proposal_sections.keys())):
            if section_name in proposal_sections and proposal_sections[section_name].strip():
                relevant_sections[section_name] = proposal_sections[section_name]

        return relevant_sections

    def _create_evaluation_prompt(self, criterion: EvaluationCriteria,
                                 text_content: str,
                                 alignment_results: Dict = None) -> str:
        """
        Create a detailed evaluation prompt for the LLM.

        Args:
            criterion: The criterion to evaluate
            text_content: Relevant proposal text
            alignment_results: Optional alignment results

        Returns:
            Complete prompt for LLM evaluation
        """
        prompt = f"""
Please evaluate the following grant proposal section(s) based on the criterion: {criterion.name}

Criterion Description: {criterion.description}
Maximum Score: {criterion.max_score}

Proposal Content:
{text_content}

"""

        if alignment_results and criterion.name == "Alignment with Solicitation":
            prompt += f"""
Alignment Analysis Results:
The similarity analysis shows an average alignment score of {sum(r['score'] for r in alignment_results.values()) / len(alignment_results):.3f}
"""

        prompt += """
Please provide a detailed evaluation in the following format:

Score: [X.X out of 10.0]

Justification: [Detailed explanation of the score]

Strengths:
- [Strength 1]
- [Strength 2]
- [Strength 3]

Weaknesses:
- [Weakness 1]
- [Weakness 2]
- [Weakness 3]

Recommendations:
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]

Be specific, constructive, and focused on the criterion. Provide actionable feedback.
"""

        return prompt

    def _parse_llm_response(self, criterion_name: str, llm_response: str) -> EvaluationResult:
        """
        Parse LLM response into structured evaluation result.

        Args:
            criterion_name: Name of the criterion
            llm_response: Raw LLM response text

        Returns:
            Structured evaluation result
        """
        try:
            # Extract score
            score_match = re.search(r'Score:\s*(\d+\.?\d*)\s*out of\s*10\.0', llm_response)
            score = float(score_match.group(1)) if score_match else 5.0
            score = min(10.0, max(0.0, score))  # Ensure score is within bounds

            # Extract justification
            justification_match = re.search(r'Justification:\s*(.*?)(?=\nStrengths:|\nWeaknesses:|\nRecommendations:|$)', llm_response, re.DOTALL)
            justification = justification_match.group(1).strip() if justification_match else "No justification provided"

            # Extract strengths
            strengths_section = re.search(r'Strengths:\s*(.*?)(?=\nWeaknesses:|\nRecommendations:|$)', llm_response, re.DOTALL)
            strengths = []
            if strengths_section:
                strength_items = re.findall(r'\-\s*(.*?)(?=\n\-|\n|$)', strengths_section.group(1))
                strengths = [s.strip() for s in strength_items if s.strip()]

            # Extract weaknesses
            weaknesses_section = re.search(r'Weaknesses:\s*(.*?)(?=\nRecommendations:|$)', llm_response, re.DOTALL)
            weaknesses = []
            if weaknesses_section:
                weakness_items = re.findall(r'\-\s*(.*?)(?=\n\-|\n|$)', weaknesses_section.group(1))
                weaknesses = [w.strip() for w in weakness_items if w.strip()]

            # Extract recommendations
            recommendations_section = re.search(r'Recommendations:\s*(.*?)(?=$)', llm_response, re.DOTALL)
            recommendations = []
            if recommendations_section:
                recommendation_items = re.findall(r'\-\s*(.*?)(?=\n\-|\n|$)', recommendations_section.group(1))
                recommendations = [r.strip() for r in recommendation_items if r.strip()]

            # Ensure we have at least some content in each category
            if not strengths:
                strengths = ["No specific strengths identified"]
            if not weaknesses:
                weaknesses = ["No specific weaknesses identified"]
            if not recommendations:
                recommendations = ["No specific recommendations provided"]

            return EvaluationResult(
                criterion=criterion_name,
                score=score,
                justification=justification,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations
            )

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Return a basic evaluation result
            return EvaluationResult(
                criterion=criterion_name,
                score=5.0,
                justification=f"Unable to parse LLM response: {str(e)}",
                strengths=["Response parsing failed"],
                weaknesses=["Unable to analyze response"],
                recommendations=["Try re-evaluating with clearer response format"]
            )

    def calculate_readability_metrics(self, text: str) -> Dict:
        """
        Calculate readability metrics for proposal text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with readability metrics
        """
        try:
            metrics = {
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "automated_readability_index": textstat.automated_readability_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "sentence_count": textstat.sentence_count(text),
                "word_count": textstat.lexicon_count(text, removepunct=True),
                "avg_sentence_length": textstat.avg_sentence_length(text)
            }
            return metrics
        except Exception as e:
            return {"error": str(e)}

    def evaluate_proposal_quality(self, proposal_sections: Dict,
                                alignment_results: Dict) -> List[EvaluationResult]:
        """
        Evaluate proposal quality against defined criteria.

        Args:
            proposal_sections: Dictionary of proposal sections
            alignment_results: Results from similarity analysis

        Returns:
            List of evaluation results
        """
        evaluation_results = []

        # Evaluate each criterion
        for criterion in self.evaluation_criteria:
            result = self._evaluate_single_criterion(
                criterion, proposal_sections, alignment_results
            )
            evaluation_results.append(result)

        return evaluation_results

    def _evaluate_single_criterion(self, criterion: EvaluationCriteria,
                                   proposal_sections: Dict,
                                   alignment_results: Dict) -> EvaluationResult:
        """
        Evaluate a single criterion.

        Args:
            criterion: Criterion to evaluate
            proposal_sections: Proposal sections
            alignment_results: Alignment analysis results

        Returns:
            Evaluation result for the criterion
        """
        criterion_name = criterion.name.lower().replace(" ", "_")

        # Use LLM for evaluation (primary method)
        if not self.use_mock_llm:
            # Special handling for alignment which needs both text and alignment results
            if criterion_name == "alignment_with_solicitation":
                return self._evaluate_with_llm(criterion, proposal_sections, alignment_results)
            elif criterion_name == "clarity_and_organization":
                # Use rule-based evaluation for clarity as it's more objective
                return self._evaluate_clarity(proposal_sections)
            else:
                # Use LLM for other criteria
                return self._evaluate_with_llm(criterion, proposal_sections)
        else:
            # Fallback to rule-based evaluation for mock mode
            if criterion_name == "alignment_with_solicitation":
                return self._evaluate_alignment(alignment_results)
            elif criterion_name == "intellectual_merit":
                return self._evaluate_intellectual_merit(proposal_sections)
            elif criterion_name == "broader_impacts":
                return self._evaluate_broader_impacts(proposal_sections)
            elif criterion_name == "feasibility":
                return self._evaluate_feasibility(proposal_sections)
            elif criterion_name == "faculty_expertise":
                return self._evaluate_faculty_expertise(proposal_sections)
            elif criterion_name == "clarity_and_organization":
                return self._evaluate_clarity(proposal_sections)
            else:
                # Default evaluation
                return self._mock_llm_evaluation(criterion, proposal_sections)

    def _evaluate_alignment(self, alignment_results: Dict) -> EvaluationResult:
        """Evaluate alignment with solicitation."""
        if not alignment_results:
            return EvaluationResult(
                criterion="Alignment with Solicitation",
                score=0.0,
                justification="No alignment analysis available",
                strengths=[],
                weaknesses=["Unable to assess alignment"],
                recommendations=["Conduct alignment analysis"]
            )

        # Calculate average alignment score
        scores = [result['score'] for result in alignment_results.values()]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Convert to 10-point scale
        score_10 = avg_score * 10

        # Generate assessment
        strengths = []
        weaknesses = []
        recommendations = []

        if avg_score > 0.5:
            strengths.append("Good overall alignment with solicitation requirements")
        elif avg_score > 0.3:
            weaknesses.append("Moderate alignment with solicitation")
            recommendations.append("Strengthen alignment by directly addressing more solicitation requirements")
        else:
            weaknesses.append("Poor alignment with solicitation")
            recommendations.append("Significant revision needed to address solicitation requirements")

        # Identify specific gaps
        low_alignment_sections = [
            section for section, result in alignment_results.items()
            if result['score'] < 0.3
        ]

        if low_alignment_sections:
            weaknesses.append(f"Low alignment in sections: {', '.join(low_alignment_sections)}")
            recommendations.append(f"Focus on improving: {', '.join(low_alignment_sections)}")

        return EvaluationResult(
            criterion="Alignment with Solicitation",
            score=score_10,
            justification=f"Average alignment score: {avg_score:.3f}",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _evaluate_intellectual_merit(self, proposal_sections: Dict) -> EvaluationResult:
        """Evaluate intellectual merit of the proposal."""
        merit_text = proposal_sections.get("Intellectual Merit", "")
        description_text = proposal_sections.get("Project Description", "")

        text = merit_text + " " + description_text

        # Simple heuristics for intellectual merit assessment
        innovation_keywords = ['innovative', 'novel', 'original', 'breakthrough', 'advance']
        significance_keywords = ['significant', 'important', 'impact', 'contribution', 'transformative']

        innovation_count = sum(1 for keyword in innovation_keywords if keyword.lower() in text.lower())
        significance_count = sum(1 for keyword in significance_keywords if keyword.lower() in text.lower())

        # Base score on presence of key concepts
        base_score = min(6.0, (innovation_count * 0.5) + (significance_count * 0.5))

        # Adjust based on text length and substance
        if len(text) > 500:
            base_score += 1.0

        score = min(10.0, base_score)

        # Generate assessment
        strengths = []
        weaknesses = []
        recommendations = []

        if score >= 7.0:
            strengths.append("Strong presentation of intellectual merit")
        elif score >= 5.0:
            strengths.append("Adequate description of intellectual merit")
            recommendations.append("Enhance description of innovative aspects")
        else:
            weaknesses.append("Insufficient discussion of intellectual merit")
            recommendations.append("Significantly expand intellectual merit section")

        return EvaluationResult(
            criterion="Intellectual Merit",
            score=score,
            justification=f"Based on analysis of innovation and significance indicators",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _evaluate_broader_impacts(self, proposal_sections: Dict) -> EvaluationResult:
        """Evaluate broader impacts of the proposal."""
        impacts_text = proposal_sections.get("Broader Impacts", "")

        # Check for key broader impacts elements
        education_keywords = ['education', 'teaching', 'curriculum', 'students', 'outreach']
        diversity_keywords = ['diversity', 'underrepresented', 'inclusive', 'equity']
        society_keywords = ['society', 'public', 'community', 'social', 'benefit']

        education_count = sum(1 for keyword in education_keywords if keyword.lower() in impacts_text.lower())
        diversity_count = sum(1 for keyword in diversity_keywords if keyword.lower() in impacts_text.lower())
        society_count = sum(1 for keyword in society_keywords if keyword.lower() in impacts_text.lower())

        # Calculate score
        base_score = min(6.0, (education_count * 0.7) + (diversity_count * 0.7) + (society_count * 0.7))

        # Adjust based on text length
        if len(impacts_text) > 300:
            base_score += 1.0

        score = min(10.0, base_score)

        strengths = []
        weaknesses = []
        recommendations = []

        if score >= 7.0:
            strengths.append("Comprehensive broader impacts section")
        elif score >= 5.0:
            strengths.append("Basic broader impacts addressed")
            recommendations.append("Expand broader impacts with specific activities")
        else:
            weaknesses.append("Insufficient broader impacts")
            recommendations.append("Develop detailed broader impacts plan")

        return EvaluationResult(
            criterion="Broader Impacts",
            score=score,
            justification=f"Based on analysis of education, diversity, and society impact elements",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _evaluate_feasibility(self, proposal_sections: Dict) -> EvaluationResult:
        """Evaluate feasibility of the proposal."""
        # Check for feasibility indicators
        budget_text = proposal_sections.get("Budget Justification", "")
        description_text = proposal_sections.get("Project Description", "")

        text = budget_text + " " + description_text

        # Look for feasibility indicators
        timeline_keywords = ['timeline', 'schedule', 'milestones', 'duration']
        resource_keywords = ['resources', 'equipment', 'facilities', 'personnel']
        methodology_keywords = ['methodology', 'approach', 'procedures', 'methods']

        timeline_count = sum(1 for keyword in timeline_keywords if keyword.lower() in text.lower())
        resource_count = sum(1 for keyword in resource_keywords if keyword.lower() in text.lower())
        methodology_count = sum(1 for keyword in methodology_keywords if keyword.lower() in text.lower())

        # Calculate score
        base_score = min(6.0, (timeline_count * 0.8) + (resource_count * 0.8) + (methodology_count * 0.8))

        score = min(10.0, base_score)

        strengths = []
        weaknesses = []
        recommendations = []

        if score >= 7.0:
            strengths.append("Well-developed feasibility plan")
        elif score >= 5.0:
            strengths.append("Basic feasibility considerations")
            recommendations.append("Expand timeline and resource details")
        else:
            weaknesses.append("Limited feasibility information")
            recommendations.append("Add detailed timeline and resource allocation")

        return EvaluationResult(
            criterion="Feasibility",
            score=score,
            justification=f"Based on analysis of timeline, resource, and methodology planning",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _evaluate_faculty_expertise(self, proposal_sections: Dict) -> EvaluationResult:
        """Evaluate faculty expertise and qualifications."""
        faculty_info = self.extract_faculty_information(proposal_sections)

        # Score based on available information
        score = 5.0  # Base score

        if faculty_info["pi"].get("name"):
            score += 1.0

        if faculty_info["co_pi"].get("name"):
            score += 0.5

        if faculty_info["expertise_areas"]:
            score += min(2.0, len(faculty_info["expertise_areas"]) * 0.5)

        if faculty_info["prior_funding"]:
            score += 1.0

        if faculty_info["publications"]:
            score += 0.5

        score = min(10.0, score)

        strengths = []
        weaknesses = []
        recommendations = []

        if score >= 7.0:
            strengths.append("Strong faculty expertise demonstrated")
        elif score >= 5.0:
            strengths.append("Adequate faculty expertise")
            recommendations.append("Provide more detail on relevant experience")
        else:
            weaknesses.append("Limited faculty expertise information")
            recommendations.append("Expand biographical sketches with relevant experience")

        return EvaluationResult(
            criterion="Faculty Expertise",
            score=score,
            justification=f"Based on analysis of faculty qualifications and experience",
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _evaluate_clarity(self, proposal_sections: Dict) -> EvaluationResult:
        """Evaluate clarity and organization of the proposal."""
        # Combine all sections for readability analysis
        full_text = " ".join(proposal_sections.values())

        readability_metrics = self.calculate_readability_metrics(full_text)

        if "error" in readability_metrics:
            # Fallback scoring
            score = 6.0
            justification = "Unable to calculate readability metrics"
        else:
            # Score based on readability metrics
            fk_grade = readability_metrics["flesch_kincaid_grade"]
            reading_ease = readability_metrics["flesch_reading_ease"]

            # Ideal scores: FK grade 12-15, Reading ease 30-50
            if 12 <= fk_grade <= 15 and 30 <= reading_ease <= 50:
                score = 8.0
            elif 10 <= fk_grade <= 18 and 20 <= reading_ease <= 60:
                score = 7.0
            else:
                score = 6.0

            justification = f"Flesch-Kincaid Grade: {fk_grade:.1f}, Reading Ease: {reading_ease:.1f}"

        strengths = []
        weaknesses = []
        recommendations = []

        if score >= 7.0:
            strengths.append("Clear and well-organized writing")
        elif score >= 6.0:
            strengths.append("Generally clear presentation")
            recommendations.append("Improve readability of complex sections")
        else:
            weaknesses.append("Clarity and organization need improvement")
            recommendations.append("Revise for better readability and structure")

        return EvaluationResult(
            criterion="Clarity and Organization",
            score=score,
            justification=justification,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _mock_llm_evaluation(self, criterion: EvaluationCriteria,
                           proposal_sections: Dict) -> EvaluationResult:
        """
        Mock LLM evaluation for testing purposes.

        Args:
            criterion: Criterion to evaluate
            proposal_sections: Proposal sections

        Returns:
            Mock evaluation result
        """
        # Simple scoring based on section presence
        sections_present = len(proposal_sections)
        base_score = min(8.0, sections_present * 0.8)

        return EvaluationResult(
            criterion=criterion.name,
            score=base_score,
            justification=f"Mock evaluation of {criterion.name}",
            strengths=[f"Basic coverage of {criterion.name}"],
            weaknesses=[f"Limited detailed analysis of {criterion.name}"],
            recommendations=[f"Enhance {criterion.name} section with more specific details"]
        )

    def calculate_overall_score(self, evaluation_results: List[EvaluationResult]) -> float:
        """
        Calculate weighted overall score from evaluation results.

        Args:
            evaluation_results: List of evaluation results

        Returns:
            Weighted overall score
        """
        total_weight = sum(criterion.weight for criterion in self.evaluation_criteria)
        weighted_sum = sum(
            result.score * criterion.weight
            for result, criterion in zip(evaluation_results, self.evaluation_criteria)
        )

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def generate_evaluation_summary(self, evaluation_results: List[EvaluationResult]) -> Dict:
        """
        Generate a summary of evaluation results.

        Args:
            evaluation_results: List of evaluation results

        Returns:
            Dictionary with evaluation summary
        """
        overall_score = self.calculate_overall_score(evaluation_results)

        # Categorize performance
        if overall_score >= 8.0:
            category = "Excellent"
            recommendation = "Strong proposal with minor improvements suggested"
        elif overall_score >= 7.0:
            category = "Good"
            recommendation = "Competitive proposal with some areas for enhancement"
        elif overall_score >= 6.0:
            category = "Fair"
            recommendation = "Moderate proposal requiring significant improvements"
        else:
            category = "Needs Improvement"
            recommendation = "Major revisions required before submission"

        # Collect all strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []

        for result in evaluation_results:
            all_strengths.extend(result.strengths)
            all_weaknesses.extend(result.weaknesses)
            all_recommendations.extend(result.recommendations)

        return {
            "overall_score": overall_score,
            "category": category,
            "recommendation": recommendation,
            "top_strengths": all_strengths[:3],  # Top 3 strengths
            "critical_weaknesses": all_weaknesses[:3],  # Top 3 weaknesses
            "priority_recommendations": all_recommendations[:5],  # Top 5 recommendations
            "detailed_results": [
                {
                    "criterion": result.criterion,
                    "score": result.score,
                    "weight": next((c.weight for c in self.evaluation_criteria if c.name == result.criterion), 0.0)
                }
                for result in evaluation_results
            ]
        }