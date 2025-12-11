"""
ResearcherMatcher class encapsulates all logic related to scoring and ranking 
individual researchers against a solicitation.
"""

import re
import time
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity

from .data_models import ResearcherMatch, MatchingResults, Solicitation


class ResearcherMatcher:
    """Handles researcher scoring and matching against solicitations."""
    
    def __init__(self):
        """Initialize matcher as stateless utility class."""
        self.alpha = 0.7  # TF-IDF weight
        self.beta = 0.3   # Dense weight
    
    def filter_eligibility(self, solicitation: Solicitation, researchers: List[str], 
                          researcher_metadata) -> List[str]:
        """Apply eligibility filtering based on solicitation requirements."""
        eligible = set(researchers)
        eligibility = solicitation.eligibility or {}
        
        # Early-career filter
        if eligibility and any('early' in str(v).lower() for v in eligibility.values() if v):
            early_career = researcher_metadata[
                researcher_metadata['first_publication_year'] >= 2015
            ]['researcher_openalex_id'].tolist()
            eligible = eligible.intersection(set(early_career))
            print(f" Applied early-career filter: {len(eligible)} remain")
        
        # Grant experience filter
        if eligibility and any('grant' in str(v).lower() or 'funding' in str(v).lower() 
                              for v in eligibility.values() if v):
            experienced = researcher_metadata[
                researcher_metadata['grant_experience_factor'] > 0
            ]['researcher_openalex_id'].tolist()
            eligible = eligible.intersection(set(experienced))
            print(f" Applied grant experience filter: {len(eligible)} remain")
        
        return list(eligible)
    
    def extract_keywords_from_skills(self, skills: List[str]) -> List[str]:
        """Extract keywords from solicitation skills using same logic as researcher topics."""
        stop_words = {'and', 'in', 'of', 'for', 'the', 'a', 'an', 'to', 'with', 'on', 'at', 'by',
                     'expertise', 'experience', 'knowledge', 'ability', 'skills', 'understanding',
                     'capacity', 'proficiency', 'e.g.', 'eg', 'including', 'such', 'as'}
        
        all_keywords = []
        
        for skill in skills:
            # Clean and split
            cleaned = re.sub(r'[^\w\s-]', ' ', skill.lower())
            words = cleaned.split()
            
            # Extract meaningful keywords
            for word in words:
                word = word.strip('-')
                if (len(word) >= 3 and
                    word not in stop_words and
                    not word.isdigit()):
                    all_keywords.append(word)
        
        return all_keywords
    
    def score_researcher(self, researcher_id: str, skills: List[str], 
                        solicitation_embedding: np.ndarray, models: Dict[str, Any], 
                        data: Dict[str, Any], debug_mode: bool = False) -> Optional[ResearcherMatch]:
        """Score a single researcher with optional debug output."""
        try:
            # Get metadata
            researcher_metadata = data['researcher_metadata']
            researcher_row = researcher_metadata[
                researcher_metadata['researcher_openalex_id'] == researcher_id
            ]
            if researcher_row.empty:
                return None
            
            researcher_name = researcher_row.iloc[0]['researcher_name']
            total_papers = int(researcher_row.iloc[0]['total_papers'])
            grant_factor = researcher_row.iloc[0]['grant_experience_factor']
            
            # Extract keywords and format with commas (same as researcher documents)
            solicitation_keywords = self.extract_keywords_from_skills(skills)
            solicitation_text = ', '.join(solicitation_keywords)
            
            if debug_mode:
                print(f"DEBUG - Researcher: {researcher_name}")
                print(f" Extracted keywords: {solicitation_keywords[:10]}...")
            
            # Calculate sparse score (TF-IDF)
            researcher_vectors = data['researcher_vectors']
            if researcher_id not in researcher_vectors:
                return None
            
            researcher_vector = researcher_vectors[researcher_id]
            tfidf_model = models['tfidf_model']
            
            # Transform solicitation text to TF-IDF space
            solicitation_tfidf = tfidf_model.transform([solicitation_text])
            
            # Calculate cosine similarity
            s_sparse = cosine_similarity(researcher_vector.reshape(1, -1), solicitation_tfidf)[0, 0]
            
            # Calculate dense score (semantic similarity)
            researcher_papers = data['evidence_index'].get(researcher_id, {})
            if not researcher_papers:
                s_dense = 0.0
            else:
                # Get all papers for this researcher
                all_papers = []
                for topic_papers in researcher_papers.values():
                    all_papers.extend(topic_papers)
                
                # Get embeddings for available papers
                conceptual_profiles = data['conceptual_profiles']
                paper_embeddings = []
                for paper_id in all_papers[:50]:  # Limit for performance
                    if paper_id in conceptual_profiles:
                        paper_embeddings.append(conceptual_profiles[paper_id])
                
                if paper_embeddings:
                    # Average paper embeddings for researcher representation
                    researcher_embedding = np.mean(paper_embeddings, axis=0)
                    # Calculate cosine similarity with solicitation
                    s_dense = cosine_similarity(
                        researcher_embedding.reshape(1, -1), 
                        solicitation_embedding.reshape(1, -1)
                    )[0, 0]
                else:
                    s_dense = 0.0
            
            # Calculate final scores
            academic_expertise_score = s_sparse  # Base academic relevance
            f_ge = min(grant_factor, 1.0)  # Grant experience factor (capped at 1.0)
            final_affinity_score = (self.alpha * s_sparse + self.beta * s_dense) * (1 + 0.1 * f_ge)
            
            return ResearcherMatch(
                researcher_id=researcher_id,
                researcher_name=researcher_name,
                academic_expertise_score=academic_expertise_score,
                s_sparse=s_sparse,
                s_dense=s_dense,
                f_ge=f_ge,
                final_affinity_score=final_affinity_score,
                total_papers=total_papers,
                eligibility_status="Eligible"
            )
            
        except Exception as e:
            if debug_mode:
                print(f"Error scoring researcher {researcher_id}: {e}")
            return None
    
    def search_researchers(self, solicitation: Solicitation, models: Dict[str, Any], 
                          data: Dict[str, Any], top_k: int = 100) -> MatchingResults:
        """Main entry point for researcher matching."""
        start_time = time.time()
        
        print(f"🔍 Analyzing solicitation: {solicitation.title}")
        print(f"📋 Skills to analyze: {len(solicitation.required_skills_checklist)}")
        
        # Get all researchers
        all_researchers = list(data['researcher_vectors'].keys())
        print(f"👥 Total researchers in database: {len(all_researchers)}")
        
        # Apply eligibility filters
        eligible_researchers = self.filter_eligibility(
            solicitation, all_researchers, data['researcher_metadata']
        )
        print(f"✅ Eligible researchers after filtering: {len(eligible_researchers)}")
        
        # Create solicitation embedding for dense scoring
        sentence_model = models['sentence_model']
        if sentence_model is not None:
            solicitation_text_for_embedding = f"{solicitation.title} {solicitation.abstract}"
            solicitation_embedding = sentence_model.encode([solicitation_text_for_embedding])[0]
        else:
            # Create dummy embedding if sentence model not available
            solicitation_embedding = np.zeros(384)  # Default embedding size
        
        # Score all eligible researchers
        matches = []
        for i, researcher_id in enumerate(eligible_researchers):
            if i % 100 == 0:
                print(f"Processing researcher {i}/{len(eligible_researchers)}...")
            
            match = self.score_researcher(
                researcher_id, 
                solicitation.required_skills_checklist, 
                solicitation_embedding,
                models, 
                data
            )
            if match:
                matches.append(match)
        
        # Sort by final affinity score
        matches.sort(key=lambda x: x.final_affinity_score, reverse=True)
        top_matches = matches[:top_k]
        
        processing_time = time.time() - start_time
        
        print(f"🎯 Found {len(top_matches)} top matches in {processing_time:.2f}s")
        
        return MatchingResults(
            solicitation_title=solicitation.title,
            eligible_researchers=len(eligible_researchers),
            total_researchers=len(all_researchers),
            top_matches=top_matches,
            skills_analyzed=solicitation.required_skills_checklist,
            processing_time_seconds=processing_time
        )
