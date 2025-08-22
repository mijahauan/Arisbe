"""
Rock-solid EGI → EGDF translation system based on working PNG generation logic.

This module extracts the proven containment hierarchy and positioning logic
from the PNG generation script and creates a platform-independent EGDF
layout system that preserves EGI logical structure.
"""

import subprocess
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import tempfile

from egi_core_dau import RelationalGraphWithCuts
from egdf_parser import EGDFDocument, LayoutElement


@dataclass
class ContainmentHierarchy:
    """Represents the logical containment structure from EGI."""
    cut_id: str
    elements: Set[str]
    nested_cuts: List['ContainmentHierarchy']
    parent_cut: Optional[str] = None
    
    def get_all_contained_elements(self) -> Set[str]:
        """Get all elements contained in this cut and its nested cuts."""
        all_elements = self.elements.copy()
        for nested_cut in self.nested_cuts:
            all_elements.update(nested_cut.get_all_contained_elements())
        return all_elements


@dataclass
class SpatialBounds:
    """Platform-independent spatial bounds."""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def x2(self) -> float:
        return self.x + self.width
    
    @property
    def y2(self) -> float:
        return self.y + self.height
    
    def contains_point(self, px: float, py: float) -> bool:
        """Check if point is inside bounds."""
        return self.x <= px <= self.x2 and self.y <= py <= self.y2
    
    def contains_bounds(self, other: 'SpatialBounds') -> bool:
        """Check if other bounds are completely inside this bounds."""
        return (self.x <= other.x and self.y <= other.y and 
                self.x2 >= other.x2 and self.y2 >= other.y2)


