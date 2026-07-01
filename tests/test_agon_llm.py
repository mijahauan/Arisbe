"""Tests for the LLM Graphist (``agon_llm``) — Stage 1 of the automated Endoporeutic Game.

CI-safe: every test drives a **scripted fake client** (no SDK, no network, no key). The one
live test is skipped unless the ``anthropic`` SDK and an API key are both present. The
headline check mirrors ``test_agon_evolution``: fed the swan doubts, the LLM Graphist drives
the mechanical panel to reproduce the hand-played ``dialogue_swan_revision`` trajectory —
even when it emits Capitalized FOL predicates (normalization reduces them to M's vocabulary).
"""

import os

import pytest

from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from semantic_game import Verdict3

from agon_evolution import run, peel
from agon_llm import (
    ANTHROPIC_AVAILABLE, LLMGraphist, attention_brief, _normalize_fol,
)


# --------------------------------------------------------------------------- #
# A scripted fake Anthropic client                                            #
# --------------------------------------------------------------------------- #

class _Block:
    def __init__(self, inp):
        self.type = "tool_use"
        self.name = "propose_graph"
        self.input = inp


class _Resp:
    def __init__(self, inp):
        self.content = [_Block(inp)]


class FakeClient:
    """Returns scripted ``propose_graph`` tool inputs, one per ``messages.create`` call
    (the last one repeats if the script is exhausted)."""

    def __init__(self, script):
        self._script = list(script)
        self._i = 0
        self.calls = []

        class _Messages:
            def create(_self, **kw):
                self.calls.append(kw)
                inp = self._script[min(self._i, len(self._script) - 1)]
                self._i += 1
                return _Resp(inp)

        self.messages = _Messages()


def _doubt(fol, doubt_type="gap", **kw):
    return {"fol": fol, "predicates": kw.get("predicates", {}),
            "constants": kw.get("constants", []), "doubt_type": doubt_type,
            "rationale": kw.get("rationale", "a doubt.")}


SWAN_M0 = '(swan "Alba") (white "Alba") (swan "Ciel")'
SWAN_LAW = '~[ (swan *x) ~[ (white x) ] ]'
# The LLM emits *Capitalized* FOL predicates on purpose — normalization must reduce them.
SWAN_SCRIPT = [
    _doubt("White(Ciel)", "gap"),
    _doubt("∀x (Swan(x) → White(x))", "over_generalization"),
    _doubt("Swan(Nox) ∧ ¬White(Nox)", "over_generalization"),
]


# --------------------------------------------------------------------------- #
# Vocabulary normalization                                                     #
# --------------------------------------------------------------------------- #

def test_normalize_fol_maps_to_model_vocabulary():
    # Capitalized predicate → M's lowercase spelling; constant untouched.
    assert _normalize_fol("White(Ciel)", {"white", "swan"}) == "white(Ciel)"
    # a genuinely new predicate → lowercase (codebase convention), no M match needed
    assert _normalize_fol("Dragon(Puff)", {"white"}) == "dragon(Puff)"
    # quantified form
    assert (_normalize_fol("∀x (Swan(x) → White(x))", {"swan", "white"})
            == "∀x (swan(x) → white(x))")


# --------------------------------------------------------------------------- #
# Attention brief                                                              #
# --------------------------------------------------------------------------- #

def test_attention_brief_invites_bootstrapping_on_blank_sheet():
    brief = attention_brief(parse_egif(""))
    assert brief.vocabulary == [] and "EMPTY" in brief.text


def test_attention_brief_names_the_thin_spots():
    # 'white' has one instance; 'Ciel' appears once; a law swan→flies is ungrounded (no flies fact)
    m = parse_egif('(swan "Alba") (white "Alba") (swan "Ciel") ~[ (flies *x) ~[ (swan x) ] ]')
    brief = attention_brief(m)
    assert "white" in brief.thin_relations
    assert "Ciel" in brief.lonely_individuals
    assert ("flies", "swan") in brief.ungrounded_laws


# --------------------------------------------------------------------------- #
# propose(): reduce-to-artifact, retry, never-raise                            #
# --------------------------------------------------------------------------- #

