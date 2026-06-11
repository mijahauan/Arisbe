"""
The Domain Oracle — situating a graph in "enough" of a model M.

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md``.

The Endoporeutic Game tests a proposal G against a domain model **M** — the
"outside" that enables the outside-in interpretation. The game's *only* operation
against the domain is a graph homomorphism of a negation-free outermost piece *g*
into M ("the Proposer must show a mapping between *g* and the objects and
relations in M").  So the contact surface is **a queried oracle, not a bulk
import**: the game asks a bounded sequence of strictly local questions, and M is
never materialised in full — only the neighbourhood the inquiry actually touches.

This module defines that contact surface:

    DomainOracle.resolve(g)   -> CONFIRMED (with a mapping) | UNKNOWN | DENIED
    DomainOracle.witness(...)  -> candidate individuals for the negative-area pick

and one backing, ``CorpusOracle``, over local EGIs (the tomos corpus).  The game
stays EGI-native and source-agnostic; a remote ``SparqlOracle`` (Wikidata) or a
clinical service can implement the same two methods later without changing the
game.

Scope of this first step (see the doc's §6 "minimal first step"):

* ``resolve`` accepts a **negation-free** ``g`` (a flat conjunction of relations
  over lines of identity — no cuts; that is exactly the fragment the game's
  outside-in unwrapping hands to the homomorphism check).  A ``g`` containing a
  cut raises ``ValueError`` — nested structure is the game's business, not the
  oracle's.
* It matches ``g`` against M's **asserted (sheet-level) atoms**.  Deeper positive
  areas and Beta scope subtleties are a documented future refinement.
* ``UNKNOWN`` vs ``DENIED`` is governed by whether the backing declares itself
  **closed** (asserted-complete → negation-as-failure → a miss is ``DENIED``) or
  **open** (sampled → a miss is ``UNKNOWN``).  Open is the default; the open-world
  ``UNKNOWN`` is a first-class verdict, not a failure.

The match is a conjunctive-query homomorphism, implemented directly on the public
EGI API rather than the protected isomorphism engine, because a negation-free
``g`` has no cuts and the embedding is well-defined and small.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts


# ---------------------------------------------------------------------------
# Verdicts and results
# ---------------------------------------------------------------------------

# An element-to-element map (g -> M).
Mapping_t = Dict[ElementID, ElementID]


class Verdict(Enum):
    """The three answers the game's outside-in process knows how to use."""

    CONFIRMED = "confirmed"   # g maps into M (a homomorphism exists)
    UNKNOWN = "unknown"       # open world: M neither confirms nor denies g
    DENIED = "denied"         # closed region: g provably fails in M


@dataclass(frozen=True)
class Mapping:
    """A homomorphism witnessing CONFIRMED: g's elements -> M's elements."""

    vertices: Mapping_t  # g vertex id -> M vertex id
    edges: Mapping_t     # g edge id   -> M edge id


@dataclass(frozen=True)
class ResolveResult:
    """Answer to ``resolve(g)`` — a verdict plus provenance."""

    verdict: Verdict
    mapping: Optional[Mapping] = None
    source: Optional[str] = None     # which backing answered (provenance)
    detail: str = ""

    @property
    def confirmed(self) -> bool:
        return self.verdict is Verdict.CONFIRMED


@dataclass(frozen=True)
class WitnessResult:
    """Candidate individuals for the negative-area pick (game rule 2)."""

    individuals: Tuple[str, ...]
    source: Optional[str] = None


# ---------------------------------------------------------------------------
# The interface
# ---------------------------------------------------------------------------

