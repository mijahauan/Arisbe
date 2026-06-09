"""The definition layer — named graphs (``name(ports) := body``), the term-level
twin of the derived-rule layer in ``src/derived_rules.py``.

A **definition** lets ``(subset z x)``, ``(empty e)``, ``(succ x s)`` stand in for
their spelled-out bodies, the way ``universal_instantiation`` is a named *move*.
It is a **conservative (definitional) extension**: pure abbreviation, always
eliminable.  ``expand`` rewrites every defined-relation edge back to its body via
the shared :func:`eg_splice.splice`; the result is an ordinary Dau-Beta graph, so
**all logic, §3.3 attestation, and EGIF/CGIF/CLIF round-tripping run on the
expanded form** (see ``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` Part III-bis, rule
1).  Expressive power is unchanged — Dau's Beta admits this exactly as FOL admits
defined predicates; in CLIF a definition *is* the biconditional
``(forall (ports) (iff (name ports) body))``, and in Sowa's conceptual graphs it
is the native lambda type/relation definition EGIF otherwise lacks.

**Scope (v1): non-recursive definitions only.**  Peirce's ``+``/``×`` are
*recursion equations* on the successor (``x + S(y) = S(x + y)``) and would expand
without end; they need the schema/recursion machinery, not this layer, and are
deliberately out of scope here.  ``expand`` raises on a (direct or indirect)
recursive definition rather than loop.

Touches no protected module.
"""

from typing import Dict, List, Optional, Sequence

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from eg_splice import splice


class Definition:
    """A named graph ``name(ports) := body``.

    ``ports`` are EGIF variable names appearing in ``body_egif`` (in argument
    order); they are the body's free lines, welded onto a use site's arguments on
    expansion.  ``body_egif`` declares the ports with ``*`` at its top scope and
    its own internal lines likewise — those internal lines are α-renamed fresh on
    every expansion so they never fuse onto host lines.
    """

    def __init__(self, name: str, ports: Sequence[str], body_egif: str):
        self.name = name
        self.ports = tuple(ports)
        self.body_egif = body_egif
        self._body: Optional[RelationalGraphWithCuts] = None
        # validate ports resolve in the body, eagerly
        missing = [p for p in self.ports if self._port_id(p) is None]
        if missing:
            raise ValueError(
                f"definition {name!r}: ports {missing} are not lines in the body"
            )

    @property
    def arity(self) -> int:
        return len(self.ports)

    @property
    def body(self) -> RelationalGraphWithCuts:
        if self._body is None:
            self._body = parse_egif(self.body_egif)
        return self._body

    def _port_id(self, name: str) -> Optional[ElementID]:
        for vid, vname in self.body.variable_names.items():
            if vname == name:
                return vid
        return None

    def port_ids(self) -> List[ElementID]:
        """The body vertex ids for ``self.ports``, in argument order."""
        return [self._port_id(p) for p in self.ports]

    def __repr__(self) -> str:
        return f"Definition({self.name}/{self.arity})"


class DefinitionRegistry:
    """A set of definitions, keyed by relation name."""

    def __init__(self, definitions: Optional[Sequence[Definition]] = None):
        self._by_name: Dict[str, Definition] = {}
        for d in definitions or ():
            self.add(d)

    def add(self, definition: Definition) -> "DefinitionRegistry":
        if definition.name in self._by_name:
            raise ValueError(f"definition {definition.name!r} already registered")
        self._by_name[definition.name] = definition
        return self

    def get(self, name: str) -> Optional[Definition]:
        return self._by_name.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def names(self) -> List[str]:
        return list(self._by_name)


# A generous cap: any non-recursive expansion terminates well within it, so
# exceeding it means the definitions are (directly or indirectly) recursive.
_MAX_EXPANSIONS = 10_000


def _find_defined_edge(
    egi: RelationalGraphWithCuts, registry: DefinitionRegistry
) -> Optional[ElementID]:
    for eid, rel in egi.rel.items():
        if rel in registry:
            return eid
    return None


def expand(
    egi: RelationalGraphWithCuts, registry: DefinitionRegistry
) -> RelationalGraphWithCuts:
    """Replace every defined-relation edge in ``egi`` with its body, repeatedly,
    until only primitive relations remain.  The returned graph is an ordinary
    Dau-Beta graph (no defined relations).

    Raises ``ValueError`` if expansion does not terminate within
    ``_MAX_EXPANSIONS`` steps — the signature of a recursive definition, which
    this layer does not support.
    """
    g = egi
    for _ in range(_MAX_EXPANSIONS):
        edge = _find_defined_edge(g, registry)
        if edge is None:
            return g
        defn = registry.get(g.rel[edge])
        arity = len(g.nu[edge])
        if arity != defn.arity:
            raise ValueError(
                f"use of {defn.name!r} has arity {arity}, definition has "
                f"{defn.arity}"
            )
        g = splice(g, edge, defn.body, ports=defn.port_ids())
    raise ValueError(
        "definition expansion did not terminate — recursive definitions are not "
        "supported by the definition layer (see module docstring)"
    )


__all__ = ["Definition", "DefinitionRegistry", "expand"]
