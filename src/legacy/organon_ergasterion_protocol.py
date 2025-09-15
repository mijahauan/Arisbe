#!/usr/bin/env python3
"""
Organon-Ergasterion Integration Protocol

Handles the three-case handoff between Organon and Ergasterion:
1. Brand new graph (no EGI) - user creates from scratch
2. EGI without EGDF - user draws diagram to match existing logic
3. EGI + EGDF - user adjusts appearance or practices transformations

Manages dynamic constraint switching based on completion state.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from diagram_coordinator import DiagramCoordinator, ValidationMode
from egi_core_dau import RelationalGraphWithCuts


class GraphHandoffType(Enum):
    """Types of graph handoff from Organon to Ergasterion."""

    BRAND_NEW = "brand_new"  # Case 1: No EGI, no EGDF
    EGI_ONLY = "egi_only"  # Case 2: EGI exists, no EGDF
    EGI_PLUS_EGDF = "egi_plus_egdf"  # Case 3: Both EGI and EGDF exist


@dataclass
class GraphHandoffPackage:
    """Package for transferring graph data between Organon and Ergasterion."""

    handoff_type: GraphHandoffType
    graph_id: str
    metadata: Dict[str, Any]
    egi: Optional[RelationalGraphWithCuts] = None
    egdf: Optional[Dict[str, Any]] = None


@dataclass
class GraphReturnPackage:
    """Package for returning completed work from Ergasterion."""

    graph_id: str
    egi: RelationalGraphWithCuts
    egdf: Dict[str, Any]
    metadata: Dict[str, Any]
    completion_status: str
    return_destination: str = "organon"  # "organon", "agon", or "both"


class ErgasterionWorkflowManager:
    """Manages workflow state and constraint switching for different handoff types."""

    def __init__(self, coordinator: DiagramCoordinator):
        self.coordinator = coordinator
        self.current_package: Optional[GraphHandoffPackage] = None
        self.target_egi: Optional[RelationalGraphWithCuts] = None
        self.completion_state = "not_started"

    def receive_handoff(self, package: GraphHandoffPackage) -> bool:
        """Receive graph handoff from Organon and initialize appropriate workflow."""
        self.current_package = package

        if package.handoff_type == GraphHandoffType.BRAND_NEW:
            return self._initialize_case1_workflow(package)
        elif package.handoff_type == GraphHandoffType.EGI_ONLY:
            return self._initialize_case2_workflow(package)
        elif package.handoff_type == GraphHandoffType.EGI_PLUS_EGDF:
            return self._initialize_case3_workflow(package)

        return False

    def _initialize_case1_workflow(self, package: GraphHandoffPackage) -> bool:
        """Case 1: Brand new graph - user creates from scratch."""
        # Start with empty diagram
        self.coordinator.current_drawing_schema = {
            "sheet_id": "sheet",
            "cuts": [],
            "vertices": [],
            "predicates": [],
            "ligatures": [],
        }

        # Syntactic constraints only
        self.coordinator.set_validation_mode(ValidationMode.COMPOSITION)
        self.completion_state = "creating"
        return True

    def _initialize_case2_workflow(self, package: GraphHandoffPackage) -> bool:
        """Case 2: EGI exists, no EGDF - user draws diagram to match logic."""
        if not package.egi:
            return False

        # Store target EGI for comparison (but don't set as current EGI)
        self.target_egi = package.egi
        self.coordinator.set_target_egi(package.egi)

        # Start with completely empty diagram - user must draw to match EGI
        self.coordinator.current_drawing_schema = {
            "sheet_id": "sheet",
            "cuts": [],
            "vertices": [],
            "predicates": [],
            "ligatures": [],
        }

        # Clear any existing EGI so current shows as empty
        self.coordinator.egi = None

        # Initialize empty scene for drawing
        self.coordinator.initialize_empty_scene()

        # Syntactic constraints only until diagram matches EGI
        self.coordinator.set_validation_mode(ValidationMode.COMPOSITION)
        self.completion_state = "matching_egi"
        return True

    def _initialize_case3_workflow(self, package: GraphHandoffPackage) -> bool:
        """Case 3: EGI + EGDF exist - user adjusts appearance or practices."""
        if not package.egi or not package.egdf:
            return False

        # Load existing diagram
        self.coordinator.egi = package.egi
        success = self.coordinator.load_from_egdf(package.egdf)

        if not success:
            return False

        # Full constraints from the start
        self.coordinator.set_validation_mode(ValidationMode.PRACTICE)
        self.completion_state = "ready_for_practice"
        return True

    def check_completion_state(self) -> str:
        """Check and update completion state, potentially switching constraint modes."""
        if not self.current_package:
            return self.completion_state

        if self.current_package.handoff_type == GraphHandoffType.EGI_ONLY:
            # Case 2: Check if diagram now matches target EGI
            if self.completion_state == "matching_egi":
                current_egi = self.coordinator.generate_egi_from_diagram()
                if current_egi and self._egi_equivalent(current_egi, self.target_egi):
                    self.completion_state = "egi_matched_pending_confirmation"
            elif self.completion_state == "egi_matched_confirmed":
                # User has confirmed the match - enable practice mode
                self.coordinator.set_validation_mode(ValidationMode.PRACTICE)

        elif self.current_package.handoff_type == GraphHandoffType.BRAND_NEW:
            # Case 1: Check if user has created meaningful content
            if self.completion_state == "creating":
                if self._has_meaningful_content():
                    self.completion_state = "content_created"

        return self.completion_state

    def confirm_egi_match(self) -> bool:
        """Confirm that the user accepts the EGI match and replace drawing IDs with target IDs."""
        if self.completion_state != "egi_matched_pending_confirmation":
            return False

        # Replace current drawing IDs with target EGI IDs
        success = self.coordinator.replace_drawing_ids_with_target_egi_ids(
            self.target_egi
        )
        if success:
            self.completion_state = "egi_matched_confirmed"
            return True
        return False

    def is_egi_match_pending_confirmation(self) -> bool:
        """Check if EGI match is pending user confirmation."""
        return self.completion_state == "egi_matched_pending_confirmation"

    def create_return_package(
        self, completion_status: str = "completed"
    ) -> GraphReturnPackage:
        """Create return package with current state.

        Args:
            completion_status: Status of the work (completed, in_progress, etc.)
        """
        if not self.current_package:
            raise ValueError("No active handoff package to return")

        # Get current EGI and EGDF from coordinator
        current_egi = self.coordinator.get_current_egi()
        current_egdf = self.coordinator.export_to_egdf()

        return GraphReturnPackage(
            graph_id=self.current_package.graph_id,
            egi=current_egi,
            egdf=current_egdf,
            metadata=self.current_package.metadata,
            completion_status=completion_status,
            return_destination="organon",
        )

    def _egi_equivalent(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Check if two EGI structures are equivalent."""
        try:
            # Compare basic structure
            if len(egi1.V) != len(egi2.V) or len(egi1.E) != len(egi2.E):
                return False

            # Compare nu mappings
            if len(egi1.nu) != len(egi2.nu):
                return False

            return True

        except Exception:
            return False

    def _has_meaningful_content(self) -> bool:
        """Check if diagram has meaningful content for Case 1."""
        schema = self.coordinator.current_drawing_schema
        return (
            len(schema["predicates"]) > 0
            or len(schema["vertices"]) > 0
            or len(schema["cuts"]) > 0
        )

    def _determine_completion_status(self) -> str:
        """Determine completion status for return package."""
        if self.current_package.handoff_type == GraphHandoffType.BRAND_NEW:
            return (
                "completed"
                if self.completion_state == "content_created"
                else "in_progress"
            )
        elif self.current_package.handoff_type == GraphHandoffType.EGI_ONLY:
            return (
                "completed"
                if self.completion_state == "egi_matched_confirmed"
                else "in_progress"
            )
        elif self.current_package.handoff_type == GraphHandoffType.EGI_PLUS_EGDF:
            return "practice_session"
        return "in_progress"


class OrganonErgasterionBridge:
    """Bridge interface for communication between Organon and Ergasterion."""

    @staticmethod
    def create_handoff_package(
        graph_id: str,
        metadata: Dict[str, Any],
        egi: Optional[RelationalGraphWithCuts] = None,
        egdf: Optional[Dict[str, Any]] = None,
    ) -> GraphHandoffPackage:
        """Create appropriate handoff package based on available data."""

        # Determine handoff type
        if egi is None and egdf is None:
            handoff_type = GraphHandoffType.BRAND_NEW
        elif egi is not None and egdf is None:
            handoff_type = GraphHandoffType.EGI_ONLY
        elif egi is not None and egdf is not None:
            handoff_type = GraphHandoffType.EGI_PLUS_EGDF
        else:
            raise ValueError("Invalid combination: EGDF without EGI not supported")

        return GraphHandoffPackage(
            handoff_type=handoff_type,
            graph_id=graph_id,
            metadata=metadata,
            egi=egi,
            egdf=egdf,
        )
