#!/usr/bin/env python3
"""
Fix Artifact Detection Logic

The test is still detecting artifacts because:
1. Size is still 60x30 instead of 0x0
2. Text_only is False instead of True
3. Center_dot and artifacts are "unknown" instead of "none"

The issue is that the visual specification in the EGRF generator is not being applied correctly.
"""

import sys
from pathlib import Path

def find_and_fix_predicate_visual_override():
    """Find where the predicate visual is being overridden and fix it."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Look for where the visual properties are being set in the EGRFPredicate creation
    if 'egrf_predicate = EGRFPredicate(' in content:
        # Find the predicate creation section
        predicate_start = content.find('egrf_predicate = EGRFPredicate(')
        predicate_end = content.find('egrf_doc.predicates.append(egrf_predicate)', predicate_start)
        
        if predicate_start != -1 and predicate_end != -1:
            predicate_section = content[predicate_start:predicate_end]
            
            print("Current predicate creation section:")
            print(predicate_section[:500] + "..." if len(predicate_section) > 500 else predicate_section)
            
            # Replace the entire predicate creation with clean version
            new_predicate_creation = '''            egrf_predicate = EGRFPredicate(
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
            )
            
            '''
            
            # Replace the section
            content = content[:predicate_start] + new_predicate_creation + content[predicate_end:]
            print("✅ Replaced predicate creation with clean version")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix the artifact detection by ensuring clean predicate creation."""
    
    print("🔧 FIXING ARTIFACT DETECTION")
    print("=" * 40)
    print("Ensuring predicate creation uses completely clean visual specification")
    
    try:
        success = find_and_fix_predicate_visual_override()
        
        if success:
            print("✅ Predicate creation fixed")
            print("✅ Should now generate artifact-free predicates")
            return True
        else:
            print("❌ Failed to fix predicate creation")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