class DomainOracle(ABC):
    """The contact surface between the game and a domain model M.

    Two methods, because the game asks the domain exactly two things.  Any
    backing (local corpus, SPARQL endpoint, clinical service) that answers them
    can serve as M without the game knowing the difference.
    """

    @abstractmethod
    def resolve(
        self,
        g: RelationalGraphWithCuts,
        elements: Optional[frozenset] = None,
    ) -> ResolveResult:
        """Does the negation-free fragment ``g`` map into M?

        Args:
            g: a negation-free EGI (no cuts).  Raises ``ValueError`` otherwise.
            elements: optional subset of ``g``'s element ids to treat as the
                pattern; defaults to ``g``'s sheet-level contents.
        """

    @abstractmethod
    def witness(
        self,
        relation: str,
        partial_binding: Optional[Dict[int, str]] = None,
    ) -> WitnessResult:
        """Offer individuals from M that satisfy ``relation`` under a partial
        binding — the domain's contribution to the negative-area individual pick.

        ``partial_binding`` maps argument positions (0-based) to a required
        individual (a constant label).  Unpinned positions are free.
        """

    @abstractmethod
    def match_atoms(
        self,
        atoms: List[Tuple[str, Tuple[ElementID, ...]]],
        bound: Optional[Mapping_t] = None,
        constants: Optional[Dict[ElementID, str]] = None,
    ) -> List[Mapping_t]:
        """Enumerate **all** ways the conjunction of ``atoms`` maps into M.

        The lower-level primitive the semantic game needs: unlike ``resolve`` (one
        homomorphism, a verdict), this returns *every* binding, because the
        Verifier may need a particular witness among several to defeat a nested
        cut.  ``atoms`` is ``[(relation_name, (vertex_id, …)), …]``; ``bound``
        pins vertices already fixed by an enclosing area (a shared line of
        identity crossing a cut boundary — the Beta case); ``constants`` gives the
        labels of constant vertices, which must match by label.  Returns a list of
        complete bindings (vertex id → M vertex id), each extending ``bound``.
        """

    @abstractmethod
    def individuals(self) -> List[ElementID]:
        """The domain of M — every individual the Falsifier/Verifier may pick for
        an otherwise-unconstrained line of identity."""


# ---------------------------------------------------------------------------
# Atom extraction (the conjunctive-query view of an EGI)
# ---------------------------------------------------------------------------

# An atom is (edge_id, relation_name, (vertex_id, ...)) in nu-order.
_Atom = Tuple[ElementID, str, Tuple[ElementID, ...]]


def _atoms(egi: RelationalGraphWithCuts, element_ids) -> List[_Atom]:
    """The relation atoms of ``egi`` restricted to ``element_ids``."""
    out: List[_Atom] = []
    for edge in egi.E:
        if edge.id in element_ids:
            out.append(
                (edge.id, egi.get_relation_name(edge.id), tuple(egi.nu[edge.id]))
            )
    return out


def _vertex_labels(egi: RelationalGraphWithCuts) -> Dict[ElementID, Optional[str]]:
    """vertex id -> constant label (None for generic lines of identity)."""
    return {v.id: (v.label if not v.is_generic else None) for v in egi.V}


def _constant_vertices(egi: RelationalGraphWithCuts) -> Dict[ElementID, str]:
    """vertex id -> label, for constant vertices only."""
    return {v.id: v.label for v in egi.V if not v.is_generic and v.label is not None}


# ---------------------------------------------------------------------------
# The homomorphism search (conjunctive query of g into one model M)
# ---------------------------------------------------------------------------

def _all_bindings(
    g_atoms: Sequence[Tuple[str, Tuple[ElementID, ...]]],
    g_const_label: Dict[ElementID, str],
    m_by_key: Dict[Tuple[str, int], List[Tuple[ElementID, ...]]],
    m_vertex_label: Dict[ElementID, Optional[str]],
    seed: Mapping_t,
) -> List[Mapping_t]:
    """Every binding of the pattern atoms into M extending ``seed``.

    The enumerating cousin of ``_match_into`` (which returns the first): the
    semantic game needs *all* witnesses, because the Verifier may need a specific
    one to defeat a nested cut.  ``g_atoms`` is ``[(relation, (vid, …)), …]``;
    ``m_by_key`` maps (relation, arity) → the model's argument tuples; ``seed``
    pins vertices bound by an enclosing area.  A binding that contradicts ``seed``
    (a shared line forced two ways) simply never completes.
    """
    results: List[Mapping_t] = []
    vbind: Mapping_t = dict(seed)

    def rec(i: int) -> None:
        if i == len(g_atoms):
            results.append(dict(vbind))
            return
        rel, gverts = g_atoms[i]
        for mverts in m_by_key.get((rel, len(gverts)), ()):
            saved = dict(vbind)
            ok = True
            for gv, mv in zip(gverts, mverts):
                if gv in vbind:
                    if vbind[gv] != mv:
                        ok = False
                        break
                else:
                    lab = g_const_label.get(gv)
                    if lab is not None and m_vertex_label.get(mv) != lab:
                        ok = False
                        break
                    vbind[gv] = mv
            if ok:
                rec(i + 1)
            vbind.clear()
            vbind.update(saved)

    rec(0)
    return results


