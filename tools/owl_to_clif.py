"""
OWL → CLIF translator — the front half of the OWL→CLIF→EGI import pipeline.

The back half already exists and is solid: ``clif_parser_dau.parse_clif`` turns a
Common Logic sentence into a ``RelationalGraphWithCuts`` exactly as the EG encoding
wants —  ``(forall (x)(if (Man x)(Mortal x)))`` → the scroll ``~[ (Man x) ~[ (Mortal x) ] ]``,
an intersection body → a conjunctive Horn body, an ``exists`` head → an existential
scroll, ``(not (and ...))`` → a disjointness denial.  Those are precisely the shapes
``model_materialization`` and ``theory_query`` consume.  So bringing a real OWL
ontology in as a domain model M reduces to **OWL → CLIF**, and that is this module.

We read **OWL 2 Functional-Style Syntax** (the structural-specification serialization,
``.ofn`` / ``.owl`` functional form) because it is line/form-oriented and maps almost
one-to-one onto the axiom shapes — no RDF triple store, no blank-node restriction
decoding, no XML.  Same discipline as ``suokif_to_eg`` (the manifest floor: *attest
correspondence, not truth*): translate **only** the genuinely first-order-EG-expressible
axiom forms, and **report everything dropped** by construct — never a silent truncation
that reads as "imported the whole ontology" when it didn't.

Translated axiom forms.  Class expressions cover **named classes**,
``ObjectIntersectionOf`` / ``ObjectUnionOf`` of translatable expressions,
``ObjectSomeValuesFrom`` and ``ObjectHasValue`` over a named property, and
``ObjectMinCardinality`` ``0`` (≡ ``owl:Thing``) / ``1`` (≡ ``ObjectSomeValuesFrom``) —
all sound in **any** position — plus ``ObjectAllValuesFrom`` and ``ObjectComplementOf`` in
**superclass (positive) position only** (see the note below):

    SubClassOf(C D)                  → (forall (x) (if 〚C〛 〚D〛))
    EquivalentClasses(C D …)         → pairwise (forall (x) (iff 〚Ci〛 〚Cj〛))
    DisjointClasses(C D …)           → pairwise (forall (x) (not (and 〚Ci〛 〚Cj〛)))
    SubObjectPropertyOf(R S)         → (forall (x y) (if (R x y) (S x y)))
    ObjectPropertyDomain(R C)        → (forall (x y) (if (R x y) 〚C〛[x]))
    ObjectPropertyRange(R C)         → (forall (x y) (if (R x y) 〚C〛[y]))
    InverseObjectProperties(R S)     → (forall (x y) (if (R x y) (S y x))) + converse
    SymmetricObjectProperty(R)       → (forall (x y) (if (R x y) (R y x)))
    TransitiveObjectProperty(R)      → (forall (x y z)(if (and (R x y)(R y z))(R x z)))
    ClassAssertion(C a)              → 〚C〛[a]
    ObjectPropertyAssertion(R a b)   → (R a b)
    SameIndividual(a b …)            → pairwise (= a b)
    DifferentIndividuals(a b …)      → pairwise (not (= a b))

A **disjunction** ``C ⊔ D`` compiles to ``(or 〚C〛 〚D〛)`` (the De-Morgan double cut,
sound in either polarity; a disjunctive head is non-Horn, so the contest peel uses it
rather than materialization).  A **universal restriction** ``∀R.D`` in superclass
position is *prenexed* into a flat OWL-2-RL Horn rule — ``SubClassOf(C, ∀R.D)`` →
``(forall (x y) (if (and 〚C〛 (R x y)) 〚D〛[y]))`` — which the materializer recognises;
a **complement** ``¬D`` in superclass position becomes
``(if 〚C〛 (not 〚D〛))`` (non-Horn, contest).  An intersection head mixing plain conjuncts
with such restrictions splits into several rules.

``∀R.D`` and ``¬D`` are **not** translated in negative position (subclass / equivalent /
disjoint): parse_clif places a vertex at its first-reference area, not its
least-common-ancestor, so a construct that wraps the bound variable in an added cut flips
it unsoundly to existential — these are reported instead.  (``ObjectSomeValuesFrom``,
``ObjectHasValue`` and ``ObjectMinCardinality 1`` add no such cut, so they stay sound in
either polarity.)

``Declaration(...)`` forms are vocabulary, not content — counted, not "skipped".
Everything still outside the fragment (``ObjectMinCardinality n≥2`` / ``ObjectMaxCardinality``
/ ``ObjectExactCardinality``, ``ObjectHasSelf``, ``ObjectOneOf``, ``∀R.D`` / ``¬D`` in
negative position, datatypes, functional/key axioms, annotations) is reported by construct
and left to a later pass or the contest game.

``translate(text) -> (clif_text, report)``; ``owl_to_egi(text) -> (egi, report)`` pipes
through ``parse_clif``.  Run standalone on a ``.ofn`` path to print the report.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# ---------------------------------------------------------------------------
# A minimal S-expression reader for OWL functional syntax
# ---------------------------------------------------------------------------

# A node is either a str atom (a name / IRI / literal token) or a list [head, *args].
Node = Union[str, list]


def _strip_comments(text: str) -> str:
    """Drop full-line ``#`` comments (a line whose first non-space char is ``#``).

    OWL functional syntax has no comment form, but authored ``.ofn`` sources often
    carry ``#`` headers; IRIs contain ``#`` only mid-token, never at line start, so
    this is safe."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _tokenize(text: str) -> List[str]:
    """Tokens of functional syntax: parens, ``<IRI>`` spans, ``"string"`` spans
    (with optional ``^^datatype`` / ``@lang`` suffix kept attached), and bare atoms."""
    toks: List[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in "()":
            toks.append(ch)
            i += 1
        elif ch == "<":
            j = text.find(">", i)
            if j == -1:
                j = n - 1
            toks.append(text[i:j + 1])
            i = j + 1
        elif ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 1
                j += 1
            j += 1  # past the closing quote
            # keep an attached ^^<dt> or @lang suffix as part of the literal token
            while j < n and not text[j].isspace() and text[j] not in "()":
                if text[j] == "<":
                    j = text.find(">", j)
                    j = n if j == -1 else j + 1
                else:
                    j += 1
            toks.append(text[i:j])
            i = j
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()<"':
                j += 1
            toks.append(text[i:j])
            i = j
    return toks


def _read_forms(toks: List[str]) -> List[Node]:
    """Parse functional-syntax tokens into S-expression nodes.

    OWL functional syntax is **function-application** form — the head sits *outside*
    the parens (``SubClassOf(:A :B)``, not ``(SubClassOf :A :B)``).  So an atom
    immediately followed by ``(`` is a call ``[head, *args]``; a bare ``( … )`` group
    (an argument list with no head) becomes a plain list.
    """
    pos = 0

    def read_group() -> List[Node]:
        nonlocal pos
        pos += 1  # past '('
        items: List[Node] = []
        while pos < len(toks) and toks[pos] != ")":
            items.append(read())
        if pos < len(toks):
            pos += 1  # past ')'
        return items

    def read() -> Node:
        nonlocal pos
        tok = toks[pos]
        if tok == "(":
            return read_group()
        pos += 1                                   # consume the atom
        if pos < len(toks) and toks[pos] == "(":   # head( … ) — a call
            return [tok, *read_group()]
        return tok

    forms: List[Node] = []
    while pos < len(toks):
        if toks[pos] == ")":      # stray close-paren — skip defensively
            pos += 1
            continue
        forms.append(read())
    return forms


# ---------------------------------------------------------------------------
# Name resolution (IRI / prefixed-name → a CLIF-safe local identifier)
# ---------------------------------------------------------------------------

# Functional syntax: a head is followed by '(' with no space, so the tokenizer above
# yields e.g. "SubClassOf" then "(" — heads are bare atoms.  Class/property/individual
# references are <IRI>, prefix:Local, or :Local.

def _localname(ref: str) -> str:
    """The local part of an IRI or prefixed name."""
    if ref.startswith("<") and ref.endswith(">"):
        body = ref[1:-1]
        for sep in ("#", "/", ":"):
            if sep in body:
                body = body.rsplit(sep, 1)[-1]
        return body
    if '"' in ref:                       # a literal — strip quotes/suffix
        m = re.match(r'"((?:[^"\\]|\\.)*)"', ref)
        return m.group(1) if m else ref
    if ":" in ref:                       # prefix:Local or :Local
        return ref.rsplit(":", 1)[-1]
    return ref


def _safe_ident(name: str) -> str:
    """Sanitize a local name to a CLIF/EGIF identifier (letter then alnum/_)."""
    s = re.sub(r"[^0-9A-Za-z_]", "_", name)
    if not s:
        s = "_x"
    if not s[0].isalpha():
        s = "C_" + s
    return s


# owl:Thing / owl:Nothing get special treatment (the universal / empty class).
def _is_thing(ref: str) -> bool:
    return _localname(ref) == "Thing"


def _is_nothing(ref: str) -> bool:
    return _localname(ref) == "Nothing"


# ---------------------------------------------------------------------------
# Class-expression compiler:  〚C〛(var)  →  a CLIF formula string, or None
# ---------------------------------------------------------------------------

@dataclass
class _Ctx:
    """Fresh-variable supply for existential restrictions — ``w``-prefixed so they
    never collide with the per-axiom top-level variables (``x``/``y``/``z`` + index).
    Shared across the whole document so two axioms' fillers stay distinct."""
    n: int = 0

    def fresh(self) -> str:
        self.n += 1
        return f"w{self.n}"


def _class_expr(node: Node, var: str, ctx: _Ctx) -> Optional[str]:
    """Compile an OWL class expression applied to ``var`` into a CLIF formula.

    Returns ``None`` when the expression is outside the translatable fragment
    (union, complement, cardinality, allValuesFrom, hasValue, …) — the caller then
    skips the whole axiom and reports it.  ``Thing`` → a tautology marker ``"T"``;
    ``Nothing`` → a contradiction marker ``"F"`` (handled by the axiom builders).
    """
    if isinstance(node, str):
        if _is_thing(node):
            return "T"
        if _is_nothing(node):
            return "F"
        return f"({_safe_ident(_localname(node))} {var})"

    head = node[0] if node else None
    args = node[1:]
    if head == "ObjectIntersectionOf":
        parts = [_class_expr(a, var, ctx) for a in args]
        if any(p is None for p in parts):
            return None
        parts = [p for p in parts if p != "T"]      # drop tautologies
        if any(p == "F" for p in parts):
            return "F"
        if not parts:
            return "T"
        if len(parts) == 1:
            return parts[0]
        return "(and " + " ".join(parts) + ")"
    if head == "ObjectUnionOf":
        # 〚C ⊔ D〛(x) = (or 〚C〛(x) 〚D〛(x)).  parse_clif renders (or A B) as the
        # De-Morgan double cut ~[ ~[A] ~[B] ], so a union reads correctly in *either*
        # polarity (verified: the bound line settles universal in a body, existential
        # on the sheet — the cut nesting carries it).  A disjunctive *head* is non-Horn
        # (materialization skips it), but it is sound EG and the contest peel uses it.
        parts = [_class_expr(a, var, ctx) for a in args]
        if any(p is None for p in parts):
            return None
        if any(p == "T" for p in parts):       # C ⊔ Thing = Thing
            return "T"
        parts = [p for p in parts if p != "F"]  # drop empty disjuncts
        if not parts:                           # Nothing ⊔ Nothing = Nothing
            return "F"
        if len(parts) == 1:
            return parts[0]
        return "(or " + " ".join(parts) + ")"
    if head == "ObjectSomeValuesFrom":
        if len(args) != 2 or not isinstance(args[0], str):
            return None
        rel = _safe_ident(_localname(args[0]))
        y = ctx.fresh()
        filler = _class_expr(args[1], y, ctx)
        if filler is None or filler == "F":
            return None
        rel_atom = f"({rel} {var} {y})"
        inner = rel_atom if filler == "T" else f"(and {rel_atom} {filler})"
        return f"(exists ({y}) {inner})"
    if head == "ObjectHasValue":
        # 〚R value a〛(x) = (R x a) — a binary atom with the individual fixed.  No
        # added cut around the bound variable, so it reads soundly in either polarity.
        if len(args) != 2 or not all(isinstance(a, str) for a in args):
            return None
        rel = _safe_ident(_localname(args[0]))
        ind = _safe_ident(_localname(args[1]))
        return f"({rel} {var} {ind})"
    if head == "ObjectMinCardinality":
        # ≥0 is Thing; ≥1 R [C] ≡ ObjectSomeValuesFrom(R [C]) (an existential — sound in
        # either polarity); ≥n (n≥2) needs n pairwise-distinct fillers — left to a later
        # pass (not minted here).
        if len(args) < 2 or not isinstance(args[0], str):
            return None
        try:
            n = int(args[0])
        except ValueError:
            return None
        if n == 0:
            return "T"
        if n != 1 or not isinstance(args[1], str):
            return None
        rel = _safe_ident(_localname(args[1]))
        y = ctx.fresh()
        rel_atom = f"({rel} {var} {y})"
        if len(args) >= 3:                      # qualified: ≥1 R C
            filler = _class_expr(args[2], y, ctx)
            if filler is None or filler == "F":
                return None
            inner = rel_atom if filler == "T" else f"(and {rel_atom} {filler})"
        else:                                   # unqualified: ≥1 R
            inner = rel_atom
        return f"(exists ({y}) {inner})"
    return None  # untranslatable class expression


# ---------------------------------------------------------------------------
# Head-position prenexing:  a universal restriction ∀R.C in *superclass* position
# ---------------------------------------------------------------------------
#
# ``_class_expr`` deliberately returns None for ``ObjectAllValuesFrom`` — it cannot be
# compiled to a single formula-in-one-variable, and in *negative* (subclass / equivalent
# / disjoint) position it would be unsound here anyway: parse_clif places a vertex at its
# first-reference area, not its least-common-ancestor, so a universal-in-the-antecedent
# silently flips to existential (verified).
#
# But in *positive* (superclass) position a universal restriction is both sound and
# **Horn**.  SubClassOf(C, ∀R.D) ≡ ∀x∀y(C(x) ∧ R(x,y) → D(y)) — the canonical OWL-2-RL
# rule, whose flat scroll ~[ (C x)(R x y) ~[ (D y) ] ] the materializer recognises (the
# *nested* form ~[ (C x) ~[ ~[ (R x y) ~[ (D y) ] ] ] ] reads as "negation in head" and
# would fall only to the contest).  So we **prenex** the restriction's variable + relation
# atom into the rule's antecedent.  A superclass that is an intersection mixing plain
# conjuncts with ∀-restrictions splits into several rules (C ⊑ D ⊓ ∀R.E  →  C⊑D  and
# C⊓R(x,y)⊑E(y)) — itself a sound, layout-friendly decomposition.
#
# A clause is (extra_bound_vars, extra_antecedent_atoms, consequent_formula): for a plain
# head it is ([], [], 〚D〛); for ∀R.D it is ([y], ["(R x y)"], 〚D〛[y]).

def _head_clauses(node: Node, var: str, ctx: _Ctx):
    """Compile a *superclass* class expression to a list of Horn clauses, or None.

    Returns a list of ``(extra_vars, extra_atoms, consequent)`` tuples — the caller
    conjoins ``extra_atoms`` onto the rule body and binds ``extra_vars`` universally.
    ``None`` if any part is untranslatable; ``[]`` if the whole head is a tautology.
    """
    if isinstance(node, list) and node and node[0] == "ObjectAllValuesFrom":
        args = node[1:]
        if len(args) != 2 or not isinstance(args[0], str):
            return None
        rel = _safe_ident(_localname(args[0]))
        y = ctx.fresh()
        inner = _head_clauses(args[1], y, ctx)   # the filler is itself in head position
        if inner is None:
            return None
        rel_atom = f"({rel} {var} {y})"
        out = []
        for (vs, atoms, cons) in inner:
            out.append(([y, *vs], [rel_atom, *atoms], cons))
        return out
    if isinstance(node, list) and node and node[0] == "ObjectComplementOf":
        # ¬D in *superclass* position is sound (the bound line stays universal):
        # SubClassOf(C, ¬D) → (forall (x) (if 〚C〛 (not 〚D〛))).  Non-Horn (a negated
        # consequent), so the contest peel uses it.  In *negative* position the not-cut
        # would misplace the variable (→ existential), so it is left to _class_expr —
        # which returns None for complement, and the axiom is reported.
        args = node[1:]
        if len(args) != 1:
            return None
        inner = _class_expr(args[0], var, ctx)
        if inner is None or inner in ("T", "F"):
            return None
        return [([], [], f"(not {inner})")]
    if isinstance(node, list) and node and node[0] == "ObjectIntersectionOf":
        out = []
        for a in node[1:]:
            sub = _head_clauses(a, var, ctx)
            if sub is None:
                return None
            out.extend(sub)
        return out
    # Everything else falls back to the single-formula compiler (named class,
    # ObjectSomeValuesFrom, ObjectUnionOf, …): one clause, no extra antecedent.
    f = _class_expr(node, var, ctx)
    if f is None:
        return None
    if f == "T":        # ⊑ Thing conjunct — contributes nothing
        return []
    if f == "F":        # ⊑ Nothing — a denial, not a Horn rule; leave to a later pass
        return None
    return [([], [], f)]


# ---------------------------------------------------------------------------
# The translator
# ---------------------------------------------------------------------------

@dataclass
class OWLReport:
    translated: Counter = field(default_factory=Counter)
    skipped: Counter = field(default_factory=Counter)
    declarations: Counter = field(default_factory=Counter)
    classes: set = field(default_factory=set)
    properties: set = field(default_factory=set)
    individuals: set = field(default_factory=set)

    @property
    def n_axioms(self) -> int:
        return sum(self.translated.values())

    @property
    def summary(self) -> str:
        return (f"{self.n_axioms} CLIF axioms "
                f"({dict(self.translated)}); "
                f"skipped {sum(self.skipped.values())} {dict(self.skipped)}; "
                f"{len(self.classes)} classes, {len(self.properties)} properties, "
                f"{len(self.individuals)} individuals")


def _axiom_forms(forms: List[Node]) -> List[Node]:
    """Flatten ``Ontology(...)`` wrappers; drop ``Prefix`` / leading IRI atoms."""
    out: List[Node] = []
    for f in forms:
        if isinstance(f, list) and f and f[0] == "Ontology":
            for child in f[1:]:
                if isinstance(child, list):     # skip the ontology/version IRI atoms
                    out.append(child)
        elif isinstance(f, list) and f and f[0] == "Prefix":
            continue
        elif isinstance(f, list):
            out.append(f)
    return out


def _strip_annotations(args: List[Node]) -> List[Node]:
    """Drop leading in-axiom Annotation(...) arguments (OWL allows them anywhere)."""
    return [a for a in args
            if not (isinstance(a, list) and a and a[0] == "Annotation")]


def translate(text: str) -> Tuple[str, OWLReport]:
    """Translate the EG-expressible axioms of an OWL functional-syntax document.

    Returns ``(clif_text, report)`` — newline-separated CLIF sentences ready for
    ``parse_clif``, and an honest account of what translated, what was skipped (by
    construct), and the declared vocabulary.
    """
    forms = _read_forms(_tokenize(_strip_comments(text)))
    return translate_axiom_forms(_axiom_forms(forms))


def translate_axiom_forms(axiom_forms: List[Node]) -> Tuple[str, OWLReport]:
    """Translate already-parsed, already-flattened OWL axiom ``Node`` forms to CLIF.

    The shared core behind both front-ends: ``translate`` (OWL functional syntax) feeds
    forms parsed from text, and ``rdf_to_owl`` (RDF / Turtle / RDF-XML via rdflib) feeds
    forms reconstructed from triples.  Both reuse every axiom + class-expression rule here.
    """
    report = OWLReport()
    sentences: List[str] = []

    def note_class(ref: Node):
        if isinstance(ref, str) and not _is_thing(ref) and not _is_nothing(ref):
            report.classes.add(_safe_ident(_localname(ref)))

    def note_prop(ref: Node):
        if isinstance(ref, str):
            report.properties.add(_safe_ident(_localname(ref)))

    def note_ind(ref: Node):
        if isinstance(ref, str):
            report.individuals.add(_safe_ident(_localname(ref)))

    # One shared fresh-variable supply for restriction fillers, and a per-axiom index
    # so each universally-quantified axiom gets its *own* bound variables (x7, y7, …).
    # Reusing "x" across axioms would make parse_clif unify them into a single line of
    # identity threaded through every scroll — a correctness smell and a layout
    # catastrophe (one vertex crossing dozens of cut boundaries).
    ctx = _Ctx()
    nax = 0
    for form in axiom_forms:
        if not isinstance(form, list) or not form:
            continue
        head = form[0]
        args = _strip_annotations(form[1:])
        nax += 1
        vx, vy, vz = f"x{nax}", f"y{nax}", f"z{nax}"

        if head == "Declaration":
            if args and isinstance(args[0], list) and args[0]:
                kind, ref = args[0][0], (args[0][1] if len(args[0]) > 1 else None)
                report.declarations[kind] += 1
                if kind == "Class":
                    note_class(ref)
                elif kind in ("ObjectProperty", "DataProperty"):
                    note_prop(ref)
                elif kind in ("NamedIndividual", "Individual"):
                    note_ind(ref)
            continue

        if head == "SubClassOf" and len(args) == 2:
            for a in args:
                note_class(a)
            sub = _class_expr(args[0], vx, ctx)
            if sub is None or sub == "F":
                report.skipped["SubClassOf (complex class expression)"] += 1
                continue
            sup = _class_expr(args[1], vx, ctx)
            if sup is not None:
                if sup == "T":      # C ⊑ Thing — trivially true
                    report.skipped["SubClassOf (… ⊑ Thing, trivial)"] += 1
                    continue
                body = "(true)" if sub == "T" else sub
                sentences.append(f"(forall ({vx}) (if {body} {sup}))")
                report.translated["SubClassOf"] += 1
                continue
            # The superclass isn't a single formula (e.g. it carries an ∀R.C
            # restriction).  Prenex it into one or more flat Horn rules.
            clauses = _head_clauses(args[1], vx, ctx)
            if clauses is None:
                report.skipped["SubClassOf (complex class expression)"] += 1
                continue
            if not clauses:         # head is all-tautology (… ⊑ Thing ⊓ Thing)
                report.skipped["SubClassOf (… ⊑ Thing, trivial)"] += 1
                continue
            for (extra_vars, extra_atoms, cons) in clauses:
                ante = ([] if sub == "T" else [sub]) + extra_atoms
                body = ("(true)" if not ante
                        else ante[0] if len(ante) == 1
                        else "(and " + " ".join(ante) + ")")
                bound = " ".join([vx, *extra_vars])
                sentences.append(f"(forall ({bound}) (if {body} {cons}))")
                report.translated["SubClassOf (head restriction)"] += 1
            continue

        if head in ("EquivalentClasses", "DisjointClasses") and len(args) >= 2:
            for a in args:
                note_class(a)
            exprs = [_class_expr(a, vx, ctx) for a in args]
            if any(e is None or e in ("T", "F") for e in exprs):
                report.skipped[f"{head} (complex/empty class expression)"] += 1
                continue
            made = 0
            for i in range(len(exprs)):
                for j in range(i + 1, len(exprs)):
                    if head == "EquivalentClasses":
                        sentences.append(f"(forall ({vx}) (iff {exprs[i]} {exprs[j]}))")
                    else:
                        sentences.append(
                            f"(forall ({vx}) (not (and {exprs[i]} {exprs[j]})))")
                    made += 1
            report.translated[head] += made
            continue

        if head == "SubObjectPropertyOf" and len(args) == 2 and all(
                isinstance(a, str) for a in args):
            r, s = (_safe_ident(_localname(a)) for a in args)
            note_prop(args[0]); note_prop(args[1])
            sentences.append(f"(forall ({vx} {vy}) (if ({r} {vx} {vy}) ({s} {vx} {vy})))")
            report.translated["SubObjectPropertyOf"] += 1
            continue

        if head in ("ObjectPropertyDomain", "ObjectPropertyRange") and len(args) == 2:
            if not isinstance(args[0], str):
                report.skipped[head] += 1
                continue
            note_prop(args[0]); note_class(args[1])
            r = _safe_ident(_localname(args[0]))
            v = vx if head == "ObjectPropertyDomain" else vy
            cls = _class_expr(args[1], v, ctx)
            if cls is None or cls in ("T", "F"):
                report.skipped[f"{head} (complex class)"] += 1
                continue
            sentences.append(f"(forall ({vx} {vy}) (if ({r} {vx} {vy}) {cls}))")
            report.translated[head] += 1
            continue

        if head == "InverseObjectProperties" and len(args) == 2 and all(
                isinstance(a, str) for a in args):
            r, s = (_safe_ident(_localname(a)) for a in args)
            note_prop(args[0]); note_prop(args[1])
            sentences.append(f"(forall ({vx} {vy}) (if ({r} {vx} {vy}) ({s} {vy} {vx})))")
            sentences.append(f"(forall ({vx} {vy}) (if ({s} {vx} {vy}) ({r} {vy} {vx})))")
            report.translated["InverseObjectProperties"] += 2
            continue

        if head == "SymmetricObjectProperty" and len(args) == 1 and isinstance(
                args[0], str):
            r = _safe_ident(_localname(args[0]))
            note_prop(args[0])
            sentences.append(f"(forall ({vx} {vy}) (if ({r} {vx} {vy}) ({r} {vy} {vx})))")
            report.translated["SymmetricObjectProperty"] += 1
            continue

        if head == "TransitiveObjectProperty" and len(args) == 1 and isinstance(
                args[0], str):
            r = _safe_ident(_localname(args[0]))
            note_prop(args[0])
            sentences.append(
                f"(forall ({vx} {vy} {vz}) (if (and ({r} {vx} {vy}) ({r} {vy} {vz})) "
                f"({r} {vx} {vz})))")
            report.translated["TransitiveObjectProperty"] += 1
            continue

        if head == "ClassAssertion" and len(args) == 2 and isinstance(args[1], str):
            note_class(args[0]); note_ind(args[1])
            a = _safe_ident(_localname(args[1]))
            cls = _class_expr(args[0], a, ctx)
            if cls is None or cls in ("T", "F"):
                report.skipped["ClassAssertion (complex class)"] += 1
                continue
            sentences.append(cls)
            report.translated["ClassAssertion"] += 1
            continue

        if head == "ObjectPropertyAssertion" and len(args) == 3 and isinstance(
                args[0], str):
            r = _safe_ident(_localname(args[0]))
            a, b = (_safe_ident(_localname(x)) for x in args[1:])
            note_prop(args[0]); note_ind(args[1]); note_ind(args[2])
            sentences.append(f"({r} {a} {b})")
            report.translated["ObjectPropertyAssertion"] += 1
            continue

        if head in ("SameIndividual", "DifferentIndividuals") and len(args) >= 2 and all(
                isinstance(a, str) for a in args):
            names = [_safe_ident(_localname(a)) for a in args]
            for a in args:
                note_ind(a)
            made = 0
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    if head == "SameIndividual":
                        sentences.append(f"(= {names[i]} {names[j]})")
                    else:
                        sentences.append(f"(not (= {names[i]} {names[j]}))")
                    made += 1
            report.translated[head] += made
            continue

        # Anything else: record by construct and move on (the honest floor).
        report.skipped[str(head)] += 1

    return "\n".join(sentences), report


def owl_to_egi(text: str):
    """Translate OWL → CLIF → EGI in one step.  Returns ``(egi, clif_text, report)``."""
    from clif_parser_dau import parse_clif

    clif_text, report = translate(text)
    egi = parse_clif(clif_text) if clif_text.strip() else parse_clif("(true)")
    return egi, clif_text, report


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: owl_to_clif.py <ontology.ofn>")
        return 2
    text = Path(argv[0]).read_text(encoding="utf-8")
    clif_text, report = translate(text)
    print(f"OWL functional-syntax translation of {argv[0]}:")
    print("  translated  :", dict(report.translated))
    print("  skipped     :", dict(report.skipped))
    print("  declarations:", dict(report.declarations))
    print(f"  → {report.n_axioms} CLIF axioms over {len(report.classes)} classes, "
          f"{len(report.properties)} properties, {len(report.individuals)} individuals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
