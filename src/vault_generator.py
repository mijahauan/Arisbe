"""Deterministic, structure-only synthetic vault for the West-in-kytē E1 harness.

Metadata-only bodies (a SENTINELBODY marker) honor the custody discipline — the
reader never needs bodies. Deterministic given `seed`: a per-item sha256 stream
replaces any RNG (Date.now/random/hash() are forbidden here per the plan's
Global Constraints)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

_SENTINEL = "SENTINELBODY"


@dataclass(frozen=True)
class CrossLink:
    source_note: str
    source_folder: str
    target_note: str
    target_folder: str


@dataclass(frozen=True)
class VaultManifest:
    folders: Tuple[str, ...]
    notes: Tuple[str, ...]          # relpaths, e.g. "Folder-0/note-3.md"
    cross_links: Tuple[CrossLink, ...]
    journal_len: int


def _unit(seed: int, *parts: str) -> float:
    """A deterministic float in [0, 1) keyed by (seed, parts)."""
    h = hashlib.sha256((str(seed) + "|" + "|".join(parts)).encode()).hexdigest()
    return int(h[:16], 16) / float(1 << 64)


def _pick(seed: int, tag: str, options):
    options = list(options)
    idx = int(_unit(seed, tag, "pick") * len(options))
    return options[min(idx, len(options) - 1)]


def generate_vault(dest: Path, *, seed: int, folders: int, notes_per_folder: int,
                   cross_folder_link_prob: float, journal_len: int) -> VaultManifest:
    dest = Path(dest)
    folder_names = tuple(f"Folder-{k}" for k in range(folders))
    # Note stems must be GLOBALLY unique across the whole vault: VaultWorld._stems()
    # resolves a bare wikilink stem to exactly one note (first-wins setdefault), so
    # per-folder-repeating names ("note-0" in every folder) make resolution
    # ambiguous. A global index g = k * notes_per_folder + i gives every note a
    # unique "note-{g}" stem regardless of which folder it lives in.
    note_relpaths = []
    note_by_folder_local = {}  # (folder_name, local_i) -> relpath
    for k, fk in enumerate(folder_names):
        for i in range(notes_per_folder):
            g = k * notes_per_folder + i
            rp = f"{fk}/note-{g}.md"
            note_relpaths.append(rp)
            note_by_folder_local[(fk, i)] = rp
    note_relpaths = tuple(note_relpaths)

    # First pass: decide cross-folder links deterministically.
    cross = []
    for rp in note_relpaths:
        fk = rp.split("/")[0]
        if _unit(seed, rp, "cross") < cross_folder_link_prob:
            target_folder = _pick(seed, rp + "tf",
                                  [f for f in folder_names if f != fk])
            ti = int(_unit(seed, rp, "ti") * notes_per_folder)
            ti = min(ti, notes_per_folder - 1)
            target_note = note_by_folder_local[(target_folder, ti)]
            cross.append(CrossLink(rp, fk, target_note, target_folder))
    cross_by_source = {}
    for cl in cross:
        cross_by_source.setdefault(cl.source_note, []).append(cl)

    # Second pass: write the tree (structure-only, sentinel bodies).
    for rp in note_relpaths:
        p = dest / rp
        p.parent.mkdir(parents=True, exist_ok=True)
        # Wikilink text is the bare, globally-unique stem — VaultWorld._stems()
        # resolves wikilinks by bare lowercase stem, not by full path.
        links = "".join(f"[[{Path(cl.target_note).stem}]] "
                        for cl in cross_by_source.get(rp, []))
        tag = _pick(seed, rp + "tag", ["topic-a", "topic-b", "topic-c"])
        p.write_text(
            f"---\ntags: [{tag}]\n---\n{_SENTINEL} {links}\n"
        )

    # A dated journal spine under Journal/. Named "Journal.md" (capital J) —
    # not "journal.md" — because VaultWorld.journal_paths() globs
    # "Journal*.md", and pathlib's glob matching is case-sensitive even on
    # macOS's default case-insensitive filesystem (confirmed empirically);
    # a lowercase filename would be silently invisible to journal_paths()
    # while still being counted by notes()'s case-insensitive-suffix "*.md".
    jdir = dest / "Journal"
    jdir.mkdir(parents=True, exist_ok=True)
    lines = []
    for d in range(journal_len):
        year = 1975 + d  # a wide span so entries_per_decade is populated
        # VaultWorld.journal_entries() starts a new entry ONLY at a BARE
        # date-line (the whole stripped line must match the date-line shape) —
        # a leading "- " or trailing text disqualifies it. So each entry is two
        # lines: a bare date-line, then a separate body line.
        lines.append(f"{year}-01-0{(d % 9) + 1}")
        lines.append(f"{_SENTINEL} entry {d}")
    (jdir / "Journal.md").write_text(
        "---\ntags: [journal]\n---\n" + "\n".join(lines) + "\n"
    )

    return VaultManifest(
        folders=folder_names,
        notes=note_relpaths,
        cross_links=tuple(cross),
        journal_len=journal_len,
    )
