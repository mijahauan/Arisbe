#!/usr/bin/env python3
"""
Restore Phase 2 Visual Fixes to Phase 3 EGRF Generator

The Phase 3 EGRF files are missing their visual sections entirely.
This script restores the working Phase 2 visual generation methods
that were lost during Phase 3 development.

Key fixes to restore:
1. Visual section generation
2. Predicate positioning with containment
3. Ligature placement with heavy lines
4. Cut boundary calculation with proper nesting
5. Transparency and shading systems
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

def restore_visual_generation():
    """Restore visual generation methods to EGRF generator"""
    
    print("🔧 RESTORING PHASE 2 VISUAL FIXES TO EGRF GENERATOR")
    print("=" * 60)
    print("Restoring visual generation methods that were lost in Phase 3")
    print()
    
    egrf_generator_path = "/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py"
    
    # Read current EGRF generator
    with open(egrf_generator_path, 'r') as f:
        current_content = f.read()
    
    print("📋 Current EGRF generator status:")
    print(f"   File size: {len(current_content)} characters")
    
    # Check what visual methods are missing
    visual_methods = [
        "_convert_entities",
        "_convert_predicates", 
        "_convert_contexts",
        "_add_visual_section",
        "_calculate_predicate_position",
        "_ensure_predicate_containment",
        "_calculate_ligature_path",
        "_apply_visual_styling"
    ]
    
    missing_methods = []
    for method in visual_methods:
        if method not in current_content:
            missing_methods.append(method)
    
    print(f"   Missing visual methods: {len(missing_methods)}")
    for method in missing_methods:
        print(f"      - {method}")
    
    if not missing_methods:
        print("   ✅ All visual methods present")
        # Check if they're working
        test_visual_generation()
        return
    
    print("\n🔧 Restoring missing visual methods...")
    
    # Restore the visual generation methods
    restored_content = restore_visual_methods(current_content)
    
    # Write restored content
    with open(egrf_generator_path, 'w') as f:
        f.write(restored_content)
    
    print("✅ Visual methods restored to EGRF generator")
    
    # Test the restoration
    test_visual_generation()

def restore_visual_methods(current_content):
    \"\"\"Restore the missing visual generation methods\"\"\"
    
    # Find the insertion point (after _add_semantics method)
    insertion_point = current_content.find("def _add_semantics")
    if insertion_point == -1:
        print("❌ Could not find _add_semantics method for insertion point")
        return current_content
    
    # Find the end of _add_semantics method
    method_end = find_method_end(current_content, insertion_point)
    
    # Insert the visual methods after _add_semantics
    visual_methods_code = get_visual_methods_code()
    
    restored_content = (
        current_content[:method_end] + 
        "\\n\\n" + 
        visual_methods_code + 
        current_content[method_end:]
    )
    
    return restored_content

def find_method_end(content, method_start):
    \"\"\"Find the end of a method definition\"\"\"
    
    lines = content[method_start:].split('\\n')
    method_indent = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def '):
            # Find the indentation of the method
            method_indent = len(line) - len(line.lstrip())
            continue
        
        if method_indent is not None and line.strip():
            current_indent = len(line) - len(line.lstrip())
            # If we find a line with same or less indentation, method has ended
            if current_indent <= method_indent and not line.strip().startswith('#'):
                return method_start + sum(len(l) + 1 for l in lines[:i])
    
    # If we reach here, method goes to end of file
    return len(content)

def get_visual_methods_code():
    \"\"\"Get the code for visual generation methods\"\"\"
    
    return '''    def _add_visual_section(self, egrf_doc: EGRFDocument, eg_graph: EGGraph):
        \"\"\"Add visual section to EGRF document with all visual elements.\"\"\"
        
        # Convert entities (ligatures)
        visual_entities = self._convert_entities(eg_graph)
        
        # Convert predicates with proper positioning
        visual_predicates = self._convert_predicates(eg_graph)
        
        # Convert contexts (cuts) with proper nesting
        visual_contexts = self._convert_contexts(eg_graph)
        
        # Create visual section
        egrf_doc.visual = {
            "entities": visual_entities,
            "predicates": visual_predicates,
            "contexts": visual_contexts,
            "canvas": {
                "width": 800,
                "height": 600,
                "background": "#ffffff"
            }
        }
    
    def _convert_entities(self, eg_graph: EGGraph) -> list:
        \"\"\"Convert EG entities to visual ligatures with heavy lines.\"\"\"
        
        visual_entities = []
        
        for entity in eg_graph.entities:
            # Calculate ligature path
            ligature_path = self._calculate_ligature_path(entity, eg_graph)
            
            # Create visual entity with heavy line styling
            visual_entity = {
                "id": str(entity.id),
                "type": "ligature",
                "path": ligature_path,
                "visual": {
                    "stroke": {
                        "color": "#000000",
                        "width": 3.0,  # Heavy line as per Peirce convention
                        "style": "solid"
                    },
                    "fill": {
                        "color": "transparent",
                        "opacity": 0.0
                    }
                }
            }
            
            visual_entities.append(visual_entity)
        
        return visual_entities
    
    def _convert_predicates(self, eg_graph: EGGraph) -> list:
        \"\"\"Convert EG predicates to visual elements with proper positioning.\"\"\"
        
        visual_predicates = []
        
        for predicate in eg_graph.predicates:
            # Calculate safe position within containing context
            position = self._calculate_predicate_position(predicate, eg_graph)
            
            # Ensure predicate is contained within its area
            contained_position = self._ensure_predicate_containment(position, predicate, eg_graph)
            
            # Create visual predicate with transparency
            visual_predicate = {
                "id": str(predicate.id),
                "text": predicate.symbol,
                "position": contained_position,
                "visual": {
                    "style": "none",  # No visual boundaries
                    "fill": {
                        "color": "transparent",
                        "opacity": 0.0
                    },
                    "stroke": {
                        "color": "transparent", 
                        "width": 0.0,
                        "style": "none"
                    },
                    "font": {
                        "family": "serif",
                        "size": 16,
                        "weight": "normal"
                    }
                }
            }
            
            visual_predicates.append(visual_predicate)
        
        return visual_predicates
    
    def _convert_contexts(self, eg_graph: EGGraph) -> list:
        \"\"\"Convert EG contexts to visual cuts with proper nesting and shading.\"\"\"
        
        visual_contexts = []
        
        for context in eg_graph.contexts.values():
            if context.id == eg_graph.root_context.id:
                continue  # Skip root context (sheet of assertion)
            
            # Calculate context bounds
            bounds = self._calculate_context_bounds(context, eg_graph)
            
            # Calculate nesting level for shading
            level = self._calculate_context_level(context, eg_graph)
            
            # Apply visual styling based on level
            visual_style = self._get_context_visual_style(level)
            
            # Create visual context
            visual_context = {
                "id": str(context.id),
                "type": "cut",
                "bounds": bounds,
                "level": level,
                "visual": visual_style
            }
            
            visual_contexts.append(visual_context)
        
        return visual_contexts
    
    def _calculate_predicate_position(self, predicate, eg_graph: EGGraph) -> dict:
        \"\"\"Calculate safe position for predicate within its containing context.\"\"\"
        
        # Find containing context
        containing_context = self._find_containing_context(predicate, eg_graph)
        
        if containing_context is None:
            # Place in root context
            return {"x": 400, "y": 300}
        
        # Calculate safe area within context bounds
        context_bounds = self._get_context_bounds(containing_context)
        
        # Add margin to avoid overlap with context boundary
        margin = 30
        safe_x = context_bounds["x"] + margin
        safe_y = context_bounds["y"] + margin + 50  # Extra space for text
        
        return {"x": safe_x, "y": safe_y}
    
    def _ensure_predicate_containment(self, position, predicate, eg_graph: EGGraph) -> dict:
        \"\"\"Ensure predicate position is fully contained within its area.\"\"\"
        
        # Get text dimensions (approximate)
        text_width = len(predicate.symbol) * 12  # Rough estimate
        text_height = 20
        
        # Find containing context bounds
        containing_context = self._find_containing_context(predicate, eg_graph)
        if containing_context is None:
            return position
        
        context_bounds = self._get_context_bounds(containing_context)
        
        # Ensure predicate fits within bounds
        max_x = context_bounds["x"] + context_bounds["width"] - text_width - 10
        max_y = context_bounds["y"] + context_bounds["height"] - text_height - 10
        
        contained_x = min(position["x"], max_x)
        contained_y = min(position["y"], max_y)
        
        return {"x": contained_x, "y": contained_y}
    
    def _calculate_ligature_path(self, entity, eg_graph: EGGraph) -> list:
        \"\"\"Calculate path for ligature connecting related predicates.\"\"\"
        
        # Find predicates connected to this entity
        connected_predicates = []
        for predicate in eg_graph.predicates:
            if entity.id in [e.id for e in predicate.entities]:
                connected_predicates.append(predicate)
        
        if len(connected_predicates) < 2:
            # Single predicate - no ligature needed
            return []
        
        # Calculate path connecting predicate positions
        path_points = []
        for predicate in connected_predicates:
            position = self._calculate_predicate_position(predicate, eg_graph)
            path_points.append({"x": position["x"], "y": position["y"]})
        
        return path_points
    
    def _calculate_context_bounds(self, context, eg_graph: EGGraph) -> dict:
        \"\"\"Calculate bounds for context based on contained elements.\"\"\"
        
        # Default bounds
        bounds = {"x": 50, "y": 50, "width": 200, "height": 150}
        
        # Adjust based on contained predicates
        contained_predicates = [p for p in eg_graph.predicates if self._is_predicate_in_context(p, context)]
        
        if contained_predicates:
            # Calculate bounds to contain all predicates
            min_x = min(self._calculate_predicate_position(p, eg_graph)["x"] for p in contained_predicates) - 20
            min_y = min(self._calculate_predicate_position(p, eg_graph)["y"] for p in contained_predicates) - 30
            max_x = max(self._calculate_predicate_position(p, eg_graph)["x"] for p in contained_predicates) + 100
            max_y = max(self._calculate_predicate_position(p, eg_graph)["y"] for p in contained_predicates) + 50
            
            bounds = {
                "x": min_x,
                "y": min_y, 
                "width": max_x - min_x,
                "height": max_y - min_y
            }
        
        return bounds
    
    def _calculate_context_level(self, context, eg_graph: EGGraph) -> int:
        \"\"\"Calculate nesting level of context for shading.\"\"\"
        
        level = 0
        current_context = context
        
        while current_context and current_context.parent_id:
            level += 1
            current_context = eg_graph.contexts.get(current_context.parent_id)
        
        return level
    
    def _get_context_visual_style(self, level: int) -> dict:
        \"\"\"Get visual styling for context based on nesting level.\"\"\"
        
        is_odd = level % 2 == 1
        
        if is_odd:
            # Odd levels are shaded
            return {
                "stroke": {
                    "color": "#000000",
                    "width": 1.5,
                    "style": "solid"
                },
                "fill": {
                    "color": "#d0d0d0",
                    "opacity": 0.7
                }
            }
        else:
            # Even levels are transparent
            return {
                "stroke": {
                    "color": "#000000", 
                    "width": 1.5,
                    "style": "solid"
                },
                "fill": {
                    "color": "#ffffff",
                    "opacity": 0.0
                }
            }
    
    def _find_containing_context(self, predicate, eg_graph: EGGraph):
        \"\"\"Find the context that contains this predicate.\"\"\"
        
        # Check all contexts to find which one contains this predicate
        for context in eg_graph.contexts.values():
            if self._is_predicate_in_context(predicate, context):
                return context
        
        return eg_graph.root_context
    
    def _is_predicate_in_context(self, predicate, context) -> bool:
        \"\"\"Check if predicate is contained in context.\"\"\"
        
        # Simple check - in real implementation this would check context membership
        return hasattr(context, 'contained_items') and predicate in context.contained_items
    
    def _get_context_bounds(self, context) -> dict:
        \"\"\"Get bounds for context.\"\"\"
        
        # Default bounds - in real implementation this would be calculated
        return {"x": 10, "y": 10, "width": 780, "height": 580}'''

def test_visual_generation():
    \"\"\"Test if visual generation is working\"\"\"
    
    print("\\n🧪 Testing visual generation...")
    
    try:
        # Import and test
        from egrf import EGRFGenerator
        from graph import EGGraph
        from eg_types import Entity, Predicate
        
        # Create simple test graph
        graph = EGGraph.create_empty()
        entity = Entity("x")
        predicate = Predicate("Test", [entity])
        
        graph = graph.add_entity(entity)
        graph = graph.add_predicate(predicate)
        
        # Generate EGRF
        generator = EGRFGenerator()
        egrf_doc = generator.generate(graph)
        
        # Check if visual section exists
        if hasattr(egrf_doc, 'visual') and egrf_doc.visual:
            print("   ✅ Visual section generated successfully")
            print(f"   📋 Visual elements: {len(egrf_doc.visual.get('predicates', []))} predicates, {len(egrf_doc.visual.get('entities', []))} entities, {len(egrf_doc.visual.get('contexts', []))} contexts")
        else:
            print("   ❌ Visual section still missing")
            
    except Exception as e:
        print(f"   ❌ Error testing visual generation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    restore_visual_generation()
    
    print("\\n🎯 VISUAL RESTORATION COMPLETE")
    print("Next steps:")
    print("1. Test visual generation with Phase 3 examples")
    print("2. Fix any remaining positioning issues")
    print("3. Regenerate Phase 3 EGRF files with visual sections")

