"""
Provenance bundle — typed, multi-layer attribution for a worked proof.

A single ``source_citation`` cannot hold the truth about an imported proof,
because **provenance splits into layers that do not share a source** (see
``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §2.5):

    theorem_source   — where the *proposition* comes from
                       (Peirce 1885; Aristotle; Leibniz)
    proof_source     — where *this EG derivation* comes from: either a
                       published proof we transcribed (Sowa, for the
                       Praeclarum), or one *authored here* (Peirce's Law,
                       Barbara — original to Arisbe, NOT a transcription)
    method_sources   — the *calculus* the proof is conducted in
                       (Peirce MS 514; Sowa's rules; Dau LNAI 2892; Roberts)

Flattening these into one citation would misattribute an *authored* derivation
to a *historical* source — exactly the un-attested truth-claim the floor forbids
(``docs/MANIFEST_AND_MEANING.md``).  So the bundle keeps the layers distinct and
marks the derivation **transcribed vs. authored-here**.

**Warrant has two objects, as provenance has two layers.** A known classical
theorem has high external standing — but Arisbe *attests correspondence, never
truth*, so a UoD enters the corpus at **low** warrant regardless, carried by an
*authored, machine-checkable, not-yet-Agon-tested* derivation that is also low.
Warrant is therefore a small per-layer record here, not a tag and not a
``UoDMetadata`` field (that module is protected, and per-layer warrant wants
structure a flat field can't give).  It is a gradient: it rises by withstanding
Agon and can fall (``docs/CHAIN_OF_SEMIOSIS.md``).

Each citation is a CSL-compatible dict (the same field names the ``bibliography``
service collects), rendered here by a small self-contained author-date formatter
(``provenance`` stays dependency-light — like the annotation layer it imports no
web/layout code); an optional ``bibkey`` on a record cross-references
``docs/references/eg_proofs.bib``.  Persistence is
``tomos_service.save_provenance`` / ``load_provenance`` (a ``provenance.json``
side-file), and ``save_uod_with_chain`` carries it so a worked proof imports as a
low-warrant chain (the doorway-union, R1).  Like the annotation layer and the
bibliography record, the bundle is **outside §3.3** — it describes the source,
it is not a sign in the graph.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _brief(record: Dict[str, Any]) -> str:
    """A compact author-date face of a CSL-compatible record.

    Self-contained (no dependency on the ``bibliography`` service, which lives
    under ``web_api`` — provenance must be importable by the build tools and
    ``tomos_service`` without pulling the web layer).  Omits absent fields.
    """
    if not record:
        return ""
    author = str(record.get("author") or "").strip()
    year = str(record.get("year") or "").strip()
    title = str(record.get("title") or "").strip()
    container = str(record.get("container_title") or "").strip()
    head = " ".join(x for x in [author, f"({year})" if year else ""] if x).strip()
    return ". ".join(b for b in [head, title, container] if b)


# How a derivation came to be in the corpus.
DERIVATION_TRANSCRIBED = "transcribed"   # copied from a published EG proof
DERIVATION_AUTHORED = "authored"         # constructed here (original to Arisbe)
_DERIVATION_KINDS = (DERIVATION_TRANSCRIBED, DERIVATION_AUTHORED)

# Warrant gradient (low is the import/authored floor; tested = withstood Agon).
WARRANT_BLANK = "blank"      # the sheet itself — inviolable
WARRANT_LOW = "low"          # admitted/authored, attested for correspondence, not asserted true
WARRANT_TESTED = "tested"    # withstood dialogical challenge (Agon) — future
_WARRANT_LEVELS = (WARRANT_BLANK, WARRANT_LOW, WARRANT_TESTED)

_DEFAULT_WARRANT = {"theorem": WARRANT_LOW, "derivation": WARRANT_LOW}


@dataclass(frozen=True)
class Provenance:
    """The typed, multi-layer source record for a worked proof.

    ``theorem_source`` / ``method_sources`` are CSL-compatible records (or
    empty).  ``proof_source`` is a small discriminated record:

        {"kind": "transcribed", "citation": {<CSL>}}        # e.g. Sowa's proof
        {"kind": "authored", "author": "…", "system": "…"}  # original to Arisbe

    ``warrant`` is a per-layer level map (``{"theorem": …, "derivation": …}``).
    """

    theorem_source: Dict[str, Any] = field(default_factory=dict)
    proof_source: Dict[str, Any] = field(default_factory=dict)
    method_sources: List[Dict[str, Any]] = field(default_factory=list)
    warrant: Dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_WARRANT))

    def validate(self) -> None:
        kind = self.proof_source.get("kind")
        if kind is not None and kind not in _DERIVATION_KINDS:
            raise ValueError(
                f"Provenance: proof_source.kind must be one of {_DERIVATION_KINDS}, "
                f"got {kind!r}"
            )
        if kind == DERIVATION_TRANSCRIBED and not self.proof_source.get("citation"):
            raise ValueError(
                "Provenance: a transcribed proof_source needs a 'citation' record"
            )
        if kind == DERIVATION_AUTHORED and not self.proof_source.get("author"):
            raise ValueError(
                "Provenance: an authored proof_source needs an 'author'"
            )
        for layer, level in self.warrant.items():
            if level not in _WARRANT_LEVELS:
                raise ValueError(
                    f"Provenance: warrant[{layer!r}] must be one of "
                    f"{_WARRANT_LEVELS}, got {level!r}"
                )

    def is_authored_here(self) -> bool:
        """True when *this derivation* was constructed in Arisbe (not transcribed)."""
        return self.proof_source.get("kind") == DERIVATION_AUTHORED

    def formatted(self) -> Dict[str, Any]:
        """Human-readable faces of each layer, for display alongside the raw bundle."""
        theorem = _brief(self.theorem_source)
        if self.proof_source.get("kind") == DERIVATION_TRANSCRIBED:
            proof = _brief(self.proof_source.get("citation", {}))
        elif self.proof_source.get("kind") == DERIVATION_AUTHORED:
            who = self.proof_source.get("author", "Arisbe")
            system = self.proof_source.get("system")
            proof = f"Original derivation by {who}" + (f" ({system})" if system else "")
        else:
            proof = ""
        methods = [_brief(m) for m in self.method_sources if m]
        return {"theorem": theorem, "proof": proof, "methods": methods}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theorem_source": dict(self.theorem_source),
            "proof_source": dict(self.proof_source),
            "method_sources": [dict(m) for m in self.method_sources],
            "warrant": dict(self.warrant),
            "formatted": self.formatted(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Provenance":
        warrant = dict(_DEFAULT_WARRANT)
        warrant.update(d.get("warrant") or {})
        return cls(
            theorem_source=dict(d.get("theorem_source") or {}),
            proof_source=dict(d.get("proof_source") or {}),
            method_sources=[dict(m) for m in (d.get("method_sources") or [])],
            warrant=warrant,
        )


def authored_proof(author: str, *, system: Optional[str] = None) -> Dict[str, Any]:
    """A ``proof_source`` for a derivation constructed in Arisbe (not transcribed)."""
    rec: Dict[str, Any] = {"kind": DERIVATION_AUTHORED, "author": author}
    if system:
        rec["system"] = system
    return rec


def transcribed_proof(citation: Dict[str, Any]) -> Dict[str, Any]:
    """A ``proof_source`` for a derivation copied from a published EG proof."""
    return {"kind": DERIVATION_TRANSCRIBED, "citation": dict(citation)}


def make_provenance(
    *,
    theorem_source: Optional[Dict[str, Any]] = None,
    proof_source: Optional[Dict[str, Any]] = None,
    method_sources: Optional[List[Dict[str, Any]]] = None,
    warrant: Optional[Dict[str, str]] = None,
) -> Provenance:
    """Build and validate a provenance bundle, defaulting warrant to low/low."""
    w = dict(_DEFAULT_WARRANT)
    w.update(warrant or {})
    prov = Provenance(
        theorem_source=dict(theorem_source or {}),
        proof_source=dict(proof_source or {}),
        method_sources=[dict(m) for m in (method_sources or [])],
        warrant=w,
    )
    prov.validate()
    return prov


__all__ = [
    "Provenance",
    "DERIVATION_TRANSCRIBED",
    "DERIVATION_AUTHORED",
    "WARRANT_BLANK",
    "WARRANT_LOW",
    "WARRANT_TESTED",
    "authored_proof",
    "transcribed_proof",
    "make_provenance",
]
