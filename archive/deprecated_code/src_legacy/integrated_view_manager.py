"""
Integrated View Manager

This module consolidates all view management functionality into a unified system
that integrates with the core Dau formalism manager to provide coherent,
validated view generation and management.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

# Core formalism integration
from .core_dau_formalism import CoreDauFormalismManager, get_dau_formalism_manager
from .egi_core_dau import RelationalGraphWithCuts
from .hierarchical_index import HierarchicalIndex


class ViewType(Enum):
    """Types of EGI views."""
    OVERVIEW = "overview"           # High-level structural view
    DETAILED = "detailed"           # Complete detailed view
    FOCUSED = "focused"             # Focus on specific subgraph
    HIERARCHICAL = "hierarchical"   # Emphasize cut nesting
    SPATIAL = "spatial"             # Spatial layout view
    LOGICAL = "logical"             # Logical structure view
    TRANSFORMATION = "transformation"  # Transformation sequence view
    COMPARATIVE = "comparative"     # Compare multiple EGIs


class ViewLevel(Enum):
    """Zoom levels for views."""
    MACRO = "macro"         # Highest level overview
    INTERMEDIATE = "intermediate"  # Mid-level detail
    MICRO = "micro"         # Detailed element view
    ATOMIC = "atomic"       # Individual component view


@dataclass
class ViewConfiguration:
    """Configuration for view generation."""
    view_type: ViewType
    zoom_level: ViewLevel
    focus_elements: List[str] = field(default_factory=list)
    show_labels: bool = True
    show_cuts: bool = True
    show_polarity: bool = True
    show_nesting_levels: bool = False
    highlight_elements: List[str] = field(default_factory=list)
    filter_categories: List[str] = field(default_factory=list)
    max_depth: Optional[int] = None
    spatial_layout: bool = True


@dataclass
class ViewElement:
    """Represents an element in a view."""
    element_id: str
    element_type: str  # vertex, edge, cut, area
    position: Optional[Tuple[float, float]] = None
    size: Optional[Tuple[float, float]] = None
    style: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    interactive: bool = True


@dataclass
class GeneratedView:
    """A generated view of an EGI."""
    view_id: str
    egi_id: str
    configuration: ViewConfiguration
    elements: List[ViewElement]
    layout_bounds: Tuple[float, float, float, float]  # x, y, width, height
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_timestamp: Optional[str] = None


class ViewGenerator(ABC):
    """Abstract base class for view generators."""
    
    @abstractmethod
    def generate_view(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> GeneratedView:
        """Generate a view of the EGI according to configuration."""
        pass
    
    @abstractmethod
    def supports_view_type(self, view_type: ViewType) -> bool:
        """Check if this generator supports the given view type."""
        pass


class OverviewViewGenerator(ViewGenerator):
    """Generates overview views showing high-level structure."""
    
    def supports_view_type(self, view_type: ViewType) -> bool:
        return view_type in [ViewType.OVERVIEW, ViewType.HIERARCHICAL]
    
    def generate_view(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> GeneratedView:
        """Generate overview view."""
        elements = []
        
        # Generate cut hierarchy overview
        if hasattr(egi, 'hierarchical_index') and egi.hierarchical_index.areas:
            elements.extend(self._generate_cut_hierarchy(egi, config))
        
        # Generate vertex/edge summary
        elements.extend(self._generate_element_summary(egi, config))
        
        # Calculate layout bounds
        bounds = self._calculate_bounds(elements)
        
        return GeneratedView(
            view_id=f"overview_{id(egi)}",
            egi_id=getattr(egi, 'id', str(id(egi))),
            configuration=config,
            elements=elements,
            layout_bounds=bounds,
            metadata={"generator": "OverviewViewGenerator"}
        )
    
    def _generate_cut_hierarchy(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate cut hierarchy elements."""
        elements = []
        
        for cut in egi.Cut:
            nesting_level = egi.hierarchical_index.get_nesting_level(cut.id) or 0
            polarity = egi.hierarchical_index.get_polarity(cut.id)
            
            element = ViewElement(
                element_id=cut.id,
                element_type="cut",
                style={
                    "nesting_level": nesting_level,
                    "polarity": polarity,
                    "stroke_width": max(1, 3 - nesting_level * 0.5)
                },
                metadata={"nesting_level": nesting_level, "polarity": polarity}
            )
            elements.append(element)
        
        return elements
    
    def _generate_element_summary(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate summary of vertices and edges."""
        elements = []
        
        # Vertices
        for vertex in egi.V:
            element = ViewElement(
                element_id=vertex.id,
                element_type="vertex",
                style={
                    "is_generic": vertex.is_generic,
                    "label": vertex.label if config.show_labels else None
                },
                metadata={"is_generic": vertex.is_generic, "label": vertex.label}
            )
            elements.append(element)
        
        # Edges
        for edge in egi.E:
            relation = egi.rel.get(edge.id, "")
            element = ViewElement(
                element_id=edge.id,
                element_type="edge",
                style={
                    "relation": relation if config.show_labels else None
                },
                metadata={"relation": relation}
            )
            elements.append(element)
        
        return elements
    
    def _calculate_bounds(self, elements: List[ViewElement]) -> Tuple[float, float, float, float]:
        """Calculate layout bounds for elements."""
        # Simple default bounds - would be more sophisticated in practice
        return (0.0, 0.0, 800.0, 600.0)


class DetailedViewGenerator(ViewGenerator):
    """Generates detailed views showing complete EGI structure."""
    
    def supports_view_type(self, view_type: ViewType) -> bool:
        return view_type in [ViewType.DETAILED, ViewType.SPATIAL, ViewType.LOGICAL]
    
    def generate_view(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> GeneratedView:
        """Generate detailed view."""
        elements = []
        
        # Generate all vertices
        elements.extend(self._generate_vertices(egi, config))
        
        # Generate all edges with ligatures
        elements.extend(self._generate_edges_with_ligatures(egi, config))
        
        # Generate all cuts
        elements.extend(self._generate_cuts(egi, config))
        
        # Generate areas if spatial layout
        if config.spatial_layout:
            elements.extend(self._generate_areas(egi, config))
        
        # Apply focus filtering
        if config.focus_elements:
            elements = self._apply_focus_filter(elements, config.focus_elements)
        
        # Calculate spatial layout
        if config.spatial_layout:
            elements = self._apply_spatial_layout(elements, egi)
        
        bounds = self._calculate_detailed_bounds(elements)
        
        return GeneratedView(
            view_id=f"detailed_{id(egi)}",
            egi_id=getattr(egi, 'id', str(id(egi))),
            configuration=config,
            elements=elements,
            layout_bounds=bounds,
            metadata={"generator": "DetailedViewGenerator", "element_count": len(elements)}
        )
    
    def _generate_vertices(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate vertex elements."""
        elements = []
        
        for vertex in egi.V:
            # Determine which area contains this vertex
            containing_area = None
            for area_id, contents in egi.area.items():
                if vertex.id in contents:
                    containing_area = area_id
                    break
            
            element = ViewElement(
                element_id=vertex.id,
                element_type="vertex",
                style={
                    "is_generic": vertex.is_generic,
                    "label": vertex.label if config.show_labels else None,
                    "shape": "circle" if vertex.is_generic else "square",
                    "fill_color": "#ffffff" if vertex.is_generic else "#cccccc"
                },
                metadata={
                    "is_generic": vertex.is_generic,
                    "label": vertex.label,
                    "containing_area": containing_area
                },
                visible=vertex.id not in config.filter_categories
            )
            elements.append(element)
        
        return elements
    
    def _generate_edges_with_ligatures(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate edge elements with ligature connections."""
        elements = []
        
        for edge in egi.E:
            # Get connected vertices
            connected_vertices = egi.nu.get(edge.id, ())
            relation = egi.rel.get(edge.id, "")
            
            # Determine containing area
            containing_area = None
            for area_id, contents in egi.area.items():
                if edge.id in contents:
                    containing_area = area_id
                    break
            
            element = ViewElement(
                element_id=edge.id,
                element_type="edge",
                style={
                    "relation": relation if config.show_labels else None,
                    "connected_vertices": list(connected_vertices),
                    "arity": len(connected_vertices),
                    "stroke_color": "#000000",
                    "stroke_width": 2
                },
                metadata={
                    "relation": relation,
                    "connected_vertices": list(connected_vertices),
                    "arity": len(connected_vertices),
                    "containing_area": containing_area
                },
                visible=edge.id not in config.filter_categories
            )
            elements.append(element)
        
        return elements
    
    def _generate_cuts(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate cut elements."""
        elements = []
        
        if not config.show_cuts:
            return elements
        
        for cut in egi.Cut:
            nesting_level = 0
            polarity = "positive"
            
            if hasattr(egi, 'hierarchical_index') and egi.hierarchical_index.areas:
                nesting_level = egi.hierarchical_index.get_nesting_level(cut.id) or 0
                polarity = egi.hierarchical_index.get_polarity(cut.id) or "positive"
            
            # Get cut contents
            cut_contents = egi.area.get(cut.id, set())
            
            element = ViewElement(
                element_id=cut.id,
                element_type="cut",
                style={
                    "nesting_level": nesting_level,
                    "polarity": polarity,
                    "stroke_width": max(1, 4 - nesting_level * 0.5),
                    "stroke_color": "#ff0000" if polarity == "negative" else "#0000ff",
                    "fill_opacity": 0.1,
                    "show_polarity": config.show_polarity
                },
                metadata={
                    "nesting_level": nesting_level,
                    "polarity": polarity,
                    "contents": list(cut_contents),
                    "content_count": len(cut_contents)
                },
                visible=cut.id not in config.filter_categories
            )
            elements.append(element)
        
        return elements
    
    def _generate_areas(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> List[ViewElement]:
        """Generate area elements for spatial layout."""
        elements = []
        
        for area_id, contents in egi.area.items():
            if area_id == egi.sheet:  # Skip sheet area
                continue
            
            element = ViewElement(
                element_id=f"area_{area_id}",
                element_type="area",
                style={
                    "fill_opacity": 0.05,
                    "stroke_opacity": 0.3,
                    "area_id": area_id
                },
                metadata={
                    "area_id": area_id,
                    "contents": list(contents),
                    "content_count": len(contents)
                },
                visible=True
            )
            elements.append(element)
        
        return elements
    
    def _apply_focus_filter(self, elements: List[ViewElement], focus_elements: List[str]) -> List[ViewElement]:
        """Apply focus filter to show only specified elements and their connections."""
        if not focus_elements:
            return elements
        
        focused_elements = []
        focus_set = set(focus_elements)
        
        for element in elements:
            # Include if directly in focus
            if element.element_id in focus_set:
                focused_elements.append(element)
                continue
            
            # Include if connected to focus elements (for edges)
            if element.element_type == "edge":
                connected = element.metadata.get("connected_vertices", [])
                if any(vertex_id in focus_set for vertex_id in connected):
                    focused_elements.append(element)
                    continue
            
            # Include containing cuts/areas
            if element.element_type in ["cut", "area"]:
                contents = element.metadata.get("contents", [])
                if any(content_id in focus_set for content_id in contents):
                    focused_elements.append(element)
                    continue
        
        return focused_elements
    
    def _apply_spatial_layout(self, elements: List[ViewElement], egi: RelationalGraphWithCuts) -> List[ViewElement]:
        """Apply spatial layout to elements."""
        # Simple grid-based layout - would be more sophisticated in practice
        vertex_elements = [e for e in elements if e.element_type == "vertex"]
        
        grid_size = int(len(vertex_elements) ** 0.5) + 1
        spacing = 100
        
        for i, element in enumerate(vertex_elements):
            row = i // grid_size
            col = i % grid_size
            element.position = (col * spacing + 50, row * spacing + 50)
            element.size = (30, 30)
        
        return elements
    
    def _calculate_detailed_bounds(self, elements: List[ViewElement]) -> Tuple[float, float, float, float]:
        """Calculate bounds for detailed view."""
        if not elements:
            return (0.0, 0.0, 800.0, 600.0)
        
        # Find positioned elements
        positioned = [e for e in elements if e.position is not None]
        if not positioned:
            return (0.0, 0.0, 800.0, 600.0)
        
        min_x = min(e.position[0] for e in positioned)
        min_y = min(e.position[1] for e in positioned)
        max_x = max(e.position[0] + (e.size[0] if e.size else 30) for e in positioned)
        max_y = max(e.position[1] + (e.size[1] if e.size else 30) for e in positioned)
        
        # Add padding
        padding = 50
        return (min_x - padding, min_y - padding, max_x - min_x + 2*padding, max_y - min_y + 2*padding)


class TransformationViewGenerator(ViewGenerator):
    """Generates views showing transformation sequences."""
    
    def supports_view_type(self, view_type: ViewType) -> bool:
        return view_type == ViewType.TRANSFORMATION
    
    def generate_view(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> GeneratedView:
        """Generate transformation sequence view."""
        # This would show before/after states and transformation steps
        # Simplified implementation for now
        elements = []
        
        # Generate current state elements
        detail_generator = DetailedViewGenerator()
        detailed_view = detail_generator.generate_view(egi, config)
        elements.extend(detailed_view.elements)
        
        # Add transformation metadata
        for element in elements:
            element.metadata["transformation_state"] = "current"
        
        return GeneratedView(
            view_id=f"transformation_{id(egi)}",
            egi_id=getattr(egi, 'id', str(id(egi))),
            configuration=config,
            elements=elements,
            layout_bounds=detailed_view.layout_bounds,
            metadata={"generator": "TransformationViewGenerator"}
        )


class IntegratedViewManager:
    """
    Integrated view manager that provides unified, coherent view generation
    for EGIs using the core Dau formalism system.
    """
    
    def __init__(self, core_manager: CoreDauFormalismManager = None):
        self.logger = logging.getLogger(__name__)
        
        # Core formalism integration
        self.core_manager = core_manager or get_dau_formalism_manager()
        
        # View generators
        self.generators: Dict[ViewType, ViewGenerator] = {}
        self._initialize_generators()
        
        # View cache
        self.view_cache: Dict[str, GeneratedView] = {}
        self.cache_enabled = True
        
        # Default configurations
        self.default_configs = self._create_default_configurations()
        
        self.logger.info("IntegratedViewManager initialized with core formalism integration")
    
    def _initialize_generators(self):
        """Initialize view generators."""
        overview_gen = OverviewViewGenerator()
        detailed_gen = DetailedViewGenerator()
        transform_gen = TransformationViewGenerator()
        
        # Register generators by supported view types
        for view_type in ViewType:
            if overview_gen.supports_view_type(view_type):
                self.generators[view_type] = overview_gen
            elif detailed_gen.supports_view_type(view_type):
                self.generators[view_type] = detailed_gen
            elif transform_gen.supports_view_type(view_type):
                self.generators[view_type] = transform_gen
    
    def _create_default_configurations(self) -> Dict[ViewType, ViewConfiguration]:
        """Create default configurations for each view type."""
        return {
            ViewType.OVERVIEW: ViewConfiguration(
                view_type=ViewType.OVERVIEW,
                zoom_level=ViewLevel.MACRO,
                show_labels=True,
                show_cuts=True,
                show_polarity=False,
                spatial_layout=False
            ),
            ViewType.DETAILED: ViewConfiguration(
                view_type=ViewType.DETAILED,
                zoom_level=ViewLevel.INTERMEDIATE,
                show_labels=True,
                show_cuts=True,
                show_polarity=True,
                spatial_layout=True
            ),
            ViewType.HIERARCHICAL: ViewConfiguration(
                view_type=ViewType.HIERARCHICAL,
                zoom_level=ViewLevel.INTERMEDIATE,
                show_labels=False,
                show_cuts=True,
                show_polarity=True,
                show_nesting_levels=True,
                spatial_layout=False
            ),
            ViewType.TRANSFORMATION: ViewConfiguration(
                view_type=ViewType.TRANSFORMATION,
                zoom_level=ViewLevel.INTERMEDIATE,
                show_labels=True,
                show_cuts=True,
                show_polarity=True,
                spatial_layout=True
            )
        }
    
    # ========================================================================
    # Main View Generation Interface
    # ========================================================================
    
    def generate_view(self, egi: RelationalGraphWithCuts, view_type: ViewType = ViewType.DETAILED,
                     config: Optional[ViewConfiguration] = None) -> GeneratedView:
        """Generate a view of the EGI."""
        try:
            # Validate EGI first
            validation = self.core_manager.validate_egi(egi)
            if not validation.get("overall_valid", False):
                self.logger.warning(f"Generating view for invalid EGI: {validation.get('errors', [])}")
            
            # Use provided config or default
            if config is None:
                config = self.default_configs.get(view_type, self.default_configs[ViewType.DETAILED])
            
            # Check cache
            cache_key = self._generate_cache_key(egi, config)
            if self.cache_enabled and cache_key in self.view_cache:
                self.logger.debug(f"Returning cached view: {cache_key}")
                return self.view_cache[cache_key]
            
            # Get appropriate generator
            generator = self.generators.get(view_type)
            if not generator:
                raise ValueError(f"No generator available for view type: {view_type}")
            
            # Generate view
            view = generator.generate_view(egi, config)
            
            # Add generation timestamp
            from datetime import datetime
            view.generation_timestamp = datetime.now().isoformat()
            
            # Cache view
            if self.cache_enabled:
                self.view_cache[cache_key] = view
            
            self.logger.info(f"Generated {view_type.value} view with {len(view.elements)} elements")
            return view
            
        except Exception as e:
            self.logger.error(f"View generation failed: {e}")
            raise
    
    def generate_multiple_views(self, egi: RelationalGraphWithCuts, 
                               view_types: List[ViewType]) -> Dict[ViewType, GeneratedView]:
        """Generate multiple views of the same EGI."""
        views = {}
        
        for view_type in view_types:
            try:
                views[view_type] = self.generate_view(egi, view_type)
            except Exception as e:
                self.logger.error(f"Failed to generate {view_type.value} view: {e}")
        
        return views
    
    def generate_comparative_view(self, egis: List[RelationalGraphWithCuts], 
                                 config: Optional[ViewConfiguration] = None) -> GeneratedView:
        """Generate comparative view of multiple EGIs."""
        if not egis:
            raise ValueError("No EGIs provided for comparative view")
        
        if config is None:
            config = ViewConfiguration(
                view_type=ViewType.COMPARATIVE,
                zoom_level=ViewLevel.INTERMEDIATE,
                show_labels=True,
                show_cuts=True,
                spatial_layout=True
            )
        
        # Generate individual views
        individual_views = []
        for i, egi in enumerate(egis):
            view = self.generate_view(egi, ViewType.DETAILED, config)
            # Offset positions for side-by-side layout
            for element in view.elements:
                if element.position:
                    element.position = (element.position[0] + i * 400, element.position[1])
            individual_views.append(view)
        
        # Combine elements
        all_elements = []
        for view in individual_views:
            all_elements.extend(view.elements)
        
        # Calculate combined bounds
        if individual_views:
            bounds = individual_views[0].layout_bounds
            for view in individual_views[1:]:
                bounds = (
                    min(bounds[0], view.layout_bounds[0]),
                    min(bounds[1], view.layout_bounds[1]),
                    bounds[2] + view.layout_bounds[2],
                    max(bounds[3], view.layout_bounds[3])
                )
        else:
            bounds = (0, 0, 800, 600)
        
        return GeneratedView(
            view_id=f"comparative_{len(egis)}_egis",
            egi_id="comparative",
            configuration=config,
            elements=all_elements,
            layout_bounds=bounds,
            metadata={
                "generator": "IntegratedViewManager",
                "view_count": len(individual_views),
                "egi_count": len(egis)
            }
        )
    
    def generate_transformation_sequence_view(self, transformation_history: List[Dict[str, Any]]) -> GeneratedView:
        """Generate view showing transformation sequence."""
        if not transformation_history:
            raise ValueError("No transformation history provided")
        
        # This would create a timeline view of transformations
        # Simplified implementation for now
        elements = []
        
        for i, transform in enumerate(transformation_history):
            element = ViewElement(
                element_id=f"transform_{i}",
                element_type="transformation",
                position=(i * 150, 100),
                size=(120, 80),
                style={
                    "rule_name": transform.get("rule", "unknown"),
                    "success": transform.get("success", False)
                },
                metadata=transform
            )
            elements.append(element)
        
        bounds = (0, 0, len(transformation_history) * 150 + 100, 300)
        
        return GeneratedView(
            view_id="transformation_sequence",
            egi_id="sequence",
            configuration=ViewConfiguration(ViewType.TRANSFORMATION, ViewLevel.INTERMEDIATE),
            elements=elements,
            layout_bounds=bounds,
            metadata={"generator": "IntegratedViewManager", "sequence_length": len(transformation_history)}
        )
    
    # ========================================================================
    # View Management and Utilities
    # ========================================================================
    
    def get_supported_view_types(self) -> List[ViewType]:
        """Get list of supported view types."""
        return list(self.generators.keys())
    
    def clear_view_cache(self):
        """Clear the view cache."""
        self.view_cache.clear()
        self.logger.info("View cache cleared")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get view cache statistics."""
        return {
            "cached_views": len(self.view_cache),
            "cache_enabled": self.cache_enabled,
            "cache_keys": list(self.view_cache.keys())
        }
    
    def export_view(self, view: GeneratedView, format_type: str = "json") -> str:
        """Export view in specified format."""
        if format_type == "json":
            import json
            # Convert view to JSON-serializable format
            view_data = {
                "view_id": view.view_id,
                "egi_id": view.egi_id,
                "configuration": {
                    "view_type": view.configuration.view_type.value,
                    "zoom_level": view.configuration.zoom_level.value,
                    "show_labels": view.configuration.show_labels,
                    "show_cuts": view.configuration.show_cuts,
                    "show_polarity": view.configuration.show_polarity,
                    "spatial_layout": view.configuration.spatial_layout
                },
                "elements": [
                    {
                        "element_id": elem.element_id,
                        "element_type": elem.element_type,
                        "position": elem.position,
                        "size": elem.size,
                        "style": elem.style,
                        "metadata": elem.metadata,
                        "visible": elem.visible
                    }
                    for elem in view.elements
                ],
                "layout_bounds": view.layout_bounds,
                "metadata": view.metadata,
                "generation_timestamp": view.generation_timestamp
            }
            return json.dumps(view_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _generate_cache_key(self, egi: RelationalGraphWithCuts, config: ViewConfiguration) -> str:
        """Generate cache key for EGI and configuration."""
        egi_hash = hash(str(egi))  # Simple hash - would be more sophisticated
        config_hash = hash((
            config.view_type.value,
            config.zoom_level.value,
            tuple(config.focus_elements),
            config.show_labels,
            config.show_cuts,
            config.show_polarity,
            config.spatial_layout
        ))
        return f"{egi_hash}_{config_hash}"


# ============================================================================
# Global Instance Management
# ============================================================================

_global_view_manager: Optional[IntegratedViewManager] = None

def get_integrated_view_manager() -> IntegratedViewManager:
    """Get the global integrated view manager instance."""
    global _global_view_manager
    if _global_view_manager is None:
        _global_view_manager = IntegratedViewManager()
    return _global_view_manager

def reset_view_manager():
    """Reset global view manager (for testing)."""
    global _global_view_manager
    _global_view_manager = None
