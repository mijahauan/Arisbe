from egif_parser_dau import parse_egif
from world_scroll import find_world_scroll
from west_coordinator import Coordinator, member_relation_names


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
