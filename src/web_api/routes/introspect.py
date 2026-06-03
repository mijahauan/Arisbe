"""
Introspection route — area/polarity + content for a graph, for
selection-driven clients.

The Ergasterion dogfood (memory ``project-ergasterion-dogfood-findings``,
#1) found that to select elements for a rule a client must know which
*area* each element lives in, that area's *polarity*, and — to name an
element by meaning rather than by ephemeral id — its *content* (relation
name, vertex label, incidence). The session and game payloads already
carry an ``introspection`` block; this route exposes the same
``egi_introspection`` for an **arbitrary** graph (a corpus UoD or an
inline linear form), so a client can introspect before opening a session
and the capability is reachable on its own.

Like ``/rules``, it is **mode-independent** and **read-only**: it derives
from the EGI, mutates nothing, and makes no §3.3 claim (correspondence is
attested at the render/corpus boundaries, not here).
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import ApiResponse, IntrospectRequest
from web_api.services.introspection import egi_introspection

from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from egif_parser_dau import parse_egif
from tomos_service import TomosService


router = APIRouter(prefix="/introspect")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")
_PARSERS = {"egif": parse_egif, "cgif": parse_cgif, "clif": parse_clif}

_tomos_service: Optional[TomosService] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


@router.post("")
@router.post("/")
async def introspect(request: IntrospectRequest):
    """Area/polarity + content introspection for a graph.

    Source is a corpus UoD (``uod_id``) or an inline linear form
    (``text`` + ``notation``). Returns the ``egi_introspection`` block:
    every area with its polarity/depth, and every element with its area,
    polarity, and content (edges carry ``relation`` / ``arity`` /
    ``incident_vertices``; vertices carry ``label``)."""
    try:
        if request.uod_id:
            uod = _get_tomos().load_uod(request.uod_id)
            if uod is None or uod.current_egi is None:
                return ApiResponse(
                    success=False,
                    error={"code": "UOD_NOT_FOUND",
                           "message": f"UoD '{request.uod_id}' not found or empty."},
                )
            egi = uod.current_egi
        elif request.text is not None:
            parser = _PARSERS.get((request.notation or "egif").lower())
            if parser is None:
                return ApiResponse(
                    success=False,
                    error={"code": "BAD_NOTATION",
                           "message": f"Unknown notation '{request.notation}'. "
                                      f"Valid: {sorted(_PARSERS)}."},
                )
            try:
                egi = parser(request.text)
            except Exception as exc:
                return ApiResponse(
                    success=False,
                    error={"code": "PARSE_ERROR", "message": str(exc)},
                )
        else:
            return ApiResponse(
                success=False,
                error={"code": "NO_SOURCE",
                       "message": "Provide a uod_id or inline text."},
            )

        return ApiResponse(success=True, data=egi_introspection(egi))

    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "INTROSPECT_FAILED",
                   "message": str(exc), "type": type(exc).__name__},
        )
