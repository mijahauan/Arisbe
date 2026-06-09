"""The graph-with-holes (schema) node — the one genuinely new primitive the math
arc adds on top of Peirce's five rules.

A **schema** is a Beta graph plus ≥1 *holes*.  A hole is a placeholder edge whose
relation name is declared a hole; every occurrence of the same hole name shares
one identity, so a single instantiation fills all of them.  This is what lets
Beta store ZFC's Separation/Replacement and Peirce's induction (the least-number
principle) as *finitely many* hole-bearing graphs — first-order EG cannot
quantify over formulas, so a schema cannot be one ordinary graph.

The schema stays on the **Beta side of the Beta/Gamma boundary** by a deliberate
dodge: it does not quantify over formulas *inside* the logic.  It is a metalevel
*generator* — a template plus an external rule (:func:`instance_of_schema`) that
licenses asserting any concrete instance.  Every instance
(:func:`instantiate`) is a pure Dau-Beta graph, exactly as ZFC/PA's schemas
generate ordinary first-order axioms.  See
``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` Part III + III-bis.

Consistency contract (III-bis, rule 2): the **instance** is the round-trippable
unit, not the schema.  The ``⟨…⟩`` hole token is an Arisbe extension to EGIF
(handled wrapper-side here so the protected EGIF parser is untouched); Common
Logic / CGIF are first-order and have no schema construct, so a schema is **never**
exported as a single first-order sentence — only its instances are.

Instantiation reuses the shared :func:`eg_splice.splice`: for each occurrence,
splice a fresh copy of the filler ``g`` welding ``g``'s ports onto that
occurrence's arguments — which is why ZFC Replacement's per-occurrence port
relabeling (``?y`` vs ``?y2``) falls out for free.

Touches no protected module.
"""

import re
from typing import Dict, List, Optional, Sequence, Tuple, Union

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from eg_splice import splice


# ⟨name: a b c⟩  — the hole token (Arisbe extension; desugared to (name a b c)).
_HOLE_RE = re.compile(r"⟨\s*([^:⟩]+?)\s*:\s*([^⟩]*?)\s*⟩")


def desugar_holes(egif_with_holes: str) -> Tuple[str, Dict[str, int]]:
    """Rewrite ``⟨φ: a b⟩`` hole tokens to ordinary ``(φ a b)`` relations and
    collect ``{hole_name: arity}``.  Raises if a hole name appears at inconsistent
    arity (its arity must be fixed even though its arguments vary per occurrence).
    """
    holes: Dict[str, int] = {}

    def repl(m: "re.Match") -> str:
        name = m.group(1).strip()
        args = m.group(2).split()
        if name in holes and holes[name] != len(args):
            raise ValueError(
                f"hole {name!r} used at inconsistent arity "
                f"({holes[name]} vs {len(args)})"
            )
        holes[name] = len(args)
        return "(" + name + (" " + " ".join(args) if args else "") + ")"

    return _HOLE_RE.sub(repl, egif_with_holes), holes


def resugar_holes(egif: str, holes: Dict[str, int]) -> str:
    """Inverse of :func:`desugar_holes`: rewrite ``(name a b)`` back to
    ``⟨name: a b⟩`` for each declared hole name (hole args are simple lines, no
    nested parens)."""
    out = egif
    for name in holes:
        pat = re.compile(r"\(\s*" + re.escape(name) + r"\b\s*([^()]*?)\s*\)")
        out = pat.sub(lambda m: "⟨" + name + ": " + m.group(1).strip() + "⟩", out)
    return out


class Schema:
    """A Beta graph (``egi``) plus its hole declarations (``holes``: name → arity).

    The holes' relation names live in ``egi`` like ordinary relations; ``holes``
    is what marks them as placeholders to be filled, never asserted as relations.
    """

    def __init__(self, egi: RelationalGraphWithCuts, holes: Dict[str, int]):
        self.egi = egi
        self.holes = dict(holes)
        # every declared hole must actually occur, at its declared arity
        for name, arity in self.holes.items():
            occ = self.occurrences(name)
            if not occ:
                raise ValueError(f"declared hole {name!r} does not occur in the graph")
            for eid in occ:
                if len(egi.nu[eid]) != arity:
                    raise ValueError(
                        f"hole {name!r} occurs at arity {len(egi.nu[eid])}, "
                        f"declared {arity}"
                    )

    @classmethod
    def from_egif(cls, egif_with_holes: str) -> "Schema":
        """Parse schema EGIF written with ``⟨name: args⟩`` hole tokens."""
        rewritten, holes = desugar_holes(egif_with_holes)
        return cls(parse_egif(rewritten), holes)

    def to_egif(self) -> str:
        """Serialize as Arisbe-native EGIF, re-sugaring holes to ``⟨name: args⟩``.

        Allowed (rule 2 of the III-bis contract): EGIF is Arisbe-native and the
        ``⟨…⟩`` token is our extension.  Round-trips: ``Schema.from_egif(s.to_egif())``
        recovers the same schema."""
        from egif_generator_dau import generate_egif

        return resugar_holes(generate_egif(self.egi), self.holes)

    def to_clif(self) -> str:
        """Refused: a schema is a metalevel object, not a first-order sentence.

        Common Logic / CGIF are first-order and have no schema construct, so a
        schema must never be exported as a single counterfeit CLIF/CGIF sentence
        (III-bis, rule 2).  Export its **instances** instead — each is an ordinary
        Dau-Beta graph and round-trips normally."""
        raise ValueError(
            "a schema is a metalevel object and has no first-order CLIF form; "
            "export instance_of_schema(...) results instead (they round-trip)"
        )

    to_cgif = to_clif

    def is_hole(self, edge_id: ElementID) -> bool:
        return self.egi.rel.get(edge_id) in self.holes

    def occurrences(self, hole: Optional[str] = None) -> List[ElementID]:
        """Edge ids of hole occurrences — of ``hole`` if given, else of any hole."""
        return [
            eid
            for eid, rel in self.egi.rel.items()
            if rel in self.holes and (hole is None or rel == hole)
        ]

    def is_complete(self) -> bool:
        """True iff no holes remain (an ordinary Beta graph)."""
        return not self.occurrences()

    def __repr__(self) -> str:
        decl = ", ".join(f"{n}/{a}" for n, a in self.holes.items())
        return f"Schema(holes={{{decl}}})"


