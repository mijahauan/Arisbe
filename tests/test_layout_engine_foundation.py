"""
Test Layout Engine Foundation - Phase 1 Implementation
"""

import pytest
from src.layout_engine import LayoutEngine, Point, BoundingBox, ViewConfiguration
from src.egi_core_dau import create_empty_graph, create_vertex, create_cut
from src.style_aware_layout import StyleAwareLayoutEngine


class TestLayoutEngineFoundation:
    
    def test_empty_graph_layout(self):
        """Test layout of empty graph"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        result = engine.compute_layout(egi)
        
        assert len(result.vertex_positions) == 0
        assert len(result.cut_bounds) == 0
        assert isinstance(result.viewport_bounds, BoundingBox)
    
    def test_single_vertex_layout(self):
        """Test layout with single vertex"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        result = engine.compute_layout(egi)
        
        assert len(result.vertex_positions) == 1
        assert vertex.id in result.vertex_positions
        position = result.vertex_positions[vertex.id]
        assert position.x == 50.0
        assert position.y == 50.0
    
    def test_cut_containment_enforcement(self):
        """Test cut bounds contain their elements"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        
        # Create cut first
        cut = create_cut()
        egi = egi.with_cut(cut)
        
        # Create vertex and add it to the cut's context
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex_in_context(vertex, cut.id)
        
        result = engine.compute_layout(egi)
        
        # Verify containment
        assert cut.id in result.cut_bounds
        cut_bounds = result.cut_bounds[cut.id]
        vertex_pos = result.vertex_positions[vertex.id]
        assert cut_bounds.contains_point(vertex_pos)
    
    def test_spatial_compliance_validation(self):
        """Test spatial compliance validation against EGI"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        
        # Create nested cuts structure
        outer_cut = create_cut()
        inner_cut = create_cut()
        vertex = create_vertex(label="Human", is_generic=False)
        
        # Build: outer_cut contains inner_cut contains vertex
        egi = egi.with_cut(outer_cut)
        egi = egi.with_cut(inner_cut, outer_cut.id)  # inner_cut in outer_cut
        egi = egi.with_vertex_in_context(vertex, inner_cut.id)  # vertex in inner_cut
        
        result = engine.compute_layout(egi)
        compliance = result.validate_spatial_compliance(egi)
        
        # Should be compliant - layout engine enforces containment
        assert compliance.is_compliant
        assert len(compliance.violations) == 0
    
    def test_view_configuration_support(self):
        """Test layout engine accepts view configuration"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        # Create custom view configuration
        view_config = ViewConfiguration(
            focus_element=vertex.id,
            vertex_spacing=100.0,
            zoom_level=1.5
        )
        
        result = engine.compute_layout(egi, view_config)
        
        # Should still produce valid layout
        assert len(result.vertex_positions) == 1
        assert vertex.id in result.vertex_positions
    
    def test_layout_result_is_immutable_dto(self):
        """Test that LayoutResult is immutable DTO"""
        engine = LayoutEngine()
        egi = create_empty_graph()
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        result = engine.compute_layout(egi)
        
        # Should be frozen dataclass (immutable) - test the dataclass itself
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            result.viewport_bounds = BoundingBox(0, 0, 1, 1)
        
        # Should contain all required spatial data
        assert hasattr(result, 'cut_bounds')
        assert hasattr(result, 'vertex_positions') 
        assert hasattr(result, 'edge_paths')
        assert hasattr(result, 'viewport_bounds')
        
        # Verify it's a complete DTO with all spatial information
        assert isinstance(result.cut_bounds, dict)
        assert isinstance(result.vertex_positions, dict)
        assert isinstance(result.edge_paths, dict)
        assert isinstance(result.viewport_bounds, BoundingBox)
    
    def test_style_aware_layout_engine(self):
        """Test style-aware layout engine foundation"""
        style_engine = StyleAwareLayoutEngine()
        egi = create_empty_graph()
        vertex = create_vertex(label="Human", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        # Test with None style (should use defaults)
        result = style_engine.base_engine.compute_layout(egi)
        assert len(result.vertex_positions) == 1
        assert vertex.id in result.vertex_positions
