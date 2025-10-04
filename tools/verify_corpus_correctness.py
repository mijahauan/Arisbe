#!/usr/bin/env python3
"""Verify logical correctness across entire corpus"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from style_loader import StyleLoader

# Import checking functions
exec(open('tools/check_cut_nesting.py').read().split('# Test graphs')[0])

storage = EntityStorageManager(Path('corpus/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style = StyleLoader().load_default_style()

entities = storage.list_entities()
print(f"Verifying logical correctness of {len(entities)} corpus graphs...")
print()

all_passed = True

for entity_name in sorted(entities):
    entity = storage.load_entity(entity_name)
    egi = entity.current_egi
    
    # Skip empty graphs
    if not egi.area or egi.sheet not in egi.area:
        print(f"⊘  {entity_name}: empty graph (skipped)")
        continue
    
    dto = layout_engine.generate_layout(egi, style, None)
    
    # Check cut nesting
    nesting_issues = check_cut_nesting(egi, dto)
    
    # Check ligature crossings
    crossing_issues = check_ligature_crossings(egi, dto)
    
    if nesting_issues or crossing_issues:
        all_passed = False
        print(f"❌ {entity_name}:")
        for issue in nesting_issues:
            print(f"   NESTING: {issue}")
        for issue in crossing_issues:
            print(f"   CROSSING: {issue}")
    else:
        print(f"✅ {entity_name}: logically correct")

print()
print("=" * 60)
if all_passed:
    print("🎉 ALL CORPUS GRAPHS ARE LOGICALLY CORRECT!")
    print("   - All cuts properly nested")
    print("   - Zero illegal ligature crossings")
    print("   - Bottom-up layout architecture validated")
else:
    print("❌ Some graphs have logical errors")
    print("   Layout cannot be considered correct")
