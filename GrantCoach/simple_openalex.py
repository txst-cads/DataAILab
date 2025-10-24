"""
Simple OpenAlex Client for Grant Coach
Simplified synchronous client for researcher profile fetching
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ResearcherProfile:
    """Simplified researcher profile"""
    id: str
    display_name: str
    works_count: int
    cited_by_count: int
    institution: Optional[str] = None
    last_known_institution: Optional[str] = None

@dataclass
class Publication:
    """Simplified publication record"""
    id: str
    title: str
    publication_year: int
    citation_count: int
    abstract: Optional[str] = None
    concepts: List[str] = None

    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []

class SimpleOpenAlexClient:
    """Simplified synchronous OpenAlex client"""

    def __init__(self, email: str, rate_limit: int = 10):
        """
        Initialize client.

        Args:
            email: Email for API identification (required by OpenAlex)
            rate_limit: Requests per second
        """
        self.base_url = "https://api.openalex.org"
        self.email = email
        self.rate_limit = rate_limit
        self.last_request_time = 0

    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """Make rate-limited request to OpenAlex API"""

        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < (1.0 / self.rate_limit):
            time.sleep((1.0 / self.rate_limit) - time_since_last)

        self.last_request_time = time.time()

        # Add email to params for API identification
        if params is None:
            params = {}
        params['mailto'] = self.email

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}

    def search_researcher(self, name: str, institution: str = None) -> Optional[ResearcherProfile]:
        """
        Search for a researcher by name.

        Args:
            name: Researcher name
            institution: Optional institution to narrow search

        Returns:
            ResearcherProfile if found, None otherwise
        """
        try:
            # Construct search query
            query = name
            if institution:
                query += f" {institution}"

            url = f"{self.base_url}/authors"
            params = {
                'search': query,
                'per-page': 5
            }

            data = self._make_request(url, params)

            if data.get('results') and len(data['results']) > 0:
                # Get the best match
                best_match = data['results'][0]

                # Extract institution info
                institution_name = None
                if best_match.get('last_known_institution') and best_match['last_known_institution'].get('display_name'):
                    institution_name = best_match['last_known_institution']['display_name']

                return ResearcherProfile(
                    id=best_match['id'],
                    display_name=best_match['display_name'],
                    works_count=best_match.get('works_count', 0),
                    cited_by_count=best_match.get('cited_by_count', 0),
                    institution=institution_name,
                    last_known_institution=institution_name
                )

            return None

        except Exception as e:
            logger.error(f"Error searching researcher {name}: {e}")
            return None

    def get_researcher_works(self, researcher_id: str, from_year: int = 2018, limit: int = 50) -> List[Publication]:
        """
        Get recent works for a researcher.

        Args:
            researcher_id: OpenAlex researcher ID
            from_year: Starting year for publications
            limit: Maximum number of works to return

        Returns:
            List of publications
        """
        try:
            url = f"{self.base_url}/works"
            params = {
                'filter': f'author.id:{researcher_id},from_publication_date:{from_year}-01-01',
                'per-page': limit,
                'sort': 'publication_date:desc'
            }

            data = self._make_request(url, params)

            publications = []
            if data.get('results'):
                for work in data['results']:
                    try:
                        # Extract concepts
                        concepts = []
                        if work.get('concepts'):
                            concepts = [concept['display_name'] for concept in work['concepts'][:5]]

                        publication = Publication(
                            id=work['id'],
                            title=work.get('title', 'Untitled'),
                            publication_year=work.get('publication_year', 2020),
                            citation_count=work.get('cited_by_count', 0),
                            abstract=work.get('abstract'),
                            concepts=concepts
                        )
                        publications.append(publication)
                    except Exception as e:
                        logger.warning(f"Error parsing work: {e}")
                        continue

            return publications

        except Exception as e:
            logger.error(f"Error getting works for {researcher_id}: {e}")
            return []

    def analyze_researcher_expertise(self, name: str, institution: str = None) -> Dict:
        """
        Comprehensive analysis of researcher expertise.

        Args:
            name: Researcher name
            institution: Optional institution

        Returns:
            Dict with researcher analysis
        """
        profile = self.search_researcher(name, institution)
        if not profile:
            return {
                'found': False,
                'name': name,
                'error': 'Researcher not found in OpenAlex'
            }

        # Get recent publications
        recent_works = self.get_researcher_works(profile.id, from_year=2018, limit=50)

        # Extract expertise keywords from concepts
        concept_freq = {}
        for work in recent_works:
            for concept in work.concepts:
                concept_freq[concept] = concept_freq.get(concept, 0) + 1

        # Sort by frequency
        top_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'found': True,
            'name': profile.display_name,
            'institution': profile.institution,
            'works_count': profile.works_count,
            'citation_count': profile.cited_by_count,
            'recent_publications': len(recent_works),
            'expertise_keywords': [concept for concept, count in top_concepts],
            'publications': [
                {
                    'title': work.title,
                    'year': work.publication_year,
                    'citations': work.citation_count,
                    'concepts': work.concepts
                }
                for work in recent_works[:10]  # Top 10 recent works
            ]
        }

if __name__ == "__main__":
    # Test the client
    client = SimpleOpenAlexClient(email='grantcoach@example.com')

    # Test with known researchers
    test_names = ['Tahir Ekin', 'Apan Qasem']

    for name in test_names:
        print(f"\n=== Analyzing {name} ===")
        analysis = client.analyze_researcher_expertise(name)
        print(json.dumps(analysis, indent=2))