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
  (``accessible_projection.spoken_reading``). Always correct, never idiomatic.
* **idiomatic** — recognises the common EG idioms and speaks them familiarly:
  the scroll ``~[ A ~[ B ] ]`` → *"if A then B"* / *"every A is B"*; a single cut
  ``~[ A ]`` → *"there is no A"* / *"it is not the case that A"*; a double cut →
  the bare content; a **global co-reference** map so a line introduced once ("a
  married woman") is referred to the same way wherever it recurs, even inside a
  nested cut ("…then the married woman commits suicide"). Relation *names are
  humanised* (``married_woman`` → "married woman") and rendered by a light
  part-of-speech heuristic: a unary that reads as a **verb** ("commits_suicide") →
  *"x commits suicide"*, else a **noun/adjective** → *"x is a married woman"*; a
  binary that is a **preposition** ("on") → *"x is on y"*, a **verb** ("loves") →
  *"x loves y"*, else a **relational noun** ("husband") → *"x is the husband of y"*.

**Meaning-safe by construction**: any shape it cannot confidently idiomatise falls
back to structural phrasing inline, so it is never confidently wrong — and the
literal register is always one toggle away. The part-of-speech heuristic is exactly
that — a heuristic (a relation name is an opaque identifier; a rare s-ending noun
like *genus* will read as a verb). Fully-fluent prose (pronouns, entity-centred
nesting) needs a lexicon Arisbe deliberately does not carry; the ceiling on this
register is *readable and correct-in-meaning*, and the literal reading is the exact one.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from eg_navigation import child_cuts, child_edges, child_vertices

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
        # A vertex's home area (the area it is placed in) — where its existential is
        # introduced, and where its type predicates live.
        self.home: Dict[ElementID, ElementID] = {}
        for area_id, content in egi.area.items():
            for vid in content:
                if vid in self.vertices:
                    self.home[vid] = area_id
        # A **global** referring phrase per generic line, so a line reads the same
        # everywhere (including inside nested cuts): "the <type>", else the noun-role
        # it plays ("the husband" from ``(husband x y)``), else "it".
        self.refer: Dict[ElementID, str] = {}
        self.role_edge: Dict[ElementID, ElementID] = {}
        for v in egi.V:
            if not v.is_generic:
                continue
            hv = self.home.get(v.id, egi.sheet)
            types = self._unary_types(v.id, hv)
            if types:
                self.refer[v.id] = "the " + _humanize(egi.rel.get(types[0]) or "thing")
                continue
            role = self._noun_role(v.id)
            if role is not None:
                self.refer[v.id] = "the " + _humanize(egi.rel.get(role) or "thing")
                self.role_edge[v.id] = role
            else:
                self.refer[v.id] = "it"

    # ---- terms & incidences ---------------------------------------------- #

    def _label(self, vid: ElementID) -> str:
        v = self.vertices.get(vid)
        return (v.label if v and v.label else "an individual")

    def _term(self, vid: ElementID) -> str:
        """A referring term for a vertex in an atom: a constant's name, or a generic
        line's global referring phrase."""
        v = self.vertices.get(vid)
        if v is None:
            return "something"
        if not v.is_generic:
            return self._label(vid)
        return self.refer.get(vid, "it")

    def _unary_types(self, vid: ElementID, area_id: ElementID) -> List[ElementID]:
        out = []
        for eid in _sorted_edges(self.egi, child_edges(self.egi, area_id), self.names):
            args = self.egi.nu.get(eid, ())
            if len(args) == 1 and args[0] == vid:
                out.append(eid)
        return out

    def _noun_role(self, vid: ElementID) -> Optional[ElementID]:
        """A binary edge whose *subject* is ``vid`` and whose relation reads as a
        **relational noun** (not a verb, not a preposition) — so an untyped line can
        be named by the role it plays: ``(husband x y)`` names x "the husband"."""
        for eid in _sorted_edges(self.egi, [e.id for e in self.egi.E], self.names):
            args = self.egi.nu.get(eid, ())
            if len(args) == 2 and args[0] == vid:
                if _pos_binary(self.egi.rel.get(eid) or "") == "noun":
                    return eid
        return None

    def _atom(self, eid: ElementID, *, refer: Dict[ElementID, str] = None,
              negated: bool = False) -> str:
        """One atom as an English clause, with the global co-reference map (per-call
        keys override it, e.g. eliding a universal's subject)."""
        r = dict(self.refer)
        if refer:
            r.update(refer)
        rel = self.egi.rel.get(eid) or "related"
        args = list(self.egi.nu.get(eid, ()))
        terms = [r.get(v) or self._term(v) for v in args]
        if len(terms) == 0:
            return f"it is {'not ' if negated else ''}the case that {_humanize(rel)}"
        if len(terms) == 1:
            return _unary_clause(terms[0], rel, negated)
        if len(terms) == 2:
            return _binary_clause(terms[0], rel, terms[1], negated)
        h = _humanize(rel)
        head = ", ".join(terms[:-1])
        core = f"{h} holds among {head}, and {terms[-1]}"
        return ("it is not the case that " + core) if negated else core

    # ---- area readings ---------------------------------------------------- #

    def _content(self, area_id: ElementID):
        gverts = [v for v in _sorted_vertices(self.egi, child_vertices(self.egi, area_id), self.names)
                  if self.vertices[v].is_generic]
        cverts = [v for v in _sorted_vertices(self.egi, child_vertices(self.egi, area_id), self.names)
                  if not self.vertices[v].is_generic]
        edges = _sorted_edges(self.egi, child_edges(self.egi, area_id), self.names)
        cuts = _sorted_cuts(self.egi, child_cuts(self.egi, area_id), self.names)
        return gverts, cverts, edges, cuts

    def _intro_sort_key(self, vid: ElementID) -> int:
        # typed lines first (so a role line "a husband of the married woman" can
        # refer to an already-introduced "married woman"), then role lines, then bare.
        if self._unary_types(vid, self.home.get(vid, self.egi.sheet)):
            return 0
        if vid in self.role_edge:
            return 1
        return 2

    def _positive(self, area_id: ElementID) -> str:
        """A positive (asserted) reading of an area's direct content."""
        gverts, cverts, edges, cuts = self._content(area_id)
        clauses: List[str] = []
        used_edges = set()

        for vid in sorted(gverts, key=self._intro_sort_key):
            types = self._unary_types(vid, area_id)
            if types:
                noun = _humanize(self.egi.rel.get(types[0]) or "thing")
                used_edges.update(types)
                preds = [_unary_predicate(self.egi.rel.get(t) or "thing") for t in types[1:]]
                if preds:
                    clauses.append(f"there is {_art(noun)} that " + _join_and(preds))
                else:
                    clauses.append(f"there is {_art(noun)}")
            elif vid in self.role_edge and self.role_edge[vid] in edges:
                # Fold the naming relation into the introduction: "a husband of <z>".
                e = self.role_edge[vid]
                z = self.egi.nu.get(e, (None, None))[1]
                used_edges.add(e)
                zt = self._term(z) if z is not None else "something"
                clauses.append(f"there is {_art(_humanize(self.egi.rel.get(e) or 'thing'))} of {zt}")
            else:
                clauses.append("there is something")

        for vid in cverts:
            if not any(vid in self.egi.nu.get(e, ()) for e in edges):
                clauses.append(f"{self._label(vid)} exists")

        for eid in edges:
            if eid in used_edges:
                continue
            clauses.append(self._atom(eid))

        for cid in cuts:
            clauses.append(self._negation(cid))

        if not clauses:
            return "nothing holds"
        return _join_and(clauses)

    def _negation(self, cut_id: ElementID) -> str:
        gverts, cverts, edges, cuts = self._content(cut_id)

        # Double cut ~[ ~[ X ] ] — unwrap to X.
        if not gverts and not cverts and not edges and len(cuts) == 1:
            return self._positive(cuts[0])

        # Scroll ~[ ANT ~[ CONS ] ] — a conditional; universal when a line is shared.
        if len(cuts) == 1 and (gverts or cverts or edges):
            inner = cuts[0]
            shared = self._shared_universal(cut_id, inner)
            if shared is not None:
                vid, type_edge = shared
                noun = _humanize(self.egi.rel.get(type_edge) or "thing")
                return f"every {noun} {self._consequent_of(inner, vid)}"
            ant = self._positive_antecedent(cut_id, inner)
            cons = self._positive(inner)
            return f"if {ant}, then {cons}"

        # ~[ a single ground atom ] — a plain negated atom.
        if not gverts and len(cuts) == 0 and len(edges) == 1 and self._is_ground(edges[0]):
            return self._atom(edges[0], negated=True)

        # ~[ (T *x) … ] — "there is no <T> …".
        if len(gverts) == 1 and not cverts and not cuts:
            vid = gverts[0]
            types = self._unary_types(vid, cut_id)
            if types:
                noun = _humanize(self.egi.rel.get(types[0]) or "thing")
                extra = [_unary_predicate(self.egi.rel.get(t) or "thing") for t in types[1:]]
                for e in edges:
                    if e in types:
                        continue
                    extra.append(self._atom(e, refer={vid: "it"}))
                tail = (" that " + _join_and(extra)) if extra else ""
                return f"there is no {noun}{tail}"

        return f"it is not the case that {self._positive(cut_id)}"

    # ---- scroll helpers --------------------------------------------------- #

    def _shared_universal(self, outer: ElementID, inner: ElementID
                          ) -> Optional[Tuple[ElementID, ElementID]]:
        gverts, cverts, edges, cuts = self._content(outer)
        if len(gverts) != 1 or cverts:
            return None
        vid = gverts[0]
        types = self._unary_types(vid, outer)
        if not types:
            return None
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
        """The consequent of a universal, subject elided: ``(mortal x)`` →
        ``is a mortal`` / ``commits suicide``; ``~[(mortal x)]`` → ``is not a mortal``."""
        gverts, cverts, edges, cuts = self._content(inner)
        if not cuts and len(edges) == 1:
            a = self.egi.nu.get(edges[0], ())
            if len(a) == 1 and a[0] == subject:
                return _unary_predicate(self.egi.rel.get(edges[0]) or "thing")
            return self._atom(edges[0], refer={subject: "it"})
        if not edges and len(cuts) == 1 and not gverts and not cverts:
            ig, ic, ie, icu = self._content(cuts[0])
            if not icu and len(ie) == 1:
                a = self.egi.nu.get(ie[0], ())
                if len(a) == 1 and a[0] == subject:
                    return _unary_predicate(self.egi.rel.get(ie[0]) or "thing", negated=True)
        return "is such that " + self._positive(inner)

    def _positive_antecedent(self, outer: ElementID, inner: ElementID) -> str:
        gverts, cverts, edges, cuts = self._content(outer)
        clauses = []
        for vid in gverts:
            types = self._unary_types(vid, outer)
            if types:
                clauses.append("there is " + _art(_humanize(self.egi.rel.get(types[0]) or "thing")))
            else:
                clauses.append("there is something")
        for eid in edges:
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
        if body == "nothing holds":
            return "The sheet is blank — it asserts nothing (and so is trivially true)."
        return _cap(body) + "."


# --------------------------------------------------------------------------- #
# lexical heuristics (a relation name is an opaque identifier — best effort)   #
# --------------------------------------------------------------------------- #

_PREPS = {"on", "in", "at", "of", "with", "by", "under", "over", "near", "above",
          "below", "between", "from", "to", "into", "onto", "inside", "outside"}


def _humanize(name: str) -> str:
    """A relation/type identifier as words: ``married_woman`` → ``married woman``."""
    return (name or "thing").replace("_", " ").strip() or "thing"


def _verby(word: str) -> bool:
    """Whether a lowercase word reads as a 3rd-person-singular **verb** (``commits``,
    ``fails``, ``loves``) — a heuristic: ends in a lone ``s``, length ≥ 4 (so ``bus``
    / ``gas`` stay nouns). Misfires on rare s-ending nouns (``genus``)."""
    w = word.lower()
    return len(w) >= 4 and w.endswith("s") and not w.endswith("ss")


def _pos_binary(rel: str) -> str:
    """Part of speech of a binary relation: ``prep`` / ``verb`` / ``noun``."""
    h = _humanize(rel)
    first = h.split()[0] if h else h
    if h in _PREPS or first in _PREPS:
        return "prep"
    if _verby(first):
        return "verb"
    return "noun"


def _base(phrase: str) -> str:
    """The base (non-3rd-person) form of a verb phrase for negation: ``commits
    suicide`` → ``commit suicide``, ``fails in business`` → ``fail in business``."""
    ws = phrase.split()
    if ws:
        ws[0] = _base_word(ws[0])
    return " ".join(ws)


def _base_word(v: str) -> str:
    if v.endswith("sses") or v.endswith("shes") or v.endswith("ches"):
        return v[:-2]
    if len(v) > 3 and v.endswith("s") and not v.endswith("ss"):
        return v[:-1]
    return v


def _unary_clause(subject: str, rel: str, negated: bool) -> str:
    """A unary atom with an explicit subject: verb (``Otto commits suicide`` /
    ``Otto does not commit suicide``) or copula (``Otto is a man`` / ``… is not a man``)."""
    h = _humanize(rel)
    first = h.split()[0] if h else h
    if _verby(first):
        return f"{subject} does not {_base(h)}" if negated else f"{subject} {h}"
    return f"{subject} is {'not ' if negated else ''}{_art(h)}"


def _unary_predicate(rel: str, negated: bool = False) -> str:
    """A unary atom with the subject elided (a universal's consequent / a woven
    predicate): ``commits suicide`` / ``does not commit suicide`` / ``is a mortal``."""
    h = _humanize(rel)
    first = h.split()[0] if h else h
    if _verby(first):
        return f"does not {_base(h)}" if negated else h
    return f"is {'not ' if negated else ''}{_art(h)}"


def _binary_clause(a: str, rel: str, b: str, negated: bool) -> str:
    """A binary atom: preposition (``the cat is on the mat``), verb (``Romeo loves
    Juliet``), or relational noun (``Otto is the husband of Clara``)."""
    h = _humanize(rel)
    pos = _pos_binary(rel)
    neg = "not " if negated else ""
    if pos == "prep":
        return f"{a} is {neg}{h} {b}"
    if pos == "verb":
        return f"{a} does not {_base(h)} {b}" if negated else f"{a} {h} {b}"
    return f"{a} is {neg}the {h} of {b}"


# --------------------------------------------------------------------------- #
# small text helpers                                                          #
# --------------------------------------------------------------------------- #

def _art(word: str) -> str:
    w = (word or "thing").strip()
    art = "an" if w[:1].lower() in "aeiou" else "a"
    return f"{art} {w}"


def _join_and(clauses: List[str]) -> str:
    clauses = [c for c in clauses if c]
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return clauses[0] + " and " + clauses[1]
    return ", ".join(clauses[:-1]) + ", and " + clauses[-1]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


__all__ = ["english_readings", "idiomatic_reading"]
