"""
Organon (archive) routes.

Organon is the read-only mode in the Organon / Ergasterion / Agon trio
(`docs/VISION_AND_SCOPE.md`, `CLAUDE.md`).  It surfaces the tomos corpus
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
from web_api.services.layout_service import (
    generate_layout,
    generate_overview_layout,
    layout_dto_to_dict,
)
from web_api.services.linear_forms import linear_forms
from web_api.services.introspection import egi_introspection

from tomos_service import TomosService
from provenance import standing_of
from annotations import (
    SCOPE_UOD,
    SCOPE_CHAIN,
    annotations_from_list,
    annotations_to_list,
    for_scope,
    for_state,
    for_step,
)

from web_api.paths import TOMOS_PATH

router = APIRouter(prefix="/organon")

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
    facets = {"kind": None, "cited": False, "description": "", "extra_tags": [],
              "warrant": None, "has_chain": False}
    path = entry.get("path")
    if not path:
        return facets
    base = Path(path)
    try:
        prov = json.loads((base / "provenance.json").read_text(encoding="utf-8"))
        facets["kind"] = prov.get("kind")
        facets["cited"] = bool(prov.get("theorem_source"))
        facets["warrant"] = prov.get("warrant")
    except Exception:
        pass
    try:
        meta = json.loads((base / "uod.meta.json").read_text(encoding="utf-8"))
        facets["description"] = meta.get("description") or ""
        facets["extra_tags"] = list(meta.get("tags") or [])
    except Exception:
        pass
    # Cheap chain-existence (a file stat, no parse) — the "derived" signal.
    facets["has_chain"] = (base / "history" / "chain.jsonl").exists()
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
        from liveness import get_log
        tomos = _get_tomos()
        entries = tomos.list_uods()
        live = get_log(TOMOS_PATH).all()   # forward-facing usage status per UoD
        items = []
        for e in entries:
            f = _browse_facets(e)
            uid = e.get("uod_id", "")
            ls = live.get(uid)
            row_tags = e.get("tags", []) + [t for t in f["extra_tags"] if t not in e.get("tags", [])]
            standing = standing_of(
                warrant=f["warrant"], tags=row_tags,
                has_chain=f["has_chain"] or e.get("uod_type") == "historical",
            )
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
                "tags": row_tags,
                "total_states": e.get("total_states", 1),
                "total_transformations": e.get("total_transformations", 0),
                "kind": f["kind"],
                "cited": f["cited"],
                # Standing badge (posited / derived / withstood-Agon) — see standing_of.
                "standing": standing,
                "description": f["description"],
                # Forward-facing usage status (manifest floor #7): alive / dormant /
                # unconsulted / retired — for a liveness badge in the browser list.
                "liveness_status": ls.status if ls else "unconsulted",
                "consult_count": ls.count if ls else 0,
            })
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_ERROR", "message": str(exc)},
        )


@router.get("/uods/{uod_id}")
async def get_uod(uod_id: str, style: Optional[str] = None, engine: str = "elk",
                  lod: str = "full", expand: Optional[str] = None):
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

    ``lod`` selects the level of detail — ``"full"`` (default, the canonical
    §3.3 drawing) or ``"overview"`` (the navigation projection,
    docs/ADAPTIVE_SCOPE_VIEWER.md): collapse deep cuts into content-sized
    placeholders so a graph too large to draw whole can still be navigated.
    ``expand`` is a comma-separated list of cut ids the reader has drilled into
    (ancestors auto-included); absent ⇒ the auto-expand policy opens the top of
    the graph to a drawn-cut budget.  An overview is attested by the *weaker*
    ``attest_overview`` (visible part corresponds + placeholders faithfully
    summarize) — explicitly **not** a full §3.3 correspondence, and never a
    promotion source; the fully-expanded drawing stays §3.3-governed.  The
    response carries a ``collapsed`` map (placeholder cut id → badge) for the
    client's badges and expand affordances.
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

        # Overview (adaptive-scope navigation projection): collapse deep cuts
        # into placeholders so the Drawing renders graphs ELK can't draw whole.
        collapsed_map = None
        if lod == "overview":
            expand_ids = (
                [s for s in (expand.split(",") if expand else []) if s.strip()]
            ) or None
            layout_dto, svg, collapsed_map, _collapsed_ids = (
                generate_overview_layout(egi, expand=expand_ids, style_name=style)
            )
            layout_dict = layout_dto_to_dict(layout_dto)
            return ApiResponse(
                success=True,
                data={
                    "uod_id": uod_id,
                    "svg": svg,
                    "layout_dto": layout_dict,
                    "lod": "overview",
                    # Placeholder badges (cut id → {cuts, vertices, predicates,
                    # polarity, boundary_degree}) — *form*, never actuality.
                    "collapsed": collapsed_map,
                    "egi_summary": _egi_summary(egi),
                },
            )

        # Style is a *projection* choice: view any form in any style directly,
        # without the export path.  §3.3 attests every styled render.
        layout_dto, svg = generate_layout(egi, style_name=style, engine=engine)
        layout_dict = layout_dto_to_dict(layout_dto)

        # Forward-facing provenance (manifest floor #7): opening a UoD in Organon is
        # a *consultation* — it keeps the telling alive.  Outside §3.3; mutates only
        # the local usage log, never the UoD.  (overview/structure sub-routes don't
        # record — this is the canonical "open this UoD" event.)
        from liveness import get_log, KIND_VIEWED
        liveness = get_log(TOMOS_PATH).record(uod_id, KIND_VIEWED).to_dict()

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

        # Standing — what this graph's claim to a corpus place rests on (posited /
        # derived / withstood-Agon), a display projection over warrant + chain +
        # tags.  Its tooltip carries the "correspondence, not truth" non-claim, so
        # the badge is never read as a verdict.  Outside §3.3.
        prov = tomos.load_provenance(uod_id)
        standing = standing_of(
            warrant=(prov or {}).get("warrant"),
            tags=uod.metadata.tags,
            has_chain=tomos.has_chain(uod_id),
            is_blank=not (egi.V or egi.E or egi.Cut),
        )

        return ApiResponse(
            success=True,
            data={
                "uod_id": uod_id,
                "svg": svg,
                "layout_dto": layout_dict,
                "egi_summary": _egi_summary(egi),
                "linear_forms": linear_forms(egi),
                # Per-element area + polarity, from the SAME egi as the svg so
                # element ids match — the context reflex's enclosure walk
                # (which cuts enclose a clicked element). Outside §3.3.
                "introspection": egi_introspection(egi),
                # Bibliographic provenance for imported UoDs (None for
                # non-imports) — the trace of the un-hosted dialogue the
                # linear form came from.
                "bibliography": tomos.load_bibliography(uod_id),
                # Provenance bundle — typed theorem / EG-derivation / calculus
                # source layers + per-layer warrant + transcribed-vs-authored
                # flag (None for items without one).  Outside §3.3.
                "provenance": prov,
                # Standing badge (posited / derived / withstood-Agon) + the
                # correspondence-not-truth non-claim.  Outside §3.3.
                "standing": standing,
                # Annotation layer — marginalia *about* this UoD, all scopes
                # (the client filters by scope).  Outside §3.3; [] when none.
                "annotations": tomos.load_annotations(uod_id),
                # Forward-facing provenance: is this telling still alive in the
                # conversation? (consultations / last-consulted / desuetude status /
                # explicit retirement).  Outside §3.3; *form* of use, never a verdict.
                "liveness": liveness,
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


@router.get("/uods/{uod_id}/structure")
async def get_uod_structure(uod_id: str):
    """Return the UoD's **coordinate-free structure** (no drawing, no layout).

    The shared foundation for the adaptive-scope viewer projection spike
    (`docs/archived/ADAPTIVE_SCOPE_SPIKE.md`): the containment tree + polarity, recursive
    content counts, the predicate/vertex inventory, and per-ligature required
    crossing-sequences — the projection-independent facts every candidate
    projection (circle-packing / 3-D shells / hyperbolic) realizes differently.

    Read-only and **O(n), not geometric**: it loads the UoD with ``attest=False``
    (no §3.3 layout at the load boundary) and never runs a layout engine, so it
    returns even the 250-cut SUMO taxonomy — which chokes ELK at ~74 s — in
    milliseconds. Correspondence is unaffected: this returns *structure*, not a
    drawing, and mutates nothing.
    """
    try:
        from eg_structure import egi_structure
        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id, attest=False)
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found in tomos"})
        egi = uod.current_egi
        if egi is None:
            return ApiResponse(success=False, error={
                "code": "EMPTY_UOD", "message": f"UoD '{uod_id}' has no current EGI"})
        return ApiResponse(success=True, data={
            "uod_id": uod_id, "name": uod.name, "structure": egi_structure(egi)})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "STRUCTURE_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.post("/structure")
async def structure_from_egif(payload: dict):
    """Coordinate-free structure for a raw EGIF string (the ad-hoc sibling of
    ``/uods/{id}/structure``) — body ``{"egif": "..."}``. Read-only; no attestation
    (structure, not a drawing)."""
    try:
        from eg_structure import egi_structure
        from egif_parser_dau import parse_egif
        egif = (payload or {}).get("egif", "")
        if not egif.strip():
            return ApiResponse(success=False, error={
                "code": "EMPTY_EGIF", "message": "body must carry a non-empty 'egif'"})
        egi = parse_egif(egif)
        return ApiResponse(success=True, data={"structure": egi_structure(egi)})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "STRUCTURE_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.get("/uods/{uod_id}/liveness")
async def get_uod_liveness(uod_id: str):
    """The forward-facing usage record for a UoD **without** recording a consultation
    (manifest floor #7).  The detail route (``GET /uods/{id}``) records a view; this
    one only reads — for a badge refresh that must not itself keep the telling alive."""
    try:
        from liveness import get_log
        return ApiResponse(success=True,
                           data=get_log(TOMOS_PATH).summary(uod_id).to_dict())
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "LIVENESS_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.post("/uods/{uod_id}/liveness/retire")
async def retire_uod(uod_id: str, payload: Optional[dict] = None):
    """Explicitly **retire** (the deliberate second death) or **revive** a model —
    body ``{"retired": true|false}`` (default ``true``).

    Reversible by construction: nothing is asserted, nothing is deleted, the UoD and
    its drawing are untouched — only the local usage *stance* changes (manifest: "no
    irreversible commitment anywhere").  Re-consulting the UoD revives it on its own.
    """
    try:
        from liveness import get_log
        retired = True if payload is None else bool(payload.get("retired", True))
        summary = get_log(TOMOS_PATH).set_retired(uod_id, retired)
        return ApiResponse(success=True, data=summary.to_dict())
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "LIVENESS_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.get("/uods/{uod_id}/history-structure")
async def get_history_structure(uod_id: str, style: Optional[str] = None,
                                engine: str = "elk"):
    """Diachronic substrate for the adaptive-scope spike's *time-flow* lenses
    (storyboard + time-stack) — `docs/archived/ADAPTIVE_SCOPE_SPIKE.md`.

    Like ``/chain`` but each frame also carries its **geometric layout**
    (`layout_dto`, so a time-stack can draw survivor threads by matching element ids
    across frames) and a **per-step `legible_diff`** (`egi_diff` — what the rule
    changed, in EG vocabulary). Read-only; each frame's `generate_layout` attests §3.3.
    """
    try:
        from egi_diff import legible_diff
        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id)
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found"})
        chain = tomos.load_chain(uod_id)
        if chain is None:
            return ApiResponse(success=True,
                               data={"uod_id": uod_id, "has_chain": False, "frames": []})

        def _diff(prev_egi, cur_egi):
            rep = legible_diff(prev_egi, cur_egi)   # how cur (attempt) differs from prev (target)
            by = {}
            for f in rep.findings:
                by[f.kind] = by.get(f.kind, 0) + 1
            # extra = added by the rule; missing = erased by the rule
            bits = []
            if by.get("extra"): bits.append(f"+{by['extra']}")
            if by.get("missing"): bits.append(f"−{by['missing']}")
            for k in ("structure", "scope", "incidence", "order"):
                if by.get(k): bits.append(f"{k} {by[k]}")
            return {"summary": " · ".join(bits) or "no net change",
                    "findings": [{"kind": f.kind, "message": f.message,
                                  "subject": f.subject} for f in rep.findings]}

        def _frame(index, kind, egi, prev_egi, rule=None, annotation=None,
                   step_id=None, state_id=None):
            dto, svg = generate_layout(egi, style_name=style, engine=engine)
            return {
                "index": index, "kind": kind, "rule": rule,
                "annotation": annotation, "step_id": step_id, "state_id": state_id,
                "svg": svg, "layout": layout_dto_to_dict(dto),
                "egi_summary": _egi_summary(egi),
                "diff": _diff(prev_egi, egi) if prev_egi is not None else None,
            }

        base_egi = chain.states[chain.initial_state_id]
        frames = [_frame(0, "base", base_egi, None, state_id=chain.initial_state_id)]
        prev = base_egi
        for i, step in enumerate(chain.steps, start=1):
            cur = chain.states[step.to_state_id]
            frames.append(_frame(i, "step", cur, prev, rule=step.rule_name,
                                  annotation=step.user_annotation,
                                  step_id=step.step_id, state_id=step.to_state_id))
            prev = cur

        # The derivation **DAG** (the branch-aware view): one node per *unique*
        # state, one edge per step. A chain branches when two steps share a
        # from_state (a fork) and converges when two share a to_state (a merge) —
        # the topology the storyboard's single line cannot show. depth = longest
        # path from the initial state, so the lens can layer the nodes.
        edges = [{"from": s.from_state_id, "to": s.to_state_id, "rule": s.rule_name,
                  "branch_id": s.branch_id, "annotation": s.user_annotation,
                  "step_id": s.step_id,
                  "diff": _diff(chain.states[s.from_state_id], chain.states[s.to_state_id])}
                 for s in chain.steps]
        depth = {chain.initial_state_id: 0}
        for _ in range(len(chain.states)):            # relax to longest path (tiny DAG)
            for e in edges:
                if e["from"] in depth:
                    depth[e["to"]] = max(depth.get(e["to"], 0), depth[e["from"]] + 1)
        nodes = []
        for sid, egi in chain.states.items():
            dto, svg = generate_layout(egi, style_name=style, engine=engine)
            nodes.append({
                "id": sid, "depth": depth.get(sid, 0),
                "kind": "base" if sid == chain.initial_state_id else "state",
                "svg": svg, "layout": layout_dto_to_dict(dto),
                "egi_summary": _egi_summary(egi),
            })
        nodes.sort(key=lambda n: (n["depth"], n["id"]))
        from collections import Counter
        frm, to = Counter(e["from"] for e in edges), Counter(e["to"] for e in edges)
        branching = any(v > 1 for v in frm.values()) or any(v > 1 for v in to.values())

        return ApiResponse(success=True, data={
            "uod_id": uod_id, "name": uod.name, "has_chain": True,
            "step_count": len(chain.steps), "frames": frames,
            # The DAG view consumes this; `branching` lets the client offer the
            # linear lenses (storyboard / time-stack) only when the chain is a line.
            "dag": {"nodes": nodes, "edges": edges, "branching": branching,
                    "initial_state_id": chain.initial_state_id}})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "HISTORY_STRUCTURE_ERROR", "message": str(exc),
            "type": type(exc).__name__})


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

        from egi_diff import legible_diff

        def _step_diff(prev_egi, cur_egi):
            # What this step *changed*, in EG vocabulary — so the player can say
            # "this step: +… / −…" instead of only naming the rule (U10). Same
            # shape the derivation-DAG lens already shows on its edges.
            rep = legible_diff(prev_egi, cur_egi)
            by = {}
            for f in rep.findings:
                by[f.kind] = by.get(f.kind, 0) + 1
            bits = []
            if by.get("extra"):
                bits.append(f"+{by['extra']}")
            if by.get("missing"):
                bits.append(f"−{by['missing']}")
            for k in ("structure", "scope", "incidence", "order"):
                if by.get(k):
                    bits.append(f"{k} {by[k]}")
            return {"summary": " · ".join(bits) or "no net change"}

        def _frame(index, kind, egi, state_id, rule=None, annotation=None,
                   step_id=None, prev_egi=None):
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
                "diff": _step_diff(prev_egi, egi) if prev_egi is not None else None,
                "annotations": annotations_to_list(frame_anns),  # additive layer
                "svg": svg,
                "egi_summary": _egi_summary(egi),
                "linear_forms": linear_forms(egi),
                # Per-frame introspection from the same egi as the svg (ids
                # match) — the context reflex's enclosure walk per chain state.
                "introspection": egi_introspection(egi),
            }

        frames = [
            _frame(0, "base", chain.states[chain.initial_state_id],
                   chain.initial_state_id)
        ]
        _prev = chain.states[chain.initial_state_id]
        for i, step in enumerate(chain.steps, start=1):
            _cur = chain.states[step.to_state_id]
            frames.append(
                _frame(
                    i,
                    "step",
                    _cur,
                    step.to_state_id,
                    rule=step.rule_name,
                    annotation=step.user_annotation,
                    step_id=step.step_id,
                    prev_egi=_prev,
                )
            )
            _prev = _cur

        # A chain *branches* when two steps share a from_state (fork) or a
        # to_state (converge) — the linear lenses (storyboard / time-stack / the
        # frame player) read a single line, so the client offers them only when
        # the chain is linear; the derivation-DAG lens handles the rest.
        from collections import Counter as _C
        _frm = _C(s.from_state_id for s in chain.steps)
        _to = _C(s.to_state_id for s in chain.steps)
        branching = any(v > 1 for v in _frm.values()) or any(v > 1 for v in _to.values())

        return ApiResponse(
            success=True,
            data={
                "uod_id": uod_id,
                "has_chain": True,
                "step_count": len(chain.steps),
                "branching": branching,
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


@router.get("/uods/{uod_id}/modal")
async def get_uod_modal(uod_id: str, over: str = "states",
                        proposal: Optional[str] = None, closed: bool = True,
                        thumbs: bool = True):
    """Read **◇ (possibility) and □ (necessity) off the branching history** — the
    *trajectory reading* of `docs/MODALITY_WITHOUT_GAMMA.md` §1, with **no modal
    mark** (the diachronic lens for ``src/modal_query.py``).

    A modal operator is a quantifier over a Kripke frame ⟨W, R⟩, and a UoD's
    transformation chain *is* that frame: the worlds are its EGI states (sheets),
    accessibility is the legal-transition DAG.  So for a relation φ scribed across
    the reachable sheets, ◇φ = "some legal trajectory scribes φ" and □φ = "every
    legal trajectory scribes φ" — *possibility is branching, necessity is
    convergence.*  This route classifies every relation appearing across the worlds
    as **necessary** (□ — on every reachable sheet) or merely **possible** (◇ — on
    some but not all).

    ``over`` quantifies over ``"states"`` (all reachable sheets, the standard Kripke
    reading; default) or ``"leaves"`` (the trajectory endpoints only).  ``has_chain``
    is False (empty ``relations``) for the synchronic majority of the corpus.

    ``proposal`` (optional EGIF) is the **compound-meaning reader** the Gamma
    demonstrations need (docs/GAMMA_DEMONSTRATIONS.md): a per-relation ◇/◻ cannot
    display Peirce's would-be ◻(fails→suicides).  G is peeled at each world with the
    same three-valued semantics the audit route uses (materialize + closed-world
    ``CorpusOracle`` by default; ``closed=false`` for the open-world reading), and
    the response's ``proposal`` block reports ◻G (TRUE at every world) / ◇G (TRUE at
    some), with witnesses, counterexamples, and UNKNOWN worlds listed — abstentions
    reported, never coerced.  Absent an explicit proposal, the UoD's declared
    ``audit-proposal`` annotation is evaluated (so a would-be exemplar pre-fills).

    ``thumbs`` adds a small **drawn thumbnail** per world (the §3.3-attested render
    path, like ``/history-structure``) so the worlds strip shows the pictures
    themselves; skipped with ``thumbs_omitted`` when the frame exceeds 24 worlds.
    Without thumbnails the route stays geometry-free (``attest=False`` load, no
    layout engine, no §3.3 obligation).
    """
    try:
        import modal_query as mq
        from egif_generator_dau import generate_egif

        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id, attest=False)   # structure only — modality is geometry-free
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found in tomos"})

        chain = tomos.load_chain(uod_id)
        if chain is None:
            return ApiResponse(success=True, data={
                "uod_id": uod_id, "has_chain": False, "relations": []})

        if over not in ("states", "leaves"):
            over = "states"
        worlds = sorted(
            mq.leaf_states(chain) if over == "leaves" else mq.reachable_states(chain))

        # Every relation name scribed on *some* considered world — the φ's to classify.
        names = sorted({n for w in worlds for n in chain.states[w].rel.values()})
        relations = []
        for name in names:
            pos = mq.possibly(chain, mq.scribes_relation(name), over=over)
            nec = mq.necessarily(chain, mq.scribes_relation(name), over=over)
            relations.append({
                "name": name,
                "necessary": nec.holds,            # □ — on every reachable sheet
                "possible": pos.holds,             # ◇ — on some reachable sheet
                "modal": "necessary" if nec.holds else "possible",
                "witnesses": pos.witnesses,        # worlds where φ holds
                "counterexamples": nec.counterexamples,  # worlds where φ is absent
                "summary": nec.summary if nec.holds else pos.summary,
            })

        # Is the blank sheet (the one unconditioned world) reachable? — ◇⊤-shaped.
        blank = mq.possibly(chain, mq.is_blank(), over=over)

        # The compound-meaning reader: peel a proposal G at each world (the audit
        # route's three-valued semantics), then read ◻G/◇G off the verdict map.
        # An explicit ?proposal= wins; else the declared audit-proposal pre-fills.
        proposal_block = None
        effective = (proposal or "").strip() or _audit_proposal_default(tomos, uod_id)
        if effective:
            from domain_oracle import CorpusOracle
            from egif_parser_dau import parse_egif
            from model_materialization import materialize_egi
            from semantic_game import evaluate as evaluate_semantic
            try:
                g_egi = parse_egif(effective)
            except Exception as pexc:
                if (proposal or "").strip():
                    return ApiResponse(success=False, error={
                        "code": "MODAL_PROPOSAL_INVALID",
                        "message": f"proposal is not well-formed EGIF: {pexc}"})
                g_egi = None      # a broken *declared* default is skipped, not fatal
            if g_egi is not None:
                verdicts = {}
                for w in worlds:
                    facts, _ = materialize_egi(chain.states[w])
                    oracle = CorpusOracle([("M", facts)], closed=closed)
                    verdicts[w] = evaluate_semantic(
                        g_egi, oracle, closed=closed).verdict.value
                true_w = [w for w, v in verdicts.items() if v == "true"]
                false_w = [w for w, v in verdicts.items() if v == "false"]
                unknown_w = [w for w, v in verdicts.items() if v == "unknown"]
                nec = bool(worlds) and len(true_w) == len(worlds)
                pos = bool(true_w)
                glyph = "□" if nec else ("◇" if pos else "□¬")
                proposal_block = {
                    "proposal": effective,
                    "from_annotation": not bool((proposal or "").strip()),
                    "closed": closed,
                    "necessary": nec,              # ◻G — TRUE at every considered world
                    "possible": pos,               # ◇G — TRUE at some considered world
                    "witnesses": true_w,
                    "counterexamples": false_w,
                    "unknown_worlds": unknown_w,   # abstentions reported, never coerced
                    "verdicts": verdicts,
                    "summary": (f"{glyph}G over {len(worlds)} {over} — "
                                f"true at {len(true_w)}, false at {len(false_w)}"
                                + (f", unknown at {len(unknown_w)}" if unknown_w else "")),
                }

        # Per-world descriptors so the lens can show the sheets the modality reads off
        # — with a drawn thumbnail (the attested render path) unless the frame is huge.
        leaves = mq.leaf_states(chain)
        thumbs_omitted = thumbs and len(worlds) > 24
        render_thumbs = thumbs and not thumbs_omitted
        worlds_detail = []
        for w in worlds:
            d = {
                "id": w,
                "egif": generate_egif(chain.states[w]).strip() or "(blank sheet)",
                "is_initial": w == chain.initial_state_id,
                "is_leaf": w in leaves,
            }
            if proposal_block is not None:
                d["verdict"] = proposal_block["verdicts"].get(w)
            if render_thumbs:
                _dto, svg = generate_layout(chain.states[w])
                d["svg"] = svg
            worlds_detail.append(d)

        from collections import Counter as _C
        _frm = _C(s.from_state_id for s in chain.steps)
        _to = _C(s.to_state_id for s in chain.steps)
        branching = any(v > 1 for v in _frm.values()) or any(v > 1 for v in _to.values())

        return ApiResponse(success=True, data={
            "uod_id": uod_id, "name": uod.name, "has_chain": True,
            "over": over, "branching": branching,
            "world_count": len(worlds), "worlds": worlds_detail,
            "relations": relations,
            "blank_possible": blank.holds,
            "proposal": proposal_block,
            "thumbs_omitted": thumbs_omitted,
        })
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "MODAL_ERROR", "message": str(exc), "type": type(exc).__name__})


def _audit_proposal_default(tomos: TomosService, uod_id: str) -> Optional[str]:
    """The standing proposal a chained UoD declares for auditing — a UoD-scoped
    annotation tagged ``audit-proposal`` whose text is the proposal's EGIF (written
    by the dialogue exemplar's build script).  ``None`` if the UoD declares none."""
    for ann in tomos.load_annotations(uod_id) or []:
        if "audit-proposal" in (ann.get("tags") or []):
            text = (ann.get("text") or "").strip()
            if text:
                return text
    return None


@router.get("/uods/{uod_id}/audit")
async def get_uod_audit(uod_id: str, proposal: Optional[str] = None,
                        closed: bool = True):
    """Peel a **standing proposal G against every state of the chain** — the
    *verdict trajectory* of a model **revised through dialog** (``src/model_revision.py``;
    `docs/EXEMPLARS.md` §6).

    An inning is *given M, then G*; what the dialogue does is **revise M itself**, and
    the verdict a later inning gives can flip as M grows.  This route makes that
    visible: it walks the chain (each state is a successive model M), materializes M's
    Horn fragment, and peels the same proposal G against it — returning the verdict at
    each state, so a reader watches the audit move (the dialogue exemplar flips
    FALSE→TRUE→FALSE→TRUE).  This is read-only **model-checking** (truth-in-a-model, not
    inference); **nothing is asserted** — a proposal earns warrant only by withstanding
    Agon.

    ``proposal`` is the EGIF of G; absent, the UoD's declared ``audit-proposal``
    annotation is used (404-style ``NO_PROPOSAL`` if neither is present).  ``closed``
    selects closed-world (default — a domain model is read as a closed record) vs
    open-world.  Geometry-free (``attest=False``); no §3.3 obligation.
    """
    try:
        from model_materialization import materialize_egi
        from domain_oracle import CorpusOracle
        from semantic_game import evaluate as evaluate_semantic
        from egif_parser_dau import parse_egif

        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id, attest=False)
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found in tomos"})

        chain = tomos.load_chain(uod_id)
        if chain is None:
            return ApiResponse(success=True, data={
                "uod_id": uod_id, "has_chain": False, "frames": []})

        if not (proposal and proposal.strip()):
            proposal = _audit_proposal_default(tomos, uod_id)
        if not (proposal and proposal.strip()):
            return ApiResponse(success=False, error={
                "code": "NO_PROPOSAL",
                "message": ("no proposal given and this UoD declares no 'audit-proposal' "
                            "— pass ?proposal=<egif>")})

        g_egi = parse_egif(proposal)   # raises (caught) if the proposal is ill-formed

        def _verdict(state_egi):
            facts, _ = materialize_egi(state_egi)
            oracle = CorpusOracle([("M", facts)], closed=closed)
            return evaluate_semantic(g_egi, oracle, closed=closed)

        def _frame(index, kind, state_id, rule=None, params=None, annotation=None):
            r = _verdict(chain.states[state_id])
            p = params or {}
            # The revision's payload, under whichever key the disposition used
            # (a sheet fact, a law/rule cut, or the subgraph relinquished).
            fact = (p.get("fact") or p.get("fact_egif") or p.get("rule_egif")
                    or p.get("subgraph_egif"))
            return {
                "index": index, "kind": kind, "state_id": state_id,
                "rule": rule, "fact": fact, "annotation": annotation,
                # The inning outcome that produced this M (the taxonomy made visible):
                # which disposition, in which Peircean mode.
                "disposition": p.get("disposition"), "mode": p.get("mode"),
                "verdict": r.verdict.value, "summary": r.summary,
                "winning_witness": r.winning_witness,
                "counterexample": r.counterexample,
            }

        frames = [_frame(0, "base", chain.initial_state_id)]
        for i, step in enumerate(chain.steps, start=1):
            frames.append(_frame(
                i, "step", step.to_state_id, rule=step.rule_name,
                params=(step.parameters or {}), annotation=step.user_annotation))

        return ApiResponse(success=True, data={
            "uod_id": uod_id, "name": uod.name, "has_chain": True,
            "proposal": proposal, "closed": closed,
            "step_count": len(chain.steps), "frames": frames})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "AUDIT_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.get("/uods/{uod_id}/accessible")
