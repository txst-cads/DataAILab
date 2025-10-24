"""
Enhanced Researcher Expertise Analyzer for Grant Coach
Advanced concept-based expertise analysis with TF-IDF and semantic understanding

Based on comprehensive OpenAlex API research:
================================================================
CONCEPTS VS KEYWORDS RESEARCH FINDINGS:
- OpenAlex uses CONCEPTS (not keywords) as primary categorization method
- Concepts are NOT deprecated - they're the recommended approach
- CONCEPT STRUCTURE: display_name, score (0-1 importance), level (0-5 hierarchy), wikidata_id
- LEVEL HIERARCHY:
    * Level 0 = Most general (e.g., "Computer science")
    * Level 5 = Most specific (e.g., "Deep learning")
- ENHANCED PROCESSING:
    * TF-IDF-inspired scoring for concept importance
    * Frequency analysis across all researcher publications
    * Level-based weighting (more specific = higher relevance)
    * OpenAlex score integration for domain importance

BEST PRACTICES FOR EXPERTISE ANALYSIS:
================================================================
1. Use concepts from all publications (not just author profile)
2. Apply TF-IDF-inspired scoring: tf * score * level_weight
3. Prioritize specific concepts (higher levels) for expertise
4. Use semantic matching for solicitation requirements
5. Aggregate frequency across entire publication corpus
"""

import json
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
import math
import logging

from simple_openalex import SimpleOpenAlexClient
from llm_personnel_extractor import LLMPersonnelExtractor

logger = logging.getLogger(__name__)

@dataclass
class Concept:
    """Enhanced concept representation from OpenAlex"""
    display_name: str
    score: float  # OpenAlex concept score (importance)
    level: int  # Concept hierarchy level (0-5)
    wikidata_id: str = None
    frequency: int = 0  # Frequency in researcher's work
    relevance_score: float = 0.0  # Relevance to solicitation

@dataclass
class ExpertiseAnalysis:
    """Enhanced expertise analysis result"""
    researcher_name: str
    role: str
    total_publications: int
    total_citations: int
    top_concepts: List[Concept]  # Top concepts with scores
    concept_distribution: Dict[str, float]  # Concept category distribution
    alignment_score: float
    matching_concepts: List[str]
    relevant_publications: List[Dict]
    research_focus_areas: List[str]  # Derived research focus areas

