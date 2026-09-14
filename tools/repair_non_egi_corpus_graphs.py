"""Repair the two corpus graphs that are not EGIs (Dau Def 12.5, p.125).

`bfo_core` holds the generic vertex `v_x26`, and `colore_field` holds `v_zero`
and `v_one`, each placed in one cut while edges in *sibling* cuts use them. A
vertex must dominate every edge that uses it, so these stored graphs were never
EGIs — and that, not any linear form, is why their round trips failed: writing
them out and reading them back *repaired* them.

`vertex_scope.hoist_vertices_to_lca` performs exactly the repair: each vertex
moves outward to the least common area of its uses, which is the reading every
parser already applies.

**This is a choice of reading, not an inert renaming.** The "one constant, one
line" normalization argues its own inertness from a name denoting a single
individual; nothing of that argument transfers here, because
`hoist_vertices_to_lca` draws no generic/constant distinction and every vertex
moved in these two graphs is *generic*. A generic line's area sets its
quantifier's scope and polarity, so moving one would be a change of meaning —
if there were a meaning to change. There is not: neither stored structure is an
EGI, so Dau's semantics never assigned it one. What recommends the least-common-
area placement is that it is the reading every parser already applies to these
same graphs, and that all three round trips begin to hold once it is made.

Run once:

    uv run python tools/repair_non_egi_corpus_graphs.py --write

Without --write it reports what it would do and changes nothing. It refuses to
write a graph that is still not an EGI after the hoist, or whose EGIF, CGIF or
CLIF round trip does not then hold.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from clif_generator_dau import generate_clif
from clif_parser_dau import parse_clif
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from tomos_service import TomosService
from vertex_scope import hoist_vertices_to_lca

TOMOS = Path(__file__).resolve().parent.parent / "tomos"
GRAPHS = ("bfo_core", "colore_field")
FORMS = (("EGIF", generate_egif, parse_egif), ("CGIF", generate_cgif, parse_cgif),
         ("CLIF", generate_clif, parse_clif))


def dominating(graph) -> bool:
    for edge_id, sequence in graph.nu.items():
        chain, area = [], graph.get_context(edge_id)
        while True:
            chain.append(area)
            if area == graph.sheet:
                break
            area = graph.get_context(area)
        if any(graph.get_context(v) not in chain for v in sequence):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    service = TomosService(TOMOS)
    for uod_id in GRAPHS:
        uod = service.load_uod(uod_id, attest=False)
        before = uod.current_egi
        after = hoist_vertices_to_lca(before)
        moved = [v.id for v in after.V if after.get_context(v.id) != before.get_context(v.id)]
        print(f"{uod_id}: EGI {dominating(before)} -> {dominating(after)}; moved {moved}")
        if not dominating(after):
            print(f"  REFUSING {uod_id}: still not an EGI after the hoist")
            return 1
        for name, generate, parse in FORMS:
            if not nav.same_graph(after, parse(generate(after))):
                print(f"  REFUSING {uod_id}: the {name} round trip does not hold after the hoist")
                return 1
            print(f"  {name} round trip holds")
        if args.write:
            uod.current_egi = after
            uod._current_egif = uod._current_cgif = uod._current_clif = None
            service.save_uod(uod)
            print(f"  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
