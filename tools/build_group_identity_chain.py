"""
Build **uniqueness of the group identity** as a real transformation chain — the
Beta, *theory-relative* third fixture of the Organon import walkthrough
(``docs/archived/ORGANON_IMPORT_WALKTHROUGH.md`` §4.3), and the one that exercises
**multi-line universal instantiation** and **equality-as-ligature**.

    A1. ∀y. e·y = y     (e is a left identity)
    A2. ∀x. x·f = x     (f is a right identity)
    A3. single-valued   (M(x,y,z) ∧ M(x,y,w) → z = w)
        ────────────────────────────────────────────
                         ⊢  e = f

The classic one-liner ``e = e·f = f``.  Unlike Peirce's Law (⊢ φ from the blank
sheet) and like Barbara (Γ ⊢ φ from premises), this is *theory-relative* — true
relative to the three axioms — and it is the first fixture to step past purely
*logical* validity to a genuinely *mathematical* theorem.

Product ``x·y = z`` is the ternary relation ``(M x y z)``; equality is written the
native Peircean way, as a **line of identity** joining two spots (Arisbe's ``=``
edge / merged vertex), *not* a dyadic predicate — Sowa: "inserting a connection
between two nodes has the effect of identifying two nodes" (Fig. 14); Dau §16.6.
``e`` and ``f`` are two generic lines on the sheet (constants intern per-area in
this EGIF dialect, so a *shared* line is the faithful encoding of a named
individual referenced across cuts).

Eight steps, every one a real, attestable rule application:

    1. UI A1 (y := f)   instantiate A1 to the f-line   → (M e f f) on the sheet
    2. UI A2 (x := e)   instantiate A2 to the e-line   → (M e f e) on the sheet
    3. UI A3 (x,y,z,w := e,f,f,e)   *four lines at once* to the e/f constants
                        → ~[ (M e f f) (M e f e) ~[ =(e,f) ] ]   (instantiated scroll)
    4. IT-  deiterate the inner (M e f f)   (a copy of the sheet's)
    5. IT-  deiterate the inner (M e f e)
    6. DC-  erase the freed double cut       → =(e,f) on the sheet   (e = f ∎)
    7. ERA  erase the spent (M e f f)        (tidy the derived products away)
    8. ERA  erase the spent (M e f e)        → the bare theorem  e = f

Steps 1–3 are universal instantiation: 1–2 single-line to a sheet constant
(``derived_rules.instantiate_to_lines`` then a double-cut erase — Sowa's
1i·2i·2e·2e·3e for UI-to-a-name), 3 the **multi-line** instantiation of the
functionality axiom (the same derived move, four ``(source, target)`` joins in
one beat).  Steps 4–6 are detachment (modus ponens in EG form).  Because
coreference is unordered, A3's consequent landing as ``=(f,e)`` *is* the goal
``=(e,f)`` — the symmetry is free.  The derivation is original to Arisbe (the
theorem is folklore), at low warrant.  Import-safe (no side effects on import).
"""

import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eg_navigation as nav
from annotations import (
    SCOPE_CHAIN,
    SCOPE_STEP,
    SCOPE_UOD,
    annotations_to_list,
    make_annotation,
)
from derived_rules import instantiate_to_lines
from egi_core_dau import Edge, RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from proof_authoring import ProofChain, apply_rule
from provenance import authored_proof, make_provenance
from tomos_service import TransformationChain
from universe_of_discourse import UniverseOfDiscourse

UOD_ID = "group_identity"

# The two identities (e, f) are shared sheet lines; A3's consequent =(r,s) is
# added programmatically (the ``=`` relation is not part of the EGIF surface).
_BASE_EGIF = (
    "[*e] [*f] "
    "~[ [*y] ~[ (M e y y) ] ] "            # A1: forall y. e*y = y
    "~[ [*x] ~[ (M x f x) ] ] "            # A2: forall x. x*f = x
    "~[ [*p][*q][*r][*s] (M p q r) (M p q s) ~[ ] ]"  # A3 skeleton (=(r,s) added below)
)


