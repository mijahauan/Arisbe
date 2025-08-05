#!/usr/bin/env python3
"""
Generate Visual Examples of EGIF Rendering

Generate actual PNG images of various EGIF examples to demonstrate
the "completely solidified" and "visually compliant" rendering claims.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def generate_comprehensive_visual_examples():
    """Generate comprehensive visual examples of EGIF rendering."""
    
    print("🎨 Generating Visual Examples of EGIF Rendering")
    print("=" * 50)
    
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        from diagram_renderer_clean import RenderingTheme
        from pyside6_contract_integration import render_egif_with_contracts
        
        # Comprehensive test cases covering key EG patterns
        test_cases = [
            # Basic patterns
            ("simple_predicate", '(Human "Socrates")', "Simple predicate with constant"),
            ("identity_line", '*x (Human x)', "Identity line with predicate"),
            ("multiple_predicates", '*x (Human x) (Mortal x)', "Multiple predicates on same identity"),
            
            # Cut patterns
            ("simple_cut", '~[ (Human "Socrates") ]', "Simple negation cut"),
            ("cut_with_identity", '*x ~[ (Mortal x) ]', "Cut with identity line"),
            ("nested_cuts", '*x ~[ ~[ (Mortal x) ] ]', "Nested cuts (double negation)"),
            
            # Complex patterns
            ("sibling_cuts", '*x ~[ (P x) ] ~[ (Q x) ]', "Sibling cuts with shared identity"),
            ("mixed_sheet_cut", '(Human "Socrates") ~[ (Mortal "Socrates") ]', "Mixed sheet and cut elements"),
            ("complex_nesting", '*x (Human x) ~[ (Mortal x) ~[ (Wise x) ] ]', "Complex nested structure"),
            
            # Advanced patterns
            ("multiple_identities", '*x *y (Loves x y)', "Multiple identity variables"),
            ("complex_sharing", '*x (Human x) (Mortal x) ~[ (Wise x) (Good x) ]', "Complex identity sharing"),
            ("deep_nesting", '*x ~[ ~[ ~[ (P x) ] ] ]', "Deep nesting (triple negation)"),
        ]
        
        layout_engine = GraphvizLayoutEngine()
        theme = RenderingTheme()
        
        print(f"📋 Rendering Theme Configuration:")
        print(f"   • Identity line width: {theme.identity_line_width}")
        print(f"   • Cut line width: {theme.cut_line_width}")
        print(f"   • Vertex radius: {theme.vertex_radius}")
        print(f"   • Hook line width: {theme.hook_line_width}")
        print()
        
        success_count = 0
        total_count = len(test_cases)
        
        for filename, egif, description in test_cases:
            print(f"🖼️  Generating: {filename}.png")
            print(f"   EGIF: {egif}")
            print(f"   Description: {description}")
            
            try:
                # Parse EGIF
                graph = parse_egif(egif)
                print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
                
                # Generate layout
                layout_result = layout_engine.create_layout_from_graph(graph)
                print(f"   ✅ Layout: {len(layout_result.primitives)} spatial primitives")
                
                # Use contract-enforced rendering
                output_path = f"visual_example_{filename}.png"
                success = render_egif_with_contracts(
                    egif, output_path, 
                    canvas_width=800, canvas_height=600
                )
                
                if success:
                    print(f"   ✅ Saved: {output_path} (contract-enforced)")
                    success_count += 1
                else:
                    print(f"   ❌ Contract validation failed")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Generation Summary:")
        print(f"   • Successfully generated: {success_count}/{total_count} examples")
        print(f"   • Success rate: {success_count/total_count*100:.1f}%")
        
        if success_count > 0:
            print(f"\n🔍 Visual Inspection Instructions:")
            print(f"   1. Open the generated PNG files to inspect visual quality")
            print(f"   2. Verify heavy identity lines vs fine cut boundaries")
            print(f"   3. Check that cuts properly contain their elements")
            print(f"   4. Confirm nested cuts show clear hierarchy")
            print(f"   5. Validate spacing and professional appearance")
            
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_visual_quality():
    """Analyze the visual quality of generated examples."""
    
    print(f"\n🔍 Visual Quality Analysis")
    print("-" * 30)
    
    # Check if files were generated
    expected_files = [
        "visual_example_simple_predicate.png",
        "visual_example_identity_line.png", 
        "visual_example_simple_cut.png",
        "visual_example_nested_cuts.png",
        "visual_example_sibling_cuts.png",
        "visual_example_mixed_sheet_cut.png"
    ]
    
    generated_files = []
    for filename in expected_files:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            generated_files.append((filename, file_size))
            print(f"   ✅ {filename} ({file_size:,} bytes)")
        else:
            print(f"   ❌ {filename} - Not found")
    
    if generated_files:
        print(f"\n📋 Visual Validation Checklist:")
        print(f"   For each generated PNG, verify:")
        print(f"   □ Heavy identity lines are visually distinct (4.0 width)")
        print(f"   □ Cut boundaries are fine-drawn (1.0 width)")
        print(f"   □ Vertex spots are prominent (3.5 radius)")
        print(f"   □ Elements are properly contained in cuts")
        print(f"   □ Nested cuts show clear hierarchy")
        print(f"   □ Spacing prevents visual crowding")
        print(f"   □ Overall professional appearance")
        
        return len(generated_files)
    else:
        print(f"   ⚠️  No visual examples were generated successfully")
        return 0

def demonstrate_dau_conventions():
    """Demonstrate specific Dau conventions in the visual output."""
    
    print(f"\n📚 Dau Convention Demonstration")
    print("-" * 35)
    
    print(f"The generated examples should demonstrate:")
    print(f"")
    print(f"🔹 HEAVY LINES OF IDENTITY (Dau's Key Convention):")
    print(f"   • Lines connecting vertices to predicates should be bold/heavy")
    print(f"   • Width: 4.0 (enhanced from previous 3.0)")
    print(f"   • Color: Black, solid style")
    print(f"   • Should be clearly distinguishable from cut boundaries")
    print(f"")
    print(f"🔹 FINE CUT BOUNDARIES (Dau's Key Convention):")
    print(f"   • Cut boundaries should be fine-drawn closed curves")
    print(f"   • Width: 1.0 (maintained fine appearance)")
    print(f"   • Shape: Oval/circular, no fill")
    print(f"   • Should clearly contain their logical contents")
    print(f"")
    print(f"🔹 IDENTITY SPOTS (Vertex Rendering):")
    print(f"   • Vertices should appear as prominent spots")
    print(f"   • Radius: 3.5 (enhanced from previous 2.0)")
    print(f"   • Should be visible connection points for identity lines")
    print(f"")
    print(f"🔹 HIERARCHICAL CONTAINMENT:")
    print(f"   • Nested cuts should show clear visual hierarchy")
    print(f"   • Inner cuts should be visually inside outer cuts")
    print(f"   • No overlapping between sibling cuts")
    print(f"")
    print(f"🔹 PROFESSIONAL SPACING:")
    print(f"   • Enhanced node separation (4.0)")
    print(f"   • Enhanced rank separation (3.0)")
    print(f"   • Minimum element separation (+25)")
    print(f"   • No visual crowding or overlap")

if __name__ == "__main__":
    print("Arisbe Visual Example Generation")
    print("Generating actual PNG images to validate rendering claims...")
    print()
    
    # Generate visual examples
    success = generate_comprehensive_visual_examples()
    
    if success:
        # Analyze visual quality
        file_count = analyze_visual_quality()
        
        if file_count > 0:
            # Demonstrate Dau conventions
            demonstrate_dau_conventions()
            
            print(f"\n🎉 VISUAL EXAMPLES GENERATED SUCCESSFULLY")
            print("=" * 45)
            print(f"✅ {file_count} PNG files generated for visual inspection")
            print(f"✅ Examples cover key EGIF patterns and conventions")
            print(f"✅ Ready for direct visual validation of rendering claims")
            print()
            print(f"👀 NEXT STEP: Open the generated PNG files to visually")
            print(f"   inspect the 'completely solidified' and 'visually")
            print(f"   compliant' rendering quality!")
            
        else:
            print(f"\n❌ No visual examples were successfully generated")
    else:
        print(f"\n❌ Visual example generation failed")
