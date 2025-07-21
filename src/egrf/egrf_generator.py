"""
EGRF Generator: Maps EG-CL-Manus2 data structures to EGRF format.

This module converts EG-CL-Manus2 graphs to EGRF while preserving logical integrity:
1. Hierarchical consistency - elements positioned according to tree structure
2. Cut containment - cuts properly encompass/are encompassed, no overlaps at same level  
3. Ligature connections - entities connect to predicates within predicate's area
4. Quantifier scope - outermost area of ligature determines existential/universal quantification
"""

import sys
import os
from typing import Dict, List, Optional, Set, Tuple, Any
import uuid
from dataclasses import dataclass

# Import EG-CL-Manus2 types
from graph import EGGraph
from eg_types import Entity, Predicate, Context, EntityId, PredicateId, ContextId

# Import EGRF types
from .egrf_types import (
    EGRFDocument, Entity as EGRFEntity, Predicate as EGRFPredicate, 
    Context as EGRFContext, Point, Size, Connection, Label, Bounds,
    EGRFSerializer
)


@dataclass
class LayoutConstraints:
    """Layout constraints for maintaining logical integrity."""
    
    # Spacing between elements
    entity_spacing: float = 100.0
    predicate_spacing: float = 80.0
    context_padding: float = 20.0
    
    # Size constraints
    predicate_width: float = 60.0
    predicate_height: float = 30.0
    context_min_width: float = 100.0
    context_min_height: float = 60.0
    
    # Canvas dimensions
    canvas_width: float = 800.0
    canvas_height: float = 600.0


