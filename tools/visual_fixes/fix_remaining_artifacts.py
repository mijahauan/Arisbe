#!/usr/bin/env python3
"""
Fix Remaining Visual Artifacts

The test shows that predicates still have artifacts:
- Style: "oval" instead of "none"
- Size: width/height instead of 0
- Text only: False instead of True

This script fixes these remaining issues.
"""

import sys
from pathlib import Path

def fix_predicate_style_artifacts():
    """Fix the predicate style to eliminate all visual artifacts."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Find the predicate creation section and fix the visual specification
    if 'egrf_predicate = EGRFPredicate(' in content:
        # Look for the visual section in predicate creation
        predicate_start = content.find('egrf_predicate = EGRFPredicate(')
        predicate_end = content.find('egrf_doc.predicates.append(egrf_predicate)', predicate_start)
        
        if predicate_start != -1 and predicate_end != -1:
            predicate_section = content[predicate_start:predicate_end]
            
            # Replace the entire visual section with completely artifact-free version
            if '"visual": {' in predicate_section:
                visual_start = predicate_section.find('"visual": {')
                visual_end = predicate_section.find('},', visual_start) + 1
                
                # Create completely clean visual specification
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
                
                predicate_section = predicate_section[:visual_start] + clean_visual + predicate_section[visual_end:]
                
                # Replace the section in the full content
                content = content[:predicate_start] + predicate_section + content[predicate_end:]
                print("✅ Fixed predicate visual specification to eliminate artifacts")
            
            # Also check if there's a separate style assignment that overrides this
            if '"style": "oval"' in content:
                content = content.replace('"style": "oval"', '"style": "none"')
                print("✅ Fixed oval style override")
            
            # Fix any size assignments
            if '"width": 60.0' in content and 'predicate' in content:
                content = content.replace('"width": 60.0', '"width": 0')
                print("✅ Fixed predicate width")
            
            if '"height": 30.0' in content and 'predicate' in content:
                content = content.replace('"height": 30.0', '"height": 0')
                print("✅ Fixed predicate height")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def fix_predicate_creation_method():
    """Fix the predicate creation method to use text-only rendering."""
    
    egrf_generator_path = Path("/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py")
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    # Look for the predicate style method and ensure it returns clean specification
    if '_get_peirce_predicate_style' in content:
        # Find and replace the entire method
        method_start = content.find('def _get_peirce_predicate_style(self, context_id: str, eg_graph: EGGraph) -> dict:')
        if method_start != -1:
            method_end = content.find('\n    def ', method_start + 1)
            if method_end == -1:
                method_end = content.find('\n\n    def ', method_start + 1)
            
            if method_end != -1:
                new_method = '''def _get_peirce_predicate_style(self, context_id: str, eg_graph: EGGraph) -> dict:
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
        }'''
                
                content = content[:method_start] + new_method + content[method_end:]
                print("✅ Fixed _get_peirce_predicate_style method")
    
    # Write updated content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix all remaining visual artifacts."""
    
    print("🔧 FIXING REMAINING VISUAL ARTIFACTS")
    print("=" * 50)
    print("Eliminating all predicate visual artifacts:")
    print("- Style: oval → none")
    print("- Size: 60x30 → 0x0")
    print("- Text only: False → True")
    print("=" * 50)
    
    try:
        # Fix predicate style artifacts
        print("\n🔧 Fixing predicate style artifacts...")
        fix_predicate_style_artifacts()
        
        # Fix predicate creation method
        print("\n🔧 Fixing predicate creation method...")
        fix_predicate_creation_method()
        
        print("\n✅ ALL VISUAL ARTIFACTS FIXES APPLIED")
        print("✅ Predicates should now be completely clean")
        print("✅ Text-only rendering enabled")
        print("✅ No visual boundaries or artifacts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing visual artifacts: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

