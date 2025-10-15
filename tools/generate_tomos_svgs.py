#!/usr/bin/env python3
"""Generate SVGs for entire tomos with bottom-up layout"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from style_loader import StyleLoader

storage = EntityStorageManager(Path('tomos/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
renderer = GraphvizSVGRenderer()
style = StyleLoader().load_default_style()

output_dir = Path("test_outputs/corpus_bottom_up_verified")
output_dir.mkdir(parents=True, exist_ok=True)

entities = storage.list_entities()
print(f"Generating SVGs for {len(entities)} tomos graphs...")
print(f"Output directory: {output_dir}")
print()

generated = []
skipped = []

for entity_name in sorted(entities):
    entity = storage.load_entity(entity_name)
    egi = entity.current_egi
    
    # Skip empty graphs
    if not egi.area or egi.sheet not in egi.area:
        print(f"⊘  {entity_name}: empty graph (skipped)")
        skipped.append(entity_name)
        continue
    
    try:
        # Generate layout
        dto = layout_engine.generate_layout(egi, style, None)
        
        # Render to SVG
        svg_path = renderer.save_svg(
            dto,
            f"{entity_name} (Bottom-Up Verified)",
            entity.get_current_egif(),
            entity_name,
            output_dir
        )
        
        generated.append(entity_name)
        print(f"✅ {entity_name}")
        print(f"   → {svg_path.name}")
        
    except Exception as e:
        print(f"❌ {entity_name}: {e}")

print()
print("=" * 60)
print(f"Generated {len(generated)} SVGs")
print(f"Skipped {len(skipped)} empty graphs")
print()
print(f"📁 SVGs saved to: {output_dir.absolute()}")
print()
print("Key graphs to review:")
print("  - shared_constant_disjunction.svg: Simple nested case")
print("  - peirce_modus_ponens.svg: Triple nesting")
print("  - roberts_domain_modeling.svg: Complex with multiple vertices")
print("  - stanford_nested_quantifiers.svg: Complex quantifier scoping")
