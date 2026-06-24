"""
Contract tests for the semantic game (``src/semantic_game.py``).

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md`` §6.

The semantic game evaluates a proposed graph G against a model M (reached through a
``DomainOracle``) outside-in, with three-valued Kleene logic.  These pin the core
truth table: ground atoms, negation, conjunction, the scroll (implication), the
universal with a line crossing a cut boundary, and existential witness selection —
each in both the **open** world (a miss is UNKNOWN) and the **closed** world (a miss
is FALSE / negation-as-failure).
"""

from egif_parser_dau import parse_egif

from domain_oracle import CorpusOracle
from semantic_game import Verdict3, evaluate


def M(closed=False, **named):
    return CorpusOracle.from_egif(named, closed=closed)


def verdict(egif, oracle):
    return evaluate(parse_egif(egif), oracle).verdict


# A small worked domain.
BISCUIT = '(dog "Biscuit") (mammal "Biscuit") (warmblooded "Biscuit")'


# ---------------------------------------------------------------------------
# Ground atoms
# ---------------------------------------------------------------------------

def test_present_atom_is_true_either_world():
    assert verdict('(dog "Biscuit")', M(animals=BISCUIT)) is Verdict3.TRUE
    assert verdict('(dog "Biscuit")', M(closed=True, animals=BISCUIT)) is Verdict3.TRUE


def test_absent_atom_open_is_unknown_closed_is_false():
    assert verdict('(dog "Rex")', M(animals=BISCUIT)) is Verdict3.UNKNOWN
    assert verdict('(dog "Rex")', M(closed=True, animals=BISCUIT)) is Verdict3.FALSE


def test_conjunction_all_present_true():
    assert verdict('(dog "Biscuit") (mammal "Biscuit")', M(animals=BISCUIT)) is Verdict3.TRUE


def test_conjunction_one_missing_open_unknown_closed_false():
    assert verdict('(dog "Biscuit") (reptile "Biscuit")', M(animals=BISCUIT)) is Verdict3.UNKNOWN
    assert verdict('(dog "Biscuit") (reptile "Biscuit")',
                   M(closed=True, animals=BISCUIT)) is Verdict3.FALSE


# ---------------------------------------------------------------------------
# Negation — present vs absent, and the monotonicity asymmetry
# ---------------------------------------------------------------------------

def test_negation_of_present_atom_is_false_either_world():
    # man(Socrates) holds → ~[man(Socrates)] is definitely false, even open-world,
    # because M only grows (a present fact stays present).
    m = M(facts='(man "Socrates")')
    assert verdict('~[ (man "Socrates") ]', m) is Verdict3.FALSE
    assert verdict('~[ (man "Socrates") ]', M(closed=True, facts='(man "Socrates")')) is Verdict3.FALSE


def test_negation_of_absent_atom_open_unknown_closed_true():
    # Nothing known about Rex.  Open: ~[man(Rex)] is UNKNOWN; closed (NAF): TRUE.
    assert verdict('~[ (man "Rex") ]', M(facts='(man "Socrates")')) is Verdict3.UNKNOWN
    assert verdict('~[ (man "Rex") ]', M(closed=True, facts='(man "Socrates")')) is Verdict3.TRUE


# ---------------------------------------------------------------------------
# The scroll (implication) — the open-world subtlety
# ---------------------------------------------------------------------------

def test_ground_implication_both_present_is_true_even_open_world():
    # man(S)→mortal(S), both present: TRUE even open-world (the residue lift must
    # NOT fire on a ground formula).
    m = M(facts='(man "Socrates") (mortal "Socrates")')
    assert verdict('~[ (man "Socrates") ~[ (mortal "Socrates") ] ]', m) is Verdict3.TRUE


def test_ground_implication_antecedent_only_open_unknown_closed_false():
    m_open = M(facts='(man "Socrates")')
    m_closed = M(closed=True, facts='(man "Socrates")')
    g = '~[ (man "Socrates") ~[ (mortal "Socrates") ] ]'
    assert verdict(g, m_open) is Verdict3.UNKNOWN     # mortal(S) might hold in a larger M
    assert verdict(g, m_closed) is Verdict3.FALSE     # man but provably not mortal


# ---------------------------------------------------------------------------
# The universal (a shared line crossing a cut boundary)
# ---------------------------------------------------------------------------

def test_universal_closed_true_open_unknown():
    # ∀x(man(x)→mortal(x)) over a domain where the one man is mortal.
    g = '~[ (man *x) ~[ (mortal x) ] ]'
    m = M(facts='(man "Socrates") (mortal "Socrates")')
    assert verdict(g, m) is Verdict3.UNKNOWN                       # open: can't confirm ∀
    assert verdict(g, M(closed=True, facts='(man "Socrates") (mortal "Socrates")')) is Verdict3.TRUE


