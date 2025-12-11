"""
Matching Engine Package
========================
Core logic from NSF Grant Matching Engine adapted for GrantScout team augmentation.

This package provides:
- Researcher matching and scoring algorithms
- Team assembly optimization
- Data loading and management
- Data models for matching results
"""

from .data_models import (
    ResearcherMatch,
    MatchingResults,
    TeamAssemblyResult,
    Solicitation
)
from .data_loader import DataLoader
from .matcher import ResearcherMatcher
from .team_builder import TeamBuilder

__all__ = [
    'ResearcherMatch',
    'MatchingResults',
    'TeamAssemblyResult',
    'Solicitation',
    'DataLoader',
    'ResearcherMatcher',
    'TeamBuilder'
]
