"""
Researcher Expertise Analyzer for Grant Coach
Analyzes researcher publications against solicitation requirements
"""

import json
from typing import List, Dict, Set
from dataclasses import dataclass
from collections import Counter
import logging

from simple_openalex import SimpleOpenAlexClient
from llm_personnel_extractor import LLMPersonnelExtractor

logger = logging.getLogger(__name__)

@dataclass
class ExpertiseMatch:
    """Represents expertise matching results"""
    researcher_name: str
    role: str
    total_publications: int
    total_citations: int
    expertise_keywords: List[str]
    relevant_publications: List[Dict]
    alignment_score: float
    matching_keywords: List[str]

class ResearcherExpertiseAnalyzer:
    """Analyzes researcher expertise against solicitation requirements"""

    def __init__(self, openalex_email: str = 'grantcoach@example.com'):
        self.openalex_client = SimpleOpenAlexClient(email=openalex_email)
        self.personnel_extractor = LLMPersonnelExtractor()

        # Define solicitation requirement keywords
        self.requirement_keywords = {
            "AI capacity building": [
                "artificial intelligence", "machine learning", "deep learning", "neural networks",
                "AI education", "AI training", "AI curriculum", "AI methods",
                "high performance computing", "HPC", "computing infrastructure",
                "GPU computing", "parallel computing", "distributed computing",
                "AI research infrastructure", "computational resources",
                "AI capacity", "AI capabilities", "AI development"
            ],
            "Educational impact": [
                "education", "curriculum", "teaching", "learning", "students",
                "academic", "university", "higher education", "STEM education",
                "student training", "faculty development", "educational outcomes",
                "course development", "academic programs", "educational research",
                "pedagogy", "instruction", "educational materials"
            ],
            "Research infrastructure": [
                "research infrastructure", "computing resources", "data infrastructure",
                "laboratory", "research facilities", "equipment", "tools",
                "research computing", "data storage", "networking", "hardware",
                "software infrastructure", "research platforms", "cyberinfrastructure"
            ],
            "Faculty development": [
                "faculty development", "faculty training", "professional development",
                "academic development", "faculty support", "faculty mentoring",
                "faculty workshops", "faculty programs", "academic advancement",
                "faculty education", "teaching development", "research development"
            ],
            "Student workforce development": [
                "student development", "workforce development", "student training",
                "student research", "student mentoring", "internships",
                "student careers", "STEM workforce", "student pipeline",
                "student success", "career development", "workforce preparation"
            ],
            "Diversity and inclusion": [
                "diversity", "inclusion", "equity", "underrepresented",
                "minority", "women", "Hispanic", "African American", "diversification",
                "inclusive", "broadening participation", "diverse perspectives",
                "cultural diversity", "equal opportunity", "access"
            ],
            "Broader impacts": [
                "broader impacts", "societal impact", "community engagement",
                "public understanding", "science communication", "outreach",
                "social impact", "economic impact", "educational outreach",
                "knowledge transfer", "technology transfer", "public engagement"
            ],
            "Interdisciplinary collaboration": [
                "interdisciplinary", "multidisciplinary", "cross-disciplinary",
                "collaboration", "cooperation", "partnership", "team science",
                "cross-disciplinary research", "interdisciplinary research",
                "collaborative research", "multidisciplinary approach"
            ]
        }

    def analyze_researchers(self, personnel_text: str) -> List[ExpertiseMatch]:
        """Analyze expertise of all researchers in personnel text"""

        # Extract researchers
        researchers = self.personnel_extractor.extract_personnel(personnel_text)

        print(f"Analyzing expertise for {len(researchers)} researchers...")

        expertise_matches = []

        for researcher in researchers:
            print(f"Analyzing: {researcher.name} ({researcher.role})")

            try:
                # Try multiple name variations for OpenAlex search
                name_variations = self._get_name_variations(researcher.name)
                profile = None

                for name_variant in name_variations:
                    profile = self.openalex_client.search_researcher(
                        name_variant,
                        researcher.department
                    )
                    if profile:
                        print(f"✅ Found {researcher.name} as: {profile.display_name}")
                        break

                if not profile:
                    print(f"⚠️ {researcher.name} not found in OpenAlex")
                    continue

                # Get recent publications (2018-2025)
                recent_works = self.openalex_client.get_researcher_works(
                    profile.id,
                    from_year=2018,
                    limit=100
                )

                # Analyze expertise match
                match = self._analyze_expertise_match(
                    researcher, profile, recent_works
                )

                expertise_matches.append(match)

                print(f"✅ {researcher.name}: {match.alignment_score:.2f} alignment score")

            except Exception as e:
                print(f"❌ Error analyzing {researcher.name}: {e}")
                continue

        return expertise_matches

    def _get_name_variations(self, name: str) -> List[str]:
        """Generate name variations for OpenAlex search"""

        variations = [name]

        # Handle cases where last name might be split
        if ' ' in name:
            parts = name.split()
            if len(parts) >= 2:
                # Try first name + last name only
                variations.append(f"{parts[0]} {parts[-1]}")

                # Try last name only
                variations.append(parts[-1])

        return variations

    def _analyze_expertise_match(self, researcher, profile, recent_works) -> ExpertiseMatch:
        """Analyze expertise match for a single researcher"""

        # Extract all keywords from publications
        all_keywords = []
        for work in recent_works:
            all_keywords.extend([kw.lower() for kw in work.concepts])

        # Count keyword frequency
        keyword_counter = Counter(all_keywords)

        # Find matching keywords with solicitation requirements
        matching_keywords = set()
        for requirement_keywords in self.requirement_keywords.values():
            for req_keyword in requirement_keywords:
                if req_keyword.lower() in [kw.lower() for kw in all_keywords]:
                    matching_keywords.add(req_keyword)

        # Calculate alignment score
        alignment_score = self._calculate_alignment_score(
            researcher, profile, recent_works, matching_keywords
        )

        # Get relevant publications (those with matching keywords)
        relevant_publications = []
        for work in recent_works:
            work_keywords = [kw.lower() for kw in work.concepts]
            if any(req_keyword.lower() in work_keywords
                   for requirement_keywords in self.requirement_keywords.values()
                   for req_keyword in requirement_keywords):
                relevant_publications.append({
                    'title': work.title,
                    'year': work.publication_year,
                    'citations': work.citation_count,
                    'concepts': work.concepts
                })

        return ExpertiseMatch(
            researcher_name=researcher.name,
            role=researcher.role,
            total_publications=profile.works_count,
            total_citations=profile.cited_by_count,
            expertise_keywords=[kw for kw, count in keyword_counter.most_common(10)],
            relevant_publications=relevant_publications[:10],  # Top 10 relevant
            alignment_score=alignment_score,
            matching_keywords=list(matching_keywords)
        )

    def _calculate_alignment_score(self, researcher, profile, recent_works, matching_keywords) -> float:
        """Calculate alignment score based on multiple factors"""

        score = 0.0

        # Publication volume factor (max 0.2)
        if profile.works_count > 50:
            score += 0.2
        elif profile.works_count > 20:
            score += 0.15
        elif profile.works_count > 10:
            score += 0.1

        # Citation impact factor (max 0.2)
        if profile.cited_by_count > 500:
            score += 0.2
        elif profile.cited_by_count > 200:
            score += 0.15
        elif profile.cited_by_count > 50:
            score += 0.1

        # Recent activity factor (max 0.2)
        recent_years = [w for w in recent_works if w.publication_year >= 2020]
        if len(recent_years) > 10:
            score += 0.2
        elif len(recent_years) > 5:
            score += 0.15
        elif len(recent_years) > 2:
            score += 0.1

        # Keyword relevance factor (max 0.4)
        keyword_density = len(matching_keywords) / max(len(recent_works), 1)
        score += min(keyword_density * 2, 0.4)  # Cap at 0.4

        return min(score, 1.0)

    def generate_team_expertise_report(self, expertise_matches: List[ExpertiseMatch]) -> Dict:
        """Generate comprehensive team expertise report"""

        if not expertise_matches:
            return {
                'error': 'No researcher expertise data available',
                'researchers_analyzed': 0
            }

        # Sort by alignment score
        expertise_matches.sort(key=lambda x: x.alignment_score, reverse=True)

        # Calculate team statistics
        total_publications = sum(m.total_publications for m in expertise_matches)
        total_citations = sum(m.total_citations for m in expertise_matches)
        avg_alignment = sum(m.alignment_score for m in expertise_matches) / len(expertise_matches)

        # Aggregate expertise keywords
        all_keywords = []
        for match in expertise_matches:
            all_keywords.extend(match.expertise_keywords)

        top_keywords = Counter(all_keywords).most_common(20)

        # Role distribution
        role_counts = {}
        for match in expertise_matches:
            role_counts[match.role] = role_counts.get(match.role, 0) + 1

        return {
            'team_summary': {
                'researchers_analyzed': len(expertise_matches),
                'total_publications': total_publications,
                'total_citations': total_citations,
                'average_alignment_score': avg_alignment,
                'top_expertise_keywords': [kw for kw, count in top_keywords],
                'role_distribution': role_counts
            },
            'researchers': [
                {
                    'name': match.researcher_name,
                    'role': match.role,
                    'alignment_score': match.alignment_score,
                    'publications': match.total_publications,
                    'citations': match.total_citations,
                    'expertise_keywords': match.expertise_keywords[:5],
                    'matching_requirement_keywords': match.matching_keywords,
                    'relevant_publications': match.relevant_publications[:5]
                }
                for match in expertise_matches
            ]
        }

if __name__ == "__main__":
    # Test the analyzer
    import fitz
    import re

    # Get personnel text from PDF
    def get_personnel_text():
        doc = fitz.open('/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/TXST_NSFExpandAI_2334268 Project Description.pdf')
        full_text = ''

        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()

        # Get the full personnel section
        personnel_pattern = r'(4\.\s*PERSONNEL)([\s\S]*?)(?=\n\s*\d+\.\s+[A-Z\s]+$|\Z)'
        match = re.search(personnel_pattern, full_text, re.IGNORECASE)

        if match:
            return match.group(2).strip()
        else:
            return None

    # Run analysis
    analyzer = ResearcherExpertiseAnalyzer()
    personnel_text = get_personnel_text()

    if personnel_text:
        print("=== STARTING EXPERTISE ANALYSIS ===")
        expertise_matches = analyzer.analyze_researchers(personnel_text)

        print("\n=== GENERATING TEAM REPORT ===")
        report = analyzer.generate_team_expertise_report(expertise_matches)

        print(json.dumps(report, indent=2))

        # Save report
        with open('/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/output/team_expertise_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Report saved with {len(expertise_matches)} researchers analyzed")
    else:
        print("❌ Failed to get personnel text")