async def get_uod_accessible(uod_id: str):
    """The UoD's **non-visual, screen-reader-native projection** (R4).

    An EG's ground truth is coordinate-free (``natural_layout(egi)``); the
    picture is one projection of it, and this is another — a traversable
    sheet → cut → area → ligature tree, a flat spoken reading order, and a
    single outside-in reading of the whole graph — so the graph is legible to a
    reader who is not looking at a drawing (see
    ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §3.1–§3.2).

    Because it is a **pure function of the EGI + its natural layout**, it *is*
    the ground truth: there is no drawing in between, so — like ``/modal`` and
    ``/audit`` — it loads with ``attest=False`` and carries **no §3.3
    obligation** (no geometry, no layout engine).  The canonical linear form is
    included beside the reading as the cross-check (picture, reading, and
    proposition all denote the same object).
    """
    try:
        from accessible_projection import accessible_projection, projection_to_dict

        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id, attest=False)   # geometry-free — no §3.3 obligation
        if uod is None:
            return ApiResponse(success=False, error={
                "code": "UOD_NOT_FOUND", "message": f"UoD '{uod_id}' not found in tomos"})
        egi = uod.current_egi
        if egi is None:
            return ApiResponse(success=False, error={
                "code": "EMPTY_UOD", "message": f"UoD '{uod_id}' has no current EGI"})

        proj = projection_to_dict(accessible_projection(egi))
        return ApiResponse(success=True, data={
            "uod_id": uod_id, "name": uod.name,
            "tree": proj["tree"],
            "reading": proj["reading"],
            "reading_lines": proj["reading_lines"],
            "linear_forms": linear_forms(egi),
        })
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "ACCESSIBLE_ERROR", "message": str(exc), "type": type(exc).__name__})
