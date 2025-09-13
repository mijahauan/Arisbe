"""
EGI JSON serialization utilities.

Schema produced/consumed matches tools/migrate_corpus_to_egi.py egi_to_dict.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU


def to_dict(egi: RelationalGraphWithCuts) -> Dict[str, Any]:
    return {
        "sheet": egi.sheet,
        "V": [{"id": v.id, "label": v.label, "is_generic": v.is_generic} for v in sorted(egi.V, key=lambda x: x.id)],
        "E": [{"id": e.id} for e in sorted(egi.E, key=lambda x: x.id)],
        "Cut": [{"id": c.id} for c in sorted(egi.Cut, key=lambda x: x.id)],
        "nu": {k: list(v) for k, v in sorted(egi.nu.items())},
        "rel": dict(sorted(egi.rel.items())),
        "area": {k: sorted(list(v)) for k, v in sorted(egi.area.items())},
        "alphabet": None if egi.alphabet is None else {
            "C": sorted(list(egi.alphabet.C)),
            "F": sorted(list(egi.alphabet.F)),
            "R": sorted(list(egi.alphabet.R)),
            "ar": dict(egi.alphabet.ar),
        },
        "rho": {k: v for k, v in sorted(egi.rho.items())},
    }


def from_dict(d: Dict[str, Any]) -> RelationalGraphWithCuts:
    V = frozenset(Vertex(id=vi["id"], label=vi.get("label"), is_generic=bool(vi.get("is_generic", True))) for vi in d.get("V", []))
    E = frozenset(Edge(id=ei["id"]) for ei in d.get("E", []))
    Cutset = frozenset(Cut(id=ci["id"]) for ci in d.get("Cut", []))
    nu = frozendict({k: tuple(v) for k, v in d.get("nu", {}).items()})
    rel = frozendict(d.get("rel", {}))
    area = frozendict({k: frozenset(v) for k, v in d.get("area", {}).items()})
    alph_in = d.get("alphabet")
    alphabet = None
    if alph_in is not None:
        alphabet = AlphabetDAU(
            C=frozenset(alph_in.get("C", [])),
            F=frozenset(alph_in.get("F", [])),
            R=frozenset(alph_in.get("R", [])),
            ar=frozendict(alph_in.get("ar", {})),
        ).with_defaults()
    rho = frozendict(d.get("rho", {}))
    return RelationalGraphWithCuts(
        V=V,
        E=E,
        nu=nu,
        sheet=d["sheet"],
        Cut=Cutset,
        area=area,
        rel=rel,
        alphabet=alphabet,
        rho=rho,
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
