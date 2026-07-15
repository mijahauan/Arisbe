"""**Facets** — the axis a reader browses by, beside the one the code records.

``UoDCategory`` answers a *producer's* question: how was this made, and does it
carry a history? (Static import vs dynamic session — and the code depends on that
gating.) It was never a subject taxonomy, and using it as one is what turned
``domain_model`` into a junk drawer: seven imported ontologies, two game boards,
three dialogue episodes, a Gamma demonstration, and the whole arithmetic ladder,
all on one shelf because it is the only shelf that means "…and the rest."

The proof that the axis fails a reader: the **Gamma demonstration trio** —
``broken_cut_square``, ``would_be_de_inesse``, ``would_be_courses`` — is *one set of
three* (docs/EXEMPLARS.md §5.1) filed under three different categories. You cannot
find them together.

So this module adds the reader's axis without touching the producer's:

    subject  — what is it ABOUT   (mathematics · logic · ontology · modality ·
                                   dialogue · worlds · live-run)
    purpose  — what is it FOR     (teach · prove · demonstrate · reference ·
                                   play · model)

**Derived, not invented.** Every UoD in the corpus already carries annotation tags
(``ontology``, ``modality``, ``mathematics``, ``teaching``, ``demonstration``…) and
a provenance ``kind``. :func:`facets_for` reads those, in a fixed order, and says
which shelf the thing belongs on — and *how it knew* (``derived_by``), so a
mis-shelving is traceable rather than mysterious.

**Warrant.** A facet is a **reader's convenience, not a fact about the graph**. It
is revisable, low-warrant, and nothing in the calculus may depend on it: Dau's rules
do not care what shelf a graph sits on, and the correspondence check never consults
one. Facets live beside the corpus exactly as annotations do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

# --------------------------------------------------------------------------- #
# The two axes                                                                 #
# --------------------------------------------------------------------------- #

SUBJECTS: Dict[str, str] = {
    "mathematics": "Number, order, proof-about-proof — mathematics grown on the sheet.",
    "logic": "The graphs themselves: rules, patterns, classic derivations.",
    "ontology": "Imported vocabularies — what a domain says exists.",
    "modality": "Possibility and necessity, read off a branching history "
                "(no Gamma mark: docs/MODALITY_WITHOUT_GAMMA.md).",
    "second-order": "Graphs about graphs — the frontier Peirce called Gamma.",
    "dialogue": "A model changing through argument — how M is revised.",
    "worlds": "Domain boards: places to play the game in.",
    "live-run": "Artifacts of a live run against the world.",
}

PURPOSES: Dict[str, str] = {
    "teach": "Built to be climbed — read it in order.",
    "prove": "A derivation: premisses to conclusion by the rules.",
    "demonstrate": "Shows a capability or a distinction working.",
    "reference": "A cited example from the literature.",
    "play": "A board for the Endoporeutic Game.",
    "model": "A model of a domain, revisable.",
}

UNFILED = "unfiled"


@dataclass(frozen=True)
class Facets:
    """Where a UoD sits on the reader's two axes, and how that was decided.

    **Both axes are multi-valued**, deliberately. Cohen's forcing conditions are
    *mathematics* AND a *modality* demonstration; the arithmetic ladder both teaches
    and proves. Forcing one shelf per thing is precisely the mistake that made
    ``domain_model`` a junk drawer — do not repeat it one level down.

    ``derived_by`` names the evidence (``tag:…`` / ``kind:…`` / ``category:…``) so a
    wrong shelf is *traceable*. Empty tuples mean **unfiled** — a real answer, and a
    visible gap is better than a silent default."""

    uod_id: str
    subjects: tuple = ()
    purposes: tuple = ()
    derived_by: tuple = ()

    @property
    def unfiled(self) -> bool:
        return not self.subjects or not self.purposes

    def to_dict(self) -> dict:
        return {
            "uod_id": self.uod_id,
            "subjects": list(self.subjects),
            "purposes": list(self.purposes),
            "derived_by": list(self.derived_by),
        }


# --------------------------------------------------------------------------- #
# Derivation — tags first, then provenance kind, then category                 #
# --------------------------------------------------------------------------- #

# A tag that decides a subject outright.
_SUBJECT_BY_TAG = {
    "mathematics": "mathematics",
    "ontology": "ontology",
    "t-box": "ontology",
    "modality": "modality",
    # NOTE ON "GAMMA" — a homonym, deliberately NOT mapped here.
    # In Arisbe's settled vocabulary, modality is carried WITHOUT Gamma
    # (docs/MODALITY_WITHOUT_GAMMA.md), and "Gamma" now names the SECOND-ORDER
    # frontier (docs/SECOND_ORDER_FRONTIER.md) — graphs about graphs. Peirce's
    # *historical* Gamma attempts at modality are a different thing, and the corpus
    # tags them `peirce-gamma` so the two never collide (charter P2: one word, one
    # way). A future second-order UoD would be tagged `second-order`.
    "second-order": "second-order",
    "model-revision": "dialogue",
    "liveness": "dialogue",
    "dialogue": "dialogue",
    "agon-board": "worlds",
    "forcing": "mathematics",
    "live-run": "live-run",
}

_PURPOSE_BY_TAG = {
    "teaching": "teach",
    "pedagogy": "teach",
    "demonstration": "demonstrate",
    "cited": "reference",
}

# Provenance ``kind`` → subject (the ontology cluster is exactly this).
_SUBJECT_BY_KIND = {"ontology": "ontology"}

# The producer's axis still tells us something when nothing else does.
_PURPOSE_BY_CATEGORY = {
    "theorem_proof": "prove",
    "literature_example": "reference",
    "canonical_pattern": "reference",
    "epg_session": "play",
    "practice_session": "teach",
    "domain_model": "model",
}


def facets_for(
    uod_id: str,
    *,
    tags: Iterable[str] = (),
    category: Optional[str] = None,
    kind: Optional[str] = None,
) -> Facets:
    """Which shelves does this UoD belong on? Deterministic, evidence-ordered.

    Tags are the most specific evidence (an author said so); provenance ``kind``
    next; the producer-side ``category`` last. Nothing here guesses from a name."""
    tagset = {t.strip().lower() for t in tags if t}
    subjects, purposes, why = [], [], []

    # Every matching tag counts — a thing may sit on more than one shelf.
    for tag, subj in _SUBJECT_BY_TAG.items():
        if tag in tagset and subj not in subjects:
            subjects.append(subj)
            why.append(f"tag:{tag}")
    if kind in _SUBJECT_BY_KIND and _SUBJECT_BY_KIND[kind] not in subjects:
        subjects.append(_SUBJECT_BY_KIND[kind])
        why.append(f"kind:{kind}")
    if not subjects and category in ("theorem_proof", "literature_example",
                                     "canonical_pattern"):
        # A proof, or a cited EG example, IS logic — not a guess; it is what those
        # categories mean.
        subjects.append("logic")
        why.append(f"category:{category}")

    for tag, purp in _PURPOSE_BY_TAG.items():
        if tag in tagset and purp not in purposes:
            purposes.append(purp)
            why.append(f"tag:{tag}")
    if not purposes and category in _PURPOSE_BY_CATEGORY:
        purposes.append(_PURPOSE_BY_CATEGORY[category])
        why.append(f"category:{category}")
    if "worlds" in subjects and "play" not in purposes:
        purposes.append("play")            # a board is for playing, whatever else

    return Facets(uod_id=uod_id, subjects=tuple(subjects), purposes=tuple(purposes),
                  derived_by=tuple(why))


def facets_for_entry(entry: dict, *, tags: Iterable[str] = (),
                     kind: Optional[str] = None) -> Facets:
    """:func:`facets_for` over a ``tomos/index.json`` entry.

    Note the index's own ``tags`` field is empty for every UoD in the corpus — the
    authored tags live in each UoD's ``annotations.json``. So the caller passes
    them (:func:`facets_for_corpus` does the reading)."""
    return facets_for(
        entry.get("uod_id", "?"),
        tags=tags or entry.get("tags") or (),
        category=entry.get("category"),
        kind=kind,
    )


def _read_json(path) -> object:
    import json
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _uod_dir(tomos_root, entry: dict) -> str:
    """A UoD's directory, resolved against THIS clone's tomos root. The index
    entry's ``path`` must be honored — the corpus is NOT all under
    ``universes/`` (the 15 literature examples live in ``literature/``) — but
    it is stored tomos-root-relative now (a legacy absolute entry from another
    machine is re-rooted by its trailing ``<category>/<uod_id>`` components).
    Falls back to ``universes/<id>`` when path is absent."""
    import os
    path = entry.get("path")
    if path:
        p = path if os.path.isabs(path) else os.path.join(str(tomos_root), path)
        if os.path.isdir(p):
            return p
        parts = os.path.normpath(path).split(os.sep)
        if len(parts) >= 2:
            rerooted = os.path.join(str(tomos_root), parts[-2], parts[-1])
            if os.path.isdir(rerooted):
                return rerooted
    return os.path.join(str(tomos_root), "universes", entry.get("uod_id", ""))


# Public name for other modules (the web routes) that need the same resolution.
uod_dir = _uod_dir


def tags_of(tomos_root, uod_id_or_entry) -> List[str]:
    """The authored tags of a UoD — read from its ``annotations.json`` (where they
    actually live; the index's ``tags`` field is empty corpus-wide)."""
    import os
    entry = (uod_id_or_entry if isinstance(uod_id_or_entry, dict)
             else {"uod_id": uod_id_or_entry})
    data = _read_json(os.path.join(_uod_dir(tomos_root, entry), "annotations.json"))
    items = data if isinstance(data, list) else (data or {}).get("annotations", [])
    out = set()
    for a in items or []:
        for t in (a.get("tags") or []):
            out.add(t)
    return sorted(out)


def kind_of(tomos_root, uod_id_or_entry) -> Optional[str]:
    """The provenance ``kind`` (``ontology`` / ``proof`` / ``domain_model`` / …)."""
    import os
    entry = (uod_id_or_entry if isinstance(uod_id_or_entry, dict)
             else {"uod_id": uod_id_or_entry})
    data = _read_json(os.path.join(_uod_dir(tomos_root, entry), "provenance.json"))
    return (data or {}).get("kind") if isinstance(data, dict) else None


def facets_for_corpus(tomos_root, entries: Sequence[dict]) -> List[Facets]:
    """Shelve a whole corpus: read each UoD's authored tags + provenance kind, then
    derive. Deterministic; nothing is written."""
    out = []
    for e in entries:
        uid = e.get("uod_id")
        if not uid:
            continue
        out.append(facets_for_entry(e, tags=tags_of(tomos_root, e),
                                    kind=kind_of(tomos_root, e)))
    return out


def group_by_subject(facets: Sequence[Facets]) -> Dict[str, List[str]]:
    """subject → the UoDs on that shelf (a UoD may appear on several)."""
    out: Dict[str, List[str]] = {}
    for f in facets:
        for s in (f.subjects or (UNFILED,)):
            out.setdefault(s, []).append(f.uod_id)
    return {k: sorted(v) for k, v in sorted(out.items())}


def group_by_purpose(facets: Sequence[Facets]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for f in facets:
        for p in (f.purposes or (UNFILED,)):
            out.setdefault(p, []).append(f.uod_id)
    return {k: sorted(v) for k, v in sorted(out.items())}


def unfiled(facets: Sequence[Facets]) -> List[str]:
    """The honest gap: UoDs no rule could shelve. Never silently defaulted — a
    growing list here says the tag vocabulary needs a word."""
    return sorted(f.uod_id for f in facets if f.unfiled)


__all__ = [
    "SUBJECTS", "PURPOSES", "UNFILED", "Facets",
    "facets_for", "facets_for_entry", "facets_for_corpus", "tags_of", "kind_of",
    "group_by_subject", "group_by_purpose", "unfiled",
]
