"""
Transformation API endpoints (apply, validate, undo, redo).
"""

import sys
from pathlib import Path

_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import (
    ApiResponse,
    TransformApplyRequest,
    TransformValidateRequest,
    SubgraphValidateRequest,
    UndoRedoRequest,
)
from web_api.services.session_manager import get_session_manager
from web_api.services.layout_service import generate_layout, layout_dto_to_dict

from formal_transformation_rules import FormalTransformationEngine
from subgraph_closure_validator import SubgraphClosureValidator
from egif_parser_dau import parse_egif
from simple_svg_renderer import SimpleSVGRenderer
from egif_generator_dau import EGIFGenerator

router = APIRouter(prefix="/api")

_engine = FormalTransformationEngine()


def _egi_summary(egi) -> dict:
    return {
        "vertex_count": len(egi.V),
        "edge_count": len(egi.E),
        "cut_count": len(egi.Cut),
    }


def _render_svg(egi, dto) -> str:
    try:
        egif = EGIFGenerator().generate(egi)
    except Exception:
        egif = ""
    renderer = SimpleSVGRenderer()
    return renderer.render_to_svg(dto, title="Existential Graph", egif=egif, egi=egi)


def _infer_target_area(egi, selected_elements) -> str:
    """Infer the target area from selected elements (shallowest common area)."""
    if not selected_elements:
        return egi.sheet

    # Find what areas each element lives in
    elem_areas = {}
    for area_id, contents in egi.area.items():
        for elem_id in contents:
            if elem_id in selected_elements:
                elem_areas[elem_id] = area_id

    if not elem_areas:
        return egi.sheet

    # Get depth of each candidate area
    area_depths = {}
    for area_id in set(elem_areas.values()):
        try:
            _, depth = egi.area_polarity(area_id)
            area_depths[area_id] = depth
        except Exception:
            area_depths[area_id] = 0

    # Return shallowest area (lowest depth)
    return min(area_depths, key=area_depths.get)


@router.post("/transform/validate")
async def validate_transform(request: TransformValidateRequest):
    """Validate a transformation without applying it."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(request.session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            )

        egi = session.current_egi
        rule = request.rule
        params = request.parameters

        errors = []
        preview_svg = None

        if rule == "ERA":
            selected = frozenset(params.get("selected_elements", []))
            target_area = params.get("target_area") or _infer_target_area(egi, selected)

            if not selected:
                errors.append("No elements selected for erasure")
            else:
                # Check polarity
                try:
                    polarity, _ = egi.area_polarity(target_area)
                    if polarity.value != "positive":
                        errors.append("ERA requires a positive (recto) area")
                except Exception as e:
                    errors.append(f"Area polarity error: {e}")

                # Check closure
                validator = SubgraphClosureValidator(egi)
                analysis = validator.analyze_closure(selected, allow_expansion=True)
                if not analysis.is_closed:
                    missing = list(analysis.added_elements)
                    errors.append(f"Selection is not a closed subgraph; missing: {missing}")

        elif rule == "INS":
            egif_content = params.get("egif_content", "")
            target_area = params.get("target_area", egi.sheet)
            if not egif_content:
                errors.append("EGIF content required for INS")
            else:
                try:
                    parse_egif(egif_content)
                except Exception as e:
                    errors.append(f"Invalid EGIF: {e}")
                try:
                    polarity, _ = egi.area_polarity(target_area)
                    if polarity.value != "negative":
                        errors.append("INS requires a negative (verso) area")
                except Exception as e:
                    errors.append(f"Area polarity error: {e}")

        elif rule in ("DC+", "IT+"):
            target_area = params.get("target_area", egi.sheet)
            if target_area not in egi.area:
                errors.append(f"Area {target_area} does not exist")

        elif rule == "DC-":
            target_cut = params.get("target_cut")
            if not target_cut:
                errors.append("target_cut required for DC-")

        elif rule in ("IT-",):
            selected = frozenset(params.get("selected_elements", []))
            if not selected:
                errors.append("No elements selected for deiteration")

        valid = len(errors) == 0
        return ApiResponse(
            success=True,
            data={
                "valid": valid,
                "errors": errors,
                "preview_svg": preview_svg,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "VALIDATE_ERROR", "message": str(exc)},
        )


@router.post("/transform/apply")
async def apply_transform(request: TransformApplyRequest):
    """Apply a transformation rule to the current EGI."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(request.session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            )

        egi = session.current_egi
        rule = request.rule
        params = request.parameters

        # Extract parameters per rule
        if rule == "ERA":
            selected = frozenset(params.get("selected_elements", []))
            target_area = params.get("target_area") or _infer_target_area(egi, selected)

        elif rule == "INS":
            egif_content = params.get("egif_content", "")
            target_area = params.get("target_area", egi.sheet)
            # For INS the selected_subgraph is the parsed graph's elements
            try:
                insert_egi = parse_egif(egif_content)
                selected = frozenset(
                    [v.id for v in insert_egi.V]
                    + [e.id for e in insert_egi.E]
                    + [c.id for c in insert_egi.Cut]
                )
            except Exception as e:
                return ApiResponse(
                    success=False,
                    error={"code": "PARSE_ERROR", "message": f"Invalid EGIF: {e}"},
                )

        elif rule == "DC+":
            selected = frozenset(params.get("selected_elements", []))
            target_area = params.get("target_area", egi.sheet)

        elif rule == "DC-":
            target_cut = params.get("target_cut")
            if not target_cut:
                return ApiResponse(
                    success=False,
                    error={"code": "PARAM_ERROR", "message": "target_cut required for DC-"},
                )
            selected = frozenset([target_cut])
            # Find where the cut lives
            target_area = _infer_target_area(egi, selected)

        elif rule == "IT+":
            selected = frozenset(params.get("selected_elements", []))
            target_area = params.get("target_area", egi.sheet)

        elif rule == "IT-":
            selected = frozenset(params.get("selected_elements", []))
            target_area = _infer_target_area(egi, selected)

        else:
            return ApiResponse(
                success=False,
                error={"code": "UNKNOWN_RULE", "message": f"Unknown rule: {rule}"},
            )

        # Apply the rule
        result = _engine.apply_rule(rule, egi, target_area, selected)

        if not result.success:
            return ApiResponse(
                success=False,
                error={"code": "TRANSFORM_FAILED", "message": result.error_message},
            )

        new_egi = result.result_egi
        previous_layout = session.current_layout_dto
        new_dto, svg = generate_layout(new_egi, previous_layout=previous_layout)

        session_manager.update_session(
            request.session_id, new_egi, new_dto, rule=rule, params=params
        )
        updated_session = session_manager.get_session(request.session_id)

        return ApiResponse(
            success=True,
            data={
                "svg": svg,
                "layout_dto": layout_dto_to_dict(new_dto),
                "egi_summary": _egi_summary(new_egi),
                "can_undo": updated_session.can_undo(),
                "can_redo": updated_session.can_redo(),
                "history_index": updated_session.history_index,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "APPLY_ERROR", "message": str(exc)},
        )


