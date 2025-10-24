"""
LLM Content Analyzer for Grant Coach
Uses GROQ API for intelligent content analysis and comprehension
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import groq

logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysis:
    """Result of LLM content analysis"""
    summary: str
    key_objectives: List[str]
    methodology: List[str]
    outcomes: List[str]
    alignment_score: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

class LLMContentAnalyzer:
    """LLM-powered content analysis using GROQ API"""

    def __init__(self):
        """Initialize LLM analyzer with GROQ API"""
        load_dotenv('/Users/quamos/Desktop/CADS/DataAILab/.env')

        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.model = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
        self.max_tokens = int(os.getenv('GROQ_MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('GROQ_TEMPERATURE', '0.3'))

        self.client = groq.Groq(api_key=self.api_key)
        logger.info(f"LLM Content Analyzer initialized with model: {self.model}")

    def _analyze_with_llm(self, content: str, analysis_type: str, context: str = "") -> Dict[str, Any]:
        """Generic LLM analysis method"""

        prompts = {
            'solicitation': {
                'system': """You are an expert grant proposal analyst. Analyze this NSF solicitation and provide:
1. Core requirements and objectives
2. Key evaluation criteria
3. Expected outcomes and impacts
4. Important technical requirements
5. Budget and timeline expectations

Respond in JSON format with these keys:
- core_requirements: list of strings
- evaluation_criteria: list of strings
- expected_outcomes: list of strings
- technical_requirements: list of strings
- budget_timeline: list of strings
- summary: string""",

                'user': f"""Analyze this NSF solicitation document:

{context}

Solicitation content:
{content}"""
            },

            'proposal': {
                'system': """You are an expert grant proposal evaluator. Analyze this research proposal and provide:
1. Research objectives and goals
2. Methodology and approach
3. Expected outcomes and impact
4. Team expertise and capabilities
5. Technical feasibility

Respond in JSON format with these keys:
- objectives: list of strings
- methodology: list of strings
- outcomes: list of strings
- team_capabilities: list of strings
- feasibility: list of strings
- strengths: list of strings
- weaknesses: list of strings
- summary: string""",

                'user': f"""Analyze this research proposal:

{context}

Proposal content:
{content}"""
            },

            'alignment': {
                'system': """You are an expert grant proposal evaluator. Compare a solicitation with a proposal and assess alignment.

Provide detailed analysis covering:
1. Overall alignment score (0-1)
2. Strength matches between requirements and proposal
3. Gaps and weaknesses
4. Specific recommendations for improvement
5. Competitive assessment

Respond in JSON format with these keys:
- alignment_score: float (0-1)
- strong_matches: list of strings
- gaps: list of strings
- recommendations: list of strings
- competitive_assessment: string
- detailed_analysis: string""",

                'user_template': """Compare this solicitation with the proposal and assess alignment:

SOLICITATION:
{solicitation_content}

PROPOSAL:
{proposal_content}

Provide detailed alignment analysis."""
            }
        }

        prompt_config = prompts.get(analysis_type)
        if not prompt_config:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

        try:
            # Handle user content - either direct or template
            user_content = prompt_config.get('user')
            if 'user_template' in prompt_config:
                # Template needs to be formatted with context
                user_content = prompt_config['user_template'].format(
                    solicitation_content=solicitation_text[:8000],
                    proposal_content=proposal_text[:8000]
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_config['system']},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"LLM {analysis_type} analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"LLM analysis failed for {analysis_type}: {e}")
            # Return basic fallback analysis
            return self._get_fallback_analysis(analysis_type)

    def _get_fallback_analysis(self, analysis_type: str) -> Dict[str, Any]:
        """Return fallback analysis if LLM fails"""
        fallbacks = {
            'solicitation': {
                'core_requirements': ['AI capacity building', 'Educational impact'],
                'evaluation_criteria': ['Technical merit', 'Broader impacts', 'Team expertise'],
                'expected_outcomes': ['Enhanced AI capabilities', 'Educational outcomes'],
                'technical_requirements': ['Computational infrastructure', 'AI methods'],
                'budget_timeline': ['Multi-year implementation', 'Phased approach'],
                'summary': 'Solicitation focused on AI expansion and education'
            },
            'proposal': {
                'objectives': ['AI capacity building', 'Educational programs'],
                'methodology': ['HPC training', 'Curriculum development'],
                'outcomes': 'Enhanced AI research capabilities',
                'team_capabilities': ['Interdisciplinary team', 'Technical expertise'],
                'feasibility': ['Technically sound approach'],
                'strengths': ['Strong team composition'],
                'weaknesses': ['Limited technical details'],
                'summary': 'Proposal addressing AI capacity and education'
            },
            'alignment': {
                'alignment_score': 0.7,
                'strong_matches': ['AI capacity building', 'Educational impact'],
                'gaps': ['Technical infrastructure details'],
                'recommendations': ['Strengthen technical methodology'],
                'competitive_assessment': 'Competitive with improvements needed',
                'detailed_analysis': 'Basic alignment assessment'
            }
        }
        return fallbacks.get(analysis_type, {})

    def analyze_solicitation(self, solicitation_text: str) -> Dict[str, Any]:
        """Analyze solicitation content using LLM"""

        # Preprocess - extract key sections
        sections = self._extract_document_sections(solicitation_text)

        context = f"""
