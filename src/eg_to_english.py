"""Read an EGI as **English** — a natural-language *reading*, not an authoritative form.

The four linear notations (EGIF / CGIF / CLIF / FOPL) each *round-trip*: they denote
the same mathematical object and that identity is §3.3-attested. **Natural language
cannot join that club** — English is ambiguous and lossy, so a reading produced here
is a *gloss*: it connects the picture and the linear forms to familiar talk, but you
cannot parse it back and attest it. It is offered *beside* the linear forms, clearly
labelled a reading, never as a fifth editable notation.

Two registers, both derived from the same immutable graph (read-only — the ``area``
tree, ``nu`` incidence, vertex genericity; never a ``with_*`` builder):

* **literal** — the faithful, structural, outside-in reading
  (``accessible_projection.spoken_reading``): *"The sheet asserts: there is something
  x; man holds of x; it is not the case that: mortal holds of x."* Always correct,
  never idiomatic.
* **idiomatic** — recognises the common EG idioms and speaks them familiarly:
  the scroll ``~[ A ~[ B ] ]`` → *"if A then B"* / *"every A is B"*; a single cut
  ``~[ A ]`` → *"there is no A"* / *"it is not the case that A"*; a double cut →
  the bare content; a relation → a verb or copula phrase; a generic line → an
  existential. **Meaning-safe by construction**: any shape it cannot confidently
  idiomatise falls back to the structural phrasing inline, so it is never
  confidently wrong — and the literal register is always one toggle away.

The idiom set is deliberately the high-frequency Alpha/Beta fragment (the dragons,
the corpus proofs); exotic shapes (deeply nested scrolls, teridentity woven across
several cuts) read structurally rather than being mis-verbalised.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from eg_navigation import child_cuts, child_edges, child_vertices

# Reuse the deterministic reading-name assignment + the literal reading, so the two
# registers agree on variable names and two parses of one graph read identically.
from accessible_projection import (
    _reading_names,
    _sorted_cuts,
    _sorted_edges,
    _sorted_vertices,
    spoken_reading,
)


def english_readings(egi: RelationalGraphWithCuts) -> Dict[str, str]:
    """Both registers as ``{"idiomatic": str, "literal": str}`` — the payload the
    linear-form panel renders beside the four notations (a reading, not a form)."""
    return {
        "idiomatic": idiomatic_reading(egi),
        "literal": spoken_reading(egi),
    }


def idiomatic_reading(egi: RelationalGraphWithCuts) -> str:
    """A single familiar-English reading of the whole graph (see module docstring)."""
    return _Verbalizer(egi).sentence()


# --------------------------------------------------------------------------- #
# The idiomatic verbaliser                                                    #
# --------------------------------------------------------------------------- #

class _Verbalizer:
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.names = _reading_names(egi)
        self.vertices = {v.id: v for v in egi.V}

    # ---- terms & phrases -------------------------------------------------- #

    def _label(self, vid: ElementID) -> str:
        """A constant's name, plain (no quotes) — ``Socrates``, ``Romeo``."""
        v = self.vertices.get(vid)
        return (v.label if v and v.label else "an individual")

    def _var(self, vid: ElementID) -> str:
        return self.names.get(vid, "x")

    def _term(self, vid: ElementID, *, pronoun: Optional[str] = None) -> str:
        """A referring term for a vertex in an atom: a constant's name, or (for a
        generic line) the given pronoun / its variable letter."""
        v = self.vertices.get(vid)
        if v is None:
            return "something"
        if not v.is_generic:
            return self._label(vid)
        return pronoun or self._var(vid)

    def _unary_types(self, vid: ElementID, area_id: ElementID) -> List[ElementID]:
        """Edge ids of the unary atoms in ``area_id`` that apply solely to ``vid`` —
        the vertex's *type* predicates (``man`` in ``(man *x)``)."""
        out = []
        for eid in _sorted_edges(self.egi, child_edges(self.egi, area_id), self.names):
            args = self.egi.nu.get(eid, ())
            if len(args) == 1 and args[0] == vid:
                out.append(eid)
        return out

    def _atom(self, eid: ElementID, *, refer: Dict[ElementID, str] = None,
              negated: bool = False) -> str:
        """One atom as an English clause. Unary → copula (``x is a man`` /
        ``x is not a man``); binary → verb (``Romeo loves Juliet`` /
        ``Romeo does not love Juliet``); n-ary → a safe generic phrasing. ``refer``
        maps a generic vertex to its referring phrase (``the cat`` / ``it``)."""
        refer = refer or {}
        rel = self.egi.rel.get(eid) or "related"
        args = list(self.egi.nu.get(eid, ()))
        terms = [refer.get(v) or self._term(v) for v in args]
        if len(terms) == 0:
            return f"it is {'not ' if negated else ''}the case that {rel}"
        if len(terms) == 1:
            return f"{terms[0]} is {'not ' if negated else ''}{_art(rel)}"
        if len(terms) == 2:
            if negated:
                return f"{terms[0]} does not {_base(rel)} {terms[1]}"
            return f"{terms[0]} {rel} {terms[1]}"
        head = ", ".join(terms[:-1])
        if negated:
            return f"it is not the case that {rel} holds among {head}, and {terms[-1]}"
        return f"{rel} holds among {head}, and {terms[-1]}"

    # ---- area readings ---------------------------------------------------- #

    def _content(self, area_id: ElementID):
        gverts = [v for v in _sorted_vertices(self.egi, child_vertices(self.egi, area_id), self.names)
                  if self.vertices[v].is_generic]
        cverts = [v for v in _sorted_vertices(self.egi, child_vertices(self.egi, area_id), self.names)
                  if not self.vertices[v].is_generic]
        edges = _sorted_edges(self.egi, child_edges(self.egi, area_id), self.names)
        cuts = _sorted_cuts(self.egi, child_cuts(self.egi, area_id), self.names)
        return gverts, cverts, edges, cuts

    def _positive(self, area_id: ElementID) -> str:
        """A positive (asserted) reading of an area's direct content — a conjunction
        of its lines, atoms, and nested (negated) cuts, spoken idiomatically."""
        gverts, cverts, edges, cuts = self._content(area_id)
        clauses: List[str] = []

        # Weave each generic line into "there is a <type> that …" (the first unary is
        # the sortal noun; the rest are copular predicates), and record a referring
        # phrase ("the <type>" / a variable) so later atoms co-refer to it.
        used_edges = set()
        refer: Dict[ElementID, str] = {}
        for vid in gverts:
            types = self._unary_types(vid, area_id)
            if types:
                noun = self.egi.rel.get(types[0]) or "thing"
                refer[vid] = "the " + noun
                used_edges.update(types)
                preds = ["is " + _art(self.egi.rel.get(t) or "thing") for t in types[1:]]
                if preds:
                    clauses.append(f"there is {_art(noun)} that " + _join_and(preds))
                else:
                    clauses.append(f"there is {_art(noun)}")
            else:
                refer[vid] = self._var(vid)
                clauses.append("there is something")

        # Constant vertices with no incident edge assert the individual exists.
        for vid in cverts:
            if not any(vid in self.egi.nu.get(e, ()) for e in edges):
                clauses.append(f"{self._label(vid)} exists")

        # Remaining atoms (binary/n-ary, and unary on constants) — co-referring to
        # the lines introduced above ("the cat is on the mat").
        for eid in edges:
            if eid in used_edges:
                continue
            clauses.append(self._atom(eid, refer=refer))

        # Nested cuts → negations, each via the negation idioms.
        for cid in cuts:
            clauses.append(self._negation(cid))

        if not clauses:
            return "nothing holds"
        return _join_and(clauses)

    def _negation(self, cut_id: ElementID) -> str:
        """A cut, spoken as the appropriate negative idiom (see module docstring)."""
        gverts, cverts, edges, cuts = self._content(cut_id)

        # Double cut ~[ ~[ X ] ] — a bare re-assertion; unwrap to X's positive reading.
        if not gverts and not cverts and not edges and len(cuts) == 1:
            return self._positive(cuts[0])

        # Scroll ~[ ANT  ~[ CONS ] ] — a conditional, universal when a line is shared.
        if len(cuts) == 1 and (gverts or cverts or edges):
            inner = cuts[0]
            shared = self._shared_universal(cut_id, inner)
            if shared is not None:
                vid, type_edge = shared
                noun = self.egi.rel.get(type_edge) or "thing"
                consequent = self._consequent_of(inner, vid)
                return f"every {noun} {consequent}"
            ant = self._positive_antecedent(cut_id, inner)
            cons = self._positive(inner)
            return f"if {ant}, then {cons}"

        # ~[ a single ground atom ] — a plain negated atom.
        if not gverts and len(cuts) == 0 and len(edges) == 1 and self._is_ground(edges[0]):
            return self._atom(edges[0], negated=True)

        # ~[ (T *x) … ] — "there is no <T> …" when the negated content is one existential.
        if len(gverts) == 1 and not cverts and not cuts:
            vid = gverts[0]
            types = self._unary_types(vid, cut_id)
            if types:
                noun = self.egi.rel.get(types[0]) or "thing"
                refer = {vid: "it"}
                extra = ["is " + _art(self.egi.rel.get(t) or "thing") for t in types[1:]]
                for e in edges:
                    if e in types:
                        continue
                    extra.append(self._atom(e, refer=refer))
                tail = (" that " + _join_and(extra)) if extra else ""
                return f"there is no {noun}{tail}"

        # Anything else: negate the structural positive reading (meaning-safe).
        return f"it is not the case that {self._positive(cut_id)}"

    # ---- scroll helpers --------------------------------------------------- #

    def _shared_universal(self, outer: ElementID, inner: ElementID
                          ) -> Optional[Tuple[ElementID, ElementID]]:
        """If the scroll's antecedent has exactly one generic line, that line is
        typed by a unary in the antecedent, and it is referenced in the consequent,
        return ``(vid, type_edge)`` — the "every <type>" reading applies."""
        gverts, cverts, edges, cuts = self._content(outer)
        if len(gverts) != 1 or cverts:
            return None
        vid = gverts[0]
        types = self._unary_types(vid, outer)
        if not types:
            return None
        # the line must actually be used in the consequent (a genuine restriction)
        if not self._vertex_used_in(inner, vid):
            return None
        return (vid, types[0])

    def _vertex_used_in(self, area_id: ElementID, vid: ElementID) -> bool:
        for eid in child_edges(self.egi, area_id):
            if vid in self.egi.nu.get(eid, ()):
                return True
        for cid in child_cuts(self.egi, area_id):
            if self._vertex_used_in(cid, vid):
                return True
        return False

    def _consequent_of(self, inner: ElementID, subject: ElementID) -> str:
        """The consequent of a universal, with the shared line elided to a copula/verb
        with an implicit subject: ``(mortal x)`` → ``is mortal``; ``~[(mortal x)]`` →
        ``is not mortal``."""
        gverts, cverts, edges, cuts = self._content(inner)
        # single unary on the subject → "is a <T>"
        if not cuts and len(edges) == 1:
            a = self.egi.nu.get(edges[0], ())
            if len(a) == 1 and a[0] == subject:
                return "is " + _art(self.egi.rel.get(edges[0]) or "thing")
            return self._atom(edges[0], refer={subject: "it"})
        # single nested cut with a single unary → "is not a <T>"
        if not edges and len(cuts) == 1 and not gverts and not cverts:
            ig, ic, ie, icu = self._content(cuts[0])
            if not icu and len(ie) == 1:
                a = self.egi.nu.get(ie[0], ())
                if len(a) == 1 and a[0] == subject:
                    return "is not " + _art(self.egi.rel.get(ie[0]) or "thing")
        # fallback: "is such that <positive>", subject referred to as "it"
        return "is such that " + self._positive(inner)

    def _positive_antecedent(self, outer: ElementID, inner: ElementID) -> str:
        """The antecedent of a plain (non-universal) conditional — the outer content
        minus the inner cut, read positively (lines as 'a thing', etc.)."""
        gverts, cverts, edges, cuts = self._content(outer)
        clauses = []
        for vid in gverts:
            types = self._unary_types(vid, outer)
            if types:
                clauses.append("there is a " + (self.egi.rel.get(types[0]) or "thing"))
            else:
                clauses.append("there is something")
        for eid in edges:
            # skip type edges already spoken
            a = self.egi.nu.get(eid, ())
            if len(a) == 1 and a[0] in gverts and self._unary_types(a[0], outer)[:1] == [eid]:
                continue
            clauses.append(self._atom(eid))
        return _join_and(clauses) if clauses else "it holds"

    # ---- misc ------------------------------------------------------------- #

    def _is_ground(self, eid: ElementID) -> bool:
        return all(not self.vertices[v].is_generic for v in self.egi.nu.get(eid, ()))

    def sentence(self) -> str:
        body = self._positive(self.egi.sheet)
        # An empty sheet asserts nothing and is simply true.
        if body == "nothing holds":
            return "The sheet is blank — it asserts nothing (and so is trivially true)."
        return _cap(body) + "."


# --------------------------------------------------------------------------- #
# small text helpers                                                          #
# --------------------------------------------------------------------------- #

def _join_and(clauses: List[str]) -> str:
    clauses = [c for c in clauses if c]
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return clauses[0] + " and " + clauses[1]
    return ", ".join(clauses[:-1]) + ", and " + clauses[-1]


def _art(word: str) -> str:
    """``a`` / ``an`` + the word (article by leading vowel sound — an approximation)."""
    w = (word or "thing").strip()
    art = "an" if w[:1].lower() in "aeiou" else "a"
    return f"{art} {w}"


def _base(verb: str) -> str:
    """A rough base form of a 3rd-person verb for negation (``loves`` → ``love``),
    so ``does not <base>`` reads. Heuristic — not a full conjugator."""
    v = verb or "relate"
    if v.endswith("sses") or v.endswith("shes") or v.endswith("ches"):
        return v[:-2]
    if v.endswith("s") and not v.endswith("ss"):
        return v[:-1]
    return v


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


__all__ = ["english_readings", "idiomatic_reading"]
