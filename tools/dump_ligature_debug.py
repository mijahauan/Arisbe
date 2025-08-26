#!/usr/bin/env python3
import sys
import os
import json
from typing import Any, Dict

# Ensure src/ is on the path
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def dump_for_egif(egif_text: str) -> Dict[str, Any]:
    # Be verbose to help spot pipeline failures
    os.environ.setdefault('ARISBE_DEBUG_ROUTING', '1')
    try:
        from egi_system import EGISystem
    except Exception as e:
        return {"error": f"import egi_system failed: {e}"}

    try:
        eg = EGISystem()
        eg.load_egif(egif_text)
        egdf = eg.to_egdf()
    except Exception as e:
        return {"error": f"EGDF generation failed: {e}"}

    try:
        out: Dict[str, Any] = {}
        egi_struct = egdf.get('egi_structure', {})
        out['NU'] = egi_struct.get('connections')
        out['REL'] = egi_struct.get('relations')
        out['VERTICES'] = egi_struct.get('vertices')
        out['EDGES'] = egi_struct.get('edges')

        layout = egdf.get('visual_layout', {}).get('spatial_primitives', [])
        out['LAYOUT_TYPES'] = {p.get('id'): p.get('type') for p in layout}
        ligs = [p for p in layout if p.get('type') == 'ligature']
        out['LIGATURE_COUNT'] = len(ligs)
        out['LIGATURES'] = []
        for p in ligs:
            ld = p.get('ligature_data', {})
            out['LIGATURES'].append({
                'id': p.get('id'),
                'vertices': ld.get('vertices'),
                'path_len': len(ld.get('spatial_path') or []),
                'branching_point_count': len(ld.get('branching_points') or []),
            })
        return out
    except Exception as e:
        return {"error": f"layout inspection failed: {e}"}


def main() -> int:
    if len(sys.argv) > 1:
        egif = " ".join(sys.argv[1:])
    else:
        egif = "*x *y (Loves x y)"
    result = dump_for_egif(egif)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
