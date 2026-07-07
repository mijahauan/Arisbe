"""
Export routes — take an EGI out of the corpus to the outside world.

The return leg of the outer arc (world → Organon → world). Given a source
(a corpus UoD or an inline linear form), a format, and a style, produce
the artifact. SVG / linear are always available; PNG / PDF require
``rsvg-convert`` (reported via ``/export/formats``).
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import (
    ApiResponse, ExportRequest, ExportChainRequest, ExportDocumentRequest,
)
from web_api.services import export_service

from correspondence_attestation import CorrespondenceViolation
from presentation_deltas import deltas_from_list
from egif_parser_dau import parse_egif
from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from tomos_service import TomosService
import scholarly_citation
from web_api.paths import TOMOS_PATH


router = APIRouter(prefix="/export")

_tomos_service: Optional[TomosService] = None
_PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


def _citation_for_uod(uod_id: str, uod=None) -> dict:
    """The scholarly citation bundle for a UoD — built from its provenance +
    bibliography + free-text source_citation (``scholarly_citation.citation_for``).
    Fabricates nothing: a sourceless graph reports ``has_source: false``."""
    tomos = _get_tomos()
    prov = tomos.load_provenance(uod_id)
    bib = tomos.load_bibliography(uod_id)
    name = None
    src = None
    if uod is not None:
        name = uod.name
        src = getattr(uod.metadata, "source_citation", None)
    return scholarly_citation.citation_for(
        provenance=prov, bibliography=bib, source_citation=src, name=name)


@router.get("/formats")
async def formats():
    """List export formats with runtime availability (PNG/PDF need rsvg)."""
    return ApiResponse(success=True, data=export_service.available_formats())


@router.post("")
@router.post("/")
async def do_export(request: ExportRequest):
    """Export an EGI (from a UoD or inline linear form) in a format + style."""
    try:
        # Resolve the source EGI + a sensible export basename.
        caption = None
        if request.uod_id:
            uod = _get_tomos().load_uod(request.uod_id)
            if uod is None or uod.current_egi is None:
                return ApiResponse(
                    success=False,
                    error={"code": "UOD_NOT_FOUND",
                           "message": f"UoD '{request.uod_id}' not found or empty."},
                )
            egi = uod.current_egi
            basename = request.uod_id
            # Scholarly attribution caption (authentic-Peirce export only).
            if request.cite and request.format == "peirce-tikz":
                caption = _citation_for_uod(request.uod_id, uod).get("citation")
        elif request.text is not None:
            parser = _PARSERS.get((request.notation or "egif").lower())
            if parser is None:
                return ApiResponse(
                    success=False,
                    error={"code": "BAD_NOTATION",
                           "message": f"Unknown notation '{request.notation}'."},
                )
            try:
                egi = parser(request.text)
            except Exception as exc:
                return ApiResponse(
                    success=False,
                    error={"code": "PARSE_ERROR", "message": str(exc)},
                )
            basename = "export"
        else:
            return ApiResponse(
                success=False,
                error={"code": "NO_SOURCE",
                       "message": "Provide a uod_id or inline text."},
            )

        # Regime-3 adjustments (optional) — replayed before drawing so the
        # export reflects a hand-tuned arrangement ("export what you adjusted").
        deltas = None
        if request.deltas:
            try:
                deltas = deltas_from_list(request.deltas)
            except Exception as exc:
                return ApiResponse(
                    success=False,
                    error={"code": "BAD_DELTAS", "message": str(exc)},
                )

        artifact = export_service.export_egi(
            egi, request.format, style_name=request.style_name,
            engine=request.engine, standalone=request.standalone, basename=basename,
            deltas=deltas, scroll_glyph=request.scroll_glyph, caption=caption,
        )
        return ApiResponse(success=True, data=artifact)

    except export_service.ExportError as exc:
        return ApiResponse(
            success=False,
            error={"code": "EXPORT_ERROR", "message": str(exc)},
        )
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "EXPORT_FAILED", "message": str(exc), "type": type(exc).__name__},
        )


@router.post("/chain")
@router.post("/chain/")
async def do_export_chain(request: ExportChainRequest):
    """Export a UoD's worked transformation chain as one authentic-Peirce LaTeX
    document — a reasoning episode in print, one figure per step."""
    try:
        chain = _get_tomos().load_chain(request.uod_id)
        if chain is None:
            return ApiResponse(
                success=False,
                error={"code": "CHAIN_NOT_FOUND",
                       "message": f"UoD '{request.uod_id}' has no worked chain."},
            )
        artifact = export_service.export_peirce_chain(
            chain, title=request.title, style_name=request.style_name,
            engine=request.engine, basename=f"{request.uod_id}-chain",
        )
        return ApiResponse(success=True, data=artifact)
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "EXPORT_FAILED", "message": str(exc), "type": type(exc).__name__},
        )


@router.get("/citation")
async def get_citation(uod_id: str):
    """The scholarly **citation** for a corpus UoD — a human author-date line plus
    a **BibTeX** entry, built from the UoD's provenance (``scholarly_citation``).

    Read-only; fabricates nothing — a graph with no recorded source reports
    ``has_source: false`` and an honest "reproduced with Arisbe" line. Feeds the
    "Cite" affordance in the export panel and the ``cite=true`` export caption."""
    try:
        uod = _get_tomos().load_uod(uod_id)
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found."})
        return ApiResponse(success=True, data=_citation_for_uod(uod_id, uod))
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "CITATION_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.post("/document")
@router.post("/document/")
async def do_export_document(request: ExportDocumentRequest):
    """Export **several corpus UoDs** as one authentic-Peirce LaTeX document — the
    scholar's appendix of figures (a batch). Each graph is a captioned figure
    (name + provenance citation when ``cite``); each layout is §3.3-attested."""
    try:
        if not request.uod_ids:
            return ApiResponse(success=False, error={
                "code": "NO_SOURCE", "message": "Provide at least one uod_id."})
        items = []
        missing = []
        tomos = _get_tomos()
        for uid in request.uod_ids:
            uod = tomos.load_uod(uid)
            if uod is None or uod.current_egi is None:
                missing.append(uid)
                continue
            citation = (_citation_for_uod(uid, uod).get("citation")
                        if request.cite else "")
            items.append((uod.current_egi, uod.name or uid, citation))
        if not items:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND",
                "message": f"No exportable UoDs among {request.uod_ids}."})
        artifact = export_service.export_peirce_document(
            items, title=request.title, style_name=request.style_name,
            engine=request.engine)
        artifact["missing"] = missing   # honestly name any skipped ids
        return ApiResponse(success=True, data=artifact)
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "EXPORT_FAILED", "message": str(exc), "type": type(exc).__name__},
        )
