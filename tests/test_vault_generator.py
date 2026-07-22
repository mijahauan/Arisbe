from pathlib import Path
import hashlib
from vault_generator import generate_vault, VaultManifest
from vault_world import VaultWorld


def _tree_sha(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.md")):
        h.update(str(p.relative_to(root)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def test_generate_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    m1 = generate_vault(a, seed=20260721, folders=3, notes_per_folder=5,
                        cross_folder_link_prob=0.2, journal_len=6)
    m2 = generate_vault(b, seed=20260721, folders=3, notes_per_folder=5,
                        cross_folder_link_prob=0.2, journal_len=6)
    assert _tree_sha(a) == _tree_sha(b)
    assert m1 == m2


def test_generated_tree_is_vaultworld_readable(tmp_path):
    m = generate_vault(tmp_path, seed=1, folders=4, notes_per_folder=6,
                       cross_folder_link_prob=0.15, journal_len=8)
    w = VaultWorld(tmp_path)
    # The manifest's `folders` are the content folders only; VaultWorld's
    # top_dirs() also picks up the "Journal" directory that holds the dated
    # journal spine, so it is a superset, not an equal set (author's
    # resolution of the brief's Step 4 ambiguity note).
    assert set(m.folders) <= set(w.top_dirs())
    assert "Journal" in w.top_dirs()
    # notes() globs "*.md" case-insensitively-in-suffix-only, so it also
    # counts the single Journal/Journal.md spine file alongside the
    # folders*notes_per_folder content notes (confirmed by reading
    # VaultWorld.notes()/journal_paths() at src/vault_world.py:206/365).
    assert len(w.notes()) == 4 * 6 + 1
    assert len(w.journal_paths()) >= 1
    # every cross-link's endpoints are real notes in different folders
    for cl in m.cross_links:
        assert cl.source_folder != cl.target_folder
        assert cl.target_note in m.notes


def test_cross_link_prob_monotone(tmp_path):
    lo = generate_vault(tmp_path / "lo", seed=7, folders=4, notes_per_folder=20,
                        cross_folder_link_prob=0.05, journal_len=4)
    hi = generate_vault(tmp_path / "hi", seed=7, folders=4, notes_per_folder=20,
                        cross_folder_link_prob=0.6, journal_len=4)
    assert len(hi.cross_links) > len(lo.cross_links)


def test_bodies_are_sentinel_only(tmp_path):
    generate_vault(tmp_path, seed=1, folders=2, notes_per_folder=3,
                   cross_folder_link_prob=0.0, journal_len=3)
    for p in tmp_path.rglob("*.md"):
        assert "SENTINELBODY" in p.read_text()


def test_journal_entries_are_readable(tmp_path):
    # Finding 1: VaultWorld.journal_entries() only starts a new entry at a
    # BARE date-line (the whole stripped line matches the date shape). The
    # old one-line "- YYYY-MM-DD SENTINELBODY entry N" format fails that
    # shape check for every line, so journal_entries() returned zero entries
    # regardless of journal_len. This is biting: it fails against the old
    # generator and passes once each entry is a bare date-line followed by a
    # separate body line.
    generate_vault(tmp_path, seed=9, folders=1, notes_per_folder=1,
                   cross_folder_link_prob=0.0, journal_len=12)
    w = VaultWorld(tmp_path)
    jp = w.journal_paths()[0]
    assert len(w.journal_entries(jp)[0]) == 12
    assert w.journal_facts(jp) != ""


def test_note_stems_are_globally_unique(tmp_path):
    # Finding 2 (part a): VaultWorld._stems() resolves a bare wikilink stem
    # to exactly one note via a first-wins setdefault. The old generator
    # named every folder's notes identically ("note-0".."note-{n-1}"), so
    # stems collided across folders. Stems must be globally unique.
    m = generate_vault(tmp_path, seed=5, folders=4, notes_per_folder=6,
                       cross_folder_link_prob=0.3, journal_len=4)
    stems = [Path(n).stem for n in m.notes]
    assert len(stems) == len(set(stems))


def test_cross_links_resolve_as_internal_links(tmp_path):
    # Finding 2 (part b): the old generator wrote cross-folder wikilink text
    # as the full path "[[Folder-k/note-i]]", which never matches a bare
    # stem key in VaultWorld._stems() — every cross-link emitted as an
    # unresolved "(links_out ...)" atom instead of a resolved internal
    # "(links ...)" atom. With globally-unique bare stems as link text,
    # resolution must succeed.
    m = generate_vault(tmp_path, seed=5, folders=4, notes_per_folder=6,
                       cross_folder_link_prob=0.6, journal_len=4)
    assert len(m.cross_links) >= 1
    w = VaultWorld(tmp_path)
    for cl in m.cross_links:
        facts = w.note_facts(cl.source_note)
        source_id = w.note_id(cl.source_note)
        target_id = w.note_id(cl.target_note)
        assert f'(links "{source_id}" "{target_id}")' in facts
        assert f'(links_out "{source_id}" "{target_id}")' not in facts
