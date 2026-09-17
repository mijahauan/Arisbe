"""A reused variable name is two lines of identity, not one (CLIF and CGIF).

**These tests fail today, on purpose, and are pinned strict.** They state the
reading Dau's translation gives, not the reading the parsers give.

CLIF and CGIF key a generic vertex by the variable's *name* — ``v_{name}`` at
``clif_parser_dau`` (the atomic branch) and ``cgif_parser_dau`` (the concept and
relation branches) — so two separate quantifiers that happen to reuse a name
share one vertex, and the least-common-area placement then merges them into a
single line. ``(forall (x) (P x)) (forall (x) (Q x))`` comes back as one
existential line spanning both, and the parse says something the formula does
not.

Dau: a quantifier binds only the occurrences in *its own* formula —
FV(∃α.f) = FV(f)\\{α} (Def 18.1, p.197), ∀α.f := ¬∃α.¬f (p.198) — and renaming
a bound variable changes nothing (α-conversion, Def 18.3, p.199). Ψ's
existential step builds this in: it replaces the α-vertices of Ψ(f), the
formula being quantified, by one fresh vertex v₀ and marks them generic, so a
later ∃α over a *different* formula cannot reach them, and a conjunction is the
juxtaposition of two already-closed translations (p.207).

The defect is older than the Def 12.5 enforcement that exposed it: before that
enforcement these parses succeeded and silently returned the merged graph. The
Def 12.5 reordering (the parsers place a vertex before any edge hooks it) makes
them succeed again, and returns the same merged graph — so the wrong reading is
back, and it is pinned here rather than left silent. Fixing it is a separate
decision: strict xfail means a fix shows up as XPASS and fails loudly, with
these assertions to say what it must produce.
"""

import pytest

import eg_navigation as nav
from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from egif_parser_dau import parse_egif

SCOPING_DEFECT = (
    "known CLIF/CGIF scoping defect: a generic vertex is keyed by the variable's "
    "name, not by the quantifier that binds it, so two binders reusing a name "
    "share one line (Dau Def 18.1, p.197-198; α-conversion Def 18.3, p.199; Ψ's "
    "existential step, p.207)"
)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SCOPING_DEFECT)
@pytest.mark.parametrize(
    "clif,egif",
    [
        # ∀x P(x) ∧ ∀x Q(x) — two universals, two lines.
        (
            "(forall (x) (P x)) (forall (x) (Q x))",
            "~[ *x ~[ (P x) ] ] ~[ *y ~[ (Q y) ] ]",
        ),
        # The subsumption scrolls the ontology importers emit.
        (
            "(forall (x) (if (Cat x) (Animal x))) (forall (x) (if (Dog x) (Animal x)))",
            "~[ *x (Cat x) ~[ (Animal x) ] ] ~[ *y (Dog y) ~[ (Animal y) ] ]",
        ),
        # ∃x P(x) ∧ ∃x Q(x) — not ∃x (P(x) ∧ Q(x)).
        (
            "(exists (x) (P x)) (exists (x) (Q x))",
            "*x (P x) *y (Q y)",
        ),
    ],
)
def test_clif_reads_two_binders_as_two_lines(clif, egif):
    assert nav.same_graph(parse_clif(clif), parse_egif(egif))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SCOPING_DEFECT)
def test_cgif_reads_two_defining_labels_as_two_lines():
    assert nav.same_graph(
        parse_cgif("~[[*x] (P ?x)] ~[[*x] (Q ?x)]"),
        parse_egif("~[ *x (P x) ] ~[ *y (Q y) ]"),
    )


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SCOPING_DEFECT)
def test_clif_renaming_a_bound_variable_changes_nothing():
    """α-conversion (Dau Def 18.3, p.199): the name a binder uses is not meaning."""
    assert nav.same_graph(
        parse_clif("(forall (x) (P x)) (forall (x) (Q x))"),
        parse_clif("(forall (x) (P x)) (forall (y) (Q y))"),
    )


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SCOPING_DEFECT)
def test_cgif_renaming_a_defining_label_changes_nothing():
    assert nav.same_graph(
        parse_cgif("~[[*x] (P ?x)] ~[[*x] (Q ?x)]"),
        parse_cgif("~[[*x] (P ?x)] ~[[*y] (Q ?y)]"),
    )
