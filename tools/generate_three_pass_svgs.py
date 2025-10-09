#!/usr/bin/env python3
"""
Generate SVG outputs from the three-pass layout engine.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from three_pass_layout_engine import ThreePassLayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from style_loader import StyleLoader
from egif_generator_dau import EGIFGenerator

def generate_svgs():
    """Generate SVGs for all graphs."""
    storage = EntityStorageManager(Path('corpus/graphs'))
    engine = ThreePassLayoutEngine()
    renderer = GraphvizSVGRenderer()
    style = StyleLoader().load_default_style()
    
    output_dir = Path('test_outputs/three_pass_svgs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    corpus_dir = Path('corpus/graphs')
    
    print("Generating SVGs with three-pass layout engine...")
    print()
    
    success = 0
    failed = 0
    
    for graph_dir in sorted(corpus_dir.iterdir()):
        if not graph_dir.is_dir():
            continue
        
        egi_files = list(graph_dir.glob('*.egi.json'))
        if not egi_files:
            continue
        
        name = graph_dir.name
        
        try:
            entity = storage.load_entity(name)
            egi = entity.current_egi
            
            # Generate layout
            dto = engine.generate_layout(egi, style, None)
            
            # Generate EGIF
            egif = EGIFGenerator(egi).generate()
            
            # Render SVG
            svg_path = renderer.save_svg(
                dto, 
                f"Three-Pass Layout - {name}", 
                egif,
                name,
                output_dir,
                style
            )
            
            print(f"✅ {name:35s} -> {svg_path.name}")
            success += 1
            
        except Exception as e:
            print(f"❌ {name:35s} FAILED: {str(e)[:60]}")
            failed += 1
    
    print()
    print(f"Generated {success} SVGs in {output_dir}")
    if failed > 0:
        print(f"Failed: {failed}")

if __name__ == '__main__':
    generate_svgs()
