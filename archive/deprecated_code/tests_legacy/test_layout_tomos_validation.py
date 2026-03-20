"""
Layout Engine Tomos Validation Tests
"""

import pytest
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from src.layout_engine import LayoutEngine
from src.egif_parser_dau import parse_egif
from src.gui.styles.dau_compliant_style import DauCompliantStyle


def render_layout_svg(layout, egif_source, filename, style=None, egi=None):
    """
    Pure SVG renderer that ONLY uses information from the layout DTO.
    
    This test validates that the DTO contains everything needed for rendering.
    NO layout logic should be in this function - only DTO-to-SVG translation.
    """
    viewport = layout.viewport_bounds
    width = max(250, int(viewport.max_x - viewport.min_x + 60))
    height = max(200, int(viewport.max_y - viewport.min_y + 80))
    
    svg = ET.Element("svg", {"width": str(width), "height": str(height), "xmlns": "http://www.w3.org/2000/svg"})
    
    # PURE DTO RENDERING - NO STYLE LOGIC HERE
    # Background
    ET.SubElement(svg, "rect", {"x": "0", "y": "0", "width": str(width), "height": str(height), "fill": "white"})
    
    # Title showing style applied (from DTO)
    ET.SubElement(svg, "text", {"x": "10", "y": "20", "font-size": "14", "font-weight": "bold"}).text = f"{style.name if style else 'Default'} Style"
    
    # Style ID from layout DTO
    if layout.style_id:
        ET.SubElement(svg, "text", {"x": "10", "y": "35", "font-size": "10", "fill": "gray"}).text = f"Style ID: {layout.style_id}"
    
    # Cuts - render from DTO bounds only
    for bounds in layout.cut_bounds.values():
        ET.SubElement(svg, "rect", {
            "x": str(bounds.min_x + 20), "y": str(bounds.min_y + 50),
            "width": str(bounds.max_x - bounds.min_x), "height": str(bounds.max_y - bounds.min_y),
            "fill": "none", "stroke": "black", "stroke-width": "2.0",
            "rx": "8.0", "ry": "8.0"  # TODO: Get from DTO style info
        })
    
    # Predicate labels - render from DTO edge_labels
    for edge_id, text_layout in layout.edge_labels.items():
        ET.SubElement(svg, "text", {
            "x": str(text_layout.position.x + 20), 
            "y": str(text_layout.position.y + 50),
            "text-anchor": text_layout.alignment, 
            "font-size": str(text_layout.font_size), 
            "font-family": text_layout.font_family,
            "fill": text_layout.color
        }).text = text_layout.text
    
    # Ligatures - render from DTO edge_paths
    for edge_id, path_list in layout.edge_paths.items():
        for path in path_list:
            if len(path.points) >= 2:
                path_data = f"M {path.points[0].x + 20} {path.points[0].y + 50}"
                for point in path.points[1:]:
                    path_data += f" L {point.x + 20} {point.y + 50}"
                
                ET.SubElement(svg, "path", {
                    "d": path_data, "fill": "none",
                    "stroke": "black", "stroke-width": "3.0"  # Dau spec: thicker ligatures
                })
    
    # Vertices - render from DTO positions AND styles
    for vertex_id, pos in layout.vertex_positions.items():
        vertex_style = layout.vertex_styles.get(vertex_id)
        if vertex_style:
            attrs = {
                "cx": str(pos.x + 20), 
                "cy": str(pos.y + 50), 
                "r": str(vertex_style.radius),
                "fill": vertex_style.fill_color
            }
            if vertex_style.stroke_color != "none":
                attrs["stroke"] = vertex_style.stroke_color
                attrs["stroke-width"] = str(vertex_style.stroke_width)
            else:
                attrs["stroke"] = "none"
            
            ET.SubElement(svg, "circle", attrs)
    
    # EGIF at bottom for comparison
    ET.SubElement(svg, "text", {
        "x": "10", "y": str(height - 10), "font-family": "monospace", "font-size": "12"
    }).text = f"EGIF: {egif_source}"
    
    # Save
    output_dir = Path("test_outputs/corpus_layouts")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"{filename}.svg", 'w') as f:
        f.write(ET.tostring(svg, encoding='unicode'))


