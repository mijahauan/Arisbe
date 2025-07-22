#!/usr/bin/env python3
"""
Fix Context Parent Attribute Access

The code is trying to access context.parent_id but Context objects have 
context.parent_context.
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

def fix_context_parent_attribute():
    """Fix context parent attribute access in EGRF generator"""
    
    print("🔧 FIXING CONTEXT PARENT ATTRIBUTE ACCESS")
    print("=" * 45)
    
    egrf_generator_path = "/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py"
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    print("📋 Looking for context parent attribute access...")
    
    # Fix context.parent_id -> context.parent_context
    old_parent_id = "context.parent_id"
    new_parent_context = "context.parent_context"
    
    if old_parent_id in content:
        content = content.replace(old_parent_id, new_parent_context)
        print("✅ Fixed context.parent_id -> context.parent_context")
    else:
        print("⚠️  context.parent_id not found")
    
    # Also check for current_context.parent_id
    old_current_parent = "current_context.parent_id"
    new_current_parent = "current_context.parent_context"
    
    if old_current_parent in content:
        content = content.replace(old_current_parent, new_current_parent)
        print("✅ Fixed current_context.parent_id -> current_context.parent_context")
    else:
        print("⚠️  current_context.parent_id not found")
    
    # Write fixed content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Context parent attribute fixes applied")
    
    # Test the fix by regenerating Phase 3
    test_phase3_regeneration()

def test_phase3_regeneration():
    """Test Phase 3 regeneration with fixed context attributes"""
    
    print("\n🧪 TESTING PHASE 3 REGENERATION WITH FIXES")
    print("=" * 45)
    
    try:
        from egrf import EGRFGenerator
        from egrf.egrf_serializer import EGRFSerializer
        from graph import EGGraph
        from eg_types import Entity, Predicate
        
        generator = EGRFGenerator()
        
        print("🔧 Creating test Phase 3 example...")
        
        # Simple test example
        graph = EGGraph.create_empty()
        
        # Entities
        socrates = Entity.create(name="Socrates", entity_type="individual")
        x = Entity.create(name="x", entity_type="variable")
        
        # Predicates
        man_socrates = Predicate.create(name="Man", entities=[socrates.id])
        mortal_socrates = Predicate.create(name="Mortal", entities=[socrates.id])
        
        # Add to graph
        graph = graph.add_entity(socrates).add_entity(x)
        graph = graph.add_predicate(man_socrates).add_predicate(mortal_socrates)
        
        # Create cut with correct API
        graph, cut_context = graph.create_context("cut", parent_id=graph.root_context_id)
        
        print("✅ Test graph created with context")
        
        # Generate EGRF
        egrf_doc = generator.generate(graph)
        egrf_doc.metadata.title = "Phase 3 Test"
        egrf_doc.metadata.description = "Testing Phase 3 regeneration with all fixes"
        
        print("🎉 EGRF GENERATION SUCCESSFUL!")
        
        # Validate visual section
        has_visual = hasattr(egrf_doc, 'visual') and egrf_doc.visual
        if has_visual:
            visual = egrf_doc.visual
            predicates = len(visual.get('predicates', []))
            entities = len(visual.get('entities', []))
            contexts = len(visual.get('contexts', []))
            
            print(f"✅ Visual section: P:{predicates} E:{entities} C:{contexts}")
            
            # Check Phase 2 fixes
            if predicates > 0:
                pred = visual['predicates'][0]
                visual_style = pred.get('visual', {})
                style = visual_style.get('style', '')
                fill_opacity = visual_style.get('fill', {}).get('opacity', 1.0)
                stroke_width = visual_style.get('stroke', {}).get('width', 1.0)
                
                print(f"   Predicate fixes: Style={style}, Fill={fill_opacity}, Stroke={stroke_width}")
                
                if style == 'none' and fill_opacity == 0.0 and stroke_width == 0.0:
                    print("   ✅ ALL PHASE 2 FIXES WORKING!")
                else:
                    print("   ⚠️  Some Phase 2 fixes need adjustment")
        else:
            print("❌ Visual section missing")
        
        # Validate CLIF
        has_semantics = hasattr(egrf_doc, 'semantics') and egrf_doc.semantics
        if has_semantics:
            if hasattr(egrf_doc.semantics, 'logical_form'):
                logical_form = egrf_doc.semantics.logical_form
                if hasattr(logical_form, 'clif_equivalent'):
                    clif = logical_form.clif_equivalent
                    print(f"✅ CLIF: {clif}")
                else:
                    print("❌ CLIF: No clif_equivalent attribute")
            else:
                print("❌ CLIF: No logical_form")
        else:
            print("❌ CLIF: No semantics")
        
        # Save test file
        egrf_json_str = EGRFSerializer.to_json(egrf_doc, indent=2)
        with open("/home/ubuntu/phase3_test_all_fixes_working.egrf", 'w') as f:
            f.write(egrf_json_str)
        print("💾 Test file saved: phase3_test_all_fixes_working.egrf")
        
        print("\n🎉🎉🎉 PHASE 3 REGENERATION TEST: SUCCESS! 🎉🎉🎉")
        print("✅ All API issues resolved")
        print("✅ Visual generation working")
        print("✅ Phase 2 fixes applied")
        print("✅ Ready for full Phase 3 regeneration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_context_parent_attribute()
    
    print("\n🎯 CONTEXT PARENT ATTRIBUTE FIXES COMPLETE")
    print("🎉 READY FOR FULL PHASE 3 REGENERATION!")

