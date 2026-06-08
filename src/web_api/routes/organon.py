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
from annotations import (
    SCOPE_UOD,
    SCOPE_CHAIN,
    annotations_from_list,
    annotations_to_list,
    for_scope,
    for_state,
    for_step,
)

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


def _browse_facets(entry: dict) -> dict:
    """Cheap browse facets for a list row — the provenance ``kind`` + a
    cited/authored flag + the description + tags — read straight from the
    ``provenance.json`` / ``uod.meta.json`` side-files.

    Deliberately does NOT call ``load_uod`` (that would parse + §3.3-attest every
    corpus graph on every list request); only the small JSON side-files are read.
    """
    import json
    facets = {"kind": None, "cited": False, "description": "", "extra_tags": []}
    path = entry.get("path")
    if not path:
        return facets
    base = Path(path)
    try:
        prov = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
        facets["kind"] = prov.get("kind")
        facets["cited"] = bool(prov.get("theorem_source"))
    except Exception:
        pass
    try:
        meta = json.loads((base / "uod.meta.json").read_text(encoding="utf-8"))
        facets["description"] = meta.get("description") or ""
        facets["extra_tags"] = list(meta.get("tags") or [])
    except Exception:
        pass
    return facets


@router.get("/uods")
async def list_uods():
    """List all UoDs in the tomos corpus, enriched with browse facets.

    Beyond the lightweight index metadata, each row carries the provenance
    ``kind`` (the shelving dimension), a ``cited`` flag, and the ``description``
    — enough for the browser to group, facet, sort, and search without a detail
    fetch per item.  Read-only; no session, no attestation (facets come from the
    cheap side-files, see ``_browse_facets``).
    """
    try:
        tomos = _get_tomos()
        entries = tomos.list_uods()
        items = []
        for e in entries:
            f = _browse_facets(e)
            items.append({
                "uod_id": e.get("uod_id", ""),
                "name": e.get("name", "Untitled"),
                "category": e.get("category", ""),
                "uod_type": e.get("uod_type", ""),
                "is_static": e.get("is_static", True),
                "is_dynamic": e.get("is_dynamic", False),
                "created": e.get("created", ""),
                "last_modified": e.get("last_modified", ""),
                "authors": e.get("authors", []),
                "tags": e.get("tags", []) + [t for t in f["extra_tags"] if t not in e.get("tags", [])],
                "total_states": e.get("total_states", 1),
                "total_transformations": e.get("total_transformations", 0),
                "kind": f["kind"],
                "cited": f["cited"],
                "description": f["description"],
            })
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_ERROR", "message": str(exc)},
        )


@router.get("/uods/{uod_id}")
async def get_uod(uod_id: str, style: Optional[str] = None, engine: str = "elk"):
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

    ``engine`` selects the layout projection — ``"elk"`` (default) or
    ``"tension"`` (the ligature-first reading); both are §3.3-attested at the
    render boundary, and ``tension`` falls back to ELK on any graph it can't yet
    lay out.  A style-only/engine-only reprojection of an attested graph is free
    (§3.3 attests *correspondence*, not truth), so the archive may show it.
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

        # Style is a *projection* choice: view any form in any style directly,
        # without the export path.  §3.3 attests every styled render.
        layout_dto, svg = generate_layout(egi, style_name=style, engine=engine)
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
                # Bibliographic provenance for imported UoDs (None for
                # non-imports) — the trace of the un-hosted dialogue the
                # linear form came from.
                "bibliography": tomos.load_bibliography(uod_id),
                # Provenance bundle — typed theorem / EG-derivation / calculus
                # source layers + per-layer warrant + transcribed-vs-authored
                # flag (None for items without one).  Outside §3.3.
                "provenance": tomos.load_provenance(uod_id),
                # Annotation layer — marginalia *about* this UoD, all scopes
                # (the client filters by scope).  Outside §3.3; [] when none.
                "annotations": tomos.load_annotations(uod_id),
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


@router.get("/uods/{uod_id}/chain")
async def get_uod_chain(uod_id: str, style: Optional[str] = None,
                        engine: str = "elk"):
    """Return the UoD's transformation chain as an ordered list of *frames*.

    A UoD is *fundamentally diachronic* — an evolving reasoning episode, not
    a single picture (`docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`).  The
    seeded exemplars (``theorem_praeclarum``, ``beta_modus_ponens``,
    ``beta_converse_mp``) persist a real ``TransformationChain``; this route
    surfaces it so the archive can *play it through* — frame 0 the base state,
    then one frame per rule application, each carrying the resulting drawing
    and linear form so picture and proposition are watched co-evolving.

    Each frame's drawing is produced by ``generate_layout``, so §3.3 is
    attested at the render boundary for *every* state in the chain, not just
    the current one.  Read-only; no session.  ``has_chain`` is False (with an
    empty ``frames``) for the synchronic majority of the corpus that carries
    no ``history/``.
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

        chain = tomos.load_chain(uod_id)
        if chain is None:
            return ApiResponse(
                success=True,
                data={"uod_id": uod_id, "has_chain": False, "frames": []},
            )

        # Annotation layer (marginalia, outside §3.3).  ``annotation`` below
        # remains the step's *baked-in* user_annotation (authored rationale);
        # ``layer`` carries the *additive* external notes for this frame —
        # step-scoped (by step_id) plus element-scoped (anchored in this state).
        layer = annotations_from_list(tomos.load_annotations(uod_id))

        def _frame(index, kind, egi, state_id, rule=None, annotation=None,
                   step_id=None):
            _dto, svg = generate_layout(egi, style_name=style, engine=engine)  # attests §3.3 per state
            frame_anns = list(for_state(layer, state_id))
            if step_id is not None:
                frame_anns = list(for_step(layer, step_id)) + frame_anns
            return {
                "index": index,
                "kind": kind,             # "base" | "step"
                "rule": rule,
                "annotation": annotation,  # "<peirce label>: <note>" (baked-in)
                "step_id": step_id,
                "state_id": state_id,
                "annotations": annotations_to_list(frame_anns),  # additive layer
                "svg": svg,
                "egi_summary": _egi_summary(egi),
                "linear_forms": linear_forms(egi),
            }

        frames = [
            _frame(0, "base", chain.states[chain.initial_state_id],
                   chain.initial_state_id)
        ]
        for i, step in enumerate(chain.steps, start=1):
            frames.append(
                _frame(
                    i,
                    "step",
                    chain.states[step.to_state_id],
                    step.to_state_id,
                    rule=step.rule_name,
                    annotation=step.user_annotation,
                    step_id=step.step_id,
                )
            )

        return ApiResponse(
            success=True,
            data={
                "uod_id": uod_id,
                "has_chain": True,
                "step_count": len(chain.steps),
                # Whole-derivation and whole-universe notes (not tied to a frame).
                "chain_annotations": annotations_to_list(for_scope(layer, SCOPE_CHAIN)),
                "uod_annotations": annotations_to_list(for_scope(layer, SCOPE_UOD)),
                "frames": frames,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "CHAIN_LOAD_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )
