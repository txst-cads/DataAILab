"""
Data models for the research team matching system.
Centralizes all dataclass definitions for type safety and clean code organization.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime


@dataclass
class ResearcherMatch:
    """Represents a single researcher match with scoring details."""
    researcher_id: str
    researcher_name: str
    academic_expertise_score: float
    s_sparse: float
    s_dense: float
    f_ge: float
    final_affinity_score: float
    total_papers: int
    eligibility_status: str


@dataclass
class MatchingResults:
    """Results from the researcher matching process."""
    solicitation_title: str
    eligible_researchers: int
    total_researchers: int
    top_matches: List[ResearcherMatch]
    skills_analyzed: List[str]
    processing_time_seconds: float


@dataclass
class TeamAssemblyResult:
    """Results from the team assembly process."""
    affinity_df: pd.DataFrame
    team_indices: List[int]
    selection_history: List[Dict]
    team_members: List[Dict]
    overall_coverage_score: float


@dataclass
class DreamTeamReport:
    """Complete dream team analysis report."""
    team_members: List[Dict]
    overall_coverage_score: float
    skill_analysis: List[Dict]
    strategic_analysis: str
    selection_history: List[Dict]
    generated_at: str


@dataclass
class Solicitation:
    """Formal solicitation object with all required fields."""
    title: str
    abstract: str
    required_skills_checklist: List[str]
    eligibility: Optional[Dict] = None
    description: Optional[str] = None
    funding_amount: Optional[str] = None
    deadline: Optional[str] = None
    program: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Solicitation':
        """Create Solicitation from dictionary data."""
        return cls(
            title=data.get('title', ''),
            abstract=data.get('abstract', ''),
            required_skills_checklist=data.get('required_skills_checklist', []),
            eligibility=data.get('eligibility'),
            description=data.get('description'),
            funding_amount=data.get('funding_amount'),
            deadline=data.get('deadline'),
            program=data.get('program')
        )
