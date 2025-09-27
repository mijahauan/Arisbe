"""
Style Specification for EGI Layout Engine

Defines the structure and types for customizable styling of EGI diagrams.
Implements a "smart engine, simple spec" architecture where the engine contains
the logic for when to apply styles, driven by declarative style specifications.
"""

from typing import TypedDict, Dict, Any, Optional
from dataclasses import dataclass, field


class GraphvizAttrs(TypedDict, total=False):
    """Graphviz attributes for graph, node, and edge styling"""
    graph: Dict[str, Any]
    node: Dict[str, Any] 
    edge: Dict[str, Any]


class LayoutConfig(TypedDict, total=False):
    """Layout configuration section"""
    engine: str  # 'neato', 'fdp', 'sfdp', etc.
    graphviz_attrs: GraphvizAttrs


class PaddingConfig(TypedDict, total=False):
    """Padding configuration for geometric elements"""
    area: float  # Padding around cut boundaries
    label: float  # Padding around text labels


class GeometryConfig(TypedDict, total=False):
    """Geometry configuration section"""
    padding: PaddingConfig
    port_style: str  # 'boundary_midpoint', 'center', 'edge_closest'


class CutRenderingConfig(TypedDict, total=False):
    """Cut rendering configuration"""
    shape: str  # 'rounded_rectangle', 'rectangle', 'ellipse'
    stroke_width: float
    odd_fill: str  # Fill color for odd-depth cuts (negative areas)
    even_fill: str  # Fill color for even-depth cuts (positive areas)
    double_cut_stroke_width: float


class LigatureRenderingConfig(TypedDict, total=False):
    """Ligature rendering configuration"""
    stroke_width: float
    color: str


class LabelRenderingConfig(TypedDict, total=False):
    """Label rendering configuration"""
    font_color: str


class RenderingConfig(TypedDict, total=False):
    """Rendering configuration section"""
    cuts: CutRenderingConfig
    ligatures: LigatureRenderingConfig
    labels: LabelRenderingConfig


class AnnotationConfig(TypedDict, total=False):
    """Annotation configuration section"""
    show_vertex_variables: bool
    highlight_double_cuts: bool
    show_connection_ports: bool  # Show connection ports on edge labels


class StyleSpecification(TypedDict):
    """Complete style specification structure"""
    name: str
    layout: LayoutConfig
    geometry: GeometryConfig
    rendering: RenderingConfig
    annotations: AnnotationConfig


@dataclass
class RenderableAnnotation:
    """Annotation object for additional visual elements"""
    id: str
    parent_area_id: str
    annotation_type: str  # 'vertex_variable', 'double_cut_highlight', etc.
    position: tuple[float, float]
    text: Optional[str] = None
    style: Dict[str, Any] = field(default_factory=dict)


def load_default_dau_style() -> StyleSpecification:
    """Load the default Dau Treatise style specification"""
    return {
        "name": "Dau Treatise Default",
        "layout": {
            "engine": "neato",
            "graphviz_attrs": {
                "graph": {
                    "sep": "0.6",
                    "splines": "true",
                    "overlap": "false"
                },
                "node": {
                    "fontname": "Times-Roman",
                    "fontsize": "12"
                },
                "edge": {}
            }
        },
        "geometry": {
            "padding": {
                "area": 15,
                "label": 5
            },
            "port_style": "boundary_midpoint"
        },
        "rendering": {
            "cuts": {
                "shape": "rounded_rectangle",
                "stroke_width": 1.0,
                "odd_fill": "rgba(240, 240, 240, 0.5)",
                "even_fill": "transparent",
                "double_cut_stroke_width": 2.0
            },
            "ligatures": {
                "stroke_width": 2.5,
                "color": "black"
            },
            "labels": {
                "font_color": "black"
            }
        },
        "annotations": {
            "show_vertex_variables": False,
            "highlight_double_cuts": False
        }
    }


def create_style_from_json(json_path: str) -> StyleSpecification:
    """Load style specification from JSON file"""
    import json
    from pathlib import Path
    
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Style file not found: {json_path}")
    
    with open(path, 'r') as f:
        return json.load(f)


def create_style_from_yaml(yaml_path: str) -> StyleSpecification:
    """Load style specification from YAML file"""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML style files. Install with: pip install PyYAML")
    
    from pathlib import Path
    
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Style file not found: {yaml_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)
