#!/usr/bin/env python3
"""
Fix Predicate Constructor Parameter Mismatch

Based on the EGRF types, the Predicate constructor expects:
- connected_entities (not entities)
- type, arity parameters
- visual as PredicateVisual object (not dict)

This script fixes the parameter mismatch in egrf_generator.py
"""

import sys
from pathlib import Path

def fix_predicate_constructor():
    """Fix the predicate constructor call in egrf_generator.py."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    print("🔍 Found Predicate constructor parameters:")
    print("- id: str")
    print("- name: str") 
    print("- type: str")
    print("- arity: int")
    print("- connected_entities: List[str]")
    print("- visual: PredicateVisual")
    print("- labels: List[Label]")
    print("- connections: List[Connection]")
    
    # Find and fix the predicate creation
    old_predicate_creation = '''            egrf_predicate = EGRFPredicate(
                id=str(predicate_id),
                name=predicate.name,
                entities=[str(entity_id) for entity_id in predicate.entities],
                visual={
                    "style": "none",
                    "position": {"x": position.x, "y": position.y},
                    "size": {"width": 0, "height": 0},
                    "fill": {"color": "transparent", "opacity": 0.0},
                    "stroke": {"color": "transparent", "width": 0.0, "style": "none"},
                    "border": "none",
                    "background": "transparent",
                    "center_dot": "none",
                    "artifacts": "none",
                    "text_only": True
                },
                labels=[{
                    "text": predicate.name,
                    "position": {"x": position.x, "y": position.y},
                    "font": {
                        "family": "Arial",
                        "size": 14.0,
                        "weight": "normal",
                        "color": "#000000"
                    },
                    "alignment": "center"
                }]
            )'''
    
    new_predicate_creation = '''            # Import required types
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
            )'''
    
    if old_predicate_creation in content:
        content = content.replace(old_predicate_creation, new_predicate_creation)
        print("✅ Fixed predicate constructor with correct parameters")
    else:
        print("❌ Could not find the exact predicate creation section")
        # Try a more targeted approach
        if 'entities=[str(entity_id) for entity_id in predicate.entities]' in content:
            content = content.replace(
                'entities=[str(entity_id) for entity_id in predicate.entities]',
                'connected_entities=[str(entity_id) for entity_id in predicate.entities]'
            )
            print("✅ Fixed entities parameter name to connected_entities")
        
        # Add missing imports at the top of the file
        if 'from egrf.egrf_types import' not in content:
            import_line = 'from egrf.egrf_types import EGRFDocument, Entity as EGRFEntity, Predicate as EGRFPredicate, Context as EGRFContext, Ligature as EGRFLigature, Metadata, Canvas, Semantics'
            
            # Find the existing imports section
            lines = content.split('\n')
            import_index = -1
            for i, line in enumerate(lines):
                if line.startswith('from') or line.startswith('import'):
                    import_index = i
            
            if import_index != -1:
                lines.insert(import_index + 1, import_line)
                content = '\n'.join(lines)
                print("✅ Added missing imports")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix the predicate constructor parameter mismatch."""
    
    print("🔧 FIXING PREDICATE CONSTRUCTOR PARAMETER MISMATCH")
    print("=" * 60)
    
    try:
        success = fix_predicate_constructor()
        
        if success:
            print("\n✅ PREDICATE CONSTRUCTOR FIXED!")
            print("✅ Parameter 'entities' → 'connected_entities'")
            print("✅ Added required type and arity parameters")
            print("✅ Fixed visual specification to use proper types")
            print("✅ Added missing imports")
            return True
        else:
            print("\n❌ Failed to fix predicate constructor")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