def _match_into(
    g_atoms: List[_Atom],
    g_const_label: Dict[ElementID, str],
    g_isolated_constants: Sequence[ElementID],
    g_isolated_generics: Sequence[ElementID],
    m_atoms: List[_Atom],
    m_vertex_label: Dict[ElementID, Optional[str]],
    m_label_to_vertex: Dict[str, ElementID],
    m_all_vertices: Sequence[ElementID],
) -> Optional[Tuple[Mapping_t, Mapping_t]]:
    """Find a homomorphism of the pattern (g_atoms) into the model (m_atoms).

    Backtracking over atoms.  A g-vertex that is a constant must land on an
    M-vertex with the same label; a generic g-vertex (a line of identity) may
    land on any M-vertex, and two distinct generics may coincide (homomorphism,
    not embedding).  Returns (vertex_map, edge_map) or None.
    """
    # Index M atoms by (relation, arity) for the inner loop.
    m_by_key: Dict[Tuple[str, int], List[_Atom]] = {}
    for atom in m_atoms:
        m_by_key.setdefault((atom[1], len(atom[2])), []).append(atom)

    vbind: Mapping_t = {}
    ebind: Mapping_t = {}

    def rec(i: int) -> bool:
        if i == len(g_atoms):
            return True
        g_edge, rel, gverts = g_atoms[i]
        for m_edge, _mrel, mverts in m_by_key.get((rel, len(gverts)), ()):
            saved_v, saved_e = dict(vbind), dict(ebind)
            ok = True
            for gv, mv in zip(gverts, mverts):
                if gv in vbind:
                    if vbind[gv] != mv:
                        ok = False
                        break
                else:
                    lab = g_const_label.get(gv)
                    if lab is not None and m_vertex_label.get(mv) != lab:
                        ok = False
                        break
                    vbind[gv] = mv
            if ok:
                ebind[g_edge] = m_edge
                if rec(i + 1):
                    return True
            vbind.clear()
            vbind.update(saved_v)
            ebind.clear()
            ebind.update(saved_e)
        return False

    if not rec(0):
        return None

    # Isolated g-vertices (no incident edge): a bare assertion of existence.
    for gv in g_isolated_constants:
        if gv in vbind:
            continue
        mv = m_label_to_vertex.get(g_const_label[gv])
        if mv is None:
            return None  # named individual absent from M
        vbind[gv] = mv
    for gv in g_isolated_generics:
        if gv in vbind:
            continue
        if not m_all_vertices:
            return None  # "something exists" but M is empty
        vbind[gv] = m_all_vertices[0]

    return dict(vbind), dict(ebind)


# ---------------------------------------------------------------------------
# CorpusOracle — backed by local EGIs (the tomos corpus)
# ---------------------------------------------------------------------------