class TestCorpusLayoutValidation:
    """Test layout engine with corpus-style EGIFs"""
    
    def setup_method(self):
        self.engine = LayoutEngine()
    
    def test_corpus_examples(self):
        """Test layout engine against COMPLETE CORPUS (15 graphs) with Dau style"""
        from src.corpus_index import load_index
        
        dau_style = DauCompliantStyle()
        corpus_index = load_index()
        
        print(f"\n=== TESTING COMPLETE CORPUS ({len(corpus_index['entries'])} graphs) ===")
        
        success_count = 0
        total_count = 0
        
        for entry in corpus_index['entries']:
            graph_id = entry['id']
            total_count += 1
            print(f"\n[{total_count}/15] Testing: {graph_id}")
            
            # Load the EGIF from the tomos entry
            graph_path = Path(entry['path'])
            json_file = graph_path / f"{graph_id}.json"
            
            if json_file.exists():
                with open(json_file, 'r') as f:
                    graph_data = json.load(f)
                    
                if 'linear_forms' in graph_data and 'egif' in graph_data['linear_forms']:
                    egif = graph_data['linear_forms']['egif']['content']
                    print(f"  EGIF: {egif}")
                    
                    try:
                        egi = parse_egif(egif)
                        layout = self.engine.compute_layout(egi, diagram_style=dau_style)
                        
                        # Validate style was applied
                        assert layout.style_id == "dau-compliant@1.0"
                        
                        # Debug key metrics
                        print(f"  Vertices: {len(egi.V)}, Edges: {len(egi.E)}, Cuts: {len(egi.Cut)}")
                        print(f"  Layout: {len(layout.vertex_positions)} vertices, {len(layout.edge_positions)} predicates")
                        
                        # Render to SVG for inspection
                        render_layout_svg(layout, egif, f"corpus_{graph_id}", dau_style, egi)
                        
                        success_count += 1
                        print(f"  ✅ SUCCESS - Layout computed with Dau style")
                        
                    except Exception as e:
                        print(f"  ❌ FAILED: {e}")
                        # Still assert to fail the test
                        raise AssertionError(f"Tomos graph {graph_id} failed: {e}")
                else:
                    print(f"  ⚠️  No EGIF found - skipping")
            else:
                print(f"  ⚠️  JSON file not found: {json_file}")
        
        print(f"\n=== CORPUS TEST SUMMARY ===")
        print(f"✅ Success: {success_count}/{total_count} graphs")
        print(f"📊 Success rate: {success_count/total_count*100:.1f}%")
        
        # Require high success rate
        assert success_count >= 14, f"Expected at least 14 successful layouts, got {success_count}"
    
    def test_basic_examples(self):
        """Test layout engine with basic EG examples for development/debugging"""
        dau_style = DauCompliantStyle()
        
        # Basic examples for development and regression testing
        basic_examples = [
            ("simple", '*x (Human x)'),
            ("cut", '~[ *x (Human x) ]'),
            ("relation", '*x *y (Loves x y)'),  # Binary relation
            ("multiple", '*x *y (Human x) (Mortal y)'),  # Two separate predicates
            ("nested", '~[ ~[ *x (Human x) ] ]')  # Nested cuts
        ]
        
        print(f"\n=== TESTING BASIC EXAMPLES ({len(basic_examples)} graphs) ===")
        
        for name, egif in basic_examples:
            print(f"\nTesting: {name}")
            print(f"  EGIF: {egif}")
            
            egi = parse_egif(egif)
            layout = self.engine.compute_layout(egi, diagram_style=dau_style)
            
            # Validate style was applied
            assert layout.style_id == "dau-compliant@1.0"
            
            # Debug key metrics
            print(f"  Vertices: {len(egi.V)}, Edges: {len(egi.E)}, Cuts: {len(egi.Cut)}")
            print(f"  Layout: {len(layout.vertex_positions)} vertices, {len(layout.edge_positions)} predicates")
            
            # Render using style information with EGI for relation names
            render_layout_svg(layout, egif, name, dau_style, egi)
            
            print(f"  ✅ SUCCESS - {name}: style={layout.style_id}")


if __name__ == "__main__":
    test = TestCorpusLayoutValidation()
    test.setup_method()
    test.test_corpus_examples()
