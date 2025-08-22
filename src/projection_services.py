#!/usr/bin/env python3
"""
Projection Services - Generate Linear and Visual Forms from EGI

These services generate EGIF, EGDF, and other representations from the canonical EGI state.
All forms are projections of the EGI - no independent state is maintained.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from egi_core_dau import RelationalGraphWithCuts
from egdf_parser import EGDFDocument
from layout_phase_implementations import AreaCompactionPhase
from spatial_awareness_system import SpatialAwarenessSystem


class ProjectionService(ABC):
    """Base class for EGI projection services."""
    
    @abstractmethod
    def project(self, egi: RelationalGraphWithCuts, **kwargs) -> Any:
        """Generate projection from EGI state."""
        pass


class EGIFProjectionService(ProjectionService):
    """Generate EGIF linear form from EGI."""
    
    def project(self, egi: RelationalGraphWithCuts, **kwargs) -> str:
        """Convert EGI to EGIF string representation."""
        # Use existing EGIF generation logic
        from egif_generator_dau import EGIFGenerator
        generator = EGIFGenerator()
        return generator.generate_egif(egi)


class EGDFProjectionService(ProjectionService):
    """Generate EGDF visual form from EGI using layout pipeline."""
    
    def __init__(self):
        self.spatial_system = SpatialAwarenessSystem()
        self.layout_phase = AreaCompactionPhase()
    
    def project(self, egi: RelationalGraphWithCuts, **kwargs) -> EGDFDocument:
        """Convert EGI to EGDF document with spatial layout."""
        # Run minimal pipeline to generate spatial layout
        context = self._prepare_layout_context(egi, **kwargs)
        
        # Execute layout phase to generate EGDF
        result = self.layout_phase.execute(egi, context)
        
        if result.status.name == 'COMPLETED' and 'egdf_document' in context:
            return context['egdf_document']
        else:
            raise RuntimeError(f"EGDF projection failed: {result.error_message}")
    
    def _prepare_layout_context(self, egi: RelationalGraphWithCuts, **kwargs) -> Dict[str, Any]:
        """Prepare minimal context for layout generation."""
        # Create basic element dimensions
        element_dimensions = {}
        for vertex in egi.V:
            element_dimensions[vertex.id] = {'width': 0.1, 'height': 0.05}
        for edge in egi.E:
            element_dimensions[edge.id] = {'width': 0.08, 'height': 0.03}
        for cut in egi.Cut:
            element_dimensions[cut.id] = {'width': 0.2, 'height': 0.15}
        
        # Basic spatial context
        context = {
            'element_dimensions': element_dimensions,
            'logical_system': self.spatial_system.create_logical_coordinate_system(),
            'logical_bounds': {},
            'cluster_bounds': {},
            'working_bounds': None,
            'collision_free_positions': {},
            'spatial_violations': [],
            'predicate_elements': {},
            'vertex_elements': {},
            'element_tracking': {}
        }
        
        # Apply any custom layout parameters
        context.update(kwargs.get('layout_params', {}))
        
        return context


class ProjectionManager:
    """Manages all projection services and coordinates updates."""
    
    def __init__(self):
        self.services: Dict[str, ProjectionService] = {
            'egif': EGIFProjectionService(),
            'egdf': EGDFProjectionService()
        }
        self.cache: Dict[str, Any] = {}
        self.cache_valid = False
    
    def register_service(self, name: str, service: ProjectionService):
        """Register a new projection service."""
        self.services[name] = service
    
    def project_to(self, format_name: str, egi: RelationalGraphWithCuts, **kwargs) -> Any:
        """Generate projection in specified format."""
        if format_name not in self.services:
            raise ValueError(f"Unknown projection format: {format_name}")
        
        # Check cache first
        cache_key = f"{format_name}_{id(egi)}"
        if self.cache_valid and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Generate projection
        result = self.services[format_name].project(egi, **kwargs)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def invalidate_cache(self):
        """Invalidate projection cache when EGI changes."""
        self.cache.clear()
        self.cache_valid = False
    
    def on_egi_changed(self, egi: RelationalGraphWithCuts, operation):
        """Callback for EGI repository changes."""
        self.invalidate_cache()


# Factory functions
def create_projection_manager() -> ProjectionManager:
    """Create a new projection manager with default services."""
    return ProjectionManager()

def create_egif_service() -> EGIFProjectionService:
    """Create EGIF projection service."""
    return EGIFProjectionService()

def create_egdf_service() -> EGDFProjectionService:
    """Create EGDF projection service."""
    return EGDFProjectionService()
