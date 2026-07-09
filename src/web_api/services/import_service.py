"""
Import service — admit an external linear form into the corpus.

This is the doorway *into* the corpus that the read-only Organon implies.
Per the philosophical floor (docs/MANIFEST_AND_MEANING.md), an import is
**admitted at low warrant**: comprehended (it parses into our vocabulary),
attested for **correspondence** (§3.3 — the chord, the picture/proposition
identity), bibliographically **attributed** (the trace of the un-hosted
dialogue it came from), and *never asserted as true*.  We attest only what
we can — well-formedness and correspondence — and manufacture nothing we
cannot, least of all truth.  No logical/semantic (Z3) check runs here:
truth is not ours to confer at admission.

Two operations:

  * ``check`` — parse, run **round-trip integrity** (so a transcription
    typo surfaces) and the **§3.3** render check; persists nothing.
  * ``admit`` — build a standalone ``LITERATURE_EXAMPLE`` UoD at low
    warrant, attribute it, and save (``save_uod`` fires §3.3 at the
    corpus boundary; a violation aborts cleanly).  The structured
    bibliographic record is persisted beside it.

Touches no protected module: parsing/generation are public, and the
bibliography sidecar lives in the (unprotected) tomos service.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from cgif_generator_dau import generate_cgif
from cgif_parser_dau import parse_cgif
from clif_generator_dau import generate_clif
from clif_parser_dau import parse_clif
from correspondence_attestation import CorrespondenceViolation
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from tomos_service import TomosService
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)

from web_api.services import bibliography
from web_api.services.layout_service import generate_layout, layout_dto_to_dict
from web_api.services.linear_forms import linear_forms


# Parser / generator per notation.  Mirrors the linear_forms registry.
_PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}
_GENERATORS = {"egif": generate_egif, "cgif": generate_cgif, "clif": generate_clif}

# Ontology file formats → (label, importer). Each importer returns a
# domain_model_importer.ImportResult carrying the EGI + the construct-level
# skip-report (``warnings``) — partial translation, never silently dropped.
_ONTOLOGY_FORMATS = {
    "owl": "OWL 2 functional syntax (.ofn)",
    "rdf-turtle": "RDF (Turtle)",
    "rdf-xml": "RDF/XML",
    "clif": "Common Logic (CLIF / SUO-KIF-style)",
}

# Element count (V+E+Cut) beyond which ELK layout is super-linear to draw
# (docs: a ~250-cut taxonomy is ~74 s). Above WARN we still admit but flag it;
# above CAP we refuse an *interactive* import (it would hang the §3.3 attest at
# save) and point to the CLI / structure view — the honest layout-at-scale limit.
_ONTOLOGY_SCALE_WARN = 80
_ONTOLOGY_SCALE_CAP = 220


class ImportError_(Exception):
    """A recoverable import problem (bad notation, duplicate id, …)."""


def _import_ontology(text: str, fmt: str):
    """Run the format-appropriate importer → ImportResult (egi + skip-report)."""
    from domain_model_importer import from_clif_text, from_owl_text, from_rdf_text
    fmt = (fmt or "owl").lower().strip()
    if fmt == "owl":
        return from_owl_text(text or "")
    if fmt == "rdf-turtle":
        return from_rdf_text(text or "", "turtle")
    if fmt == "rdf-xml":
        return from_rdf_text(text or "", "xml")
    if fmt == "clif":
        return from_clif_text(text or "")
    raise ImportError_(
        f"Unknown ontology format '{fmt}'. Valid: {sorted(_ONTOLOGY_FORMATS)}.")


def _egi_size(egi) -> int:
    return len(egi.V) + len(egi.E) + len(egi.Cut)


def check_ontology(text: str, fmt: str) -> Dict[str, Any]:
    """Inspect an ontology file (OWL/RDF/CLIF) without persisting anything.

    Returns the EGI summary + import counts, the **construct-level skip-report**
    (what could not be translated, by construct — never silently dropped), a
    **scale assessment**, and — only when the graph is small enough to draw
    interactively — a §3.3-attested drawing preview. A large ontology is correct
    but super-linear to draw, so the preview is skipped with a scale warning
    rather than hanging the request.
    """
    fmt = (fmt or "owl").lower().strip()
    result: Dict[str, Any] = {
        "fmt": fmt, "format_label": _ONTOLOGY_FORMATS.get(fmt, fmt),
        "parsed": {"ok": False, "error": None},
        "counts": None, "egi_summary": None,
        "skipped_constructs": [], "scale": None,
        "svg": None, "layout_dto": None,
        "correspondence": {"ok": False, "error": None},
        "ok": False,
    }
    try:
        imp = _import_ontology(text, fmt)
    except ImportError_:
        raise
    except Exception as exc:
        result["parsed"]["error"] = f"{type(exc).__name__}: {exc}"
        return result
    egi = imp.egi
    result["parsed"]["ok"] = True
    result["counts"] = {"axioms": imp.num_axioms, "types": imp.num_types,
                        "relations": imp.num_relations, "individuals": imp.num_individuals}
    result["egi_summary"] = {"vertex_count": len(egi.V), "edge_count": len(egi.E),
                             "cut_count": len(egi.Cut)}
    result["skipped_constructs"] = list(imp.warnings or [])
    size = _egi_size(egi)
    if size > _ONTOLOGY_SCALE_CAP:
        result["scale"] = {"size": size, "level": "too_large",
                           "message": (f"{size} elements — too large to draw and §3.3-attest "
                                       "interactively. Import via the CLI (tools/build_ontologies) "
                                       "or browse it in the coordinate-free Structure view.")}
    elif size > _ONTOLOGY_SCALE_WARN:
        result["scale"] = {"size": size, "level": "large",
                           "message": (f"{size} elements — large; drawing may take a while "
                                       "(layout is super-linear).")}
    else:
        result["scale"] = {"size": size, "level": "ok", "message": ""}

    # Draw + attest only when it is small enough to be interactive.
    if size <= _ONTOLOGY_SCALE_CAP:
        try:
            dto, svg = generate_layout(egi)
            result["svg"] = svg
            result["layout_dto"] = layout_dto_to_dict(dto)
            result["correspondence"]["ok"] = True
        except CorrespondenceViolation as exc:
            result["correspondence"]["error"] = str(exc)
        except Exception as exc:
            result["correspondence"]["error"] = f"{type(exc).__name__}: {exc}"
    result["ok"] = result["parsed"]["ok"] and (
        size > _ONTOLOGY_SCALE_CAP or result["correspondence"]["ok"])
    return result


def admit_ontology(
    *,
    text: str,
    fmt: str,
    uod_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    tomos: TomosService,
) -> Dict[str, Any]:
    """Admit an ontology file into the corpus as a low-warrant ``kind=ontology`` UoD.

    Translates OWL/RDF/CLIF → EGI, builds a ``DOMAIN_MODEL`` UoD shelved as an
    **ontology** (so Organon facets it and Agon lists it as a model M), persists
    the **construct-level skip-report** in its provenance, and saves it (``save_uod``
    fires §3.3 at the boundary). Refuses a graph too large to draw/attest
    interactively (it would hang the attest) — the honest layout-at-scale limit.
    """
    fmt = (fmt or "owl").lower().strip()
    uod_id = (uod_id or "").strip()
    if not uod_id:
        raise ImportError_("A uod_id is required to admit an import.")
    if tomos.uod_exists(uod_id):
        raise ImportError_(
            f"UoD '{uod_id}' already exists; import never overwrites. "
            f"Choose a different id.")
    try:
        imp = _import_ontology(text, fmt)
    except ImportError_:
        raise
    except Exception as exc:
        raise ImportError_(f"Could not import {fmt.upper()}: {exc}")

    egi = imp.egi
    size = _egi_size(egi)
    if size > _ONTOLOGY_SCALE_CAP:
        raise ImportError_(
            f"This ontology is too large to draw and §3.3-attest interactively "
            f"({size} elements > {_ONTOLOGY_SCALE_CAP}). Import it via the CLI "
            f"(tools/build_ontologies) where it is admitted as a spine, or reduce it.")

    from provenance import KIND_ONTOLOGY, Provenance

    now = datetime.now(timezone.utc)
    tag_set = set(tags or [])
    tag_set.update({"import", "warrant:low", "kind:ontology", "source:ontology"})
    metadata = UoDMetadata(
        uod_id=uod_id,
        uod_type=UoDType.STANDALONE,
        name=name or uod_id,
        description=description or "",
        category=UoDCategory.DOMAIN_MODEL,
        created=now,
        last_modified=now,
        authors=[],
        tags=tag_set,
        source_citation="",
        natural_language_summary=description or None,
    )
    uod = UniverseOfDiscourse(metadata=metadata, current_egi=egi)

    # §3.3 fires inside save_uod BEFORE any disk write.
    tomos.save_uod(uod)

    # Provenance: shelve as kind=ontology (the browse/facet + M-picker dimension)
    # and persist the construct-level skip-report so the partial translation is
    # visible in Organon, not only at the CLI. The skip-report rides in the raw
    # provenance dict (the detail route passes it through un-rehydrated).
    prov = Provenance(kind=KIND_ONTOLOGY).to_dict()
    prov["skipped_constructs"] = list(imp.warnings or [])
    prov["import_format"] = _ONTOLOGY_FORMATS.get(fmt, fmt)
    tomos.save_provenance(uod, prov)

    return {
        "uod_id": uod_id,
        "kind": "ontology",
        "counts": {"axioms": imp.num_axioms, "types": imp.num_types,
                   "relations": imp.num_relations, "individuals": imp.num_individuals},
        "skipped_constructs": list(imp.warnings or []),
        "egi_summary": {"vertex_count": len(egi.V), "edge_count": len(egi.E),
                        "cut_count": len(egi.Cut)},
    }


def _canonical(egi) -> str:
    """Canonical EGIF for structural comparison (round-trip stability)."""
    return generate_egif(egi)


def check(text: str, notation: str) -> Dict[str, Any]:
    """Inspect a linear form without persisting anything.

    Returns a dict describing each stage:

        {
          "notation": "egif",
          "parsed": {"ok": bool, "error": str|None},
          "roundtrip": {"ok": bool, "stable": bool, "regenerated": str|None,
                        "error": str|None},
          "correspondence": {"ok": bool, "error": str|None},   # §3.3
          "egi_summary": {...} | None,
          "svg": str | None,
          "layout_dto": {...} | None,
          "linear_forms": {...} | None,     # all notations, for cross-check
          "ok": bool,                       # parsed AND §3.3 held
        }

    Grammatical correctness is the parse stage; "imperfection" surfaces as
    round-trip instability (parsed into a graph that does not regenerate
    to itself) and as a §3.3 correspondence failure.
    """
    notation = (notation or "egif").lower().strip()
    parser = _PARSERS.get(notation)
    generator = _GENERATORS.get(notation)
    result: Dict[str, Any] = {
        "notation": notation,
        "parsed": {"ok": False, "error": None},
        "roundtrip": {"ok": False, "stable": False, "regenerated": None, "error": None},
        "correspondence": {"ok": False, "error": None},
        "egi_summary": None,
        "svg": None,
        "layout_dto": None,
        "linear_forms": None,
        "ok": False,
    }
    if parser is None:
        result["parsed"]["error"] = (
            f"Unknown notation '{notation}'. Valid: {sorted(_PARSERS)}."
        )
        return result

    # --- grammatical correctness ---
    try:
        egi = parser(text or "")
    except Exception as exc:
        result["parsed"]["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["parsed"]["ok"] = True
    result["egi_summary"] = {
        "vertex_count": len(egi.V),
        "edge_count": len(egi.E),
        "cut_count": len(egi.Cut),
    }

    # --- round-trip integrity (surfaces transcription error) ---
    try:
        regenerated = generator(egi)
        egi2 = parser(regenerated)
        result["roundtrip"]["regenerated"] = regenerated
        result["roundtrip"]["stable"] = _canonical(egi) == _canonical(egi2)
        result["roundtrip"]["ok"] = True
    except Exception as exc:
        result["roundtrip"]["error"] = f"{type(exc).__name__}: {exc}"

    # --- §3.3 correspondence (render the drawing, attest) ---
    try:
        dto, svg = generate_layout(egi)
        result["svg"] = svg
        result["layout_dto"] = layout_dto_to_dict(dto)
        result["correspondence"]["ok"] = True
    except CorrespondenceViolation as exc:
        result["correspondence"]["error"] = str(exc)
    except Exception as exc:
        result["correspondence"]["error"] = f"{type(exc).__name__}: {exc}"

    # --- all notations, for cross-notation cross-check ---
    result["linear_forms"] = linear_forms(egi)

    result["ok"] = result["parsed"]["ok"] and result["correspondence"]["ok"]
    return result


def admit(
    *,
    text: str,
    notation: str,
    bibliography_record: Dict[str, Any],
    uod_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    tomos: TomosService,
) -> Dict[str, Any]:
    """Admit a linear form into the corpus as a low-warrant import.

    Builds a standalone ``LITERATURE_EXAMPLE`` UoD, attributes it from the
    bibliographic record, and saves it (``save_uod`` fires §3.3 before any
    disk write).  The structured bibliographic record is persisted beside
    the UoD.

    Raises ``ImportError_`` for bad notation / missing required citation
    fields / duplicate id, and propagates ``CorrespondenceViolation`` from
    the corpus boundary unchanged.
    """
    notation = (notation or "egif").lower().strip()
    parser = _PARSERS.get(notation)
    if parser is None:
        raise ImportError_(f"Unknown notation '{notation}'. Valid: {sorted(_PARSERS)}.")

    uod_id = (uod_id or "").strip()
    if not uod_id:
        raise ImportError_("A uod_id is required to admit an import.")
    if tomos.uod_exists(uod_id):
        raise ImportError_(
            f"UoD '{uod_id}' already exists; import never overwrites. "
            f"Choose a different id."
        )

    # Bibliographic attribution — required fields per type.
    try:
        bibliography.validate(bibliography_record)
    except bibliography.BibliographyError as exc:
        raise ImportError_(str(exc))

    try:
        egi = parser(text or "")
    except Exception as exc:
        raise ImportError_(f"Could not parse {notation.upper()}: {exc}")

    formatted = bibliography.format_citation(bibliography_record)
    authors = bibliography.authors_list(bibliography_record)

    now = datetime.now(timezone.utc)
    tag_set = set(tags or [])
    # Carry the low-warrant status and source kind in tags (warrant is a
    # gradient; an import enters low and rises only by withstanding
    # challenge — it is not a first-class field yet, by design).
    tag_set.update({
        "import",
        "warrant:low",
        f"source:{bibliography_record.get('type', 'document')}",
    })

    metadata = UoDMetadata(
        uod_id=uod_id,
        uod_type=UoDType.STANDALONE,
        name=name or (bibliography_record.get("title") or uod_id),
        description=description or "",
        category=UoDCategory.LITERATURE_EXAMPLE,
        created=now,
        last_modified=now,
        authors=authors,
        tags=tag_set,
        source_citation=formatted,
        natural_language_summary=description or None,
    )
    uod = UniverseOfDiscourse(metadata=metadata, current_egi=egi)

    # §3.3 fires inside save_uod BEFORE any disk write — a violation aborts
    # cleanly (nothing half-written).
    tomos.save_uod(uod)
    # Persist the structured bibliographic record beside the UoD.
    tomos.save_bibliography(uod, bibliography_record, formatted)

    return {
        "uod_id": uod_id,
        "source_citation": formatted,
        "authors": authors,
        "egi_summary": {
            "vertex_count": len(egi.V),
            "edge_count": len(egi.E),
            "cut_count": len(egi.Cut),
        },
    }
