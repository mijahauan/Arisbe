"""
Constrained Force-Directed Layout Engine

Implements two-level optimization:
1. CONTAINMENT (hard constraint): Elements must stay within area boundaries
2. RELATIONAL (soft optimization): Minimize ligature lengths via spring forces

This replaces Graphviz with a custom algorithm that respects EGI formal logic.
"""

import math
import random
from typing import Dict, List, Tuple, Set

from egi_core_dau import RelationalGraphWithCuts


class Vec2:
    """2D vector for force calculations"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        return Vec2(self.x / scalar, self.y / scalar)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalized(self):
        length = self.length()
        if length < 0.0001:
            return Vec2(0, 0)
        return self / length
    
    def to_tuple(self):
        return (self.x, self.y)


class Rect:
    """Rectangle for area boundaries - compatible with engine's Rect"""
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def contains_point(self, pos: Vec2) -> bool:
        return (self.x <= pos.x <= self.x + self.width and
                self.y <= pos.y <= self.y + self.height)
    
    def clip_point(self, pos: Vec2, padding: float = 5.0) -> Vec2:
        """Clip a point to be within this rectangle (with padding from edges)"""
        return Vec2(
            max(self.x + padding, min(pos.x, self.x + self.width - padding)),
            max(self.y + padding, min(pos.y, self.y + self.height - padding))
        )
    
    def center(self) -> Vec2:
        return Vec2(self.x + self.width / 2, self.y + self.height / 2)
    
    def union(self, other: 'Rect') -> 'Rect':
        """Return the union (bounding box) of two rectangles"""
        min_x = min(self.x, other.x)
        min_y = min(self.y, other.y)
        max_x = max(self.x + self.width, other.x + other.width)
        max_y = max(self.y + self.height, other.y + other.height)
        return Rect(min_x, min_y, max_x - min_x, max_y - min_y)