Filler = Union[str, RelationalGraphWithCuts]


def _as_graph(g: Filler) -> RelationalGraphWithCuts:
    return parse_egif(g) if isinstance(g, str) else g


def _resolve(g: RelationalGraphWithCuts, name_or_id: ElementID) -> ElementID:
    """Resolve a filler line given by EGIF variable name or by vertex id."""
    if name_or_id in {v.id for v in g.V}:
        return name_or_id
    for vid, vname in g.variable_names.items():
        if vname == name_or_id:
            return vid
    raise ValueError(f"filler has no line named {name_or_id!r}")


def instantiate(
    schema: Schema,
    g: Filler,
    *,
    hole: Optional[str] = None,
    ports: Sequence[ElementID],
    parameters: Optional[Dict[ElementID, ElementID]] = None,
) -> Union[Schema, RelationalGraphWithCuts]:
    """Fill one hole of ``schema`` with ``g``, returning the result.

    Every occurrence of the chosen hole is replaced by a fresh α-renamed copy of
    ``g`` whose ``ports`` are welded onto that occurrence's arguments.

    Args:
        schema: the schema to instantiate.
        g: the filler graph (EGIF string or EGI).  Its free lines are its ports
            (+ optional parameters).
        hole: which hole to fill.  Optional iff the schema has exactly one hole.
        ports: the filler's port lines (EGIF names or ids), in argument order;
            ``len(ports)`` must equal the hole's arity.  Welded per-occurrence.
        parameters: optional ``{filler_line: schema_line}`` for ambient parameters
            the filler shares with the schema — welded to the **same** schema line
            in every occurrence (e.g. ``φ(x) := (in x p)`` sharing ``p``).  Each
            value is a schema line given by EGIF name or id.

    Returns a :class:`Schema` if other holes remain, else the finished hole-free
    Beta graph (one axiom).  Raises ``ValueError`` on arity/hole/line errors.
    """
    if hole is None:
        if len(schema.holes) != 1:
            raise ValueError(
                "schema has multiple holes; specify hole= "
                f"(one of {sorted(schema.holes)})"
            )
        hole = next(iter(schema.holes))
    elif hole not in schema.holes:
        raise ValueError(f"unknown hole {hole!r}; have {sorted(schema.holes)}")

    arity = schema.holes[hole]
    if len(ports) != arity:
        raise ValueError(
            f"hole {hole!r} has arity {arity} but {len(ports)} ports were given"
        )

    gg = _as_graph(g)
    port_ids = [_resolve(gg, p) for p in ports]
    param_weld: Dict[ElementID, ElementID] = {}
    for fline, sline in (parameters or {}).items():
        param_weld[_resolve(gg, fline)] = _resolve(schema.egi, sline)

    result = schema.egi
    for occ in schema.occurrences(hole):  # captured before splicing; ids stable
        result = splice(result, occ, gg, ports=port_ids, weld=param_weld)

    remaining = {n: a for n, a in schema.holes.items() if n != hole}
    return Schema(result, remaining) if remaining else result


def instance_of_schema(
    schema: Schema,
    fillers: Dict[str, Tuple[Filler, Sequence[ElementID]]],
    *,
    parameters: Optional[Dict[str, Dict[ElementID, ElementID]]] = None,
) -> RelationalGraphWithCuts:
    """The new inference side-rule: produce a hole-free instance by filling **all**
    holes of ``schema``.  Licenses asserting the result when ``schema`` is on the
    sheet — the *only* new primitive the schema machinery adds atop Peirce's five
    rules (every instance is ordinary Dau-Beta).

    Args:
        schema: the schema on the sheet.
        fillers: ``{hole_name: (filler, ports)}`` for every hole.
        parameters: optional ``{hole_name: {filler_line: schema_line}}``.

    Returns the finished hole-free Beta graph.  Raises if a hole is unfilled.
    """
    missing = set(schema.holes) - set(fillers)
    if missing:
        raise ValueError(f"instance_of_schema: holes left unfilled: {sorted(missing)}")

    params = parameters or {}
    current: Union[Schema, RelationalGraphWithCuts] = schema
    for name, (filler, ports) in fillers.items():
        assert isinstance(current, Schema)
        current = instantiate(
            current, filler, hole=name, ports=ports, parameters=params.get(name)
        )
    assert isinstance(current, RelationalGraphWithCuts)
    return current


__all__ = [
    "Schema",
    "desugar_holes",
    "instantiate",
    "instance_of_schema",
]
