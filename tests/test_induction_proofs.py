"""Real induction proofs driven by the P7 least-number schema (``src/schema.py``).

Built smallest-first (the user's chosen order), each a genuine
``ProofChain`` — every step a sound Dau-rule (or recorded derived) application,
the conclusion checked by full isomorphism:

  1. **Mechanized induction inference** (this file, below) — instantiate P7 for a
     concrete ψ via the new ``instance-of-schema`` side-rule, supply the
     nonemptiness witness, and detach the "a ψ-minimal element exists" conclusion.
     The inductive core, mechanized and checked.
  2. least-counterexample of a modest theorem            (to come)
  3. totality of addition                                (to come)

ψ(n) := (even n).  P7-instance:
    ∃x even(x) → ∃u( even(u) ∧ ∀y( even(y) → ¬(y<u) ) )
i.e. "if there is an even number, there is a *least* even number" — the
least-number principle in action.
"""

import eg_navigation as nav
from derived_rules import existential_generalization, instantiate_to_lines
from eg_navigation import same_graph
from eg_splice import graft
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from schema import Schema, instance_of_schema, instantiate

P7 = Schema.from_egif(
    "~[ [*x] ⟨psi: x⟩ "
    "   ~[ [*u] ⟨psi: u⟩ "
    "      ~[ [*y] ⟨psi: y⟩ (lt y u) ] ] ]"
)


def _sheet_cut(egi):
    """The single scroll cut sitting on the sheet."""
    return nav.child_cuts(egi, egi.sheet)[0]


def test_mechanized_induction_inference_least_even():
    # ψ(n) := (even n); the induction instance for this ψ.
    p7_even = instance_of_schema(P7, {"psi": ("[*n] (even n)", ["n"])})
    assert "psi" not in set(p7_even.rel.values())

    # Premise: ∃x even(x) — a witness on the sheet.
    chain = ProofChain.from_egif("[*a] (even a)")

    # Step 1 — the instance-of-schema side-rule: assert the P7 instance.
    chain.apply_derived(
        "instance-of-schema",
        lambda egi: graft(egi, p7_even),
        label="ind",
        note="Assert the least-number induction principle for ψ(n) := even(n).",
    )

    # Step 2 — derived universal instantiation: the scroll is ∀x(even(x) → Q);
    # instantiate its line x to the witness line a (join x into a).
    def ui_join(egi):
        cut = _sheet_cut(egi)
        x = nav.child_vertices(egi, cut)[0]          # the antecedent line
        a = nav.child_vertices(egi, egi.sheet)[0]    # the witness line
        return instantiate_to_lines(egi, universal_cut=cut, joins=[(x, a)])

    chain.apply_derived(
        "universal-instantiation", ui_join, label="UI", note="x := a (the witness)."
    )

    # Step 3 — IT- : the antecedent even(a) inside the scroll is now a copy of the
    # sheet's even(a); deiterate it.
    def inner_even(egi):
        cut = _sheet_cut(egi)
        return [
            e for e in nav.child_edges(egi, cut) if nav.relation_of(egi, e) == "even"
        ][0]

    chain.apply("IT-", select=inner_even, label="2e", note="Deiterate the matched antecedent.")

    # Step 4 — DC- : remove the freed double cut, releasing the consequent Q.
    chain.apply("DC-", select=_sheet_cut, label="2e", note="Release the consequent.")

    # ⊢ witness ∧ Q, where Q = ∃u( even(u) ∧ ∀y( even(y) → ¬(y<u) ) ).
    goal = parse_egif("[*a] (even a) [*u] (even u) ~[ [*y] (even y) (lt y u) ]")
    assert same_graph(chain.current, goal)


