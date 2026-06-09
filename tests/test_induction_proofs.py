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
from derived_rules import instantiate_to_lines
from eg_navigation import same_graph
from eg_splice import graft
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain
from schema import Schema, instance_of_schema

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
