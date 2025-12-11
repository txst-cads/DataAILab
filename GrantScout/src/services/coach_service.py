"""
Grant Coach Service
===================
The "Brain" of the Centralized Grant Coach system.

This service orchestrates team augmentation by:
1. Analyzing grant proposals to extract required skills
2. Diagnosing current team skill coverage
3. Using optimization algorithms to suggest new collaborators

Architecture:
- Accepts: Grant proposal draft + Current team member list
- Performs: Proposal scoring, team diagnosis, strategic augmentation
- Returns: Comprehensive coaching report with collaborator suggestions
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

from ..matching_engine import (
    ResearcherMatcher,
    TeamBuilder,
    DataLoader,
    Solicitation
)

load_dotenv()


class CoachService:
    """
    Centralized Grant Coach Service

    Integrates proposal evaluation with team augmentation recommendations.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the Coach Service.

        Args:
            data_dir: Path to directory containing researcher database artifacts
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Initialize matching engine components
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "researcher_db"

        self.data_loader = DataLoader(str(data_dir))
        self.matcher = ResearcherMatcher()
        self.team_builder = TeamBuilder()

        # Cache for loaded data (loaded on first use)
        self._models = None
        self._data = None

    def _ensure_data_loaded(self):
        """Lazy load the researcher database (only when needed)."""
        if self._models is None or self._data is None:
            print("📚 Loading researcher database...")
            all_data = self.data_loader.get_all_data()
            self._models = all_data['models']
            self._data = all_data['data']
            print(f"✅ Loaded {len(self._data['researcher_vectors'])} researchers")

    def resolve_team_member_ids(self, team_member_names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Resolve team member names to researcher IDs.

        Args:
            team_member_names: List of faculty names (e.g., ["Jane Doe", "John Smith"])

        Returns:
            Tuple of (resolved_ids, unresolved_names)
        """
        self._ensure_data_loaded()

        resolved_ids = []
        unresolved_names = []

        researcher_metadata = self._data['researcher_metadata']

        for name in team_member_names:
            # Try exact match (case-insensitive)
            matches = researcher_metadata[
                researcher_metadata['researcher_name'].str.lower() == name.lower()
            ]

            if not matches.empty:
                researcher_id = matches.iloc[0]['researcher_openalex_id']
                resolved_ids.append(researcher_id)
                print(f"  ✅ Resolved: {name} -> {researcher_id}")
            else:
                # Try partial match
                matches = researcher_metadata[
                    researcher_metadata['researcher_name'].str.contains(name, case=False, na=False)
                ]

                if not matches.empty:
                    researcher_id = matches.iloc[0]['researcher_openalex_id']
                    resolved_ids.append(researcher_id)
                    actual_name = matches.iloc[0]['researcher_name']
                    print(f"  ⚠️ Partial match: {name} -> {actual_name} ({researcher_id})")
                else:
                    unresolved_names.append(name)
                    print(f"  ❌ Could not resolve: {name}")

        return resolved_ids, unresolved_names

    def extract_skills_from_proposal(self, proposal_text: str) -> List[str]:
        """
        Use LLM to extract required skills from grant proposal text.

        Args:
            proposal_text: Full text of the grant proposal

        Returns:
            List of skill/expertise requirements
        """
        prompt = f"""You are analyzing a grant proposal to extract the required skills and expertise areas.

**Proposal Text:**
{proposal_text[:5000]}  # Limit to first 5000 chars to stay within token limits

**Your Task:**
Extract ALL technical skills, domain expertise, methodologies, and competencies that would be required to successfully execute this grant proposal.

**Output Format (JSON):**
{{
  "required_skills": [
    "skill or expertise area 1",
    "skill or expertise area 2",
    ...
  ]
}}

**Guidelines:**
- Focus on TECHNICAL and DOMAIN-SPECIFIC skills
- Include methodologies, tools, and approaches mentioned
- Include cross-disciplinary requirements
- Be specific (e.g., "machine learning for climate modeling" not just "machine learning")
- Extract 10-30 skills

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research expertise analyzer. Extract skill requirements precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            skills = result.get("required_skills", [])

            print(f"  📋 Extracted {len(skills)} required skills")
            return skills

        except Exception as e:
            print(f"  ❌ Error extracting skills: {e}")
            return []

    def calculate_team_coverage(self, current_team_ids: List[str],
                                required_skills: List[str]) -> Dict:
        """
        Calculate how well the current team covers the required skills.

        Args:
            current_team_ids: List of researcher OpenAlex IDs
            required_skills: List of required skill areas

        Returns:
            Coverage analysis dictionary
        """
        self._ensure_data_loaded()

        # Create a minimal solicitation object for matching
        solicitation = Solicitation(
            title="Team Coverage Analysis",
            abstract="Analyzing current team coverage",
            required_skills_checklist=required_skills
        )

        # Get affinity scores for current team members
        team_coverage = {}

        for researcher_id in current_team_ids:
            if researcher_id in self._data['researcher_vectors']:
                # Score this researcher
                match = self.matcher.score_researcher(
                    researcher_id,
                    required_skills,
                    solicitation_embedding=None,  # Will use TF-IDF only
                    models=self._models,
                    data=self._data
                )

                if match:
                    team_coverage[match.researcher_name] = {
                        'academic_expertise_score': match.academic_expertise_score,
                        'final_affinity_score': match.final_affinity_score,
                        'total_papers': match.total_papers
                    }

        # Calculate overall coverage metrics
        if team_coverage:
            avg_score = sum(m['final_affinity_score'] for m in team_coverage.values()) / len(team_coverage)
            max_score = max(m['final_affinity_score'] for m in team_coverage.values())
        else:
            avg_score = 0.0
            max_score = 0.0

        return {
            'team_members': team_coverage,
            'average_coverage_score': avg_score,
            'maximum_coverage_score': max_score,
            'team_size': len(team_coverage)
        }

    def suggest_augmentation_candidates(
        self,
        current_team_ids: List[str],
        required_skills: List[str],
        proposal_text: str = "",
        max_suggestions: int = 3,
        top_k_pool: int = 100
    ) -> Dict:
        """
        Suggest new collaborators to augment the current team.

        This implements the "Forced Inclusion" algorithm:
        1. Get top-K researchers for the proposal
        2. Force-include current team members
        3. Run greedy optimization initialized with current team
        4. Return top N candidates with highest marginal gain

        Args:
            current_team_ids: Current team member IDs
            required_skills: Required skill areas
            proposal_text: Full proposal text (for abstract generation)
            max_suggestions: Number of candidates to suggest (1-5)
            top_k_pool: Size of candidate pool to consider

        Returns:
            Augmentation recommendations dictionary
        """
        self._ensure_data_loaded()

        print("\n🎯 Running Team Augmentation Analysis...")
        print(f"  Current team size: {len(current_team_ids)}")
        print(f"  Required skills: {len(required_skills)}")
        print(f"  Candidate pool: {top_k_pool}")

        # Create solicitation object
        # Extract abstract from proposal (first 500 chars)
        abstract = proposal_text[:500] if proposal_text else "Team augmentation analysis"

        solicitation = Solicitation(
            title="Grant Proposal Team Augmentation",
            abstract=abstract,
            required_skills_checklist=required_skills
        )

        # Step 1: Find top-K researchers for this proposal
        print("\n  🔍 Finding candidate researchers...")
        matching_results = self.matcher.search_researchers(
            solicitation=solicitation,
            models=self._models,
            data=self._data,
            top_k=top_k_pool
        )

        # Step 2: Ensure current team members are in the pool (forced inclusion)
        print("\n  🔒 Forcing inclusion of current team members...")
        existing_ids = {match.researcher_id for match in matching_results.top_matches}

        forced_matches = []
        for team_id in current_team_ids:
            if team_id not in existing_ids:
                # Score and add current team member
                match = self.matcher.score_researcher(
                    team_id,
                    required_skills,
                    solicitation_embedding=None,
                    models=self._models,
                    data=self._data
                )
                if match:
                    forced_matches.append(match)
                    print(f"    Added: {match.researcher_name}")

        # Combine forced and top matches
        all_matches = forced_matches + matching_results.top_matches
        matching_results.top_matches = all_matches[:top_k_pool]

        # Step 3: Build affinity matrix
        print("\n  📊 Building skill affinity matrix...")
        affinity_df = self.team_builder.create_affinity_matrix(
            matching_results,
            self._models,
            self._data
        )

        # Step 4: Calculate baseline coverage with current team
        print("\n  📏 Calculating baseline team coverage...")

        # Find indices of current team members in affinity matrix
        current_team_indices = []
        for team_id in current_team_ids:
            for idx, match in enumerate(matching_results.top_matches):
                if match.researcher_id == team_id:
                    current_team_indices.append(idx)
                    break

        baseline_coverage = self.team_builder.calculate_team_coverage(
            current_team_indices,
            affinity_df
        )
        print(f"    Baseline coverage score: {baseline_coverage:.3f}")

        # Step 5: Run greedy optimization initialized with current team
        print("\n  🚀 Running greedy augmentation algorithm...")

        # Modified greedy: start with current team, add up to max_suggestions more
        augmented_team_indices = current_team_indices.copy()
        selection_history = []

        candidates = [i for i in range(len(affinity_df)) if i not in current_team_indices]

        for round_num in range(max_suggestions):
            if not candidates:
                break

            best_candidate = None
            best_gain = -1

            for candidate_idx in candidates:
                marginal_gain = self.team_builder.calculate_marginal_gain(
                    candidate_idx,
                    augmented_team_indices,
                    affinity_df
                )

                if marginal_gain > best_gain:
                    best_gain = marginal_gain
                    best_candidate = candidate_idx

            if best_candidate is not None and best_gain > 0:
                augmented_team_indices.append(best_candidate)
                candidates.remove(best_candidate)

                researcher_name = affinity_df.iloc[best_candidate]['Researcher']
                new_coverage = self.team_builder.calculate_team_coverage(
                    augmented_team_indices,
                    affinity_df
                )

                selection_history.append({
                    'round': round_num + 1,
                    'researcher': researcher_name,
                    'marginal_gain': best_gain,
                    'cumulative_coverage': new_coverage,
                    'researcher_index': best_candidate
                })

                print(f"    Round {round_num + 1}: {researcher_name} (+{best_gain:.3f})")
            else:
                print(f"    Round {round_num + 1}: No beneficial candidates remaining")
                break

        # Step 6: Compile recommendations
        final_coverage = self.team_builder.calculate_team_coverage(
            augmented_team_indices,
            affinity_df
        )

        recommendations = []
        for history in selection_history:
            idx = history['researcher_index']

            # Find the corresponding match
            matching_researcher = None
            researcher_name = affinity_df.iloc[idx]['Researcher']
            for match in matching_results.top_matches:
                if match.researcher_name == researcher_name:
                    matching_researcher = match
                    break

            if matching_researcher:
                # Get researcher details from metadata
                researcher_row = self._data['researcher_metadata'][
                    self._data['researcher_metadata']['researcher_openalex_id'] == matching_researcher.researcher_id
                ]

                if not researcher_row.empty:
                    recommendations.append({
                        'name': matching_researcher.researcher_name,
                        'researcher_id': matching_researcher.researcher_id,
                        'institution': researcher_row.iloc[0].get('institution', 'Unknown'),
                        'final_affinity_score': matching_researcher.final_affinity_score,
                        'marginal_gain': history['marginal_gain'],
                        'total_papers': matching_researcher.total_papers,
                        'rationale': f"Adds {history['marginal_gain']:.1%} skill coverage improvement"
                    })

        return {
            'baseline_coverage': baseline_coverage,
            'final_coverage': final_coverage,
            'coverage_improvement': final_coverage - baseline_coverage,
            'current_team_size': len(current_team_ids),
            'suggested_additions': len(recommendations),
            'recommendations': recommendations,
            'selection_history': selection_history
        }

    def run_full_coaching_analysis(
        self,
        proposal_text: str,
        current_team_names: List[str],
        max_suggestions: int = 3
    ) -> Dict:
        """
        Complete end-to-end coaching analysis workflow.

        Args:
            proposal_text: Full grant proposal text
            current_team_names: List of current team member names
            max_suggestions: Number of new collaborators to suggest

        Returns:
            Comprehensive coaching report
        """
        start_time = time.time()

        print("\n" + "="*60)
        print("🎓 GRANT COACH: TEAM AUGMENTATION ANALYSIS")
        print("="*60)

        # Step 1: Extract required skills from proposal
        print("\n📋 Step 1: Analyzing proposal requirements...")
        required_skills = self.extract_skills_from_proposal(proposal_text)

        # Step 2: Resolve team member names to IDs
        print("\n👥 Step 2: Resolving current team members...")
        current_team_ids, unresolved = self.resolve_team_member_ids(current_team_names)

        if unresolved:
            print(f"\n  ⚠️ Warning: {len(unresolved)} team members could not be found in database:")
            for name in unresolved:
                print(f"     - {name}")

        # Step 3: Calculate current team coverage
        print("\n📊 Step 3: Diagnosing current team coverage...")
        team_coverage = self.calculate_team_coverage(current_team_ids, required_skills)

        # Step 4: Generate augmentation recommendations
        print("\n🎯 Step 4: Generating augmentation recommendations...")
        augmentation = self.suggest_augmentation_candidates(
            current_team_ids,
            required_skills,
            proposal_text,
            max_suggestions=max_suggestions
        )

        processing_time = time.time() - start_time

        # Compile final report
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'processing_time_seconds': processing_time,
            'proposal_analysis': {
                'required_skills': required_skills,
                'total_skills': len(required_skills)
            },
            'current_team': {
                'requested_members': current_team_names,
                'resolved_members': len(current_team_ids),
                'unresolved_members': unresolved,
                'coverage_analysis': team_coverage
            },
            'augmentation_recommendations': augmentation,
            'summary': {
                'current_coverage': team_coverage['average_coverage_score'],
                'baseline_coverage': augmentation['baseline_coverage'],
                'projected_coverage': augmentation['final_coverage'],
                'coverage_improvement': augmentation['coverage_improvement'],
                'suggested_collaborators': len(augmentation['recommendations'])
            }
        }

        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE")
        print(f"   Processing time: {processing_time:.1f}s")
        print(f"   Current coverage: {augmentation['baseline_coverage']:.1%}")
        print(f"   Projected coverage: {augmentation['final_coverage']:.1%}")
        print(f"   Improvement: +{augmentation['coverage_improvement']:.1%}")
        print(f"   Suggested additions: {len(augmentation['recommendations'])}")
        print("="*60)

        return report
