"""
AgriGrantCoach-AFRI Source Package

Modular analysis pipeline for USDA AFRI proposal assessment.
"""

__version__ = "1.0.0"
__author__ = "DataAILab"

from .config import Config
from .data_loader import DataLoader
from .rubric_analyzer import RubricAnalyzer
from .semantic_analyzer import SemanticAnalyzer
from .team_analyzer import TeamAnalyzer
from .report_generator import ReportGenerator

__all__ = [
    'Config',
    'DataLoader',
    'RubricAnalyzer',
    'SemanticAnalyzer',
    'TeamAnalyzer',
    'ReportGenerator',
]
