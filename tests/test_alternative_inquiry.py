"""Tests for ``src/alternative_inquiry.py`` — Item 4 Phase 2, Task 4: wiring
peel-UNKNOWN verdicts into interrogative ``AlternativeSet``s whose consequences
are *traced* (not assumed). See
``docs/superpowers/specs/2026-07-25-alternative-set-inquiry-principle.md`` and
``docs/superpowers/plans/2026-07-25-item-4-phase-2-tasks-4-6-revised.md`` §"Task 4".
"""

import json

import pytest

from alternative_inquiry import (
    BoundedRegister,
    KyteProfile,
    alternatives_from_unknowns,
    interrogative_from_unknown,
)
from alternative_set import AlternativeSet
from eg_navigation import same_graph
from egif_parser_dau import parse_egif
from egi_transformation_history import EGITransformationHistory
from query_docket import QueryDocket
from universe_of_discourse import UniverseOfDiscourse, UoDMetadata, UoDType, UoDCategory
from world_scroll import wrap_state


SWAN_EGIF = '(swan "Alba") ~[ (swan *x) ~[ (white x) ] ]'


@pytest.fixture
def swan_m():
    return parse_egif(SWAN_EGIF)


def _fresh_registers(s_cap=32, a_cap=32):
    return BoundedRegister(s_cap), BoundedRegister(a_cap)


# --------------------------------------------------------------------------- #
# 1. Detect                                                                    #
# --------------------------------------------------------------------------- #

