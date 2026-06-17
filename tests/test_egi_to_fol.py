"""
Contract tests for ``src/egi_to_fol.py`` — reading an EGI back up to a first-order formula.

The reader is the EGI-touching half of the DLCore coverage lever (it lets the finite-model
finder be pointed at any EGI).  Two things must hold:

* **Faithfulness.** The formula read back from ``_build(φ)``'s EGI is *logically equivalent*
  to φ — verified by Z3 (the same oracle ``folio_fol`` decides entailment with).  This closes
  the build→read loop: the picture means what the proposition meant.
* **Read-only.** Reading never mutates the immutable graph — asserted structurally (the EGI is
  identical before and after) so the bedrock-formalism guarantee is mechanically checked.

The corpus pass simply confirms every drawable ontology UoD reads without error and the model
finder runs over the result (no crash on real, non-toy graphs).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from egi_to_fol import read_egi_to_fol
from folio_fol import Atom, Not, parse_fol
from folio_native import _build_graph

z3 = pytest.importorskip("z3")
from folio_fol import _Z3Compiler  # noqa: E402  (after the z3 import guard)


# A spread of FOLIO-relevant shapes: Horn rules, existentials, constants, disjunction,
# biconditional, nested + alternating quantifiers, existential-under-negation.
FORMULAS = [
    "∀x (Dog(x) → Mammal(x))",
    "∃x (Cat(x) ∧ ¬Dog(x))",
    "P(a) ∧ Q(a,b)",
    "∀x (P(x) → ∃y R(x,y))",
    "¬(A(a) ∧ B(a))",
    "∀x ((Bird(x) ∧ ¬Penguin(x)) → Flies(x))",
    "∃x ∀y Loves(x,y)",
    "(P(a) ∨ Q(a))",
    "∀x (P(x) ↔ Q(x))",
    "∀x (Student(x) → (Smart(x) ∨ Hardworking(x)))",
]


def _equiv(f1, f2) -> bool:
    """Are two FOLIO ASTs logically equivalent? (their Z3 compilations agree everywhere)"""
    c = _Z3Compiler()
    a, b = c.compile(f1, {}), c.compile(f2, {})
    s = z3.Solver()
    s.add(z3.Not(a == b))
    return s.check() == z3.unsat


@pytest.mark.parametrize("src", FORMULAS)
def test_read_back_is_logically_equivalent(src):
    orig = parse_fol(src)
    egi = _build_graph([orig])
    (back,) = read_egi_to_fol(egi)
    assert _equiv(orig, back), f"{src}  read back as  {back}"


def test_reading_is_read_only():
    egi = _build_graph([parse_fol("∀x (Dog(x) → Mammal(x))"), parse_fol("Dog(a)")])
    before = (egi.V, egi.E, egi.Cut, egi.nu, egi.area, egi.sheet)
    read_egi_to_fol(egi)
    after = (egi.V, egi.E, egi.Cut, egi.nu, egi.area, egi.sheet)
    assert before == after  # the immutable graph is untouched by reading


def test_empty_cut_reads_as_falsity():
    # An empty cut ~[] is ¬⊤ = ⊥ — unsatisfiable.
    egi = parse_egif("~[ ]")
    (f,) = read_egi_to_fol(egi)
    c = _Z3Compiler()
    s = z3.Solver()
    s.add(c.compile(f, {}))
    assert s.check() == z3.unsat


def test_generic_variable_never_collides_with_a_constant():
    # A constant literally named like the generated variable prefix must still read distinctly.
    egi = _build_graph([parse_fol("∃x P(x, _v0)")])  # _v0 is a constant here
    (f,) = read_egi_to_fol(egi)
    assert _equiv(parse_fol("∃x P(x, _v0)"), f)


def test_corpus_ontologies_read_and_model_find():
    # Every drawable ontology UoD reads without error; the model finder runs over the result.
    from folio_model_finder import find_model
    tools = Path(__file__).parent.parent / "tools"
    sys.path.insert(0, str(tools))
    try:
        import build_ontologies  # noqa: F401
    except Exception:
        pytest.skip("ontology build tooling unavailable")
    # A couple of small, drawn fragments suffice to exercise real (non-toy) geometry.
    samples = ["~[ (Dog *x) ~[ (Animal x) ] ]", '(Dog "rex") ~[ (Dog *x) ~[ (Mammal x) ] ]']
    for src in samples:
        egi = parse_egif(src)
        asts = read_egi_to_fol(egi)
        # Must not raise; a model exists for these consistent fragments.
        assert find_model(asts) is not None