@router.post("/undo")
async def undo(request: UndoRedoRequest):
    """Undo the last transformation."""
    try:
        session_manager = get_session_manager()
        result = session_manager.undo(request.session_id)
        if result is None:
            return ApiResponse(
                success=False,
                error={"code": "UNDO_UNAVAILABLE", "message": "Nothing to undo"},
            )
        egi, dto = result
        svg = _render_svg(egi, dto)
        session = session_manager.get_session(request.session_id)
        return ApiResponse(
            success=True,
            data={
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
            error={"code": "UNDO_ERROR", "message": str(exc)},
        )


@router.post("/redo")
async def redo(request: UndoRedoRequest):
    """Redo the last undone transformation."""
    try:
        session_manager = get_session_manager()
        result = session_manager.redo(request.session_id)
        if result is None:
            return ApiResponse(
                success=False,
                error={"code": "REDO_UNAVAILABLE", "message": "Nothing to redo"},
            )
        egi, dto = result
        svg = _render_svg(egi, dto)
        session = session_manager.get_session(request.session_id)
        return ApiResponse(
            success=True,
            data={
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
            error={"code": "REDO_ERROR", "message": str(exc)},
        )


@router.post("/subgraph/validate")
async def validate_subgraph(request: SubgraphValidateRequest):
    """Validate whether the selected elements form a closed subgraph."""
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(request.session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            )

        egi = session.current_egi
        selection = frozenset(request.selected_elements)
        context_area = request.context_area

        validator = SubgraphClosureValidator(egi)
        analysis = validator.analyze_closure(
            selection,
            allow_expansion=True,
            context_area=context_area,
        )

        if analysis.is_closed:
            return ApiResponse(
                success=True,
                data={
                    "is_closed": True,
                    "missing_elements": list(analysis.added_elements),
                    "closure": list(analysis.closed_subgraph),
                },
            )
        else:
            missing = set()
            for v in analysis.violations:
                missing.update(v.missing_elements)
            return ApiResponse(
                success=False,
                error={
                    "code": "NOT_CLOSED",
                    "message": "Selection does not form a closed subgraph",
                    "details": {
                        "missing_elements": list(missing),
                        "closure": list(analysis.closed_subgraph),
                    },
                },
            )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "VALIDATE_SUBGRAPH_ERROR", "message": str(exc)},
        )
