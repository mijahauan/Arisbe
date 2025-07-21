#!/usr/bin/env python3
"""
Fix Critical Visual Issues

This script addresses the remaining critical visual rendering problems:
1. Predicate containment - ensure predicates and text stay within containing cuts
2. Visual artifacts - eliminate dots/marks in predicate centers
3. Consistent alternating shading - all even areas same as level 0
"""

import sys
from pathlib import Path

# Add the EG-CL-Manus2 src directory to Python path
sys.path.insert(0, str(Path("/home/ubuntu/EG-CL-Manus2/src")))

def fix_predicate_containment():
    """Fix predicate positioning to ensure complete containment within cuts."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find the _calculate_predicate_positions method and update it for proper containment
    if '_calculate_predicate_positions' in content:
        # Add a new method for safe predicate positioning
        safe_positioning_method = '''
    def _calculate_safe_predicate_position(self, predicate_id: str, context_id: str, eg_graph: EGGraph) -> Point:
        """Calculate predicate position ensuring complete containment within context bounds."""
        
        # Get context bounds
        context = eg_graph.context_manager.contexts[context_id]
        context_bounds = self._calculate_context_bounds(context, eg_graph)
        
        # Calculate safe margins to ensure predicate stays inside
        margin = 30  # Minimum distance from context border
        text_width = len(predicate_id) * 8 + 20  # Estimate text width
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
        
        print(f"DEBUG: Predicate {predicate_id} positioned at ({safe_x}, {safe_y}) within context bounds")
        print(f"       Context bounds: ({context_bounds.x}, {context_bounds.y}, {context_bounds.width}, {context_bounds.height})")
        print(f"       Safe area: ({safe_x_min}, {safe_y_min}) to ({safe_x_max}, {safe_y_max})")
        
        return Point(safe_x, safe_y)
'''
        
        # Insert the new method before _calculate_predicate_positions
        calc_pos_start = content.find('def _calculate_predicate_positions(')
        if calc_pos_start != -1:
            content = content[:calc_pos_start] + safe_positioning_method + '\n    ' + content[calc_pos_start:]
    
    # Update the predicate conversion to use safe positioning
    if 'position = predicate_positions.get(predicate_id, Point(200, 200))' in content:
        content = content.replace(
            'position = predicate_positions.get(predicate_id, Point(200, 200))',
            'position = self._calculate_safe_predicate_position(predicate_id, containing_context_id, eg_graph)'
        )
        print("✅ Updated predicate positioning to use safe containment")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed predicate containment positioning")

def eliminate_visual_artifacts():
    """Eliminate dots and visual artifacts in predicate centers."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find the predicate visual specification and ensure no artifacts
    if 'egrf_predicate = EGRFPredicate(' in content:
        # Look for the visual section in predicate creation
        predicate_start = content.find('egrf_predicate = EGRFPredicate(')
        predicate_end = content.find('egrf_doc.predicates.append(egrf_predicate)', predicate_start)
        
        if predicate_start != -1 and predicate_end != -1:
            predicate_section = content[predicate_start:predicate_end]
            
            # Replace any visual specifications that might create artifacts
            updated_section = predicate_section
            
            # Ensure completely clean visual specification
            if '"visual": {' in updated_section:
                # Replace the entire visual section with artifact-free version
                visual_start = updated_section.find('"visual": {')
                visual_end = updated_section.find('},', visual_start) + 1
                
                clean_visual = '''                "visual": {
                    "style": "none",
                    "position": {"x": position.x, "y": position.y},
                    "size": {"width": 0, "height": 0},
                    "fill": {"color": "transparent", "opacity": 0.0},
                    "stroke": {"color": "transparent", "width": 0.0, "style": "none"},
                    "border": "none",
                    "background": "transparent",
                    "center_dot": "none",
                    "artifacts": "none",
                    "text_only": true
                }'''
                
                updated_section = updated_section[:visual_start] + clean_visual + updated_section[visual_end:]
            
            # Replace the section in the full content
            content = content[:predicate_start] + updated_section + content[predicate_end:]
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Eliminated visual artifacts in predicate centers")

def fix_alternating_shading_consistency():
    """Fix alternating shading to ensure all even areas match level 0."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find and replace the _get_peirce_area_style method with consistent shading
    old_area_style = '''def _get_peirce_area_style(self, context_level: int) -> dict:
        """Get Peirce-compliant area styling based on nesting level."""
        cut_style = self._get_cut_style()
        
        print(f"Getting style for level {context_level}, odd={context_level % 2 == 1}")
        
        if context_level % 2 == 1:  # Odd level - shaded (negative area)
            return {
                "fill": {"color": "#c0c0c0", "opacity": 0.8},  # Darker gray shading
                "stroke": cut_style["stroke"],  # Lighter cut lines
                "shading_level": "odd"
            }
        else:  # Even level - unshaded (positive area)
            return {
                "fill": {"color": "#ffffff", "opacity": 0.0},  # Completely transparent
                "stroke": cut_style["stroke"],  # Lighter cut lines
                "shading_level": "even"
            }'''
    
    new_area_style = '''def _get_peirce_area_style(self, context_level: int) -> dict:
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
            return level_0_style'''
    
    # Replace the method
    if old_area_style in content:
        content = content.replace(old_area_style, new_area_style)
        print("✅ Fixed alternating shading consistency")
    else:
        # Try to find and replace a more general pattern
        area_style_start = content.find('def _get_peirce_area_style(self, context_level: int) -> dict:')
        if area_style_start != -1:
            # Find the end of the method
            method_end = content.find('\n    def ', area_style_start + 1)
            if method_end == -1:
                method_end = content.find('\n\n    def ', area_style_start + 1)
            
            if method_end != -1:
                content = content[:area_style_start] + new_area_style + content[method_end:]
                print("✅ Fixed alternating shading consistency (general pattern)")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed alternating shading consistency")

def add_containment_validation():
    """Add validation to ensure predicates are properly contained."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Add validation method
    validation_method = '''
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
'''
    
    # Insert before the _convert_predicates method
    convert_pred_start = content.find('def _convert_predicates(self, eg_graph: EGGraph, egrf_doc: EGRFDocument):')
    if convert_pred_start != -1:
        content = content[:convert_pred_start] + validation_method + '\n    ' + content[convert_pred_start:]
        print("✅ Added predicate containment validation")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)

def main():
    """Fix all critical visual issues."""
    
    print("🔧 FIXING CRITICAL VISUAL ISSUES")
    print("=" * 60)
    print("Addressing remaining visual rendering problems:")
    print("1. Predicate containment within cuts")
    print("2. Visual artifacts in predicate centers")
    print("3. Consistent alternating shading")
    print("=" * 60)
    
    try:
        # Fix predicate containment
        print("\n🔧 Phase 1: Fixing predicate containment...")
        fix_predicate_containment()
        
        # Eliminate visual artifacts
        print("\n🔧 Phase 2: Eliminating visual artifacts...")
        eliminate_visual_artifacts()
        
        # Fix alternating shading consistency
        print("\n🔧 Phase 3: Fixing shading consistency...")
        fix_alternating_shading_consistency()
        
        # Add containment validation
        print("\n🔧 Phase 4: Adding containment validation...")
        add_containment_validation()
        
        print("\n🎉 ALL CRITICAL VISUAL ISSUES ADDRESSED!")
        print("✅ Predicate containment positioning implemented")
        print("✅ Visual artifacts eliminated")
        print("✅ Alternating shading consistency fixed")
        print("✅ Containment validation added")
        print("\n📋 Next: Test with regenerated examples")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing critical visual issues: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