# --------------------------------------------------------------------------- #
# Structural locators (re-resolved against the current state each step)        #
# --------------------------------------------------------------------------- #

def _sheet_cuts(g) -> List[str]:
    return [c.id for c in g.Cut if nav.area_of(g, c.id) == g.sheet]


def _a3_outer(g):
    """A3's outer cut — the only sheet-cut holding ``M`` edges *directly*."""
    for c in _sheet_cuts(g):
        if nav.child_edges(g, c, "M"):
            return c
    return None


def _nested_m_cut(g, predicate_test):
    """A sheet-cut whose single nested cut holds an ``M`` matching ``predicate_test``
    on its ν-tuple.  Distinguishes A1 (``M(?, y, y)``) from A2 (``M(x, f, x)``)."""
    for c in _sheet_cuts(g):
        inner = nav.child_cuts(g, c)
        if not inner or nav.child_edges(g, c, "M"):
            continue
        ms = nav.child_edges(g, inner[0], "M")
        if ms and predicate_test(g.nu[ms[0]]):
            return c, ms[0], g.nu[ms[0]]
    return None


def _a1_outer(g):
    """A1 = ``~[ [*y] ~[ (M e y y) ] ]`` — nested M with ``nu[1] == nu[2]``."""
    return _nested_m_cut(g, lambda nu: nu[1] == nu[2])


def _a2_outer(g):
    """A2 = ``~[ [*x] ~[ (M x f x) ] ]`` — nested M with ``nu[0] == nu[2] != nu[1]``."""
    return _nested_m_cut(g, lambda nu: nu[0] == nu[2] and nu[1] != nu[2])


def _double_cut_over_equality(g):
    """The bare double cut ``~[ ~[ =(e,f) ] ]`` left after detachment."""
    for c in _sheet_cuts(g):
        inner = nav.child_cuts(g, c)
        if (
            len(list(g.area.get(c, ()))) == 1
            and inner
            and any(g.rel.get(e) == "=" for e in g.area.get(inner[0], ()))
        ):
            return c
    return None


def build_base() -> Tuple[RelationalGraphWithCuts, str, str]:
    """Parse the axioms, attach A3's equality ligature, and identify the e/f
    lines.  Returns ``(egi, e_vertex_id, f_vertex_id)``."""
    g = parse_egif(_BASE_EGIF)
    a3o = _a3_outer(g)
    ms = nav.child_edges(g, a3o, "M")
    r, s = g.nu[ms[0]][2], g.nu[ms[1]][2]           # A3's z, w lines
    inner = nav.child_cuts(g, a3o)[0]
    g = g.with_edge(Edge(id="e_A3eq"), (r, s), "=", inner)   # =(z, w) consequent
    e_id = _a1_outer(g)[2][0]                        # e = arg0 of A1's M(e, y, y)
    f_id = _a2_outer(g)[2][1]                        # f = arg1 of A2's M(x, f, x)
    return g, e_id, f_id


# --------------------------------------------------------------------------- #
# The proof                                                                    #
# --------------------------------------------------------------------------- #

