"""
Import routes — admit an external linear form into the corpus.

The doorway *into* the corpus that read-only Organon implies.  An import
is **admitted at low warrant** (docs/MANIFEST_AND_MEANING.md): parsed
(comprehended), attested for §3.3 correspondence, bibliographically
attributed, never asserted as true.

Endpoints (prefix ``/import``):
  * ``GET  /import``                 — the import page
  * ``GET  /import/citation-types``  — the bibliographic form spec (data-driven)
  * ``POST /import/check``           — parse + round-trip + §3.3, no persistence
  * ``POST /import/format-citation`` — live-preview a formatted citation
  * ``POST /import/admit``           — create a low-warrant LITERATURE_EXAMPLE UoD
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter
from fastapi.responses import FileResponse

from web_api.models.api_models import (
    ApiResponse,
    FormatCitationRequest,
    ImportAdmitRequest,
    ImportCheckRequest,
)
from web_api.services import bibliography, import_service

from correspondence_attestation import CorrespondenceViolation
from tomos_service import TomosService


router = APIRouter(prefix="/import")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")
VIEWER_DIR = Path(__file__).parent.parent.parent / "web_viewer"

_tomos_service: Optional[TomosService] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def import_index():
    """Serve the Import page."""
    return FileResponse(str(VIEWER_DIR / "import.html"))


@router.get("/citation-types")
async def citation_types():
    """The bibliographic form spec — types and per-type fields (data-driven)."""
    return ApiResponse(success=True, data=bibliography.CITATION_TYPES)


@router.post("/check")
async def check(request: ImportCheckRequest):
    """Inspect a linear form: grammar, round-trip integrity, §3.3.  No write."""
    try:
        result = import_service.check(request.text, request.notation)
        return ApiResponse(success=True, data=result)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "CHECK_ERROR", "message": str(exc), "type": type(exc).__name__},
        )


@router.post("/format-citation")
async def format_citation(request: FormatCitationRequest):
    """Live-preview the formatted citation string for a structured record."""
    try:
        formatted = bibliography.format_citation(request.record)
        authors = bibliography.authors_list(request.record)
        return ApiResponse(success=True, data={"formatted": formatted, "authors": authors})
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "FORMAT_ERROR", "message": str(exc)},
        )


@router.post("/admit")
async def admit(request: ImportAdmitRequest):
    """Admit the linear form into the corpus as a low-warrant import."""
    try:
        result = import_service.admit(
            text=request.text,
            notation=request.notation,
            bibliography_record=request.bibliography or {},
            uod_id=request.uod_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            tomos=_get_tomos(),
        )
        return ApiResponse(success=True, data=result)
    except import_service.ImportError_ as exc:
        return ApiResponse(
            success=False,
            error={"code": "IMPORT_ERROR", "message": str(exc)},
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
            error={"code": "ADMIT_ERROR", "message": str(exc), "type": type(exc).__name__},
        )
