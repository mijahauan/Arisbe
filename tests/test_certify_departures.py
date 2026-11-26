"""What observe mode finds on production's own paths, held as it stands.

The Phase 2 gate — the kernel rejects exactly what the calculus ledger
describes — is a statement about the moves the calculus suite tries. Production
reaches the engine by other roads too, and changes graphs in places no rule is
named. Each departure found there is reproduced here and pinned, by name, so
that it is neither lost nor fixed without someone noticing: a test below that
starts failing because its departure is gone is the signal to retire it.

Found by running the whole suite with ``ARISBE_CERTIFY_LOG`` set, which records
for every certificate the kernel did not accept the caller that asked for the
move. Outside the calculus suite that run held 11,315 such certificates: 11,101
from ``_join_admitted_individuals``, 204 from ``retract_from_m``, and 10 from
test code, the MCP verifier's tests and one dry run.

Two of the four found then were retired on 2026-11-26 (Phase 3, item 1), and
their tests below now hold the repaired behaviour instead: admission and
discharge join a shared individual's lines by Dau's constant rules and the
checked merge, every step certified and recorded.

``KNOWN_DEPARTURES`` is the register. It is the counterpart, for production
paths, of ``tests/calculus_ledger.json`` for the suite's moves.
"""
import json
from collections import Counter
from pathlib import Path

import calculus_certify
import dau_kernel
import derived_rules
import egi_io
import world_scroll
from calculus_certify import Act, certify
from dau_kernel import ACCEPTED, REJECTED
from egif_parser_dau import parse_egif

ROOT = Path(__file__).resolve().parent.parent

KNOWN_DEPARTURES = {
    "ui-scribes-its-identity-edge-by-no-rule":
        "derived_rules.universal_instantiation iterates, then adds the identity edge that "
        "joins the copy to the line with the data model's own with_edge, then merges. The "
        "iteration and the merge are each certified and accepted; the edge between them is "
        "named by no rule and checked by nothing — not even that its area is negative "
        "(specification 3.3a finding 5; Phase 3 item 3). instantiate_to_lines does the same.",
    "retract-leans-on-era-erasing-the-vertex-it-isolates":
        "world_scroll.retract_from_m erases an atom by selecting its edge and relies on ERA "
        "also taking the vertex the erasure isolates. That is the calculus ledger's own "
        "era-also-erases-the-vertex-it-isolates, met here on a production caller: when "
        "Phase 3 item 2 makes ERA remove the edge only, retraction must name the vertex's "
        "erasure as its own step or it will leave the individual standing.",
}


class _Recorder:
    """Every certificate issued while it is installed, with the graph it was
    issued on and the graph it vouches for: (certificate, g, h)."""

    def __init__(self, monkeypatch):
        self.seen = []
        original = calculus_certify._observe

        def observe(way, rule, g, h, move, may_raise=True):
            cert = original(way, rule, g, h, move, may_raise)
            self.seen.append((cert, g, h))
            return cert

        monkeypatch.setattr(calculus_certify, "_observe", observe)


def _in_custody(seen, first, last) -> bool:
    """R9: each certificate is issued on the graph the one before vouched
    for, from ``first`` to ``last`` — nothing changed a graph in between."""
    graphs = [first] + [h for _c, _g, h in seen]
    return all(g is before for (_c, g, _h), before in zip(seen, graphs)) and graphs[-1] is last


def test_admitting_a_fact_joins_the_named_vertex_by_rules_the_kernel_accepts(monkeypatch):
    """Was KNOWN_DEPARTURES["admit-joins-a-named-vertex"], retired 2026-11-26:
    the join was one unchecked merge of a named vertex, which the kernel
    rejected, inside a step recorded as INS alone. It is now Dau's own road —
    a vertex of that name at W, then each mention linked to it and merged
    into it — and the record says so."""
    resident, scroll = world_scroll.wrap_m(parse_egif('(bird "Rex")'))
    recorder = _Recorder(monkeypatch)
    admitted, derivation = world_scroll.enlarge_m_recorded(resident, '(white "Rex")')
    certs = [(c.way, c.steps[0].rule, c.status) for c, _g, _h in recorder.seen]
    assert certs == [("protocol", "INS", ACCEPTED),
                     ("engine", "CONSTANT_EXISTENCE", ACCEPTED),
                     ("engine", "CONSTANT_IDENTITY", ACCEPTED),
                     ("merge-checked", "MERGE_VERTICES", ACCEPTED),
                     ("engine", "CONSTANT_IDENTITY", ACCEPTED),
                     ("merge-checked", "MERGE_VERTICES", ACCEPTED)]
    assert derivation == [rule for _way, rule, _status in certs]
    assert _in_custody(recorder.seen, resident, admitted)
    assert sum(1 for v in admitted.V if v.label == "Rex") == 1
    assert sum(1 for v in recorder.seen[0][2].V if v.label == "Rex") == 2


