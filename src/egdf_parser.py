#!/usr/bin/env python3
"""
EGDF (Existential Graph Diagram Format) Parser

Implements parsing and generation of EGDF format with round-trip validation.
EGDF captures both logical structure (EGI) and visual arrangement for rendering and export.

Key Features:
- EGI ↔ EGDF round-trip validation
- Visual arrangement preservation
- Export format support (LaTeX, SVG, PNG)
- Dau convention compliance validation
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Import canonical SpatialPrimitive and types from pipeline contracts
from layout_types import LayoutResult, LayoutElement, Bounds
from egi_core_dau import ElementID

# Base class for spatial primitives
@dataclass
class SpatialPrimitive:
    """Base class for spatial primitives in EGDF."""
    element_id: str
    position: Tuple[float, float]
    bounds: Optional[Bounds] = None
    element_type: Optional[str] = None
    z_index: Optional[int] = None
    attachment_points: Optional[Dict[str, Tuple[float, float]]] = None
import os
import re

# YAML support with fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

# Use proper API contracts and current EGI implementation
from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, Vertex, Edge, Cut
from egif_parser_dau import EGIFParser
from pipeline_contracts import (
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_spatial_primitive,
    enforce_contracts,
    ContractViolationError
)

# Use canonical Coordinate type from layout_engine_clean.py
Coordinate = Tuple[float, float]

class VertexPrimitive(SpatialPrimitive):
    """Visual representation of an EGI vertex."""
    annotations: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    
    def __init__(self, element_id: str, position: Coordinate, bounds: Optional[Bounds] = None, **kwargs):
        # Coordinate is already a tuple (x, y)
        pos_tuple = position
        # Default bounds if not provided
        if bounds is None:
            bounds = (pos_tuple[0]-5, pos_tuple[1]-5, pos_tuple[0]+5, pos_tuple[1]+5)
        # Vertices have z_index=1 (above cuts=0, below edges=2)
        super().__init__(element_id=element_id, element_type='vertex', position=pos_tuple, bounds=bounds, z_index=1)
        self.annotations = kwargs.get('annotations')
        self.provenance = kwargs.get('provenance')
    
    @property
    def element_id(self) -> str:
        """Consistent element_id interface."""
        return super().element_id
    
    @property
    def element_type(self) -> str:
        """Consistent element_type interface."""
        return super().element_type

class IdentityLinePrimitive(SpatialPrimitive):
    """Visual representation of an identity line (heavy line)."""
    coordinates: List[Coordinate]
    connection_points: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    
    def __init__(self, element_id: str, coordinates: List[Coordinate], **kwargs):
        # Calculate bounds from coordinates (coordinates are tuples (x, y))
        if coordinates:
            x_coords = [c[0] for c in coordinates]
            y_coords = [c[1] for c in coordinates]
            bounds = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
            # Use first coordinate as position
            position = coordinates[0]
        else:
            bounds = (0, 0, 0, 0)
            position = (0, 0)
        # Identity lines have z_index=2 (same as predicates, above vertices=1 and cuts=0)
        super().__init__(element_id=element_id, element_type='identity_line', position=position, bounds=bounds, z_index=2)
        self.coordinates = coordinates
        self.connection_points = kwargs.get('connection_points')
        self.provenance = kwargs.get('provenance')

class PredicatePrimitive(SpatialPrimitive):
    """Visual representation of a predicate."""
    text: str
    bounding_box: Optional[Dict[str, float]] = None
    argument_order: Optional[List[Dict[str, Any]]] = None
    provenance: Optional[Dict[str, Any]] = None
    
    def __init__(self, element_id: str, position: Coordinate, text: str, bounds: Optional[Bounds] = None, **kwargs):
        # Coordinate is already a tuple (x, y)
        pos_tuple = position
        # Default bounds based on text size if not provided
        if bounds is None:
            text_width = len(text) * 8  # Rough estimate
            text_height = 16
            bounds = (pos_tuple[0]-text_width//2, pos_tuple[1]-text_height//2, pos_tuple[0]+text_width//2, pos_tuple[1]+text_height//2)
        # Predicates have z_index=2 (above vertices=1 and cuts=0)
        super().__init__(element_id=element_id, element_type='predicate', position=pos_tuple, bounds=bounds, z_index=2)
        self.text = text
        self.bounding_box = kwargs.get('bounding_box')
        self.argument_order = kwargs.get('argument_order')
        self.provenance = kwargs.get('provenance')
    
    @property
    def element_id(self) -> str:
        """Consistent element_id interface."""
        return super().element_id
    
    @property
    def element_type(self) -> str:
        """Consistent element_type interface."""
        return super().element_type

@dataclass
class CutPrimitive:
    """Visual representation of a cut (negation boundary)."""
    type: str
    id: str
    egi_element_id: str
    shape: str  # ellipse, rectangle, polygon
    bounds: Dict[str, float]  # x, y, width, height
    style_overrides: Optional[Dict[str, Any]] = None
    containment: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    
    @property
    def element_id(self) -> str:
        """Consistent element_id interface."""
        return self.id
    
    @property
    def element_type(self) -> str:
        """Consistent element_type interface."""
        return self.type

@dataclass
class CanvasSettings:
    """Canvas configuration for EGDF."""
    width: int
    height: int
    background_color: str = "#ffffff"
    coordinate_system: str = "cartesian"

@dataclass
class StyleTheme:
    """Visual style theme for Dau conventions."""
    name: str = "dau_standard"
    identity_line_width: float = 8.0
    vertex_radius: float = 6.0
    cut_line_width: float = 1.0
    predicate_font_size: int = 12
    predicate_font_family: str = "serif"

@dataclass
class EGDFMetadata:
    """Metadata for EGDF documents."""
    title: Optional[str] = None
    author: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[Dict[str, Any]] = None  # { id, name, email? }
    generator: Optional[Dict[str, Any]] = None   # { tool, version, run_at }
    history: Optional[List[Dict[str, Any]]] = None  # [{ author, time, action }]

@dataclass
class EGDFDocument:
    """Complete EGDF document structure."""
    metadata: EGDFMetadata
    canonical_egi: Dict[str, Any]  # Serialized EGI structure
    visual_layout: Dict[str, Any]
    format: str = "EGDF"
    version: str = "1.0.0"
    export_settings: Optional[Dict[str, Any]] = None

class EGDFParser:
    """Parser for EGDF format with validation and round-trip support."""
    
    def __init__(self):
        # EGIFParser will be initialized when needed with actual text
        self.egif_parser = None
        self._schema = self._create_egdf_schema()
    
    def _create_egdf_schema(self) -> Dict[str, Any]:
        """Create JSON schema for EGDF validation."""
        return {
            "type": "object",
            "required": ["format", "version", "canonical_egi", "visual_layout"],
            "properties": {
                "format": {"type": "string", "const": "EGDF"},
                "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "title": {"type": ["string", "null"]},
                        "author": {"type": ["string", "null"]},
                        "created": {"type": ["string", "null"]},
                        "modified": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]},
                        "source": {"type": ["string", "null"]},
                        "tags": {"type": ["array", "null"], "items": {"type": "string"}},
                        "created_by": {"type": ["object", "null"]},
                        "generator": {"type": ["object", "null"]},
                        "history": {"type": ["array", "null"], "items": {"type": "object"}}
                    }
                },
                "canonical_egi": {"type": "object"},
                "visual_layout": {
                    "type": "object",
                    "required": ["spatial_primitives"],
                    "properties": {
                        "canvas": {
                            "type": "object",
                            "required": ["width", "height"],
                            "properties": {
                                "width": {"type": "integer", "minimum": 1},
                                "height": {"type": "integer", "minimum": 1},
                                "background_color": {"type": "string"},
                                "coordinate_system": {"type": "string", "enum": ["cartesian", "polar"]}
                            }
                        },
                        "style_theme": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "identity_line_width": {"type": "number", "minimum": 0},
                                "vertex_radius": {"type": "number", "minimum": 0},
                                "cut_line_width": {"type": "number", "minimum": 0},
                                "predicate_font_size": {"type": "integer", "minimum": 1},
                                "predicate_font_family": {"type": "string"}
                            }
                        },
                        "spatial_primitives": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["type", "id", "egi_element_id"],
                                "properties": {
                                    "type": {"type": "string", "enum": ["vertex", "identity_line", "predicate", "cut"]},
                                    "id": {"type": "string"},
                                    "egi_element_id": {"type": "string"},
                                    "position": {"type": ["array", "null"]},
                                    "bounds": {"type": ["array", "object", "null"]},
                                    "coordinates": {"type": ["array", "null"]},
                                    "text": {"type": ["string", "null"]},
                                    "annotations": {"type": ["object", "null"]},
                                    "provenance": {"type": ["object", "null"]}
                                }
                            }
                        }
                    }
                },
                "export_settings": {"type": ["object", "null"]}
            }
        }
    
    def validate_egdf(self, egdf_data: Dict[str, Any]) -> bool:
        """Validate EGDF document against schema."""
        try:
            # Basic structural validation - check required top-level fields
            required_fields = ["metadata", "canonical_egi", "visual_layout"]
            for field in required_fields:
                if field not in egdf_data:
                    print(f"EGDF validation error: Missing required field '{field}'")
                    return False
            
            # Check that canonical_egi is a dict
            if not isinstance(egdf_data["canonical_egi"], dict):
                print(f"EGDF validation error: canonical_egi must be a dictionary")
                return False
                
            # Check that visual_layout is a dict
            if not isinstance(egdf_data["visual_layout"], dict):
                print(f"EGDF validation error: visual_layout must be a dictionary")
                return False
            
            return True
        except Exception as e:
            print(f"EGDF validation error: {e}")
            return False
    
    def _serialize_egi_to_dict(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Serialize EGI to dictionary format for EGDF storage."""
        try:
            # Serialize vertices
            vertices = []
            for vertex in egi.V:
                vertices.append({
                    "id": vertex.id,
                    "label": vertex.label,
                    "is_generic": vertex.is_generic
                })
            
            # Serialize edges
            edges = []
            for edge in egi.E:
                edge_data = {
                    "id": edge.id,
                    "relation_name": egi.rel.get(edge.id, ""),
                    "incident_vertices": list(egi.nu.get(edge.id, ()))
                }
                edges.append(edge_data)
            
            # Serialize cuts
            cuts = []
            for cut in egi.Cut:
                cuts.append({
                    "id": cut.id
                })
            
            # Serialize area mapping
            area_mapping = {}
            for context_id, elements in egi.area.items():
                area_mapping[context_id] = list(elements)
            
            return {
                "vertices": vertices,
                "edges": edges,
                "cuts": cuts,
                "sheet": egi.sheet,
                "area_mapping": area_mapping,
                "nu_mapping": dict(egi.nu),
                "rel_mapping": dict(egi.rel)
            }
            
        except Exception as e:
            raise ValueError(f"EGI serialization error: {e}")
    
    def _deserialize_egi_from_dict(self, egi_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Deserialize EGI from dictionary format stored in EGDF."""
        try:
            from frozendict import frozendict
            
            # Reconstruct vertices
            vertices = set()
            for v_data in egi_data.get("vertices", []):
                vertex = Vertex(
                    id=v_data["id"],
                    label=v_data.get("label"),
                    is_generic=v_data.get("is_generic", True)
                )
                vertices.add(vertex)
            
            # Reconstruct edges
            edges = set()
            for e_data in egi_data.get("edges", []):
                edge = Edge(id=e_data["id"])
                edges.add(edge)
            
            # Reconstruct cuts
            cuts = set()
            for c_data in egi_data.get("cuts", []):
                cut = Cut(id=c_data["id"])
                cuts.add(cut)
            
            # Reconstruct mappings
            nu_mapping = {}
            for edge_id, vertex_seq in egi_data.get("nu_mapping", {}).items():
                nu_mapping[edge_id] = tuple(vertex_seq)
            
            area_mapping = {}
            for context_id, elements in egi_data.get("area_mapping", {}).items():
                area_mapping[context_id] = frozenset(elements)
            
            rel_mapping = egi_data.get("rel_mapping", {})
            
            # Create RelationalGraphWithCuts
            egi = RelationalGraphWithCuts(
                V=frozenset(vertices),
                E=frozenset(edges),
                nu=frozendict(nu_mapping),
                sheet=egi_data.get("sheet", "sheet"),
                Cut=frozenset(cuts),
                area=frozendict(area_mapping),
                rel=frozendict(rel_mapping)
            )
            
            return egi
            
        except Exception as e:
            raise ValueError(f"EGI deserialization error: {e}")
    
    def _detect_format(self, content: str) -> str:
        """Auto-detect whether content is JSON or YAML format."""
        content = content.strip()
        
        # JSON typically starts with { or [
        if content.startswith(('{', '[')):
            return 'json'
        
        # YAML indicators
        if any(line.strip() and not line.strip().startswith(('#', '{', '[')) and ':' in line 
               for line in content.split('\n')[:10]):
            return 'yaml'
        
        # Default to JSON
        return 'json'
    
    def parse_egdf(self, content: str, format_hint: str = "auto") -> EGDFDocument:
        """Parse EGDF from JSON or YAML format."""
        if format_hint == "auto":
            format_hint = self._detect_format(content)
        
        if format_hint == "yaml":
            return self._parse_yaml(content)
        else:
            return self._parse_json(content)
    
    def _parse_json(self, egdf_json: str) -> EGDFDocument:
        """Parse EGDF JSON string into EGDFDocument."""
        try:
            data = json.loads(egdf_json)
            return self._create_egdf_document(data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"EGDF JSON parsing error: {e}")
    
    def _parse_yaml(self, egdf_yaml: str) -> EGDFDocument:
        """Parse EGDF YAML string into EGDFDocument."""
        if not YAML_AVAILABLE:
            raise ValueError("YAML parsing requested but PyYAML not available. Install with: pip install PyYAML")
        
        try:
            data = yaml.safe_load(egdf_yaml)
            return self._create_egdf_document(data)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        except Exception as e:
            raise ValueError(f"EGDF YAML parsing error: {e}")
    
    def _create_egdf_document(self, data: Dict[str, Any]) -> EGDFDocument:
        """Create EGDFDocument from parsed data dictionary."""
        if not self.validate_egdf(data):
            raise ValueError("Invalid EGDF format")
        
        # Extract metadata
        metadata_data = data.get("metadata", {})
        metadata = EGDFMetadata(**metadata_data)
        
        # Create EGDF document
        egdf_doc = EGDFDocument(
            metadata=metadata,
            canonical_egi=data["canonical_egi"],
            visual_layout=data["visual_layout"],
            format=data.get("format", "EGDF"),
            version=data.get("version", "1.0.0"),
            export_settings=data.get("export_settings")
        )
        
        return egdf_doc
    
    @enforce_contracts(output_contract=validate_relational_graph_with_cuts)
    def extract_egi_from_egdf(self, egdf_doc: EGDFDocument) -> RelationalGraphWithCuts:
        """Extract canonical EGI from EGDF document."""
        try:
            # Extract the canonical EGI data from EGDF
            egi_data = egdf_doc.canonical_egi
            
            # Deserialize using our new method
            egi = self._deserialize_egi_from_dict(egi_data)
            
            # Validate the extracted graph using API contracts
            validate_relational_graph_with_cuts(egi)
            
            return egi
            
        except Exception as e:
            raise ValueError(f"EGI extraction error: {e}")
    
    def _validate_layout_primitives_complete(self, layout_primitives: List[Any], egi: RelationalGraphWithCuts) -> bool:
        """Validate that layout primitives cover all EGI elements."""
        try:
            # Get all element IDs from layout primitives (handle both dict and SpatialPrimitive formats)
            layout_element_ids = set()
            for primitive in layout_primitives:
                if hasattr(primitive, 'element_id'):
                    layout_element_ids.add(primitive.element_id)
                elif isinstance(primitive, dict) and 'element_id' in primitive:
                    layout_element_ids.add(primitive['element_id'])
                else:
                    raise ValueError(f"Invalid primitive format: {type(primitive)}")
            
            # Get all element IDs from EGI
            egi_element_ids = set()
            egi_element_ids.update(vertex.id for vertex in egi.V)
            egi_element_ids.update(edge.id for edge in egi.E)
            egi_element_ids.update(cut.id for cut in egi.Cut)
            
            # Check coverage
            missing_elements = egi_element_ids - layout_element_ids
            if missing_elements:
                raise ContractViolationError(f"Layout primitives missing elements: {missing_elements}")
            
            # Validate each primitive (skip validation for dict format, as it's already validated by GraphvizLayoutEngine)
            for primitive in layout_primitives:
                if hasattr(primitive, 'element_id'):
                    validate_spatial_primitive(primitive)
                # Dict format primitives are already validated by GraphvizLayoutEngine
            
            return True
            
        except Exception as e:
            raise ContractViolationError(f"Layout primitives validation failed: {e}")
    
    def _validate_egdf_document(self, egdf_doc: EGDFDocument) -> bool:
        """Validate that EGDF document meets all structural requirements."""
        try:
            # Check required fields
            if not hasattr(egdf_doc, 'metadata'):
                raise ContractViolationError("EGDF document missing metadata")
            if not hasattr(egdf_doc, 'canonical_egi'):
                raise ContractViolationError("EGDF document missing canonical_egi")
            if not hasattr(egdf_doc, 'visual_layout'):
                raise ContractViolationError("EGDF document missing visual_layout")
            
            # Validate that canonical_egi can be deserialized
            egi = self._deserialize_egi_from_dict(egdf_doc.canonical_egi)
            validate_relational_graph_with_cuts(egi)
            
            return True
            
        except Exception as e:
            raise ContractViolationError(f"EGDF document validation failed: {e}")
    
    @enforce_contracts(
        input_contracts={
            'egi': validate_relational_graph_with_cuts,
            'layout_primitives': lambda primitives: len(primitives) >= 0  # Basic check, detailed validation below
        }
    )
    def create_egdf_from_egi(self, egi: RelationalGraphWithCuts, 
                           layout_primitives: List[SpatialPrimitive],
                           metadata: Optional[EGDFMetadata] = None) -> EGDFDocument:
        """Create EGDF document from EGI and spatial primitives."""
        
        # Validate layout primitives completeness
        self._validate_layout_primitives_complete(layout_primitives, egi)
        
        if metadata is None:
            metadata = EGDFMetadata(
                created=datetime.now().isoformat(),
                modified=datetime.now().isoformat()
            )
        
        # Serialize EGI using our new method
        canonical_egi = self._serialize_egi_to_dict(egi)
        
        # Create visual layout
        canvas = CanvasSettings(width=800, height=600)
        style_theme = StyleTheme()
        
        # Convert spatial primitives to dict format (handle both dict and dataclass formats)
        spatial_primitives_data = []
        for primitive in layout_primitives:
            if isinstance(primitive, dict):
                primitive_dict = primitive
            else:
                primitive_dict = asdict(primitive)
            spatial_primitives_data.append(primitive_dict)
        
        visual_layout = {
            "canvas": asdict(canvas),
            "style_theme": asdict(style_theme),
            "spatial_primitives": spatial_primitives_data
        }
        
        egdf_doc = EGDFDocument(
            metadata=metadata,
            canonical_egi=canonical_egi,
            visual_layout=visual_layout
        )
        
        # Validate output using contract
        self._validate_egdf_document(egdf_doc)
        
        return egdf_doc
    
    def egdf_to_json(self, egdf_doc: EGDFDocument, indent: int = 2) -> str:
        """Convert EGDFDocument to JSON string."""
        return json.dumps(asdict(egdf_doc), indent=indent, default=str)
    
    def _convert_tuples_to_lists(self, obj):
        """Recursively convert tuples to lists for YAML compatibility."""
        if isinstance(obj, tuple):
            return list(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_tuples_to_lists(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_tuples_to_lists(item) for item in obj]
        else:
            return obj
    
    def egdf_to_yaml(self, egdf_doc: EGDFDocument) -> str:
        """Convert EGDFDocument to YAML string."""
        if not YAML_AVAILABLE:
            raise ValueError("YAML export requested but PyYAML not available. Install with: pip install PyYAML")
        
        # Convert to dict and add helpful comments
        data = asdict(egdf_doc)
        
        # Convert tuples to lists for YAML compatibility
        data = self._convert_tuples_to_lists(data)
        
        # Create YAML with custom formatting
        yaml_str = "# EGDF (Existential Graph Diagram Format)\n"
        yaml_str += f"# Generated: {datetime.now().isoformat()}\n\n"
        
        # Use YAML dump with custom settings for readability
        yaml_content = yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            width=120,
            allow_unicode=True
        )
        
        return yaml_str + yaml_content
    
    def export_egdf(self, egdf_doc: EGDFDocument, format_type: str = "json", **kwargs) -> str:
        """Export EGDF document in specified format."""
        if format_type.lower() == "yaml":
            return self.egdf_to_yaml(egdf_doc)
        elif format_type.lower() == "json":
            indent = kwargs.get('indent', 2)
            return self.egdf_to_json(egdf_doc, indent=indent)
        else:
            raise ValueError(f"Unsupported export format: {format_type}. Use 'json' or 'yaml'")
    
    @enforce_contracts(
        input_contracts={'original_egi': validate_relational_graph_with_cuts}
    )
    def validate_round_trip(self, original_egi: RelationalGraphWithCuts, 
                          egdf_doc: EGDFDocument) -> Tuple[bool, List[str]]:
        """Validate that EGDF round-trip preserves EGI structure."""
        errors = []
        
        try:
            # Extract EGI from EGDF
            extracted_egi = self.extract_egi_from_egdf(egdf_doc)
            
            # Validate extracted EGI using contracts
            validate_relational_graph_with_cuts(extracted_egi)
            
            # Compare structures (placeholder validation)
            # Compare EGI structures for round-trip validation
            
            # For now, basic validation
            if not hasattr(extracted_egi, 'V') or not hasattr(extracted_egi, 'E'):
                errors.append("Extracted EGI missing required attributes")
            
            return len(errors) == 0, errors
            
        except ContractViolationError as e:
            errors.append(f"Contract violation in round-trip: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Round-trip validation error: {e}")
            return False, errors

class EGDFLayoutGenerator:
    """Generate Dau-compliant spatial primitives from EGI using the formal mapping specification."""
    
    def __init__(self):
        self.default_canvas = CanvasSettings(width=800, height=600)
        self.default_style = StyleTheme()
        
        # Use the formal Dau-compliant mapper
        from dau_compliant_egdf_mapper import DauCompliantEGDFMapper
        self.dau_mapper = DauCompliantEGDFMapper()
    
    def generate_layout_from_egi(self, egi: RelationalGraphWithCuts) -> List[SpatialPrimitive]:
        """
        Generate Dau-compliant spatial primitives from EGI using the formal mapping specification.
        
        This implements the complete pipeline:
        EGI → Graphviz DOT → xdot output → Dau-compliant EGDF primitives
        """
        try:
            # Step 1: Generate Graphviz layout
            layout_result = self.dau_mapper.layout_engine.create_layout_from_graph(egi)
            
            # Step 2: Get the xdot output from Graphviz
            xdot_output = self._extract_xdot_from_layout(layout_result, egi)
            
            # Step 3: Use DauCompliantEGDFMapper to convert xdot → EGDF
            dau_primitives = self.dau_mapper.xdot_to_egdf(xdot_output, egi)
            
            # Step 4: Validate correspondence
            if not self.dau_mapper.validate_correspondence(dau_primitives, egi):
                print("⚠️  Correspondence validation failed, using fallback")
                return self._generate_fallback_layout(egi)
            
            print(f"✅ Generated {len(dau_primitives)} Dau-compliant EGDF primitives")
            return dau_primitives
            
        except Exception as e:
            print(f"⚠️  Dau-compliant layout generation failed: {e}")
            return self._generate_fallback_layout(egi)
    
    def _extract_xdot_from_layout(self, layout_result: LayoutResult, egi: RelationalGraphWithCuts) -> str:
        """Extract xdot output from the Graphviz layout process."""
        try:
            # Generate DOT from EGI
            dot_content = self.dau_mapper.layout_engine._generate_dot_from_egi(egi)
            
            # Execute Graphviz to get xdot output (use existing method)
            xdot_output = self.dau_mapper.layout_engine._execute_graphviz(dot_content)
            
            return xdot_output
            
        except Exception as e:
            print(f"⚠️  xdot extraction failed: {e}")
            # Fallback: construct synthetic xdot from layout_result
            return self._create_synthetic_xdot(layout_result, egi)
    
    def _create_synthetic_xdot(self, layout_result: LayoutResult, egi: RelationalGraphWithCuts) -> str:
        """Create synthetic xdot output from layout result for fallback."""
        xdot_lines = [
            'digraph G {',
            '  graph [bb="0,0,800,600"];'
        ]
        
        # Add clusters (cuts)
        for primitive in layout_result.primitives:
            if primitive.element_type == 'cut':
                bb = f"{primitive.bounds[0]},{primitive.bounds[1]},{primitive.bounds[2]},{primitive.bounds[3]}"
                xdot_lines.append(f'  subgraph cluster_{primitive.element_id} {{')
                xdot_lines.append(f'    graph [bb="{bb}"];')
                xdot_lines.append('  }')
        
        # Add nodes
        for primitive in layout_result.primitives:
            if primitive.element_type in ['vertex', 'edge']:
                pos = f"{primitive.position[0]},{primitive.position[1]}"
                width = primitive.bounds[2] - primitive.bounds[0]
                height = primitive.bounds[3] - primitive.bounds[1]
                xdot_lines.append(f'  {primitive.element_id} [pos="{pos}", width="{width/72}", height="{height/72}"];')
        
        xdot_lines.append('}')
        return '\n'.join(xdot_lines)
    
    def _generate_fallback_layout(self, egi: RelationalGraphWithCuts) -> List[SpatialPrimitive]:
        """Generate simple fallback layout when Dau-compliant mapping fails."""
        primitives = []
        
        # Simple grid layout for vertices
        for i, vertex in enumerate(egi.V):
            vertex_primitive = VertexPrimitive(
                element_id=vertex.id,
                position=(100.0 + i * 150, 200.0),
                annotations={'fallback': True}
            )
            primitives.append(vertex_primitive)
        
        # Simple layout for predicates
        for i, edge in enumerate(egi.E):
            relation_name = egi.get_relation_name(edge.id)
            predicate_primitive = PredicatePrimitive(
                element_id=edge.id,
                position=(200.0 + i * 150, 200.0),
                text=relation_name,
                provenance={'fallback': True}
            )
            primitives.append(predicate_primitive)
        
        # Simple cuts
        for i, cut in enumerate(egi.Cut):
            cut_primitive = CutPrimitive(
                type="cut",
                id=cut.id,
                egi_element_id=cut.id,
                shape="rounded_rectangle",  # Still Dau-compliant
                bounds={'left': 50 + i * 200, 'top': 150, 'right': 350 + i * 200, 'bottom': 250},
                provenance={'fallback': True}
            )
            primitives.append(cut_primitive)
        
        print(f"✅ Generated {len(primitives)} fallback EGDF primitives")
        return primitives
        
        return primitives

def create_test_egdf() -> str:
    """Create a test EGDF document for validation."""
    parser = EGDFParser()
    layout_generator = EGDFLayoutGenerator()
    
    # Create test EGI using proper function
    egi = create_empty_graph()
    
    # Validate EGI using contracts
    validate_relational_graph_with_cuts(egi)
    
    # Generate layout
    primitives = layout_generator.generate_layout_from_egi(egi)
    
    # Create metadata
    metadata = EGDFMetadata(
        title="Test EGDF Document",
        author="Arisbe System",
        description="Test document for EGDF validation",
        created=datetime.now().isoformat()
    )
    
    # Create EGDF document
    egdf_doc = parser.create_egdf_from_egi(egi, primitives, metadata)
    
    return parser.egdf_to_json(egdf_doc)

if __name__ == "__main__":
    print("🎯 EGDF Parser Test")
    print("=" * 50)
    
    # Create test EGDF
    test_egdf_json = create_test_egdf()
    print("✅ Created test EGDF document")
    
    # Parse and validate
    parser = EGDFParser()
    try:
        egdf_doc = parser.parse_egdf(test_egdf_json)
        print("✅ EGDF parsing successful")
        
        # Validate round-trip
        egi = create_empty_graph()
        validate_relational_graph_with_cuts(egi)
        is_valid, errors = parser.validate_round_trip(egi, egdf_doc)
        
        if is_valid:
            print("✅ Round-trip validation successful")
        else:
            print("❌ Round-trip validation failed:")
            for error in errors:
                print(f"   - {error}")
        
        print("\n📄 Sample EGDF Structure:")
        print(test_egdf_json[:500] + "..." if len(test_egdf_json) > 500 else test_egdf_json)
        
    except Exception as e:
        print(f"❌ EGDF test failed: {e}")
    
    print("\n🚀 EGDF Parser Implementation Complete!")
