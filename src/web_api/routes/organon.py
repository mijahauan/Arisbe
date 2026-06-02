"""
Organon (archive) routes.

Organon is the read-only mode in the Organon / Ergasterion / Agon trio
(`docs/PRODUCT_VISION.md`, `CLAUDE.md`).  It surfaces the tomos corpus
as a browsable archive — list every UoD, open one, see its drawing.
No editing, no transformation UI, no session state.

Both backend boundaries that this route depends on already attest §3.3
correspondence: ``TomosService.load_uod`` (load boundary, see
`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md` §6) and
``layout_service.generate_layout`` (render boundary, same §6).  A single
GET ``/organon/uods/{uod_id}`` therefore fires both hooks; either
refusal propagates as a 500 with a CorrespondenceViolation payload.
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

from web_api.models.api_models import ApiResponse
from web_api.services.layout_service import generate_layout, layout_dto_to_dict
from web_api.services.linear_forms import linear_forms

from tomos_service import TomosService

router = APIRouter(prefix="/organon")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")
VIEWER_DIR = Path(__file__).parent.parent.parent / "web_viewer"

_tomos_service: Optional[TomosService] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


def _egi_summary(egi) -> dict:
    return {
        "vertex_count": len(egi.V),
        "edge_count": len(egi.E),
        "cut_count": len(egi.Cut),
    }


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def organon_index():
    """Serve the Organon HTML viewer at /organon."""
    return FileResponse(str(VIEWER_DIR / "organon.html"))


@router.get("/uods")
async def list_uods():
    """List all UoDs in the tomos corpus.

    Returns the same lightweight metadata that ``TomosService.list_uods``
    exposes — enough for the browser to render a list and open any
    entry.  Read-only; no session is created.
    """
    try:
        tomos = _get_tomos()
        entries = tomos.list_uods()
        items = [
            {
                "uod_id": e.get("uod_id", ""),
                "name": e.get("name", "Untitled"),
                "category": e.get("category", ""),
                "uod_type": e.get("uod_type", ""),
                "is_static": e.get("is_static", True),
                "is_dynamic": e.get("is_dynamic", False),
                "created": e.get("created", ""),
                "last_modified": e.get("last_modified", ""),
                "authors": e.get("authors", []),
                "tags": e.get("tags", []),
                "total_states": e.get("total_states", 1),
                "total_transformations": e.get("total_transformations", 0),
            }
            for e in entries
        ]
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_ERROR", "message": str(exc)},
        )


@router.get("/uods/{uod_id}")
async def get_uod(uod_id: str):
    """Return the UoD's drawing + summary metadata.

    Pipeline:
        TomosService.load_uod(uod_id)
          ↳ attests §3.3 at the load boundary
        layout_service.generate_layout(egi)
          ↳ attests §3.3 at the render boundary
        return (svg, layout_dto, metadata)

    Both boundary attestations fire on every call; a drift in either
    raises ``CorrespondenceViolation`` and surfaces here as a 500-style
    error payload.  No session is created — Organon is read-only.
    """
    try:
        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id)
        if uod is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "UOD_NOT_FOUND",
                    "message": f"UoD '{uod_id}' not found in tomos",
                },
            )

        egi = uod.current_egi
        if egi is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "EMPTY_UOD",
                    "message": f"UoD '{uod_id}' has no current EGI to draw",
                },
            )

        layout_dto, svg = generate_layout(egi)
        layout_dict = layout_dto_to_dict(layout_dto)

        metadata = {
            "uod_id": uod.uod_id,
            "name": uod.name,
            "description": getattr(uod.metadata, "description", "") or "",
            "category": uod.category.value,
            "created": uod.metadata.created.isoformat(),
            "last_modified": uod.metadata.last_modified.isoformat(),
            "authors": list(uod.metadata.authors),
            "tags": list(uod.metadata.tags),
            "source_citation": getattr(uod.metadata, "source_citation", None),
        }

        return ApiResponse(
            success=True,
            data={
                "uod_id": uod_id,
                "svg": svg,
                "layout_dto": layout_dict,
                "egi_summary": _egi_summary(egi),
                "linear_forms": linear_forms(egi),
                "metadata": metadata,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "LOAD_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )
