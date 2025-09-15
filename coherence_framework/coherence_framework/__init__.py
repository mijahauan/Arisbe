"""
AI Coherence Framework - Standalone Package

A comprehensive framework for maintaining codebase coherence when projects
exceed AI assistant context windows.
"""

__version__ = "1.0.0"
__author__ = "AI Development Team"

from .core.context_awareness import ContextAwarenessSystem
from .core.quality_gates import QualityGateSystem
from .core.smart_git import SmartCommitSystem
from .core.living_docs import LivingDocumentationSystem
from .analyzers.function_indexer import FunctionIndexer
from .analyzers.coherence_analyzer import CoherenceAnalyzer
from .cli.project_initializer import ProjectInitializer

__all__ = [
    "ContextAwarenessSystem",
    "QualityGateSystem", 
    "SmartCommitSystem",
    "LivingDocumentationSystem",
    "FunctionIndexer",
    "CoherenceAnalyzer",
    "ProjectInitializer",
]
