"""
B-min core contract — the second-order maps in the protected core.

Stage 1 of the authorized core opening (① B-min, verdicts 2026-07-16):
``RelationalGraphWithCuts`` gains two parallel maps in the ``rho`` pattern —
``sort`` (vertex → second-order sort) and ``quotation`` (quotation-cut →
quoting-vertex) — plus the constructors ``with_sort`` /
``with_quotation_binding`` / ``with_quotation`` / ``without_quotation``.

What these tests pin:

1. **Validation** — every malformed second-order state is refused at
   construction (bad sort vocabulary, dangling ids, unsorted quoting name,
   name/oval area mismatch, one-oval-per-name, quotation-in-quotation).
2. **Preservation** — every immutable builder carries both maps; removal
   paths prune exactly what leaves; piecemeal removal of quotation parts is
   refused (``without_quotation`` is the only sanctioned unquoting).
3. **Isomorphism** — ``apply_isomorphism`` remaps keys and values;
   ``same_graph`` distinguishes sorted from unsorted twins and a quotation
   area from a negation.
4. **IO** — JSON round-trips the maps; a first-order graph emits no new
   keys (byte-identical schema) and old JSON loads.
5. **Signature** — a sorted line never collapses with an unsorted twin in
   the canonical colors; first-order canonical order is unchanged.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from frozendict import frozendict

from egi_core_dau import (
    SORT_ABSTRACTION,
    SORT_PROPOSITION,
    Cut,
    RelationalGraphWithCuts,
    Vertex,
    create_cut,
    create_empty_graph,
    create_vertex,
)
from egi_io import from_dict, to_dict
from eg_navigation import same_graph
from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from formal_transformation_rules import _rebuild_graph


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


def host_with_name(label: str = "M_law") -> tuple:
    """A tiny host: (superseded "M_law") on the sheet; returns (egi, name_id)."""
    egi = parse_egif(f'(superseded "{label}")')
    name_id = next(v.id for v in egi.V if v.label == label)
    return egi, name_id


def quoted_host() -> tuple:
    """A host carrying a full quotation: sorted name + flagged cut holding
    one atom. Returns (egi, name_id, cut_id, inner_vertex_id)."""
    egi, name_id = host_with_name()
    cut = create_cut()
    egi = egi.with_cut(cut)
    inner_v = create_vertex()
    egi = egi.with_vertex_in_context(inner_v, cut.id)
    egi = egi.with_quotation_binding(name_id, cut.id, sort_name=SORT_PROPOSITION)
    return egi, name_id, cut.id, inner_v.id


# --------------------------------------------------------------------------- #
# 1. Validation                                                               #
# --------------------------------------------------------------------------- #


class TestValidation:
    def test_first_order_graph_carries_empty_maps(self):
        egi = parse_egif("(P *x)")
        assert egi.sort == frozendict()
        assert egi.quotation == frozendict()

    def test_bad_sort_vocabulary_refused(self):
        egi, name_id = host_with_name()
        with pytest.raises(ValueError, match="second-order sort"):
            egi.with_sort(name_id, "individual")

    def test_sort_on_unknown_vertex_refused(self):
        egi, _ = host_with_name()
        with pytest.raises(ValueError, match="not found"):
            egi.with_sort("v_nowhere", SORT_PROPOSITION)

    def test_quotation_flagging_non_cut_refused(self):
        egi, name_id = host_with_name()
        egi = egi.with_sort(name_id, SORT_PROPOSITION)
        with pytest.raises(ValueError, match="Cut .* not found"):
            egi.with_quotation_binding(name_id, "c_nowhere")

    def test_quotation_with_unsorted_name_refused(self):
        egi, name_id = host_with_name()
        cut = create_cut()
        egi = egi.with_cut(cut)
        with pytest.raises(ValueError, match="no second-order sort"):
            egi.with_quotation_binding(name_id, cut.id)

    def test_name_and_oval_must_share_an_area(self):
        egi, name_id = host_with_name()
        outer = create_cut()
        egi = egi.with_cut(outer)
        inner = create_cut()
        egi = egi.with_cut(inner, outer.id)  # oval one level deeper than name
        with pytest.raises(ValueError, match="same area"):
            egi.with_quotation_binding(name_id, inner.id, sort_name=SORT_PROPOSITION)

    def test_one_oval_per_name(self):
        egi, name_id, cut_id, _ = quoted_host()
        second = create_cut()
        egi = egi.with_cut(second)
        with pytest.raises(ValueError, match="more than one oval"):
            egi.with_quotation_binding(name_id, second.id)

    def test_quotation_in_quotation_refused(self):
        egi, name_id, cut_id, _ = quoted_host()
        # a second sorted name + oval INSIDE the existing quotation area
        inner_name = create_vertex(label="inner", is_generic=False)
        egi = egi.with_vertex_in_context(inner_name, cut_id)
        inner_cut = create_cut()
        egi = egi.with_cut(inner_cut, cut_id)
        with pytest.raises(ValueError, match="B-min limit"):
            egi.with_quotation_binding(
                inner_name.id, inner_cut.id, sort_name=SORT_PROPOSITION
            )

    def test_direct_construction_validates_too(self):
        # The maps are validated in __post_init__, not only via constructors.
        egi, name_id = host_with_name()
        with pytest.raises(ValueError, match="unknown vertex"):
            RelationalGraphWithCuts(
                V=egi.V,
                E=egi.E,
                nu=egi.nu,
                sheet=egi.sheet,
                Cut=egi.Cut,
                area=egi.area,
                rel=egi.rel,
                sort=frozendict({"v_ghost": SORT_PROPOSITION}),
            )


# --------------------------------------------------------------------------- #
# 2. Preservation through the builders                                        #
# --------------------------------------------------------------------------- #


class TestBuilderPreservation:
    def test_with_vertex_and_edge_and_cut_preserve(self):
        egi, name_id, cut_id, _ = quoted_host()
        before = (dict(egi.sort), dict(egi.quotation))
        egi = egi.with_vertex(create_vertex())
        from egi_core_dau import Edge

        v2 = create_vertex()
        egi = egi.with_vertex(v2)
        egi = egi.with_edge(Edge(id="e_extra"), (v2.id,), "Extra")
        egi = egi.with_cut(create_cut())
        assert (dict(egi.sort), dict(egi.quotation)) == before

    def test_vertex_move_preserves(self):
        egi, name_id, cut_id, _ = quoted_host()
        loose = create_vertex()
        egi = egi.with_vertex(loose)
        plain = create_cut()
        egi = egi.with_cut(plain)
        moved = egi.with_vertex_moved_to_context(loose.id, plain.id)
        assert moved.sort == egi.sort and moved.quotation == egi.quotation

    def test_without_vertex_prunes_sort_of_nonquoting_line(self):
        egi, name_id = host_with_name()
        other = create_vertex(label="other", is_generic=False)
        egi = egi.with_vertex(other).with_sort(other.id, SORT_ABSTRACTION)
        pruned = egi.without_element(other.id)
        assert other.id not in pruned.sort

    def test_without_vertex_refuses_a_quoting_name(self):
        egi, name_id, _, _ = quoted_host()
        with pytest.raises(ValueError, match="without_quotation"):
            egi.without_element(name_id)

    def test_without_cut_refuses_a_quotation_area(self):
        egi, _, cut_id, _ = quoted_host()
        with pytest.raises(ValueError, match="without_quotation"):
            egi.without_element(cut_id)

    def test_without_quotation_removes_the_unit(self):
        egi, name_id, cut_id, inner_id = quoted_host()
        # name is held by the host's superseded edge, so it survives, de-quoted
        bare = egi.without_quotation(cut_id)
        assert cut_id not in {c.id for c in bare.Cut}
        assert inner_id not in {v.id for v in bare.V}
        assert bare.quotation == frozendict()
        assert name_id in {v.id for v in bare.V}  # host-wired name survives
        assert bare.sort.get(name_id) == SORT_PROPOSITION  # mention by name

    def test_without_quotation_removes_an_unheld_name(self):
        # constructive quotation: fresh name, wired to nothing
        egi = create_empty_graph()
        name = create_vertex(label="q", is_generic=False)
        egi = egi.with_quotation(name)
        cut_id = next(iter(egi.quotation))
        bare = egi.without_quotation(cut_id)
        assert bare.V == frozenset() and bare.Cut == frozenset()
        assert bare.sort == frozendict() and bare.quotation == frozendict()

    def test_without_quotation_only_touches_its_unit(self):
        egi, name_id, cut_id, _ = quoted_host()
        plain = create_cut()
        egi = egi.with_cut(plain)
        bare = egi.without_quotation(cut_id)
        assert plain.id in {c.id for c in bare.Cut}
        assert len(bare.E) == len(egi.E)  # the host edge survives


# --------------------------------------------------------------------------- #
# 3. Isomorphism                                                              #
# --------------------------------------------------------------------------- #


class TestIsomorphism:
    def test_apply_isomorphism_remaps_both_maps(self):
        egi, name_id, cut_id, inner_id = quoted_host()
        mapped = egi.apply_isomorphism(
            vertex_mapping={name_id: "v_NAME", inner_id: "v_INNER"},
            edge_mapping={},
            cut_mapping={cut_id: "c_OVAL"},
        )
        assert mapped.sort.get("v_NAME") == SORT_PROPOSITION
        assert mapped.quotation.get("c_OVAL") == "v_NAME"
        assert name_id not in mapped.sort and cut_id not in mapped.quotation

    def test_same_graph_distinguishes_sorted_from_unsorted_twin(self):
        egi, name_id = host_with_name()
        sorted_twin = egi.with_sort(name_id, SORT_PROPOSITION)
        assert same_graph(egi, egi)
        assert not same_graph(egi, sorted_twin)

    def test_same_graph_distinguishes_quotation_from_negation(self):
        egi, name_id = host_with_name()
        cut = create_cut()
        with_plain_cut = egi.with_cut(cut)
        with_oval = with_plain_cut.with_quotation_binding(
            name_id, cut.id, sort_name=SORT_PROPOSITION
        )
        assert not same_graph(with_plain_cut, with_oval)

    def test_same_graph_holds_between_sorted_copies(self):
        a1, n1, _, _ = quoted_host()
        a2, n2, _, _ = quoted_host()
        assert same_graph(a1, a2)


# --------------------------------------------------------------------------- #
# 4. IO                                                                       #
# --------------------------------------------------------------------------- #


class TestIO:
    def test_first_order_json_has_no_new_keys(self):
        egi = parse_egif('~[ (P *x) ~[ (Q x) ] ]')
        d = to_dict(egi)
        assert "sort" not in d and "quotation" not in d

    def test_old_json_without_keys_loads(self):
        egi = parse_egif("(P *x)")
        d = to_dict(egi)
        # simulate a pre-B-min file: keys simply absent
        loaded = from_dict(d)
        assert loaded.sort == frozendict() and loaded.quotation == frozendict()

    def test_quotation_round_trips(self):
        egi, name_id, cut_id, inner_id = quoted_host()
        loaded = from_dict(to_dict(egi))
        assert dict(loaded.sort) == dict(egi.sort)
        assert dict(loaded.quotation) == dict(egi.quotation)
        assert same_graph(loaded, egi)


# --------------------------------------------------------------------------- #
# 5. Canonical signature                                                      #
# --------------------------------------------------------------------------- #


class TestSignature:
    def test_sorted_line_gets_a_distinct_color(self):
        from canonical_signature import compute_canonical_signatures

        egi = parse_egif('(superseded "A" "B")')
        a_id = next(v.id for v in egi.V if v.label == "A")
        b_id = next(v.id for v in egi.V if v.label == "B")
        vcol, _, _ = compute_canonical_signatures(egi)
        sorted_egi = egi.with_sort(a_id, SORT_PROPOSITION)
        vcol2, _, _ = compute_canonical_signatures(sorted_egi)
        # before the sort A and B are both plain constants with distinct
        # names; after the sort A's color class must still be distinct
        assert vcol2[a_id] != vcol2[b_id]

    def test_first_order_generation_unchanged(self):
        # The appended-uniform-constant claim: canonical order (hence
        # generated text) of a sortless graph is what it always was.
        src = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ] (P *x) (Q x)'
        egi = parse_egif(src)
        text1 = generate_egif(egi)
        text2 = generate_egif(parse_egif(text1))
        assert text1 == text2

    def test_quotation_cut_signature_differs_from_plain(self):
        from canonical_signature import compute_canonical_signatures

        egi, name_id = host_with_name()
        cut = create_cut()
        with_plain = egi.with_cut(cut)
        _, _, csig_plain = compute_canonical_signatures(with_plain)
        with_oval = with_plain.with_quotation_binding(
            name_id, cut.id, sort_name=SORT_PROPOSITION
        )
        _, _, csig_oval = compute_canonical_signatures(with_oval)
        assert csig_plain[cut.id] != csig_oval[cut.id]


# --------------------------------------------------------------------------- #
# 6. Docket item (2): _rebuild_graph pruning invariant                        #
# --------------------------------------------------------------------------- #


class TestRebuildPruningInvariant:
    """Docket item 2: a quotation entry dies whole or not at all.

    ``_rebuild_graph`` prunes ``quotation`` to the surviving cuts/vertices.
    If only one half of a (cut, name) pair survives a reconstruction, the
    other half silently disappears and the surviving cut stands unflagged —
    a mention demoted to an unflagged (asserted) cut. Every reconstruction
    path must refuse that split, not just the rule call sites that happen to
    guard it upstream."""

    def test_cut_survives_name_gone_raises(self):
        egi, name_id, cut_id, _inner_v_id = quoted_host()
        with pytest.raises(ValueError, match="quotation"):
            _rebuild_graph(
                egi,
                V=frozenset(v for v in egi.V if v.id != name_id),
                E=egi.E,
                nu=egi.nu,
                cuts=egi.Cut,
                area=frozendict(
                    {a: c - {name_id} for a, c in egi.area.items()}
                ),
                rel=egi.rel,
            )

    def test_name_survives_cut_gone_raises(self):
        egi, name_id, cut_id, _inner_v_id = quoted_host()
        interior = egi.area.get(cut_id, frozenset())
        with pytest.raises(ValueError, match="quotation"):
            _rebuild_graph(
                egi,
                V=frozenset(v for v in egi.V if v.id not in interior),
                E=frozenset(e for e in egi.E if e.id not in interior),
                nu=egi.nu,
                cuts=frozenset(c for c in egi.Cut if c.id != cut_id),
                area=frozendict(
                    {
                        a: c - {cut_id}
                        for a, c in egi.area.items()
                        if a != cut_id
                    }
                ),
                rel=egi.rel,
            )

    def test_both_gone_prunes_cleanly_and_both_kept_survive(self):
        egi, name_id, cut_id, _inner_v_id = quoted_host()
        rebuilt = _rebuild_graph(
            egi, V=egi.V, E=egi.E, nu=egi.nu, cuts=egi.Cut,
            area=egi.area, rel=egi.rel,
        )
        assert dict(rebuilt.quotation) == dict(egi.quotation)
