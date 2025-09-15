"""Command-line interface for the AI Coherence Framework."""

from .project_initializer import ProjectInitializer
from .commands import (
    init_project,
    check_coherence,
    smart_commit,
    session_manager,
)

__all__ = [
    "ProjectInitializer",
    "init_project",
    "check_coherence", 
    "smart_commit",
    "session_manager",
]