class CorpusOracle(DomainOracle):
    """A ``DomainOracle`` over one or more local EGIs.

    Each model is a named EGI; ``resolve`` tries them in order and the first
    that admits a homomorphism answers CONFIRMED, tagged with its name
    (provenance).  If none do, the verdict is DENIED when the corpus is declared
    ``closed`` (asserted-complete), else UNKNOWN (open world).
    """

    def __init__(
        self,
        models: Sequence[Tuple[str, RelationalGraphWithCuts]],
        *,
        closed: bool = False,
    ):
        self._models = list(models)
        self._closed = closed
        # Precompute the asserted (sheet-level) atom view of each model.
        self._index: List[Tuple[str, RelationalGraphWithCuts, List[_Atom], Dict, Dict, List]] = []
        for name, M in self._models:
            sheet_ids = M.area.get(M.sheet, frozenset())
            m_atoms = _atoms(M, sheet_ids)
            m_vlabel = _vertex_labels(M)
            m_label_to_vertex = {
                lab: vid for vid, lab in _constant_vertices(M).items()
            }
            m_all_vertices = [v.id for v in M.V]
            self._index.append(
                (name, M, m_atoms, m_vlabel, m_label_to_vertex, m_all_vertices)
            )

    @classmethod
    def from_egif(
        cls,
        named_egifs: Dict[str, str],
        *,
        closed: bool = False,
    ) -> "CorpusOracle":
        """Convenience constructor from ``{name: EGIF string}``."""
        from egif_parser_dau import parse_egif

        models = [(name, parse_egif(text)) for name, text in named_egifs.items()]
        return cls(models, closed=closed)

    # -- DomainOracle ---------------------------------------------------------

    def resolve(
        self,
        g: RelationalGraphWithCuts,
        elements: Optional[frozenset] = None,
    ) -> ResolveResult:
        if g.Cut:
            raise ValueError(
                "resolve() expects a negation-free fragment (no cuts); "
                "the game's outside-in unwrapping handles negations before the "
                "homomorphism check."
            )

        pattern_ids = elements if elements is not None else g.area.get(g.sheet, frozenset())
        g_atoms = _atoms(g, pattern_ids)
        g_const_label = _constant_vertices(g)

        # Vertices that appear in some atom vs. isolated bare lines of identity.
        in_atom = {vid for _, _, verts in g_atoms for vid in verts}
        pattern_vertices = [v.id for v in g.V if v.id in pattern_ids]
        g_isolated_constants = [
            vid for vid in pattern_vertices
            if vid not in in_atom and vid in g_const_label
        ]
        g_isolated_generics = [
            vid for vid in pattern_vertices
            if vid not in in_atom and vid not in g_const_label
        ]

        for name, _M, m_atoms, m_vlabel, m_label_to_vertex, m_all_vertices in self._index:
            found = _match_into(
                g_atoms,
                g_const_label,
                g_isolated_constants,
                g_isolated_generics,
                m_atoms,
                m_vlabel,
                m_label_to_vertex,
                m_all_vertices,
            )
            if found is not None:
                vmap, emap = found
                return ResolveResult(
                    verdict=Verdict.CONFIRMED,
                    mapping=Mapping(vertices=vmap, edges=emap),
                    source=name,
                    detail=f"homomorphism into {name}",
                )

        if self._closed:
            return ResolveResult(
                verdict=Verdict.DENIED,
                source="corpus(closed)",
                detail="no homomorphism into any asserted-complete model",
            )
        return ResolveResult(
            verdict=Verdict.UNKNOWN,
            source="corpus(open)",
            detail="no homomorphism found; open world — neither confirmed nor denied",
        )

    def witness(
        self,
        relation: str,
        partial_binding: Optional[Dict[int, str]] = None,
    ) -> WitnessResult:
        pins: Dict[int, str] = dict(partial_binding) if partial_binding else {}
        individuals: List[str] = []
        seen = set()
        for name, M, m_atoms, m_vlabel, _l2v, _all in self._index:
            for _edge, rel, verts in m_atoms:
                if rel != relation:
                    continue
                # honour pinned positions
                if any(
                    pos < len(verts) and m_vlabel.get(verts[pos]) != lab
                    for pos, lab in pins.items()
                ):
                    continue
                for pos, vid in enumerate(verts):
                    if pos in pins:
                        continue
                    ind = m_vlabel.get(vid) or vid
                    if ind not in seen:
                        seen.add(ind)
                        individuals.append(ind)
        return WitnessResult(
            individuals=tuple(individuals),
            source="corpus",
        )

    def match_atoms(
        self,
        atoms: List[Tuple[str, Tuple[ElementID, ...]]],
        bound: Optional[Mapping_t] = None,
        constants: Optional[Dict[ElementID, str]] = None,
    ) -> List[Mapping_t]:
        seed: Mapping_t = dict(bound) if bound else {}
        const_label: Dict[ElementID, str] = dict(constants) if constants else {}
        g_atoms = [(rel, tuple(verts)) for rel, verts in atoms]

        out: List[Mapping_t] = []
        for _name, _M, m_atoms, m_vlabel, _l2v, _all in self._index:
            # Index this model's atoms by (relation, arity).
            m_by_key: Dict[Tuple[str, int], List[Tuple[ElementID, ...]]] = {}
            for _edge, rel, verts in m_atoms:
                m_by_key.setdefault((rel, len(verts)), []).append(verts)
            # ``seed`` may carry M-vertex ids from a *different* model (a binding
            # fixed higher in the same evaluation); those simply never match this
            # model's atoms, so the wrong model contributes nothing.  Vertex ids
            # are globally unique, so model identity threads through the binding.
            out.extend(_all_bindings(g_atoms, const_label, m_by_key, m_vlabel, seed))
        return out

    def individuals(self) -> List[ElementID]:
        out: List[ElementID] = []
        for _name, M, *_rest in self._index:
            out.extend(v.id for v in M.V)
        return out

    def individual_label(self, mvid: ElementID) -> str:
        """A readable name for an M individual (its constant label, or its id)."""
        for _name, _M, _ma, m_vlabel, _l2v, _all in self._index:
            if mvid in m_vlabel:
                return m_vlabel[mvid] or mvid
        return mvid
