"""
Export service — take an EGI out of the corpus to the outside world.

Completes the outer arc (world → Organon → world): an EGI is exported in
a chosen **style** (Dau / Peirce / Sowa — the projection's visual
realization) and a chosen **format**.

Formats:
  * linear  — EGIF / CGIF / CLIF text (the proposition, in any notation)
  * svg     — the styled drawing (vector, web-native)
  * tikz    — portable TikZ/LaTeX (compiles anywhere; LyX-includable)
  * png/pdf — rasterised/vector via ``rsvg-convert`` (runtime-guarded)

Each format is produced defensively; PNG/PDF report cleanly if the
external rasteriser is absent rather than crashing.  (The authentic
Peirce ``egpeirce.sty`` LaTeX path is a separate, structural exporter.)
"""

import base64
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from cgif_generator_dau import generate_cgif
from clif_generator_dau import generate_clif
from egif_generator_dau import generate_egif

from web_api.services.layout_service import generate_layout
from web_api.services.tikz_export import export_tikz
from peirce_latex import (
    export_peirce_latex, export_peirce_chain_document, _tex_escape,
)


class ExportError(Exception):
    """A recoverable export problem (unknown format, missing tool, …)."""


# Ordered format registry.  ``requires`` names an external binary that must
# be present (None = always available).  Adding a format is a row here.
_FORMATS: List[Dict[str, Any]] = [
    {"format": "egif", "label": "EGIF (linear)", "ext": "egif", "media_type": "text/plain", "binary": False, "requires": None},
    {"format": "cgif", "label": "CGIF (linear)", "ext": "cgif", "media_type": "text/plain", "binary": False, "requires": None},
    {"format": "clif", "label": "CLIF (linear)", "ext": "clif", "media_type": "text/plain", "binary": False, "requires": None},
    {"format": "svg", "label": "SVG (styled drawing)", "ext": "svg", "media_type": "image/svg+xml", "binary": False, "requires": None},
    {"format": "tikz", "label": "TikZ / LaTeX", "ext": "tex", "media_type": "text/x-tex", "binary": False, "requires": None},
    {"format": "peirce-tikz", "label": "Authentic Peirce (LaTeX/TikZ)", "ext": "tex", "media_type": "text/x-tex", "binary": False, "requires": None},
    {"format": "png", "label": "PNG (raster)", "ext": "png", "media_type": "image/png", "binary": True, "requires": "rsvg-convert"},
    {"format": "pdf", "label": "PDF (vector)", "ext": "pdf", "media_type": "application/pdf", "binary": True, "requires": "rsvg-convert"},
]

_FORMATS_BY_KEY = {f["format"]: f for f in _FORMATS}

_LINEAR = {"egif": generate_egif, "cgif": generate_cgif, "clif": generate_clif}


def _tool_available(name: Optional[str]) -> bool:
    return name is None or shutil.which(name) is not None


def available_formats() -> List[Dict[str, Any]]:
    """The format registry, annotated with runtime availability."""
    out = []
    for f in _FORMATS:
        out.append({
            "format": f["format"], "label": f["label"], "ext": f["ext"],
            "binary": f["binary"], "requires": f["requires"],
            "available": _tool_available(f["requires"]),
        })
    return out


