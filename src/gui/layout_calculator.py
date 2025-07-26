"""
Layout calculator for EGRF elements with proper dynamic sizing and containment.
"""

from typing import Dict, Any, List, Tuple
import math

class LayoutCalculator:
    """Calculate layout positions and sizes for EGRF elements."""
    
    def __init__(self, canvas_width=1200, canvas_height=800):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = 20
        self.cut_padding = 30
        self.predicate_width = 80
        self.predicate_height = 40
        self.entity_width = 100
        self.entity_height = 20
    
    def calculate_layout(self, egrf_doc) -> Dict[str, Any]:
        """Calculate layout for all EGRF elements with proper containment."""
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
        
        # Sort contexts by containment level (deepest first for sizing)
        contexts.sort(key=lambda x: x['containment_level'], reverse=True)
        
        print(f"Processing {len(contexts)} contexts, {len(predicates)} predicates, {len(entities)} entities")
        
        # Step 1: Calculate content layout (predicates and entities)
        content_layout = self._calculate_content_layout(predicates, entities, contexts)
        layout_data.update(content_layout)
        
        # Step 2: Calculate context sizes based on content (inside-out)
        context_layout = self._calculate_context_layout(contexts, layout_data)
        layout_data.update(context_layout)
        
        # Step 3: Calculate line connections
        line_layout = self._calculate_line_connections(entities, layout_data)
        layout_data.update(line_layout)
        
        return layout_data
    
    def _calculate_content_layout(self, predicates: List[Dict], entities: List[Dict], contexts: List[Dict]) -> Dict[str, Any]:
        """Calculate layout for predicates and entities based on their containment."""
        layout_data = {}
        
        # Create context lookup by ID
        context_lookup = {ctx['id']: ctx for ctx in contexts}
        
        # Position predicates based on their parent_container
        for pred in predicates:
            parent_id = pred['parent_container']
            if parent_id and parent_id in context_lookup:
                parent_ctx = context_lookup[parent_id]
                level = parent_ctx['containment_level']
                
                # Calculate position based on containment level
                # Higher levels (deeper cuts) should be more centered
                base_x = 50 + (level * 40)
                base_y = 50 + (level * 40)
                
                layout_data[pred['id']] = {
                    'element_type': 'predicate',
                    'position': {'x': base_x, 'y': base_y},
                    'size': {'width': self.predicate_width, 'height': self.predicate_height},
                    'bounds': {'x': base_x, 'y': base_y, 'width': self.predicate_width, 'height': self.predicate_height},
                    'nesting_level': level,
                    'name': pred['properties'].get('name', 'Unknown'),
                    'hook_points': self._calculate_predicate_hooks(base_x, base_y, self.predicate_width, self.predicate_height)
                }
        
        # Position entities based on their parent_container
        for ent in entities:
            parent_id = ent['parent_container']
            if parent_id and parent_id in context_lookup:
                parent_ctx = context_lookup[parent_id]
                level = parent_ctx['containment_level']
                
                # Position entity to connect predicates
                base_x = 200 + (level * 40)
                base_y = 50 + (level * 40)
                
                layout_data[ent['id']] = {
                    'element_type': 'entity',
                    'position': {'x': base_x, 'y': base_y},
                    'size': {'width': self.entity_width, 'height': self.entity_height},
                    'bounds': {'x': base_x, 'y': base_y, 'width': self.entity_width, 'height': self.entity_height},
                    'nesting_level': level,
                    'name': ent['properties'].get('name', 'Unknown'),
                    'entity_type': ent['properties'].get('entity_type', 'constant'),
                    'connected_predicates': ent['properties'].get('connected_entities', []),
                    'line_segments': []  # Will be calculated later
                }
        
        return layout_data
    
    def _calculate_context_layout(self, contexts: List[Dict], content_layout: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate context sizes and positions based on their content (inside-out)."""
        layout_data = {}
        
        # Process contexts from deepest to shallowest
        for context in contexts:
            context_id = context['id']
            level = context['containment_level']
            logical_type = context['logical_type']
            
            if logical_type == 'sheet':
                # Sheet encompasses everything
                layout_data[context_id] = {
                    'element_type': 'context',
                    'position': {'x': self.padding, 'y': self.padding},
                    'size': {'width': self.canvas_width - 2*self.padding, 'height': self.canvas_height - 2*self.padding},
                    'bounds': {'x': self.padding, 'y': self.padding, 'width': self.canvas_width - 2*self.padding, 'height': self.canvas_height - 2*self.padding},
                    'nesting_level': level,
                    'semantic_role': 'Sheet of Assertion'
                }
            else:
                # Cut: size based on content
                content_bounds = self._get_content_bounds(context_id, content_layout, layout_data)
                
                # Add padding around content
                cut_x = content_bounds['min_x'] - self.cut_padding
                cut_y = content_bounds['min_y'] - self.cut_padding
                cut_width = content_bounds['width'] + 2*self.cut_padding
                cut_height = content_bounds['height'] + 2*self.cut_padding
                
                # Ensure minimum size
                cut_width = max(cut_width, 120)
                cut_height = max(cut_height, 80)
                
                layout_data[context_id] = {
                    'element_type': 'context',
                    'position': {'x': cut_x, 'y': cut_y},
                    'size': {'width': cut_width, 'height': cut_height},
                    'bounds': {'x': cut_x, 'y': cut_y, 'width': cut_width, 'height': cut_height},
                    'nesting_level': level,
                    'semantic_role': context['properties'].get('name', f'Cut Level {level}')
                }
        
        return layout_data
    
    def _get_content_bounds(self, context_id: str, content_layout: Dict[str, Any], context_layout: Dict[str, Any]) -> Dict[str, float]:
        """Get the bounding box of all content in a context."""
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # Check all content elements
        for element_id, layout_info in content_layout.items():
            bounds = layout_info.get('bounds', {})
            if bounds:
                min_x = min(min_x, bounds['x'])
                min_y = min(min_y, bounds['y'])
                max_x = max(max_x, bounds['x'] + bounds['width'])
                max_y = max(max_y, bounds['y'] + bounds['height'])
        
        # Check child contexts
        for element_id, layout_info in context_layout.items():
            if layout_info.get('nesting_level', 0) > context_layout.get(context_id, {}).get('nesting_level', 0):
                bounds = layout_info.get('bounds', {})
                if bounds:
                    min_x = min(min_x, bounds['x'])
                    min_y = min(min_y, bounds['y'])
                    max_x = max(max_x, bounds['x'] + bounds['width'])
                    max_y = max(max_y, bounds['y'] + bounds['height'])
        
        # Handle empty contexts
        if min_x == float('inf'):
            min_x = 100
            min_y = 100
            max_x = 200
            max_y = 150
        
        return {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def _calculate_predicate_hooks(self, x: float, y: float, width: float, height: float) -> List[Dict[str, Any]]:
        """Calculate hook points around a predicate for line connections."""
        center_x = x + width / 2
        center_y = y + height / 2
        
        return [
            {'x': center_x, 'y': y, 'side': 'top'},
            {'x': x + width, 'y': center_y, 'side': 'right'},
            {'x': center_x, 'y': y + height, 'side': 'bottom'},
            {'x': x, 'y': center_y, 'side': 'left'}
        ]
    
    def _calculate_line_connections(self, entities: List[Dict], layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate line of identity connections between predicates through entities."""
        line_layout = {}
        
        for entity in entities:
            entity_id = entity['id']
            entity_layout = layout_data.get(entity_id)
            if not entity_layout:
                continue
            
            # Find predicates that connect to this entity
            # Look through all predicates to see which ones reference this entity
            connected_predicate_ids = []
            for element_id, layout_info in layout_data.items():
                if layout_info.get('element_type') == 'predicate':
                    # Check if this predicate connects to our entity
                    # We need to look at the original predicate data
                    for pred in [p for p in layout_data.values() if p.get('element_type') == 'predicate']:
                        # For now, connect all predicates to the entity (simplified)
                        connected_predicate_ids.append(element_id)
                        break
            
            # Get all predicate IDs for connection
            all_predicate_ids = [eid for eid, info in layout_data.items() if info.get('element_type') == 'predicate']
            
            if len(all_predicate_ids) >= 2:
                # Calculate line segments connecting predicates through entity
                entity_pos = entity_layout['position']
                entity_center = {
                    'x': entity_pos['x'] + entity_layout['size']['width'] / 2,
                    'y': entity_pos['y'] + entity_layout['size']['height'] / 2
                }
                
                line_segments = []
                for pred_id in all_predicate_ids:
                    pred_layout = layout_data.get(pred_id)
                    if pred_layout and pred_layout.get('element_type') == 'predicate':
                        # Find closest hook point
                        hooks = pred_layout.get('hook_points', [])
                        if hooks:
                            closest_hook = min(hooks, key=lambda h: 
                                math.sqrt((h['x'] - entity_center['x'])**2 + (h['y'] - entity_center['y'])**2))
                            
                            # Create line segment from hook to entity center
                            line_segments.append({
                                'type': 'line',
                                'points': [
                                    {'x': closest_hook['x'], 'y': closest_hook['y']},
                                    {'x': entity_center['x'], 'y': entity_center['y']}
                                ]
                            })
                
                # Update entity layout with line segments
                if line_segments:
                    entity_layout['line_segments'] = line_segments
                    line_layout[entity_id] = entity_layout
        
        return line_layout

