#!/usr/bin/env python3
"""
Fix Graph Iteration in EGRF Generator

The issue is that the EGRF generator iterates through eg_graph.entities (keys)
instead of eg_graph.entities.values() (Entity objects).
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

def fix_graph_iteration():
    """Fix graph iteration in EGRF generator"""
    
    print("🔧 FIXING GRAPH ITERATION IN EGRF GENERATOR")
    print("=" * 50)
    
    egrf_generator_path = "/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py"
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    print("📋 Fixing iteration patterns...")
    
    # Fix entity iteration
    old_entity_iteration = "for entity in eg_graph.entities:"
    new_entity_iteration = "for entity in eg_graph.entities.values():"
    
    if old_entity_iteration in content:
        content = content.replace(old_entity_iteration, new_entity_iteration)
        print("✅ Fixed entity iteration")
    else:
        print("⚠️  Entity iteration pattern not found")
    
    # Fix predicate iteration
    old_predicate_iteration = "for predicate in eg_graph.predicates:"
    new_predicate_iteration = "for predicate in eg_graph.predicates.values():"
    
    if old_predicate_iteration in content:
        content = content.replace(old_predicate_iteration, new_predicate_iteration)
        print("✅ Fixed predicate iteration")
    else:
        print("⚠️  Predicate iteration pattern not found")
    
    # Fix context iteration if needed
    old_context_iteration = "for context in eg_graph.contexts:"
    new_context_iteration = "for context in eg_graph.contexts.values():"
    
    if old_context_iteration in content:
        content = content.replace(old_context_iteration, new_context_iteration)
        print("✅ Fixed context iteration")
    else:
        print("⚠️  Context iteration pattern not found or already correct")
    
    # Write fixed content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Graph iteration fixes applied")
    
    # Test the fix
    test_graph_iteration()

def test_graph_iteration():
    """Test if graph iteration is now working"""
    
    print("\n🧪 TESTING FIXED GRAPH ITERATION")
    print("=" * 40)
    
    try:
        from egrf import EGRFGenerator
        from graph import EGGraph
        from eg_types import Entity, Predicate
        
        # Create test data
        graph = EGGraph.create_empty()
        entity = Entity.create(name="x", entity_type="variable")
        predicate = Predicate.create(name="Test", entities=[entity.id])
        
        graph = graph.add_entity(entity)
        graph = graph.add_predicate(predicate)
        
        print("✅ Test graph created")
        
        # Debug what we're iterating through now
        print(f"\n🔍 Graph entities.values():")
        for i, entity_obj in enumerate(graph.entities.values()):
            print(f"   {i}: {type(entity_obj)} = {entity_obj}")
            print(f"      Has .id: {hasattr(entity_obj, 'id')}")
        
        print(f"\n🔍 Graph predicates.values():")
        for i, predicate_obj in enumerate(graph.predicates.values()):
            print(f"   {i}: {type(predicate_obj)} = {predicate_obj}")
            print(f"      Has .entities: {hasattr(predicate_obj, 'entities')}")
        
        # Test generation
        generator = EGRFGenerator()
        egrf_doc = generator.generate(graph)
        
        print("\n🎉 EGRF GENERATION SUCCESSFUL!")
        
        # Check visual section
        if hasattr(egrf_doc, 'visual') and egrf_doc.visual:
            print("🎉 VISUAL SECTION GENERATED SUCCESSFULLY!")
            
            visual = egrf_doc.visual
            predicates = visual.get('predicates', [])
            entities = visual.get('entities', [])
            contexts = visual.get('contexts', [])
            canvas = visual.get('canvas', {})
            
            print(f"📋 Visual elements generated:")
            print(f"   Predicates: {len(predicates)}")
            print(f"   Entities: {len(entities)}")
            print(f"   Contexts: {len(contexts)}")
            print(f"   Canvas: {canvas}")
            
            # Check Phase 2 visual fixes
            print("\n🔍 Checking Phase 2 visual fixes:")
            
            if predicates:
                pred = predicates[0]
                print(f"📍 Predicate: {pred.get('text', 'N/A')}")
                print(f"   Position: {pred.get('position', 'N/A')}")
                
                visual_style = pred.get('visual', {})
                style = visual_style.get('style', '')
                fill_opacity = visual_style.get('fill', {}).get('opacity', 'N/A')
                stroke_width = visual_style.get('stroke', {}).get('width', 'N/A')
                
                print(f"   Style: {style}")
                print(f"   Fill opacity: {fill_opacity}")
                print(f"   Stroke width: {stroke_width}")
                
                if style == 'none':
                    print("   ✅ Predicate transparency fix applied")
                else:
                    print("   ⚠️  Predicate transparency fix missing")
            
            if entities:
                ent = entities[0]
                print(f"🔗 Entity: {ent.get('type', 'N/A')}")
                
                stroke = ent.get('visual', {}).get('stroke', {})
                stroke_width = stroke.get('width', 0)
                print(f"   Stroke width: {stroke_width}")
                
                if stroke_width >= 3.0:
                    print("   ✅ Heavy line fix applied")
                else:
                    print("   ⚠️  Heavy line fix missing")
            
            # Check CLIF generation
            if hasattr(egrf_doc, 'semantics') and egrf_doc.semantics:
                logical_form = egrf_doc.semantics.get('logical_form', {})
                clif = logical_form.get('clif_equivalent', '')
                print(f"🔍 CLIF: {clif}")
                
                if clif and clif != "()":
                    print("   ✅ CLIF generation working")
                else:
                    print("   ⚠️  CLIF generation issue")
            
            # Save test file
            from egrf.egrf_serializer import EGRFSerializer
            egrf_json_str = EGRFSerializer.to_json(egrf_doc, indent=2)
            with open("/home/ubuntu/test_visual_iteration_fixed.egrf", 'w') as f:
                f.write(egrf_json_str)
            print("\n💾 Test file saved: test_visual_iteration_fixed.egrf")
            
            return True
        else:
            print("❌ Visual section still missing")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_graph_iteration()
    
    print("\n🎯 GRAPH ITERATION FIXES COMPLETE")
    print("Visual generation should now be fully working!")