def build_group_identity_chain() -> Tuple[TransformationChain, UniverseOfDiscourse]:
    """Construct uniqueness-of-the-group-identity as a real ``TransformationChain``."""
    base, e_id, f_id = build_base()

    def ui_a1(g):
        """UI A1 (y := f): instantiate to the f-line, then erase the double cut →
        (M e f f) on the sheet."""
        c, m, nu = _a1_outer(g)
        g = instantiate_to_lines(g, universal_cut=c, joins=[(nu[1], f_id)],
                                 edge_id_prefix="e_ui_a1")
        return apply_rule("DC-", g, selection=[c])

    def ui_a2(g):
        """UI A2 (x := e): instantiate to the e-line, then erase the double cut →
        (M e f e) on the sheet."""
        c, m, nu = _a2_outer(g)
        g = instantiate_to_lines(g, universal_cut=c, joins=[(nu[0], e_id)],
                                 edge_id_prefix="e_ui_a2")
        return apply_rule("DC-", g, selection=[c])

    def ui_a3(g):
        """UI A3 (x,y,z,w := e,f,f,e): the multi-line instantiation — four lines
        joined to the two constants in a single derived move."""
        c = _a3_outer(g)
        ms = nav.child_edges(g, c, "M")
        p, q, r = g.nu[ms[0]][0], g.nu[ms[0]][1], g.nu[ms[0]][2]
        s = g.nu[ms[1]][2]
        return instantiate_to_lines(
            g, universal_cut=c,
            joins=[(p, e_id), (q, f_id), (r, f_id), (s, e_id)],
            edge_id_prefix="e_ui_a3",
        )

    def inner_m(g):
        """An ``M`` still nested inside A3's instantiated scroll — the deiteration
        candidate (a copy of a sheet-level instance)."""
        return nav.child_edges(g, _a3_outer(g), "M")[0]

    def sheet_m(g):
        """A spent ``(M e f …)`` left on the sheet after detachment."""
        return [e.id for e in g.E
                if g.rel.get(e.id) == "M" and nav.area_of(g, e.id) == g.sheet][0]

    author = (
        ProofChain(base)
        .apply_derived(
            "UI", ui_a1, label="1i·2i·2e·2e·3e",
            note="Universal instantiation of A1 at y := f → (M e f f) asserted on "
                 "the sheet (e·f = f). Single-line UI-to-a-name: insert the "
                 "f-connection, merge, erase the freed double cut (Sowa Fig. 14; "
                 "Dau §16).",
        )
        .apply_derived(
            "UI", ui_a2, label="1i·2i·2e·2e·3e",
            note="Universal instantiation of A2 at x := e → (M e f e) on the sheet "
                 "(e·f = e).",
        )
        .apply_derived(
            "UI", ui_a3, label="multi-line",
            note="The centerpiece: instantiate the functionality axiom A3's FOUR "
                 "lines (x,y,z,w) to the two constants (e,f,f,e) in a single move "
                 "→ ~[ (M e f f) (M e f e) ~[ =(e,f) ] ]. Multi-line universal "
                 "instantiation; the consequent =(z,w) lands as the goal ligature "
                 "=(e,f) (coreference is unordered, so f=e IS e=f).",
        )
        .apply("IT-", select=inner_m, label="2e",
               note="Deiterate the inner (M e f f) — a copy of the sheet's e·f = f.")
        .apply("IT-", select=inner_m, label="2e",
               note="Deiterate the inner (M e f e) — a copy of the sheet's e·f = e. "
                    "A3's antecedent is now discharged.")
        .apply("DC-", select=_double_cut_over_equality, label="3e",
               note="Erase the freed double cut → =(e,f) asserted on the sheet. "
                    "The left identity equals the right identity: e = f ∎.")
        .apply("ERA", select=sheet_m, label="1e",
               note="Erase the spent (M e f …) from the sheet (a derived product, "
                    "no longer needed).")
        .apply("ERA", select=sheet_m, label="1e",
               note="Erase the remaining derived product → the bare theorem e = f.")
    )
    return author.to_uod(
        uod_id=UOD_ID,
        name="Uniqueness of the Group Identity",
        description=(
            "A1 (∀y. e·y = y), A2 (∀x. x·f = x), A3 (single-valued) ⊢ e = f — the "
            "left identity equals the right identity, the classic e = e·f = f. A "
            "Beta, theory-relative theorem (Γ ⊢ φ from axioms) and the first "
            "fixture to exercise multi-line universal instantiation (A3's four "
            "lines to two constants at once) and equality-as-ligature. The "
            "derivation is original to Arisbe (the theorem is folklore); every "
            "step a real, attestable rule application."
        ),
    )


# --------------------------------------------------------------------------- #
# Provenance + annotations                                                     #
# --------------------------------------------------------------------------- #

