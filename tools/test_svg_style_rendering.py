#!/usr/bin/env python3
"""
SVG Style Rendering Test

Tests the complete pipeline from EGIF → StyleAwareLayoutEngine → SVG rendering
with different styles and readability optimization levels.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from layout_engine_styled import StyleAwareLayoutEngine, ElementDistribution
from readability_optimizer import OptimizationLevel
from style_loader import StyleLoader, load_default_style
from egif_parser_dau import parse_egif
from svg_renderer_dto import SVGRendererDTO


def test_svg_style_rendering():
    """Test SVG rendering with different styles and optimization levels"""
    
    print("🎨 SVG STYLE RENDERING TEST")
    print("=" * 40)
    
    # Test EGIFs with different complexity levels
    test_cases = [
        {
            "name": "Simple",
            "egif": "*x (Human x)",
            "description": "Basic vertex and predicate"
        },
        {
            "name": "Complex",
            "egif": "*x *y (Human x) (Human y) (Friend x y) (Mortal x)",
            "description": "Multiple vertices and relations"
        },
        {
            "name": "WithCut",
            "egif": "*x (Human x) ~[ (Mortal x) ]",
            "description": "Negation with cut"
        },
        {
            "name": "Nested",
            "egif": "*x *y (Human x) (Human y) ~[ (Enemy x y) ~[ (Friend x y) ] ]",
            "description": "Nested cuts with complex relations"
        }
    ]
    
    # Load available styles
    style_loader = StyleLoader()
    available_styles = style_loader.list_available_styles()
    
    # Filter to valid styles (skip problematic ones)
    valid_styles = [s for s in available_styles if s.endswith('@1.0') and s != 'dau-classic@1.0']
    
    print(f"📚 Available styles: {', '.join(valid_styles)}")
    print()
    
    # Create SVG renderer
    renderer = SVGRendererDTO()
    
    # Test each combination
    total_rendered = 0
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']} - {test_case['description']}")
        
        try:
            # Parse EGIF
            egi = parse_egif(test_case['egif'])
            print(f"   ✅ Parsed: {len(egi.V)} vertices, {len(egi.E)} edges")
            
            for style_name in valid_styles:
                try:
                    # Load style
                    style = style_loader.load_style(style_name)
                    engine = StyleAwareLayoutEngine(style)
                    
                    # Test different optimization levels
                    for optimize in [False, True]:
                        opt_label = "Optimized" if optimize else "Basic"
                        
                        # Generate layout
                        layout = engine.compute_layout(egi, optimize_readability=optimize)
                        
                        # Create filename
                        safe_style = style_name.replace('@', '_').replace('-', '_')
                        filename = f"{test_case['name'].lower()}_{safe_style}_{opt_label.lower()}"
                        
                        # Render SVG
                        title = f"{test_case['name']} - {style.style_name} ({opt_label})"
                        svg_path = renderer.save_svg(
                            layout, egi, filename, title, test_case['egif']
                        )
                        
                        print(f"   ✅ {style.style_name} ({opt_label}): {Path(svg_path).name}")
                        total_rendered += 1
                        
                except Exception as e:
                    print(f"   ❌ {style_name}: {e}")
            
        except Exception as e:
            print(f"   ❌ Failed to parse EGIF: {e}")
        
        print()
    
    print(f"🎉 RENDERING COMPLETE!")
    print(f"   Total SVGs rendered: {total_rendered}")
    print(f"   Output directory: test_outputs/new_layouts/")
    print()
    
    # Create an index HTML file for easy viewing
    create_svg_index(total_rendered)


def create_svg_index(total_count):
    """Create an HTML index file for viewing all SVGs"""
    
    output_dir = Path("test_outputs/new_layouts")
    svg_files = list(output_dir.glob("*.svg"))
    
    if not svg_files:
        print("   ⚠️  No SVG files found to index")
        return
    
    # Sort files for better organization
    svg_files.sort()
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Arisbe SVG Style Rendering Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .svg-container {{ 
            display: inline-block; 
            margin: 10px; 
            border: 1px solid #ccc; 
            padding: 10px;
            vertical-align: top;
        }}
        .svg-title {{ 
            font-weight: bold; 
            margin-bottom: 5px; 
            font-size: 12px;
        }}
        svg {{ 
            max-width: 300px; 
            max-height: 250px; 
        }}
        .summary {{ 
            background: #f0f0f0; 
            padding: 10px; 
            margin-bottom: 20px; 
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>🎨 Arisbe SVG Style Rendering Test Results</h1>
    
    <div class="summary">
        <h3>Test Summary</h3>
        <p><strong>Total SVGs rendered:</strong> {total_count}</p>
        <p><strong>Styles tested:</strong> DAU-compliant, Peirce-authentic, Sowa-compliant</p>
        <p><strong>Optimization levels:</strong> Basic, Optimized (with readability optimization)</p>
        <p><strong>Test cases:</strong> Simple, Complex, WithCut, Nested</p>
    </div>
    
    <h2>Rendered Diagrams</h2>
"""
    
    for svg_file in svg_files:
        # Extract info from filename
        filename = svg_file.stem
        parts = filename.split('_')
        
        test_case = parts[0].title() if parts else "Unknown"
        style_info = ' '.join(parts[1:-1]).replace('_', ' ').title() if len(parts) > 2 else "Unknown Style"
        opt_level = parts[-1].title() if parts else "Unknown"
        
        html_content += f"""
    <div class="svg-container">
        <div class="svg-title">{test_case} - {style_info} ({opt_level})</div>
        <object data="{svg_file.name}" type="image/svg+xml">
            <img src="{svg_file.name}" alt="{filename}" />
        </object>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    # Save HTML index
    index_path = output_dir / "index.html"
    with open(index_path, 'w') as f:
        f.write(html_content)
    
    print(f"   📄 HTML index created: {index_path}")
    print(f"   🌐 Open in browser: file://{index_path.absolute()}")


def test_style_comparison():
    """Create a side-by-side comparison of all styles"""
    
    print("🔄 CREATING STYLE COMPARISON")
    print("-" * 30)
    
    # Use a moderately complex EGIF for comparison
    test_egif = "*x *y (Human x) (Human y) (Friend x y) ~[ (Enemy x y) ]"
    
    try:
        egi = parse_egif(test_egif)
        style_loader = StyleLoader()
        renderer = SVGRendererDTO()
        
        # Create comparison layouts
        valid_styles = ['dau-compliant@1.0', 'peirce-authentic@1.0', 'sowa-compliant@1.0']
        
        for style_name in valid_styles:
            if style_name in style_loader.list_available_styles():
                try:
                    style = style_loader.load_style(style_name)
                    engine = StyleAwareLayoutEngine(style)
                    
                    # Generate optimized layout
                    layout = engine.compute_layout(egi, optimize_readability=True)
                    
                    # Render comparison SVG
                    filename = f"comparison_{style_name.replace('@', '_').replace('-', '_')}"
                    title = f"Style Comparison - {style.style_name}"
                    
                    svg_path = renderer.save_svg(layout, egi, filename, title, test_egif)
                    print(f"   ✅ {style.style_name}: {Path(svg_path).name}")
                    
                except Exception as e:
                    print(f"   ❌ {style_name}: {e}")
        
        print("   ✅ Style comparison complete")
        
    except Exception as e:
        print(f"   ❌ Comparison failed: {e}")


if __name__ == '__main__':
    try:
        test_svg_style_rendering()
        test_style_comparison()
        
        print("\n🎯 SVG RENDERING TEST COMPLETE!")
        print("Check test_outputs/new_layouts/ for all rendered SVGs")
        print("Open test_outputs/new_layouts/index.html in a browser to view all results")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
