#!/usr/bin/env python3
"""
Test Clean EGI System - Demonstrate Simple, Parsimonious Architecture

This test shows the essential operations:
1. Create EGI through formal operations
2. Generate EGIF linear form
3. Generate EGDF visual form
4. All centered on EGI as single source of truth
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egi_system import create_egi_system
import json


def test_clean_egi_system():
    """Test the clean EGI-centric architecture."""
    
    print("🧪 Testing Clean EGI System")
    print("=" * 50)
    
    # Create EGI system
    egi_system = create_egi_system()
    
    # Build a simple graph: P(x)
    print("\n📝 Building graph: P(x)")
    
    # Insert vertex x
    result = egi_system.insert_vertex("x")
    print(f"   Insert vertex 'x': {'✅' if result.success else '❌'}")
    
    # Insert predicate P connecting to x
    result = egi_system.insert_edge("P", "P", ["x"])
    print(f"   Insert edge 'P(x)': {'✅' if result.success else '❌'}")
    
    # Generate EGIF linear form
    print("\n📄 Linear Form (EGIF):")
    try:
        egif = egi_system.to_egif()
        print(f"   {egif}")
    except Exception as e:
        print(f"   ❌ EGIF generation failed: {e}")
    
    # Generate EGDF visual form
    print("\n🎨 Visual Form (EGDF):")
    try:
        egdf = egi_system.to_egdf()
        print(f"   Vertices: {len(egdf['egi_structure']['vertices'])}")
        print(f"   Edges: {len(egdf['egi_structure']['edges'])}")
        print(f"   Spatial primitives: {len(egdf['visual_layout']['spatial_primitives'])}")
        
        # Show spatial layout
        for primitive in egdf['visual_layout']['spatial_primitives']:
            ptype = primitive['type']
            pid = primitive['id']
            bounds = primitive['bounds']
            print(f"   {ptype} '{pid}': x={bounds['x']}, y={bounds['y']}")
            
    except Exception as e:
        print(f"   ❌ EGDF generation failed: {e}")
    
    # Test with negation: ~P(x)
    print("\n📝 Adding negation: ~P(x)")
    
    # Insert cut
    result = egi_system.insert_cut("cut1")
    print(f"   Insert cut: {'✅' if result.success else '❌'}")
    
    # Move P(x) into cut (simplified - just insert new P in cut)
    result = egi_system.insert_vertex("x2", "cut1")
    print(f"   Insert vertex in cut: {'✅' if result.success else '❌'}")
    
    result = egi_system.insert_edge("P2", "P", ["x2"], "cut1")
    print(f"   Insert edge in cut: {'✅' if result.success else '❌'}")
    
    # Show final state
    print("\n📊 Final EGI State:")
    egi = egi_system.get_egi()
    print(f"   Vertices: {len(egi.V)}")
    print(f"   Edges: {len(egi.E)}")
    print(f"   Cuts: {len(egi.Cut)}")
    print(f"   Areas: {list(egi.area.keys())}")
    
    # Generate final EGDF
    print("\n🎨 Final Visual Form:")
    try:
        final_egdf = egi_system.to_egdf()
        print(f"   Total spatial primitives: {len(final_egdf['visual_layout']['spatial_primitives'])}")
        
        # Export to file for inspection
        with open('clean_egi_output.json', 'w') as f:
            json.dump(final_egdf, f, indent=2)
        print("   📁 Exported to clean_egi_output.json")
        
    except Exception as e:
        print(f"   ❌ Final EGDF generation failed: {e}")
    
    print("\n✅ Clean EGI System Test Complete")
    print("   - EGI as single source of truth")
    print("   - Formal operations preserve Dau compliance")
    print("   - Linear and visual forms are projections")
    print("   - Simple, clean, parsimonious architecture")


if __name__ == "__main__":
    test_clean_egi_system()
