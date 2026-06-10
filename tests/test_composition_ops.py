"""Contract tests for the regime-1 composition ops (the palette's server half).

Spec: docs/COMPOSITION_WORKFLOW_SPEC.md §2–§4, §6 step 1, §7.
Every op is a pure egi → ComposeResult rewrite; well-formedness is enforced
(§3) while soundness is suspended (regime 1).  The replay contract —
``recorded_parameters`` reproduce the op byte-stably — is what lets a vaulted
chain of compose steps verify end-to-end.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import composition_ops as co
from composition_ops import ComposeResult, apply_compose, verify_chain_replay
from eg_navigation import same_graph
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif


def empty():
    return parse_egif("")


def roundtrips(egi):
    """The draft is a real EGI: its EGIF parses back to the same graph."""
    return same_graph(parse_egif(generate_egif(egi)), egi)


# --------------------------------------------------------------------------- #
# Placing                                                                      #
# --------------------------------------------------------------------------- #


class TestPlacing:
    def test_add_cut_on_sheet(self):
        r = co.add_cut(empty())
        assert len(r.egi.Cut) == 1
        assert r.created["cut"] in {c.id for c in r.egi.Cut}
        assert roundtrips(r.egi)

    def test_add_cut_nested(self):
        r1 = co.add_cut(empty())
        r2 = co.add_cut(r1.egi, r1.created["cut"])
        inner = r2.created["cut"]
        assert inner in r2.egi.area[r1.created["cut"]]
        assert roundtrips(r2.egi)

    def test_add_cut_unknown_area_refused(self):
        with pytest.raises(ValueError, match="does not exist"):
            co.add_cut(empty(), "nowhere")

    def test_add_line(self):
        r = co.add_line(empty())
        v = r.egi.get_vertex(r.created["vertex"])
        assert v.is_generic and v.label is None
        assert roundtrips(r.egi)

    def test_add_constant(self):
        r = co.add_constant(empty(), "Socrates")
        v = r.egi.get_vertex(r.created["vertex"])
        assert not v.is_generic and v.label == "Socrates"
        assert roundtrips(r.egi)

    def test_add_constant_empty_label_refused(self):
        with pytest.raises(ValueError, match="non-empty label"):
            co.add_constant(empty(), "   ")

    def test_add_relation_mints_placeholder_lines(self):
        r = co.add_relation(empty(), "loves", arity=2)
        egi = r.egi
        assert len(egi.E) == 1 and len(egi.V) == 2
        assert egi.nu[r.created["edge"]] == tuple(r.created["placeholders"])
        assert roundtrips(egi)

    def test_add_relation_over_chosen_line(self):
        r1 = co.add_line(empty())
        r2 = co.add_relation(r1.egi, "Human", hooks=[r1.created["vertex"]])
        assert r2.egi.nu[r2.created["edge"]] == (r1.created["vertex"],)
        assert r2.created["placeholders"] == []

    def test_add_relation_reaches_enclosing_line(self):
        # Line on the sheet, relation inside a cut — the Beta pattern.
        r1 = co.add_line(empty())
        r2 = co.add_cut(r1.egi)
        r3 = co.add_relation(
            r2.egi, "Mortal", r2.created["cut"], hooks=[r1.created["vertex"]]
        )
        assert roundtrips(r3.egi)

    def test_add_relation_refuses_sibling_cut_line(self):
        # Line buried in one cut; relation placed in a sibling cut.
        r1 = co.add_cut(empty())
        r2 = co.add_line(r1.egi, r1.created["cut"])
        r3 = co.add_cut(r2.egi)
        with pytest.raises(ValueError, match="sibling or deeper"):
            co.add_relation(
                r3.egi, "P", r3.created["cut"], hooks=[r2.created["vertex"]]
            )

    def test_add_relation_empty_name_refused(self):
        with pytest.raises(ValueError, match="non-empty name"):
            co.add_relation(empty(), "")


# --------------------------------------------------------------------------- #
# Attach / detach                                                              #
# --------------------------------------------------------------------------- #


class TestAttachDetach:
    def test_attach_prunes_placeholder(self):
        r1 = co.add_relation(empty(), "Human", arity=1)
        r2 = co.add_line(r1.egi)
        line = r2.created["vertex"]
        r3 = co.attach(r2.egi, r1.created["edge"], 0, line)
        assert r3.egi.nu[r1.created["edge"]] == (line,)
        assert r3.removed == (r1.created["placeholders"][0],)
        assert len(r3.egi.V) == 1

    def test_attach_keeps_shared_line(self):
        # The old hook line is wired elsewhere too — not a placeholder, stays.
        r1 = co.add_relation(empty(), "Human", arity=1)
        shared = r1.created["placeholders"][0]
        r2 = co.add_relation(r1.egi, "Greek", hooks=[shared])
        r3 = co.add_line(r2.egi)
        r4 = co.attach(r3.egi, r1.created["edge"], 0, r3.created["vertex"])
        assert r4.removed == ()
        assert shared in {v.id for v in r4.egi.V}

    def test_attach_refuses_buried_line(self):
        r1 = co.add_relation(empty(), "Human", arity=1)
        r2 = co.add_cut(r1.egi)
        r3 = co.add_line(r2.egi, r2.created["cut"])
        with pytest.raises(ValueError, match="sibling or deeper"):
            co.attach(r3.egi, r1.created["edge"], 0, r3.created["vertex"])

    def test_attach_hook_out_of_range(self):
        r1 = co.add_relation(empty(), "Human", arity=1)
        r2 = co.add_line(r1.egi)
        with pytest.raises(ValueError, match="out of range"):
            co.attach(r2.egi, r1.created["edge"], 3, r2.created["vertex"])

    def test_detach_mints_placeholder(self):
        r1 = co.add_line(empty())
        line = r1.created["vertex"]
        r2 = co.add_relation(r1.egi, "Human", hooks=[line])
        r3 = co.detach(r2.egi, r2.created["edge"], 0)
        assert r3.egi.nu[r2.created["edge"]] == (r3.created["vertex"],)
        assert line in {v.id for v in r3.egi.V}  # the line itself stays
        assert roundtrips(r3.egi)


# --------------------------------------------------------------------------- #
# Rename                                                                       #
# --------------------------------------------------------------------------- #


class TestRename:
    def test_rename_relation(self):
        r1 = co.add_relation(empty(), "Humann", arity=1)
        r2 = co.rename(r1.egi, r1.created["edge"], "Human")
        assert r2.egi.rel[r1.created["edge"]] == "Human"

    def test_relabel_constant(self):
        r1 = co.add_constant(empty(), "Socates")
        r2 = co.rename(r1.egi, r1.created["vertex"], "Socrates")
        assert r2.egi.get_vertex(r1.created["vertex"]).label == "Socrates"

    def test_rename_generic_line_refused(self):
        r1 = co.add_line(empty())
        with pytest.raises(ValueError, match="line of identity"):
            co.rename(r1.egi, r1.created["vertex"], "x")

    def test_rename_unknown_element(self):
        with pytest.raises(ValueError, match="does not exist"):
            co.rename(empty(), "ghost", "X")


# --------------------------------------------------------------------------- #
# Erase (cascade)                                                              #
# --------------------------------------------------------------------------- #


class TestErase:
    def test_erase_relation_leaves_lines(self):
        r1 = co.add_relation(empty(), "loves", arity=2)
        r2 = co.erase(r1.egi, r1.created["edge"])
        assert len(r2.egi.E) == 0 and len(r2.egi.V) == 2
        assert roundtrips(r2.egi)

    def test_erase_line_takes_wired_relations(self):
        # The spec's cascade fixture: a line wired to two relations.
        r1 = co.add_line(empty())
        line = r1.created["vertex"]
        r2 = co.add_relation(r1.egi, "Human", hooks=[line])
        r3 = co.add_relation(r2.egi, "Greek", hooks=[line])
        r4 = co.erase(r3.egi, line)
        assert len(r4.egi.V) == 0 and len(r4.egi.E) == 0
        assert set(r4.removed) == {line, r2.created["edge"], r3.created["edge"]}

    def test_erase_cut_takes_subtree(self):
        # A cut holding a sub-draft: relation + nested cut with a line.
        r1 = co.add_cut(empty())
        outer = r1.created["cut"]
        r2 = co.add_relation(r1.egi, "P", outer, arity=1)
        r3 = co.add_cut(r2.egi, outer)
        r4 = co.add_line(r3.egi, r3.created["cut"])
        r5 = co.erase(r4.egi, outer)
        egi = r5.egi
        assert len(egi.V) == 0 and len(egi.E) == 0 and len(egi.Cut) == 0
        assert egi.area == parse_egif("").area or list(egi.area.keys()) == [
            egi.sheet
        ]
        assert roundtrips(egi)

    def test_erase_cut_cascades_outside_edge_wired_to_inside_line(self):
        # A relation inside a cut reaching a sheet line: erasing the *line's*
        # holder is fine, but erasing the cut keeps the sheet line.
        r1 = co.add_line(empty())
        line = r1.created["vertex"]
        r2 = co.add_cut(r1.egi)
        cut = r2.created["cut"]
        r3 = co.add_relation(r2.egi, "Mortal", cut, hooks=[line])
        r4 = co.erase(r3.egi, cut)
        assert line in {v.id for v in r4.egi.V}
        assert len(r4.egi.E) == 0
        # No dangling nu/rel anywhere.
        assert dict(r4.egi.nu) == {} and dict(r4.egi.rel) == {}

    def test_erase_then_nothing_dangling(self):
        r1 = co.add_relation(empty(), "loves", arity=2)
        v1, v2 = r1.created["placeholders"]
        r2 = co.erase(r1.egi, v1)
        # Edge cascaded; the other placeholder survives, no orphan refs.
        assert v2 in {v.id for v in r2.egi.V}
        assert all(v1 not in elems for elems in r2.egi.area.values())

    def test_erase_unknown_element(self):
        with pytest.raises(ValueError, match="does not exist"):
            co.erase(empty(), "ghost")


# --------------------------------------------------------------------------- #
# Move across areas (the composing drag)                                       #
# --------------------------------------------------------------------------- #


class TestMoveToArea:
    def test_move_vertex_into_cut(self):
        r1 = co.add_line(empty())
        r2 = co.add_cut(r1.egi)
        r3 = co.move_to_area(r2.egi, r1.created["vertex"], r2.created["cut"])
        assert r1.created["vertex"] in r3.egi.area[r2.created["cut"]]
        assert roundtrips(r3.egi)

    def test_move_edge_deeper_keeps_reaching_line(self):
        # (Human x) on the sheet → moved into a cut: line still enclosing, OK.
        r1 = co.add_relation(empty(), "Human", arity=1)
        line = r1.created["placeholders"][0]
        r2 = co.add_cut(r1.egi)
        r3 = co.move_to_area(r2.egi, r1.created["edge"], r2.created["cut"])
        assert r3.egi.nu[r1.created["edge"]] == (line,)
        assert roundtrips(r3.egi)

    def test_move_wired_line_deeper_than_its_relation_refused(self):
        # Moving the line *below* its relation breaks the context condition.
        r1 = co.add_relation(empty(), "Human", arity=1)
        line = r1.created["placeholders"][0]
        r2 = co.add_cut(r1.egi)
        with pytest.raises(ValueError, match="across a cut"):
            co.move_to_area(r2.egi, line, r2.created["cut"])

    def test_move_cut_with_contents(self):
        # ~[ (P x) ] moved inside another cut: the subtree travels.
        r1 = co.add_cut(empty())
        inner = r1.created["cut"]
        r2 = co.add_relation(r1.egi, "P", inner, arity=1)
        r3 = co.add_cut(r2.egi)
        host = r3.created["cut"]
        r4 = co.move_to_area(r3.egi, inner, host)
        assert inner in r4.egi.area[host]
        assert r2.created["edge"] in r4.egi.area[inner]
        assert roundtrips(r4.egi)

    def test_move_cut_into_own_interior_refused(self):
        r1 = co.add_cut(empty())
        r2 = co.add_cut(r1.egi, r1.created["cut"])
        with pytest.raises(ValueError, match="own interior"):
            co.move_to_area(r2.egi, r1.created["cut"], r2.created["cut"])

    def test_move_cut_breaking_interior_reach_refused(self):
        # Cut holds (Mortal x) reaching a line inside a *different* cut after
        # the move — the line stops being enclosing → refuse.
        r1 = co.add_cut(empty())
        holder = r1.created["cut"]
        r2 = co.add_line(r1.egi, holder)
        line = r2.created["vertex"]
        r3 = co.add_cut(r2.egi, holder)
        deep = r3.created["cut"]
        r4 = co.add_relation(r3.egi, "Mortal", deep, hooks=[line])
        r5 = co.add_cut(r4.egi)  # sibling of holder, on the sheet
        with pytest.raises(ValueError, match="across a cut"):
            co.move_to_area(r5.egi, deep, r5.created["cut"])


# --------------------------------------------------------------------------- #
# Fragment (graft)                                                             #
# --------------------------------------------------------------------------- #


class TestGraftFragment:
    def test_graft_into_cut(self):
        r1 = co.add_cut(empty())
        r2 = co.graft_fragment(r1.egi, "(Human *x) (Greek x)", r1.created["cut"])
        assert len(r2.egi.E) == 2 and len(r2.egi.V) == 1
        assert set(r2.created["elements"]) <= co._all_ids(r2.egi)
        assert roundtrips(r2.egi)

    def test_graft_bad_egif_refused(self):
        with pytest.raises(ValueError, match="did not parse"):
            co.graft_fragment(empty(), "(((")

    def test_graft_empty_refused(self):
        with pytest.raises(ValueError, match="non-empty EGIF"):
            co.graft_fragment(empty(), "  ")


# --------------------------------------------------------------------------- #
# Compose ∘ undo = identity shapes                                             #
# --------------------------------------------------------------------------- #


class TestInverseShapes:
    def test_add_then_erase_is_identity(self):
        g = parse_egif("(Human *x)")
        r1 = co.add_cut(g)
        assert same_graph(co.erase(r1.egi, r1.created["cut"]).egi, g)
        r2 = co.add_line(g)
        assert same_graph(co.erase(r2.egi, r2.created["vertex"]).egi, g)
        r3 = co.add_relation(g, "Greek", arity=1)
        g3 = co.erase(r3.egi, r3.created["edge"]).egi
        g3 = co.erase(g3, r3.created["placeholders"][0]).egi
        assert same_graph(g3, g)

    def test_attach_then_detach_round_trip(self):
        r1 = co.add_relation(empty(), "Human", arity=1)
        r2 = co.add_line(r1.egi)
        before = r2.egi
        r3 = co.attach(before, r1.created["edge"], 0, r2.created["vertex"])
        r4 = co.detach(r3.egi, r1.created["edge"], 0)
        assert same_graph(r4.egi, before)


# --------------------------------------------------------------------------- #
# Dispatcher + replay determinism                                              #
# --------------------------------------------------------------------------- #


class TestDispatcherAndReplay:
    def test_unknown_action_refused(self):
        with pytest.raises(ValueError, match="Unknown compose action"):
            apply_compose(empty(), "compose.summon", {})

    def test_recorded_parameters_replay_exactly(self):
        # Run a whole composing episode through the dispatcher, re-execute
        # each step from its recorded parameters, require id-exact states.
        g0 = empty()
        episode = [
            ("add_relation", {"name": "Human", "arity": 1}),
            ("add_cut", {}),
            ("add_line", {}),
        ]
        states = [g0]
        recorded = []
        g = g0
        for action, params in episode:
            r = apply_compose(g, action, params)
            recorded.append((action, r.recorded_parameters))
            g = r.egi
            states.append(g)
        # attach uses ids minted above
        human_edge = recorded[0][1]["edge_id"]
        line = recorded[2][1]["vertex_id"]
        r = apply_compose(
            g, "attach", {"edge_id": human_edge, "hook_index": 0, "vertex_id": line}
        )
        recorded.append(("attach", r.recorded_parameters))
        states.append(r.egi)

        g = g0
        for (action, params), expected in zip(recorded, states[1:]):
            r = apply_compose(g, action, params)
            assert co._same_state(r.egi, expected), action
            g = r.egi

    def test_verify_chain_replay_compose_steps(self):
        from tomos_service import ChainStep, TransformationChain

        g0 = empty()
        r1 = apply_compose(g0, "add_relation", {"name": "Human", "arity": 1})
        r2 = apply_compose(r1.egi, "add_cut", {})
        steps = [
            ChainStep(
                step_id="st-1",
                rule_name="compose.add_relation",
                from_state_id="s0",
                to_state_id="s1",
                parameters=r1.recorded_parameters,
                timestamp="t",
            ),
            ChainStep(
                step_id="st-2",
                rule_name="compose.add_cut",
                from_state_id="s1",
                to_state_id="s2",
                parameters=r2.recorded_parameters,
                timestamp="t",
            ),
            ChainStep(
                step_id="st-3",
                rule_name=co.FIX_GRAPH_STEP,
                from_state_id="s2",
                to_state_id="s3",
                parameters={},
                timestamp="t",
            ),
        ]
        chain = TransformationChain(
            initial_state_id="s0",
            steps=steps,
            states={"s0": g0, "s1": r1.egi, "s2": r2.egi, "s3": r2.egi},
        )
        assert verify_chain_replay(chain) == 3

    def test_verify_chain_replay_catches_divergence(self):
        from tomos_service import ChainStep, TransformationChain

        g0 = empty()
        r1 = apply_compose(g0, "add_line", {})
        bad_params = dict(r1.recorded_parameters)
        bad_params["vertex_id"] = "v_other"
        chain = TransformationChain(
            initial_state_id="s0",
            steps=[
                ChainStep(
                    step_id="st-1",
                    rule_name="compose.add_line",
                    from_state_id="s0",
                    to_state_id="s1",
                    parameters=bad_params,
                    timestamp="t",
                )
            ],
            states={"s0": g0, "s1": r1.egi},
        )
        with pytest.raises(ValueError, match="Replay diverged"):
            verify_chain_replay(chain)


# --------------------------------------------------------------------------- #
# The user's own scenario (spec §7), headless                                  #
# --------------------------------------------------------------------------- #


class TestComposeScenario:
    def test_blank_sheet_to_mortal_human(self):
        """Blank sheet → Human spot → line → attach → cut → Mortal inside,
        asserting the linear mirror at each step."""
        g = empty()
        assert generate_egif(g).strip() == ""

        r = co.add_relation(g, "Human", arity=1)
        g = r.egi
        human, line0 = r.created["edge"], r.created["placeholders"][0]
        assert same_graph(g, parse_egif("(Human *x)"))

        r = co.add_line(g)
        g, line = r.egi, r.created["vertex"]
        assert same_graph(g, parse_egif("(Human *x) *y"))

        r = co.attach(g, human, 0, line)
        g = r.egi
        assert r.removed == (line0,)
        assert same_graph(g, parse_egif("(Human *x)"))

        r = co.add_cut(g)
        g, cut = r.egi, r.created["cut"]
        assert same_graph(g, parse_egif("(Human *x) ~[ ]"))

        r = co.add_relation(g, "Mortal", cut, hooks=[line])
        g = r.egi
        assert same_graph(g, parse_egif("(Human *x) ~[ (Mortal x) ]"))
        assert roundtrips(g)
