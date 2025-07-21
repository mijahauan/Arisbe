#!/usr/bin/env python3
"""
Fix Indentation Manually

The automatic fix didn't work. Let's manually fix the indentation issue.
"""

import sys
from pathlib import Path

def fix_indentation_manually():
    """Manually fix the indentation around the problematic line."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find the problematic section and replace it with properly indented version
    old_section = '''                })
            
                        egrf_predicate = EGRFPredicate(
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
    
    new_section = '''                })
            
            egrf_predicate = EGRFPredicate(
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
    
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✅ Fixed indentation manually")
    else:
        print("❌ Could not find the exact section to fix")
        # Try a more targeted approach
        content = content.replace(
            '                        egrf_predicate = EGRFPredicate(',
            '            egrf_predicate = EGRFPredicate('
        )
        print("✅ Fixed main line indentation")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Manually fix the indentation."""
    
    print("🔧 FIXING INDENTATION MANUALLY")
    print("=" * 35)
    
    try:
        success = fix_indentation_manually()
        
        if success:
            print("✅ Manual indentation fix applied")
            return True
        else:
            print("❌ Failed to fix indentation manually")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

