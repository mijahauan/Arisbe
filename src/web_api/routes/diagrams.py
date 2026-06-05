"""
Diagram and area API endpoints.
"""

import sys
from pathlib import Path

# Ensure src/ is on path
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from web_api.models.api_models import ApiResponse, AreaAtPointRequest
from web_api.services.session_manager import get_session_manager
from web_api.services.layout_service import generate_layout, layout_dto_to_dict

from tomos_service import TomosService

router = APIRouter(prefix="/api")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")

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


@router.get("/diagrams")
async def list_diagrams():
    """List all available diagrams from the tomos corpus."""
    try:
        tomos = _get_tomos()
        raw = tomos.list_uods()
        diagrams = []
        for entry in raw:
            diagrams.append(
                {
                    "id": entry.get("uod_id", ""),
                    "name": entry.get("name", "Untitled"),
                    "category": entry.get("category", ""),
                    "description": entry.get("description", None),
                }
            )
        return ApiResponse(success=True, data=diagrams)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_ERROR", "message": str(exc)},
        )


@router.get("/diagram/{diagram_id}")
async def load_diagram(diagram_id: str):
    """Load a diagram, generate layout, create session."""
    try:
        tomos = _get_tomos()
        uod = tomos.load_uod(diagram_id)
        egi = uod.current_egi

        layout_dto, svg = generate_layout(egi)
        layout_dict = layout_dto_to_dict(layout_dto)

        session_manager = get_session_manager()
        session_id = session_manager.create_session(egi, layout_dto, diagram_id)

        metadata = {}
        if uod.metadata:
            metadata["name"] = getattr(uod.metadata, "name", uod.name if hasattr(uod, "name") else "")
            metadata["description"] = getattr(uod.metadata, "description", None)

        return ApiResponse(
            success=True,
            data={
                "session_id": session_id,
                "svg": svg,
                "layout_dto": layout_dict,
                "egi_summary": _egi_summary(egi),
                "metadata": metadata,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LOAD_ERROR", "message": str(exc)},
        )


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Return current session state."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": f"Session {session_id} not found"},
            )

        from web_api.services.layout_service import layout_dto_to_dict
        from simple_svg_renderer import SimpleSVGRenderer
        from egif_generator_dau import EGIFGenerator

        egi = session.current_egi
        dto = session.current_layout_dto

        try:
            egif = EGIFGenerator().generate(egi)
        except Exception:
            egif = ""

        renderer = SimpleSVGRenderer()
        svg = renderer.render_to_svg(dto, egif=egif, egi=egi)

        return ApiResponse(
            success=True,
            data={
                "session_id": session_id,
                "svg": svg,
                "layout_dto": layout_dto_to_dict(dto),
                "egi_summary": _egi_summary(egi),
                "can_undo": session.can_undo(),
                "can_redo": session.can_redo(),
                "history_index": session.history_index,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "SESSION_ERROR", "message": str(exc)},
        )


@router.get("/areas/{session_id}")
async def get_areas(session_id: str):
    """Return all areas with polarity and bounds."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": f"Session {session_id} not found"},
            )

        egi = session.current_egi
        dto = session.current_layout_dto

        areas = []
        # Include sheet and all cuts as areas
        all_area_ids = list(egi.area.keys())

        for area_id in all_area_ids:
            try:
                polarity, depth = egi.area_polarity(area_id)
                polarity_str = polarity.value
            except Exception:
                polarity_str = "positive"
                depth = 0

            # Get bounds from cut_bounds (sheet won't have bounds typically)
            bounds = None
            if area_id in dto.cut_bounds:
                b = dto.cut_bounds[area_id]
                bounds = {
                    "min_x": b.min_x,
                    "min_y": b.min_y,
                    "max_x": b.max_x,
                    "max_y": b.max_y,
                }

            areas.append(
                {
                    "area_id": area_id,
                    "polarity": polarity_str,
                    "depth": depth,
                    "bounds": bounds,
                }
            )

        return ApiResponse(success=True, data=areas)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "AREAS_ERROR", "message": str(exc)},
        )


@router.post("/area/at-point")
async def area_at_point(request: AreaAtPointRequest):
    """Find the deepest area containing the given (x, y) point."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(request.session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            )

        egi = session.current_egi
        dto = session.current_layout_dto
        x, y = request.x, request.y

        # Find deepest cut containing the point
        best_area_id = egi.sheet
        best_depth = 0

        for cut_id, bounds in dto.cut_bounds.items():
            if cut_id == dto.sheet_id:
                continue
            if bounds.min_x <= x <= bounds.max_x and bounds.min_y <= y <= bounds.max_y:
                try:
                    _, depth = egi.area_polarity(cut_id)
                except Exception:
                    depth = 1
                if depth > best_depth:
                    best_depth = depth
                    best_area_id = cut_id

        try:
            polarity, depth = egi.area_polarity(best_area_id)
            polarity_str = polarity.value
        except Exception:
            polarity_str = "positive"
            depth = 0

        return ApiResponse(
            success=True,
            data={
                "area_id": best_area_id,
                "polarity": polarity_str,
                "depth": depth,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "AREA_AT_POINT_ERROR", "message": str(exc)},
        )
