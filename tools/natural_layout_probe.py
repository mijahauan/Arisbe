"""
Natural-layout probe (step 1, additive / read-only).

Compares each ligature's REQUIRED crossing structure — from the
coordinate-free ``natural_layout(egi)`` — against the ACTUAL crossings
in the rendered ``LayoutDTO``, across the tomos corpus.  Touches no
existing code path; it is an evidence-gathering instrument, not a
behaviour change.

It answers the question that decides how much work the NaturalLayout
refactor is:

    Where does today's rendering PASS the existing §3.3 attestation
    (which samples area membership at points/midpoints) but FAIL the
    stronger crossing-multiset-equality check?

For each rendered ligature and each cut, "actual crossings" = the
number of times the polyline crosses that cut's boundary rectangle.
Then:

  - unauthorized cut with actual > 0          → illegitimate crossing
    (the canonical bug: the line enters an area it has no business in);
  - authorized cut with actual != 1           → wrong parity
    (missing crossing, or crosses-and-returns).

The geometry lives HERE (projection side), never in ``natural_layout``.

Run:  uv run python tools/natural_layout_probe.py
"""

import sys
from pathlib import Path

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from layout_dto import BoundingBox, Point
from natural_layout import natural_layout
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
from correspondence_attestation import check_correspondence
from tomos_service import TomosService


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


# --------------------------------------------------------------------------- #
# Geometry — count true boundary crossings of a polyline vs an AABB.          #
# A convex rect bounds a straight segment to 0/1/2 boundary crossings,        #
# decided by endpoint membership (1 if they differ) or by edge               #
# intersections when both endpoints are outside (0 or 2 for a pass-through).  #
# --------------------------------------------------------------------------- #


def _inside(p: Point, b: BoundingBox) -> bool:
    return b.min_x <= p.x <= b.max_x and b.min_y <= p.y <= b.max_y


def _orient(ax, ay, bx, by, cx, cy) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _proper_intersect(ax, ay, bx, by, cx, cy, dx, dy) -> bool:
    d1 = _orient(cx, cy, dx, dy, ax, ay)
    d2 = _orient(cx, cy, dx, dy, bx, by)
    d3 = _orient(ax, ay, bx, by, cx, cy)
    d4 = _orient(ax, ay, bx, by, dx, dy)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _outside_edge_crossings(a: Point, b: Point, r: BoundingBox) -> int:
    edges = [
        (r.min_x, r.min_y, r.max_x, r.min_y),
        (r.max_x, r.min_y, r.max_x, r.max_y),
        (r.max_x, r.max_y, r.min_x, r.max_y),
        (r.min_x, r.max_y, r.min_x, r.min_y),
    ]
    return sum(
        1
        for (x1, y1, x2, y2) in edges
        if _proper_intersect(a.x, a.y, b.x, b.y, x1, y1, x2, y2)
    )


def count_boundary_crossings(points, rect: BoundingBox) -> int:
    total = 0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        ai, bi = _inside(a, rect), _inside(b, rect)
        if ai != bi:
            total += 1
        elif not ai and not bi:
            total += _outside_edge_crossings(a, b, rect)
    return total


# --------------------------------------------------------------------------- #
# Probe                                                                       #
# --------------------------------------------------------------------------- #


def probe_uod(egi):
    """Return (n_ligatures, illegit, wrong_parity) violation lists for one EGI."""
    engine = ELKLayoutEngine()
    dto = engine.generate_layout(egi, load_default_style())

    nat = natural_layout(egi)
    cut_ids = {c.id for c in egi.Cut}

    # Index rendered paths by (predicate, vertex, port).
    paths = {
        (p.predicate_id, p.vertex_id, p.port_index): p.points
        for p in dto.ligature_paths
    }

    illegit = []        # (pred, vertex, cut, actual)  unauthorized & crossed
    wrong_parity = []    # (pred, vertex, cut, actual)  authorized & actual != 1

    for lig in nat.ligatures:
        key = (lig.predicate_id, lig.vertex_id, lig.port_index)
        pts = paths.get(key)
        if pts is None or len(pts) < 2:
            continue
        required = set(lig.required_crossings)
        for cid in cut_ids:
            bounds = dto.cut_bounds.get(cid)
            if bounds is None:
                continue
            actual = count_boundary_crossings(pts, bounds)
            if cid in required:
                if actual != 1:
                    wrong_parity.append((lig.predicate_id, lig.vertex_id, cid, actual))
            else:
                if actual > 0:
                    illegit.append((lig.predicate_id, lig.vertex_id, cid, actual))

    return len(nat.ligatures), illegit, wrong_parity


# Deliberately pathological shapes — the cases the corpus may not
# exercise but where logic→2-D projection is thinnest (spec §5.2/§5.3).
STRESS_CASES = [
    ("deep-3",        "(P *x) ~[ ~[ ~[ (R x) ] ] ]"),
    ("siblings",      "(P *x) ~[ (Q x) ] ~[ (R x) ]"),
    ("siblings-deep", "(P *x) ~[ ~[ (Q x) ] ] ~[ (R x) ]"),
    ("branch-in-cut", "(P *x) ~[ (Q x) (S x) ]"),
    ("two-vars",      "(P *x) ~[ (Q x) (R *y) ~[ (S y) ] ]"),
    ("nested-mix",    "(A *x) ~[ (B x) (D *y) ~[ (C x) (E y) ] ]"),
]


