from egif_parser_dau import parse_egif
from world_scroll import find_world_scroll
from vault_generator import CrossLink, VaultManifest
from west_coordinator import Coordinator, member_relation_names, note_id_constants


def test_member_relation_names():
    m = parse_egif('(links_to "a" "b") (has_tag "a" "topic-a")')
    names = member_relation_names(m)
    assert names == frozenset({"links_to", "has_tag"})


def test_coordinator_digest_starts_as_recognized_world_scroll():
    coord = Coordinator()
    scroll = find_world_scroll(coord._digest)
    assert scroll is not None
    assert scroll.cell_ids == ()          # empty residence: no cells yet
    assert len(scroll.hold_ids) >= 1


def test_coordinator_ingest_is_mention_not_use_and_dedups():
    coord = Coordinator()
    member = parse_egif('(links_to "a" "b") (in_folder "a" "Folder-0")')
    before = member.serialize() if hasattr(member, "serialize") else str(member.E)
    n1 = coord.ingest("Folder-0", member)
    assert n1 == 2                          # two distinct relation names -> two cells
    assert ("Folder-0", "links_to") in coord.held
    assert ("Folder-0", "in_folder") in coord.held
    # member M untouched (mention-not-use)
    after = member.serialize() if hasattr(member, "serialize") else str(member.E)
    assert before == after
    # re-ingesting the same names writes nothing new
    n2 = coord.ingest("Folder-0", member)
    assert n2 == 0
    assert coord.cells_written == 2


def test_coordinator_separates_folders():
    coord = Coordinator()
    coord.ingest("Folder-0", parse_egif('(links_to "a" "b")'))
    coord.ingest("Folder-1", parse_egif('(links_to "c" "d")'))
    assert ("Folder-0", "links_to") in coord.held
    assert ("Folder-1", "links_to") in coord.held
    assert coord.cells_written == 2


def test_coordinator_digest_stays_recognized_world_scroll_after_ingest():
    coord = Coordinator()
    coord.ingest("Folder-0", parse_egif('(links_to "a" "b") (has_tag "a" "x")'))
    scroll = find_world_scroll(coord._digest)
    assert scroll is not None
    assert len(scroll.cell_ids) == 2


def test_note_id_constants_reads_labels():
    m = parse_egif('(in_folder "Folder-0/note-0.md" "Folder-0")')
    consts = note_id_constants(m)
    assert "Folder-0/note-0.md" in consts
    assert "Folder-0" in consts


def test_consistency_scan_zero_on_synthetic():
    coord = Coordinator()
    coord.ingest("Folder-0", parse_egif('(links_to "a" "b")'))
    coord.ingest("Folder-1", parse_egif('(links_to "c" "d")'))
    assert coord.consistency_scan() == 0
    assert coord.scan_comparisons >= 0


def test_coverage_counts_resolved_cross_links():
    coord = Coordinator()
    # target note "Folder-1/note-2" is ingested by Folder-1's member (its id present)
    m0 = parse_egif('(in_folder "Folder-0/note-0" "Folder-0")')
    m1 = parse_egif('(in_folder "Folder-1/note-2" "Folder-1")')
    member_ms = {"Folder-0": m0, "Folder-1": m1}
    manifest = VaultManifest(
        folders=("Folder-0", "Folder-1"),
        notes=("Folder-0/note-0.md", "Folder-1/note-2.md"),
        cross_links=(
            CrossLink("Folder-0/note-0.md", "Folder-0",
                      "Folder-1/note-2.md", "Folder-1"),          # resolves
            CrossLink("Folder-0/note-0.md", "Folder-0",
                      "Folder-1/note-9.md", "Folder-1"),          # unresolved
        ),
        journal_len=0,
    )
    cov, unresolved = coord.coverage(manifest, member_ms)
    assert unresolved == 1
    assert abs(cov - 0.5) < 1e-9


def test_coverage_rejects_substring_false_positive():
    # "Folder-1/note-1.md" is never ingested, but it IS a substring of
    # "Folder-1/note-10.md" and "Folder-1/note-11.md", which are. A
    # substring-based match would falsely resolve the cross-link; exact
    # membership must not.
    coord = Coordinator()
    m1 = parse_egif(
        '(in_folder "Folder-1/note-10.md" "Folder-1") '
        '(in_folder "Folder-1/note-11.md" "Folder-1")'
    )
    member_ms = {"Folder-1": m1}
    manifest = VaultManifest(
        folders=("Folder-1",),
        notes=("Folder-1/note-10.md", "Folder-1/note-11.md"),
        cross_links=(
            CrossLink("Folder-0/note-0.md", "Folder-0",
                      "Folder-1/note-1.md", "Folder-1"),           # never ingested
        ),
        journal_len=0,
    )
    cov, unresolved = coord.coverage(manifest, member_ms)
    assert (cov, unresolved) == (0.0, 1)


def test_broker_route_counts_and_resolves():
    coord = Coordinator()
    m1 = parse_egif('(in_folder "Folder-1/note-2" "Folder-1")')
    member_ms = {"Folder-1": m1}
    hit = coord.route("Folder-0", "Folder-1/note-2.md", "Folder-1", member_ms)
    miss = coord.route("Folder-0", "Folder-1/note-9.md", "Folder-1", member_ms)
    assert hit is not None
    assert miss is None
    assert coord.routes == 2


def test_incremental_scan_counters_start_at_zero():
    coord = Coordinator()
    assert coord.scan_comparisons_incremental == 0
    assert coord.consistency_scan_incremental() == 0
    assert coord.scan_comparisons_incremental == 0


def test_incremental_scan_compares_each_pair_exactly_once_over_a_run():
    """The Arm I invariant: however many rounds elapse, the incremental total
    equals ONE naive scan's total — every unordered pair compared exactly once."""
    coord = Coordinator()
    m0 = parse_egif('(links_to "a" "b") (has_tag "a" "t")')
    m1 = parse_egif('(links_to "c" "d") (in_folder "c" "F1")')
    # Round 1: one folder ingests, then an incremental scan.
    coord.ingest("F0", m0)
    coord.consistency_scan_incremental()
    # Round 2: another folder ingests, then another incremental scan.
    coord.ingest("F1", m1)
    coord.consistency_scan_incremental()
    # Rounds 3-5: nothing new arrives; incremental scans must be free.
    before = coord.scan_comparisons_incremental
    for _ in range(3):
        coord.consistency_scan_incremental()
    assert coord.scan_comparisons_incremental == before, (
        "an incremental scan with no new cells must cost nothing"
    )
    h = len(coord.held)
    assert coord.scan_comparisons_incremental == h * (h - 1) // 2


def test_naive_scan_is_unchanged_and_costs_a_full_pass_every_call():
    """Arm N (the E1 behaviour) must be untouched: every call re-compares all pairs."""
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b") (has_tag "a" "t")'))
    h = len(coord.held)
    coord.consistency_scan()
    coord.consistency_scan()
    assert coord.scan_comparisons == 2 * (h * (h - 1) // 2)


def test_incremental_and_naive_counters_are_independent():
    coord = Coordinator()
    coord.ingest("F0", parse_egif('(links_to "a" "b")'))
    coord.consistency_scan()
    assert coord.scan_comparisons_incremental == 0
    coord.consistency_scan_incremental()
    h = len(coord.held)
    assert coord.scan_comparisons_incremental == h * (h - 1) // 2