def _detach_least(chain):
    """Steps shared with item 1: assert P7 for ψ:=P over a witness P(a), then
    detach the least-element conclusion ∃u(P(u) ∧ ∀w(P(w)→¬(w<u)))."""
    p7_P = instance_of_schema(P7, {"psi": ("[*n] (P n)", ["n"])})
    chain.apply_derived(
        "instance-of-schema",
        lambda egi: graft(egi, p7_P),
        label="ind",
        note="Assert the least-number induction principle for ψ(n) := P(n).",
    )

    def ui_join_x(egi):
        cut = _sheet_cut(egi)
        x = nav.child_vertices(egi, cut)[0]
        a = nav.child_vertices(egi, egi.sheet)[0]
        return instantiate_to_lines(egi, universal_cut=cut, joins=[(x, a)])

    chain.apply_derived("universal-instantiation", ui_join_x, label="UI", note="x := a.")

    def inner_P(egi):
        cut = _sheet_cut(egi)
        return [e for e in nav.child_edges(egi, cut) if nav.relation_of(egi, e) == "P"][0]

    chain.apply("IT-", select=inner_P, label="2e", note="Deiterate the matched antecedent.")
    chain.apply("DC-", select=_sheet_cut, label="2e", note="Release: a least P-element u exists.")
    return chain


def test_least_counterexample_minimum_is_lower_bound():
    """Item 2 — minimality genuinely used.  From a witness P(a), P7 gives a least
    P-element u; its minimality clause ∀w(P(w)→¬(w<u)) then yields ¬(a<u): the
    least element is a lower bound for the witness (the meaning of 'minimum')."""
    chain = ProofChain.from_egif("[*a] (P a)")
    _detach_least(chain)
    # state now: [*a] (P a) [*u] (P u) ~[ [*w] (P w) (lt w u) ]
    # the trailing cut is ∀w(P(w) → ¬(w<u)) — the minimality clause.

    def minimality_cut(egi):
        return _sheet_cut(egi)

    def witness_a(egi):
        # u is the line in the SECOND position of the cut's (lt w u); a is the
        # other sheet line (the witness).
        cut = _sheet_cut(egi)
        lt_e = [e for e in nav.child_edges(egi, cut) if nav.relation_of(egi, e) == "lt"][0]
        u = nav.vertices_of_edge(egi, lt_e)[1]
        return [v for v in nav.child_vertices(egi, egi.sheet) if v != u][0]

    # Step 5 — instantiate minimality ∀w(...) at w := a (use minimality on the witness).
    def ui_join_w(egi):
        cut = minimality_cut(egi)
        w = nav.child_vertices(egi, cut)[0]
        a = witness_a(egi)
        return instantiate_to_lines(egi, universal_cut=cut, joins=[(w, a)])

    chain.apply_derived(
        "universal-instantiation", ui_join_w, label="UI", note="w := a (minimality on the witness)."
    )
    # cut is now ~[ (P a) (lt a u) ] = ¬(P(a) ∧ a<u).

    # Step 6 — deiterate the inner P(a) (copy of the sheet's witness) → ~[ (lt a u) ].
    def inner_P_in_min(egi):
        cut = _sheet_cut(egi)
        return [e for e in nav.child_edges(egi, cut) if nav.relation_of(egi, e) == "P"][0]

    chain.apply("IT-", select=inner_P_in_min, label="2e", note="Deiterate P(a); leaves ¬(a<u).")

    # ⊢ ¬(a < u): the least P-element u is a lower bound for the witness a.
    goal = parse_egif("[*a] (P a) [*u] (P u) ~[ (lt a u) ]")
    assert same_graph(chain.current, goal)


# ===========================================================================
# Item 3 — totality of addition.  Built from three pieces: a second induction
# schema (base+step form), the mechanized base case, and the mechanized
# inductive step (the first proofs where the recursion axioms do real work).
# ===========================================================================

