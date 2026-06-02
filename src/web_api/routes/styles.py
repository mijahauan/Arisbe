"""
Styles route — the available visual styles for drawing an EGI.

A style is the *visual realization* layer of the projection: the same
coordinate-free ``NaturalLayout`` rendered in Dau's, Peirce's, or Sowa's
idiom (see ``docs/MANIFEST_AND_MEANING.md`` — three manifests, one
meaning, each §3.3-attested).  This mode-independent endpoint lets any
client (export, a view-style selector, Ergasterion) offer the choice.
"""

import sys
from pathlib import Path

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import ApiResponse

from style_loader import list_available_styles, load_default_style, load_style


router = APIRouter(prefix="/styles")


@router.get("")
@router.get("/")
async def list_styles():
    """List the available styles with their display name and description."""
    try:
        default = None
        try:
            default = getattr(load_default_style(), "style_name", None)
        except Exception:
            pass

        items = []
        for name in list_available_styles():
            entry = {"name": name, "label": name, "description": ""}
            try:
                spec = load_style(name)
                entry["label"] = getattr(spec, "style_name", name)
                raw = getattr(spec, "raw_style_data", {}) or {}
                entry["description"] = raw.get("description", "") or raw.get("global", {}).get("description", "")
            except Exception:
                pass
            entry["is_default"] = (entry["label"] == default)
            items.append(entry)
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "STYLES_LIST_ERROR", "message": str(exc)},
        )