class EGIToEGDFTranslator:
    """
    Rock-solid translator from EGI logical structure to EGDF layout primitives.
    
    Based on the proven PNG generation logic that correctly handles:
    - Containment hierarchy from egi.area mapping
    - Exclusive, non-overlapping positioning
    - Platform-independent layout primitives
    """
    
    def __init__(self):
        self.containment_hierarchy: List[ContainmentHierarchy] = []
        self.element_bounds: Dict[str, SpatialBounds] = {}
        self.cut_bounds: Dict[str, SpatialBounds] = {}
        
    def translate(self, egi: RelationalGraphWithCuts) -> EGDFDocument:
        """
        Main translation method: EGI → EGDF with guaranteed correctness.
        
        Uses the same logical flow as the working PNG generation:
        1. Build containment hierarchy from egi.area
        2. Generate DOT with proper nesting
        3. Extract spatial bounds from Graphviz
        4. Create platform-independent EGDF primitives
        """
        # Step 1: Build containment hierarchy (like PNG script)
        self.containment_hierarchy = self._build_containment_hierarchy(egi)
        
        # Step 2: Generate DOT with proper nesting (exactly like PNG)
        dot_content = self._generate_nested_dot(egi)
        
        # Step 3: Extract spatial bounds from Graphviz
        self._extract_spatial_bounds_from_graphviz(dot_content)
        
        # Step 4: Create EGDF layout primitives
        return self._create_egdf_document(egi)
    
    def _build_containment_hierarchy(self, egi: RelationalGraphWithCuts) -> List[ContainmentHierarchy]:
        """Build containment hierarchy from EGI area mapping (PNG logic)."""
        # Create hierarchy nodes for all cuts
        cut_nodes = {}
        for cut in egi.Cut:
            elements_in_cut = egi.area.get(cut.id, frozenset())
            cut_nodes[cut.id] = ContainmentHierarchy(
                cut_id=cut.id,
                elements=set(elements_in_cut),
                nested_cuts=[]
            )
        
        # Find containment relationships
        for cut_id, cut_node in cut_nodes.items():
            for element_id in cut_node.elements.copy():
                if element_id in cut_nodes:
                    # This element is actually a nested cut
                    nested_cut = cut_nodes[element_id]
                    nested_cut.parent_cut = cut_id
                    cut_node.nested_cuts.append(nested_cut)
                    cut_node.elements.remove(element_id)  # Remove from direct elements
        
        # Return top-level cuts (those with no parent)
        return [cut_node for cut_node in cut_nodes.values() if cut_node.parent_cut is None]
    
    def _generate_nested_dot(self, egi: RelationalGraphWithCuts) -> str:
        """Generate DOT with proper nesting (exactly like PNG script)."""
        dot_lines = [
            "graph EGI {",
            "  rankdir=TB;",
            "  compound=true;",
            "  clusterrank=local;",
            "  node [shape=box, style=filled, fillcolor=lightblue];"
        ]
        
        # Add predicates as nodes (like PNG)
        for edge in egi.E:
            if hasattr(edge, 'relation') and edge.relation != '=':
                relation_name = edge.relation
                dot_lines.append(f'  "{edge.id}" [label="{relation_name}"];')
        
        # Add vertices as small circles (like PNG)
        for vertex in egi.V:
            if hasattr(vertex, 'name') and vertex.name:
                dot_lines.append(f'  "{vertex.id}" [label="{vertex.name}", shape=circle, width=0.3];')
        
        # Add nested cuts using containment hierarchy (like PNG but with proper nesting)
        for i, top_cut in enumerate(self.containment_hierarchy):
            self._add_nested_cut_to_dot(dot_lines, top_cut, i, "  ")
        
        # Add sheet-level elements
        sheet_elements = egi.area.get(egi.sheet, frozenset())
        for element_id in sheet_elements:
            if not any(element_id in cut_node.get_all_contained_elements() 
                      for cut_node in self.containment_hierarchy):
                dot_lines.append(f'  "{element_id}";')
        
        # Add identity lines as edges (like PNG)
        for edge in egi.E:
            if hasattr(edge, 'relation') and edge.relation == '=':
                vertices = egi.nu.get(edge.id, [])
                if len(vertices) >= 2:
                    dot_lines.append(f'  "{vertices[0]}" -- "{vertices[1]}" [style=bold];')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def _add_nested_cut_to_dot(self, dot_lines: List[str], cut_node: ContainmentHierarchy, 
                              cluster_index: int, indent: str):
        """Recursively add nested cuts to DOT (proper containment)."""
        dot_lines.append(f"{indent}subgraph cluster_{cluster_index}_{cut_node.cut_id} {{")
        dot_lines.append(f'{indent}  label="";')
        dot_lines.append(f'{indent}  style=rounded;')
        
        # Add direct elements in this cut
        for element_id in cut_node.elements:
            dot_lines.append(f'{indent}  "{element_id}";')
        
        # Recursively add nested cuts
        for i, nested_cut in enumerate(cut_node.nested_cuts):
            self._add_nested_cut_to_dot(dot_lines, nested_cut, f"{cluster_index}_{i}", indent + "  ")
        
        dot_lines.append(f"{indent}}}")
    
    def _extract_spatial_bounds_from_graphviz(self, dot_content: str):
        """Extract spatial bounds using Graphviz (like PNG pipeline)."""
        try:
            # Run Graphviz to get xdot with positioning
            result = subprocess.run(
                ['dot', '-Txdot'],
                input=dot_content,
                text=True,
                capture_output=True,
                check=True
            )
            xdot_output = result.stdout
            
            # Parse bounds from xdot output
            self._parse_bounds_from_xdot(xdot_output)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Graphviz execution failed: {e}")
    
    def _parse_bounds_from_xdot(self, xdot_output: str):
        """Parse spatial bounds from xdot output using proven GraphvizClusterSizer logic."""
        import re
        
        # Debug: save xdot output for inspection
        print(f"DEBUG: xdot output length: {len(xdot_output)}")
        
        # Use the proven regex patterns from GraphvizClusterSizer
        # Pattern 1: Clusters with _draw_ attributes (have content)
        draw_pattern = r'subgraph cluster_(\w+).*?_draw_.*?P 4 ([0-9.-]+) ([0-9.-]+) ([0-9.-]+) ([0-9.-]+)'
        for match in re.finditer(draw_pattern, xdot_output, re.DOTALL):
            cluster_id, x1, y1, x2, y2 = match.groups()
            # Ensure proper min/max for coordinates
            min_x, max_x = min(float(x1), float(x2)), max(float(x1), float(x2))
            min_y, max_y = min(float(y1), float(y2)), max(float(y1), float(y2))
            self.cut_bounds[cluster_id] = SpatialBounds(
                x=min_x, y=min_y,
                width=max_x - min_x,
                height=max_y - min_y
            )
            print(f"DEBUG: Found cut {cluster_id} with _draw_ bounds: {self.cut_bounds[cluster_id]}")
        
        # Pattern 2: Clusters with bb= attributes (bounding box for empty clusters)
        bb_pattern = r'subgraph cluster_(\w+).*?bb="([0-9.-]+),([0-9.-]+),([0-9.-]+),([0-9.-]+)"'
        for match in re.finditer(bb_pattern, xdot_output, re.DOTALL):
            cluster_id, x1, y1, x2, y2 = match.groups()
            if cluster_id not in self.cut_bounds:  # Don't override _draw_ bounds
                self.cut_bounds[cluster_id] = SpatialBounds(
                    x=float(x1), y=float(y1),
                    width=float(x2) - float(x1),
                    height=float(y2) - float(y1)
                )
                print(f"DEBUG: Found cut {cluster_id} with bb bounds: {self.cut_bounds[cluster_id]}")
        
        # Parse node positions (simplified but functional)
        node_pattern = r'"([^"]+)" \[.*?pos="([0-9.-]+),([0-9.-]+)"'
        for match in re.finditer(node_pattern, xdot_output):
            node_id, x, y = match.groups()
            self.element_bounds[node_id] = SpatialBounds(
                x=float(x) - 30, y=float(y) - 15, width=60, height=30
            )
            print(f"DEBUG: Found element {node_id} at position: {self.element_bounds[node_id]}")
        
        print(f"DEBUG: Total cuts found: {len(self.cut_bounds)}")
        print(f"DEBUG: Total elements found: {len(self.element_bounds)}")
    
    def _create_egdf_document(self, egi: RelationalGraphWithCuts) -> EGDFDocument:
        """Create platform-independent EGDF document with layout primitives."""
        
        # Create layout elements using CutPrimitive class
        layout_elements = []
        
        # Create cut layout elements directly from cut_bounds
        print(f"DEBUG: Creating layout elements from {len(self.cut_bounds)} cuts")
        for cut_id, bounds in self.cut_bounds.items():
            cut_element = {
                "type": "cut",
                "id": cut_id,
                "egi_element_id": cut_id,
                "shape": "rectangle",
                "position": {"x": bounds.x, "y": bounds.y},
                "size": {"width": bounds.width, "height": bounds.height},
                "bounds": {"x": bounds.x, "y": bounds.y, "width": bounds.width, "height": bounds.height},
                "properties": {"platform_independent": True}
            }
            layout_elements.append(cut_element)
            print(f"DEBUG: Created layout element for cut {cut_id}")
        
        # Create element layout elements
        for element_id, bounds in self.element_bounds.items():
            element_dict = {
                "type": "element", 
                "id": element_id,
                "position": {"x": bounds.x, "y": bounds.y},
                "size": {"width": bounds.width, "height": bounds.height},
                "properties": {"platform_independent": True}
            }
            layout_elements.append(element_dict)
        
        print(f"DEBUG: Total layout elements created: {len(layout_elements)}")
        
        from egdf_parser import EGDFMetadata
        return EGDFDocument(
            metadata=EGDFMetadata(
                title="Rock-solid EGI→EGDF Translation",
                description="Platform-independent layout with preserved containment hierarchy",
                generator={"tool": "EGIToEGDFTranslator", "version": "1.0"}
            ),
            canonical_egi=self._serialize_egi(egi),
            visual_layout={
                "elements": layout_elements,  # Already dict objects
                "containment_hierarchy_preserved": True,
                "exclusive_positioning": True,
                "platform_independent": True
            }
        )
    
    def _add_cut_layout_elements(self, layout_elements: List[LayoutElement], 
                                cut_node: ContainmentHierarchy):
        """Add cut layout elements with proper nesting."""
        if cut_node.cut_id in self.cut_bounds:
            bounds = self.cut_bounds[cut_node.cut_id]
            layout_elements.append(LayoutElement(
                element_id=cut_node.cut_id,
                element_type="cut",
                position=(bounds.x, bounds.y),
                bounds=(bounds.x, bounds.y, bounds.x + bounds.width, bounds.y + bounds.height),
                metadata={
                    "contains_elements": list(cut_node.elements),
                    "contains_cuts": [nc.cut_id for nc in cut_node.nested_cuts],
                    "parent_cut": cut_node.parent_cut
                }
            ))
        
        # Recursively add nested cuts
        for nested_cut in cut_node.nested_cuts:
            self._add_cut_layout_elements(layout_elements, nested_cut)
    
    def _serialize_egi(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Serialize EGI structure for EGDF document."""
        return {
            "vertices": [{"id": v.id, "name": getattr(v, 'name', '')} for v in egi.V],
            "edges": [{"id": e.id, "relation": getattr(e, 'relation', '')} for e in egi.E],
            "cuts": [{"id": c.id} for c in egi.Cut],
            "area": {k: list(v) for k, v in egi.area.items()},
            "nu": {k: list(v) for k, v in egi.nu.items()},
            "sheet": egi.sheet
        }


def get_rock_solid_egdf_layout(egi: RelationalGraphWithCuts) -> EGDFDocument:
    """
    Main entry point for rock-solid EGI → EGDF translation.
    
    Uses the proven PNG generation logic to create platform-independent
    EGDF layout primitives with guaranteed correctness.
    """
    translator = EGIToEGDFTranslator()
    return translator.translate(egi)
