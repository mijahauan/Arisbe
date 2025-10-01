#!/usr/bin/env python3
"""
Test script for Dau-Compliant Layout Engine

This script tests the new layout engine that strictly follows Dau's formalism
for EGI visualization, ensuring logical isomorphism between mathematical
structure and spatial representation.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from layout_engine_dau_compliant import DauCompliantLayoutEngine
from style_loader import StyleLoader
from egif_parser_dau import parse_egif
from svg_renderer_dto import SVGRendererDTO


def test_dau_compliant_engine():
    """Test the Dau-compliant layout engine with problematic cases"""
    
    print("🚀 TESTING DAU-COMPLIANT LAYOUT ENGINE")
    print("=" * 60)
    
    # Load style
    try:
        style_loader = StyleLoader()
        style = style_loader.load_style('dau-compliant@1.0')
        print(f"✅ Style loaded: {style.style_name}")
    except Exception as e:
        print(f"❌ Failed to load style: {e}")
        return False
    
    # Initialize engines
    layout_engine = DauCompliantLayoutEngine(style)
    renderer = SVGRendererDTO()
    
    # Test cases that previously failed
    test_cases = [
        {
            'name': 'OverlappingText',
            'description': 'Case that produced overlapping Human labels',
            'egif': '*x *y (Human x) (Human y) (Friend x y) ~[ (Enemy x y) ]'
        },
        {
            'name': 'SimpleBoundary', 
            'description': 'Simple boundary violation case',
            'egif': '*x (Human x) ~[ (Mortal x) ]'
        },
        {
            'name': 'ComplexNested',
            'description': 'Complex nested structure',
            'egif': '*x *y *z (Human x) (Human y) (Human z) ~[ (Mortal x) ~[ (Greek y) ] ]'
        },
        {
            'name': 'MultiplePredicates',
            'description': 'Multiple predicates between same vertices',
            'egif': '*x *y (Human x) (Human y) (Friend x y) (Likes x y) (Knows x y)'
        }
    ]
    
    results = []
    output_dir = Path('test_outputs/dau_compliant_layouts')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📚 Testing with style: {style.style_name}")
    print()
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']} - {test_case['description']}")
        
        try:
            # Parse EGIF
            egi = parse_egif(test_case['egif'])
            vertex_count = len(egi.V)
            edge_count = len(egi.E) 
            cut_count = len(egi.Cut)
            print(f"   ✅ Parsed: {vertex_count} vertices, {edge_count} edges, {cut_count} cuts")
            
            # Compute layout
            layout = layout_engine.compute_layout(egi)
            print(f"   ✅ Layout computed successfully")
            
            # Validate layout
            validation_result = validate_layout(layout, egi, test_case['name'])
            
            # Render SVG
            svg_filename = f"dau_compliant_{test_case['name'].lower()}"
            svg_path = renderer.save_svg(
                layout, egi, svg_filename, 
                f"Dau-Compliant Layout - {test_case['name']}",
                test_case['egif'],
                output_dir=str(output_dir)
            )
            svg_path_obj = Path(svg_path)
            print(f"   📄 SVG rendered: {svg_path_obj.name}")
            
            results.append({
                'name': test_case['name'],
                'success': validation_result['success'],
                'issues': validation_result['issues'],
                'svg_path': svg_path_obj
            })
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'name': test_case['name'],
                'success': False,
                'issues': [f"Exception: {e}"],
                'svg_path': None
            })
        
        print()
    
    # Summary
    print("🎯 TEST SUMMARY:")
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"   Total tests: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {total - successful}")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    if successful < total:
        print("   ⚠️  Some tests failed - check output for details")
    else:
        print("   🎉 All tests passed!")
    
    # Create HTML index
    create_html_index(results, output_dir)
    
    print(f"\n📊 Results saved to: {output_dir}")
    print(f"🌐 Open in browser: file://{output_dir.absolute()}/index.html")
    
    return successful == total


def validate_layout(layout, egi, test_name):
    """Validate that layout follows Dau's principles"""
    issues = []
    
    # Check 1: All elements have positions
    all_elements = set()
    for v in egi.V:
        all_elements.add(v.id)
    for e in egi.E:
        all_elements.add(e.id)
    
    positioned_elements = set(layout.element_positions.keys())
    missing_elements = all_elements - positioned_elements
    if missing_elements:
        issues.append(f"Missing positions for elements: {missing_elements}")
    
    # Check 2: Container hierarchy is complete
    expected_containers = {egi.sheet}
    for cut in egi.Cut:
        expected_containers.add(cut.id)
    
    layout_containers = set(layout.containers.keys())
    missing_containers = expected_containers - layout_containers
    if missing_containers:
        issues.append(f"Missing containers: {missing_containers}")
    
    # Check 3: Elements are in correct containers
    for element_id, position in layout.element_positions.items():
        container_id = position.container_id
        if container_id not in layout.containers:
            issues.append(f"Element {element_id} references non-existent container {container_id}")
        else:
            container = layout.containers[container_id]
            if element_id not in container.direct_elements:
                issues.append(f"Element {element_id} not listed in container {container_id} direct elements")
    
    # Check 4: Ligature paths exist for all connections
    expected_ligatures = set()
    for edge_id, vertex_sequence in egi.nu.items():
        if vertex_sequence:
            expected_ligatures.add(edge_id)
    
    actual_ligatures = {path.edge_id for path in layout.ligature_paths}
    missing_ligatures = expected_ligatures - actual_ligatures
    if missing_ligatures:
        issues.append(f"Missing ligature paths for edges: {missing_ligatures}")
    
    # Check 5: No overlapping elements (basic check)
    positions = [(pos.local_position.x, pos.local_position.y) 
                for pos in layout.element_positions.values()]
    if len(positions) != len(set(positions)):
        issues.append("Some elements have identical positions (potential overlap)")
    
    success = len(issues) == 0
    
    if success:
        print("   ✅ Layout validation: PASSED")
    else:
        print("   ❌ Layout validation: FAILED")
        for issue in issues:
            print(f"      • {issue}")
    
    return {'success': success, 'issues': issues}


