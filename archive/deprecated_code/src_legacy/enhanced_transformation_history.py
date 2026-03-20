"""
Enhanced EGI Transformation History with Collaboration Support

Extends the basic transformation history with collaboration metadata,
enhanced provenance tracking, and advanced branching capabilities.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from frozendict import frozendict

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egi_transformation_history import (
    HistoryBranch,
    HistoryBranchType,
    LogicalProvenance,
    StateSnapshot,
    TransformationStep,
    TransformationStatus
)


@dataclass(frozen=True)
class CollaborationMetadata:
    """Metadata for collaborative transformation history."""
    
    contributors: List[str]
    creation_timestamp: str
    last_modified: str
    version: str
    tags: List[str]
    description: str


@dataclass(frozen=True)
class EnhancedEGITransformationHistory:
    """Enhanced transformation history with collaboration support."""
    
    history_id: str
    initial_egi: RelationalGraphWithCuts
    branches: Dict[str, HistoryBranch]
    current_branch_id: str
    collaboration_metadata: CollaborationMetadata
    logical_provenance: LogicalProvenance
    
    def get_current_branch(self) -> HistoryBranch:
        """Get the currently active branch."""
        return self.branches[self.current_branch_id]
    
    def get_current_state(self) -> RelationalGraphWithCuts:
        """Get the current EGI state."""
        current_branch = self.get_current_branch()
        if current_branch.steps:
            return current_branch.steps[-1].target_egi
        return self.initial_egi
    
    def add_step(self, step: TransformationStep) -> 'EnhancedEGITransformationHistory':
        """Add a transformation step to the current branch."""
        current_branch = self.get_current_branch()
        updated_steps = current_branch.steps + [step]
        updated_branch = current_branch.with_steps(updated_steps)
        updated_branches = {**self.branches, self.current_branch_id: updated_branch}
        
        return EnhancedEGITransformationHistory(
            history_id=self.history_id,
            initial_egi=self.initial_egi,
            branches=updated_branches,
            current_branch_id=self.current_branch_id,
            collaboration_metadata=self.collaboration_metadata,
            logical_provenance=self.logical_provenance
        )
    
    def create_branch(self, branch_id: str, branch_type: HistoryBranchType, 
                     branch_point_step_id: Optional[str] = None) -> 'EnhancedEGITransformationHistory':
        """Create a new branch from the current state."""
        new_branch = HistoryBranch(
            branch_id=branch_id,
            branch_type=branch_type,
            parent_branch_id=self.current_branch_id,
            branch_point_step_id=branch_point_step_id,
            steps=[],
            metadata={}
        )
        
        updated_branches = {**self.branches, branch_id: new_branch}
        
        return EnhancedEGITransformationHistory(
            history_id=self.history_id,
            initial_egi=self.initial_egi,
            branches=updated_branches,
            current_branch_id=branch_id,
            collaboration_metadata=self.collaboration_metadata,
            logical_provenance=self.logical_provenance
        )


# Export formats for proof sequences
class ProofExportFormat:
    """Supported formats for proof export."""
    
    JSON = "json"
    YAML = "yaml"
    LATEX = "latex"
    MARKDOWN = "markdown"