# The ORDINARY mathematical-induction schema (base + step ⟹ ∀), a *second*
# graph-with-holes schema: hole φ at FOUR occurrences (o, n, sn, Y), the form
# most recognise as induction.  Reads:
#   ( ∀o(zero(o)→φ(o)) ∧ ∀n∀sn(φ(n)∧succ(n,sn)→φ(sn)) ) → ∀Y φ(Y)
# = ¬( BASE ∧ STEP ∧ ∃Y¬φ(Y) ).  The conclusion clause is the *negated*
# conclusion ∃Y¬φ(Y) = ``[*Y] ~[ φ(Y) ]`` placed DIRECTLY in the outer cut — NOT
# wrapped in a further cut.  (An earlier draft wrapped it, which made the clause
# read ∀Yφ and the whole schema ¬(BASE∧STEP∧∀Yφ) = (BASE∧STEP)→¬∀Yφ — the
# negation of induction.  Verified against ``chapter18_fopl_translation``.)
ORD_INDUCTION_EGIF = (
    "~[ ~[ [*o] (zero o) ~[ ⟨phi: o⟩ ] ] "
    "   ~[ [*n] [*sn] ⟨phi: n⟩ (succ n sn) ~[ ⟨phi: sn⟩ ] ] "
    "   [*Y] ~[ ⟨phi: Y⟩ ] ]"
)


def test_ordinary_induction_schema_instantiates():
    """The base+step induction schema (4 occurrences of φ) parses, instantiates
    hole-free, and — crucially — instantiates to the *correct* induction
    principle ``(BASE ∧ STEP) → ∀Y φ(Y)`` (guarding the conclusion-clause polarity
    bug: ``[*Y] ~[φ]`` = ∃Y¬φ, NOT ``~[ [*Y] ~[φ] ]`` = ∀Yφ)."""
    ord_ind = Schema.from_egif(ORD_INDUCTION_EGIF)
    assert ord_ind.holes == {"phi": 1}            # φ is unary…
    assert len(ord_ind.occurrences("phi")) == 4   # …occurring four times (o, n, sn, Y)
    inst = instantiate(ord_ind, "[*k] (P k)", ports=["k"])
    assert "phi" not in set(inst.rel.values())
    assert same_graph(parse_egif(generate_egif(inst)), inst)
    # The instance IS the induction principle for φ:=P: ¬(BASE ∧ STEP ∧ ∃Y¬P(Y)).
    induction = parse_egif(
        "~[ ~[ [*o] (zero o) ~[ (P o) ] ] "
        "   ~[ [*n] [*sn] (P n) (succ n sn) ~[ (P sn) ] ] "
        "   [*Y] ~[ (P Y) ] ]"
    )
    assert same_graph(inst, induction)


# plus_base / plus_step axioms (from tests/test_math_fixtures.RECURSION_FIXTURES).
PLUS_BASE = "~[ [*x] [*z] (zero z) ~[ (plus x z x) ] ]"
PLUS_STEP = (
    "~[ [*x] [*y] [*z] [*sy] [*sz] "
    "   (plus x y z) (succ y sy) (succ z sz) ~[ (plus x sy sz) ] ]"
)


def _by_rel(egi, area, rel):
    return [e for e in nav.child_edges(egi, area) if nav.relation_of(egi, e) == rel]


def test_totality_base_case():
    """x + 0 = x — the base case, from the plus_base recursion axiom.

    Premises: plus_base + a fixed x and a zero o.  Instantiate the axiom at
    (x, o), detach plus(x, o, x)."""
    chain = ProofChain.from_egif(f"[*x] [*o] (zero o) {PLUS_BASE}")

    def ui_base(egi):
        cut = _sheet_cut(egi)
        zz = nav.vertices_of_edge(egi, _by_rel(egi, cut, "zero")[0])[0]
        xx = [v for v in nav.child_vertices(egi, cut) if v != zz][0]
        o = nav.vertices_of_edge(egi, _by_rel(egi, egi.sheet, "zero")[0])[0]
        x = [v for v in nav.child_vertices(egi, egi.sheet) if v != o][0]
        return instantiate_to_lines(egi, universal_cut=cut, joins=[(xx, x), (zz, o)])

    chain.apply_derived("universal-instantiation", ui_base, label="UI", note="x'/z' := x/o.")
    chain.apply(
        "IT-",
        select=lambda egi: _by_rel(egi, _sheet_cut(egi), "zero")[0],
        label="2e", note="Deiterate the zero(o) antecedent.",
    )
    chain.apply("DC-", select=_sheet_cut, label="2e", note="Release plus(x,o,x).")

    goal = parse_egif("[*x] [*o] (zero o) (plus x o x)")
    assert same_graph(chain.current, goal)


