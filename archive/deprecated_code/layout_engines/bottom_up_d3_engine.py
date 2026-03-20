"""
Bottom-Up D3-Only Layout Engine

TRUE BOTTOM-UP ARCHITECTURE:
- No Graphviz Pass 1 (no more size guessing!)
- Single recursive pass using d3-force
- Content determines container size (not the other way around)

Process:
1. Leaf cut: Run d3 in GENEROUS virtual box → Calculate TIGHT bounding box
2. Parent cut: Use child tight boxes as obstacles → Run d3 → Calculate tight box
3. Recursive bottom-up: Children sized before parents

The d3 worker's custom containment force teaches it about walls,
but the FINAL container size comes from the ACTUAL content positions.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from egi_core_dau import RelationalGraphWithCuts
from constrained_force_layout import Rect

# Import DTOs from definitive_three_pass_engine
from definitive_three_pass_engine import (
    LayoutDTO, RenderableArea, RenderableVertex, RenderableEdgeLabel,
    RenderableLigature, ConnectionPort
)

# Import ligature routing
from area_aware_astar import AreaAwareAStarPathfinder


@dataclass
class TightBounds:
    """Tight bounding box calculated from actual content positions."""
    x: float
    y: float
    width: float
    height: float
    

class BottomUpD3Engine:
    """
    Pure bottom-up layout engine using ONLY d3-force.
    
    No Graphviz. No size guessing. Content determines container size.
    """
    
    def __init__(self):
        self.element_positions: Dict[str, Tuple[float, float]] = {}
        self.area_bounds: Dict[str, Rect] = {}
        self.element_sizes: Dict[str, Tuple[float, float]] = {}
        
    def generate_layout(self, egi: RelationalGraphWithCuts, style, deltas=None) -> LayoutDTO:
        """
        Generate layout using pure bottom-up d3-force.
        
        Args:
            egi: The EGI model to layout
            style: Style specification
            deltas: Optional user position overrides (TODO: implement support)
        """
        
        print("=" * 70)
        print("BOTTOM-UP D3-ONLY LAYOUT ENGINE")
        print("=" * 70)
        print()
        
        # CRITICAL: Clear state from previous runs
        self.element_positions.clear()
        self.area_bounds.clear()
        self.element_sizes.clear()
        
        # TODO: Apply user deltas (pinned positions, custom ligature paths)
        if deltas:
            print(f"  Note: User deltas not yet implemented ({len(deltas.deltas)} deltas ignored)")
        
        # Store element sizes from style
        self._calculate_element_sizes(egi, style)
        
        # Single recursive pass - bottom-up
        print("Bottom-up recursive layout (d3-force)...")
        self._layout_recursive(egi, egi.sheet)
        print(f"  ✅ {len(self.element_positions)} elements positioned")
        print(f"  ✅ {len(self.area_bounds)} containers sized")
        print()
        
        # Build DTO with ligatures
        dto = self._build_dto(egi, style)
        print(f"✅ Complete: {len(dto.vertices)}V, {len(dto.edge_labels)}E, {len(dto.ligatures)}L")
        return dto
    
    def _calculate_element_sizes(self, egi: RelationalGraphWithCuts, style):
        """Calculate element dimensions from style."""
        # Handle both dict and StyleSpecification
        if hasattr(style, 'vertex_radius'):
            vertex_radius = style.vertex_radius
        else:
            vertex_radius = style.get('vertex_radius', 12)
        
        # egi.V and egi.E are frozensets of Vertex/Edge objects
        for v in egi.V:
            self.element_sizes[v.id] = (vertex_radius * 2, vertex_radius * 2)
        
        for e in egi.E:
            # Get label from egi.rel (relation names mapping) using API method
            label = egi.get_relation_name(e.id)
            # Estimate edge label width from text
            label_width = len(label) * 8 + 20 if label else 40
            label_height = 25
            self.element_sizes[e.id] = (label_width, label_height)
    
    def _layout_recursive(self, egi: RelationalGraphWithCuts, cut_id: str) -> TightBounds:
        """
        Recursive bottom-up layout.
        
        Returns the TIGHT bounding box for this cut.
        """
        
        # Get child cuts
        child_cut_ids = [elem for elem in egi.area.get(cut_id, []) if elem.startswith('c_')]
        
        # RECURSION: Layout children first (bottom-up!)
        child_bounds: Dict[str, TightBounds] = {}
        for child_id in child_cut_ids:
            child_bounds[child_id] = self._layout_recursive(egi, child_id)
        
        # Get content elements (vertices and edges) in this cut
        content_ids = [elem for elem in egi.area.get(cut_id, []) 
                      if elem.startswith(('v_', 'e_'))]
        
        if not content_ids and not child_cut_ids:
            # Empty cut - minimal box
            tight = TightBounds(0, 0, 100, 80)
            self.area_bounds[cut_id] = Rect(tight.x, tight.y, tight.width, tight.height)
            return tight
        
        # ADAPTIVE virtual box based on content
        # CRITICAL: Must fit all sibling cuts arranged in a row
        import math
        total_elements = len(content_ids)
        
        # Calculate space needed for siblings arranged in a row
        if child_bounds:
            # Siblings in a row with spacing
            total_child_width = sum(b.width for b in child_bounds.values())
            spacing = 30 * (len(child_bounds) + 1)  # Start margin + gaps
            virtual_width = total_child_width + spacing + 100  # Extra space for content
            
            # Height based on tallest child
            max_child_height = max(b.height for b in child_bounds.values())
            virtual_height = max(max_child_height + 100, 200)
        else:
            # No children - size based on content count
            if total_elements <= 2:
                virtual_width = 200
                virtual_height = 150
            elif total_elements <= 5:
                virtual_width = 300
                virtual_height = 250  
            else:
                rows = math.ceil(math.sqrt(total_elements))
                virtual_width = min(600, rows * 80)
                virtual_height = min(500, rows * 70)
        
        # Run d3-force layout for this cut's content
        final_bounds = self._layout_cut(
            egi, cut_id, content_ids, child_bounds,
            virtual_width, virtual_height
        )
        
        # Store for DTO generation
        self.area_bounds[cut_id] = Rect(
            final_bounds.x, final_bounds.y,
            final_bounds.width, final_bounds.height
        )
        
        return final_bounds
    
    def _layout_cut(
        self,
        egi: RelationalGraphWithCuts,
        cut_id: str,
        content_ids: List[str],
        child_bounds: Dict[str, TightBounds],
        virtual_width: float,
        virtual_height: float
    ) -> TightBounds:
        """
        Layout one cut's content using d3-force.
        
        Process:
        1. Provide GENEROUS virtual box as bounds
        2. Run d3-force (containment force teaches it about walls)
        3. Calculate TIGHT bounding box from actual positions
        4. Return tight box (parent will use it as obstacle)
        """
        
        print(f"    Laying out {cut_id}:")
        print(f"      Content: {len(content_ids)} elements")
        print(f"      Children: {len(child_bounds)} cuts")
        print(f"      Virtual box: {virtual_width}x{virtual_height}")
        
        # Build d3 payload
        payload = {
            'bounds': {
                'x': 0,
                'y': 0,
                'width': virtual_width,
                'height': virtual_height
            },
            'nodes': [],
            'links': [],
            'obstacles': [],
            'portNodes': [],
            'seed': 42  # Deterministic layouts
        }
        
        # Add content nodes (sorted for determinism)
        for elem_id in sorted(content_ids):
            width, height = self.element_sizes.get(elem_id, (30, 30))
            elem_type = 'vertex' if elem_id.startswith('v_') else 'edge_label'
            
            payload['nodes'].append({
                'id': elem_id,
                'type': elem_type,
                'width': width,
                'height': height
            })
        
        # Add child cuts as obstacles at SEPARATE positions
        # Siblings must be differentiated spatially!
        child_obstacle_positions = {}
        if child_bounds:
            # Arrange siblings in a row with spacing
            x_offset = 30  # Start position
            y_center = virtual_height / 2
            
            for child_id, bounds in sorted(child_bounds.items()):
                # Position this child
                child_x = x_offset + bounds.width / 2
                child_y = y_center
                
                child_obstacle_positions[child_id] = (child_x, child_y)
                
                payload['obstacles'].append({
                    'id': child_id,
                    'x': child_x,
                    'y': child_y,
                    'width': bounds.width,
                    'height': bounds.height
                })
                
                # Move to next position
                x_offset += bounds.width + 30  # 30px spacing between siblings
        
        # Add links (from ν connections)
        for e in egi.E:  # egi.E is a frozenset
            if e.id not in content_ids:
                continue
            # Use get_incident_vertices API method
            for v_id in egi.get_incident_vertices(e.id):
                if v_id in content_ids:
                    payload['links'].append({'source': e.id, 'target': v_id})
        
        # Call d3 worker
        worker = Path(__file__).parent / 'd3_layout_worker.js'
        result = subprocess.run(
            ['node', str(worker)],
            input=json.dumps(payload),
            capture_output=True, text=True, check=True
        )
        
        positions = json.loads(result.stdout)
        
        # Store positions temporarily
        for elem_id, pos in positions.items():
            self.element_positions[elem_id] = (pos['x'], pos['y'])
        
        # Calculate TIGHT bounding box from actual positions
        # Include child cuts at their obstacle positions
        tight = self._calculate_tight_bounds(content_ids, child_bounds, child_obstacle_positions)
        
        # CRITICAL: Normalize ALL positions to start at tight box origin
        # This ensures each cut's content is in its own (0,0)-based coordinate system
        offset_x = tight.x
        offset_y = tight.y
        
        # Translate content elements
        for elem_id in content_ids:
            if elem_id in self.element_positions:
                x, y = self.element_positions[elem_id]
                self.element_positions[elem_id] = (x - offset_x, y - offset_y)
        
        # Store child cut positions AND translate their contents
        for child_id, child_tight in child_bounds.items():
            if child_id in child_obstacle_positions:
                cx, cy = child_obstacle_positions[child_id]
                
                # Child cut position in parent's normalized space
                child_x = cx - child_tight.width/2 - offset_x
                child_y = cy - child_tight.height/2 - offset_y
                
                self.area_bounds[child_id] = Rect(
                    child_x,
                    child_y,
                    child_tight.width,
                    child_tight.height
                )
                
                # CRITICAL: Translate all elements INSIDE this child cut
                # Child's contents were positioned relative to child's (0,0)
                # Now child is at (child_x, child_y) in parent space
                # So offset all child contents by this amount
                child_elements = egi.area.get(child_id, [])
                for elem_id in child_elements:
                    if elem_id in self.element_positions and elem_id.startswith(('v_', 'e_')):
                        elem_x, elem_y = self.element_positions[elem_id]
                        # Translate element to parent's coordinate system
                        self.element_positions[elem_id] = (elem_x + child_x, elem_y + child_y)
        
        print(f"      D3 positioned {len(positions)} elements")
        print(f"      Tight box: {tight.width:.0f}x{tight.height:.0f} (normalized to 0,0)")
        
        # Return normalized tight bounds (always starting at 0,0)
        return TightBounds(x=0, y=0, width=tight.width, height=tight.height)
    
    def _calculate_tight_bounds(
        self,
        content_ids: List[str],
        child_bounds: Dict[str, TightBounds],
        child_obstacle_positions: Dict[str, Tuple[float, float]] = None
    ) -> TightBounds:
        """
        Calculate tight bounding box that encloses all content.
        
        CRITICAL: Parent must be large enough for its own content AND its children.
        Children are positioned at their obstacle locations in parent's virtual space.
        """
        
        if child_obstacle_positions is None:
            child_obstacle_positions = {}
        
        if not content_ids and not child_bounds:
            # Completely empty area
            return TightBounds(0, 0, 100, 80)
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # Include content elements (vertices and edge labels in this cut)
        for elem_id in content_ids:
            x, y = self.element_positions[elem_id]
            width, height = self.element_sizes.get(elem_id, (30, 30))
            
            min_x = min(min_x, x - width / 2)
            min_y = min(min_y, y - height / 2)
            max_x = max(max_x, x + width / 2)
            max_y = max(max_y, y + height / 2)
        
        # Include child cuts at their ACTUAL positions
        for child_id, child_tight in child_bounds.items():
            if child_id in child_obstacle_positions:
                # Child positioned as obstacle in parent's virtual space
                cx, cy = child_obstacle_positions[child_id]
                min_x = min(min_x, cx - child_tight.width / 2)
                min_y = min(min_y, cy - child_tight.height / 2)
                max_x = max(max_x, cx + child_tight.width / 2)
                max_y = max(max_y, cy + child_tight.height / 2)
            else:
                # Fallback: assume at (0,0)
                min_x = min(min_x, 0)
                min_y = min(min_y, 0)
                max_x = max(max_x, child_tight.width)
                max_y = max(max_y, child_tight.height)
        
        # Add padding
        padding = 20
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        return TightBounds(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )
    
    def _build_dto(self, egi: RelationalGraphWithCuts, style) -> LayoutDTO:
        """Build layout DTO from positions."""
        dto = LayoutDTO()
        
        # Add vertices
        for v in egi.V:  # egi.V is a frozenset
            if v.id in self.element_positions:
                x, y = self.element_positions[v.id]
                parent_id = self._find_parent_area(v.id, egi)
                print(f"    Vertex {v.id}: parent={parent_id}, pos=({x:.1f}, {y:.1f})")
                dto.vertices.append(RenderableVertex(
                    id=v.id,
                    parent_area_id=parent_id,
                    pos=(x, y),
                    label=v.label or ""
                ))
        
        # Add edge labels
        for e in egi.E:  # egi.E is a frozenset
            if e.id in self.element_positions:
                x, y = self.element_positions[e.id]
                width, height = self.element_sizes.get(e.id, (40, 25))
                label = egi.get_relation_name(e.id)  # Use API method
                parent_id = self._find_parent_area(e.id, egi)
                print(f"    EdgeLabel {e.id} ({label}): parent={parent_id}, pos=({x:.1f}, {y:.1f})")
                dto.edge_labels.append(RenderableEdgeLabel(
                    id=e.id,
                    parent_area_id=parent_id,
                    rect=Rect(x - width/2, y - height/2, width, height),
                    label=label,
                    connection_ports=[]
                ))
        
        # Add areas
        print(f"\n  DTO Areas:")
        for cut_id, rect in self.area_bounds.items():
            is_sheet = cut_id == egi.sheet
            parent_id = self._find_parent_area(cut_id, egi)
            print(f"    Area {cut_id}: parent={parent_id}, bounds=({rect.x:.1f},{rect.y:.1f}) {rect.width:.1f}x{rect.height:.1f}, sheet={is_sheet}")
            dto.areas.append(RenderableArea(
                id=cut_id,
                parent_id=parent_id,
                rect=rect,
                is_sheet=is_sheet
            ))
        
        # Add ligatures (simple straight-line routing for now)
        self._add_ligatures(egi, dto, style)
        
        return dto
    
    def _find_parent_area(self, elem_id: str, egi: RelationalGraphWithCuts) -> Optional[str]:
        """Find the parent area (cut) that contains this element."""
        for area_id, elements in egi.area.items():
            if elem_id in elements:
                return area_id
        return None
    
    def _add_ligatures(self, egi: RelationalGraphWithCuts, dto: LayoutDTO, style):
        """Add simple straight-line ligatures connecting vertices to edges."""
        
        # Simple straight-line ligatures for now
        # TODO: Use A* pathfinding for area-aware routing
        
        # egi.nu is a frozendict mapping edge_id -> tuple of vertex_ids
        for edge_id in [e.id for e in egi.E]:
            if edge_id not in self.element_positions:
                continue
            
            # Use get_incident_vertices API method
            vertex_ids = egi.get_incident_vertices(edge_id)
            if not vertex_ids:
                continue
            
            edge_pos = self.element_positions[edge_id]
            
            for hook_idx, v_id in enumerate(vertex_ids):
                if v_id not in self.element_positions:
                    continue
                
                v_pos = self.element_positions[v_id]
                
                # Simple straight line from vertex to edge
                dto.ligatures.append(RenderableLigature(
                    start_vertex_id=v_id,
                    end_edge_id=edge_id,
                    end_hook_index=hook_idx,
                    path_points=[v_pos, edge_pos]
                ))
