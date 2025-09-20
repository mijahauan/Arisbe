"""
Test Layout Engine Foundation - Phase 1 Implementation
"""

import pytest
from src.layout_engine import LayoutEngine, Point, BoundingBox
from src.egi_core_dau import create_empty_graph, create_vertex, create_cut


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
