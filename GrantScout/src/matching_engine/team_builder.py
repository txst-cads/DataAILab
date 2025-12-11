"""
TeamBuilder class contains all algorithms and logic for assembling 
the optimal team from a list of top candidates.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity

from .data_models import MatchingResults, TeamAssemblyResult


class TeamBuilder:
    """Handles optimal team assembly from candidate researchers."""
    
    def __init__(self):
        """Initialize team builder as stateless utility class."""
        pass
    
    def create_affinity_matrix(self, matching_results: MatchingResults, 
                             models: Dict[str, Any], data: Dict[str, Any]) -> pd.DataFrame:
        """Generate the researcher-skill affinity matrix."""
        print("🏗️ Creating affinity matrix...")
        
        # Get TF-IDF model and researcher vectors
        tfidf_model = models['tfidf_model']
        researcher_vectors = data['researcher_vectors']
        
        # Extract top researchers
        top_researchers = matching_results.top_matches[:50]  # Limit for performance
        researcher_ids = [match.researcher_id for match in top_researchers]
        researcher_names = [match.researcher_name for match in top_researchers]
        
        # Get skills from solicitation
        skills = matching_results.skills_analyzed
        
        # Create skill vectors using TF-IDF
        skill_vectors = []
        for skill in skills:
            # Convert skill to same format as researcher documents
            skill_text = skill.lower().replace(' ', ', ')
            skill_tfidf = tfidf_model.transform([skill_text])
            skill_vectors.append(skill_tfidf.toarray()[0])
        
        # Calculate affinity scores for each researcher-skill pair
        affinity_data = []
        
        for researcher_id, researcher_name in zip(researcher_ids, researcher_names):
            if researcher_id not in researcher_vectors:
                continue
                
            researcher_vector = researcher_vectors[researcher_id]
            researcher_affinities = []
            
            for skill_vector in skill_vectors:
                # Calculate cosine similarity
                affinity = cosine_similarity(
                    researcher_vector.reshape(1, -1),
                    skill_vector.reshape(1, -1)
                )[0, 0]
                researcher_affinities.append(affinity)
            
            affinity_data.append([researcher_name] + researcher_affinities)
        
        # Create DataFrame
        columns = ['Researcher'] + skills
        affinity_df = pd.DataFrame(affinity_data, columns=columns)
        
        print(f"✅ Created affinity matrix: {affinity_df.shape}")
        return affinity_df
    
    def calculate_team_coverage(self, team_indices: List[int], 
                               affinity_df: pd.DataFrame) -> float:
        """Calculate overall team coverage score."""
        if not team_indices:
            return 0.0
        
        # Get skill columns (exclude 'Researcher' column)
        skill_columns = [col for col in affinity_df.columns if col != 'Researcher']
        
        # Calculate maximum affinity for each skill across team members
        team_affinities = affinity_df.iloc[team_indices][skill_columns]
        max_affinities = team_affinities.max(axis=0)
        
        # Overall coverage is average of maximum affinities
        return max_affinities.mean()
    
    def calculate_marginal_gain(self, candidate_idx: int, current_team: List[int], 
                               affinity_df: pd.DataFrame) -> float:
        """Calculate marginal gain of adding a candidate to current team."""
        current_coverage = self.calculate_team_coverage(current_team, affinity_df)
        new_team = current_team + [candidate_idx]
        new_coverage = self.calculate_team_coverage(new_team, affinity_df)
        
        return new_coverage - current_coverage
    
    def dream_team_hybrid_strategy(self, affinity_df: pd.DataFrame, 
                                  max_team_size: int = 8) -> Tuple[List[int], List[Dict]]:
        """Implement the primary team selection algorithm."""
        print("🚀 Running dream team hybrid strategy...")
        
        team_indices = []
        selection_history = []
        candidates = list(range(len(affinity_df)))
        
        # Phase 1: Greedy selection for initial team
        for round_num in range(min(max_team_size, len(candidates))):
            best_candidate = None
            best_gain = -1
            
            for candidate_idx in candidates:
                if candidate_idx not in team_indices:
                    marginal_gain = self.calculate_marginal_gain(
                        candidate_idx, team_indices, affinity_df
                    )
                    
                    if marginal_gain > best_gain:
                        best_gain = marginal_gain
                        best_candidate = candidate_idx
            
            if best_candidate is not None:
                team_indices.append(best_candidate)
                researcher_name = affinity_df.iloc[best_candidate]['Researcher']
                
                selection_history.append({
                    'round': round_num + 1,
                    'researcher': researcher_name,
                    'marginal_gain': best_gain,
                    'team_coverage': self.calculate_team_coverage(team_indices, affinity_df)
                })
                
                print(f"Round {round_num + 1}: Selected {researcher_name} "
                      f"(gain: {best_gain:.3f})")
        
        final_coverage = self.calculate_team_coverage(team_indices, affinity_df)
        print(f"✅ Final team coverage: {final_coverage:.3f}")
        
        return team_indices, selection_history
    
    def assemble_team(self, matching_results: MatchingResults, 
                     models: Dict[str, Any], data: Dict[str, Any],
                     max_team_size: int = 8) -> TeamAssemblyResult:
        """Main public method for team assembly."""
        print("🏗️ Assembling dream team...")
        
        # Create affinity matrix
        affinity_df = self.create_affinity_matrix(matching_results, models, data)
        
        # Run team selection algorithm
        team_indices, selection_history = self.dream_team_hybrid_strategy(
            affinity_df, max_team_size
        )
        
        # Get team member details
        team_members = []
        for idx in team_indices:
            researcher_name = affinity_df.iloc[idx]['Researcher']
            
            # Find matching researcher from original results
            matching_researcher = None
            for match in matching_results.top_matches:
                if match.researcher_name == researcher_name:
                    matching_researcher = match
                    break
            
            if matching_researcher:
                team_members.append({
                    'name': researcher_name,
                    'researcher_id': matching_researcher.researcher_id,
                    'final_affinity_score': matching_researcher.final_affinity_score,
                    'academic_expertise_score': matching_researcher.academic_expertise_score,
                    'total_papers': matching_researcher.total_papers,
                    'team_role': f"Member {len(team_members) + 1}"
                })
        
        # Calculate overall coverage
        overall_coverage = self.calculate_team_coverage(team_indices, affinity_df)
        
        return TeamAssemblyResult(
            affinity_df=affinity_df,
            team_indices=team_indices,
            selection_history=selection_history,
            team_members=team_members,
            overall_coverage_score=overall_coverage
        )