def _large_cases():
    """Generated larger graphs — vigilance for scale-induced trouble.

    - deep-N:  a vertex on the sheet referenced N cuts deep (one ligature
      crossing N boundaries).
    - wide-M:  M sibling cuts each referencing the same sheet-level vertex
      (M ligatures, sibling-spanning W-class).
    - comb-D:  D nested cuts, each containing a predicate referencing the
      sheet-level vertex (D ligatures crossing 1..D boundaries).
    """
    cases = []
    for n in (8, 12, 20):
        cases.append(
            (f"deep-{n}", "(P *x) " + "~[ " * n + "(R x) " + "] " * n)
        )
    for m in (8, 12, 20):
        cases.append((f"wide-{m}", "(P *x) " + "~[ (Q x) ] " * m))
    for d in (6, 10):
        cases.append((f"comb-{d}", "(P *x) " + "~[ (R x) " * d + "]" * d))
    return cases


def probe_stress():
    from egif_parser_dau import parse_egif

    print("\n" + "=" * 70)
    print("STRESS CASES — synthetic pathological shapes")
    print("=" * 70)
    for label, egif in STRESS_CASES + _large_cases():
        try:
            egi = parse_egif(egif)
            n, illegit, parity = probe_uod(egi)
            status = "ok" if not illegit and not parity else "VIOLATION"
            print(f"  {label:16s} ligs={n:2d}  illegit={len(illegit)} "
                  f"parity={len(parity)}  [{status}]  {egif}")
            for pred, vert, cut, actual in illegit:
                print(f"      illegit: {pred}->{vert} crosses forbidden {cut} "
                      f"x{actual}")
            for pred, vert, cut, actual in parity:
                print(f"      parity:  {pred}->{vert} crosses authorized {cut} "
                      f"x{actual} (want 1)")
        except Exception as exc:  # noqa: BLE001
            print(f"  {label:16s} ERROR {type(exc).__name__}: {str(exc)[:60]}")


def main():
    tomos = TomosService(TOMOS_ROOT)
    uod_ids = [u["uod_id"] for u in tomos.list_uods()]

    total_ligs = 0
    total_illegit = 0
    total_parity = 0
    uods_with_illegit = []
    uods_with_parity = []
    hidden = []          # passes existing attestation but probe finds a violation
    errored = []

    for uid in uod_ids:
        try:
            uod = tomos.load_uod(uid)
            if uod is None or uod.current_egi is None:
                continue
            egi = uod.current_egi
            if not egi.Cut:
                # No cuts → no crossing constraints to probe.
                n, illegit, parity = len(natural_layout(egi).ligatures), [], []
            else:
                n, illegit, parity = probe_uod(egi)

            total_ligs += n
            total_illegit += len(illegit)
            total_parity += len(parity)
            if illegit:
                uods_with_illegit.append((uid, len(illegit)))
            if parity:
                uods_with_parity.append((uid, len(parity)))

            if illegit or parity:
                # Did the existing sampled attestation also catch it?
                from elk_layout_engine import ELKLayoutEngine as _E
                dto = _E().generate_layout(egi, load_default_style())
                existing = check_correspondence(egi, dto)
                identity = [f for f in existing if "identity" in f]
                if not identity:
                    hidden.append((uid, len(illegit), len(parity)))
        except Exception as exc:  # noqa: BLE001 — probe should never hard-fail
            errored.append((uid, type(exc).__name__ + ": " + str(exc)[:80]))

    print("=" * 70)
    print("NATURAL-LAYOUT PROBE — crossing-multiset equality vs current render")
    print("=" * 70)
    print(f"UoDs probed:                 {len(uod_ids)}")
    print(f"Total ligature incidences:   {total_ligs}")
    print(f"Illegitimate crossings:      {total_illegit}  "
          f"(in {len(uods_with_illegit)} UoDs)")
    print(f"Wrong-parity crossings:      {total_parity}  "
          f"(in {len(uods_with_parity)} UoDs)")
    print(f"HIDDEN (probe flags, sampled §3.3 identity does not): {len(hidden)} UoDs")
    if errored:
        print(f"Errored (skipped):           {len(errored)}")
    print("-" * 70)

    if uods_with_illegit:
        print("\nUoDs with illegitimate crossings (line enters a forbidden area):")
        for uid, n in sorted(uods_with_illegit, key=lambda x: -x[1])[:20]:
            print(f"  {uid:40s} {n} crossing(s)")
    if uods_with_parity:
        print("\nUoDs with wrong-parity crossings (authorized cut not crossed once):")
        for uid, n in sorted(uods_with_parity, key=lambda x: -x[1])[:20]:
            print(f"  {uid:40s} {n} crossing(s)")
    if hidden:
        print("\nHIDDEN cases — current sampled identity check passes, probe fails:")
        for uid, ni, npar in hidden[:20]:
            print(f"  {uid:40s} illegit={ni} parity={npar}")
    if errored:
        print("\nErrored UoDs (skipped, not counted as violations):")
        for uid, msg in errored[:20]:
            print(f"  {uid:40s} {msg}")
    print("=" * 70)

    probe_stress()


if __name__ == "__main__":
    main()