def test_propose_returns_emitted_graph_and_records_episode():
    g = LLMGraphist(client=FakeClient([_doubt("White(Ciel)")]))
    egif = g.propose(parse_egif(SWAN_M0), 1)
    assert same_graph(parse_egif(egif), parse_egif('(white "Ciel")'))
    assert len(g.episodes) == 1 and g.episodes[0].ok
    assert g.episodes[0].doubt_type == "gap"


def test_propose_retries_on_unparseable_then_recovers():
    g = LLMGraphist(client=FakeClient([_doubt("this is not FOL @@"), _doubt("white(Ciel)")]))
    egif = g.propose(parse_egif(SWAN_M0), 1)
    assert egif is not None and same_graph(parse_egif(egif), parse_egif('(white "Ciel")'))


def test_propose_returns_none_when_all_attempts_fail_never_raises():
    g = LLMGraphist(client=FakeClient([_doubt("@@@")]), max_retries=1)
    assert g.propose(parse_egif(SWAN_M0), 1) is None          # ends the run cleanly
    assert not g.episodes[-1].ok


def test_propose_returns_none_when_client_unreachable():
    class Boom:
        class messages:
            @staticmethod
            def create(**kw):
                raise RuntimeError("no key")
    g = LLMGraphist(client=Boom())
    assert g.propose(parse_egif(SWAN_M0), 1) is None
    assert "LLM call failed" in (g.episodes[-1].error or "")


def test_propose_avoids_repeating_a_proposal():
    # same doubt twice, then a fresh one — the repeat is rejected, the third is taken
    g = LLMGraphist(client=FakeClient([
        _doubt("white(Ciel)"), _doubt("white(Ciel)"), _doubt("white(Alba)")]))
    g._seen.add('(white "Ciel")')                             # pretend already proposed
    egif = g.propose(parse_egif(SWAN_M0), 2)
    assert same_graph(parse_egif(egif), parse_egif('(white "Alba")'))


# --------------------------------------------------------------------------- #
# Integration — the Graphist drives the mechanical loop                        #
# --------------------------------------------------------------------------- #

def test_llm_graphist_reproduces_swan_trajectory():
    g = LLMGraphist(client=FakeClient(SWAN_SCRIPT))
    res = run(SWAN_M0, g, rounds=3, uod_id="llm_swan", name="llm swan",
              standing_proposal=SWAN_LAW)
    assert [o.disposition for o in res.outcomes] == [
        "new_fact", "generalization", "challenge_to_M"]
    assert [o.standing_verdict for o in res.outcomes] == ["true", "true", "false"]
    kinds = {d.kind for d in res.discoveries}
    assert "productive_anomaly" in kinds and "superseded_law" in kinds


def test_llm_graphist_bootstraps_from_blank_sheet():
    g = LLMGraphist(client=FakeClient([
        _doubt("cat(Tom)"), _doubt("mouse(Jerry)"), _doubt("chases(Tom, Jerry)")]))
    res = run("", g, rounds=3, uod_id="llm_scratch", name="from scratch")
    # from nothing, the mechanical Observer admits the posited facts
    assert any(o.disposition == "new_fact" for o in res.outcomes)
    assert peel(res.uod.current_egi, '(cat "Tom")').verdict is Verdict3.TRUE


def test_trajectory_persists_and_attests(tmp_path):
    from tomos_service import TomosService
    g = LLMGraphist(client=FakeClient(SWAN_SCRIPT))
    res = run(SWAN_M0, g, rounds=3, uod_id="llm_swan", name="llm swan")
    service = TomosService(tmp_path)
    service.save_uod_with_chain(res.uod, res.chain)           # §3.3 fires before any write
    reloaded = service.load_chain("llm_swan")
    assert reloaded is not None and len(reloaded.steps) == len(res.chain.steps)


# --------------------------------------------------------------------------- #
# Live smoke — only with the SDK + a key                                       #
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(
    not (ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY")),
    reason="needs the 'nl' extra + ANTHROPIC_API_KEY")
def test_live_graphist_proposes_a_real_graph():
    g = LLMGraphist()
    egif = g.propose(parse_egif(SWAN_M0), 1)
    assert egif is not None
    parse_egif(egif)                                          # a real, parseable proposal