def test_totality_step_case():
    """x + v = z  ∧  succ(v,sv)  ∧  succ(z,sz)  ⊢  x + S(v) = S(z) — the inductive
    step, from the plus_step recursion axiom (detachment / modus ponens)."""
    premises = "[*x] [*v] [*z] [*sv] [*sz] (plus x v z) (succ v sv) (succ z sz)"
    chain = ProofChain.from_egif(f"{premises} {PLUS_STEP}")

    def ui_step(egi):
        cut = _sheet_cut(egi)
        # universal lines, by their roles inside the axiom cut
        plus_e = _by_rel(egi, cut, "plus")[0]
        xx, yy, zz = nav.vertices_of_edge(egi, plus_e)
        succ_es = _by_rel(egi, cut, "succ")
        syy = next(nav.vertices_of_edge(egi, e)[1] for e in succ_es
                   if nav.vertices_of_edge(egi, e)[0] == yy)
        szz = next(nav.vertices_of_edge(egi, e)[1] for e in succ_es
                   if nav.vertices_of_edge(egi, e)[0] == zz)
        # matching sheet premises, by the same roles
        s_plus = _by_rel(egi, egi.sheet, "plus")[0]
        x, v, z = nav.vertices_of_edge(egi, s_plus)
        s_succ = _by_rel(egi, egi.sheet, "succ")
        sv = next(nav.vertices_of_edge(egi, e)[1] for e in s_succ
                  if nav.vertices_of_edge(egi, e)[0] == v)
        sz = next(nav.vertices_of_edge(egi, e)[1] for e in s_succ
                  if nav.vertices_of_edge(egi, e)[0] == z)
        return instantiate_to_lines(
            egi, universal_cut=cut,
            joins=[(xx, x), (yy, v), (zz, z), (syy, sv), (szz, sz)],
        )

    chain.apply_derived("universal-instantiation", ui_step, label="UI", note="instantiate the step axiom at the premises.")
    # deiterate the three antecedent relations (copies of the sheet premises)
    for rel, lbl in (("plus", "2e"), ("succ", "2e"), ("succ", "2e")):
        chain.apply(
            "IT-",
            select=lambda egi, r=rel: _by_rel(egi, _sheet_cut(egi), r)[0],
            label=lbl, note=f"Deiterate the {rel} antecedent.",
        )
    chain.apply("DC-", select=_sheet_cut, label="2e", note="Release plus(x,sv,sz).")

    goal = parse_egif(f"{premises} (plus x sv sz)")
    assert same_graph(chain.current, goal)


# --- the existential base/step lemmas (φ := ∃z plus(x,·,z)) ------------------ #

def test_totality_base_lemma_existential():
    """∀o( zero(o) → ∃z plus(x,o,z) ) — the base in the form the induction schema
    wants, from plus_base + existential generalization."""
    chain = ProofChain.from_egif(f"[*x] {PLUS_BASE}")

    # instantiate plus_base at xx := x (leaving zz/o universal)
    def ui_xx(egi):
        cut = _sheet_cut(egi)
        zz = nav.vertices_of_edge(egi, _by_rel(egi, cut, "zero")[0])[0]
        xx = [v for v in nav.child_vertices(egi, cut) if v != zz][0]
        x = nav.child_vertices(egi, egi.sheet)[0]
        return instantiate_to_lines(egi, universal_cut=cut, joins=[(xx, x)])

    chain.apply_derived("universal-instantiation", ui_xx, label="UI", note="x' := x.")

    # ∃-generalize the value position of (plus x o x) → ∃z plus(x,o,z)
    def gen_value(egi):
        # the plus edge lives in the innermost cut
        outer = _sheet_cut(egi)
        inner = nav.child_cuts(egi, outer)[0]
        plus_e = _by_rel(egi, inner, "plus")[0]
        return existential_generalization(egi, edge_id=plus_e, position=2, new_vertex_id="zval")

    chain.apply_derived("existential-generalization", gen_value, label="EG", note="value := ∃z.")

    goal = parse_egif("[*x] ~[ [*o] (zero o) ~[ [*z] (plus x o z) ] ]")
    assert same_graph(chain.current, goal)


