"""
EGI JSON serialization utilities.

Schema produced/consumed matches tools/migrate_corpus_to_egi.py
egi_to_dict, less ``alphabet`` and ``rho``.

**Those two keys were removed from the schema on 2026-09-25**, as the IO half of
the ruling that made them derived rather than stored (egi_core_dau, 2026-09-24).
The argument is the same one, applied one level out: a file is a store, and a
stored copy of a derivable fact is two records of one fact. Keeping the keys
would have been harmless only because load throws them away — which is another
way of saying a hand-edited or hand-written file could carry an alphabet that
disagrees with its own ink and nothing would ever say so.

It loses nothing, and that was measured rather than assumed before the keys
went: of 245 corpus ``.egi.json`` files, 27 carried a stored alphabet, **none**
declared a relation or a constant it did not use, and no stored rho disagreed
with its ink.

What it does NOT settle, and what the keys were never able to settle either: a
UoD's alphabet — the *language* a diachronic discourse is conducted in, which
persists across states where a per-state alphabet cannot (an individual leaving
the sheet is not a word leaving the discourse; Dau's Σ is something a graph is
*over*, Def 12.7/23.1, and his rules hold it fixed). That belongs to the UoD,
not to a snapshot, and no such field exists yet. Emptying this slot is what
keeps it from being mistaken for one. See CLAUDE.md, ``egi_core_dau``.

A file that still carries either key loads correctly and the key is ignored —
required, since ~99k run artifacts under the gitignored ``runs/`` carry them.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


def to_dict(egi: RelationalGraphWithCuts) -> Dict[str, Any]:
    d = {
        "sheet": egi.sheet,
        "V": [{"id": v.id, "label": v.label, "is_generic": v.is_generic} for v in sorted(egi.V, key=lambda x: x.id)],
        "E": [{"id": e.id} for e in sorted(egi.E, key=lambda x: x.id)],
        "Cut": [{"id": c.id} for c in sorted(egi.Cut, key=lambda x: x.id)],
        "nu": {k: list(v) for k, v in sorted(egi.nu.items())},
        "rel": dict(sorted(egi.rel.items())),
        "area": {k: sorted(list(v)) for k, v in sorted(egi.area.items())},
    }
    # No "alphabet" and no "rho": both are derived from the ink above, so
    # writing them would record one fact twice. See the module docstring.
    # Second-order maps (B-min): emitted only when non-empty, so a first-order
    # graph's JSON is byte-identical to the pre-B-min schema.
    if egi.sort:
        d["sort"] = {k: v for k, v in sorted(egi.sort.items())}
    if egi.quotation:
        d["quotation"] = {k: v for k, v in sorted(egi.quotation.items())}
    return d


def from_dict(d: Dict[str, Any]) -> RelationalGraphWithCuts:
    V = frozenset(Vertex(id=vi["id"], label=vi.get("label"), is_generic=bool(vi.get("is_generic", True))) for vi in d.get("V", []))
    E = frozenset(Edge(id=ei["id"]) for ei in d.get("E", []))
    Cutset = frozenset(Cut(id=ci["id"]) for ci in d.get("Cut", []))
    nu = frozendict({k: tuple(v) for k, v in d.get("nu", {}).items()})
    rel = frozendict(d.get("rel", {}))
    area = frozendict({k: frozenset(v) for k, v in d.get("area", {}).items()})
    # "alphabet" and "rho" are deliberately not read. An older file may carry
    # them; the core would discard whatever was passed anyway, so reading them
    # only created a place for a file to disagree with itself.
    sort = frozendict(d.get("sort", {}))
    quotation = frozendict(d.get("quotation", {}))
    return RelationalGraphWithCuts(
        V=V,
        E=E,
        nu=nu,
        sheet=d["sheet"],
        Cut=Cutset,
        area=area,
        rel=rel,
        sort=sort,
        quotation=quotation,
    )


def load_egi_json(path: str | Path) -> RelationalGraphWithCuts:
    import json
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return from_dict(data)


def save_egi_json(egi: RelationalGraphWithCuts, path: str | Path) -> None:
    import json
    p = Path(path)
    payload = to_dict(egi)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
