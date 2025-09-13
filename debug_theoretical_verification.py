"""
Debug script for theoretical verification issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chapter18_enhanced_translation import (
    EnhancedChapter18Translator, parse_fopl_formula
)

def debug_single_case():
    """Debug a single simple case to identify the issue."""
    translator = EnhancedChapter18Translator()
    
    print("🔍 Debugging theoretical verification...")
    
    # Test simplest case
    formula_str = "Man(x)"
    print(f"Testing: {formula_str}")
    
    try:
        # Step 1: Parse formula
        print("Step 1: Parsing formula...")
        original_formula = parse_fopl_formula(formula_str)
        print(f"   Parsed: {original_formula}")
        
        # Step 2: FOPL → EGI
        print("Step 2: FOPL → EGI...")
        egi_from_fopl = translator.psi_translate(original_formula)
        print(f"   EGI: {len(egi_from_fopl.V)}v, {len(egi_from_fopl.E)}e, {len(egi_from_fopl.Cut)}c")
        
        # Step 3: EGI → FOPL
        print("Step 3: EGI → FOPL...")
        fopl_roundtrip = translator.phi_translate(egi_from_fopl)
        print(f"   Roundtrip: {fopl_roundtrip}")
        
        # Step 4: FOPL → EGI (second round)
        print("Step 4: FOPL → EGI (second round)...")
        egi_roundtrip = translator.psi_translate(parse_fopl_formula(fopl_roundtrip))
        print(f"   EGI roundtrip: {len(egi_roundtrip.V)}v, {len(egi_roundtrip.E)}e, {len(egi_roundtrip.Cut)}c")
        
        print("✅ Debug successful - no errors in basic flow")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_single_case()