# --- the inductive STEP lemma (φ := ∃z plus(x,·,z)) -------------------------- #
#
# The step in the form the induction schema wants:
#   ∀n∀sn( (∃z plus(x,n,z)) ∧ succ(n,sn) → ∃z' plus(x,sn,z') )
# This is a *different proof mode* from everything above.  Items 1–3-base are all
# **detachment** (use an existing implication via instantiate + modus ponens —
# what EG does fluently).  The step lemma must be **constructed** as a NEW
# implication from the axioms — the deduction-theorem direction (build A→B by
# deriving B under the assumption A).  The EG realisation:
#   1. DC+ an empty double cut  ~[ ~[ ] ]  — the scroll that will be A→B.
#   2. INS the antecedent A into the outer (negative) cut; weld its parameter
#      line onto x.
#   3. IT+ a copy of A, and the plus_step + succ_total axioms, into the inner
#      (positive) cut — now a forward detachment proof can run there.
#   4. inside the inner cut: discharge succ-existence (∃sz succ(z,sz) from
#      succ_total), instantiate plus_step at the premises, detach plus(x,sn,sz),
#      ∃-generalise the value, and erase the spent premises — leaving exactly the
#      consequent ∃z' plus(x,sn,z').
# The axioms are *copied* (IT+), never consumed, so they survive on the sheet —
# the conclusion is "axioms ⊢ step-lemma", the same convention the detachment
# proofs above use (premises remain in the goal).

PLUS_STEP_AX = (
    "~[ [*x2] [*y] [*zz] [*sy] [*sz] "
    "   (plus x2 y zz) (succ y sy) (succ zz sz) ~[ (plus x2 sy sz) ] ]"
)
SUCC_TOTAL_AX = "~[ [*w] ~[ [*sw] (succ w sw) ] ]"  # ∀w∃sw succ(w,sw) — Peirce P4/P6


def _cout(egi):
    """The scroll being built: a sheet cut with a plus, exactly one direct succ
    (the antecedent succ(n,sn)), and a child cut.  plus_step has *two* direct
    succ; succ_total has none — so this is unambiguous throughout the build."""
    for c in nav.child_cuts(egi, egi.sheet):
        if (_by_rel(egi, c, "plus") and len(_by_rel(egi, c, "succ")) == 1
                and nav.child_cuts(egi, c)):
            return c


def _plus_step_cut(egi):
    for c in nav.child_cuts(egi, egi.sheet):
        if _by_rel(egi, c, "plus") and len(_by_rel(egi, c, "succ")) == 2:
            return c


def _succ_total_cut(egi):
    for c in nav.child_cuts(egi, egi.sheet):
        if not _by_rel(egi, c, "plus") and not _by_rel(egi, c, "succ"):
            ks = nav.child_cuts(egi, c)
            if ks and _by_rel(egi, ks[0], "succ"):
                return c


def _empty_scroll_outer(egi):
    for c in nav.child_cuts(egi, egi.sheet):
        ks = nav.child_cuts(egi, c)
        if (len(ks) == 1 and not nav.child_edges(egi, c)
                and not nav.child_vertices(egi, c)
                and not nav.child_edges(egi, ks[0])
                and not nav.child_vertices(egi, ks[0])
                and not nav.child_cuts(egi, ks[0])):
            return c