class EnhancedExpertiseAnalyzer:
    """Enhanced researcher expertise analyzer with advanced concept processing"""

    def __init__(self, openalex_email: str = 'grantcoach@example.com'):
        self.openalex_client = SimpleOpenAlexClient(email=openalex_email)
        self.personnel_extractor = LLMPersonnelExtractor()

        # Enhanced solicitation requirement mapping with semantic categories
        self.requirement_categories = {
            "AI capacity building": {
                "core": ["artificial intelligence", "machine learning", "deep learning",
                          "neural networks", "AI algorithms", "AI methods"],
                "infrastructure": ["high performance computing", "HPC", "computing infrastructure",
                               "GPU computing", "parallel computing", "distributed computing",
                               "cloud computing", "research infrastructure", "computational resources"],
                "applications": ["AI applications", "AI tools", "AI software",
                             "AI platforms", "AI systems", "AI deployment"]
            },
            "Educational impact": {
                "core": ["education", "curriculum", "teaching", "learning", "pedagogy"],
                "academic": ["university", "higher education", "STEM education", "academic programs"],
                "development": ["faculty development", "student training", "educational outcomes",
                             "course development", "instructional design"]
            },
            "Research infrastructure": {
                "facilities": ["research facilities", "laboratory", "equipment", "tools"],
                "computing": ["data infrastructure", "research computing", "data storage",
                            "networking", "hardware", "software infrastructure"],
                "resources": ["research platforms", "cyberinfrastructure", "research resources",
                             "technical infrastructure"]
            },
            "Broader impacts": {
                "societal": ["social impact", "community engagement", "public understanding"],
                "educational": ["science communication", "educational outreach", "knowledge transfer"],
                "economic": ["economic impact", "technology transfer", "commercialization"],
                "community": ["community development", "public engagement", "outreach programs"]
            },
            "Faculty development": {
                "training": ["faculty development", "faculty training", "professional development"],
                "support": ["academic development", "faculty support", "faculty mentoring"],
                "programs": ["faculty workshops", "faculty programs", "academic advancement"]
            },
            "Student workforce development": {
                "training": ["student development", "workforce development", "student training"],
                "research": ["student research", "student mentoring", "internships"],
                "careers": ["student careers", "STEM workforce", "career development",
                           "workforce preparation"]
            },
            "Diversity and inclusion": {
                "groups": ["diversity", "inclusion", "equity", "underrepresented"],
                "focus": ["minority", "women", "Hispanic", "African American", "diversification"],
                "approaches": ["inclusive", "broadening participation", "diverse perspectives",
                             "cultural diversity", "equal opportunity", "access"]
            },
            "Interdisciplinary collaboration": {
                "approaches": ["interdisciplinary", "multidisciplinary", "cross-disciplinary"],
                "methods": ["collaboration", "cooperation", "partnership", "team science"],
                "research": ["cross-disciplinary research", "interdisciplinary research",
                           "collaborative research", "multidisciplinary approach"]
            }
        }

        # Build comprehensive keyword list for matching
        self.all_requirement_keywords = set()
        for category, subcats in self.requirement_categories.items():
            for subcat_keywords in subcats.values():
                self.all_requirement_keywords.update([kw.lower() for kw in subcat_keywords])

    def analyze_researchers(self, personnel_text: str) -> List[ExpertiseAnalysis]:
        """Analyze expertise of all researchers in personnel text"""

        # Extract researchers
        researchers = self.personnel_extractor.extract_personnel(personnel_text)

        print(f"🔍 Analyzing expertise for {len(researchers)} researchers...")

        expertise_analyses = []
        for researcher in researchers:
            try:
                print(f"   🔍 Analyzing: {researcher.name} ({researcher.role})")

                # Get OpenAlex profile
                profile = self.openalex_client.search_researcher(
                    researcher.name,
                    institution=researcher.department
                )

                if not profile:
                    print(f"   ⚠️ No profile found for {researcher.name}")
                    continue

                # Get recent works
                recent_works = self.openalex_client.get_researcher_works(
                    profile.id, from_year=2018, limit=100
                )

                print(f"   ✅ Found: {len(recent_works)} publications")

                # Enhanced analysis with concept processing
                analysis = self._analyze_expertise_enhanced(researcher, profile, recent_works)

                print(f"   ✅ Alignment score: {analysis.alignment_score:.3f}")
                expertise_analyses.append(analysis)

            except Exception as e:
                print(f"   ❌ Error analyzing researcher: {e}")
                continue

        return expertise_analyses

    def _analyze_expertise_enhanced(self, researcher, profile, recent_works) -> ExpertiseAnalysis:
        """Enhanced expertise analysis with concept processing"""

        # Process concepts from OpenAlex works
        all_concepts = self._extract_concepts_from_works(recent_works)

        # Calculate concept frequency and importance
        concepts_with_scores = self._calculate_concept_importance(all_concepts)

        # Derive research focus areas
        research_focus = self._derive_research_focus(concepts_with_scores)

        # Match against solicitation requirements using enhanced matching
        (matching_concepts, alignment_score) = self._calculate_enhanced_alignment(
            concepts_with_scores, self.all_requirement_keywords
        )

        # Get relevant publications with semantic matching
        relevant_publications = self._get_semantically_relevant_publications(
            recent_works, matching_concepts, self.requirement_categories
        )

        # Create concept distribution
        concept_distribution = self._create_concept_distribution(concepts_with_scores)

        return ExpertiseAnalysis(
            researcher_name=researcher.name,
            role=researcher.role,
            total_publications=profile.works_count,
            total_citations=profile.cited_by_count,
            top_concepts=concepts_with_scores[:15],  # Top 15 concepts
            concept_distribution=concept_distribution,
            alignment_score=alignment_score,
            matching_concepts=matching_concepts,
            relevant_publications=relevant_publications[:10],  # Top 10
            research_focus_areas=research_focus[:5]  # Top 5 focus areas
        )

    def _extract_concepts_from_works(self, works: List) -> List[Concept]:
        """Extract and enhance concepts from OpenAlex works"""

        all_concepts = []

        for work in works:
            if hasattr(work, 'concepts') and work.concepts:
                for concept_data in work.concepts:
                    # Create enhanced concept object
                    concept = Concept(
                        display_name=concept_data.get('display_name', ''),
                        score=float(concept_data.get('score', 0)),
                        level=int(concept_data.get('level', 0)),
                        wikidata_id=concept_data.get('wikidata_id')
                    )
                    all_concepts.append(concept)

        return all_concepts

    def _calculate_concept_importance(self, concepts: List[Concept]) -> List[Concept]:
        """Calculate concept importance using TF-IDF-inspired scoring and OpenAlex metadata"""

        if not concepts:
            return []

        # Count frequency across all works
        concept_freq = Counter(c.display_name.lower() for c in concepts)
        total_works = len(set(c.display_name.lower() for c in concepts)) or 1

        # Calculate enhanced importance score using TF-IDF principles
        enhanced_concepts = []
        for concept in concepts:
            freq = concept_freq.get(concept.display_name.lower(), 0)

            # TF (Term Frequency): normalized frequency
            tf = freq / total_works

            # IDF-inspired weighting: lower level = more specific = higher weight
            # Level 0 (most general): weight 1.0, Level 5 (most specific): weight 3.0
            idf_weight = 1.0 + (concept.level * 0.4)  # Higher level = more specific = higher weight

            # Combined TF-IDF-inspired score with OpenAlex's importance score
            importance_score = tf * concept.score * idf_weight

            # Additional bonus for high-frequency concepts across works
            frequency_bonus = min(freq * 0.1, 1.0)  # Cap at 1.0 bonus

            final_score = importance_score + frequency_bonus

            concept.frequency = freq
            concept.relevance_score = final_score
            enhanced_concepts.append(concept)

        # Sort by importance score
        enhanced_concepts.sort(key=lambda x: x.relevance_score, reverse=True)

        return enhanced_concepts

    def _derive_research_focus(self, concepts: List[Concept]) -> List[str]:
        """Derive research focus areas from top concepts"""

        # Simple heuristics to identify research focus
        focus_keywords = {
            'Artificial Intelligence': ['artificial intelligence', 'machine learning', 'deep learning',
                                   'neural networks', 'ai', 'ml', 'computer vision'],
            'Data Science': ['data science', 'big data', 'data mining', 'data analytics',
                            'statistical analysis', 'predictive modeling'],
            'Computer Science': ['computer science', 'algorithms', 'software', 'programming',
                               'databases', 'distributed systems'],
            'Mathematics': ['mathematics', 'statistics', 'optimization', 'probability',
                         'mathematical modeling', 'applied mathematics'],
            'Engineering': ['engineering', 'signal processing', 'control systems',
                            'robotics', 'computer engineering'],
            'Life Sciences': ['biology', 'medicine', 'healthcare', 'biomedical',
                           'genomics', 'bioinformatics'],
            'Physical Sciences': ['physics', 'chemistry', 'materials science', 'optics'],
            'Social Sciences': ['psychology', 'sociology', 'economics', 'political science'],
            'Education': ['education', 'learning', 'pedagogy', 'educational technology']
        }

        # Match concepts to focus areas
        focus_scores = defaultdict(float)
        top_concepts = concepts[:20]  # Use top 20 concepts for focus analysis

        for concept in top_concepts:
            concept_text = concept.display_name.lower()
            for focus_area, keywords in focus_keywords.items():
                if any(keyword in concept_text for keyword in keywords):
                    focus_scores[focus_area] += concept.relevance_score

        # Return top focus areas
        sorted_focus = sorted(focus_scores.items(), key=lambda x: x[1], reverse=True)
        return [area for area, score in sorted_focus if score > 0]

    def _calculate_enhanced_alignment(self, concepts: List[Concept],
                                    requirement_keywords: Set[str]) -> Tuple[List[str], float]:
        """Calculate enhanced alignment using TF-IDF and semantic matching"""

        if not concepts:
            return [], 0.0

        # Create concept documents for TF-IDF
        concept_docs = []
        for concept in concepts:
            # Each concept is a document with term frequency
            doc_text = concept.display_name.lower()
            concept_docs.append(doc_text)

        # Simple TF-IDF-inspired scoring
        matching_concepts = set()
        total_alignment_score = 0.0
        matched_concepts_with_scores = []

        for concept in concepts[:30]:  # Use top 30 concepts
            concept_text = concept.display_name.lower()

            # Direct keyword matching
            direct_matches = sum(1 for req_kw in requirement_keywords
                             if req_kw in concept_text)

            # Semantic matching (partial word matches)
            semantic_matches = 0
            for req_kw in requirement_keywords:
                req_words = req_kw.split()
                for req_word in req_words:
                    if len(req_word) > 3 and req_word in concept_text:
                        semantic_matches += 1

            # Calculate match score
            match_score = (direct_matches * 2.0 + semantic_matches * 1.0) / len(requirement_keywords)
            total_alignment_score += match_score * concept.relevance_score

            if direct_matches > 0 or semantic_matches > 0:
                matching_concepts.add(concept.display_name)
                matched_concepts_with_scores.append((concept.display_name, match_score))

        # Normalize alignment score
        max_possible_score = len(concepts) * 2.0  # Theoretical maximum
        normalized_score = min(total_alignment_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        # Additional scoring factors
        score_bonus = 0.0

        # Concept diversity bonus
        if len(matching_concepts) >= 5:
            score_bonus += 0.2
        elif len(matching_concepts) >= 3:
            score_bonus += 0.1

        # High-value concept bonus
        high_value_concepts = {'artificial intelligence', 'machine learning', 'deep learning',
                             'data science', 'education', 'research infrastructure'}
        high_value_matches = sum(1 for concept in matching_concepts
                              if any(hvc in concept.lower() for hvc in high_value_concepts))

        if high_value_matches >= 2:
            score_bonus += 0.2
        elif high_value_matches >= 1:
            score_bonus += 0.1

        final_score = min(normalized_score + score_bonus, 1.0)

        # Get top matching concepts
        top_matches = sorted(matched_concepts_with_scores, key=lambda x: x[1], reverse=True)
        final_matching_concepts = [concept for concept, score in top_matches[:10]]

        return final_matching_concepts, final_score

    def _get_semantically_relevant_publications(self, works: List,
                                               matching_concepts: List[str],
                                               requirement_categories: Dict) -> List[Dict]:
        """Get publications that are semantically relevant to requirements"""

        relevant_publications = []

        for work in works:
            if not hasattr(work, 'concepts') or not work.concepts:
                continue

            work_concepts = [c.lower() for c in work.concepts]

            # Enhanced relevance calculation
            relevance_score = self._calculate_publication_relevance(
                work_concepts, matching_concepts, requirement_categories
            )

            if relevance_score > 0:
                relevant_publications.append({
                    'title': work.title,
                    'year': work.publication_year,
                    'citations': work.citation_count,
                    'concepts': work.concepts,
                    'relevance_score': relevance_score
                })

        # Sort by relevance score
        relevant_publications.sort(key=lambda x: x['relevance_score'], reverse=True)

        return relevant_publications

    def _calculate_publication_relevance(self, work_concepts: List[str],
                                          matching_concepts: List[str],
                                          requirement_categories: Dict) -> float:
        """Calculate publication relevance to solicitation requirements"""

        relevance_score = 0.0

        # Direct concept matches
        direct_matches = sum(1 for concept in work_concepts
                           if concept in matching_concepts)
        relevance_score += direct_matches * 2.0

        # Semantic category matching
        for category, subcats in requirement_categories.items():
            for subcat_keywords in subcats.values():
                category_matches = sum(1 for req_kw in subcat_keywords
                                  if any(req_kw in concept for concept in work_concepts))
                if category_matches > 0:
                    relevance_score += category_matches * 0.5

        # High-value concept bonus
        high_value_bonus = sum(1 for concept in work_concepts
                               if any(hvc in concept for hvc in ['ai', 'ml', 'education', 'infrastructure']))
        relevance_score += high_value_bonus * 1.0

        return relevance_score

    def _create_concept_distribution(self, concepts: List[Concept]) -> Dict[str, float]:
        """Create concept distribution by category"""

        distribution = defaultdict(float)
        total_relevance = sum(c.relevance_score for c in concepts)

        if total_relevance == 0:
            return {}

        # Simple categorization heuristics
        ai_keywords = {'ai', 'ml', 'artificial', 'neural', 'deep', 'learning'}
        edu_keywords = {'education', 'teaching', 'learning', 'curriculum', 'student'}
        infra_keywords = {'infrastructure', 'computing', 'hardware', 'system', 'platform'}
        data_keywords = {'data', 'analytics', 'mining', 'statistics', 'database'}

        for concept in concepts[:20]:  # Use top 20 concepts
            concept_text = concept.display_name.lower()

            if any(kw in concept_text for kw in ai_keywords):
                distribution['AI/ML'] += concept.relevance_score
            elif any(kw in concept_text for kw in edu_keywords):
                distribution['Education'] += concept.relevance_score
            elif any(kw in concept_text for kw in infra_keywords):
                distribution['Infrastructure'] += concept.relevance_score
            elif any(kw in concept_text for kw in data_keywords):
                distribution['Data'] += concept.relevance_score
            else:
                distribution['Other'] += concept.relevance_score

        # Convert to percentages
        return {cat: score/total_relevance for cat, score in distribution.items()}

    def generate_team_expertise_report(self, expertise_analyses: List[ExpertiseAnalysis]) -> Dict:
        """Generate comprehensive team expertise analysis"""

        # Aggregate team expertise
        all_concepts = []
        total_citations = sum(analysis.total_citations for analysis in expertise_analyses)
        total_publications = sum(analysis.total_publications for analysis in expertise_analyses)

        # Collect all concepts for team analysis
        for analysis in expertise_analyses:
            all_concepts.extend(analysis.top_concepts)

        # Calculate team concept frequency
        concept_freq = Counter(c.display_name for c in all_concepts)
        top_team_concepts = concept_freq.most_common(10)

        # Role distribution
        role_distribution = {}
        for analysis in expertise_analyses:
            role_distribution[analysis.role] = role_distribution.get(analysis.role, 0) + 1

        # Average alignment
        avg_alignment = sum(analysis.alignment_score for analysis in expertise_analyses) / len(expertise_analyses)

        # Identify expertise gaps and strengths
        expertise_areas = {
            'AI/ML': 0,
            'Education': 0,
            'Infrastructure': 0,
            'Data Science': 0,
            'Research Methods': 0
        }

        for analysis in expertise_analyses:
            for concept in analysis.top_concepts[:10]:
                concept_text = concept.display_name.lower()

                if any(kw in concept_text for kw in ['ai', 'ml', 'artificial', 'neural']):
                    expertise_areas['AI/ML'] += concept.relevance_score
                elif any(kw in concept_text for kw in ['education', 'teaching', 'learning']):
                    expertise_areas['Education'] += concept.relevance_score
                elif any(kw in concept_text for kw in ['infrastructure', 'computing', 'system']):
                    expertise_areas['Infrastructure'] += concept.relevance_score
                elif any(kw in concept_text for kw in ['data', 'analytics', 'statistics']):
                    expertise_areas['Data Science'] += concept.relevance_score
                else:
                    expertise_areas['Research Methods'] += concept.relevance_score

        return {
            'team_summary': {
                'researchers_analyzed': len(expertise_analyses),
                'total_publications': total_publications,
                'total_citations': total_citations,
                'average_alignment_score': avg_alignment,
                'top_team_concepts': [concept for concept, count in top_team_concepts],
                'role_distribution': role_distribution,
                'expertise_areas': dict(expertise_areas),
                'team_strengths': [],
                'team_gaps': []
            },
            'researchers': [
                {
                    'name': analysis.researcher_name,
                    'role': analysis.role,
                    'alignment_score': analysis.alignment_score,
                    'publications': analysis.total_publications,
                    'citations': analysis.total_citations,
                    'top_concepts': [
                        {
                            'display_name': concept.display_name,
                            'score': concept.score,
                            'level': concept.level,
                            'frequency': concept.frequency,
                            'relevance_score': concept.relevance_score
                        }
                        for concept in analysis.top_concepts[:10]
                    ],
                    'matching_concepts': analysis.matching_concepts,
                    'concept_distribution': analysis.concept_distribution,
                    'research_focus_areas': analysis.research_focus_areas,
                    'relevant_publications': [
                        {
                            'title': pub['title'],
                            'year': pub['year'],
                            'citations': pub['citations'],
                            'relevance_score': pub.get('relevance_score', 0)
                        }
                        for pub in analysis.relevant_publications[:5]
                    ]
                }
                for analysis in expertise_analyses
            ]
        }

if __name__ == "__main__":
    # Test the enhanced expertise analyzer
    import fitz

    # Get personnel text from PDF for testing
    def get_personnel_text():
        doc = fitz.open('/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/TXST_NSFExpandAI_2334268 Project Description.pdf')
        full_text = ''
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()

        # Extract personnel section
        personnel_pattern = r'(4\.\s*PERSONNEL)([\s\S]*?)(?=\n\s*\d+\.\s+[A-Z\s]+$|\Z)'
        match = re.search(personnel_pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(2).strip()
        return ""

    # Test the analyzer
    analyzer = EnhancedExpertiseAnalyzer()
    personnel_text = get_personnel_text()

    if personnel_text:
        results = analyzer.analyze_researchers(personnel_text)

        # Generate team report
        team_report = analyzer.generate_team_expertise_report(results)

        # Save results
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"enhanced_expertise_analysis_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(team_report, f, indent=2, default=str)

        print(f"🎉 Enhanced expertise analysis saved to: {output_file}")
        print(f"📊 Analyzed {len(results)} researchers")

        # Print summary
        team_summary = team_report['team_summary']
        print(f"📈 Team Alignment Score: {team_summary['average_alignment_score']:.3f}")
        print(f"🎯 Top Team Concepts: {team_summary['top_team_concepts'][:5]}")