def test_discharge_returns_the_graph_its_last_certificate_vouched_for(monkeypatch):
    """Was KNOWN_DEPARTURES["discharge-normalises-constants-unrecorded"],
    retired 2026-11-26: the discharge ran a normaliser after its last rule, so
    the graph it returned was not the graph any certificate covered. The join
    is now two more certified steps, and the chain of custody holds end to end."""
    resident, _scroll = world_scroll.wrap_m(parse_egif('(bird "Rex")'))
    entertained, _ = world_scroll.entertain_episode(resident, '(flies "Rex")')
    recorder = _Recorder(monkeypatch)
    discharged, derivation = world_scroll.discharge_episode(entertained, '(flies "Rex")')
    assert derivation == ["IT-", "IT-", "DC-", "CONSTANT_IDENTITY", "MERGE_VERTICES"]
    assert [(c.steps[0].rule, c.status) for c, _g, _h in recorder.seen] == [
        (rule, ACCEPTED) for rule in derivation]
    assert _in_custody(recorder.seen, entertained, discharged)
    assert sum(1 for v in discharged.V if v.label == "Rex") == 1


def test_universal_instantiation_adds_an_edge_between_two_certificates(monkeypatch):
    """KNOWN_DEPARTURES["ui-scribes-its-identity-edge-by-no-rule"]. Barbara's
    step: iterate every M is P into every S is M and join the lines.
    Both certificates are accepted, and the second is issued on a graph the
    first did not produce."""
    g = parse_egif("~[ (M *x) ~[ (P x) ] ] ~[ (S *y) ~[ (M y) ] ]")
    cuts = {c.id for c in g.Cut}

    def sheet_cut(relation):
        return next(c for c in g.area[g.sheet]
                    if any(g.rel.get(e) == relation for e in g.area[c]))

    every_m_is_p, every_s_is_m = sheet_cut("M"), sheet_cut("S")
    inner = next(x for x in g.area[every_s_is_m] if x in cuts)
    y = g.nu[next(e for e in g.area[inner] if g.rel.get(e) == "M")][0]
    recorder = _Recorder(monkeypatch)
    derived_rules.universal_instantiation(
        g, universal_cut=every_m_is_p, target_area=inner, join_vertex=y)
    assert [(c.steps[0].rule, c.status) for c, _g, _h in recorder.seen] == [
        ("IT+", ACCEPTED), ("MERGE_VERTICES", ACCEPTED)]
    iterated, merged_from = recorder.seen[0][2], recorder.seen[1][1]
    assert not dau_kernel.same_graph(iterated, merged_from)
    assert len(merged_from.E) == len(iterated.E) + 1          # the identity edge, by no rule


def test_retracting_an_atom_leans_on_era_taking_the_isolated_vertex(monkeypatch):
    """KNOWN_DEPARTURES["retract-leans-on-era-erasing-the-vertex-it-isolates"]."""
    resident, _scroll = world_scroll.wrap_m(parse_egif('(bird "Rex") (white "Tweety")'))
    recorder = _Recorder(monkeypatch)
    retracted, derivation = world_scroll.retract_from_m(
        resident, relation="white", labels=["Tweety"])
    assert derivation == ["ERA"]
    (cert, before, after), = recorder.seen
    assert (cert.steps[0].rule, cert.status) == ("ERA", REJECTED)
    assert "differs from the licensed change" in cert.why
    assert len(cert.steps[0].selection) == 1                   # the edge alone was named
    assert (len(before.V), len(after.V)) == (2, 1)             # and Tweety's vertex went with it


def test_the_register_names_exactly_the_departures_reproduced_here():
    reproduced = {line.split('KNOWN_DEPARTURES["')[1].split('"]')[0]
                  for line in Path(__file__).read_text().splitlines()
                  if line.strip().startswith('"""KNOWN_DEPARTURES["')}
    assert reproduced == set(KNOWN_DEPARTURES)


# -- the corpus ---------------------------------------------------------------

SIX = {"ERA", "INS", "IT+", "IT-", "DC+", "DC-"}


def _primitive_steps():
    for chain in sorted((ROOT / "tomos").rglob("chain.jsonl")):
        states = chain.parent / "states"
        for line in chain.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            params = record.get("parameters", {})
            if record.get("type") == "step" and params.get("rule") in SIX \
                    and not params.get("derived"):
                yield chain.parent.parent.name, record, states


def test_every_primitive_step_the_corpus_records_replays_to_an_accepted_certificate():
    """66 steps across the corpus's chains — DC+ 16, DC- 8, ERA 17, INS 12,
    IT+ 5, IT- 8. Each is replayed from its recorded source state through the
    door; each reproduces its recorded result, and the kernel accepts each as
    the Dau move it is recorded as. So none of the corpus's primitive steps is
    one of the fused moves the ledger describes, and none needs a legacy
    expansion to be certified as it stands."""
    by_rule, problems = Counter(), []
    for uod, record, states in _primitive_steps():
        params = record["parameters"]
        g = egi_io.load_egi_json(states / f"{record['from_state_id']}.egi.json")
        recorded = egi_io.load_egi_json(states / f"{record['to_state_id']}.egi.json")
        h, cert = certify(g, Act("protocol", params["rule"], tuple(params.get("selection") or ()),
                                 params.get("target_area"), params.get("egif_content")))
        by_rule[params["rule"]] += 1
        if not cert.accepted:
            problems.append((uod, record["step_id"], cert.status, cert.why))
        elif not dau_kernel.same_graph(h, recorded):
            problems.append((uod, record["step_id"], "replay differs from the recorded state", ""))
    assert problems == []
    assert by_rule == {"DC+": 16, "DC-": 8, "ERA": 17, "INS": 12, "IT+": 5, "IT-": 8}
