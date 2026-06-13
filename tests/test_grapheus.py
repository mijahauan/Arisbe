"""
Contract tests for the automated Grapheus (``src/grapheus.py``).

Design-of-record: ``docs/AUTOMATED_GRAPHEUS.md``.

The load-bearing invariant (increment 1): the move-by-move contest, played by *local*
minimax decisions (defender maximises, challenger minimises each option's local value),
reaches a terminal whose verdict equals the one-shot peel ``semantic_game.evaluate``.
If the stepping is wrong anywhere — ownership by polarity, the per-cut role swap, the
existential/conjunction phases, the open-world UNKNOWN — self-play diverges from the
evaluator and these fail.  Pinned across shapes (atoms, conjunction, negation, the
scroll, the universal crossing a cut, existential witnessing) in both worlds, plus the
real ``skos_core`` model and a slice of the tomos corpus.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from egif_parser_dau import parse_egif

from domain_oracle import CorpusOracle
from grapheus import GrapheusContest, Outcome, Player, play
from semantic_game import Verdict3, evaluate


def M(closed=False, **named):
    return CorpusOracle.from_egif(named, closed=closed)


BISCUIT = '(dog "Biscuit") (mammal "Biscuit") (warmblooded "Biscuit")'
SOCRATES = '(man "Socrates") (mortal "Socrates")'


# A spread of (label, G-egif, oracle) cases covering the truth table in both worlds.
CASES = [
    # ground atoms
    ("present atom", '(dog "Biscuit")', M(a=BISCUIT)),
    ("present atom closed", '(dog "Biscuit")', M(closed=True, a=BISCUIT)),
    ("absent atom open", '(dog "Rex")', M(a=BISCUIT)),
    ("absent atom closed", '(dog "Rex")', M(closed=True, a=BISCUIT)),
    # conjunction
    ("conj all present", '(dog "Biscuit") (mammal "Biscuit")', M(a=BISCUIT)),
    ("conj one missing open", '(dog "Biscuit") (reptile "Biscuit")', M(a=BISCUIT)),
    ("conj one missing closed", '(dog "Biscuit") (reptile "Biscuit")', M(closed=True, a=BISCUIT)),
    # negation
    ("neg of present", '~[ (man "Socrates") ]', M(f=SOCRATES)),
    ("neg of absent open", '~[ (man "Rex") ]', M(f=SOCRATES)),
    ("neg of absent closed", '~[ (man "Rex") ]', M(closed=True, f=SOCRATES)),
    # double negation
    ("double neg present", '~[ ~[ (man "Socrates") ] ]', M(f=SOCRATES)),
    # the scroll (implication) — ground
    ("scroll true", '~[ (man "Socrates") ~[ (mortal "Socrates") ] ]', M(f=SOCRATES)),
    ("scroll false closed", '~[ (man "Socrates") ~[ (rich "Socrates") ] ]', M(closed=True, f=SOCRATES)),
    # existential
    ("exists present", '(dog *x)', M(a=BISCUIT)),
    ("exists absent open", '(unicorn *x)', M(a=BISCUIT)),
    ("exists absent closed", '(unicorn *x)', M(closed=True, a=BISCUIT)),
    # the universal with a line crossing a cut boundary
    ("universal holds closed",
     '~[ (man *x) ~[ (mortal x) ] ]', M(closed=True, f=SOCRATES)),
    ("universal counterexample closed",
     '~[ (man *x) ~[ (mortal x) ] ]', M(closed=True, f='(man "Zeus")')),
]


@pytest.mark.parametrize("label,egif,oracle", CASES, ids=[c[0] for c in CASES])
def test_selfplay_matches_evaluate(label, egif, oracle):
    g = parse_egif(egif)
    expected = evaluate(g, oracle).verdict
    result = play(g, oracle)
    assert result.is_over
    assert result.verdict is expected, (
        f"{label}: self-play {result.verdict} != evaluate {expected}\n"
        + "\n".join(result.transcript)
    )


def test_outcome_maps_verdict():
    assert play(parse_egif('(dog "Biscuit")'), M(a=BISCUIT)).outcome is Outcome.GRAPHIST_WINS
    assert play(parse_egif('~[ (dog "Biscuit") ]'), M(a=BISCUIT)).outcome is Outcome.GRAPHEUS_WINS
    assert play(parse_egif('(dog "Rex")'), M(a=BISCUIT)).outcome is Outcome.INDEPENDENT


# ---------------------------------------------------------------------------
# The real model — skos_core's materialised closure as the opponent
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def skos_oracle():
    from domain_model_importer import from_rdf_file
    from model_materialization import materialize_egi
    from egif_generator_dau import generate_egif

    facts, _ = materialize_egi(from_rdf_file(ROOT / "corpus" / "ontologies" / "skos_core.ttl").egi)
    return CorpusOracle.from_egif({"skos": generate_egif(facts)})


@pytest.mark.parametrize("egif", [
    '(broaderTransitive "Dog" "Animal")',     # derived through the closure → Graphist
    '(related "Wolf" "Dog")',                 # symmetric closure → Graphist
    '(broaderTransitive "Dog" "Cat")',        # no path, open world → independent
    '~[ (broaderTransitive "Dog" "Animal") ]',
])
def test_skos_contest_matches_evaluate(skos_oracle, egif):
    g = parse_egif(egif)
    assert play(g, skos_oracle).verdict is evaluate(g, skos_oracle).verdict


def test_skos_grapheus_must_concede_derived_fact(skos_oracle):
    # Proposing a fact M derives: the Grapheus has no defeating move → Graphist wins.
    result = play(parse_egif('(broaderTransitive "Dog" "Animal")'), skos_oracle)
    assert result.outcome is Outcome.GRAPHIST_WINS


# ---------------------------------------------------------------------------
# A slice of the tomos corpus against a couple of example models
# ---------------------------------------------------------------------------

def test_corpus_slice_matches_evaluate():
    from tomos_service import TomosService
    from egif_generator_dau import generate_egif

    svc = TomosService(ROOT / "tomos")
    oracle = M(world=BISCUIT + " " + SOCRATES)
    checked = 0
    for entry in svc.list_uods()[:12]:
        try:
            egi = svc.load_uod(entry["uod_id"], attest=False).current_egi
        except Exception:
            continue
        assert play(egi, oracle).verdict is evaluate(egi, oracle).verdict
        checked += 1
    assert checked >= 5


# ---------------------------------------------------------------------------
# The interactive surface — the human Graphist makes a real choice
# ---------------------------------------------------------------------------

def test_interactive_graphist_choice():
    # An existential the Graphist witnesses: two dogs, one path to a win.
    oracle = M(a='(dog "Biscuit") (dog "Rex") (good "Rex")')
    contest = GrapheusContest(parse_egif('(dog *x) (good x)'), oracle)
    contest.start()
    choices = contest.legal_choices()
    assert choices and choices[0].owner is Player.GRAPHIST
    assert choices[0].kind == "witness"
    # Pick the winning witness (Rex) by its option key.
    rex = next(o["key"] for o in choices[0].options if o["label"] == "Rex")
    result = contest.choose(rex)
    assert result.is_over
    assert result.outcome is Outcome.GRAPHIST_WINS
    assert result.bindings.get("x") == "Rex"


def test_interactive_rejects_illegal_and_machine_owned():
    contest = GrapheusContest(parse_egif('(dog "Biscuit")'), M(a=BISCUIT))
    contest.start()
    # A ground atom: no Graphist frontier (the Grapheus adjudicates) → over already.
    assert contest._play.is_over or contest._play.frontier is None
    with pytest.raises(ValueError):
        contest.choose("nonexistent")
