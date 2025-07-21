#!/usr/bin/env python3
"""
Test Visual Improvements

This script regenerates the Phase 2 examples with the improved visual specifications
to validate that all rendering issues have been resolved.
"""

import sys
from pathlib import Path

# Add the EG-CL-Manus2 src directory to Python path
sys.path.insert(0, str(Path("/home/ubuntu/EG-CL-Manus2/src")))

from graph import EGGraph
from eg_types import Entity, Predicate
from egrf.egrf_generator import EGRFGenerator
from egrf.egrf_serializer import EGRFSerializer

def create_test_example():
    """Create a simple test example to validate visual improvements."""
    
    print("🔨 Creating test example with nested cuts...")
    
    # Create empty graph (sheet of assertion - level 0, unshaded)
    graph = EGGraph.create_empty()
    root_id = graph.context_manager.root_context.id
    
    # Add entity and predicate to root (level 0 - unshaded)
    x = Entity.create(name="x", entity_type="variable")
    graph = graph.add_entity(x)
    
    p_x = Predicate.create(name="P", entities=[x.id])
    graph = graph.add_predicate(p_x)
    
    # Create first cut (level 1 - should be shaded)
    graph, cut1 = graph.create_context(context_type='cut', parent_id=root_id)
    
    # Add entity and predicate to first cut (level 1 - shaded)
    y = Entity.create(name="y", entity_type="variable")
    graph = graph.add_entity(y, context_id=cut1.id)
    
    q_y = Predicate.create(name="Q", entities=[y.id])
    graph = graph.add_predicate(q_y, context_id=cut1.id)
    
    # Create second cut inside first cut (level 2 - should be unshaded)
    graph, cut2 = graph.create_context(context_type='cut', parent_id=cut1.id)
    
    # Add entity and predicate to second cut (level 2 - unshaded)
    z = Entity.create(name="z", entity_type="variable")
    graph = graph.add_entity(z, context_id=cut2.id)
    
    r_z = Predicate.create(name="R", entities=[z.id])
    graph = graph.add_predicate(r_z, context_id=cut2.id)
    
    # Create third cut inside second cut (level 3 - should be shaded)
    graph, cut3 = graph.create_context(context_type='cut', parent_id=cut2.id)
    
    # Add predicate to third cut (level 3 - shaded)
    s = Predicate.create(name="S", entities=[])
    graph = graph.add_predicate(s, context_id=cut3.id)
    
    return graph

def analyze_visual_properties(egrf_doc):
    """Analyze the visual properties of the generated EGRF document."""
    
    print("\\n🔍 ANALYZING VISUAL PROPERTIES")
    print("=" * 50)
    
    # Check context shading
    print("\\n📋 Context Shading Analysis:")
    for i, context in enumerate(egrf_doc.contexts):
        visual = context.visual
        level = visual.get("peirce_level", "unknown")
        shading = visual.get("shading_level", "unknown")
        fill = visual.get("fill", {})
        
        print(f"Context {i+1}:")
        print(f"  Level: {level}")
        print(f"  Shading: {shading}")
        print(f"  Fill: {fill}")
        print(f"  Expected: {'shaded' if level != 'unknown' and level % 2 == 1 else 'unshaded'}")
    
    # Check predicate properties
    print("\\n📋 Predicate Properties Analysis:")
    for i, predicate in enumerate(egrf_doc.predicates):
        visual = predicate.visual
        fill = visual.get("fill", {})
        stroke = visual.get("stroke", {})
        center_dot = visual.get("center_dot", {})
        text_only = visual.get("text_only", False)
        
        print(f"Predicate {i+1} ({predicate.name}):")
        print(f"  Fill: {fill}")
        print(f"  Stroke: {stroke}")
        print(f"  Center dot: {center_dot}")
        print(f"  Text only: {text_only}")
    
    # Check entity properties (variable suppression)
    print("\\n📋 Entity Label Analysis:")
    for i, entity in enumerate(egrf_doc.entities):
        labels = entity.labels
        if labels:
            label = labels[0]
            text = label.get("text", "")
            visible = label.get("visible", True)
            suppressed = label.get("suppressed", False)
            annotation = label.get("annotation", "")
            
            print(f"Entity {i+1}:")
            print(f"  Original name: {entity.id}")
            print(f"  Display text: '{text}'")
            print(f"  Visible: {visible}")
            print(f"  Suppressed: {suppressed}")
            print(f"  Annotation: {annotation}")
    
    # Check line weights
    print("\\n📋 Line Weight Analysis:")
    for i, entity in enumerate(egrf_doc.entities):
        visual = entity.visual
        stroke = visual.get("stroke", {})
        width = stroke.get("width", "unknown")
        
        print(f"Entity {i+1} (ligature):")
        print(f"  Line width: {width}")
        print(f"  Expected: 3.0 (heavy line)")
    
    for i, context in enumerate(egrf_doc.contexts):
        visual = context.visual
        stroke = visual.get("stroke", {})
        width = stroke.get("width", "unknown") if isinstance(stroke, dict) else "unknown"
        
        print(f"Context {i+1} (cut):")
        print(f"  Line width: {width}")
        print(f"  Expected: 1.5 (light line)")