def test_universal_false_with_counterexample_closed():
    # A man who is provably not mortal refutes ∀x(man→mortal) in a closed world.
    g = '~[ (man *x) ~[ (mortal x) ] ]'
    m = M(closed=True, facts='(man "Socrates") (man "Zeus") (mortal "Socrates")')
    assert verdict(g, m) is Verdict3.FALSE


# ---------------------------------------------------------------------------
# Existential witness selection
# ---------------------------------------------------------------------------

def test_existential_true_when_a_witness_works():
    # ∃x (P(x) ∧ ¬Q(x)).  P holds for a,b; Q only for a.  Witness x=b succeeds.
    g = '(P *x) ~[ (Q x) ]'
    m = M(closed=True, facts='(P "a") (P "b") (Q "a")')
    assert verdict(g, m) is Verdict3.TRUE


def test_existential_false_when_every_witness_defeated_closed():
    # ∃x (P(x) ∧ ¬Q(x)) but Q holds for every P — false in a closed world.
    g = '(P *x) ~[ (Q x) ]'
    m = M(closed=True, facts='(P "a") (P "b") (Q "a") (Q "b")')
    assert verdict(g, m) is Verdict3.FALSE


def test_existential_open_world_unknown_when_unsatisfied():
    g = '(P *x) ~[ (Q x) ]'
    m = M(facts='(P "a") (Q "a")')   # open
    assert verdict(g, m) is Verdict3.UNKNOWN


def test_simple_existential_present():
    assert verdict('(dog *x)', M(animals=BISCUIT)) is Verdict3.TRUE


# ---------------------------------------------------------------------------
# Result wrapper + transcript
# ---------------------------------------------------------------------------

def test_counterexample_named_on_false_universal():
    # The student's Whale and the physician's Biscuit: the individual that defeats
    # the universal must be surfaced structurally, not just buried in the transcript.
    student = evaluate(
        parse_egif('~[ (seacreature *x) ~[ (coldblooded x) ] ]'),
        M(closed=True, sea='(seacreature "Whale") (warmblooded "Whale") '
                          '(seacreature "Cod") (coldblooded "Cod")'))
    assert student.verdict is Verdict3.FALSE
    assert student.counterexample == {"x": "Whale"}
    assert student.winning_witness is None

    physician = evaluate(
        parse_egif('~[ (mammal *x) ~[ (warmblooded x) ] ]'),
        M(closed=True, ward='(mammal "Biscuit") (mammal "Whale") (warmblooded "Whale")'))
    assert physician.verdict is Verdict3.FALSE
    assert physician.counterexample == {"x": "Biscuit"}


def test_winning_witness_named_on_true_existential():
    res = evaluate(parse_egif('(P *x) ~[ (Q x) ]'),
                   M(closed=True, f='(P "a") (P "b") (Q "a")'))
    assert res.verdict is Verdict3.TRUE
    assert res.winning_witness == {"x": "b"}   # b is the witness that escapes Q
    assert res.counterexample is None


def test_witness_vertex_ids_locate_the_deciding_line_on_G():
    # The deciding line token must also carry the *G vertex id* of the line it names,
    # so the drawing of G can be highlighted at the line that decided the verdict
    # (the board-in-Agon hook — token→individual says who, this says where).
    g = parse_egif('(P *x) ~[ (Q x) ]')
    res = evaluate(g, M(closed=True, f='(P "a") (P "b") (Q "a")'))
    assert res.verdict is Verdict3.TRUE
    assert res.witness_vertex_ids is not None
    assert set(res.witness_vertex_ids) == set(res.winning_witness)   # same tokens
    generic_ids = {v.id for v in g.V if v.is_generic}
    assert res.witness_vertex_ids["x"] in generic_ids               # a real G line

    # The counterexample line is located on G too (the student's Whale).
    sg = parse_egif('~[ (seacreature *x) ~[ (coldblooded x) ] ]')
    student = evaluate(sg, M(closed=True,
                             sea='(seacreature "Whale") (warmblooded "Whale")'))
    assert student.verdict is Verdict3.FALSE
    assert set(student.witness_vertex_ids) == set(student.counterexample)
    assert student.witness_vertex_ids["x"] in {v.id for v in sg.V if v.is_generic}

    # An UNKNOWN verdict has no decisive line — nothing to light.
    unknown = evaluate(parse_egif('(dog "Rex")'), M(animals=BISCUIT))  # open, absent
    assert unknown.verdict is Verdict3.UNKNOWN
    assert unknown.witness_vertex_ids is None


def test_result_holds_and_transcript():
    res = evaluate(parse_egif('(dog "Biscuit")'), M(animals=BISCUIT))
    assert res.holds is True
    assert res.transcript                      # outside-in narration present
    assert "Proposer wins" in res.summary

    res2 = evaluate(parse_egif('(dog "Rex")'), M(closed=True, animals=BISCUIT))
    assert res2.holds is False
    assert "Skeptic wins" in res2.summary