class ConstrainedForceLayout:
    """
    Force-directed layout with hard containment constraints.
    
    Elements connected by ligatures attract each other (spring force).
    All elements repel each other (avoid overlap).
    Elements are clipped to their area boundaries (hard constraint).
    """
    
    def __init__(self, egi: RelationalGraphWithCuts, hierarchy: Dict):
        self.egi = egi
        self.hierarchy = hierarchy
        
        # Physics parameters
        self.spring_strength = 0.1      # Ligature attraction
        self.spring_rest_length = 30.0  # Ideal ligature length
        self.repulsion_strength = 500.0 # Element repulsion
        self.damping = 0.8              # Velocity damping
        
        # Layout state
        self.positions: Dict[str, Vec2] = {}
        self.velocities: Dict[str, Vec2] = {}
        self.area_bounds: Dict[str, Rect] = {}
    
    def generate_layout(self, iterations: int = 200) -> Tuple[Dict, Dict]:
        """
        Generate complete layout with containment constraints.
        
        Returns: (global_positions, area_bounds)
        """
        # Phase 1: Calculate area sizes and positions
        self._calculate_area_bounds()
        
        # Phase 2: Initialize element positions randomly within areas
        self._initialize_positions()
        
        # Phase 3: Run force-directed simulation with containment constraints
        self._run_simulation(iterations)
        
        # Phase 4: Convert to output format
        return self._build_output()
    
    def _calculate_area_bounds(self):
        """
        Phase 1: Calculate area sizes based on content.
        Uses simple box packing - no Graphviz needed.
        """
        # Calculate sizes bottom-up (leaves to root)
        area_sizes = {}
        
        def calculate_size(area_id):
            """Calculate size recursively from leaves up"""
            if area_id in area_sizes:
                return area_sizes[area_id]
            
            info = self.hierarchy[area_id]
            n_vertices = len(info['vertices'])
            n_edges = len(info['edges'])
            n_children = len(info['children'])
            
            # Base size for direct content
            content_count = n_vertices + n_edges
            base_width = max(100, content_count * 40)
            base_height = max(80, content_count * 30)
            
            # Calculate children sizes recursively
            if n_children > 0:
                child_heights = []
                max_child_width = 0
                
                for child_id in info['children']:
                    child_w, child_h = calculate_size(child_id)
                    child_heights.append(child_h)
                    max_child_width = max(max_child_width, child_w)
                
                # Size to fit children stacked vertically with padding
                total_child_height = sum(child_heights) + (n_children - 1) * 10 + 30  # padding
                width = max(base_width, max_child_width + 30)  # padding on sides
                height = max(base_height, total_child_height)
            else:
                width = base_width
                height = base_height
            
            area_sizes[area_id] = (width, height)
            return (width, height)
        
        # Calculate all sizes starting from sheet
        calculate_size(self.egi.sheet)
        
        # Position areas in simple hierarchy (bottom-up)
        self.area_bounds = {}
        positioned_children: Set[str] = set()
        
        def position_area(area_id, parent_rect: Rect = None):
            """Position an area and its children recursively"""
            width, height = area_sizes[area_id]
            
            if area_id == self.egi.sheet:
                # Sheet at origin, sized to contain all content
                total_width = width
                total_height = height
                
                # Position child cuts in a simple layout
                child_y = 20
                for child_id in self.hierarchy[area_id]['children']:
                    child_width, child_height = area_sizes[child_id]
                    child_rect = Rect(20, child_y, child_width, child_height)
                    self.area_bounds[child_id] = child_rect
                    
                    # Recursively position nested children
                    position_area(child_id, child_rect)
                    
                    child_y += child_height + 20
                    total_height = max(total_height, child_y)
                
                # Sheet encompasses everything
                self.area_bounds[area_id] = Rect(0, 0, total_width + 40, total_height + 20)
                
            else:
                # Non-sheet area - position its children within it
                # (parent_rect is the bounds of this area, already set by parent)
                if parent_rect and self.hierarchy[area_id]['children']:
                    child_x = parent_rect.x + 15
                    child_y = parent_rect.y + 15
                    
                    for child_id in self.hierarchy[area_id]['children']:
                        child_width, child_height = area_sizes[child_id]
                        child_rect = Rect(child_x, child_y, child_width, child_height)
                        self.area_bounds[child_id] = child_rect
                        
                        # Recursively position its children
                        position_area(child_id, child_rect)
                        
                        child_y += child_height + 10
        
        # Start from sheet
        position_area(self.egi.sheet)
    
    def _get_exclusive_area(self, area_id: str) -> Rect:
        """
        Get the EXCLUSIVE area for an element - parent bounds MINUS child cut bounds.
        Elements must stay in their area but OUT of nested cuts.
        """
        area_rect = self.area_bounds[area_id]
        
        # For elements in this area, they can be anywhere EXCEPT inside child cuts
        # For now, use a simple heuristic: keep elements in top margin above child cuts
        # or in side margins beside child cuts
        
        # Get child cuts
        children = self.hierarchy[area_id]['children']
        
        if not children:
            # No children - full area available
            return area_rect
        
        # If has children, reserve space OUTSIDE child cuts
        # Simple approach: use top strip and side margins
        # Return the original bounds but note we'll do exclusion during clipping
        return area_rect
    
    def _is_point_in_child_cut(self, pos: Vec2, area_id: str) -> bool:
        """Check if a point is inside any child cut of this area"""
        for child_id in self.hierarchy[area_id]['children']:
            if child_id in self.area_bounds:
                child_rect = self.area_bounds[child_id]
                if child_rect.contains_point(pos):
                    return True
        return False
    
    def _initialize_positions(self):
        """
        Phase 2: Initialize element positions randomly within their areas,
        but OUTSIDE any nested cuts (exclusive containment).
        """
        for area_id, bounds in self.area_bounds.items():
            # Place vertices
            for v_id in self.hierarchy[area_id]['vertices']:
                # Find position that's in area but NOT in any child cut
                max_attempts = 50
                for attempt in range(max_attempts):
                    pos = Vec2(
                        bounds.x + random.uniform(10, bounds.width - 10),
                        bounds.y + random.uniform(10, bounds.height - 10)
                    )
                    
                    # Check if inside any child cut
                    if not self._is_point_in_child_cut(pos, area_id):
                        self.positions[v_id] = pos
                        break
                else:
                    # Fallback: place in top-left corner outside cuts
                    self.positions[v_id] = Vec2(bounds.x + 10, bounds.y + 10)
                
                self.velocities[v_id] = Vec2(0, 0)
            
            # Place edge labels
            for e_id in self.hierarchy[area_id]['edges']:
                max_attempts = 50
                for attempt in range(max_attempts):
                    pos = Vec2(
                        bounds.x + random.uniform(10, bounds.width - 10),
                        bounds.y + random.uniform(10, bounds.height - 10)
                    )
                    
                    if not self._is_point_in_child_cut(pos, area_id):
                        self.positions[e_id] = pos
                        break
                else:
                    self.positions[e_id] = Vec2(bounds.x + 15, bounds.y + 15)
                
                self.velocities[e_id] = Vec2(0, 0)
    
    def _run_simulation(self, iterations: int):
        """
        Phase 3: Run force-directed simulation with hard containment constraints.
        """
        all_elements = list(self.positions.keys())
        
        for iteration in range(iterations):
            # Calculate forces for each element
            forces = {elem_id: Vec2(0, 0) for elem_id in all_elements}
            
            # 1. Spring forces (ligature attraction)
            for edge_id, vertex_sequence in self.egi.nu.items():
                if edge_id not in self.positions:
                    continue
                
                edge_pos = self.positions[edge_id]
                
                for vertex_id in vertex_sequence:
                    if vertex_id not in self.positions:
                        continue
                    
                    vertex_pos = self.positions[vertex_id]
                    
                    # Spring force: F = k * (distance - rest_length) * direction
                    delta = edge_pos - vertex_pos
                    distance = delta.length()
                    
                    if distance > 0.1:
                        direction = delta.normalized()
                        spring_force = direction * (distance - self.spring_rest_length) * self.spring_strength
                        
                        # Apply equal and opposite forces
                        forces[vertex_id] = forces[vertex_id] + spring_force
                        forces[edge_id] = forces[edge_id] - spring_force
            
            # 2. Repulsion forces (avoid overlap)
            for i, elem1_id in enumerate(all_elements):
                for elem2_id in all_elements[i+1:]:
                    pos1 = self.positions[elem1_id]
                    pos2 = self.positions[elem2_id]
                    
                    delta = pos1 - pos2
                    distance = delta.length()
                    
                    if distance < 0.1:
                        # Avoid division by zero
                        delta = Vec2(random.uniform(-1, 1), random.uniform(-1, 1))
                        distance = 1.0
                    
                    # Repulsion force: F = k / distance^2
                    repulsion = delta.normalized() * (self.repulsion_strength / (distance ** 2))
                    
                    forces[elem1_id] = forces[elem1_id] + repulsion
                    forces[elem2_id] = forces[elem2_id] - repulsion
            
            # 3. Update positions with EXCLUSIVE containment constraints
            for elem_id in all_elements:
                # Update velocity (with damping)
                self.velocities[elem_id] = (self.velocities[elem_id] + forces[elem_id]) * self.damping
                
                # Update position
                new_pos = self.positions[elem_id] + self.velocities[elem_id]
                
                # HARD CONSTRAINT: Clip to area boundary AND push out of child cuts
                area_id = self._get_element_area(elem_id)
                if area_id in self.area_bounds:
                    bounds = self.area_bounds[area_id]
                    new_pos = bounds.clip_point(new_pos)
                    
                    # EXCLUSIVE: If inside a child cut, push out
                    for child_id in self.hierarchy[area_id]['children']:
                        if child_id in self.area_bounds:
                            child_rect = self.area_bounds[child_id]
                            if child_rect.contains_point(new_pos):
                                # Push to nearest edge of child cut
                                new_pos = self._push_out_of_rect(new_pos, child_rect, bounds)
                
                self.positions[elem_id] = new_pos
            
            # Cool down (reduce step size over time)
            if iteration % 50 == 0:
                self.spring_strength *= 0.95
                self.repulsion_strength *= 0.95
    
    def _push_out_of_rect(self, pos: Vec2, rect: Rect, parent_bounds: Rect) -> Vec2:
        """
        Push a point to the nearest edge of a rectangle (out of it).
        Ensures result stays within parent_bounds.
        """
        # Find distances to each edge
        dist_left = pos.x - rect.x
        dist_right = (rect.x + rect.width) - pos.x
        dist_top = pos.y - rect.y
        dist_bottom = (rect.y + rect.height) - pos.y
        
        # Find minimum distance
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        
        # Push to nearest edge
        if min_dist == dist_left and rect.x > parent_bounds.x:
            # Push left
            return Vec2(max(parent_bounds.x + 5, rect.x - 5), pos.y)
        elif min_dist == dist_right and rect.x + rect.width < parent_bounds.x + parent_bounds.width:
            # Push right
            return Vec2(min(parent_bounds.x + parent_bounds.width - 5, rect.x + rect.width + 5), pos.y)
        elif min_dist == dist_top and rect.y > parent_bounds.y:
            # Push up
            return Vec2(pos.x, max(parent_bounds.y + 5, rect.y - 5))
        else:
            # Push down
            return Vec2(pos.x, min(parent_bounds.y + parent_bounds.height - 5, rect.y + rect.height + 5))
    
    def _get_element_area(self, elem_id: str) -> str:
        """Find which area an element belongs to"""
        for area_id, info in self.hierarchy.items():
            if elem_id in info['vertices'] or elem_id in info['edges']:
                return area_id
        return self.egi.sheet
    
    def _build_output(self) -> Tuple[Dict, Dict]:
        """
        Phase 4: Convert to output format expected by layout engine.
        """
        global_positions = {'vertices': {}, 'edge_labels': {}}
        
        for elem_id, pos in self.positions.items():
            area_id = self._get_element_area(elem_id)
            
            # Check if it's a vertex or edge
            if elem_id in self.egi.nu:
                # It's an edge
                rel_name = self.egi.rel.get(elem_id, "?")
                global_positions['edge_labels'][elem_id] = {
                    'x': pos.x,
                    'y': pos.y,
                    'width': len(rel_name) * 8,
                    'height': 12,
                    'label': rel_name,
                    'parent_area_id': area_id
                }
            else:
                # It's a vertex
                global_positions['vertices'][elem_id] = {
                    'x': pos.x,
                    'y': pos.y,
                    'parent_area_id': area_id
                }
        
        return global_positions, self.area_bounds