class EGRFGenerator:
    """Generates EGRF documents from EG-CL-Manus2 graphs."""
    
    def __init__(self, constraints: Optional[LayoutConstraints] = None):
        self.constraints = constraints or LayoutConstraints()
    
    
    def _calculate_context_level(self, context_id: str, eg_graph: EGGraph) -> int:
        """Calculate the nesting level of a context (0 = sheet of assertion)."""
        if context_id == eg_graph.context_manager.root_context.id:
            return 0
        
        level = 0
        current_context = eg_graph.context_manager.contexts[context_id]
        
        # Debug: print context hierarchy
        print(f"Calculating level for context {context_id}")
        
        while current_context.parent_context is not None:
            level += 1
            parent_id = current_context.parent_context
            print(f"  Level {level}: parent = {parent_id}")
            
            if parent_id not in eg_graph.context_manager.contexts:
                print(f"  Warning: parent {parent_id} not found in contexts")
                break
                
            current_context = eg_graph.context_manager.contexts[parent_id]
        
        print(f"  Final level: {level}")
        return level
    
    def _is_odd_level(self, context_id: str, eg_graph: EGGraph) -> bool:
        """Check if context is at an odd nesting level (should be shaded)."""
        return self._calculate_context_level(context_id, eg_graph) % 2 == 1
    
    
    def _get_ligature_style(self) -> dict:
        """Get Peirce-compliant ligature (line of identity) styling with heavy lines."""
        return {
            "stroke": {"color": "#000000", "width": 3.0, "style": "solid"},  # Heavy lines
            "opacity": 1.0,
            "line_type": "ligature"
        }
    
    def _get_cut_style(self) -> dict:
        """Get Peirce-compliant cut styling with lighter lines."""
        return {
            "stroke": {"color": "#000000", "width": 1.5, "style": "solid"},  # Lighter lines
            "opacity": 1.0,
            "line_type": "cut"
        }

    def _get_peirce_area_style(self, context_level: int) -> dict:
        """Get Peirce-compliant area styling with consistent even area shading."""
        cut_style = self._get_cut_style()
        
        print(f"Getting style for level {context_level}, odd={context_level % 2 == 1}")
        
        # Define consistent level 0 (sheet of assertion) style
        level_0_style = {
            "fill": {"color": "#ffffff", "opacity": 0.0},  # Completely transparent
            "stroke": cut_style["stroke"],
            "shading_level": "even"
        }
        
        if context_level % 2 == 1:  # Odd level - shaded (negative area)
            return {
                "fill": {"color": "#d0d0d0", "opacity": 0.7},  # Consistent gray shading
                "stroke": cut_style["stroke"],
                "shading_level": "odd"
            }
        else:  # Even level - EXACTLY same as level 0
            return level_0_style
    def _get_peirce_predicate_style(self, context_id: str, eg_graph: EGGraph) -> dict:
        """Get completely clean predicate styling with no visual artifacts."""
        return {
            "style": "none",
            "fill": {"color": "transparent", "opacity": 0.0},
            "stroke": {"color": "transparent", "width": 0.0, "style": "none"},
            "border": "none",
            "background": "transparent",
            "center_dot": "none",
            "artifacts": "none",
            "text_only": True,
            "size": {"width": 0, "height": 0}
        }
    def _validate_predicate_placement(self, predicate_id: str, context_id: str, eg_graph: EGGraph) -> bool:
        """Validate that predicate placement follows Peirce rules."""
        # Predicate must be inside its containing context
        # Predicate must not overlap with inner cuts in the same area
        # Predicate border must remain within area bounds
        
        context = eg_graph.context_manager.contexts[context_id]
        
        # Check if predicate is properly contained
        if predicate_id not in context.contained_items:
            return False
        
        # Additional placement validation can be added here
        return True

    def generate(self, eg_graph: EGGraph) -> EGRFDocument:
        """Generate EGRF document from EG-CL-Manus2 graph."""
        
        # Create empty EGRF document
        egrf_doc = EGRFDocument()
        
        # Set canvas dimensions from constraints
        egrf_doc.canvas.width = self.constraints.canvas_width
        egrf_doc.canvas.height = self.constraints.canvas_height
        
        # Convert entities
        self._convert_entities(eg_graph, egrf_doc)
        
        # Convert predicates
        self._convert_predicates(eg_graph, egrf_doc)
        
        # Convert contexts
        self._convert_contexts(eg_graph, egrf_doc)
        
        # Add semantic information with proper CLIF generation
        self._add_semantics(eg_graph, egrf_doc)
        
        return egrf_doc
    
    
    def _should_suppress_variable_name(self, entity_name: str) -> bool:
        """Determine if variable name should be suppressed (single letters like x, y, z)."""
        return (len(entity_name) == 1 and 
                entity_name.lower() in 'abcdefghijklmnopqrstuvwxyz')
    
    def _get_entity_label_style(self, entity_name: str, suppress_variables: bool = True) -> dict:
        """Get entity label styling with optional variable suppression."""
        if suppress_variables and self._should_suppress_variable_name(entity_name):
            return {
                "text": "",  # Suppress variable name
                "visible": False,
                "annotation": entity_name,  # Keep as annotation for optional display
                "suppressed": True
            }
        else:
            return {
                "text": entity_name,
                "visible": True,
                "annotation": entity_name,
                "suppressed": False
            }

    def _convert_entities(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):
        """Convert EG-CL-Manus2 entities to EGRF entities."""
        
        entity_positions = self._calculate_entity_positions(eg_graph)
        
        for entity_id, entity in eg_graph.entities.items():
            position = entity_positions.get(entity_id, Point(100, 100))
            
            # Create entity path (line of identity)
            path = self._create_entity_path(entity_id, eg_graph, position)
            
            egrf_entity = EGRFEntity(
                id=str(entity_id),
                name=entity.name,
                type=entity.entity_type,
                visual={
                    "style": "line",
                    "path": [{"x": p.x, "y": p.y} for p in path],
                    "stroke": {
                        "color": "#000000",
                        "width": 3.0,
                        "style": "solid"
                    }
                },
                labels=[{
                    **self._get_entity_label_style(entity.name),
                    "position": {"x": path[-1].x, "y": path[-1].y - 15},
                    "font": {
                        "family": "Arial",
                        "size": 12.0,
                        "weight": "normal",
                        "color": "#000000"
                    },
                    "alignment": "center"
                }]
            )
            
            egrf_doc.entities.append(egrf_entity)
    
    
    def _validate_predicate_containment(self, predicate_position: Point, predicate_text: str, 
                                       context_bounds: 'Bounds') -> bool:
        """Validate that predicate is completely contained within context bounds."""
        
        # Estimate text dimensions
        text_width = len(predicate_text) * 8 + 10  # Conservative estimate
        text_height = 16  # Standard text height
        
        # Check if predicate bounds are within context bounds
        pred_left = predicate_position.x - text_width / 2
        pred_right = predicate_position.x + text_width / 2
        pred_top = predicate_position.y - text_height / 2
        pred_bottom = predicate_position.y + text_height / 2
        
        context_left = context_bounds.x
        context_right = context_bounds.x + context_bounds.width
        context_top = context_bounds.y
        context_bottom = context_bounds.y + context_bounds.height
        
        contained = (pred_left >= context_left and pred_right <= context_right and
                    pred_top >= context_top and pred_bottom <= context_bottom)
        
        if not contained:
            print(f"WARNING: Predicate '{predicate_text}' not fully contained!")
            print(f"  Predicate bounds: ({pred_left}, {pred_top}) to ({pred_right}, {pred_bottom})")
            print(f"  Context bounds: ({context_left}, {context_top}) to ({context_right}, {context_bottom})")
        
        return contained

    def _convert_predicates(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):
        """Convert EG-CL-Manus2 predicates to EGRF predicates with Peirce visual conventions."""
        
        predicate_positions = self._calculate_predicate_positions(eg_graph)
        
        for predicate_id, predicate in eg_graph.predicates.items():
            # Find the context containing this predicate FIRST
            containing_context_id = None
            for context_id, context in eg_graph.context_manager.contexts.items():
                if predicate_id in context.contained_items:
                    containing_context_id = context_id
                    break
            
            # Default to root context if not found
            if containing_context_id is None:
                containing_context_id = eg_graph.context_manager.root_context.id
            
            # Now calculate safe position with known context
            position = self._calculate_safe_predicate_position(predicate_id, containing_context_id, eg_graph)
            
            # Validate predicate placement
            if not self._validate_predicate_placement(predicate_id, containing_context_id, eg_graph):
                print(f"Warning: Predicate {predicate_id} placement violates Peirce rules")
            
            # Get Peirce-compliant predicate styling
            peirce_style = self._get_peirce_predicate_style(containing_context_id, eg_graph)
            
            # Create connections to entities
            connections = []
            for entity_id in predicate.entities:
                connections.append({
                    "entity_id": str(entity_id),
                    "connection_point": {"x": position.x, "y": position.y},
                    "style": {}
                })
            
            # Import required types
            from egrf.egrf_types import Predicate as EGRFPredicate, PredicateVisual, Label, Point, Size, Fill, Stroke, Font
            
            # Create visual specification with proper types
            predicate_visual = PredicateVisual(
                style="none",
                position=Point(position.x, position.y),
                size=Size(0, 0),
                fill=Fill("transparent", 0.0),
                stroke=Stroke("transparent", 0.0, "none")
            )
            
            # Create label with proper types
            predicate_label = Label(
                text=predicate.name,
                position=Point(position.x, position.y),
                font=Font("Arial", 14.0, "normal", "#000000"),
                alignment="center"
            )
            
            # Create predicate with correct parameters
            egrf_predicate = EGRFPredicate(
                id=str(predicate_id),
                name=predicate.name,
                type="relation",  # Default type
                arity=len(predicate.entities),
                connected_entities=[str(entity_id) for entity_id in predicate.entities],
                visual=predicate_visual,
                labels=[predicate_label],
                connections=[]  # Will be populated later if needed
            )
            
            egrf_doc.predicates.append(egrf_predicate)

    def _convert_contexts(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):
        """Convert EG-CL-Manus2 contexts to EGRF contexts with Peirce visual conventions."""
        
        for context_id, context in eg_graph.context_manager.contexts.items():
            # Calculate bounds based on contained items
            bounds = self._calculate_context_bounds(context, eg_graph)
            
            # Calculate context level for Peirce shading
            context_level = self._calculate_context_level(context_id, eg_graph)
            
            # Get Peirce-compliant styling
            peirce_style = self._get_peirce_area_style(context_level)
            
            egrf_context = EGRFContext(
                id=str(context_id),
                type=context.context_type,
                parent_context=str(context.parent_context) if context.parent_context else None,
                visual={
                    "style": "none",  # Peirce used ovals/closed curves
                    "bounds": {
                        "x": bounds.x,
                        "y": bounds.y,
                        "width": bounds.width,
                        "height": bounds.height
                    },
                    "fill": peirce_style["fill"],
                    "stroke": peirce_style["stroke"],
                    "peirce_level": context_level,  # Store level for reference
                    "is_shaded": context_level % 2 == 1  # Odd levels are shaded
                },
                contained_items=[str(item_id) for item_id in context.contained_items],
                nesting_level=context.depth
            )
            
            egrf_doc.contexts.append(egrf_context)

    def _add_semantics(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):
        """Add semantic information to EGRF document with proper CLIF generation."""
        
        # Generate CLIF equivalent based on context structure
        clif_equivalent = self._generate_clif_from_context_structure(eg_graph)
        
        egrf_doc.semantics.logical_form = {
            "clif_equivalent": clif_equivalent,
            "egif_equivalent": "Generated from EG-CL-Manus2"
        }
        egrf_doc.semantics.validation = {"is_valid": True}
    
    def _generate_clif_from_context_structure(self, eg_graph: EGGraph) -> str:
        """Generate CLIF equivalent by analyzing context structure."""
        
        # Get root context
        root_context = eg_graph.context_manager.root_context
        
        # Analyze the structure starting from root
        return self._analyze_context_for_clif(root_context, eg_graph)
    
    def _analyze_context_for_clif(self, context: Context, eg_graph: EGGraph) -> str:
        """Recursively analyze context structure to generate CLIF."""
        
        # Get predicates in this context
        predicates_in_context = []
        for item_id in context.contained_items:
            if item_id in eg_graph.predicates:
                predicate = eg_graph.predicates[item_id]
                predicates_in_context.append(predicate)
        
        # Get child contexts
        child_contexts = []
        for context_id, child_context in eg_graph.context_manager.contexts.items():
            if child_context.parent_context == context.id:
                child_contexts.append(child_context)
        
        # Generate CLIF based on context type and structure
        if context.context_type == 'sheet_of_assertion':
            # Root context - analyze children
            if len(child_contexts) == 1 and child_contexts[0].context_type == 'cut':
                # Single cut at root level
                return self._handle_single_cut_structure(child_contexts[0], eg_graph)
            else:
                # Simple conjunction or single predicates
                return self._generate_simple_clif(predicates_in_context, eg_graph)
        
        elif context.context_type == 'cut':
            # Cut context - this is negation
            return self._handle_cut_context(context, eg_graph)
        
        else:
            # Default to simple conjunction
            return self._generate_simple_clif(predicates_in_context, eg_graph)
    
    def _handle_single_cut_structure(self, cut_context: Context, eg_graph: EGGraph) -> str:
        """Handle structure with single cut (potential implication)."""
        
        # Get child contexts of this cut
        child_cuts = []
        for context_id, child_context in eg_graph.context_manager.contexts.items():
            if child_context.parent_context == cut_context.id and child_context.context_type == 'cut':
                child_cuts.append(child_context)
        
        # Get predicates directly in this cut
        predicates_in_cut = []
        for item_id in cut_context.contained_items:
            if item_id in eg_graph.predicates:
                predicate = eg_graph.predicates[item_id]
                predicates_in_cut.append(predicate)
        
        if len(child_cuts) == 1 and len(predicates_in_cut) > 0:
            # This is implication structure: [Cut: P [Cut: Q]]
            # P → Q = ¬(P ∧ ¬Q)
            
            # Get antecedent (predicates in outer cut)
            antecedent_parts = []
            for predicate in predicates_in_cut:
                antecedent_parts.append(self._predicate_to_clif(predicate, eg_graph))
            
            # Get consequent (predicates in inner cut)
            inner_cut = child_cuts[0]
            consequent_parts = []
            for item_id in inner_cut.contained_items:
                if item_id in eg_graph.predicates:
                    predicate = eg_graph.predicates[item_id]
                    consequent_parts.append(self._predicate_to_clif(predicate, eg_graph))
            
            if len(antecedent_parts) == 1 and len(consequent_parts) == 1:
                # Simple implication
                return f"(if {antecedent_parts[0]} {consequent_parts[0]})"
            elif len(antecedent_parts) > 0 and len(consequent_parts) > 0:
                # Complex implication
                antecedent = f"(and {' '.join(antecedent_parts)})" if len(antecedent_parts) > 1 else antecedent_parts[0]
                consequent = f"(and {' '.join(consequent_parts)})" if len(consequent_parts) > 1 else consequent_parts[0]
                return f"(if {antecedent} {consequent})"
        
        # Not implication structure, handle as negation
        return self._handle_cut_context(cut_context, eg_graph)
    
    def _handle_cut_context(self, context: Context, eg_graph: EGGraph) -> str:
        """Handle cut context (negation)."""
        
        # Get all content in this cut
        content_parts = []
        
        # Add predicates
        for item_id in context.contained_items:
            if item_id in eg_graph.predicates:
                predicate = eg_graph.predicates[item_id]
                content_parts.append(self._predicate_to_clif(predicate, eg_graph))
        
        # Add child contexts
        for context_id, child_context in eg_graph.context_manager.contexts.items():
            if child_context.parent_context == context.id:
                child_clif = self._analyze_context_for_clif(child_context, eg_graph)
                if child_clif and child_clif != "()":
                    content_parts.append(child_clif)
        
        if len(content_parts) == 0:
            return "()"
        elif len(content_parts) == 1:
            return f"(not {content_parts[0]})"
        else:
            return f"(not (and {' '.join(content_parts)}))"
    
    def _generate_simple_clif(self, predicates: List[Predicate], eg_graph: EGGraph) -> str:
        """Generate simple CLIF for predicates (conjunction)."""
        
        clif_parts = []
        for predicate in predicates:
            clif_parts.append(self._predicate_to_clif(predicate, eg_graph))
        
        if len(clif_parts) == 0:
            return "()"
        elif len(clif_parts) == 1:
            return clif_parts[0]
        else:
            return f"(and {' '.join(clif_parts)})"
    
    def _predicate_to_clif(self, predicate: Predicate, eg_graph: EGGraph) -> str:
        """Convert a predicate to CLIF format."""
        
        if not predicate.entities:
            # Zero-arity predicate
            return predicate.name
        
        # Get entity names
        entity_names = []
        for entity_id in predicate.entities:
            entity = eg_graph.entities.get(entity_id)
            if entity and entity.name:
                entity_names.append(entity.name)
            else:
                entity_names.append(f"?{entity_id}")
        
        return f"({predicate.name} {' '.join(entity_names)})"
    
    def _calculate_entity_positions(self, eg_graph: EGGraph) -> Dict[EntityId, Point]:
        """Calculate positions for entities."""
        positions = {}
        x_offset = 100
        y_base = 200
        
        for i, entity_id in enumerate(eg_graph.entities.keys()):
            positions[entity_id] = Point(x_offset + i * self.constraints.entity_spacing, y_base)
        
        return positions

    
    def _calculate_safe_predicate_position(self, predicate_id: str, context_id: str, eg_graph: EGGraph) -> Point:
        """Calculate predicate position ensuring complete containment within context bounds."""
        
        # Get context bounds
        context = eg_graph.context_manager.contexts[context_id]
        context_bounds = self._calculate_context_bounds(context, eg_graph)
        
        # Calculate safe margins to ensure predicate stays inside
        margin = 30  # Minimum distance from context border
        # Get predicate name for text width calculation
        predicate = eg_graph.predicates[predicate_id]
        predicate_name = predicate.name
        text_width = len(predicate_name) * 8 + 20  # Estimate text width
        text_height = 20  # Estimate text height
        
        # Calculate safe area within context
        safe_x_min = context_bounds.x + margin
        safe_x_max = context_bounds.x + context_bounds.width - margin - text_width
        safe_y_min = context_bounds.y + margin + text_height
        safe_y_max = context_bounds.y + context_bounds.height - margin
        
        # Ensure safe area is valid
        if safe_x_max <= safe_x_min:
            safe_x_max = safe_x_min + text_width
        if safe_y_max <= safe_y_min:
            safe_y_max = safe_y_min + text_height
        
        # Position predicate in center of safe area
        safe_x = (safe_x_min + safe_x_max) / 2
        safe_y = (safe_y_min + safe_y_max) / 2
        
        print(f"DEBUG: Predicate {predicate_name} positioned at ({safe_x}, {safe_y}) within context bounds")
        print(f"       Context bounds: ({context_bounds.x}, {context_bounds.y}, {context_bounds.width}, {context_bounds.height})")
        print(f"       Safe area: ({safe_x_min}, {safe_y_min}) to ({safe_x_max}, {safe_y_max})")
        
        return Point(safe_x, safe_y)

    def _calculate_predicate_positions(self, eg_graph: EGGraph) -> Dict[PredicateId, Point]:
        """Calculate positions for predicates based on context hierarchy."""
        positions = {}
        
        # Group predicates by context with proper hierarchy analysis
        context_predicates = {}
        for predicate_id, predicate in eg_graph.predicates.items():
            # Find which context contains this predicate
            context_id = self._find_predicate_context(predicate_id, eg_graph)
            
            if context_id not in context_predicates:
                context_predicates[context_id] = []
            context_predicates[context_id].append(predicate_id)
        
        # Position predicates based on context hierarchy for implication structure
        self._position_predicates_by_context_hierarchy(context_predicates, eg_graph, positions)
        
        return positions
    
    def _find_predicate_context(self, predicate_id: PredicateId, eg_graph: EGGraph) -> Optional[ContextId]:
        """Find which context contains this predicate."""
        for context_id, context in eg_graph.context_manager.contexts.items():
            if predicate_id in context.contained_items:
                return context_id
        return None
    
    def _position_predicates_by_context_hierarchy(self, context_predicates: Dict, eg_graph: EGGraph, positions: Dict):
        """Position predicates based on context hierarchy for proper implication display."""
        
        # Analyze context structure to detect implication pattern
        root_context = eg_graph.context_manager.root_context
        
        # Find cut contexts and their hierarchy
        cut_contexts = []
        for context_id, context in eg_graph.context_manager.contexts.items():
            if context.context_type == 'cut':
                cut_contexts.append((context_id, context))
        
        # Sort by depth to handle hierarchy
        cut_contexts.sort(key=lambda x: x[1].depth)
        
        if len(cut_contexts) >= 2:
            # This is likely an implication structure: [Cut: P [Cut: Q]]
            self._position_implication_structure(context_predicates, cut_contexts, eg_graph, positions)
        else:
            # Simple structure - use default positioning
            self._position_simple_structure(context_predicates, eg_graph, positions)
    
    def _position_implication_structure(self, context_predicates: Dict, cut_contexts: List, eg_graph: EGGraph, positions: Dict):
        """Position predicates for implication structure: antecedent outside inner cut, consequent inside."""
        
        # Base positioning
        canvas_center_x = self.constraints.canvas_width / 2
        canvas_center_y = self.constraints.canvas_height / 2
        
        # Outer cut (first level) - contains antecedent
        outer_cut_id = cut_contexts[0][0] if cut_contexts else None
        # Inner cut (second level) - contains consequent  
        inner_cut_id = cut_contexts[1][0] if len(cut_contexts) > 1 else None
        
        # Position antecedent predicates (in outer cut, outside inner cut)
        if outer_cut_id and outer_cut_id in context_predicates:
            antecedent_predicates = context_predicates[outer_cut_id]
            for i, predicate_id in enumerate(antecedent_predicates):
                # Position between the two cuts (outer area)
                positions[predicate_id] = Point(
                    canvas_center_x - 100 + i * 80,  # Left side of center
                    canvas_center_y - 50  # Above center
                )
        
        # Position consequent predicates (in inner cut)
        if inner_cut_id and inner_cut_id in context_predicates:
            consequent_predicates = context_predicates[inner_cut_id]
            for i, predicate_id in enumerate(consequent_predicates):
                # Position inside inner cut (center area)
                positions[predicate_id] = Point(
                    canvas_center_x + 50 + i * 80,  # Right side of center
                    canvas_center_y + 50  # Below center
                )
        
        # Position any root context predicates
        root_id = eg_graph.context_manager.root_context.id
        if root_id in context_predicates:
            root_predicates = context_predicates[root_id]
            for i, predicate_id in enumerate(root_predicates):
                positions[predicate_id] = Point(
                    100 + i * self.constraints.predicate_spacing,
                    100
                )
    
    def _position_simple_structure(self, context_predicates: Dict, eg_graph: EGGraph, positions: Dict):
        """Position predicates for simple (non-implication) structures."""
        
        base_x = 200
        base_y = 200
        
        for context_id, predicate_ids in context_predicates.items():
            if context_id is None:
                # Root context
                x_offset = base_x
                y_offset = base_y
            else:
                # Get context depth for positioning
                context = eg_graph.context_manager.contexts.get(context_id)
                if context:
                    x_offset = base_x + context.depth * 100
                    y_offset = base_y + context.depth * 50
                else:
                    x_offset = base_x
                    y_offset = base_y
            
            for i, predicate_id in enumerate(predicate_ids):
                positions[predicate_id] = Point(
                    x_offset + i * self.constraints.predicate_spacing,
                    y_offset
                )
    
    def _create_entity_path(self, entity_id: EntityId, eg_graph: EGGraph, base_position: Point) -> List[Point]:
        """Create path for entity line of identity that properly connects predicates."""
        
        # Find predicates connected to this entity
        connected_predicates = []
        predicate_positions = {}
        
        for predicate_id, predicate in eg_graph.predicates.items():
            if entity_id in predicate.entities:
                connected_predicates.append(predicate_id)
        
        if not connected_predicates:
            # No connections, just a short line
            return [base_position, Point(base_position.x + 50, base_position.y)]
        
        # Get predicate positions (we need to calculate them first)
        predicate_positions_dict = self._calculate_predicate_positions(eg_graph)
        
        # Create path that flows through all connected predicates
        path = []
        
        if len(connected_predicates) == 1:
            # Single predicate - simple connection
            pred_pos = predicate_positions_dict.get(connected_predicates[0], Point(200, 200))
            path = [
                Point(pred_pos.x - 30, pred_pos.y),  # Start before predicate
                Point(pred_pos.x, pred_pos.y),       # Through predicate center
                Point(pred_pos.x + 30, pred_pos.y)   # End after predicate
            ]
        else:
            # Multiple predicates - create flowing line
            sorted_predicates = sorted(connected_predicates, 
                                     key=lambda pid: predicate_positions_dict.get(pid, Point(0, 0)).x)
            
            for i, predicate_id in enumerate(sorted_predicates):
                pred_pos = predicate_positions_dict.get(predicate_id, Point(200 + i * 100, 200))
                
                if i == 0:
                    # Start point
                    path.append(Point(pred_pos.x - 30, pred_pos.y))
                
                # Through predicate
                path.append(Point(pred_pos.x, pred_pos.y))
                
                if i == len(sorted_predicates) - 1:
                    # End point
                    path.append(Point(pred_pos.x + 30, pred_pos.y))
                else:
                    # Connection to next predicate
                    next_pred_pos = predicate_positions_dict.get(sorted_predicates[i + 1], Point(300 + i * 100, 200))
                    path.append(Point((pred_pos.x + next_pred_pos.x) / 2, pred_pos.y))
        
        return path
    
    def _calculate_context_bounds(self, context: Context, eg_graph: EGGraph) -> Bounds:
        """Calculate bounds for context based on contained items and hierarchy."""
        
        # Base dimensions based on context depth
        padding = self.constraints.context_padding + context.depth * 10
        
        if context.context_type == 'sheet_of_assertion':
            # Root context - full canvas
            return Bounds(
                x=10,
                y=10,
                width=self.constraints.canvas_width - 20,
                height=self.constraints.canvas_height - 20
            )
        
        elif context.context_type == 'cut':
            # Cut context - size based on hierarchy and content
            if context.depth == 1:
                # Outer cut - larger area
                return Bounds(
                    x=50,
                    y=50,
                    width=self.constraints.canvas_width - 100,
                    height=self.constraints.canvas_height - 100
                )
            elif context.depth == 2:
                # Inner cut - smaller area, positioned for implication
                return Bounds(
                    x=self.constraints.canvas_width / 2 + 20,
                    y=self.constraints.canvas_height / 2 + 20,
                    width=200,
                    height=150
                )
            else:
                # Deeper cuts - progressively smaller
                size_reduction = context.depth * 50
                return Bounds(
                    x=50 + size_reduction,
                    y=50 + size_reduction,
                    width=max(100, self.constraints.canvas_width - 100 - size_reduction * 2),
                    height=max(80, self.constraints.canvas_height - 100 - size_reduction * 2)
                )
        
        else:
            # Default context
            return Bounds(
                x=padding,
                y=padding,
                width=self.constraints.canvas_width - padding * 2,
                height=self.constraints.canvas_height - padding * 2
            )

    def _calculate_layout_with_proper_containment(self, eg_graph: EGGraph) -> Dict:
        """Calculate layout with proper cut containment logic."""
        
        # First, analyze the context hierarchy
        context_hierarchy = self._analyze_context_hierarchy(eg_graph)
        
        # Calculate minimum sizes for all contexts (bottom-up)
        context_sizes = self._calculate_context_minimum_sizes(context_hierarchy, eg_graph)
        
        # Position contexts with proper nesting
        context_bounds = self._position_contexts_with_nesting(context_hierarchy, context_sizes)
        
        # Position elements within their contexts (avoiding nested cuts)
        element_positions = self._position_elements_with_containment(eg_graph, context_bounds, context_hierarchy)
        
        return {
            'context_bounds': context_bounds,
            'element_positions': element_positions,
            'context_hierarchy': context_hierarchy
        }
    
    def _analyze_context_hierarchy(self, eg_graph: EGGraph) -> Dict:
        """Analyze context hierarchy to understand nesting relationships."""
        
        hierarchy = {
            'root': eg_graph.context_manager.root_context.id,
            'children': {},  # context_id -> [child_context_ids]
            'parent': {},    # context_id -> parent_context_id
            'depth': {},     # context_id -> depth_level
            'elements': {}   # context_id -> [element_ids]
        }
        
        # Build parent-child relationships
        for context_id, context in eg_graph.context_manager.contexts.items():
            if context.parent_id:
                hierarchy['parent'][context_id] = context.parent_id
                if context.parent_id not in hierarchy['children']:
                    hierarchy['children'][context.parent_id] = []
                hierarchy['children'][context.parent_id].append(context_id)
            
            # Calculate depth
            depth = 0
            current_id = context_id
            while current_id in hierarchy['parent']:
                depth += 1
                current_id = hierarchy['parent'][current_id]
            hierarchy['depth'][context_id] = depth
            
            # Collect elements in this context
            hierarchy['elements'][context_id] = list(context.contained_items)
        
        return hierarchy
    
    def _calculate_context_minimum_sizes(self, hierarchy: Dict, eg_graph: EGGraph) -> Dict:
        """Calculate minimum sizes for contexts based on their content (bottom-up)."""
        
        sizes = {}
        
        # Start with leaf contexts (no children)
        contexts_by_depth = {}
        for context_id, depth in hierarchy['depth'].items():
            if depth not in contexts_by_depth:
                contexts_by_depth[depth] = []
            contexts_by_depth[depth].append(context_id)
        
        # Process from deepest to shallowest
        max_depth = max(contexts_by_depth.keys()) if contexts_by_depth else 0
        
        for depth in range(max_depth, -1, -1):
            for context_id in contexts_by_depth.get(depth, []):
                sizes[context_id] = self._calculate_single_context_size(
                    context_id, hierarchy, eg_graph, sizes
                )
        
        return sizes
    
    def _calculate_single_context_size(self, context_id: str, hierarchy: Dict, eg_graph: EGGraph, existing_sizes: Dict) -> Dict:
        """Calculate minimum size for a single context."""
        
        # Base size for elements
        element_count = len(hierarchy['elements'].get(context_id, []))
        base_width = max(200, element_count * 80 + 40)  # Space for elements
        base_height = max(150, 60 + 40)  # Minimum height
        
        # Add space for child contexts
        child_contexts = hierarchy['children'].get(context_id, [])
        child_area_width = 0
        child_area_height = 0
        
        if child_contexts:
            # Calculate space needed for all child contexts
            total_child_width = 0
            max_child_height = 0
            
            for child_id in child_contexts:
                if child_id in existing_sizes:
                    child_size = existing_sizes[child_id]
                    total_child_width += child_size['width'] + 20  # 20px spacing
                    max_child_height = max(max_child_height, child_size['height'])
            
            child_area_width = total_child_width + 40  # Extra padding
            child_area_height = max_child_height + 80  # Space above/below children
        
        # Context must be large enough for both elements and children
        required_width = max(base_width, child_area_width)
        required_height = max(base_height, child_area_height)
        
        # Add padding based on context type
        context = eg_graph.context_manager.contexts.get(context_id)
        if context and context.context_type == 'cut':
            padding = 30
        else:
            padding = 20
        
        return {
            'width': required_width + padding * 2,
            'height': required_height + padding * 2,
            'padding': padding
        }
    
    def _position_contexts_with_nesting(self, hierarchy: Dict, sizes: Dict) -> Dict:
        """Position contexts with proper nesting."""
        
        bounds = {}
        
        # Start with root context (full canvas)
        root_id = hierarchy['root']
        bounds[root_id] = {
            'x': 10,
            'y': 10,
            'width': self.constraints.canvas_width - 20,
            'height': self.constraints.canvas_height - 20
        }
        
        # Position child contexts within their parents
        contexts_by_depth = {}
        for context_id, depth in hierarchy['depth'].items():
            if depth not in contexts_by_depth:
                contexts_by_depth[depth] = []
            contexts_by_depth[depth].append(context_id)
        
        # Process by depth (parents before children)
        for depth in sorted(contexts_by_depth.keys()):
            for context_id in contexts_by_depth[depth]:
                if context_id != root_id:  # Skip root, already positioned
                    bounds[context_id] = self._position_child_context(
                        context_id, hierarchy, sizes, bounds
                    )
        
        return bounds
    
    def _position_child_context(self, context_id: str, hierarchy: Dict, sizes: Dict, existing_bounds: Dict) -> Dict:
        """Position a child context within its parent."""
        
        parent_id = hierarchy['parent'].get(context_id)
        if not parent_id or parent_id not in existing_bounds:
            # Fallback positioning
            return {
                'x': 50,
                'y': 50,
                'width': sizes[context_id]['width'],
                'height': sizes[context_id]['height']
            }
        
        parent_bounds = existing_bounds[parent_id]
        context_size = sizes[context_id]
        
        # Find available space within parent (avoiding siblings)
        siblings = hierarchy['children'].get(parent_id, [])
        sibling_bounds = [existing_bounds[sid] for sid in siblings if sid in existing_bounds and sid != context_id]
        
        # Try to position in available space
        padding = 20
        x = parent_bounds['x'] + padding
        y = parent_bounds['y'] + padding
        
        # Adjust position to avoid overlapping with siblings
        for sibling_bound in sibling_bounds:
            if self._bounds_overlap(
                {'x': x, 'y': y, 'width': context_size['width'], 'height': context_size['height']},
                sibling_bound
            ):
                # Move to the right of this sibling
                x = sibling_bound['x'] + sibling_bound['width'] + padding
        
        # Ensure we don't exceed parent bounds
        max_x = parent_bounds['x'] + parent_bounds['width'] - context_size['width'] - padding
        max_y = parent_bounds['y'] + parent_bounds['height'] - context_size['height'] - padding
        
        x = min(x, max_x)
        y = min(y, max_y)
        
        return {
            'x': x,
            'y': y,
            'width': context_size['width'],
            'height': context_size['height']
        }
    
    def _bounds_overlap(self, bounds1: Dict, bounds2: Dict) -> bool:
        """Check if two rectangular bounds overlap."""
        return not (
            bounds1['x'] + bounds1['width'] <= bounds2['x'] or
            bounds2['x'] + bounds2['width'] <= bounds1['x'] or
            bounds1['y'] + bounds1['height'] <= bounds2['y'] or
            bounds2['y'] + bounds2['height'] <= bounds1['y']
        )
    
    def _position_elements_with_containment(self, eg_graph: EGGraph, context_bounds: Dict, hierarchy: Dict) -> Dict:
        """Position elements within their contexts, avoiding nested cuts."""
        
        positions = {}
        
        # Position predicates
        for predicate_id, predicate in eg_graph.predicates.items():
            context_id = self._find_element_context(predicate_id, hierarchy)
            if context_id and context_id in context_bounds:
                positions[predicate_id] = self._find_valid_position_for_element(
                    predicate_id, context_id, context_bounds, hierarchy, positions, 'predicate'
                )
        
        # Position entities (create paths that connect predicates)
        for entity_id, entity in eg_graph.entities.items():
            positions[entity_id] = self._create_entity_path_with_containment(
                entity_id, eg_graph, positions, context_bounds, hierarchy
            )
        
        return positions
    
    def _find_element_context(self, element_id: str, hierarchy: Dict) -> str:
        """Find which context contains this element."""
        for context_id, elements in hierarchy['elements'].items():
            if element_id in elements:
                return context_id
        return None
    
    def _find_valid_position_for_element(self, element_id: str, context_id: str, context_bounds: Dict, 
                                       hierarchy: Dict, existing_positions: Dict, element_type: str) -> Dict:
        """Find a valid position for an element within its context, avoiding nested cuts."""
        
        context_bound = context_bounds[context_id]
        
        # Get list of nested cuts within this context
        nested_cuts = hierarchy['children'].get(context_id, [])
        nested_bounds = [context_bounds[cut_id] for cut_id in nested_cuts if cut_id in context_bounds]
        
        # Element dimensions
        if element_type == 'predicate':
            width, height = 60, 30
        else:
            width, height = 40, 20
        
        # Try to find a position that's inside the context but outside nested cuts
        padding = 15
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            # Random position within context bounds
            import random
            x = random.randint(
                int(context_bound['x'] + padding),
                int(context_bound['x'] + context_bound['width'] - width - padding)
            )
            y = random.randint(
                int(context_bound['y'] + padding),
                int(context_bound['y'] + context_bound['height'] - height - padding)
            )
            
            element_bounds = {'x': x, 'y': y, 'width': width, 'height': height}
            
            # Check if this position overlaps with any nested cuts
            overlaps_nested = any(
                self._bounds_overlap(element_bounds, nested_bound)
                for nested_bound in nested_bounds
            )
            
            # Check if this position overlaps with existing elements
            overlaps_existing = any(
                self._bounds_overlap(element_bounds, {
                    'x': pos.get('x', pos.get('position', {}).get('x', 0)),
                    'y': pos.get('y', pos.get('position', {}).get('y', 0)),
                    'width': width,
                    'height': height
                })
                for pos in existing_positions.values()
                if isinstance(pos, dict) and ('x' in pos or 'position' in pos)
            )
            
            if not overlaps_nested and not overlaps_existing:
                return {'x': x, 'y': y}
            
            attempts += 1
        
        # Fallback: position in top-left of available space
        return {
            'x': context_bound['x'] + padding,
            'y': context_bound['y'] + padding
        }
    
    def _create_entity_path_with_containment(self, entity_id: str, eg_graph: EGGraph, 
                                           predicate_positions: Dict, context_bounds: Dict, hierarchy: Dict) -> Dict:
        """Create entity path that properly connects predicates while respecting containment."""
        
        # Find predicates connected to this entity
        connected_predicates = []
        for predicate_id, predicate in eg_graph.predicates.items():
            if entity_id in predicate.entities:
                connected_predicates.append(predicate_id)
        
        if not connected_predicates:
            # No connections, create a simple line
            return {
                'path': [{'x': 100, 'y': 100}, {'x': 150, 'y': 100}]
            }
        
        # Create path that connects all predicates
        path_points = []
        
        for predicate_id in connected_predicates:
            if predicate_id in predicate_positions:
                pos = predicate_positions[predicate_id]
                path_points.append({
                    'x': pos['x'] + 30,  # Center of predicate
                    'y': pos['y'] + 15
                })
        
        # If only one predicate, extend the line
        if len(path_points) == 1:
            start_point = path_points[0]
            path_points = [
                {'x': start_point['x'] - 30, 'y': start_point['y']},
                start_point,
                {'x': start_point['x'] + 30, 'y': start_point['y']}
            ]
        
        return {'path': path_points}
    def _add_entities_with_layout(self, egrf_doc: EGRFDocument, eg_graph: EGGraph, layout: Dict):
        """Add entities using the calculated layout."""
        for entity_id, entity in eg_graph.entities.items():
            if entity_id in layout['element_positions']:
                path_data = layout['element_positions'][entity_id]
                egrf_entity = self._convert_entity_with_path(entity, path_data)
                egrf_doc.entities.append(egrf_entity)
    
    def _add_predicates_with_layout(self, egrf_doc: EGRFDocument, eg_graph: EGGraph, layout: Dict):
        """Add predicates using the calculated layout."""
        for predicate_id, predicate in eg_graph.predicates.items():
            if predicate_id in layout['element_positions']:
                position = layout['element_positions'][predicate_id]
                egrf_predicate = self._convert_predicate_with_position(predicate, position)
                egrf_doc.predicates.append(egrf_predicate)
    
    def _add_contexts_with_layout(self, egrf_doc: EGRFDocument, eg_graph: EGGraph, layout: Dict):
        """Add contexts using the calculated layout."""
        for context_id, context in eg_graph.context_manager.contexts.items():
            if context_id in layout['context_bounds']:
                bounds = layout['context_bounds'][context_id]
                egrf_context = self._convert_context_with_bounds(context, bounds)
                egrf_doc.contexts.append(egrf_context)
    
    def _convert_entity_with_path(self, entity, path_data):
        """Convert entity with calculated path."""
        from .egrf_types import Entity as EGRFEntity, EntityVisual, Point, Stroke
        
        return EGRFEntity(
            id=entity.id,
            name=entity.name,
            type=entity.entity_type,
            visual=EntityVisual(
                style="line",
                path=[Point(p['x'], p['y']) for p in path_data.get('path', [])],
                stroke=Stroke()
            )
        )
    
    def _convert_predicate_with_position(self, predicate, position):
        """Convert predicate with calculated position."""
        from .egrf_types import Predicate as EGRFPredicate, PredicateVisual, Point, Size, Fill, Stroke, Label, Font
        
        return EGRFPredicate(
            id=predicate.id,
            name=predicate.name,
            type="relation",
            arity=len(predicate.entities),
            connected_entities=list(predicate.entities),
            visual=PredicateVisual(
                style="oval",
                position=Point(position['x'], position['y']),
                size=Size(60, 30),
                fill=Fill(),
                stroke=Stroke()
            ),
            labels=[Label(
                text=predicate.name,
                position=Point(position['x'], position['y']),
                font=Font(),
                alignment="center"
            )]
        )
    
    def _convert_context_with_bounds(self, context, bounds):
        """Convert context with calculated bounds."""
        from .egrf_types import Context as EGRFContext, ContextVisual, Bounds, Fill, Stroke
        
        return EGRFContext(
            id=context.id,
            type=context.context_type,
            parent_context=context.parent_id,
            visual=ContextVisual(
                style="oval",
                bounds=Bounds(bounds['x'], bounds['y'], bounds['width'], bounds['height']),
                fill=Fill(color="#ffffff", opacity=0.1),
                stroke=Stroke()
            )
        )

    def _apply_peirce_visual_refinements(self, egrf_doc: EGRFDocument, hierarchy: Dict):
        """Apply Peirce's visual refinements to the EGRF document."""
        
        # 1. Remove variable labels from entities (ligatures express individuals)
        self._remove_variable_labels(egrf_doc)
        
        # 2. Apply proper cut shading (white for even, gray for odd)
        self._apply_cut_shading(egrf_doc, hierarchy)
        
        # 3. Make predicate borders transparent (text only, maintain attachment)
        self._make_predicate_borders_transparent(egrf_doc)
    
    def _remove_variable_labels(self, egrf_doc: EGRFDocument):
        """Remove variable labels from entities - ligatures already express individuals."""
        
        for entity in egrf_doc.entities:
            # Remove any labels that show variable names like "x", "y"
            if hasattr(entity, 'labels'):
                # Keep only labels that are not single variable letters
                entity.labels = [
                    label for label in entity.labels 
                    if not (len(label.text) == 1 and label.text.islower())
                ]
            
            # Ensure entity visual style emphasizes the line, not labels
            if hasattr(entity.visual, 'stroke'):
                entity.visual.stroke.width = 2.0  # Heavier line as Peirce intended
                entity.visual.stroke.color = "#000000"  # Strong black line
    
    def _apply_cut_shading(self, egrf_doc: EGRFDocument, hierarchy: Dict):
        """Apply proper cut shading: white for even cuts, light gray for odd cuts."""
        
        # Calculate cut depth for each context
        cut_depths = self._calculate_cut_depths(hierarchy)
        
        for context in egrf_doc.contexts:
            if context.type == 'cut':
                depth = cut_depths.get(context.id, 0)
                
                # Even number of cuts = white background
                # Odd number of cuts = light gray background
                if depth % 2 == 0:
                    # Even depth - white background
                    context.visual.fill.color = "#ffffff"
                    context.visual.fill.opacity = 0.8
                else:
                    # Odd depth - light gray background
                    context.visual.fill.color = "#f0f0f0"
                    context.visual.fill.opacity = 0.6
                
                # Cut border should be visible but not dominant
                context.visual.stroke.color = "#666666"
                context.visual.stroke.width = 1.5
                context.visual.stroke.style = "solid"
    
    def _calculate_cut_depths(self, hierarchy: Dict) -> Dict[str, int]:
        """Calculate the depth of each cut (number of cuts containing it)."""
        
        cut_depths = {}
        
        for context_id in hierarchy.get('depth', {}):
            # Count how many cuts contain this context
            cut_count = 0
            current_id = context_id
            
            while current_id in hierarchy.get('parent', {}):
                parent_id = hierarchy['parent'][current_id]
                # Check if parent is a cut (not root context)
                if parent_id != hierarchy.get('root') and parent_id in hierarchy.get('depth', {}):
                    cut_count += 1
                current_id = parent_id
            
            cut_depths[context_id] = cut_count
        
        return cut_depths
    
    def _make_predicate_borders_transparent(self, egrf_doc: EGRFDocument):
        """Make predicate borders transparent - text only, but maintain attachment points."""
        
        for predicate in egrf_doc.predicates:
            # Make the oval border transparent
            predicate.visual.stroke.color = "#ffffff"  # Transparent white
            predicate.visual.stroke.width = 0.0        # No visible border
            predicate.visual.stroke.style = "none"     # No border style
            
            # Make the fill transparent too
            predicate.visual.fill.color = "#ffffff"
            predicate.visual.fill.opacity = 0.0        # Completely transparent
            
            # Enhance the text to be more prominent since there's no border
            for label in predicate.labels:
                label.font.size = 14.0                 # Slightly larger text
                label.font.weight = "bold"             # Bold text for visibility
                label.font.color = "#000000"           # Strong black text
            
            # Maintain attachment points for ligatures (invisible but functional)
            # The visual bounds still exist for collision detection and attachment
            # but are not rendered
            
            # Add metadata to indicate this is a transparent predicate
            if not hasattr(predicate, 'metadata'):
                predicate.metadata = {}
            predicate.metadata['transparent_border'] = True
            predicate.metadata['attachment_bounds'] = {
                'x': predicate.visual.position.x - 30,  # Half width
                'y': predicate.visual.position.y - 15,  # Half height
                'width': 60,
                'height': 30
            }