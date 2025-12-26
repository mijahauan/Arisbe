#!/usr/bin/env python3
"""
Test the enhanced linear forms display functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egi_loader import load_egi_from_json
from chapter21_diagram_engine import UniversalEGIEngine

def test_linear_forms():
    """Test all linear form conversions."""
    print("🔧 TESTING ENHANCED LINEAR FORMS")
    print("=" * 60)
    
    # Load the complex example
    egi = load_egi_from_json('corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json')
    
    # Create engine
    engine = UniversalEGIEngine()
    
    print("\n1. EGIF (Existential Graph Interchange Format):")
    print("-" * 50)
    egif_text = engine._egi_to_egif(egi)
    print(egif_text)
    
    print("\n2. CGIF (Conceptual Graph Interchange Format):")
    print("-" * 50)
    cgif_text = engine._egi_to_cgif(egi)
    print(cgif_text)
    
    print("\n3. CLIF (Common Logic Interchange Format):")
    print("-" * 50)
    clif_text = engine._egi_to_clif(egi)
    print(clif_text)
    
    print("\n4. FOPL (First-Order Predicate Logic):")
    print("-" * 50)
    fopl_text = engine._egi_to_fopl(egi)
    print(fopl_text)
    
    print("\n" + "=" * 60)
    print("✅ All linear forms generated successfully!")
    print("✅ Enhanced Organon display ready for integration!")

if __name__ == "__main__":
    test_linear_forms()
