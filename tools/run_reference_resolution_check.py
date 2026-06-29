#!/usr/bin/env python3
"""Run the reference / transclusion validation harness on real candidates.

Builds reference candidates from the two substrates that *already* live in the
codebase and exercise the law ``RESOLVE ≡ INLINED-AND-ATTESTED`` without any
change to the protected core (see ``src/reference_resolution_check.py``):

  1. **Definition references** (intra-graph) — a defined-relation spot pointing at
     a body defined elsewhere (``definitions.py``).  The reference node in
     miniature: ``resolve`` = ``expand`` / ``expand_at``; the independent inlining
     is the hand-authored raw math fixture; the inverse is ``fold``.

  2. **Transclusion references** (inter-graph) — a graph that pulls in another
     graph *by name* the way ``cl_import_resolver`` does: assemble the referenced
     module's text and parse once.  ``resolve`` re-inlines the named module; the
     independent inlining is the same content authored directly in a different
     order (sheet conjunction is order-free, so this is a real, non-trivial
     ``same_graph`` test); an unresolved import demonstrates the honest horizon.

Usage:  uv run python tools/run_reference_resolution_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from definitions import Definition, DefinitionRegistry, expand, expand_at, fold
from egif_parser_dau import parse_egif
from reference_resolution_check import Reference, run_reference


# --- the math definitions + their independent raw fixtures (mirror tests/) --- #

SUBSET = Definition("subset", ("z", "x"), "[*z] [*x] ~[ [*w] (in w z) ~[ (in w x) ] ]")
EMPTY = Definition("empty", ("e",), "[*e] ~[ [*z] (in z e) ]")
SUCC = Definition(
    "succ",
    ("x", "s"),
    "[*x] [*s] ~[ [*w] ~[ ~[ (in w s) ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ] ] "
    "                     ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ~[ (in w s) ] ] ] ]",
)

POWER_SET_DEFINED = "~[ [*x] ~[ [*y] ~[ [*z] (subset z x) ~[ (in z y) ] ] ] ]"
POWER_SET_RAW = (
    "~[ [*x] ~[ [*y] "
    "   ~[ [*z] ~[ [*w] (in w z) ~[ (in w x) ] ] "
    "            ~[ (in z y) ] ] ] ]"
)
INFINITY_DEFINED = (
    "[*I] [*e] (empty e) (in e I) "
    "~[ [*x] (in x I) ~[ [*s] (in s I) (succ x s) ] ]"
)
INFINITY_RAW = (
    "[*I] "
    "  [*e] (in e I) ~[ [*z] (in z e) ] "
    "  ~[ [*x] (in x I) "
    "     ~[ [*s] (in s I) "
    "        ~[ [*w] ~[ ~[ (in w s) ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ] ] "
    "                   ~[ ~[ ~[ (in w x) ] ~[ (= w x) ] ] ~[ (in w s) ] ] ] ] ] ]"
)


def _subset_edge(egi):
    return next(eid for eid, rel in egi.rel.items() if rel == "subset")


def definition_candidates():
    """Two definition references: Power Set (local expand_at, recoverable via
    fold) and Infinity (whole-graph expand of *several* references at once)."""
    # --- Power Set: one spot, the full law incl. R3 recoverability --------- #
    reg = DefinitionRegistry([SUBSET])
    host = parse_egif(POWER_SET_DEFINED)
    edge = _subset_edge(host)
    resolved, fold_point = expand_at(host, reg, edge, return_fold_point=True)
    power_set = Reference(
        name="subset@power_set",
        origin="definition:subset",
        resolve=lambda r=resolved: r,
        inlined=parse_egif(POWER_SET_RAW),
        host=host,
        refold=lambda r, fp=fold_point: fold(r, fp),
    )

    # --- Infinity: two definitions resolved by the whole-graph expand ------- #
    reg2 = DefinitionRegistry([EMPTY, SUCC])
    host2 = parse_egif(INFINITY_DEFINED)
    infinity = Reference(
        name="empty+succ@infinity",
        origin="definition:empty,succ",
        resolve=lambda h=host2, r=reg2: expand(h, r),
        inlined=parse_egif(INFINITY_RAW),
    )
    return [power_set, infinity]


def transclusion_candidates():
    """A transclusion reference modeling cl-imports: a root that pulls in a named
    module by assembling its text and parsing once — with one unresolved import
    to exercise the honest horizon."""
    # The referenced modules, as a tiny name → EGIF "registry" (cl_import_resolver
    # does exactly this with CLIF text + an IRI resolver).
    modules = {
        "mammals": "~[ (mammal *x) ~[ (warmblooded x) ] ]",
        "a_dog": "(dog *d) (mammal d)",
    }
    root_body = "(P)"
    requested = ["mammals", "a_dog", "no_such_module"]

    def resolve():
        # Assemble the root + every resolvable module's text at the sheet level
        # (cl-imports = conjunction on the common sheet), then parse once.
        parts = [root_body] + [modules[m] for m in requested if m in modules]
        return parse_egif(" ".join(parts))

    # The independent inlining: the same content authored *directly*, in a
    # different order (sheet conjunction is order-free → same_graph must hold).
    inlined = parse_egif(
        "(dog *d) (mammal d) ~[ (mammal *x) ~[ (warmblooded x) ] ] (P)"
    )
    unresolved = [m for m in requested if m not in modules]

    return [
        Reference(
            name="root⊃{mammals,a_dog}",
            origin="transclusion:in-memory-modules",
            resolve=resolve,
            inlined=inlined,
            unresolved=unresolved,
        )
    ]


def _layout_fn():
    """Real ELK layout, wired in by the runner so the pure module stays
    geometry-free.  Returns None if the layout/web extras aren't installed (R2 is
    then skipped and declared, not failed)."""
    try:
        from elk_layout_engine import ELKLayoutEngine
        from style_loader import load_default_style

        engine = ELKLayoutEngine()
        style = load_default_style()
        return lambda egi: engine.generate_layout(egi, style)
    except Exception as exc:  # noqa: BLE001 — degrade honestly
        print(f"  (layout engine unavailable — R2 skipped: {exc})\n")
        return None


def main():
    layout_fn = _layout_fn()
    candidates = definition_candidates() + transclusion_candidates()

    print("Reference / transclusion validation harness")
    print("law: RESOLVE ≡ INLINED-AND-ATTESTED\n")

    all_ok = True
    for ref in candidates:
        report = run_reference(ref, layout_fn=layout_fn)
        all_ok = all_ok and report.ok
        mark = "PASS" if report.ok else "FAIL"
        print(f"[{mark}] {report.name}   ({report.origin})")
        print(f"       R1 resolve≡inline : {report.resolve_equals_inline}")
        print(f"       R2 resolved-attested: {report.resolved_attested}")
        rec = "n/a" if report.recoverable is None else report.recoverable
        print(f"       R3 recoverable     : {rec}")
        if report.unresolved:
            print(f"       R4 horizon (named) : {report.unresolved}")
        for f in report.failures:
            print(f"       {f.strip()}")
        for lim in report.honest_limits:
            print(f"       · {lim}")
        print()

    print("=" * 60)
    print("ALL PASS — the reference law holds on every candidate."
          if all_ok else "SOME FAILED — see above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