def _succ_total_copy(egi, area):
    """A succ_total copy inside ``area``: a child cut with no direct edges whose
    inner cut carries succ."""
    for c in nav.child_cuts(egi, area):
        if not nav.child_edges(egi, c):
            ks = nav.child_cuts(egi, c)
            if ks and _by_rel(egi, ks[0], "succ"):
                return c


def _plus_step_copy(egi, area):
    for c in nav.child_cuts(egi, area):
        if _by_rel(egi, c, "plus") and len(_by_rel(egi, c, "succ")) == 2:
            return c


def test_totality_step_lemma_existential():
    """∀n∀sn( ∃z plus(x,n,z) ∧ succ(n,sn) → ∃z' plus(x,sn,z') ) — the inductive
    step in the induction schema's form, *constructed* from plus_step + succ_total
    (the deduction-theorem direction, the harder EG mode).  See the module note."""
    chain = ProofChain.from_egif(f"[*x] {PLUS_STEP_AX} {SUCC_TOTAL_AX}")

    # 1 — DC+ the empty double cut (the scroll that becomes the implication).
    chain.apply(
        "DC+", select=[], into=lambda egi: egi.sheet, label="2i",
        note="Empty double cut — the scroll that will host the implication.",
    )

    # 2 — INS the antecedent into the outer (negative) cut.  Fresh x'-line.
    chain.apply(
        "INS", insert="[*xx] [*n] [*sn] [*z] (plus xx n z) (succ n sn)",
        into=_empty_scroll_outer, label="1i",
        note="Insert the antecedent ∃z plus(x,n,z) ∧ succ(n,sn) into the outer cut.",
    )

    # 3 — weld the inserted x'-line onto the parameter x (a join, sound in the
    # negative outer cut: insert =(x,x') there + merge).
    def weld_x(egi):
        cout = _cout(egi)
        xx = egi.nu[_by_rel(egi, cout, "plus")[0]][0]
        x = nav.child_vertices(egi, egi.sheet)[0]
        return instantiate_to_lines(egi, universal_cut=cout, joins=[(xx, x)])

    chain.apply_derived("join", weld_x, label="1i",
                        note="Weld the antecedent's x-line onto the parameter x.")

    # 4 — copy the antecedent (plus, then succ) into the inner (positive) cut.
    def cin(egi):
        return nav.child_cuts(egi, _cout(egi))[0]

    chain.apply("IT+", select=lambda egi: _by_rel(egi, _cout(egi), "plus")[0],
                into=cin, label="2it", note="Copy plus(x,n,z) into the proof cut.")
    chain.apply("IT+", select=lambda egi: _by_rel(egi, _cout(egi), "succ")[0],
                into=cin, label="2it", note="Copy succ(n,sn) into the proof cut.")

    # 5 — iterate the plus_step + succ_total axioms into the inner cut.
    chain.apply("IT+", select=_plus_step_cut, into=cin, label="2it",
                note="Iterate the plus_step axiom into the proof cut.")
    chain.apply("IT+", select=_succ_total_cut, into=cin, label="2it",
                note="Iterate succ-totality into the proof cut.")

    # role lines (stable by id through the rest): the antecedent's n, z, sn.
    def roles(egi):
        cout = _cout(egi)
        _, n, z = egi.nu[_by_rel(egi, cout, "plus")[0]]
        _, sn = egi.nu[_by_rel(egi, cout, "succ")[0]]
        return n, z, sn

    # 4a — succ-existence: instantiate the succ_total copy at w:=z, DC- to release
    # a witness sz with succ(z,sz) into the proof cut.
    def succ_witness(egi):
        _, z, _ = roles(egi)
        st = _succ_total_copy(egi, cin(egi))
        w = nav.child_vertices(egi, st)[0]
        return instantiate_to_lines(egi, universal_cut=st, joins=[(w, z)])

    chain.apply_derived("universal-instantiation", succ_witness, label="UI",
                        note="succ-totality at z: ∃sz succ(z,sz).")
    chain.apply("DC-", select=lambda egi: _succ_total_copy(egi, cin(egi)),
                label="2e", note="Release the successor witness succ(z,sz).")

    # 4b — instantiate plus_step at (x, n, z, sn, sz) — the premises in scope.
    def inst_plus_step(egi):
        n, z, sn = roles(egi)
        cn = cin(egi)
        sz = next(egi.nu[e][1] for e in _by_rel(egi, cn, "succ")
                  if egi.nu[e][0] == z)
        x = nav.child_vertices(egi, egi.sheet)[0]
        ps = _plus_step_copy(egi, cn)
        x5, x6, x7 = egi.nu[_by_rel(egi, ps, "plus")[0]]
        succs = _by_rel(egi, ps, "succ")
        x8 = next(egi.nu[e][1] for e in succs if egi.nu[e][0] == x6)
        x9 = next(egi.nu[e][1] for e in succs if egi.nu[e][0] == x7)
        return instantiate_to_lines(
            egi, universal_cut=ps,
            joins=[(x5, x), (x6, n), (x7, z), (x8, sn), (x9, sz)],
        )

    chain.apply_derived("universal-instantiation", inst_plus_step, label="UI",
                        note="Instantiate plus_step at the premises.")

    # 4c — deiterate the three antecedent relations of the instantiated axiom
    # (each a copy of a premise in the proof cut), then DC- to detach plus(x,sn,sz).
    def detach_step(egi):
        cn = cin(egi)
        ps = _plus_step_copy(egi, cn)
        g = egi
        from proof_authoring import apply_rule
        for r in ("plus", "succ", "succ"):
            g = apply_rule("IT-", g, selection=[_by_rel(g, ps, r)[0]])
        return apply_rule("DC-", g, selection=[ps])

    chain.apply_derived("modus-ponens", detach_step, label="2e/2e",
                        note="Deiterate the three antecedents, DC- → plus(x,sn,sz).")

    # 4d — ∃-generalise the value sz of plus(x,sn,sz) → a fresh existential z'.
    def gen_value(egi):
        n, z, sn = roles(egi)
        cn = cin(egi)
        cons = next(e for e in _by_rel(egi, cn, "plus") if egi.nu[e][1] == sn)
        return existential_generalization(egi, edge_id=cons, position=2,
                                          new_vertex_id="z2val")

    chain.apply_derived("existential-generalization", gen_value, label="EG",
                        note="value := ∃z' — the consequent ∃z' plus(x,sn,z').")

    # 4e — erase the spent premises in the (positive) proof cut: the antecedent
    # plus(x,n,z) and both succ relations, leaving exactly the consequent.
    def clear_proof_cut(egi):
        from proof_authoring import apply_rule
        n, z, sn = roles(egi)
        cn = cin(egi)
        g = egi
        ante = [e for e in _by_rel(g, cn, "plus") if g.nu[e][1] == n]
        for e in ante:
            g = apply_rule("ERA", g, selection=[e])
        for e in list(_by_rel(g, cin(g), "succ")):
            g = apply_rule("ERA", g, selection=[e])
        return g

    chain.apply_derived("erasure", clear_proof_cut, label="1e",
                        note="Erase the spent premises; the consequent remains.")

    # ⊢ (with the axioms surviving, since IT+ copies them) the step lemma scroll.
    goal = parse_egif(
        f"[*x] {PLUS_STEP_AX} {SUCC_TOTAL_AX} "
        "~[ [*n] [*sn] [*z] (plus x n z) (succ n sn) ~[ [*z2] (plus x sn z2) ] ]"
    )
    assert same_graph(chain.current, goal)


