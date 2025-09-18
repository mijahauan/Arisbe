"""
Formal EG transformation rules implementing precise Peirce-Dau formalism.
Each rule has clear preconditions, transformations, and postconditions.
"""

import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from graph_isomorphism_engine import IsomorphismValidator
# from legacy.level_polarity_adjustment import LevelPolarityAdjuster  # Legacy component removed


class AreaPolarity(Enum):
    """Polarity of an area based on nesting depth of cuts."""

    POSITIVE = "positive"  # Even nesting depth (0, 2, 4, ...)
    NEGATIVE = "negative"  # Odd nesting depth (1, 3, 5, ...)


@dataclass
class TransformationContext:
    """Context information for applying a transformation."""

    source_egi: RelationalGraphWithCuts
    target_area: ElementID
    selected_subgraph: FrozenSet[ElementID]
    area_polarity: AreaPolarity
    nesting_depth: int


@dataclass
class TransformationResult:
    """Result of applying a transformation rule."""

    success: bool
    result_egi: Optional[RelationalGraphWithCuts]
    error_message: Optional[str]
    changes_made: Dict[str, Any]


class FormalTransformationRule(ABC):
    """Abstract base class for formal EG transformation rules."""

    @abstractmethod
    def get_rule_name(self) -> str:
        """Get the name of this transformation rule."""
        pass

    @abstractmethod
    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """Check if the rule can be applied in the given context."""
        pass

    @abstractmethod
    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply the transformation rule to create a new EGI."""
        pass

    def is_closed_subgraph(
        self, egi: RelationalGraphWithCuts, subgraph: FrozenSet[ElementID]
    ) -> bool:
        """Check if subgraph is closed per Dau's Definition (no external connections)."""
        # A subgraph is closed if no edge in the subgraph has a vertex outside the subgraph
        subgraph_edges = {e_id for e_id in subgraph if any(e.id == e_id for e in egi.E)}

        for edge_id in subgraph_edges:
            vertex_sequence = egi.nu.get(edge_id, ())
            for vertex_id in vertex_sequence:
                # If edge connects to vertex outside subgraph, it's not closed
                if vertex_id not in subgraph:
                    return False

        return True

    def calculate_area_polarity(
        self, egi: RelationalGraphWithCuts, area_id: ElementID
    ) -> Tuple[AreaPolarity, int]:
        """Calculate the polarity and nesting depth of an area."""
        # Sheet is always level 0, positive
        if area_id == egi.sheet:
            return AreaPolarity.POSITIVE, 0

        # For cut areas, count how many cuts enclose this area
        is_cut_area = any(cut.id == area_id for cut in egi.Cut)

        if is_cut_area:
            enclosing_cuts = 0
            current_area = area_id

            while True:
                containing_area = None
                for area_candidate, contents in egi.area.items():
                    if current_area in contents:
                        containing_area = area_candidate
                        break

                if containing_area is None or containing_area == egi.sheet:
                    break

                if any(cut.id == containing_area for cut in egi.Cut):
                    enclosing_cuts += 1
                    current_area = containing_area
                else:
                    break

            nesting_depth = enclosing_cuts + 1
        else:
            # For non-cut areas, this shouldn't happen in valid EGIs
            nesting_depth = 0

        polarity = (
            AreaPolarity.POSITIVE if nesting_depth % 2 == 0 else AreaPolarity.NEGATIVE
        )
        return polarity, nesting_depth


