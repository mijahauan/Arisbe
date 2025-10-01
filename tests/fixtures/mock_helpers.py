"""
Mock helpers for unit testing.

Provides mock objects and utilities for isolated testing.
"""

from unittest.mock import Mock, MagicMock
from typing import List, Tuple, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


def create_mock_layout_engine():
    """
    Create a mock LayoutEngine for testing DiagramController in isolation.
    
    Returns:
        Mock LayoutEngine that returns a simple mock DTO
    """
    mock_engine = Mock()
    mock_dto = create_mock_dto()
    mock_engine.generate_layout.return_value = mock_dto
    return mock_engine


def create_mock_dto(vertex_count: int = 1, edge_count: int = 1, cut_count: int = 0):
    """
    Create a mock LayoutDTO with specified element counts.
    
    Args:
        vertex_count: Number of vertices to include
        edge_count: Number of edges to include
        cut_count: Number of cuts to include
        
    Returns:
        Mock LayoutDTO
    """
    mock_dto = Mock()
    
    # Create mock vertices
    mock_dto.vertices = [
        create_mock_vertex(f'v{i}', (50.0 + i*100, 50.0 + i*100))
        for i in range(vertex_count)
    ]
    
    # Create mock edges
    mock_dto.edge_labels = [
        create_mock_edge(f'e{i}', [f'v{i}'])
        for i in range(edge_count)
    ]
    
    # Create mock cuts
    mock_dto.cuts = [
        create_mock_cut(f'c{i}', i % 2)
        for i in range(cut_count)
    ]
    
    mock_dto.areas = {}
    mock_dto.ligature_paths = []
    
    return mock_dto


def create_mock_vertex(vertex_id: str, pos: Tuple[float, float]):
    """Create a mock vertex with specified ID and position."""
    mock_vertex = Mock()
    mock_vertex.id = vertex_id
    mock_vertex.pos = pos
    mock_vertex.label = f"Vertex_{vertex_id}"
    mock_vertex.style = {}
    return mock_vertex


def create_mock_edge(edge_id: str, vertex_ids: List[str]):
    """Create a mock edge with specified ID and vertices."""
    mock_edge = Mock()
    mock_edge.id = edge_id
    mock_edge.vertex_ids = vertex_ids
    mock_edge.label = f"Edge_{edge_id}"
    mock_edge.pos = (100.0, 100.0)
    mock_edge.style = {}
    return mock_edge


def create_mock_cut(cut_id: str, polarity: int):
    """Create a mock cut with specified ID and polarity."""
    mock_cut = Mock()
    mock_cut.id = cut_id
    mock_cut.polarity = polarity
    mock_cut.bounds = (0.0, 0.0, 200.0, 200.0)
    mock_cut.style = {}
    return mock_cut


def create_mock_style_specification():
    """Create a mock StyleSpecification."""
    return {
        'layout': {
            'padding': {
                'cut_padding': 20.0,
                'element_padding': 10.0,
                'min_cut_size': 60.0
            },
            'graphviz_attrs': {}
        },
        'cuts': {
            'even_cuts': {'fill': '#FFFFFF', 'opacity': 0.0},
            'odd_cuts': {'fill': '#CCCCCC', 'opacity': 0.3}
        },
        'vertices': {},
        'edges': {},
        'annotations': {
            'show_vertex_variables': False,
            'show_arity_numbers': False
        }
    }