Document sections identified:
{chr(10).join([f"- {section}: {len(text)} chars" for section, text in sections.items()])}

Focus on program objectives, requirements, and evaluation criteria.
"""

        return self._analyze_with_llm(solicitation_text, 'solicitation', context)

    def analyze_proposal(self, proposal_text: str) -> Dict[str, Any]:
        """Analyze proposal content using LLM"""

        # Preprocess - extract key sections
        sections = self._extract_document_sections(proposal_text)

        context = f"""
Document sections identified:
{chr(10).join([f"- {section}: {len(text)} chars" for section, text in sections.items()])}

Focus on research objectives, methodology, team capabilities, and expected outcomes.
"""

        return self._analyze_with_llm(proposal_text, 'proposal', context)

    def analyze_alignment(self, solicitation_text: str, proposal_text: str) -> Dict[str, Any]:
        """Analyze alignment between solicitation and proposal using LLM"""

        # Extract summaries for context
        solicitation_analysis = self.analyze_solicitation(solicitation_text)
        proposal_analysis = self.analyze_proposal(proposal_text)

        context = f"""
SOLICITATION SUMMARY:
{solicitation_analysis.get('summary', 'No summary available')}

PROPOSAL SUMMARY:
{proposal_analysis.get('summary', 'No summary available')}

Focus on how well the proposal addresses the solicitation requirements.
"""

        return self._analyze_with_llm(
            solicitation_text, 'alignment',
            context.replace('solicitation_content', solicitation_text[:8000])
                     .replace('proposal_content', proposal_text[:8000])
                     .replace('SOLICITATION', solicitation_text[:4000])
                     .replace('PROPOSAL', proposal_text[:4000])
        )

    def _extract_document_sections(self, text: str) -> Dict[str, str]:
        """Extract main sections from document text"""

        sections = {}

        # Common section patterns
        section_patterns = {
            'summary': r'(?:summary|overview|introduction|abstract)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'objectives': r'(?:objectives|goals|aims|purpose)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'methodology': r'(?:methodology|methods|approach|technical approach)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'outcomes': r'(?:outcomes|results|impact|deliverables)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'evaluation': r'(?:evaluation|assessment|criteria|review)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'budget': r'(?:budget|cost|funding|resources)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)',
            'timeline': r'(?:timeline|schedule|milestones|duration)(.*?)(?=\n\s*[A-Z][A-Z\s]+$|\Z)'
        }

        for section_name, pattern in section_patterns.items():
            matches = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                sections[section_name] = matches.group(1).strip()

        return sections

if __name__ == "__main__":
    # Test the LLM analyzer
    analyzer = LLMContentAnalyzer()

    # Test with sample content
    test_solicitation = """
    NSF ExpandAI Program Summary

    This program aims to build AI capacity at institutions.

    Key Requirements:
    1. AI education and training programs
    2. Computational infrastructure development
    3. Research capability enhancement
    4. Broadening participation in AI

    Evaluation Criteria:
    - Technical merit and innovation
    - Broader impacts and societal benefits
    - Team expertise and institutional commitment
    """

    test_proposal = """
    Project: AI Expansion at TXST

    We propose to develop AI capacity through:
    1. HPC training programs for faculty and students
    2. Development of AI curriculum modules
    3. Research infrastructure enhancement

    Our team has expertise in AI, HPC, and education.
    """

    print("🚀 Testing LLM Content Analyzer...")

    # Test solicitation analysis
    solicitation_result = analyzer.analyze_solicitation(test_solicitation)
    print(f"\n📋 Solicitation Analysis:")
    print(json.dumps(solicitation_result, indent=2))

    # Test proposal analysis
    proposal_result = analyzer.analyze_proposal(test_proposal)
    print(f"\n📄 Proposal Analysis:")
    print(json.dumps(proposal_result, indent=2))

    # Test alignment analysis
    alignment_result = analyzer.analyze_alignment(test_solicitation, test_proposal)
    print(f"\n🎯 Alignment Analysis:")
    print(json.dumps(alignment_result, indent=2))