class DoubleCutInsertionRule(FormalTransformationRule):
    """DC+ - Double Cut Insertion Rule"""

    def get_rule_name(self) -> str:
        return "DC+ (Double Cut Insertion)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        DC+ can be applied in any area to enclose any subgraph (including empty).
        No specific preconditions beyond valid area and subgraph selection.
        """
        # Verify target area exists
        if context.target_area not in context.source_egi.area:
            return False, f"Target area {context.target_area} does not exist"

        # Verify selected subgraph elements exist in the target area
        area_contents = context.source_egi.area.get(context.target_area, frozenset())
        if not context.selected_subgraph.issubset(area_contents):
            return False, "Selected subgraph contains elements not in target area"

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply DC+ by inserting a double cut around selected elements."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi


            # Create two new cuts for the double cut
            outer_cut_id = ElementID("dc_outer")
            inner_cut_id = ElementID("dc_inner")

            outer_cut = Cut(outer_cut_id)
            inner_cut = Cut(inner_cut_id)

            # Get elements to enclose (if any selected, otherwise enclose all in target area)
            if context.selected_subgraph:
                elements_to_enclose = context.selected_subgraph
            else:
                # Enclose all elements in the target area
                elements_to_enclose = egi.area.get(context.target_area, frozenset())

            # Create new area mapping
            new_area_mapping = dict(egi.area)

            # Remove enclosed elements from their current area
            current_area_contents = new_area_mapping.get(
                context.target_area, frozenset()
            )
            new_area_mapping[context.target_area] = (
                current_area_contents - elements_to_enclose
            ) | frozenset([outer_cut_id])

            # Set up the double cut structure
            new_area_mapping[outer_cut_id] = frozenset([inner_cut_id])
            new_area_mapping[inner_cut_id] = elements_to_enclose

            # Add the new cuts to the cut set
            new_cuts = egi.Cut | {outer_cut, inner_cut}

            result_egi = RelationalGraphWithCuts(
                V=egi.V,
                E=egi.E,
                nu=egi.nu,
                sheet=egi.sheet,
                Cut=new_cuts,
                area=frozendict(new_area_mapping),
                rel=egi.rel,
            )

            # Add additional attributes if they exist
            if hasattr(egi, "alphabet"):
                result_egi = dataclasses.replace(result_egi, alphabet=egi.alphabet)
            if hasattr(egi, "rho"):
                result_egi = dataclasses.replace(result_egi, rho=egi.rho)

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "DC+",
                    "outer_cut": str(outer_cut_id),
                    "inner_cut": str(inner_cut_id),
                    "enclosed_elements": [str(e) for e in elements_to_enclose],
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class DoubleCutErasureRule(FormalTransformationRule):
    """DC- - Double Cut Erasure Rule"""

    def get_rule_name(self) -> str:
        return "DC- (Double Cut Erasure)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        DC- requires identifying a subgraph that has a single cut enclosing
        nothing but another single cut (which may contain content).
        """
        if len(context.selected_subgraph) != 1:
            return False, "Must select exactly one cut for DC-"

        outer_cut_id = next(iter(context.selected_subgraph))

        # Verify it's actually a cut
        if not any(cut.id == outer_cut_id for cut in context.source_egi.Cut):
            return False, "Selected element is not a cut"

        # Check what the outer cut contains
        outer_cut_contents = context.source_egi.area.get(outer_cut_id, frozenset())

        if len(outer_cut_contents) != 1:
            return False, "Outer cut must contain exactly one element for DC-"

        inner_element_id = next(iter(outer_cut_contents))

        # Verify the inner element is also a cut
        if not any(cut.id == inner_element_id for cut in context.source_egi.Cut):
            return False, "Inner element must be a cut for DC-"

        # Double cut pattern found - inner cut can contain any content
        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply DC- by removing the double cut pattern."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi
            outer_cut_id = next(iter(context.selected_subgraph))
            inner_cut_id = next(iter(egi.area.get(outer_cut_id, frozenset())))

            # Remove both cuts
            new_cuts = frozenset(
                cut for cut in egi.Cut if cut.id not in {outer_cut_id, inner_cut_id}
            )

            # Get the contents of the inner cut (these will be moved up)
            inner_cut_contents = egi.area.get(inner_cut_id, frozenset())

            # Update area mapping
            new_area_mapping = dict(egi.area)

            # Find the area containing the outer cut and move inner cut contents there
            for area_id, contents in new_area_mapping.items():
                if outer_cut_id in contents:
                    # Remove outer cut and add inner cut contents to this area
                    new_contents = (
                        contents - frozenset([outer_cut_id])
                    ) | inner_cut_contents
                    new_area_mapping[area_id] = new_contents
                    break

            # Remove the cut areas
            if outer_cut_id in new_area_mapping:
                del new_area_mapping[outer_cut_id]
            if inner_cut_id in new_area_mapping:
                del new_area_mapping[inner_cut_id]

            result_egi = RelationalGraphWithCuts(
                V=egi.V,
                E=egi.E,
                nu=egi.nu,
                sheet=egi.sheet,
                Cut=new_cuts,
                area=frozendict(new_area_mapping),
                rel=egi.rel,
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "DC-",
                    "outer_cut_removed": str(outer_cut_id),
                    "inner_cut_removed": str(inner_cut_id),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class InsertionRule(FormalTransformationRule):
    """INS - Insertion Rule"""

    def get_rule_name(self) -> str:
        return "INS (Insertion)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        INS requires a CLOSED graph to insert and a negatively-enclosed area to insert it.
        """
        if context.area_polarity != AreaPolarity.NEGATIVE:
            return (
                False,
                "Insertion only allowed in negatively-enclosed areas (odd nesting depth)",
            )

        # Verify target area exists
        if context.target_area not in context.source_egi.area:
            return False, f"Target area {context.target_area} does not exist"

        # CRITICAL: Check if subgraph to insert is closed per Dau's requirement
        if context.selected_subgraph and not self.is_closed_subgraph(
            context.source_egi, context.selected_subgraph
        ):
            return (
                False,
                "Insertion only applies to closed subgraphs (no external edge connections)",
            )

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply INS by adding the specified subgraph to the negative area."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi

            # Handle insertion of subgraph elements
            new_vertices = set(egi.V)
            new_edges = set(egi.E)
            new_nu = dict(egi.nu)
            new_rel = dict(egi.rel)

            inserted_elements = set()

            # Check if we have direct insertion details (new approach)
            if hasattr(context, "insertion_edge_id"):
                # Direct edge construction approach
                new_edge_id = context.insertion_edge_id
                relation_name = context.insertion_relation_name
                vertex_sequence = context.insertion_vertex_sequence


                # Create any missing vertices first
                for vertex_id in vertex_sequence:
                    if not any(v.id == vertex_id for v in new_vertices):
                        new_vertex = Vertex(vertex_id)
                        new_vertices.add(new_vertex)
                        inserted_elements.add(vertex_id)

                # Create the new edge
                new_edge = Edge(new_edge_id)
                new_edges.add(new_edge)
                inserted_elements.add(new_edge_id)

                # Update nu mapping with the vertex sequence
                new_nu[new_edge_id] = vertex_sequence

                # Update relation mapping
                new_rel[new_edge_id] = relation_name

            else:
                # Fallback: create simple vertices for selected elements
                for element_id in context.selected_subgraph:
                    if str(element_id).startswith("new_vertex_") or str(
                        element_id
                    ).startswith("inserted_"):
                        new_vertex = Vertex(element_id)
                        new_vertices.add(new_vertex)
                        inserted_elements.add(element_id)

            # Update area mapping
            new_area_mapping = dict(egi.area)
            current_area_contents = new_area_mapping.get(
                context.target_area, frozenset()
            )
            new_area_mapping[context.target_area] = current_area_contents | frozenset(
                inserted_elements
            )

            # Preserve rho mapping for constants
            new_rho = dict(getattr(egi, "rho", {}))

            result_egi = RelationalGraphWithCuts(
                V=frozenset(new_vertices),
                E=frozenset(new_edges),
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel),
            )

            # Add rho mapping if it exists
            if new_rho:
                result_egi = dataclasses.replace(result_egi, rho=frozendict(new_rho))

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "INS",
                    "inserted_elements": list(inserted_elements),
                    "target_area": str(context.target_area),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class ErasureRule(FormalTransformationRule):
    """ERA - Erasure Rule"""

    def get_rule_name(self) -> str:
        return "ERA (Erasure)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        ERA requires a positively-enclosed area and a CLOSED subgraph therein to erase.
        """
        if context.area_polarity != AreaPolarity.POSITIVE:
            return (
                False,
                "Erasure only allowed in positively-enclosed areas (even nesting depth)",
            )

        # Verify target area exists
        if context.target_area not in context.source_egi.area:
            return False, f"Target area {context.target_area} does not exist"

        # Verify selected subgraph exists in the area
        area_contents = context.source_egi.area.get(context.target_area, frozenset())

        # For cut erasure, we need to expand the selected subgraph to include cut contents
        expanded_subgraph = set(context.selected_subgraph)
        for element_id in context.selected_subgraph:
            # If this element is a cut, include all its contents
            if element_id in context.source_egi.area:
                cut_contents = context.source_egi.area.get(element_id, frozenset())
                expanded_subgraph.update(cut_contents)

        # Check if the expanded subgraph (excluding cut contents) is in the target area
        elements_in_target = context.selected_subgraph.intersection(area_contents)
        if elements_in_target != context.selected_subgraph:
            return False, "Selected subgraph contains elements not in target area"

        # CRITICAL: Check if subgraph is closed per Dau's requirement
        if not self.is_closed_subgraph(context.source_egi, context.selected_subgraph):
            return (
                False,
                "Erasure only applies to closed subgraphs (no external edge connections)",
            )

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply ERA by removing the specified subgraph from the positive area."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi

            # Expand selected subgraph to include cut contents
            expanded_subgraph = set(context.selected_subgraph)
            for element_id in context.selected_subgraph:
                # If this element is a cut, include all its contents
                if element_id in egi.area:
                    cut_contents = egi.area.get(element_id, frozenset())
                    expanded_subgraph.update(cut_contents)

            # Remove vertices and edges from the EGI
            new_vertices = frozenset(v for v in egi.V if v.id not in expanded_subgraph)
            new_edges = frozenset(e for e in egi.E if e.id not in expanded_subgraph)
            new_cuts = frozenset(c for c in egi.Cut if c.id not in expanded_subgraph)

            # Update nu mapping
            new_nu = frozendict(
                {k: v for k, v in egi.nu.items() if k not in expanded_subgraph}
            )

            # Update rel mapping
            new_rel = frozendict(
                {k: v for k, v in egi.rel.items() if k not in expanded_subgraph}
            )

            # Update area mapping
            new_area_mapping = dict(egi.area)

            # Remove elements from all areas
            for area_id, contents in new_area_mapping.items():
                new_area_mapping[area_id] = contents - expanded_subgraph

            # Remove areas for erased cuts
            for element_id in expanded_subgraph:
                if element_id in new_area_mapping:
                    del new_area_mapping[element_id]

            result_egi = RelationalGraphWithCuts(
                V=new_vertices,
                E=new_edges,
                nu=new_nu,
                sheet=egi.sheet,
                Cut=new_cuts,
                area=frozendict(new_area_mapping),
                rel=new_rel,
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "ERA",
                    "erased_elements": list(context.selected_subgraph),
                    "source_area": str(context.target_area),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class IterationRule(FormalTransformationRule):
    """IT+ - Iteration Rule"""

    def get_rule_name(self) -> str:
        return "IT+ (Iteration)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        IT+ requires a selected subgraph and a properly designated area
        (the same area or area nested in the same) in which to iterate it.
        """
        # Verify selected subgraph exists
        if not context.selected_subgraph:
            return False, "Must select a subgraph to iterate"

        # Verify target area exists
        if context.target_area not in context.source_egi.area:
            return False, f"Target area {context.target_area} does not exist"

        # For now, we'll allow iteration in any area
        # Full implementation would check nesting relationships

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply IT+ by copying the selected subgraph to the designated area."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi

            # Create copies of the selected elements with new IDs
            new_vertices = set(egi.V)
            new_edges = set(egi.E)
            new_cuts = set(egi.Cut)
            new_nu = dict(egi.nu)
            new_rel = dict(egi.rel)

            copied_elements = set()
            element_mapping = {}  # Original ID -> Copy ID

            # Copy vertices
            for vertex in egi.V:
                if vertex.id in context.selected_subgraph:
                    copy_id = ElementID(f"{vertex.id}_copy")
                    copy_vertex = Vertex(copy_id)
                    new_vertices.add(copy_vertex)
                    copied_elements.add(copy_id)
                    element_mapping[vertex.id] = copy_id

            # Copy edges and update nu mapping
            for edge in egi.E:
                if edge.id in context.selected_subgraph:
                    copy_id = ElementID(f"{edge.id}_copy")
                    copy_edge = Edge(copy_id)
                    new_edges.add(copy_edge)
                    copied_elements.add(copy_id)
                    element_mapping[edge.id] = copy_id

                    # Update nu mapping for copied edge
                    if edge.id in egi.nu:
                        original_sequence = egi.nu[edge.id]
                        # Map vertex IDs in the sequence
                        new_sequence = tuple(
                            element_mapping.get(vid, vid) for vid in original_sequence
                        )
                        new_nu[copy_id] = new_sequence

                    # Update rel mapping
                    if edge.id in egi.rel:
                        new_rel[copy_id] = egi.rel[edge.id]

            # Update area mapping
            new_area_mapping = dict(egi.area)
            current_area_contents = new_area_mapping.get(
                context.target_area, frozenset()
            )
            new_area_mapping[context.target_area] = current_area_contents | frozenset(
                copied_elements
            )

            result_egi = RelationalGraphWithCuts(
                V=frozenset(new_vertices),
                E=frozenset(new_edges),
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=frozenset(new_cuts),
                area=frozendict(new_area_mapping),
                rel=frozendict(new_rel),
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "IT+",
                    "copied_elements": list(copied_elements),
                    "target_area": str(context.target_area),
                    "element_mapping": {
                        str(k): str(v) for k, v in element_mapping.items()
                    },
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class DeiterationRule(FormalTransformationRule):
    """IT- - Deiteration Rule"""

    def get_rule_name(self) -> str:
        return "IT- (Deiteration)"

    def is_valid(
        self, egi: RelationalGraphWithCuts, selected_subgraph: FrozenSet[ElementID]
    ) -> bool:
        """Check if deiteration is valid for the selected subgraph."""
        # Create a transformation context for validation
        context = TransformationContext(
            source_egi=egi,
            target_area="sheet",  # Default to sheet area
            selected_subgraph=selected_subgraph,
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0,
        )

        is_valid, _ = self.check_preconditions(context)
        return is_valid

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        IT- requires a selected subgraph to delete if there is an identical
        subgraph in the same or any enclosing area.
        """
        if not context.selected_subgraph:
            return False, "Must select a subgraph to deiterate"

        # Use the sophisticated isomorphism engine for proper Dau compliance
        return self._check_deiteration_with_isomorphism_engine(context)

    def _check_deiteration_with_isomorphism_engine(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """Check deiteration validity using the sophisticated isomorphism engine."""
        egi = context.source_egi
        selected_subgraph = context.selected_subgraph
        target_area = context.target_area

        # Build nesting hierarchy from target area to sheet
        nesting_hierarchy = self._get_nesting_hierarchy(egi, target_area)

        # Use IsomorphismValidator for rigorous structural checking
        validator = IsomorphismValidator()
        is_valid, error_message = validator.validate_deiteration_candidate(
            egi, selected_subgraph, target_area, nesting_hierarchy
        )

        return is_valid, error_message

    def _basic_deiteration_validation(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """Basic deiteration validation fallback when isomorphism engine unavailable."""
        egi = context.source_egi
        selected_subgraph = context.selected_subgraph
        target_area = context.target_area

        # Build nesting hierarchy (nest of cuts) from target area to sheet
        nesting_hierarchy = self._get_nesting_hierarchy(egi, target_area)

        # Search for structurally identical subgraph in nesting hierarchy
        for search_area in nesting_hierarchy:
            # Skip target area itself (can't deiterate against self)
            if search_area == target_area:
                continue

            # Check if this area contains a structurally identical subgraph
            if self._contains_identical_subgraph(
                egi, selected_subgraph, search_area, target_area
            ):
                return True, None

        return (
            False,
            "No structurally identical subgraph found in nest of cuts that could have been iteration source",
        )

    def _get_nesting_hierarchy(
        self, egi: RelationalGraphWithCuts, target_area: ElementID
    ) -> List[ElementID]:
        """Get ordered list of areas from target_area up to sheet (nest of cuts)."""
        hierarchy = [target_area]
        current_area = target_area

        # Walk up the nesting chain to sheet
        while current_area != egi.sheet:
            # Find which area contains current_area
            parent_area = None
            for area_id, contents in egi.area.items():
                if current_area in contents:
                    parent_area = area_id
                    break

            if parent_area is None:
                break

            hierarchy.append(parent_area)
            current_area = parent_area

        return hierarchy

    def _contains_identical_subgraph(
        self,
        egi: RelationalGraphWithCuts,
        selected_subgraph: FrozenSet[ElementID],
        search_area: ElementID,
        target_area: ElementID,
    ) -> bool:
        """Check if search_area contains a structurally identical subgraph to selected_subgraph."""

        area_contents = egi.area.get(search_area, frozenset())

        # For complete structural identity, we need to find a mapping from selected_subgraph
        # elements to area_contents elements that preserves all structural relationships

        # Generate all possible mappings of selected elements to area elements
        selected_elements = list(selected_subgraph)
        area_elements = list(area_contents)

        # Try all possible mappings of selected elements to area elements
        from itertools import permutations

        for mapping_elements in permutations(area_elements, len(selected_elements)):
            mapping = dict(zip(selected_elements, mapping_elements))

            if self._is_valid_structural_mapping(
                egi, selected_subgraph, mapping, search_area
            ):
                return True

        return False

    def _is_valid_structural_mapping(
        self,
        egi: RelationalGraphWithCuts,
        selected_subgraph: FrozenSet[ElementID],
        mapping: Dict[ElementID, ElementID],
        search_area: ElementID,
    ) -> bool:
        """Check if mapping preserves all structural relationships per Dau's isomorphism requirements."""

        # Verify all mapped elements are actually in the search area
        for mapped_element in mapping.values():
            if mapped_element not in egi.area.get(search_area, frozenset()):
                return False

        # Check structural preservation for each element type
        for original_id, mapped_id in mapping.items():

            # Vertex structural identity
            if self._is_vertex(egi, original_id):
                if not self._is_vertex(egi, mapped_id):
                    return False

                orig_vertex = self._get_vertex(egi, original_id)
                mapped_vertex = self._get_vertex(egi, mapped_id)

                # Must have identical properties
                if (
                    orig_vertex.label != mapped_vertex.label
                    or orig_vertex.is_generic != mapped_vertex.is_generic
                ):
                    return False

            # Edge structural identity
            elif self._is_edge(egi, original_id):
                if not self._is_edge(egi, mapped_id):
                    return False

                # Must have same relation name (κ mapping)
                orig_relation = egi.rel.get(original_id, "")
                mapped_relation = egi.rel.get(mapped_id, "")
                if orig_relation != mapped_relation:
                    return False

                # Must have structurally equivalent vertex sequences (ν mapping)
                orig_sequence = egi.nu.get(original_id, ())
                mapped_sequence = egi.nu.get(mapped_id, ())

                if not self._sequences_structurally_equivalent(
                    orig_sequence, mapped_sequence, mapping
                ):
                    return False

            # Cut structural identity
            elif self._is_cut(egi, original_id):
                if not self._is_cut(egi, mapped_id):
                    return False

                # Cut contents must be structurally equivalent
                orig_contents = egi.area.get(original_id, frozenset())
                mapped_contents = egi.area.get(mapped_id, frozenset())

                if not self._cut_contents_structurally_equivalent(
                    orig_contents, mapped_contents, mapping
                ):
                    return False

        return True

    def _is_vertex(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
        """Check if element is a vertex."""
        return any(v.id == element_id for v in egi.V)

    def _is_edge(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
        """Check if element is an edge."""
        return any(e.id == element_id for e in egi.E)

    def _is_cut(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
        """Check if element is a cut."""
        return any(c.id == element_id for c in egi.Cut)

    def _get_vertex(
        self, egi: RelationalGraphWithCuts, element_id: ElementID
    ) -> Vertex:
        """Get vertex by ID."""
        for v in egi.V:
            if v.id == element_id:
                return v
        raise ValueError(f"Vertex {element_id} not found")

    def _get_edge(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> Edge:
        """Get edge by ID."""
        for e in egi.E:
            if e.id == element_id:
                return e
        raise ValueError(f"Edge {element_id} not found")

    def _get_cut(self, egi: RelationalGraphWithCuts, element_id: ElementID) -> Cut:
        """Get cut by ID."""
        for c in egi.Cut:
            if c.id == element_id:
                return c
        raise ValueError(f"Cut {element_id} not found")

    def _sequences_structurally_equivalent(
        self,
        seq1: Tuple[ElementID, ...],
        seq2: Tuple[ElementID, ...],
        mapping: Dict[ElementID, ElementID],
    ) -> bool:
        """Check if vertex sequences are structurally equivalent under mapping."""
        if len(seq1) != len(seq2):
            return False

        for i, (orig_vertex_id, mapped_vertex_id) in enumerate(zip(seq1, seq2)):
            # If original vertex is in our mapping, check if it maps correctly
            if orig_vertex_id in mapping:
                if mapping[orig_vertex_id] != mapped_vertex_id:
                    return False
            # If not in mapping, vertices should be identical
            elif orig_vertex_id != mapped_vertex_id:
                return False

        return True

    def _cut_contents_structurally_equivalent(
        self,
        contents1: FrozenSet[ElementID],
        contents2: FrozenSet[ElementID],
        mapping: Dict[ElementID, ElementID],
    ) -> bool:
        """Check if cut contents are structurally equivalent under mapping."""
        if len(contents1) != len(contents2):
            return False

        # All elements in contents1 should map to elements in contents2
        mapped_contents1 = set()
        for element_id in contents1:
            if element_id in mapping:
                mapped_contents1.add(mapping[element_id])
            else:
                mapped_contents1.add(element_id)

        return mapped_contents1 == set(contents2)

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply IT- by removing one instance of the duplicated subgraph."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            # This is essentially the same as erasure for the simplified implementation
            erasure_rule = ErasureRule()

            # Create a context for erasure (IT- can work in any polarity)
            erasure_context = TransformationContext(
                source_egi=context.source_egi,
                target_area=context.target_area,
                selected_subgraph=context.selected_subgraph,
                area_polarity=AreaPolarity.POSITIVE,  # Override polarity check
                nesting_depth=context.nesting_depth,
            )

            result = erasure_rule.apply_transformation(erasure_context)

            if result.success:
                result.changes_made["rule"] = "IT-"
                result.changes_made["deiterated_elements"] = result.changes_made.pop(
                    "erased_elements", []
                )

            return result

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class HeavyDotInsertionRule(FormalTransformationRule):
    """Heavy Dot Insertion Rule - Insert individual vertex in negative context"""

    def get_rule_name(self) -> str:
        return "HEAVY_DOT (Heavy Dot Insertion)"

    def check_preconditions(
        self, context: TransformationContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Heavy dot insertion requires a negatively-enclosed area.
        """
        if context.area_polarity != AreaPolarity.NEGATIVE:
            return (
                False,
                "Heavy dot insertion only allowed in negatively-enclosed areas (odd nesting depth)",
            )

        # Verify target area exists
        if context.target_area not in context.source_egi.area:
            return False, f"Target area {context.target_area} does not exist"

        return True, None

    def apply_transformation(
        self, context: TransformationContext
    ) -> TransformationResult:
        """Apply heavy dot insertion by adding a single vertex to the negative area."""
        precondition_ok, error_msg = self.check_preconditions(context)
        if not precondition_ok:
            return TransformationResult(False, None, error_msg, {})

        try:
            egi = context.source_egi

            # Create a new vertex (heavy dot)
            heavy_dot_id = ElementID("heavy_dot_vertex")
            heavy_dot_vertex = Vertex(heavy_dot_id)

            # Add vertex to EGI
            new_vertices = egi.V | {heavy_dot_vertex}

            # Update area mapping
            new_area_mapping = dict(egi.area)
            current_area_contents = new_area_mapping.get(
                context.target_area, frozenset()
            )
            new_area_mapping[context.target_area] = current_area_contents | frozenset(
                [heavy_dot_id]
            )

            result_egi = RelationalGraphWithCuts(
                V=new_vertices,
                E=egi.E,
                nu=egi.nu,
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=frozendict(new_area_mapping),
                rel=egi.rel,
            )

            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={
                    "rule": "HEAVY_DOT",
                    "inserted_vertex": str(heavy_dot_id),
                    "target_area": str(context.target_area),
                },
            )

        except Exception as e:
            return TransformationResult(False, None, str(e), {})


class FormalTransformationEngine:
    """Engine for applying formal EG transformation rules."""

    def __init__(self):
        self.rules = {
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "INS": InsertionRule(),
            "ERA": ErasureRule(),
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
            "HEAVY_DOT": HeavyDotInsertionRule(),
        }

    def apply_rule(
        self,
        rule_name: str,
        source_egi: RelationalGraphWithCuts,
        target_area: ElementID,
        selected_subgraph: FrozenSet[ElementID],
    ) -> TransformationResult:
        """Apply a transformation rule to an EGI."""

        if rule_name not in self.rules:
            return TransformationResult(
                success=False,
                result_egi=None,
                error_message=f"Unknown rule: {rule_name}",
                changes_made={},
            )

        rule = self.rules[rule_name]

        # Calculate area polarity
        polarity, nesting_depth = rule.calculate_area_polarity(source_egi, target_area)

        # Create transformation context
        context = TransformationContext(
            source_egi=source_egi,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=polarity,
            nesting_depth=nesting_depth,
        )

        # Apply the rule
        return rule.apply_transformation(context)

    def get_available_rules(self) -> List[str]:
        """Get list of available transformation rules."""
        return list(self.rules.keys())

    def describe_rule(self, rule_name: str) -> str:
        """Get description of a transformation rule."""
        if rule_name not in self.rules:
            return f"Unknown rule: {rule_name}"

        return self.rules[rule_name].get_rule_name()


def create_test_egi() -> RelationalGraphWithCuts:
    """Create a test EGI for demonstration purposes."""

    # Create a simple EGI with vertices A and B
    vertex_a = Vertex(ElementID("A"))
    vertex_b = Vertex(ElementID("B"))

    return RelationalGraphWithCuts(
        V=frozenset([vertex_a, vertex_b]),
        E=frozenset(),
        nu=frozendict(),
        sheet=ElementID("sheet"),
        Cut=frozenset(),
        area=frozendict(
            {ElementID("sheet"): frozenset([ElementID("A"), ElementID("B")])}
        ),
        rel=frozendict(),
    )


def demonstrate_transformation_rules():
    """Demonstrate each transformation rule with test sequences."""

    print("🔧 Formal EG Transformation Rules Demonstration")
    print("=" * 50)

    engine = FormalTransformationEngine()
    test_egi = create_test_egi()

    print(
        f"Starting EGI: {len(test_egi.V)} vertices, {len(test_egi.E)} edges, {len(test_egi.Cut)} cuts"
    )
    print(f"Sheet contents: {list(test_egi.area[ElementID('sheet')])}")
    print()

    # Test each rule
    test_cases = [
        {
            "rule": "DC+",
            "description": "Insert double cut around vertex A",
            "target_area": ElementID("sheet"),
            "selected_subgraph": frozenset([ElementID("A")]),
        },
        {
            "rule": "INS",
            "description": "Insert new vertex in negative area",
            "target_area": ElementID("sheet"),  # Will be updated after DC+
            "selected_subgraph": frozenset([ElementID("new_vertex_C")]),
        },
        {
            "rule": "IT+",
            "description": "Iterate vertex B",
            "target_area": ElementID("sheet"),
            "selected_subgraph": frozenset([ElementID("B")]),
        },
    ]

    current_egi = test_egi

    for i, test_case in enumerate(test_cases):
        print(f"🎯 Test {i+1}: {test_case['rule']} - {test_case['description']}")

        # Special handling for INS - needs negative area
        if test_case["rule"] == "INS" and i > 0:
            # Look for a cut area from previous transformations
            cut_areas = [
                area_id
                for area_id in current_egi.area.keys()
                if str(area_id).startswith("dc_inner")
            ]
            if cut_areas:
                test_case["target_area"] = cut_areas[0]

        result = engine.apply_rule(
            test_case["rule"],
            current_egi,
            test_case["target_area"],
            test_case["selected_subgraph"],
        )

        if result.success:
            print(f"   ✅ SUCCESS")
            print(f"   Changes: {result.changes_made}")
            current_egi = result.result_egi
            print(
                f"   Result: {len(current_egi.V)}V, {len(current_egi.E)}E, {len(current_egi.Cut)}C"
            )
        else:
            print(f"   ❌ FAILED: {result.error_message}")

        print()

    print(
        f"📊 Final EGI: {len(current_egi.V)} vertices, {len(current_egi.E)} edges, {len(current_egi.Cut)} cuts"
    )

    return engine, current_egi


if __name__ == "__main__":
    demonstrate_transformation_rules()