def create_html_index(results, output_dir):
    """Create HTML index page for viewing results"""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Dau-Compliant Layout Engine Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .test-case { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .success { border-left: 5px solid #4CAF50; }
        .failure { border-left: 5px solid #f44336; }
        .svg-container { margin: 10px 0; }
        .issues { background: #fff3cd; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .issue { margin: 5px 0; }
        svg { border: 1px solid #ccc; margin: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Dau-Compliant Layout Engine Test Results</h1>
        <p>Testing layout engine that strictly follows Frithjof Dau's formalism for EGI visualization</p>
    </div>
"""
    
    for result in results:
        status_class = "success" if result['success'] else "failure"
        status_icon = "✅" if result['success'] else "❌"
        
        html_content += f"""
    <div class="test-case {status_class}">
        <h3>{status_icon} {result['name']}</h3>
        <p><strong>Status:</strong> {'PASSED' if result['success'] else 'FAILED'}</p>
"""
        
        if result['issues']:
            html_content += '<div class="issues"><strong>Issues:</strong><ul>'
            for issue in result['issues']:
                html_content += f'<li class="issue">{issue}</li>'
            html_content += '</ul></div>'
        
        if result['svg_path']:
            html_content += f"""
        <div class="svg-container">
            <h4>Generated Layout:</h4>
            <object data="{result['svg_path'].name}" type="image/svg+xml" width="800" height="600">
                <p>Your browser does not support SVG</p>
            </object>
        </div>
"""
        
        html_content += "    </div>\n"
    
    html_content += """
</body>
</html>"""
    
    index_path = output_dir / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html_content)
    
    print(f"   📄 HTML index created: {index_path.name}")


if __name__ == "__main__":
    success = test_dau_compliant_engine()
    sys.exit(0 if success else 1)
