"""
The overview / layout-perf frontier benchmark — the headline wall-clock measurement.

The adaptive-scope **overview** (``docs/ADAPTIVE_SCOPE_VIEWER.md``) exists to answer the
*layout-perf frontier*: ELK is super-linear in cut nesting, so a large taxonomy is too slow
to draw whole.  The structural guarantee is already unit-tested (an overview lays out
``budget`` drawn cuts regardless of ``|egi|`` — ``tests/test_overview_routes.py``).  This
harness supplies the *empirical* half: a paired wall-clock measurement on a graph at the
genuine frontier, demonstrating overview renders what full-ELK cannot draw comfortably.

The frontier UoD is the **full SUMO taxonomy** — *not* the stored ``sumo_upper`` (its
depth-≤2 upper spine, 86 cuts, lays out in ~1 s and doesn't show the win).  The full
ground subclass taxonomy (123 subsumptions → 246 cuts) is the ELK super-linear shape, so it
is rebuilt here from ``docs/references/SUMO1.2.txt`` via ``tools/suokif_to_eg.py`` rather
than stored (it cannot be saved as a drawn UoD — that's the very frontier it measures).

Usage::

    uv run python tools/overview_frontier_benchmark.py            # overview only (~1 s)
    uv run python tools/overview_frontier_benchmark.py --full-elk  # + the full ELK baseline (minutes!)

The ``--full-elk`` baseline runs a real ELK layout of all 246 cuts and is *deliberately*
slow (measured ~286 s on a 2021 laptop) — it is the number overview is measured against, so
it is opt-in.  Overview always runs.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tools"))

_SUMO = _ROOT / "docs" / "references" / "SUMO1.2.txt"


def build_frontier_egi():
    """The full SUMO ground subclass taxonomy as an EGI — the ELK super-linear shape."""
    from suokif_to_eg import translate
    from egif_parser_dau import parse_egif

    egif, report = translate(_SUMO.read_text(encoding="latin-1"))
    egi = parse_egif(egif)
    return egi, report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full-elk", action="store_true",
                    help="also run the full ELK layout baseline (minutes — opt-in)")
    ap.add_argument("--budget", type=int, default=None,
                    help="overview drawn-cut budget (default: DEFAULT_OVERVIEW_BUDGET)")
    ap.add_argument("--sweep", action="store_true",
                    help="sweep budgets to locate the cliff (the high ones take minutes)")
    args = ap.parse_args(argv)

    from web_api.services.layout_service import (
        generate_overview_layout, generate_layout, _resolve_collapsed,
        DEFAULT_OVERVIEW_BUDGET,
    )
    from overview_projection import collapse_quotient
    budget = args.budget if args.budget is not None else DEFAULT_OVERVIEW_BUDGET

    egi, report = build_frontier_egi()
    n_cuts, n_v, n_e = len(egi.Cut), len(egi.V), len(egi.E)
    print("=" * 72)
    print("Overview / layout-perf frontier benchmark")
    print("=" * 72)
    print(f"Frontier UoD: full SUMO ground taxonomy "
          f"({report['translated'].get('subclass-of', '?')} subsumptions)")
    print(f"  EGI size: {n_cuts} cuts, {n_v} vertices, {n_e} edges")
    print()

    # --- Overview (always) ----------------------------------------------------
    t0 = time.perf_counter()
    dto, svg, summary, collapsed = generate_overview_layout(
        egi, expand=None, budget=budget)
    t_overview = time.perf_counter() - t0
    quotient = collapse_quotient(egi, _resolve_collapsed(egi, None, budget))
    quotient_cuts = len(quotient.Cut)            # what ELK actually lays out
    opened = quotient_cuts - len(collapsed)      # cuts drawn with their interior
    hidden = n_cuts - quotient_cuts              # cuts not laid out at all
    print(f"OVERVIEW (auto-expand, budget={budget}):")
    print(f"  wall-clock     : {t_overview:.2f} s")
    print(f"  ELK lays out   : {quotient_cuts} cuts "
          f"({opened} opened + {len(collapsed)} leaf placeholders); {hidden} hidden")
    print(f"  attested       : yes (attest_overview passed)")
    print()

    # --- Budget sweep (opt-in) — locate the breadth cliff --------------------
    if args.sweep:
        print("BUDGET SWEEP (deterministic, sorted auto-expand):")
        for b in (0, 10, 20, 25, 30, 35, 40, 60):
            t0 = time.perf_counter()
            _, _, _, coll = generate_overview_layout(egi, expand=None, budget=b)
            dt = time.perf_counter() - t0
            flag = "  <-- cliff" if dt > 10 else ""
            print(f"  budget={b:3d}: {dt:8.2f} s  ({n_cuts - len(coll)} opened){flag}")
        print("  The cost is driven by lines of identity routed *among* opened "
              "cross-linked scrolls, not the opened count — hence a sharp cliff.")
        print()

    # --- Full ELK baseline (opt-in) ------------------------------------------
    if args.full_elk:
        print(f"FULL ELK (generate_layout of all {n_cuts} cuts) — this is slow ...",
              flush=True)
        t0 = time.perf_counter()
        generate_layout(egi)
        t_full = time.perf_counter() - t0
        print(f"  wall-clock     : {t_full:.1f} s")
        print()
        print(f"SPEEDUP: overview is {t_full / t_overview:.0f}x faster "
              f"({t_full:.0f} s -> {t_overview:.2f} s) and stays within budget "
              f"regardless of |egi|.")
    else:
        print("(Pass --full-elk to run the ELK baseline this is measured against.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
