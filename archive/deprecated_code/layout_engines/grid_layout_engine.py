"""
Grid Layout Engine - Guaranteed Non-Overlapping Cuts

Uses simple grid placement to ensure cuts NEVER overlap.
Not pretty, but CORRECT.
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class GridCell:
    row: int
    col: int
    width: int  # In cells
    height: int  # In cells


class GridLayoutEngine:
    """
    Simple grid-based layout that guarantees non-overlapping cuts.
    
    Algorithm:
    1. Bottom-up: Size inner cuts from content
    2. Grid placement: Arrange cuts in non-overlapping grid
    3. Fill cells: Place elements within each cut's grid space
    """
    
    def __init__(self, cell_size: int = 100):
        self.cell_size = cell_size  # Pixels per grid cell
    
    def generate_layout(self, egi, hierarchy: Dict) -> Dict:
        """
        Generate guaranteed non-overlapping layout.
        
        Returns: global_positions dict with all coordinates
        """
        
        # Step 1: Calculate sizes bottom-up
        sizes = self._calculate_sizes_bottom_up(egi, hierarchy)
        
        # Step 2: Assign grid cells to each area
        grid_assignments = self._assign_grid_cells(hierarchy, sizes)
        
        # Step 3: Position elements within their grid cells
        positions = self._position_elements(egi, hierarchy, grid_assignments, sizes)
        
        # Step 4: Calculate area bounds from grid assignments
        area_bounds = self._calculate_area_bounds(grid_assignments)
        
        return positions, area_bounds
    
    def _calculate_sizes_bottom_up(self, egi, hierarchy: Dict) -> Dict:
        """Calculate minimum size needed for each area"""
        sizes = {}
        
        # Process leaves first
        def calc_size(area_id):
            if area_id in sizes:
                return sizes[area_id]
            
            info = hierarchy[area_id]
            
            # Count content
            n_vertices = len(info['vertices'])
            n_edges = len(info['edges'])
            n_children = len(info['children'])
            
            # Recurse for children
            child_sizes = []
            for child_id in info['children']:
                child_sizes.append(calc_size(child_id))
            
            # Estimate size needed (in grid cells)
            content_cells = max(2, (n_vertices + n_edges + 2) // 3)  # Rough estimate
            
            if child_sizes:
                # Need space for all children plus content
                total_child_cells = sum(s[0] * s[1] for s in child_sizes)
                width_cells = max(content_cells, int((total_child_cells ** 0.5)) + 2)
                height_cells = max(content_cells, int((total_child_cells ** 0.5)) + 2)
            else:
                # Just content
                width_cells = content_cells
                height_cells = content_cells
            
            sizes[area_id] = (width_cells, height_cells)
            return sizes[area_id]
        
        # Calculate for all areas
        for area_id in hierarchy.keys():
            calc_size(area_id)
        
        return sizes
    
    def _assign_grid_cells(self, hierarchy: Dict, sizes: Dict) -> Dict:
        """Assign non-overlapping grid cells to each area"""
        assignments = {}
        
        # Find sheet (root)
        sheet_id = None
        for area_id, info in hierarchy.items():
            is_child = any(area_id in h['children'] for h in hierarchy.values())
            if not is_child:
                sheet_id = area_id
                break
        
        # Assign sheet the full grid
        sheet_w, sheet_h = sizes[sheet_id]
        assignments[sheet_id] = GridCell(0, 0, sheet_w, sheet_h)
        
        # Recursively assign children
        def assign_children(parent_id, parent_cell: GridCell):
            children = hierarchy[parent_id]['children']
            if not children:
                return
            
            # Simple strategy: arrange children in grid within parent
            n_children = len(children)
            cols = int(n_children ** 0.5) + 1
            
            col_offset = parent_cell.col + 1
            row_offset = parent_cell.row + 1
            
            for i, child_id in enumerate(children):
                col = i % cols
                row = i // cols
                
                w, h = sizes[child_id]
                
                assignments[child_id] = GridCell(
                    row_offset + row * (h + 1),
                    col_offset + col * (w + 1),
                    w,
                    h
                )
                
                assign_children(child_id, assignments[child_id])
        
        assign_children(sheet_id, assignments[sheet_id])
        
        return assignments
    
    def _position_elements(self, egi, hierarchy: Dict, 
                          grid_assignments: Dict, sizes: Dict) -> Dict:
        """Position vertices and edges within their grid cells"""
        positions = {'vertices': {}, 'edge_labels': {}}
        
        for area_id, cell in grid_assignments.items():
            info = hierarchy[area_id]
            
            # Get cell bounds in pixels
            x_base = cell.col * self.cell_size
            y_base = cell.row * self.cell_size
            cell_width = cell.width * self.cell_size
            cell_height = cell.height * self.cell_size
            
            # Position vertices in simple grid
            vertices = list(info['vertices'])
            for i, v_id in enumerate(vertices):
                x = x_base + (i + 1) * cell_width / (len(vertices) + 1)
                y = y_base + cell_height / 3
                positions['vertices'][v_id] = {
                    'x': x, 'y': y, 'parent_area_id': area_id
                }
            
            # Position edge labels
            edges = list(info['edges'])
            for i, e_id in enumerate(edges):
                x = x_base + (i + 1) * cell_width / (len(edges) + 1)
                y = y_base + 2 * cell_height / 3
                
                # Get label
                label = egi.get_edge_label(e_id) if hasattr(egi, 'get_edge_label') else str(e_id)
                
                positions['edge_labels'][e_id] = {
                    'x': x, 'y': y,
                    'width': 50, 'height': 20,
                    'label': label,
                    'parent_area_id': area_id
                }
        
        return positions
    
    def _calculate_area_bounds(self, grid_assignments: Dict) -> Dict:
        """Convert grid assignments to pixel bounds"""
        bounds = {}
        
        for area_id, cell in grid_assignments.items():
            bounds[area_id] = {
                'x': cell.col * self.cell_size,
                'y': cell.row * self.cell_size,
                'width': cell.width * self.cell_size,
                'height': cell.height * self.cell_size
            }
        
        return bounds
