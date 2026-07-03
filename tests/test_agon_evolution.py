"""Tests for the automated model-development loop (``agon_evolution``).

The loop automates the *playing* of the Endoporeutic Game: produce → test →
negotiate → inject → decay, over a closed membrane. The headline check is that
fed its own proposals it *reproduces the hand-played swan trajectory*
(``dialogue_swan_revision``). See docs/AUTOMATED_MODEL_DEVELOPMENT.md.
"""

import pytest

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from semantic_game import Verdict3

from agon_evolution import (
    peel, run,
    CorpusProposer, MutationProposer,
    DeliberationContext, Agonothetes,
    ObserverAgent, GeneralizerAgent, ChallengerAgent,
    UsageLedger, atom_key,
)

SWAN_M0 = ('(swan "Alba") (white "Alba") (swan "Bianca") (white "Bianca") '
           '(swan "Ciel")')
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'
SWAN_POOL = [
    '(white "Ciel")',                       # observe — new_fact
    SWAN_LAW,                               # leap to the law — generalization
    '(swan "Dover")',                       # newcomer the law covers — new_fact
    '(swan "Nox") ~[ (white "Nox") ]',     # a non-white swan — challenge_to_M
]


def _ctx(model_egif, proposal, known_laws=()):
    model = parse_egif(model_egif)
    return DeliberationContext(model, proposal, peel(model, proposal), list(known_laws))


# --------------------------------------------------------------------------- #
# ② Test                                                                       #
# --------------------------------------------------------------------------- #

def test_peel_reads_M_as_truth_teller():
    assert peel(parse_egif(SWAN_M0), '(swan "Alba")').verdict is Verdict3.TRUE
    assert peel(parse_egif(SWAN_M0), '(swan "Nobody")').verdict is Verdict3.FALSE


# --------------------------------------------------------------------------- #
# ③ The panel — each agent in isolation                                        #
# --------------------------------------------------------------------------- #

def test_observer_admits_novel_fact_abstains_on_redundant():
    obs = ObserverAgent()
    assert obs.vote(_ctx(SWAN_M0, '(white "Ciel")')).disposition == "new_fact"
    # already a sheet fact → redundant → abstain
    assert obs.vote(_ctx(SWAN_M0, '(swan "Alba")')) is None


def test_generalizer_admits_holding_law_refuses_false_and_vacuous():
    gen = GeneralizerAgent()
    # holds once Ciel is white
    m = '(swan "Alba") (white "Alba") (swan "Ciel") (white "Ciel")'
    assert gen.vote(_ctx(m, SWAN_LAW)).disposition == "generalization"
    # false in M0 (Ciel not white) → abstain
    assert gen.vote(_ctx(SWAN_M0, SWAN_LAW)) is None
    # vacuous (no swans at all) → abstain
    assert gen.vote(_ctx('(white "X")', SWAN_LAW)) is None


def test_challenger_fires_only_on_a_counterexample_to_a_standing_law():
    ch = ChallengerAgent()
    m = '(swan "Alba") (white "Alba")'
    # a non-white swan, with the law standing → challenge
    v = ch.vote(_ctx(m, '(swan "Nox") ~[ (white "Nox") ]', known_laws=[SWAN_LAW]))
    assert v.disposition == "challenge_to_M"
    assert v.kwargs["subgraph_egif"] == SWAN_LAW
    # no standing law → nothing to challenge
    assert ch.vote(_ctx(m, '(swan "Nox") ~[ (white "Nox") ]')) is None
    # an antecedent-only fact never refutes a Horn law (self-fulfilling)
    assert ch.vote(_ctx(m, '(swan "Nox")', known_laws=[SWAN_LAW])) is None


def test_panel_resolves_by_priority_challenger_over_observer():
    panel = Agonothetes()
    ctx = _ctx('(swan "Alba") (white "Alba")',
               '(swan "Nox") ~[ (white "Nox") ]', known_laws=[SWAN_LAW])
    winner = panel.resolve(panel.deliberate(ctx))
    assert winner.disposition == "challenge_to_M"


# --------------------------------------------------------------------------- #
# ⑤ Decay — the only bound on an unbounded plane                               #
# --------------------------------------------------------------------------- #

def test_usage_ledger_marks_idle_keys_stale():
    led = UsageLedger(ttl=2)
    led.seed({atom_key("swan", ["Alba"]), atom_key("rumor", ["X"])}, round_idx=0)
    led.touch({atom_key("swan", ["Alba"])}, round_idx=1)
    assert atom_key("rumor", ["X"]) in led.stale(2)
    assert atom_key("swan", ["Alba"]) not in led.stale(2)