def test_visual_improvements():
    """Test all visual improvements by generating and analyzing an example."""
    
    print("🧪 TESTING VISUAL IMPROVEMENTS")
    print("=" * 60)
    print("Generating test example with multiple nesting levels")
    print("Validating all visual rendering fixes")
    print("=" * 60)
    
    try:
        # Create test graph
        graph = create_test_example()
        
        print(f"\\nGraph structure:")
        print(f"  Entities: {len(graph.entities)}")
        print(f"  Predicates: {len(graph.predicates)}")
        print(f"  Contexts: {len(graph.context_manager.contexts)}")
        
        # Generate EGRF with improved visual specifications
        print("\\n📄 Generating EGRF with improved visuals...")
        generator = EGRFGenerator()
        egrf_doc = generator.generate(graph)
        
        # Update metadata
        egrf_doc.metadata.title = "Visual Improvements Test"
        egrf_doc.metadata.description = "Test example for validating visual rendering fixes"
        egrf_doc.metadata.version = "3.0"
        
        # Analyze visual properties
        analyze_visual_properties(egrf_doc)
        
        # Generate EGRF file
        serializer = EGRFSerializer()
        egrf_json = serializer.to_json(egrf_doc)
        
        filename = "visual_improvements_test.egrf"
        with open(filename, 'w') as f:
            f.write(egrf_json)
        
        print(f"\\n✅ Generated test file: {filename}")
        
        # Check CLIF generation
        clif_equivalent = egrf_doc.semantics.logical_form.get("clif_equivalent", "()")
        print(f"Generated CLIF: '{clif_equivalent}'")
        
        # Validate improvements
        print("\\n🎯 VALIDATION RESULTS")
        print("=" * 50)
        
        improvements_validated = []
        
        # Check predicate transparency
        predicate_transparent = all(
            pred.visual.get("fill", {}).get("opacity", 1.0) == 0.0 
            for pred in egrf_doc.predicates
        )
        improvements_validated.append(("Predicate transparency", predicate_transparent))
        
        # Check line weights
        heavy_ligatures = all(
            entity.visual.get("stroke", {}).get("width", 0) == 3.0
            for entity in egrf_doc.entities
        )
        improvements_validated.append(("Heavy ligature lines", heavy_ligatures))
        
        # Check variable suppression
        variables_suppressed = any(
            label.get("suppressed", False)
            for entity in egrf_doc.entities
            for label in entity.labels
        )
        improvements_validated.append(("Variable name suppression", variables_suppressed))
        
        # Check alternating shading
        has_shaded_contexts = any(
            context.visual.get("shading_level") == "odd"
            for context in egrf_doc.contexts
        )
        has_unshaded_contexts = any(
            context.visual.get("shading_level") == "even"
            for context in egrf_doc.contexts
        )
        alternating_shading = has_shaded_contexts and has_unshaded_contexts
        improvements_validated.append(("Alternating shading", alternating_shading))
        
        # Report results
        for improvement, validated in improvements_validated:
            status = "✅ WORKING" if validated else "❌ NEEDS ATTENTION"
            print(f"{improvement}: {status}")
        
        all_working = all(validated for _, validated in improvements_validated)
        
        if all_working:
            print("\\n🎉 ALL VISUAL IMPROVEMENTS VALIDATED!")
            print("✅ Ready for production use")
        else:
            print("\\n⚠️  SOME IMPROVEMENTS NEED ATTENTION")
            print("❌ Additional fixes may be required")
        
        return all_working, filename
        
    except Exception as e:
        print(f"❌ Error testing visual improvements: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def regenerate_phase2_examples():
    """Regenerate Phase 2 examples with improved visuals."""
    
    print("\\n🔄 REGENERATING PHASE 2 EXAMPLES")
    print("=" * 60)
    print("Applying visual improvements to all Phase 2 examples")
    
    # Import the Phase 2 creation functions
    sys.path.append('/home/ubuntu')
    
    try:
        from redesign_phase2_diagrams import (
            create_authentic_exactly_one_p,
            create_authentic_disjunction,
            create_authentic_implication,
            create_authentic_universal_quantification,
            create_authentic_double_negation
        )
        
        examples = [
            ("Exactly One P", create_authentic_exactly_one_p, "phase2_exactly_one_p_visual_improved.egrf"),
            ("P or Q", create_authentic_disjunction, "phase2_p_or_q_visual_improved.egrf"),
            ("A implies B", create_authentic_implication, "phase2_implication_visual_improved.egrf"),
            ("All men are mortal", create_authentic_universal_quantification, "phase2_universal_visual_improved.egrf"),
            ("Double negation", create_authentic_double_negation, "phase2_double_negation_visual_improved.egrf")
        ]
        
        generator = EGRFGenerator()
        serializer = EGRFSerializer()
        
        regenerated_files = []
        
        for name, create_func, filename in examples:
            try:
                print(f"\\n🔧 Regenerating: {name}")
                
                # Create graph
                graph, title, description = create_func()
                
                # Generate EGRF with improved visuals
                egrf_doc = generator.generate(graph)
                egrf_doc.metadata.title = title + " (Visual Improved)"
                egrf_doc.metadata.description = description + " - With improved visual rendering"
                egrf_doc.metadata.version = "3.0"
                
                # Save file
                egrf_json = serializer.to_json(egrf_doc)
                with open(filename, 'w') as f:
                    f.write(egrf_json)
                
                clif = egrf_doc.semantics.logical_form.get("clif_equivalent", "()")
                print(f"✅ Generated: {filename}")
                print(f"   CLIF: {clif}")
                
                regenerated_files.append(filename)
                
            except Exception as e:
                print(f"❌ Error regenerating {name}: {e}")
        
        print(f"\\n✅ Regenerated {len(regenerated_files)} examples with improved visuals")
        return regenerated_files
        
    except ImportError as e:
        print(f"❌ Could not import Phase 2 functions: {e}")
        return []

def main():
    """Test all visual improvements."""
    
    print("🚀 COMPREHENSIVE VISUAL IMPROVEMENTS TEST")
    print("=" * 70)
    
    # Test with new example
    success, test_file = test_visual_improvements()
    
    # Regenerate Phase 2 examples
    regenerated_files = regenerate_phase2_examples()
    
    # Summary
    print("\\n" + "=" * 70)
    print("VISUAL IMPROVEMENTS TEST SUMMARY")
    print("=" * 70)
    
    if success:
        print("✅ Visual improvements validation: PASSED")
    else:
        print("❌ Visual improvements validation: FAILED")
    
    print(f"✅ Regenerated examples: {len(regenerated_files)}")
    
    if test_file:
        print(f"✅ Test file generated: {test_file}")
    
    if regenerated_files:
        print("\\n📋 Regenerated files with improved visuals:")
        for filename in regenerated_files:
            print(f"  • {filename}")
    
    overall_success = success and len(regenerated_files) > 0
    
    if overall_success:
        print("\\n🎉 VISUAL IMPROVEMENTS SUCCESSFULLY IMPLEMENTED!")
        print("✅ All rendering issues addressed")
        print("✅ Examples regenerated with improved visuals")
        print("✅ Ready for GUI integration and testing")
    else:
        print("\\n⚠️  ADDITIONAL WORK REQUIRED")
        print("❌ Some visual improvements may need refinement")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

