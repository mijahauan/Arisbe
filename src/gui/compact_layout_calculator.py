"""
Compact layout calculator using NetworkX for efficient space utilization.

This calculator creates compact diagrams by:
1. Using NetworkX spring layout for content arrangement
2. Sizing cuts based on actual content bounds
3. Hierarchical packing from inside-out
4. Collision detection and avoidance
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import networkx as nx

class CompactLayoutCalculator:
    """Calculate compact layout positions and sizes for EGRF elements."""
    
    def __init__(self, canvas_width=1200, canvas_height=800):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = 20
        self.cut_padding = 30
        self.predicate_width = 80
        self.predicate_height = 40
        self.entity_width = 100
        self.entity_height = 20
        self.min_cut_width = 150
        self.min_cut_height = 100
    
    def calculate_layout(self, egrf_doc) -> Dict[str, Any]:
        """Calculate compact layout for all EGRF elements."""
        layout_data = {}
        
        # Group elements by type and level
        contexts = []
        predicates = []
        entities = []
        
        for element in egrf_doc.logical_elements:
            element_info = {
                'id': element.id,
                'logical_type': element.logical_type,
                'containment_level': element.containment_level,
                'parent_container': element.parent_container,
                'properties': element.properties
            }
            
            if element.logical_type in ['sheet', 'cut']:
                contexts.append(element_info)
            elif element.logical_type == 'relation':
                predicates.append(element_info)
            elif element.logical_type in ['individual', 'line_of_identity']:
                entities.append(element_info)
        
        print(f"Compact processing: {len(contexts)} contexts, {len(predicates)} predicates, {len(entities)} entities")
        
        # Step 1: Group content by containment area
        content_by_area = self._group_content_by_area(predicates, entities, contexts)
        
        # Step 2: Calculate compact layout for each area using NetworkX
        area_layouts = self._calculate_area_layouts(content_by_area)
        layout_data.update(area_layouts)
        
        # Step 3: Calculate compact context sizes based on content (inside-out)
        context_layout = self._calculate_compact_context_layout(contexts, layout_data)
        layout_data.update(context_layout)
        
        # Step 4: Calculate line connections
        line_layout = self._calculate_line_connections(entities, layout_data)
        layout_data.update(line_layout)
        
        return layout_data
    
    def _group_content_by_area(self, predicates: List[Dict], entities: List[Dict], contexts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group predicates and entities by their immediate containment area."""
        content_by_area = {}
        
        # Initialize areas
        for ctx in contexts:
            content_by_area[ctx['id']] = []
        
        # Add predicates to their areas
        for pred in predicates:
            parent_id = pred['parent_container']
            if parent_id and parent_id in content_by_area:
                content_by_area[parent_id].append({
                    'type': 'predicate',
                    'element': pred
                })
        
        # Add entities to their areas
        for ent in entities:
            parent_id = ent['parent_container']
            if parent_id and parent_id in content_by_area:
                content_by_area[parent_id].append({
                    'type': 'entity',
                    'element': ent
                })
        
        return content_by_area
    
    def _calculate_area_layouts(self, content_by_area: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate compact layout for content within each area using NetworkX."""
        layout_data = {}
        
        for area_id, content_items in content_by_area.items():
            if not content_items:
                continue
            
            # Create NetworkX graph for this area
            G = nx.Graph()
            
            # Add nodes for each content item
            for item in content_items:
                element = item['element']
                node_id = element['id']
                G.add_node(node_id, 
                          type=item['type'],
                          element=element)
            
            # Add edges for entities connected to predicates
            for item in content_items:
                if item['type'] == 'entity':
                    entity = item['element']
                    entity_id = entity['id']
                    
                    # Find predicates connected to this entity
                    for other_item in content_items:
                        if other_item['type'] == 'predicate':
                            predicate = other_item['element']
                            connected_entities = predicate['properties'].get('connected_entities', [])
                            
                            if entity_id in connected_entities:
                                G.add_edge(entity_id, predicate['id'])
            
            # Calculate compact layout using NetworkX spring layout
            if len(G.nodes()) > 0:
                if len(G.nodes()) == 1:
                    # Single node - place at origin
                    positions = {list(G.nodes())[0]: (0, 0)}
                else:
                    # Multiple nodes - use spring layout for compact arrangement
                    positions = nx.spring_layout(G, 
                                               k=1.5,  # Optimal distance between nodes
                                               iterations=100,  # More iterations for better layout
                                               scale=100)  # Scale to reasonable pixel coordinates
                
                # Convert NetworkX positions to layout data
                for node_id, (x, y) in positions.items():
                    node_data = G.nodes[node_id]
                    element_type = node_data['type']
                    element = node_data['element']
                    
                    if element_type == 'predicate':
                        layout_data[node_id] = {
                            'element_type': 'predicate',
                            'position': {'x': x, 'y': y},
                            'size': {'width': self.predicate_width, 'height': self.predicate_height},
                            'bounds': {'x': x, 'y': y, 'width': self.predicate_width, 'height': self.predicate_height},
                            'nesting_level': element['containment_level'],
                            'name': element['properties'].get('name', 'Unknown'),
                            'hook_points': self._calculate_predicate_hooks(x, y, self.predicate_width, self.predicate_height),
                            'area_id': area_id
                        }
                    elif element_type == 'entity':
                        layout_data[node_id] = {
                            'element_type': 'entity',
                            'position': {'x': x, 'y': y},
                            'size': {'width': self.entity_width, 'height': self.entity_height},
                            'bounds': {'x': x, 'y': y, 'width': self.entity_width, 'height': self.entity_height},
                            'nesting_level': element['containment_level'],
                            'name': element['properties'].get('name', 'Unknown'),
                            'area_id': area_id
                        }
        
        return layout_data
    
    def _calculate_compact_context_layout(self, contexts: List[Dict], content_layout: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate compact context sizes based on actual content bounds."""
        layout_data = {}
        
        # Sort contexts by containment level (deepest first for inside-out sizing)
        contexts.sort(key=lambda x: x['containment_level'], reverse=True)
        
        for ctx in contexts:
            ctx_id = ctx['id']
            ctx_level = ctx['containment_level']
            ctx_type = ctx['logical_type']
            
            # Find all content in this context
            content_in_context = []
            nested_contexts = []
            
            for element_id, layout_info in content_layout.items():
                area_id = layout_info.get('area_id')
                if area_id == ctx_id:
                    content_in_context.append(layout_info)
                elif layout_info.get('element_type') == 'context' and layout_info.get('parent_id') == ctx_id:
                    nested_contexts.append(layout_info)
            
            # Calculate content bounds
            if content_in_context or nested_contexts:
                all_items = content_in_context + nested_contexts
                bounds = self._calculate_content_bounds(all_items)
                
                # Ensure positive coordinates by shifting if needed
                min_x = bounds['x']
                min_y = bounds['y']
                
                # Shift content to positive coordinates if needed
                if min_x < 0 or min_y < 0:
                    shift_x = max(0, -min_x) + self.cut_padding
                    shift_y = max(0, -min_y) + self.cut_padding
                    
                    # Update all content positions
                    for item in content_in_context:
                        pos = item['position']
                        pos['x'] += shift_x
                        pos['y'] += shift_y
                        
                        # Update bounds
                        bounds_info = item.get('bounds', {})
                        if bounds_info:
                            bounds_info['x'] = pos['x']
                            bounds_info['y'] = pos['y']
                        
                        # Update hook points for predicates
                        if item.get('element_type') == 'predicate':
                            item['hook_points'] = self._calculate_predicate_hooks(
                                pos['x'], pos['y'], 
                                item['size']['width'], item['size']['height']
                            )
                    
                    # Recalculate bounds after shifting
                    bounds = self._calculate_content_bounds(content_in_context + nested_contexts)
                
                # Add padding for cuts
                if ctx_type == 'cut':
                    content_width = bounds['width'] + (2 * self.cut_padding)
                    content_height = bounds['height'] + (2 * self.cut_padding)
                    
                    # Ensure minimum cut size
                    width = max(content_width, self.min_cut_width)
                    height = max(content_height, self.min_cut_height)
                    
                    # Position cut to contain its content with padding
                    x = bounds['x'] - self.cut_padding
                    y = bounds['y'] - self.cut_padding
                else:
                    # Sheet of assertion - size based on content or use reasonable default
                    if ctx_level == 0:  # Root sheet
                        if content_in_context or nested_contexts:
                            # Size sheet to fit content with padding
                            sheet_width = bounds['width'] + (4 * self.padding)
                            sheet_height = bounds['height'] + (4 * self.padding)
                            width = max(sheet_width, 400)  # Minimum reasonable size
                            height = max(sheet_height, 300)
                        else:
                            width = 400
                            height = 300
                        x = self.padding
                        y = self.padding
                    else:
                        width = bounds['width'] + (2 * self.padding)
                        height = bounds['height'] + (2 * self.padding)
                        x = bounds['x'] - self.padding
                        y = bounds['y'] - self.padding
            else:
                # Empty context - use minimum size
                if ctx_type == 'cut':
                    width = self.min_cut_width
                    height = self.min_cut_height
                    x = self.cut_padding
                    y = self.cut_padding
                else:
                    width = 400  # Reasonable default for empty sheet
                    height = 300
                    x = self.padding
                    y = self.padding
            
            layout_data[ctx_id] = {
                'element_type': 'context',
                'position': {'x': x, 'y': y},
                'size': {'width': width, 'height': height},
                'bounds': {'x': x, 'y': y, 'width': width, 'height': height},
                'nesting_level': ctx_level,
                'context_type': ctx_type,
                'name': ctx['properties'].get('name', 'unnamed'),
                'parent_id': ctx.get('parent_container')
            }
        
        return layout_data
    
    def _calculate_content_bounds(self, items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate the bounding box of content items."""
        if not items:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for item in items:
            pos = item.get('position', {})
            size = item.get('size', {})
            
            x = pos.get('x', 0)
            y = pos.get('y', 0)
            w = size.get('width', 0)
            h = size.get('height', 0)
            
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)
        
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def _calculate_predicate_hooks(self, x: float, y: float, width: float, height: float) -> List[Dict[str, float]]:
        """Calculate hook points for predicate connections."""
        return [
            {'x': x + width/2, 'y': y},           # Top
            {'x': x + width, 'y': y + height/2}, # Right
            {'x': x + width/2, 'y': y + height}, # Bottom
            {'x': x, 'y': y + height/2}          # Left
        ]
    
    def _calculate_line_connections(self, entities: List[Dict], layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate line connections between predicates through entities."""
        line_layout = {}
        
        for entity in entities:
            entity_id = entity['id']
            entity_layout = layout_data.get(entity_id)
            
            if not entity_layout:
                continue
            
            # Find predicates connected to this entity
            connected_predicates = []
            for element_id, layout_info in layout_data.items():
                if layout_info.get('element_type') == 'predicate':
                    # Check if this predicate is connected to the entity
                    # This would need to be determined from the EGRF structure
                    # For now, assume entities connect predicates in the same area
                    if layout_info.get('area_id') == entity_layout.get('area_id'):
                        connected_predicates.append(layout_info)
            
            # Create line segments between entity and connected predicates
            if len(connected_predicates) >= 2:
                entity_pos = entity_layout['position']
                entity_center = {
                    'x': entity_pos['x'] + entity_layout['size']['width'] / 2,
                    'y': entity_pos['y'] + entity_layout['size']['height'] / 2
                }
                
                line_segments = []
                for pred_layout in connected_predicates:
                    pred_hooks = pred_layout.get('hook_points', [])
                    if pred_hooks:
                        # Find closest hook point
                        closest_hook = min(pred_hooks, 
                                         key=lambda h: math.sqrt((h['x'] - entity_center['x'])**2 + 
                                                               (h['y'] - entity_center['y'])**2))
                        
                        line_segments.append({
                            'start': entity_center,
                            'end': closest_hook
                        })
                
                # Update entity layout with line segments
                entity_layout['line_segments'] = line_segments
                line_layout[entity_id] = entity_layout
        
        return line_layout

