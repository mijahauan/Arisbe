"""
Area-based layout calculator for EGRF elements.

This calculator properly distinguishes between contexts and areas:
- Context: The entire containment hierarchy of a cut
- Area: The specific region inside a cut, excluding nested cuts

Predicates are positioned within their immediate area only.
"""

from typing import Dict, Any, List, Tuple
import math

class AreaBasedLayoutCalculator:
    """Calculate layout positions based on cut areas, not contexts."""
    
    def __init__(self, canvas_width=1200, canvas_height=800):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = 20
        self.cut_padding = 50  # Increased for better separation
        self.predicate_width = 80
        self.predicate_height = 40
        self.entity_width = 100
        self.entity_height = 20
    
    def calculate_layout(self, egrf_doc) -> Dict[str, Any]:
        """Calculate layout for all EGRF elements using area-based positioning."""
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
        
        # Sort contexts by containment level
        contexts.sort(key=lambda x: x['containment_level'])
        
        print(f"Area-based processing: {len(contexts)} contexts, {len(predicates)} predicates, {len(entities)} entities")
        
        # Step 1: Calculate cut boundaries and areas
        cut_areas = self._calculate_cut_areas(contexts)
        
        # Step 2: Position predicates in their specific areas
        predicate_layout = self._position_predicates_in_areas(predicates, cut_areas)
        layout_data.update(predicate_layout)
        
        # Step 3: Position entities in their areas
        entity_layout = self._position_entities_in_areas(entities, cut_areas)
        layout_data.update(entity_layout)
        
        # Step 4: Calculate context graphics (cuts and sheet)
        context_layout = self._calculate_context_graphics(contexts, cut_areas)
        layout_data.update(context_layout)
        
        # Step 5: Calculate line connections
        line_layout = self._calculate_line_connections(entities, layout_data)
        layout_data.update(line_layout)
        
        return layout_data
    
    def _calculate_cut_areas(self, contexts: List[Dict]) -> Dict[str, Dict]:
        """Calculate the area boundaries for each cut, excluding nested cuts."""
        cut_areas = {}
        
        # Start with sheet bounds
        sheet_bounds = {
            'x': self.padding,
            'y': self.padding,
            'width': self.canvas_width - 2 * self.padding,
            'height': self.canvas_height - 2 * self.padding
        }
        
        # Find sheet context
        sheet_ctx = next((ctx for ctx in contexts if ctx['logical_type'] == 'sheet'), None)
        if sheet_ctx:
            cut_areas[sheet_ctx['id']] = {
                'bounds': sheet_bounds,
                'area': sheet_bounds.copy(),  # Sheet area is same as bounds
                'level': 0
            }
        
        # Calculate cut areas from outside-in
        for ctx in contexts:
            if ctx['logical_type'] == 'cut':
                level = ctx['containment_level']
                
                # Calculate cut bounds based on level
                margin = self.cut_padding * level
                cut_bounds = {
                    'x': sheet_bounds['x'] + margin,
                    'y': sheet_bounds['y'] + margin,
                    'width': sheet_bounds['width'] - 2 * margin,
                    'height': sheet_bounds['height'] - 2 * margin
                }
                
                # Calculate area inside this cut (excluding nested cuts)
                area_padding = 15
                cut_area = {
                    'x': cut_bounds['x'] + area_padding,
                    'y': cut_bounds['y'] + area_padding,
                    'width': cut_bounds['width'] - 2 * area_padding,
                    'height': cut_bounds['height'] - 2 * area_padding
                }
                
                # Exclude nested cuts from this area
                nested_cuts = [c for c in contexts if c['containment_level'] > level]
                if nested_cuts:
                    # Find the immediate child cut
                    immediate_child = min(nested_cuts, key=lambda c: c['containment_level'])
                    child_level = immediate_child['containment_level']
                    child_margin = self.cut_padding * child_level
                    
                    # Reduce area to exclude child cut
                    child_bounds = {
                        'x': sheet_bounds['x'] + child_margin,
                        'y': sheet_bounds['y'] + child_margin,
                        'width': sheet_bounds['width'] - 2 * child_margin,
                        'height': sheet_bounds['height'] - 2 * child_margin
                    }
                    
                    # Area is the space between this cut and the child cut
                    # For simplicity, position elements in the top-left area
                    available_width = child_bounds['x'] - cut_area['x']
                    available_height = child_bounds['y'] - cut_area['y']
                    
                    if available_width > 50 and available_height > 50:
                        cut_area = {
                            'x': cut_area['x'],
                            'y': cut_area['y'],
                            'width': available_width,
                            'height': available_height
                        }
                
                cut_areas[ctx['id']] = {
                    'bounds': cut_bounds,
                    'area': cut_area,
                    'level': level
                }
        
        return cut_areas
    
    def _position_predicates_in_areas(self, predicates: List[Dict], cut_areas: Dict) -> Dict[str, Any]:
        """Position predicates within their specific cut areas."""
        layout_data = {}
        
        # Group predicates by their parent container (area)
        predicates_by_area = {}
        for pred in predicates:
            parent_id = pred['parent_container']
            if parent_id not in predicates_by_area:
                predicates_by_area[parent_id] = []
            predicates_by_area[parent_id].append(pred)
        
        # Position predicates in each area
        for parent_id, area_predicates in predicates_by_area.items():
            if parent_id and parent_id in cut_areas:
                area_info = cut_areas[parent_id]
                area = area_info['area']
                level = area_info['level']
                
                # Position multiple predicates with spacing
                for i, pred in enumerate(area_predicates):
                    # Calculate position with spacing for multiple predicates
                    pred_x = area['x'] + 20 + (i * (self.predicate_width + 20))
                    pred_y = area['y'] + 20
                    
                    # Ensure it fits in the area
                    if pred_x + self.predicate_width > area['x'] + area['width']:
                        # Wrap to next row
                        pred_x = area['x'] + 20
                        pred_y = area['y'] + 20 + (self.predicate_height + 20)
                    
                    if pred_y + self.predicate_height > area['y'] + area['height']:
                        pred_y = area['y'] + area['height'] - self.predicate_height - 10
                    
                    layout_data[pred['id']] = {
                        'element_type': 'predicate',
                        'position': {'x': pred_x, 'y': pred_y},
                        'size': {'width': self.predicate_width, 'height': self.predicate_height},
                        'bounds': {'x': pred_x, 'y': pred_y, 'width': self.predicate_width, 'height': self.predicate_height},
                        'nesting_level': level,
                        'name': pred['properties'].get('name', 'Unknown'),
                        'hook_points': self._calculate_predicate_hooks(pred_x, pred_y, self.predicate_width, self.predicate_height)
                    }
        
        return layout_data
    
    def _position_entities_in_areas(self, entities: List[Dict], cut_areas: Dict) -> Dict[str, Any]:
        """Position entities within their specific cut areas."""
        layout_data = {}
        
        for ent in entities:
            parent_id = ent['parent_container']
            if parent_id and parent_id in cut_areas:
                area_info = cut_areas[parent_id]
                area = area_info['area']
                level = area_info['level']
                
                # Position entity in the area (below predicates)
                ent_x = area['x'] + 20
                ent_y = area['y'] + 80  # Below predicates
                
                # Ensure it fits in the area
                if ent_x + self.entity_width > area['x'] + area['width']:
                    ent_x = area['x'] + area['width'] - self.entity_width - 20
                if ent_y + self.entity_height > area['y'] + area['height']:
                    ent_y = area['y'] + area['height'] - self.entity_height - 10
                
                layout_data[ent['id']] = {
                    'element_type': 'entity',
                    'position': {'x': ent_x, 'y': ent_y},
                    'size': {'width': self.entity_width, 'height': self.entity_height},
                    'bounds': {'x': ent_x, 'y': ent_y, 'width': self.entity_width, 'height': self.entity_height},
                    'nesting_level': level,
                    'name': ent['properties'].get('name', 'Unknown'),
                    'entity_type': ent['properties'].get('entity_type', 'constant'),
                    'connected_predicates': ent['properties'].get('connected_entities', []),
                    'line_segments': []  # Will be calculated later
                }
        
        return layout_data
    
    def _calculate_context_graphics(self, contexts: List[Dict], cut_areas: Dict) -> Dict[str, Any]:
        """Calculate graphics layout for contexts (cuts and sheet)."""
        layout_data = {}
        
        for ctx in contexts:
            ctx_id = ctx['id']
            if ctx_id in cut_areas:
                area_info = cut_areas[ctx_id]
                bounds = area_info['bounds']
                level = area_info['level']
                
                layout_data[ctx_id] = {
                    'element_type': 'context',
                    'position': {'x': bounds['x'], 'y': bounds['y']},
                    'size': {'width': bounds['width'], 'height': bounds['height']},
                    'bounds': bounds,
                    'nesting_level': level,
                    'semantic_role': ctx['properties'].get('name', f'Level {level}')
                }
        
        return layout_data
    
    def _calculate_predicate_hooks(self, x: float, y: float, width: float, height: float) -> List[Dict]:
        """Calculate hook points for predicate connections."""
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