def _rsvg(svg: str, target: str) -> bytes:
    """Convert SVG to PNG/PDF bytes via rsvg-convert (raises if unavailable)."""
    exe = shutil.which("rsvg-convert")
    if exe is None:
        raise ExportError(
            f"Cannot export {target.upper()}: 'rsvg-convert' is not installed."
        )
    try:
        proc = subprocess.run(
            [exe, "-f", target],
            input=svg.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
    except Exception as exc:  # pragma: no cover - subprocess plumbing
        raise ExportError(f"{target.upper()} conversion failed: {exc}")
    if proc.returncode != 0:
        raise ExportError(
            f"{target.upper()} conversion failed: "
            f"{proc.stderr.decode('utf-8', 'replace')[:200]}"
        )
    return proc.stdout


def export_egi(
    egi,
    fmt: str,
    *,
    style_name: Optional[str] = None,
    engine: str = "elk",
    standalone: bool = True,
    basename: str = "export",
    deltas: Optional[list] = None,
    previous_layout=None,
    scroll_glyph: bool = False,
) -> Dict[str, Any]:
    """Export *egi* in *fmt* using the same *style_name* + layout *engine* the
    viewer is showing — "export what you see".

    ``deltas`` / ``previous_layout`` thread the viewer's **regime-3
    presentation adjustments** (the logic-indifferent ``move_vertex`` /
    ``move_cut`` / ``reshape_cut`` nudges) straight into ``generate_layout``, so
    a hand-tuned arrangement is published as drawn — "export what you *adjusted*
    to see".  This is the Peirce Edition Project's transcribe-then-tune path: a
    scholar matches Peirce's page, then exports.  §3.3 still attests every
    (EGI, DTO) pair inside ``generate_layout`` — deltas are logic-indifferent,
    so attestation holds by construction.

    Returns a JSON-able dict::

        {"format", "filename", "media_type", "is_binary",
         "content": <text> | None, "content_base64": <b64> | None}

    Text formats fill ``content``; binary formats (png/pdf) fill
    ``content_base64``.  Raises ``ExportError`` for unknown formats or a
    missing external tool, and propagates ``CorrespondenceViolation`` from
    the styled render unchanged (§3.3 still guards every drawing exported).
    """
    spec = _FORMATS_BY_KEY.get(fmt)
    if spec is None:
        raise ExportError(f"Unknown format '{fmt}'. Valid: {sorted(_FORMATS_BY_KEY)}.")

    filename = f"{basename}.{spec['ext']}"
    result = {
        "format": fmt, "filename": filename, "media_type": spec["media_type"],
        "is_binary": spec["binary"], "content": None, "content_base64": None,
    }

    if fmt in _LINEAR:
        result["content"] = _LINEAR[fmt](egi)
        return result

    # The authentic-Peirce path defaults to the oval style so the layout grows
    # cut boxes that contain their contents as inscribed ellipses (a rounded-rect
    # DTO would clip an oval drawn over it).
    if fmt == "peirce-tikz" and not style_name:
        style_name = "peirce-authentic@1.0"

    def _layout():
        return generate_layout(
            egi, previous_layout=previous_layout, style_name=style_name,
            deltas=deltas, engine=engine,
        )

    if fmt == "svg":
        _dto, svg = _layout()
        result["content"] = svg
        return result

    if fmt == "tikz":
        dto, _svg = _layout()
        result["content"] = export_tikz(dto, egi, standalone=standalone, style=dto.style)
        return result

    if fmt == "peirce-tikz":
        dto, _svg = _layout()
        result["content"] = export_peirce_latex(
            dto, egi, standalone=standalone, style=dto.style, scroll_glyph=scroll_glyph)
        return result

    if fmt in ("png", "pdf"):
        # §3.3 fires here (styled render) before the external conversion.
        _dto, svg = _layout()
        result["content_base64"] = base64.b64encode(_rsvg(svg, fmt)).decode("ascii")
        return result

    raise ExportError(f"Unhandled format '{fmt}'.")  # pragma: no cover


def export_peirce_chain(
    chain,
    *,
    title: Optional[str] = None,
    style_name: Optional[str] = None,
    engine: str = "elk",
    basename: str = "chain",
) -> Dict[str, Any]:
    """Export a transformation *chain* (a ``tomos_service.TransformationChain``)
    as a single authentic-Peirce LaTeX document — one figure per step, captioned
    by the rule that produced it (the Peirce-Edition "worked chain").

    Each state is laid out through the ordinary §3.3-attested path (so every
    drawn step corresponds to its EGI), rendered with ``export_peirce_latex``,
    and assembled by ``export_peirce_chain_document``.  Returns the same
    JSON-able envelope as ``export_egi``.
    """
    if style_name is None:
        style_name = "peirce-authentic@1.0"

    figures = []
    egi0 = chain.states[chain.initial_state_id]
    dto0, _svg = generate_layout(egi0, style_name=style_name, engine=engine)  # attests §3.3
    figures.append((export_peirce_latex(dto0, egi0, standalone=False),
                    "\\textbf{Initial graph}"))

    for k, step in enumerate(chain.steps, start=1):
        egi = chain.states.get(step.to_state_id)
        if egi is None:  # pragma: no cover - a chain with a dangling state id
            continue
        dto, _svg = generate_layout(egi, style_name=style_name, engine=engine)
        body = export_peirce_latex(dto, egi, standalone=False)
        params = step.parameters or {}
        desc = params.get("description") or step.user_annotation or ""
        label = params.get("peirce_label")
        head = f"Step {k}: {_tex_escape(step.rule_name)}"
        if label:
            head += f" ({_tex_escape(str(label))})"
        caption = f"\\textbf{{{head}}}"
        if desc:
            caption += f" --- {_tex_escape(desc)}"
        figures.append((body, caption))

    doc = export_peirce_chain_document(figures, title=title)
    return {
        "format": "peirce-chain", "filename": f"{basename}.tex",
        "media_type": "text/x-tex", "is_binary": False,
        "content": doc, "content_base64": None,
    }
