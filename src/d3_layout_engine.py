"""
D3.js Layout Engine via Node.js Bridge

Uses D3's force simulation with custom containment and exclusion forces.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Tuple

from egi_core_dau import RelationalGraphWithCuts


class D3LayoutEngine:
    """
    Layout engine using D3.js force simulation via Node.js bridge.
    
    Advantages:
    - Mature, battle-tested force simulation
    - Custom force functions for containment
    - Deterministic with fixed seed
    - Better convergence than our naive implementation
    """
    
    def __init__(self):
        self.node_script = Path(__file__).parent / 'd3_layout_bridge.js'
        
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise RuntimeError("Node.js not found")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Node.js check timed out (may be system issue)")
        except FileNotFoundError:
            raise RuntimeError("Node.js is required but not installed")
    
    def generate_layout(self, egi: RelationalGraphWithCuts, hierarchy: Dict, 
                       area_bounds: Dict, iterations: int = 300) -> Tuple[Dict, Dict]:
        """
        Generate layout using D3.js force simulation.
        
        Args:
            egi: The EGI structure
            hierarchy: Area hierarchy from layout engine
            area_bounds: Initial area bounds (from size calculation)
            iterations: Number of simulation iterations
            
        Returns:
            (global_positions, area_bounds) in same format as ConstrainedForceLayout
        """
        # Prepare input for D3
        input_data = self._prepare_input(egi, hierarchy, area_bounds, iterations)
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f, indent=2)
            input_file = f.name
        
        try:
            # Call Node.js script
            result = subprocess.run(
                ['node', str(self.node_script), input_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"D3 layout failed: {result.stderr}")
            
            # Parse output
            output_data = json.loads(result.stdout)
            
            # Convert back to our format
            return self._parse_output(output_data, egi)
            
        finally:
            # Clean up temp file
            Path(input_file).unlink(missing_ok=True)
    
    def _prepare_input(self, egi: RelationalGraphWithCuts, hierarchy: Dict, 
                      area_bounds: Dict, iterations: int) -> Dict:
        """Prepare input JSON for D3 script"""
        
        nodes = []
        links = []
        
        # Add all vertices
        for area_id, info in hierarchy.items():
            area_rect = area_bounds.get(area_id)
            if not area_rect:
                continue
            
            for vertex_id in info['vertices']:
                nodes.append({
                    'id': vertex_id,
                    'type': 'vertex',
                    'area_id': area_id,
                    # Initialize in area (avoiding child cuts will be done by D3)
                    'x': area_rect.x + area_rect.width / 2,
                    'y': area_rect.y + area_rect.height / 2
                })
            
            for edge_id in info['edges']:
                nodes.append({
                    'id': edge_id,
                    'type': 'edge_label',
                    'label': egi.rel.get(edge_id, '?'),
                    'area_id': area_id,
                    'x': area_rect.x + area_rect.width / 2,
                    'y': area_rect.y + area_rect.height / 2
                })
        
        # Add ligature connections
        for edge_id, vertex_sequence in egi.nu.items():
            for vertex_id in vertex_sequence:
                links.append({
                    'source': edge_id,
                    'target': vertex_id
                })
        
        # Convert area bounds to simple dict format
        areas_dict = {}
        for area_id, rect in area_bounds.items():
            areas_dict[area_id] = {
                'x': rect.x,
                'y': rect.y,
                'width': rect.width,
                'height': rect.height
            }
        
        # Convert hierarchy to simple dict format
        hierarchy_dict = {}
        for area_id, info in hierarchy.items():
            hierarchy_dict[area_id] = {
                'children': info['children']
            }
        
        return {
            'nodes': nodes,
            'links': links,
            'areas': areas_dict,
            'hierarchy': hierarchy_dict,
            'iterations': iterations
        }
    
    def _parse_output(self, output_data: Dict, egi: RelationalGraphWithCuts) -> Tuple[Dict, Dict]:
        """
        Parse D3 output - positions are in LOCAL coordinates per area.
        Renderer will transform based on hierarchy.
        """
        
        local_positions = {'vertices': {}, 'edge_labels': {}}
        
        for node in output_data['nodes']:
            node_id = node['id']
            x, y = node['x'], node['y']
            area_id = node['area_id']
            
            if node_id in egi.nu:
                # It's an edge - position is LOCAL to its area
                rel_name = egi.rel.get(node_id, '?')
                local_positions['edge_labels'][node_id] = {
                    'x': x,  # LOCAL coordinates
                    'y': y,  # LOCAL coordinates
                    'width': len(rel_name) * 8,
                    'height': 12,
                    'label': rel_name,
                    'parent_area_id': area_id
                }
            else:
                # It's a vertex - position is LOCAL to its area
                local_positions['vertices'][node_id] = {
                    'x': x,  # LOCAL coordinates
                    'y': y,  # LOCAL coordinates
                    'parent_area_id': area_id
                }
        
        # Area bounds - all at origin (0,0) in LOCAL space
        from constrained_force_layout import Rect
        area_bounds = {}
        for area_id, area_data in output_data['areas'].items():
            area_bounds[area_id] = Rect(
                0,  # LOCAL origin
                0,  # LOCAL origin
                area_data['width'],
                area_data['height']
            )
        
        return local_positions, area_bounds