# --- the assembly: parametric totality of addition -------------------------- #
#
# ∀Y ∃z plus(x, Y, z) — totality of `+` for an arbitrary (free) x.  This is the
# induction *conclusion*, assembled by collapsing a hand-written induction
# instance against the two proven lemmas.
#
# The induction instance for φ(t) := ∃z plus(x,t,z), with x the shared ambient
# parameter (hand-written so x is ONE line, not the four α-renamed lines the
# schema generator would produce — see CURRENT_PLAN step 3):
#
#   ~[ ~[BASE]  ~[STEP]  [*Y] ~[ [*z](plus x Y z) ] ]
#     = ¬( base ∧ step ∧ ∃Y¬φ ) = (base ∧ step) → ∀Y φ(Y).
#
# ``~[BASE]`` and ``~[STEP]`` are *whole cuts* identical to the proven base /
# step lemmas sitting on the enclosing sheet — so each is removed by a single
# **cut-level IT-** (deiteration of a cut as a unit, the load-bearing capability
# this work added; flat-edge IT- could never reach a clause that is itself a
# cut).  Removing both collapses the outer cut to ``~[ [*Y] ~[ [*z](plus x Y z) ] ]``
# = ∀Y∃z plus(x,Y,z).
#
# CAVEAT (parametric, per CURRENT_PLAN): x is left FREE.  The closed object-level
# ∀x∀y∃z plus(x,y,z) additionally needs a sound universal generalisation of x;
# that move is not asserted here, so the result is stated honestly as parametric
# (totality for an arbitrary x), exactly as planned.

