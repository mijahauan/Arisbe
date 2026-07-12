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


# Curated display names for the shipped styles — what the mode dropdowns show
# (charter P2: the same choice reads the same everywhere).  An unlisted style
# falls back to its spec's style_name, so a new style appears automatically.
_DISPLAY: dict = {
    "dau-compliant@1.0": "Dau — mathematical",
    "peirce-authentic@1.0": "Peirce — handwritten",
    "sowa-compliant@1.0": "Sowa — conceptual graph",
}


@router.get("")
@router.get("/")
async def list_styles():
    """List the loadable styles with display names, default first.

    Entries whose spec cannot be loaded or that carry no ``style_name``
    (schema files, stray fixtures in the styles directory) are skipped —
    the dropdowns this feeds must never offer a style that cannot draw.
    """
    try:
        default = None
        try:
            default = getattr(load_default_style(), "style_name", None)
        except Exception:
            pass

        items = []
        for name in list_available_styles():
            try:
                spec = load_style(name)
            except Exception:
                continue  # unloadable — never offer it
            label = getattr(spec, "style_name", None)
            if not label:
                continue  # a schema/fixture file, not a style
            raw = getattr(spec, "raw_style_data", {}) or {}
            description = raw.get("description", "") or raw.get("global", {}).get("description", "")
            items.append(
                {
                    "name": name,
                    "label": label,
                    "display": _DISPLAY.get(name, label),
                    "description": description,
                    "is_default": label == default,
                }
            )
        items.sort(key=lambda e: (not e["is_default"], e["display"].lower()))
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "STYLES_LIST_ERROR", "message": str(exc)},
        )
