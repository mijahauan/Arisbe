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
ORD_INDUCTION_EGIF = (
    "~[ ~[ [*o] (zero o) ~[ ⟨phi: o⟩ ] ] "
    "   ~[ [*n] [*sn] ⟨phi: n⟩ (succ n sn) ~[ ⟨phi: sn⟩ ] ] "
    "   ~[ [*Y] ~[ ⟨phi: Y⟩ ] ] ]"
)


def test_ordinary_induction_schema_instantiates():
    """The base+step induction schema (4 occurrences of φ) parses and
    instantiates hole-free — a second, independent schema fixture."""
    ord_ind = Schema.from_egif(ORD_INDUCTION_EGIF)
    assert ord_ind.holes == {"phi": 1}            # φ is unary…
    assert len(ord_ind.occurrences("phi")) == 4   # …occurring four times (o, n, sn, Y)
    inst = instantiate(ord_ind, "[*k] (big k)", ports=["k"])
    assert "phi" not in set(inst.rel.values())
    assert same_graph(parse_egif(generate_egif(inst)), inst)


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
