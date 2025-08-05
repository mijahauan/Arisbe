#!/usr/bin/env python3
"""
Generate Sample EGIF Visuals

This script produces clean, reference-quality PNG images of various EGIF expressions
to demonstrate the properly working EG diagram rendering pipeline with all visual
fixes applied (line width distinctions, proper predicate positioning, clean connections).
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def generate_sample_egif_visuals():
    """Generate a comprehensive set of sample EGIF visuals."""
    
    print("🎨 Generating Sample EGIF Visuals")
    print("=" * 50)
    print("Creating reference-quality EG diagrams with all visual fixes applied...")
    print()
    
    # Comprehensive sample EGIF expressions demonstrating key EG features
    sample_egifs = [
        {
            'name': 'Simple Constant',
            'egif': '(Human "Socrates")',
            'description': 'Basic predicate with constant - shows heavy line connection',
            'features': ['constant vertex', 'predicate', 'heavy line of identity']
        },
        {
            'name': 'Variable Predicate',
            'egif': '*x (Human x)',
            'description': 'Variable with predicate - demonstrates variable representation',
            'features': ['variable vertex', 'predicate', 'heavy line connection']
        },
        {
            'name': 'Simple Cut',
            'egif': '*x ~[ (Mortal x) ]',
            'description': 'Vertex outside cut, predicate inside - shows cut containment',
            'features': ['cut boundary', 'predicate containment', 'line crossing cut']
        },
        {
            'name': 'Sibling Cuts',
            'egif': '*x ~[ (Human x) ] ~[ (Mortal x) ]',
            'description': 'Two non-overlapping cuts sharing a vertex',
            'features': ['non-overlapping cuts', 'shared vertex', 'proper containment']
        },
        {
            'name': 'Nested Cuts',
            'egif': '*x ~[ ~[ (Mortal x) ] ]',
            'description': 'Double negation with nested cuts',
            'features': ['nested containment', 'hierarchical cuts', 'double negation']
        },
        {
            'name': 'Binary Relation',
            'egif': '*x *y (Loves x y)',
            'description': 'Two-place predicate with two variables',
            'features': ['binary relation', 'multiple variables', 'nu mapping order']
        },
        {
            'name': 'Mixed Constants Variables',
            'egif': '*x (Loves "Socrates" x)',
            'description': 'Relation mixing constant and variable',
            'features': ['mixed arguments', 'constant and variable', 'argument order']
        },
        {
            'name': 'Complex Expression',
            'egif': '*x (Human x) ~[ (Mortal x) (Wise x) ]',
            'description': 'Human outside cut, both Mortal and Wise inside cut',
            'features': ['multiple predicates', 'shared variable', 'cut containment']
        }
    ]
    
    try:
        # Import the fixed components
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        from diagram_renderer_dau import DiagramRendererDau, VisualConvention
        from pyside6_canvas import PySide6Canvas
        from pipeline_contracts import validate_full_pipeline
        
        print("✅ All components imported successfully")
        
        # Initialize components with proper visual conventions
        layout_engine = GraphvizLayoutEngine()
        conventions = VisualConvention()
        
        print(f"📊 Visual Conventions Applied:")
        print(f"   Heavy lines (identity): {conventions.identity_line_width} width")
        print(f"   Fine lines (cuts): {conventions.cut_line_width} width")
        print(f"   Distinction ratio: {conventions.identity_line_width / conventions.cut_line_width:.1f}x")
        print()
        
        successful_renders = 0
        
        for i, sample in enumerate(sample_egifs, 1):
            print(f"{i}. {sample['name']}")
            print(f"   EGIF: {sample['egif']}")
            print(f"   Description: {sample['description']}")
            print(f"   Features: {', '.join(sample['features'])}")
            
            try:
                # Step 1: Parse EGIF → EGI
                graph = parse_egif(sample['egif'])
                print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
                
                # Step 2: Create Layout
                layout_result = layout_engine.create_layout_from_graph(graph)
                print(f"   ✅ Layout: {len(layout_result.primitives)} elements positioned")
                
                # Step 3: Validate Pipeline Contracts
                canvas = PySide6Canvas(800, 600, title=f"EGIF: {sample['name']}")
                validate_full_pipeline(sample['egif'], graph, layout_result, canvas)
                print(f"   ✅ All pipeline contracts validated")
                
                # Step 4: Render with Fixed Visual System
                renderer = DiagramRendererDau(conventions)
                renderer.render_diagram(canvas, graph, layout_result)
                
                # Step 5: Save Reference Image
                filename = f"sample_{i:02d}_{sample['name'].lower().replace(' ', '_')}.png"
                canvas.save_to_file(filename)
                print(f"   ✅ Generated: {filename}")
                successful_renders += 1
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        # Summary
        print("🎯 Sample EGIF Visual Generation Complete!")
        print("=" * 50)
        print(f"Successfully generated: {successful_renders}/{len(sample_egifs)} images")
        
        if successful_renders == len(sample_egifs):
            print("✅ All sample visuals generated successfully!")
            print("\nGenerated PNG files demonstrate:")
            print("  • Heavy lines of identity (4.0 width) vs fine cut lines (1.5 width)")
            print("  • Proper predicate containment within cut boundaries")
            print("  • Clean line connections to predicate periphery")
            print("  • Non-overlapping cuts and proper spatial separation")
            print("  • Correct nu mapping and argument order preservation")
        else:
            print(f"⚠️  {len(sample_egifs) - successful_renders} images failed to generate")
        
        return successful_renders == len(sample_egifs)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("The rendering pipeline components are not available.")
        return False

def analyze_generated_visuals():
    """Provide analysis guidance for the generated visuals."""
    
    print("\n🔍 Visual Analysis Guide")
    print("-" * 30)
    print("For each generated PNG file, verify:")
    print()
    print("✓ LINE DISTINCTIONS:")
    print("  - Heavy lines of identity are visibly thicker than cut lines")
    print("  - Clear visual difference between 4.0 and 1.5 width lines")
    print()
    print("✓ PREDICATE POSITIONING:")
    print("  - Predicate text never crosses cut boundaries")
    print("  - Predicates are entirely contained within their designated areas")
    print("  - Proper margins maintained within cuts")
    print()
    print("✓ LINE CONNECTIONS:")
    print("  - Lines connect to predicate text edges, not centers")
    print("  - Clean, consistent connections without overlaps")
    print("  - Lines cross cut boundaries only when connecting different areas")
    print()
    print("✓ SPATIAL ORGANIZATION:")
    print("  - Non-overlapping cuts (sibling cuts clearly separated)")
    print("  - Proper hierarchical containment (nested cuts)")
    print("  - Clear visual discrimination of all elements")
    print()
    print("✓ EG FORMALISM COMPLIANCE:")
    print("  - Dau's conventions properly followed")
    print("  - Argument order preserved in nu mapping")
    print("  - Logical structure accurately represented visually")

if __name__ == "__main__":
    print("Arisbe Sample EGIF Visual Generator")
    print("Generating reference-quality EG diagrams...")
    print()
    
    # Generate the sample visuals
    success = generate_sample_egif_visuals()
    
    if success:
        # Provide analysis guidance
        analyze_generated_visuals()
        
        print("\n🎉 Sample EGIF visuals ready for inspection!")
        print("These PNG files serve as reference examples of proper EG diagram rendering.")
    else:
        print("\n❌ Visual generation incomplete. Check errors above.")
