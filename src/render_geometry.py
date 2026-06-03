"""
render_geometry — pure 2-D projection geometry shared by the SVG and TikZ
renderers, so a graph's hand-drawn *manifest* is computed once and the two
renderers' "hands" agree exactly.

Everything here is **deterministic** (hash-seeded, never salted ``hash`` /
``Date`` / ``random``) and **stroke-only**: it shapes how the authorized
``LayoutDTO`` geometry is *drawn* — the curve of a line of identity, the
waver of a hand-drawn stroke, the hop where two lines cross — never the DTO
geometry that §3.3 reads (which is attested before any renderer runs).

The bridge piece is §3.0's worked example
(docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md): Peirce's hop is exactly the
convention that *recovers a distinction a 2-D projection would otherwise
collapse* — two distinct lines of identity sharing a point in the picture
yet staying distinct.
"""

import hashlib
import math
from collections import namedtuple

Point = namedtuple("Point", "x y")

# A detected crossing of two distinct lines of identity in the projection:
# the crossing point and the unit directions of the over- and under-line.
Crossing = namedtuple("Crossing", "point over_dir under_dir")

# The geometry of one hop drawn at a crossing — endpoints and Bézier
# controls of the over-line arc, plus the short straight under-line that is
# restored straight through the crossing.  All in DTO coordinates.
Bridge = namedtuple("Bridge", "a b c1 c2 under_a under_b")


def jitter(seed: str, i: int) -> float:
    """A deterministic pseudo-random value in [-1, 1] from (seed, i).

    Uses md5 (not Python's salted ``hash``) so the same element wobbles the
    same way on every render, across processes, and across the SVG and TikZ
    renderers — the "hand" is stable and layout reproducibility (invariant
    L1) is preserved."""
    h = hashlib.md5(f"{seed}|{i}".encode()).digest()
    return (int.from_bytes(h[:4], "big") / 0xFFFFFFFF) * 2.0 - 1.0


def hand_drawn_points(points, amplitude: float, seed: str):
    """Nudge each *interior* point perpendicular to the local direction by a
    deterministic amount ≤ ``amplitude``.  Endpoints are untouched so the
    line still meets its hook and vertex exactly.  Input/output are any
    objects with ``.x`` / ``.y`` (output is :data:`Point`)."""
    pts = list(points)
    if len(pts) < 3 or amplitude <= 0:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        prev, cur, nxt = pts[i - 1], pts[i], pts[i + 1]
        dx, dy = nxt.x - prev.x, nxt.y - prev.y
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length  # unit perpendicular
        j = amplitude * jitter(seed, i)
        out.append(Point(cur.x + nx * j, cur.y + ny * j))
    out.append(pts[-1])
    return out


def catmull_rom_segments(pts):
    """Catmull-Rom (tension 1/6) cubic-Bézier control points through ``pts``
    (list of ``(x, y)`` tuples, already offset).  Returns a list of
    ``(c1, c2, end)`` tuples, one per segment from ``pts[0]`` — Peirce's
    flowing line of identity.  The curve interpolates *every* layout point,
    so it stays close to the authorized polyline (no new cut crossings).

    Shared by the SVG (``M … C …``) and TikZ (``.. controls … and … ..``)
    renderers so their flowing lines agree."""
    n = len(pts)
    segs = []
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        segs.append((c1, c2, p2))
    return segs


def _unit(dx: float, dy: float):
    length = math.hypot(dx, dy) or 1.0
    return (dx / length, dy / length)


def _segment_crossing(p1, p2, p3, p4, eps: float = 1e-6):
    """Proper (interior) intersection of segments p1p2 and p3p4, or ``None``.

    Returns the intersection point only when both parameters lie strictly
    inside ``(eps, 1 - eps)`` — segments that merely share an endpoint (a
    common vertex or hook) are *not* a crossing to bridge."""
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = p4[0] - p3[0], p4[1] - p3[1]
    denom = rx * sy - ry * sx
    if abs(denom) < eps:
        return None  # parallel or collinear
    qx, qy = p3[0] - p1[0], p3[1] - p1[1]
    t = (qx * sy - qy * sx) / denom
    u = (qx * ry - qy * rx) / denom
    if eps < t < 1.0 - eps and eps < u < 1.0 - eps:
        return (p1[0] + t * rx, p1[1] + t * ry)
    return None


