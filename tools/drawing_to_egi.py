#!/usr/bin/env python3
"""
CLI helper to convert a drawing JSON into a Dau-compliant RelationalGraphWithCuts and
optionally attempt a headless spatial layout.

Usage:
  python tools/drawing_to_egi.py --input example.json [--layout]
"""
import argparse
import json
from pathlib import Path

from drawing_to_egi_adapter import drawing_to_relational_graph
from egi_spatial_correspondence import SpatialCorrespondenceEngine


def summarize(rgc):
    print("Sheet:", rgc.sheet)
    print("Vertices:", [v.id for v in rgc.V])
    print("Edges:", [e.id for e in rgc.E])
    print("Cuts:", [c.id for c in rgc.Cut])
    print("rel:", dict(rgc.rel))
    print("nu:", {k: list(v) for k, v in rgc.nu.items()})
    print("area:")
    for area_id, contents in rgc.area.items():
        print(f"  {area_id}: {sorted(list(contents))}")


def main():
    ap = argparse.ArgumentParser(description="Drawing → EGI converter")
    ap.add_argument("--input", required=True, help="Path to drawing JSON file")
    ap.add_argument("--layout", action="store_true", help="Attempt headless spatial layout")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text())
    rgc = drawing_to_relational_graph(data)

    summarize(rgc)

    if args.layout:
        try:
            engine = SpatialCorrespondenceEngine(rgc)
            layout = engine.generate_spatial_layout()
            print(f"\nLayout elements: {len(layout)}")
            # Print a compact summary by type counts
            counts = {}
            for k, v in layout.items():
                counts[v.element_type] = counts.get(v.element_type, 0) + 1
            print("By type:", counts)
        except AssertionError as e:
            print("\nLayout failed with assertion:", e)
        except Exception as e:
            print("\nLayout failed with error:", e)


if __name__ == "__main__":
    main()
