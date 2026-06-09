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