def ligature_crossings(ligature_paths, min_sep: float = 6.0):
    """Where two *distinct* lines of identity cross in the 2-D projection.

    "Distinct" = different ``vertex_id``: paths sharing a vertex are one line
    of identity (the same W-partition class), and their meeting is not a
    crossing to bridge.  Returns a **deterministic** list of :data:`Crossing`
    records — iteration follows DTO order, the over-line is whichever path's
    ``(vertex_id, predicate_id, port_index)`` key sorts higher (stable across
    renders and across SVG/TikZ), and near-coincident crossings (within
    ``min_sep``) are collapsed to one hop.

    Detection runs on the authorized DTO polylines (``lig.points``), not the
    drawn curve/waver — the bridge marks the genuine projection crossing and
    the hand-drawn stroke passes close by.  This is the detection behind
    ``Conventions.ligature_crossing_marks = "bridges"``."""
    paths = [p for p in ligature_paths if len(p.points) >= 2]
    found = []
    for a in range(len(paths)):
        for b in range(a + 1, len(paths)):
            pa, pb = paths[a], paths[b]
            if pa.vertex_id == pb.vertex_id:
                continue
            key_a = (pa.vertex_id, pa.predicate_id, pa.port_index)
            key_b = (pb.vertex_id, pb.predicate_id, pb.port_index)
            for i in range(len(pa.points) - 1):
                a1, a2 = pa.points[i], pa.points[i + 1]
                for j in range(len(pb.points) - 1):
                    b1, b2 = pb.points[j], pb.points[j + 1]
                    x = _segment_crossing(
                        (a1.x, a1.y), (a2.x, a2.y), (b1.x, b1.y), (b2.x, b2.y)
                    )
                    if x is None:
                        continue
                    da = _unit(a2.x - a1.x, a2.y - a1.y)
                    db = _unit(b2.x - b1.x, b2.y - b1.y)
                    over, under = (da, db) if key_a >= key_b else (db, da)
                    found.append(Crossing(Point(*x), over, under))
    deduped = []
    for c in found:
        if any(
            math.hypot(c.point.x - d.point.x, c.point.y - d.point.y) < min_sep
            for d in deduped
        ):
            continue
        deduped.append(c)
    return deduped


def bridge_path(crossing: Crossing, radius: float) -> Bridge:
    """Geometry of a single hop at ``crossing``.

    The over-line is lifted into a smooth semicircular arc (cubic Bézier) of
    the given radius, bulging to one deterministic side; the under-line is
    restored straight through the crossing so it reads as continuous.
    Endpoints and controls are in DTO coordinates — each renderer applies
    its own offset (SVG) or none (TikZ) when drawing."""
    x, y = crossing.point
    ux, uy = crossing.over_dir
    vx, vy = crossing.under_dir
    a = (x - radius * ux, y - radius * uy)
    b = (x + radius * ux, y + radius * uy)
    nx, ny = -uy, ux  # perpendicular to the over-line; bulge toward +n
    k = 1.3 * radius
    c1 = (a[0] + nx * k, a[1] + ny * k)
    c2 = (b[0] + nx * k, b[1] + ny * k)
    under_a = (x - radius * vx, y - radius * vy)
    under_b = (x + radius * vx, y + radius * vy)
    return Bridge(a, b, c1, c2, under_a, under_b)


__all__ = [
    "Point", "Crossing", "Bridge",
    "jitter", "hand_drawn_points", "catmull_rom_segments",
    "ligature_crossings", "bridge_path",
]