def test_detect_creates_interrogative_alternative_set_unfiltered(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "white", ["Alba"],
        alt_id="a0", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert isinstance(alt, AlternativeSet)
    assert alt.kind == "interrogative"
    assert alt.source == "unknown_in_peel"
    assert alt.emerged_at_state == "s0"
    assert alt.status == "unresolved"
    assert len(alt.alternatives) == 2
    assert '(white "Alba")' in alt.alternatives
    assert '~[ (white "Alba") ]' in alt.alternatives


# --------------------------------------------------------------------------- #
# 2. Material distinction                                                     #
# --------------------------------------------------------------------------- #

def test_material_distinction_swan_bella(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert alt.warrant == 1.0
    assert "white" in alt.consequence_description
    assert "derivable:white" in alt.s_expansion
    assert "distinction:swan" in alt.s_expansion
    assert "condition-on:swan" in alt.a_expansion
    assert "derive-via:white" in alt.a_expansion
    assert "resolve:swan" in alt.a_expansion


# --------------------------------------------------------------------------- #
# 3. Bare distinction                                                         #
# --------------------------------------------------------------------------- #

def test_bare_distinction_no_law_touches_relation(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "green", ["Alba"],
        alt_id="a2", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert alt.warrant == 0.5
    assert not any(t.startswith("derive-via:") for t in alt.a_expansion)
    assert "resolve:green" in alt.a_expansion
    assert not any(t.startswith("distinction:") for t in alt.s_expansion)


# --------------------------------------------------------------------------- #
# 4. M never mutated                                                          #
# --------------------------------------------------------------------------- #

def test_m_never_mutated(swan_m):
    original = parse_egif(SWAN_EGIF)
    s_reg, a_reg = _fresh_registers()
    interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert same_graph(swan_m, original)


# --------------------------------------------------------------------------- #
# 5. Bounded decay                                                             #
# --------------------------------------------------------------------------- #

def test_bounded_register_displaces_least_recently_touched():
    reg = BoundedRegister(capacity=2)
    assert reg.admit("a") is None
    assert reg.admit("b") is None
    displaced = reg.admit("c")            # register full -> "a" (oldest) displaced
    assert displaced == "a"
    assert reg.terms == ["b", "c"]
    assert reg.admitted == 3
    assert reg.displaced == 1


def test_bounded_register_readmit_refreshes_no_displacement():
    reg = BoundedRegister(capacity=2)
    reg.admit("a")
    reg.admit("b")
    # touch "a" again — refreshes it, so "b" (not "a") is now the oldest
    refreshed = reg.admit("a")
    assert refreshed is None
    displaced = reg.admit("c")
    assert displaced == "b"
    assert reg.terms == ["a", "c"]
    assert reg.displaced == 1
    assert reg.admitted == 3          # "a" touch doesn't count as a new admission


def test_material_call_reports_s_and_a_decay_when_registers_are_tight(swan_m):
    # capacity 1: the second admission this call makes will displace the first
    s_reg = BoundedRegister(capacity=1)
    a_reg = BoundedRegister(capacity=3)
    alt = interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    # S refinement admits derivable:white then distinction:swan -> the first
    # is displaced by the second under capacity 1.
    assert "derivable:white" in alt.s_decayed
    assert "distinction:swan" in alt.s_expansion
    assert s_reg.terms == ["distinction:swan"]


# --------------------------------------------------------------------------- #
# 6. External input                                                           #
# --------------------------------------------------------------------------- #

def test_external_agrees_false_caps_warrant_and_sets_external_warrant(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
        external_input="a colleague says otherwise",
        external_input_source="colleague",
        external_agrees=False,
    )
    assert alt.external_warrant == 0.1
    assert alt.warrant <= 0.5
    assert alt.external_input == "a colleague says otherwise"
    assert alt.external_input_source == "colleague"


def test_external_agrees_true_does_not_change_internal_warrant(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
        external_agrees=True,
    )
    assert alt.external_warrant == 0.9
    assert alt.warrant == 1.0


def test_external_agrees_none_is_the_default():
    s_reg, a_reg = _fresh_registers()
    m = parse_egif(SWAN_EGIF)
    alt = interrogative_from_unknown(
        m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert alt.external_warrant == 0.0
    assert alt.external_input is None


# --------------------------------------------------------------------------- #
# 7. Batch                                                                     #
# --------------------------------------------------------------------------- #

def test_batch_dedups_and_shares_registers(swan_m):
    unknowns = [
        ("swan", ["Bella"]),
        ("green", ["Alba"]),
        ("swan", ["Bella"]),          # exact duplicate — skipped
    ]
    alts = alternatives_from_unknowns(unknowns, swan_m, state_id="s0")
    assert len(alts) == 2
    assert alts[0].id == "unk_0_swan"
    assert alts[1].id == "unk_1_green"


def test_batch_shared_registers_allow_cross_item_decay(swan_m):
    s_reg = BoundedRegister(capacity=1)
    a_reg = BoundedRegister(capacity=32)
    unknowns = [("swan", ["Bella"]), ("green", ["Alba"])]
    alts = alternatives_from_unknowns(
        unknowns, swan_m, state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    # The first item's S admissions can be displaced by the second item's,
    # since the registers are the SAME object across the whole batch.
    assert len(s_reg) <= 1
    assert s_reg.admitted >= 1


# --------------------------------------------------------------------------- #
# 8. End-to-end persistence                                                    #
# --------------------------------------------------------------------------- #

def test_uod_record_and_json_roundtrip_preserves_new_fields(swan_m):
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        swan_m, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
        external_input="noted", external_input_source="test", external_agrees=False,
    )

    now = __import__("datetime").datetime.now()
    metadata = UoDMetadata(
        uod_id="test-alt-inquiry",
        uod_type=UoDType.HISTORICAL,
        name="Alt Inquiry Test",
        description="Task 4 persistence test",
        category=UoDCategory.ACTIVE_INQUIRY,
        created=now,
        last_modified=now,
    )
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=swan_m,
        history=EGITransformationHistory(initial_egi=swan_m, description="init"),
    )
    uod.record_alternative_at_state("s0", alt)
    assert uod.alternatives_at_state("s0") == [alt]

    roundtripped = AlternativeSet.from_dict(json.loads(json.dumps(alt.to_dict())))
    assert roundtripped.s_decayed == alt.s_decayed
    assert roundtripped.s_expansion == alt.s_expansion
    assert roundtripped.a_expansion == alt.a_expansion
    assert roundtripped.a_decayed == alt.a_decayed
    assert roundtripped.external_warrant == alt.external_warrant
    assert roundtripped.external_input == alt.external_input
    assert roundtripped.external_input_source == alt.external_input_source
    assert roundtripped.consequence_description == alt.consequence_description
    assert roundtripped.warrant == alt.warrant
    assert same_graph(roundtripped.context, alt.context)


# --------------------------------------------------------------------------- #
# 9. Resident M                                                                #
# --------------------------------------------------------------------------- #

def test_resident_m_still_finds_material_distinction_through_m_view(swan_m):
    resident, _scroll = wrap_state(swan_m)
    s_reg, a_reg = _fresh_registers()
    alt = interrogative_from_unknown(
        resident, "swan", ["Bella"],
        alt_id="a1", state_id="s0",
        s_register=s_reg, a_register=a_reg,
    )
    assert alt.warrant == 1.0
    assert "derivable:white" in alt.s_expansion


# --------------------------------------------------------------------------- #
# 10. Docket co-feed                                                           #
# --------------------------------------------------------------------------- #

def test_docket_and_alternatives_coexist_without_interference(swan_m):
    unknowns = [("swan", ["Bella"]), ("green", ["Alba"])]

    docket = QueryDocket(labels={})
    docket.note_unknowns(unknowns)
    assert len(docket.open_entries) == 2

    alts = alternatives_from_unknowns(unknowns, swan_m, state_id="s0")
    assert len(alts) == 2
    # Both seams fed from the exact same iterable, independently.
    assert {e.shape for e in docket.open_entries} == {"swan", "green"}
    assert {a.id.rsplit("_", 1)[-1] for a in alts} == {"swan", "green"}