_T_BASE_LEMMA = "~[ [*o] (zero o) ~[ [*z] (plus x o z) ] ]"
_T_STEP_LEMMA = (
    "~[ [*n] [*sn] [*z] (plus x n z) (succ n sn) ~[ [*z2] (plus x sn z2) ] ]"
)
_T_IND_INSTANCE = (
    "~[ " + _T_BASE_LEMMA + " " + _T_STEP_LEMMA
    + " [*Y] ~[ [*z] (plus x Y z) ] ]"
)


def test_totality_assembly_parametric():
    """Collapse the induction instance against the proven base/step lemmas →
    ∀Y∃z plus(x,Y,z) (parametric totality of addition).

    Premises on one sheet, x shared throughout:
      • the base lemma   ``~[ [*o](zero o) ~[ [*z](plus x o z) ] ]``
        (proven in ``test_totality_base_lemma_existential``),
      • the step lemma   (proven in ``test_totality_step_lemma_existential``),
      • the induction instance for φ:=∃z plus(x,·,z) (a legitimate schema
        instance, asserted like an axiom instance).
    The two assembly moves are *cut-level* deiterations — the new capability."""
    chain = ProofChain.from_egif(
        f"[*x] {_T_BASE_LEMMA} {_T_STEP_LEMMA} {_T_IND_INSTANCE}"
    )

    def _ind_cut(egi):
        # The induction instance is the only sheet-child cut with no direct
        # edges (the base lemma has a `zero` edge; the step lemma `plus`/`succ`).
        # Robust before AND after deiteration removes its clause cuts.
        return [c for c in nav.child_cuts(egi, egi.sheet)
                if not nav.child_edges(egi, c)][0]

    def _base_clause(egi):
        return [c for c in nav.child_cuts(egi, _ind_cut(egi))
                if _by_rel(egi, c, "zero")][0]

    def _step_clause(egi):
        return [c for c in nav.child_cuts(egi, _ind_cut(egi))
                if _by_rel(egi, c, "succ")][0]

    chain.apply("IT-", select=_base_clause, label="2e",
                note="Deiterate ~[BASE] against the proven base lemma (cut-IT-).")
    chain.apply("IT-", select=_step_clause, label="2e",
                note="Deiterate ~[STEP] against the proven step lemma (cut-IT-).")

    # ⊢ the lemmas survive (deiteration removes the *copies*) and the induction
    # cut has collapsed to ∀Y∃z plus(x,Y,z).
    goal = parse_egif(
        f"[*x] {_T_BASE_LEMMA} {_T_STEP_LEMMA} ~[ [*Y] ~[ [*z] (plus x Y z) ] ]"
    )
    assert same_graph(chain.current, goal)