def test_decay_erases_an_atom_that_fell_from_use():
    pool = ['(swan "Bianca")', '(white "Bianca")', '(swan "Ciel")']
    res = run('(swan "Alba") (white "Alba") (rumor "X")', CorpusProposer(pool),
              rounds=3, ttl=2, uod_id="decay", name="decay")
    assert any(atom_key("rumor", ["X"]) in o.decayed for o in res.outcomes)
    assert "rumor" not in res.uod.current_egi.rel.values()


def test_decay_is_atom_level_the_habit_is_the_fact_not_the_name():
    """The rulebook decision (affirmed 2026-07-03): one atom of a name decays while
    a *re-delivered* atom of the SAME name stays — the F1″ warm-name pinning
    dissolved. Under the old name-level ledger the re-delivery of (spot Alba)
    would have kept (spot Ciel) warm forever."""
    pool = ['(spot "Alba")'] * 4                       # Alba re-delivered every round
    res = run('(spot "Alba") (spot "Ciel")', CorpusProposer(pool),
              rounds=4, ttl=2, uod_id="atomdecay", name="atomdecay")
    decayed = [k for o in res.outcomes for k in o.decayed]
    assert atom_key("spot", ["Ciel"]) in decayed        # the idle atom fell
    assert atom_key("spot", ["Alba"]) not in decayed    # the re-delivered habit held
    final = res.uod.current_egi
    standing = {tuple(final.get_vertex(v).label for v in final.nu[e.id])
                for e in final.E if final.rel.get(e.id) == "spot"}
    assert standing == {("Alba",)}                      # the name survives on its warm atom


# --------------------------------------------------------------------------- #
# The headline — reproduce the hand-played swan trajectory                     #
# --------------------------------------------------------------------------- #

def test_loop_reproduces_swan_trajectory():
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4,
              uod_id="auto_swan", name="auto swan", standing_proposal=SWAN_LAW)
    assert [o.disposition for o in res.outcomes] == [
        "new_fact", "generalization", "new_fact", "challenge_to_M"]
    assert [o.mode for o in res.outcomes] == [
        "induction", "induction", "induction", "abduction"]
    # the audited proposal flips TRUE→…→FALSE exactly when the law is relinquished
    assert [o.standing_verdict for o in res.outcomes] == [
        "true", "true", "true", "false"]


def test_swan_run_is_reproducible():
    a = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4, uod_id="s", name="s")
    b = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4, uod_id="s", name="s")
    assert [o.disposition for o in a.outcomes] == [o.disposition for o in b.outcomes]
    assert same_graph(a.uod.current_egi, b.uod.current_egi)


def test_final_model_reflects_the_revisions():
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4, uod_id="s", name="s")
    final = res.uod.current_egi
    # the over-general law was relinquished; the anomaly Nox survives
    assert peel(final, SWAN_LAW).verdict is Verdict3.FALSE
    assert peel(final, '(swan "Nox")').verdict is Verdict3.TRUE


def test_discoveries_flag_anomaly_and_superseded_law():
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4, uod_id="s", name="s")
    kinds = {d.kind for d in res.discoveries}
    assert "productive_anomaly" in kinds
    assert "superseded_law" in kinds   # the law was admitted then relinquished


# --------------------------------------------------------------------------- #
# Non-revising rounds, and the mutation membrane                               #
# --------------------------------------------------------------------------- #

def test_redundant_proposal_is_a_non_revising_round():
    res = run(SWAN_M0, CorpusProposer(['(swan "Alba")']), rounds=1,
              uod_id="r", name="r")
    assert res.outcomes[0].disposition is None
    assert not res.outcomes[0].changed
    # M is untouched
    assert same_graph(res.uod.current_egi, parse_egif(SWAN_M0))


def test_mutation_membrane_finds_supported_subsumptions_only():
    M = ('(dog "Rex") (mammal "Rex") (dog "Fido") (mammal "Fido") '
         '(sparrow "Pip") (bird "Pip")')
    res = run(M, MutationProposer(M), rounds=30, uod_id="zoo", name="zoo")
    admitted = {o.proposal_egif for o in res.outcomes if o.disposition}
    assert '~[ (dog *x) ~[ (mammal x) ] ]' in admitted        # genuinely holds
    assert '~[ (bird *x) ~[ (dog x) ] ]' not in admitted       # Pip refutes it


# --------------------------------------------------------------------------- #
# §3.3 — the trajectory persists and attests at the corpus boundary            #
# --------------------------------------------------------------------------- #

def test_trajectory_persists_and_attests(tmp_path):
    from tomos_service import TomosService
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4,
              uod_id="auto_swan", name="auto swan")
    service = TomosService(tmp_path)
    # save_uod_with_chain runs §3.3 on the tail state before any disk write
    service.save_uod_with_chain(res.uod, res.chain)
    reloaded = service.load_chain("auto_swan")
    assert reloaded is not None
    assert len(reloaded.steps) == len(res.chain.steps)
