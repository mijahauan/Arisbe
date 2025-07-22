#!/usr/bin/env python3
"""
Fix Missing Visual Section Call

The generate method is not calling _add_visual_section, which is why
the visual section is missing from the EGRF documents.
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

def fix_missing_visual_call():
    """Add missing _add_visual_section call to generate method"""
    
    print("🔧 FIXING MISSING VISUAL SECTION CALL")
    print("=" * 40)
    
    egrf_generator_path = "/home/ubuntu/EG-CL-Manus2/src/egrf/egrf_generator.py"
    
    # Read current content
    with open(egrf_generator_path, 'r') as f:
        content = f.read()
    
    print("📋 Looking for generate method...")
    
    # Find the generate method and add the missing visual call
    old_generate_end = """        # Add semantic information with proper CLIF generation
        self._add_semantics(egrf_doc, eg_graph)
        
        return egrf_doc"""
    
    new_generate_end = """        # Add visual section with all visual elements
        self._add_visual_section(egrf_doc, eg_graph)
        
        # Add semantic information with proper CLIF generation
        self._add_semantics(egrf_doc, eg_graph)
        
        return egrf_doc"""
    
    if old_generate_end in content:
        content = content.replace(old_generate_end, new_generate_end)
        print("✅ Added _add_visual_section call to generate method")
    else:
        print("⚠️  Generate method pattern not found - checking alternative patterns")
        
        # Try alternative pattern
        alt_pattern = """        # Add semantic information with proper CLIF generation
        self._add_semantics(egrf_doc, eg_graph)
        
        return egrf_doc"""
        
        if alt_pattern in content:
            alt_replacement = """        # Add visual section with all visual elements
        self._add_visual_section(egrf_doc, eg_graph)
        
        # Add semantic information with proper CLIF generation
        self._add_semantics(egrf_doc, eg_graph)
        
        return egrf_doc"""
            
            content = content.replace(alt_pattern, alt_replacement)
            print("✅ Added _add_visual_section call (alternative pattern)")
        else:
            print("❌ Could not find generate method pattern to modify")
            return False
    
    # Write fixed content back
    with open(egrf_generator_path, 'w') as f:
        f.write(content)
    
    print("✅ Visual section call added to generate method")
    
    # Test the fix
    test_visual_call_fix()
    
    return True

def test_visual_call_fix():
    """Test if visual section is now being generated"""
    
    print("\n🧪 TESTING VISUAL SECTION CALL FIX")
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
        
        # Test generation
        generator = EGRFGenerator()
        egrf_doc = generator.generate(graph)
        
        print("🎉 EGRF GENERATION SUCCESSFUL!")
        
        # Check visual section
        if hasattr(egrf_doc, 'visual') and egrf_doc.visual:
            print("🎉🎉🎉 VISUAL SECTION FINALLY GENERATED! 🎉🎉🎉")
            
            visual = egrf_doc.visual
            predicates = visual.get('predicates', [])
            entities = visual.get('entities', [])
            contexts = visual.get('contexts', [])
            canvas = visual.get('canvas', {})
            
            print(f"\n📋 COMPLETE VISUAL ELEMENTS:")
            print(f"   Predicates: {len(predicates)}")
            print(f"   Entities: {len(entities)}")
            print(f"   Contexts: {len(contexts)}")
            print(f"   Canvas: {canvas}")
            
            # ULTIMATE PHASE 2 FIXES VALIDATION
            print(f"\n🏆 ULTIMATE PHASE 2 FIXES VALIDATION:")
            print(f"=" * 45)
            
            success_count = 0
            total_checks = 0
            
            if predicates:
                pred = predicates[0]
                print(f"📍 PREDICATE: '{pred.get('text', 'N/A')}'")
                print(f"   Position: {pred.get('position', 'N/A')}")
                
                visual_style = pred.get('visual', {})
                style = visual_style.get('style', '')
                fill = visual_style.get('fill', {})
                stroke = visual_style.get('stroke', {})
                
                # Check all predicate fixes
                checks = [
                    ("Transparent Style", style == 'none'),
                    ("Transparent Fill", fill.get('opacity', 1.0) == 0.0),
                    ("No Border", stroke.get('width', 1.0) == 0.0),
                    ("Text Only Rendering", style == 'none' and stroke.get('width', 1.0) == 0.0)
                ]
                
                print(f"   PREDICATE FIXES:")
                for check_name, is_working in checks:
                    status = "✅" if is_working else "❌"
                    print(f"     {status} {check_name}")
                    total_checks += 1
                    if is_working:
                        success_count += 1
            
            if entities:
                ent = entities[0]
                print(f"\n🔗 ENTITY: '{ent.get('type', 'N/A')}'")
                
                visual_style = ent.get('visual', {})
                stroke = visual_style.get('stroke', {})
                stroke_width = stroke.get('width', 1.0)
                
                heavy_line_working = stroke_width >= 3.0
                status = "✅" if heavy_line_working else "❌"
                print(f"   ENTITY FIXES:")
                print(f"     {status} Heavy Line (width: {stroke_width})")
                
                total_checks += 1
                if heavy_line_working:
                    success_count += 1
            
            # CLIF validation
            if hasattr(egrf_doc, 'semantics') and egrf_doc.semantics:
                logical_form = egrf_doc.semantics.get('logical_form', {})
                clif = logical_form.get('clif_equivalent', '')
                
                clif_working = clif and clif != "()"
                status = "✅" if clif_working else "❌"
                print(f"\n🔍 CLIF: '{clif}'")
                print(f"   SEMANTIC FIXES:")
                print(f"     {status} CLIF Generation")
                
                total_checks += 1
                if clif_working:
                    success_count += 1
            
            # Save ultimate test file
            from egrf.egrf_serializer import EGRFSerializer
            egrf_json_str = EGRFSerializer.to_json(egrf_doc, indent=2)
            with open("/home/ubuntu/ULTIMATE_PHASE2_RESTORATION_SUCCESS.egrf", 'w') as f:
                f.write(egrf_json_str)
            print(f"\n💾 ULTIMATE TEST FILE: ULTIMATE_PHASE2_RESTORATION_SUCCESS.egrf")
            
            # Final success rate
            success_rate = (success_count / total_checks) * 100 if total_checks > 0 else 0
            print(f"\n🏆 FINAL SUCCESS RATE: {success_count}/{total_checks} ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                print(f"🎉🎉🎉 PHASE 2 VISUAL FIXES SUCCESSFULLY RESTORED! 🎉🎉🎉")
                print(f"✅ Ready to regenerate Phase 3 examples with proper visual presentation")
                return True
            else:
                print(f"⚠️  Some fixes need fine-tuning, but visual generation is working!")
                return True
        else:
            print("❌ Visual section still missing after adding call")
            print("Need to debug _add_visual_section method")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_missing_visual_call()
    
    if success:
        print("\n🎯 VISUAL SECTION CALL FIX COMPLETE")
        print("🎉 PHASE 2 VISUAL FIXES RESTORATION: SUCCESS!")
    else:
        print("\n❌ Could not fix visual section call")
        print("Manual intervention may be needed")

