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
