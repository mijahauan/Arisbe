"""Tests for the automated model-development loop (``agon_evolution``).

The loop automates the *playing* of the Endoporeutic Game: produce → test →
negotiate → inject → decay, over a closed membrane. The headline check is that
fed its own proposals it *reproduces the hand-played swan trajectory*
(``dialogue_swan_revision``). See docs/AUTOMATED_MODEL_DEVELOPMENT.md.
"""

import pytest

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from eg_navigation import area_of, same_graph
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
    # M is untouched (its content read through m_view — the loop plays over
    # M resident in the standing world-scroll since sweep #2)
    from world_scroll import m_view
    assert same_graph(m_view(res.uod.current_egi), parse_egif(SWAN_M0))


def test_loop_chain_is_rule_licensed_from_the_first_move():
    """Sweep #2 / §8.1: the loop's chain opens with genuine DC+ · INS residence
    steps and every M-revising step carries act + executed derivation — the
    same standard the polarity gate holds the hand-built corpus to."""
    from world_scroll import find_world_scroll
    res = run(SWAN_M0, CorpusProposer(SWAN_POOL), rounds=4,
              uod_id="s", name="s")
    steps = res.chain.steps
    assert [s.rule_name for s in steps[:2]] == ["DC+", "INS"]
    assert find_world_scroll(res.uod.current_egi) is not None
    for s in steps:
        if s.rule_name.startswith("REVISE_M") or s.rule_name == "DECAY":
            assert s.parameters.get("act") in {
                "m_enlargement", "m_retraction", "m_revision"}
            derivation = s.parameters.get("derivation")
            assert derivation and set(derivation) <= {"ERA", "INS"}
    # every state after the residence steps carries the standing scroll
    for sid, egi in res.chain.states.items():
        if sid in ("s0", "s1"):
            continue
        assert find_world_scroll(egi) is not None


def test_decay_records_the_faded_flavor():
    """§9.7/D6: disuse-decay is the same licensed ERA as refutation-driven
    retraction, distinguished by the recorded flavor."""
    pool = ['(swan "Bianca")', '(white "Bianca")', '(swan "Ciel")']
    res = run('(swan "Alba") (white "Alba") (rumor "X")', CorpusProposer(pool),
              rounds=3, ttl=2, uod_id="decay", name="decay")
    decay_steps = [s for s in res.chain.steps if s.rule_name == "DECAY"]
    assert decay_steps
    for s in decay_steps:
        assert s.parameters["flavor"] == "pruned:disuse"
        assert s.parameters["derivation"] == ["ERA"]


def test_decay_never_reaches_denial_cells(tmp_path):
    """Docket ⑥ pin: licensed disuse-decay is **cell-scoped**. An atom standing
    in a cell is a habit and fades; an identical atom sitting inside a *denial*
    cell (``~[ (nests "Ara" "Oak") ]``) is not a standing habit at all, and no
    decay pass may touch it. The deleted ``_structural_retract_atom`` fallback
    matched by relation + labels over the whole of ``g.E``, so it erased both."""
    from world_scroll import wrap_m, enlarge_m
    from agon_evolution import sheet_atom_keys

    seed, _ = wrap_m(parse_egif('(nests "Ara" "Oak")'))
    seed = enlarge_m(seed, '~[ (nests "Ara" "Oak") ]')

    res = run(generate_egif(seed), CorpusProposer(['(rumor "Q")']), rounds=1,
              ttl=1, uod_id="denial", name="denial")

    final = res.uod.current_egi
    # the standing habit faded ...
    assert atom_key("nests", ["Ara", "Oak"]) not in sheet_atom_keys(final)
    # ... while the denied atom, never a habit, still stands inside its cut
    assert sum(1 for e in final.E if final.rel.get(e.id) == "nests") == 1


def test_decay_skip_is_counted_never_structural():
    """Docket ④/⑥: what the licensed rule refuses is **skipped and counted**,
    never erased by unlicensed structural surgery.

    The refusal is reachable only on a legacy EGIF carry: a text round-trip
    shares an identical constant across sibling cells into ONE vertex — here
    "Rex", argument of both ``(bird "Rex")`` (its own cell) and
    ``(white "Rex")`` (a sibling cell). Decaying ``bird`` first leaves that
    vertex orphaned in a cell it has no edge left in; the licensed per-cell ERA
    then rightly refuses to decay ``white``, because erasing it would reach
    into a different area."""
    from world_scroll import wrap_m, enlarge_m, find_world_scroll
    from agon_evolution import sheet_atom_keys

    seed, _ = wrap_m(parse_egif('(bird "Rex")'))
    seed = enlarge_m(seed, '(white "Rex")')
    seed_egif = generate_egif(seed)
    round_tripped = parse_egif(seed_egif)

    # Confirm the shared-constant condition the round-trip induces: the two
    # atoms' argument vertex is literally the same vertex, but the atoms sit
    # in two different (sibling) cells.
    scroll = find_world_scroll(round_tripped)
    assert len(scroll.cell_ids) == 2
    bird_edge = next(e for e in round_tripped.E
                      if round_tripped.rel.get(e.id) == "bird")
    white_edge = next(e for e in round_tripped.E
                       if round_tripped.rel.get(e.id) == "white")
    assert round_tripped.nu[bird_edge.id] == round_tripped.nu[white_edge.id]
    assert area_of(round_tripped, bird_edge.id) != area_of(round_tripped, white_edge.id)

    # ttl=1 with a single unrelated proposal makes both seeded atoms stale in
    # round 1 — sorted decay order retracts "bird" before "white" (lexical),
    # reproducing the exact failing sequence.
    res = run(seed_egif, CorpusProposer(['(rumor "Q")']), rounds=1, ttl=1,
              uod_id="skip", name="skip")

    decayed = {k for o in res.outcomes for k in o.decayed}
    assert atom_key("bird", ["Rex"]) in decayed
    assert atom_key("white", ["Rex"]) not in decayed          # refused, so not erased

    # the refusal is recorded, never silent
    skipped = {k for o in res.outcomes for k, _reason in o.decay_skipped}
    assert skipped == {atom_key("white", ["Rex"])}

    # the atom STANDS — no unlicensed surgery took it
    assert atom_key("white", ["Rex"]) in sheet_atom_keys(res.uod.current_egi)

    # and every recorded decay step is a real licensed ERA (no empty derivation)
    decay_steps = [s for s in res.chain.steps if s.rule_name == "DECAY"]
    assert [s.parameters.get("derivation") for s in decay_steps] == [["ERA"]]
    assert all(s.parameters.get("act") == "m_retraction" for s in decay_steps)


def test_the_unlicensed_structural_fallback_is_gone():
    """Docket ⑥: the F2¹³ accommodation is deleted, not merely unused — nothing
    in the loop may erase M's ink without a rule licensing the move."""
    import agon_evolution
    assert not hasattr(agon_evolution, "_structural_retract_atom")


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
