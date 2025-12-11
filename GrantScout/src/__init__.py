"""
GrantScout Source Package
==========================
"""

from .ingester import DocumentIngester, SmartChunker
from .faculty_bot import FacultyBot
from .evaluator import CompetencyEngine, RubricCriterion, EvaluationResult
from .reporter import ReportGenerator

__all__ = [
    'DocumentIngester',
    'SmartChunker',
    'FacultyBot',
    'CompetencyEngine',
    'RubricCriterion',
    'EvaluationResult',
    'ReportGenerator'
]
