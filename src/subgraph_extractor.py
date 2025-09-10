"""
Subgraph Extractor for EGI

Comprehensive system for selecting and extracting proper subgraphs from EGI structures.
Supports multiple selection criteria while preserving logical relationships and 
spatial correspondence.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import copy

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from rtree_cut_tracker import RTreeCutTracker, SpatialBounds, CutSpatialInfo
from historical_graph_model import HistoricalGraph, CompositionSource
from simplified_sheet_of_assertion import SheetMetadata, SheetPurpose


class SelectionCriterion(Enum):
    """Criteria for subgraph selection."""
    CONNECTED_COMPONENT = "connected_component"      # Connected elements from seed
    CONTEXT_BASED = "context_based"                 # All elements within a cut context
    SPATIAL_REGION = "spatial_region"               # Elements within spatial bounds
    SEMANTIC_PATTERN = "semantic_pattern"           # Elements matching semantic criteria
    DEPTH_LIMITED = "depth_limited"                 # Limited nesting depth
    CUSTOM_PREDICATE = "custom_predicate"           # User-defined selection function


class SubgraphBoundary(Enum):
    """How to handle subgraph boundaries."""
    STRICT = "strict"                               # Only selected elements
    INCLUDE_DEPENDENCIES = "include_dependencies"   # Include required dependencies
    COMPLETE_CONTEXTS = "complete_contexts"         # Complete cut contexts
    MINIMAL_CLOSURE = "minimal_closure"             # Minimal logically valid closure


@dataclass
class SelectionParameters:
    """Parameters for subgraph selection."""
    criterion: SelectionCriterion
    boundary_handling: SubgraphBoundary = SubgraphBoundary.INCLUDE_DEPENDENCIES
    
    # Seed elements for selection
    seed_elements: Set[ElementID] = field(default_factory=set)
    
    # Spatial selection parameters
    spatial_bounds: Optional[SpatialBounds] = None
    
    # Context-based parameters
    target_contexts: Set[ElementID] = field(default_factory=set)
    
    # Depth parameters
    max_depth: Optional[int] = None
    min_depth: Optional[int] = None
    
    # Custom predicate function
    custom_predicate: Optional[Callable[[ElementID, RelationalGraphWithCuts], bool]] = None
    
    # Metadata
    preserve_spatial_info: bool = True
    include_transformation_history: bool = False


@dataclass
class SubgraphExtractionResult:
    """Result of subgraph extraction."""
    success: bool
    extracted_subgraph: Optional[RelationalGraphWithCuts] = None
    selected_elements: Set[ElementID] = field(default_factory=set)
    spatial_info: Dict[ElementID, SpatialBounds] = field(default_factory=dict)
    
    # Metadata about extraction
    original_sheet_id: str = ""
    extraction_method: str = ""
    boundary_elements: Set[ElementID] = field(default_factory=set)
    
    # Error information
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class SubgraphExtractor:
    """
    Comprehensive subgraph extraction system for EGI structures.
    
    Provides multiple selection criteria and boundary handling strategies
    while preserving logical relationships and spatial correspondence.
    """
    
    def __init__(self):
        self.selection_strategies = {
            SelectionCriterion.CONNECTED_COMPONENT: self._select_connected_component,
            SelectionCriterion.CONTEXT_BASED: self._select_context_based,
            SelectionCriterion.SPATIAL_REGION: self._select_spatial_region,
            SelectionCriterion.SEMANTIC_PATTERN: self._select_semantic_pattern,
            SelectionCriterion.DEPTH_LIMITED: self._select_depth_limited,
            SelectionCriterion.CUSTOM_PREDICATE: self._select_custom_predicate
        }
        
        self.boundary_handlers = {
            SubgraphBoundary.STRICT: self._apply_strict_boundary,
            SubgraphBoundary.INCLUDE_DEPENDENCIES: self._apply_dependency_boundary,
            SubgraphBoundary.COMPLETE_CONTEXTS: self._apply_context_boundary,
            SubgraphBoundary.MINIMAL_CLOSURE: self._apply_minimal_closure
        }
    
    def extract_subgraph(self, source_egi: RelationalGraphWithCuts,
                        parameters: SelectionParameters,
                        spatial_tracker: Optional[RTreeCutTracker] = None) -> SubgraphExtractionResult:
        """
        Extract a subgraph based on selection parameters.
        """
        try:
            # Step 1: Select initial elements based on criterion
            selection_strategy = self.selection_strategies.get(parameters.criterion)
            if not selection_strategy:
                return SubgraphExtractionResult(
                    success=False,
                    error_message=f"Unknown selection criterion: {parameters.criterion}"
                )
            
            selected_elements = selection_strategy(source_egi, parameters)
            
            if not selected_elements:
                return SubgraphExtractionResult(
                    success=False,
                    error_message="No elements selected by criterion"
                )
            
            # Step 2: Apply boundary handling
            boundary_handler = self.boundary_handlers.get(parameters.boundary_handling)
            if boundary_handler:
                selected_elements, boundary_elements = boundary_handler(
                    source_egi, selected_elements, parameters
                )
            else:
                boundary_elements = set()
            
            # Step 3: Extract subgraph structure
            extracted_subgraph = self._create_subgraph_structure(
                source_egi, selected_elements
            )
            
            # Step 4: Preserve spatial information if requested
            spatial_info = {}
            if parameters.preserve_spatial_info and spatial_tracker:
                spatial_info = self._extract_spatial_info(
                    selected_elements, spatial_tracker
                )
            
            return SubgraphExtractionResult(
                success=True,
                extracted_subgraph=extracted_subgraph,
                selected_elements=selected_elements,
                spatial_info=spatial_info,
                extraction_method=parameters.criterion.value,
                boundary_elements=boundary_elements
            )
            
        except Exception as e:
            return SubgraphExtractionResult(
                success=False,
                error_message=f"Extraction failed: {str(e)}"
            )
    
    def _select_connected_component(self, egi: RelationalGraphWithCuts, 
                                  params: SelectionParameters) -> Set[ElementID]:
        """Select connected component from seed elements."""
        if not params.seed_elements:
            return set()
        
        connected = set()
        frontier = list(params.seed_elements)
        
        # Build adjacency information
        vertex_to_edges = {}
        for edge_id, vertex_seq in egi.nu.items():
            for vertex_id in vertex_seq:
                vertex_to_edges.setdefault(vertex_id, []).append(edge_id)
        
        while frontier:
            element_id = frontier.pop()
            if element_id in connected:
                continue
            
            connected.add(element_id)
            
            # Expand based on element type
            if element_id in egi._vertex_map:
                # Vertex: add incident edges and their other vertices
                for edge_id in vertex_to_edges.get(element_id, []):
                    if edge_id not in connected:
                        frontier.append(edge_id)
                        # Add other vertices of this edge
                        for vertex_id in egi.nu.get(edge_id, []):
                            if vertex_id != element_id and vertex_id not in connected:
                                frontier.append(vertex_id)
            
            elif element_id in egi._edge_map:
                # Edge: add incident vertices
                for vertex_id in egi.nu.get(element_id, []):
                    if vertex_id not in connected:
                        frontier.append(vertex_id)
            
            elif element_id in egi._cut_map:
                # Cut: add all elements in its context
                context_elements = egi.get_full_context(element_id)
                for ctx_element in context_elements:
                    if ctx_element not in connected:
                        frontier.append(ctx_element)
        
        return connected
    
    def _select_context_based(self, egi: RelationalGraphWithCuts, 
                            params: SelectionParameters) -> Set[ElementID]:
        """Select all elements within specified contexts."""
        selected = set()
        
        for context_id in params.target_contexts:
            if context_id in egi._cut_map or context_id == egi.sheet:
                context_elements = egi.get_full_context(context_id)
                selected.update(context_elements)
                selected.add(context_id)  # Include the context itself
        
        return selected
    
    def _select_spatial_region(self, egi: RelationalGraphWithCuts, 
                             params: SelectionParameters) -> Set[ElementID]:
        """Select elements within spatial bounds."""
        if not params.spatial_bounds:
            return set()
        
        # This would require spatial information to be available
        # For now, return empty set as placeholder
        # Full implementation would query spatial tracker
        return set()
    
    def _select_semantic_pattern(self, egi: RelationalGraphWithCuts, 
                               params: SelectionParameters) -> Set[ElementID]:
        """Select elements matching semantic patterns."""
        # Placeholder for semantic pattern matching
        # Would analyze vertex labels, edge types, etc.
        return set()
    
    def _select_depth_limited(self, egi: RelationalGraphWithCuts, 
                            params: SelectionParameters) -> Set[ElementID]:
        """Select elements within specified nesting depth range."""
        selected = set()
        
        for element_id in egi.get_all_elements():
            try:
                depth = egi.get_nesting_depth(element_id)
                
                if params.min_depth is not None and depth < params.min_depth:
                    continue
                if params.max_depth is not None and depth > params.max_depth:
                    continue
                
                selected.add(element_id)
                
            except Exception:
                continue
        
        return selected
    
    def _select_custom_predicate(self, egi: RelationalGraphWithCuts, 
                               params: SelectionParameters) -> Set[ElementID]:
        """Select elements using custom predicate function."""
        if not params.custom_predicate:
            return set()
        
        selected = set()
        
        for element_id in egi.get_all_elements():
            try:
                if params.custom_predicate(element_id, egi):
                    selected.add(element_id)
            except Exception:
                continue
        
        return selected
    
    def _apply_strict_boundary(self, egi: RelationalGraphWithCuts, 
                             selected: Set[ElementID], 
                             params: SelectionParameters) -> Tuple[Set[ElementID], Set[ElementID]]:
        """Apply strict boundary - only selected elements."""
        return selected, set()
    
    def _apply_dependency_boundary(self, egi: RelationalGraphWithCuts, 
                                 selected: Set[ElementID], 
                                 params: SelectionParameters) -> Tuple[Set[ElementID], Set[ElementID]]:
        """Include elements required for logical validity."""
        extended = set(selected)
        boundary = set()
        
        # For each edge, ensure all incident vertices are included
        for element_id in selected:
            if element_id in egi._edge_map:
                for vertex_id in egi.nu.get(element_id, []):
                    if vertex_id not in selected:
                        extended.add(vertex_id)
                        boundary.add(vertex_id)
        
        # For each vertex, consider including incident edges
        for element_id in selected:
            if element_id in egi._vertex_map:
                for edge_id, vertex_seq in egi.nu.items():
                    if element_id in vertex_seq:
                        # Include edge if all its vertices are selected
                        if all(v_id in extended for v_id in vertex_seq):
                            if edge_id not in selected:
                                extended.add(edge_id)
                                boundary.add(edge_id)
        
        return extended, boundary
    
    def _apply_context_boundary(self, egi: RelationalGraphWithCuts, 
                              selected: Set[ElementID], 
                              params: SelectionParameters) -> Tuple[Set[ElementID], Set[ElementID]]:
        """Complete cut contexts for selected elements."""
        extended = set(selected)
        boundary = set()
        
        # For each selected element, include its complete context
        for element_id in selected:
            try:
                context_id = egi.get_context(element_id)
                if context_id not in selected:
                    # Include all elements in this context
                    context_elements = egi.get_full_context(context_id)
                    for ctx_element in context_elements:
                        if ctx_element not in selected:
                            extended.add(ctx_element)
                            boundary.add(ctx_element)
                    
                    # Include the context cut itself
                    if context_id not in selected:
                        extended.add(context_id)
                        boundary.add(context_id)
                        
            except Exception:
                continue
        
        return extended, boundary
    
    def _apply_minimal_closure(self, egi: RelationalGraphWithCuts, 
                             selected: Set[ElementID], 
                             params: SelectionParameters) -> Tuple[Set[ElementID], Set[ElementID]]:
        """Apply minimal logically valid closure."""
        # Start with dependency boundary
        extended, boundary = self._apply_dependency_boundary(egi, selected, params)
        
        # Add minimal context requirements
        additional_boundary = set()
        
        for element_id in extended:
            try:
                context_id = egi.get_context(element_id)
                # Only include context if it's not the sheet and not already included
                if context_id != egi.sheet and context_id not in extended:
                    extended.add(context_id)
                    additional_boundary.add(context_id)
            except Exception:
                continue
        
        boundary.update(additional_boundary)
        return extended, boundary
    
    def _create_subgraph_structure(self, source_egi: RelationalGraphWithCuts, 
                                 selected_elements: Set[ElementID]) -> RelationalGraphWithCuts:
        """Create new EGI structure containing only selected elements."""
        subgraph = RelationalGraphWithCuts()
        
        # Copy selected vertices
        for vertex_id in selected_elements:
            if vertex_id in source_egi._vertex_map:
                vertex = source_egi._vertex_map[vertex_id]
                subgraph.V.add(copy.deepcopy(vertex))
                subgraph._vertex_map[vertex_id] = vertex
        
        # Copy selected edges and their incidence
        for edge_id in selected_elements:
            if edge_id in source_egi._edge_map:
                edge = source_egi._edge_map[edge_id]
                subgraph.E.add(copy.deepcopy(edge))
                subgraph._edge_map[edge_id] = edge
                
                # Copy incidence relation if vertices are included
                if edge_id in source_egi.nu:
                    vertex_seq = source_egi.nu[edge_id]
                    if all(v_id in selected_elements for v_id in vertex_seq):
                        subgraph.nu[edge_id] = vertex_seq
        
        # Copy selected cuts and their areas
        for cut_id in selected_elements:
            if cut_id in source_egi._cut_map:
                cut = source_egi._cut_map[cut_id]
                subgraph.Cut.add(copy.deepcopy(cut))
                subgraph._cut_map[cut_id] = cut
                
                # Copy area relation for included elements
                if cut_id in source_egi.area:
                    area_elements = source_egi.area[cut_id]
                    included_area = frozenset(
                        elem for elem in area_elements 
                        if elem in selected_elements
                    )
                    if included_area:
                        subgraph.area[cut_id] = included_area
        
        return subgraph
    
    def _extract_spatial_info(self, selected_elements: Set[ElementID], 
                            spatial_tracker: RTreeCutTracker) -> Dict[ElementID, SpatialBounds]:
        """Extract spatial information for selected elements."""
        spatial_info = {}
        
        for element_id in selected_elements:
            cut_info = spatial_tracker.get_cut_info(element_id)
            if cut_info:
                spatial_info[element_id] = cut_info.bounds
        
        return spatial_info
    
    def create_historical_subgraph(self, extraction_result: SubgraphExtractionResult,
                                 metadata: SheetMetadata) -> Optional[HistoricalGraph]:
        """Create a HistoricalGraph from extraction result."""
        if not extraction_result.success or not extraction_result.extracted_subgraph:
            return None
        
        # Create historical graph with extraction provenance
        historical_graph = HistoricalGraph(
            metadata=metadata,
            initial_egi=extraction_result.extracted_subgraph,
            creation_source=CompositionSource.SUBGRAPH_ADDITION
        )
        
        # Add extraction metadata to creation event
        if historical_graph.history.events:
            creation_event = next(iter(historical_graph.history.events.values()))
            creation_event.metadata.update({
                "extraction_method": extraction_result.extraction_method,
                "original_sheet": extraction_result.original_sheet_id,
                "selected_elements": list(extraction_result.selected_elements),
                "boundary_elements": list(extraction_result.boundary_elements)
            })
        
        return historical_graph


class SubgraphSelector:
    """
    High-level interface for common subgraph selection operations.
    """
    
    def __init__(self, extractor: SubgraphExtractor):
        self.extractor = extractor
    
    def select_around_element(self, egi: RelationalGraphWithCuts, 
                            element_id: ElementID,
                            spatial_tracker: Optional[RTreeCutTracker] = None) -> SubgraphExtractionResult:
        """Select connected component around a specific element."""
        params = SelectionParameters(
            criterion=SelectionCriterion.CONNECTED_COMPONENT,
            boundary_handling=SubgraphBoundary.INCLUDE_DEPENDENCIES,
            seed_elements={element_id}
        )
        
        return self.extractor.extract_subgraph(egi, params, spatial_tracker)
    
    def select_context(self, egi: RelationalGraphWithCuts, 
                      context_id: ElementID,
                      spatial_tracker: Optional[RTreeCutTracker] = None) -> SubgraphExtractionResult:
        """Select all elements within a specific context."""
        params = SelectionParameters(
            criterion=SelectionCriterion.CONTEXT_BASED,
            boundary_handling=SubgraphBoundary.COMPLETE_CONTEXTS,
            target_contexts={context_id}
        )
        
        return self.extractor.extract_subgraph(egi, params, spatial_tracker)
    
    def select_by_depth(self, egi: RelationalGraphWithCuts, 
                       min_depth: Optional[int] = None,
                       max_depth: Optional[int] = None,
                       spatial_tracker: Optional[RTreeCutTracker] = None) -> SubgraphExtractionResult:
        """Select elements within specified nesting depth range."""
        params = SelectionParameters(
            criterion=SelectionCriterion.DEPTH_LIMITED,
            boundary_handling=SubgraphBoundary.MINIMAL_CLOSURE,
            min_depth=min_depth,
            max_depth=max_depth
        )
        
        return self.extractor.extract_subgraph(egi, params, spatial_tracker)
    
    def select_custom(self, egi: RelationalGraphWithCuts,
                     predicate: Callable[[ElementID, RelationalGraphWithCuts], bool],
                     boundary: SubgraphBoundary = SubgraphBoundary.INCLUDE_DEPENDENCIES,
                     spatial_tracker: Optional[RTreeCutTracker] = None) -> SubgraphExtractionResult:
        """Select elements using custom predicate."""
        params = SelectionParameters(
            criterion=SelectionCriterion.CUSTOM_PREDICATE,
            boundary_handling=boundary,
            custom_predicate=predicate
        )
        
        return self.extractor.extract_subgraph(egi, params, spatial_tracker)