_THEOREM_SOURCE = {
    "type": "manuscript",
    "title": "Uniqueness of the identity element (folklore)",
    "note": "Standard one-line group-theory lemma: e = e·f = f, where e is a "
            "left identity and f a right identity. No single canonical source.",
}
_METHOD_SOURCES = [
    {"type": "book", "author": "Dau, Frithjof",
     "title": "Mathematical Logic with Diagrams",
     "note": "§16.1 derived rules for ligatures (Lem 16.2 extending a ligature; "
             "Def 16.6 merging vertices, ctx(v1) ≥ ctx(e) = ctx(v2)); §17 "
             "soundness — the warrant for multi-line instantiation."},
    {"type": "article-journal", "author": "Sowa, John F.",
     "title": "Conceptual Graphs (Handbook of Knowledge Representation, ch. 5)",
     "year": "2008",
     "note": "Fig. 14: UI as iterate-and-join; 'inserting a connection between "
             "two nodes identifies them' — equality is the ligature, not a dyadic "
             "predicate."},
    {"type": "book", "author": "Roberts, Don D.",
     "title": "The Existential Graphs of Charles S. Peirce",
     "year": "1973", "bibkey": "roberts1973existential"},
]


def group_identity_provenance() -> dict:
    return make_provenance(
        theorem_source=_THEOREM_SOURCE,
        proof_source=authored_proof("Arisbe", system="Peirce–Sowa EGIF"),
        method_sources=_METHOD_SOURCES,
    ).to_dict()


def group_identity_annotations() -> List[dict]:
    anns = [
        make_annotation(
            SCOPE_UOD,
            "Uniqueness of the group identity (e = f) — the first tomos fixture "
            "that is genuinely *mathematical* (true relative to the three axioms, "
            "Γ ⊢ φ) rather than purely logical, and the first to carry equality "
            "as a line of identity rather than a predicate.",
            tags=["pedagogy", "theory-relative"],
        ),
        make_annotation(
            SCOPE_CHAIN,
            "The shape is the one-liner e = e·f = f: derive e·f = f and e·f = e "
            "(steps 1–2), then single-valuedness forces f = e (steps 3–6). The "
            "axioms are consumed (a Γ ⊢ φ derivation may spend its premises); the "
            "conclusion stands alone as the bare equality.",
        ),
        make_annotation(
            SCOPE_STEP,
            "Multi-line universal instantiation: A3's four lines (x,y,z,w) are "
            "joined to the two constants (e,f,f,e) in a single move — four "
            "'insert a connection' ligatures at once (Sowa Fig. 14; Dau §16.6). "
            "This is where an engine that handles one line at a time, or drops a "
            "coreference, would fail; the consequent =(z,w) lands as =(e,f), and "
            "because coreference is unordered that IS the goal (no e=f vs f=e "
            "bookkeeping).",
            step_id="step-3", tags=["crux", "beta-crux", "fixture", "multi-line"],
        ),
    ]
    return annotations_to_list(anns)


# --------------------------------------------------------------------------- #
# Conclusion check + persistence                                              #
# --------------------------------------------------------------------------- #

def _is_bare_equality(g) -> bool:
    """The conclusion is exactly ``e = f``: two distinct sheet lines, one ``=``
    edge joining them on the sheet, and nothing else.  Checked structurally so it
    is independent of the (randomly generated) vertex ids."""
    if g.Cut or len(g.E) != 1 or len(g.V) != 2:
        return False
    (eq,) = [e.id for e in g.E]
    return (
        g.rel.get(eq) == "="
        and nav.area_of(g, eq) == g.sheet
        and set(g.nu[eq]) == {v.id for v in g.V}
        and all(nav.area_of(g, v.id) == g.sheet for v in g.V)
    )


def main(argv=None) -> int:
    from tomos_service import TomosService

    chain, uod = build_group_identity_chain()
    assert _is_bare_equality(uod.current_egi), (
        "built proof does not reduce to the bare equality e = f"
    )

    tomos_root = Path(__file__).resolve().parent.parent / "tomos"
    service = TomosService(tomos_root)
    service.save_uod_with_chain(uod, chain, provenance=group_identity_provenance())
    service.save_annotations(uod, group_identity_annotations())
    print(f"Saved '{uod.uod_id}' with a {len(chain.steps)}-step chain.")
    print(f"  rules: {' → '.join(s.rule_name for s in chain.steps)}")
    print("  final: e = f  (a single = ligature on the sheet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
