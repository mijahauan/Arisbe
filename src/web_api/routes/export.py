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

from web_api.models.api_models import ApiResponse, ExportRequest
from web_api.services import export_service

from correspondence_attestation import CorrespondenceViolation
from egif_parser_dau import parse_egif
from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from tomos_service import TomosService


router = APIRouter(prefix="/export")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")

_tomos_service: Optional[TomosService] = None
_PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


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

        artifact = export_service.export_egi(
            egi, request.format, style_name=request.style_name,
            standalone=request.standalone, basename=basename,
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
