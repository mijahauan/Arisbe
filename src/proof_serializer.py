"""
Proof Serializer for EGI Transformation Sequences

Provides round-trip serialization of EGI transformation histories:
  - JSON format: machine-readable, preserves full metadata + EGIF per state
  - Text format:  human-readable proof notation (one EGIF per step)

Motivating use case: save, share, and replay proofs built in the Ergasterion
GUI or produced by automated transformation engines.

Usage::

    from proof_serializer import ProofSerializer

    # Serialize a proof (EGITransformationHistory → JSON)
    json_str = ProofSerializer.to_json(history)

    # Serialize as readable text
    text = ProofSerializer.to_text(history)

    # Reconstruct history from JSON (re-parses EGIF strings → EGI)
    restored = ProofSerializer.from_json(json_str)
"""

import json
from typing import Any, Dict, List, Optional

from egi_core_dau import RelationalGraphWithCuts
from egi_transformation_history import (
    EGITransformationHistory,
    TransformationStatus,
)
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)


class ProofSerializer:
    """Serialize and deserialize EGI transformation histories."""

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    @staticmethod
    def to_json(history: EGITransformationHistory, indent: int = 2) -> str:
        """
        Serialize a transformation history to JSON.

        Each state includes its EGIF string so the proof is self-contained;
        EGI objects can be reconstructed by re-parsing those strings.
        """
        data = ProofSerializer._build_export_dict(history)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def to_text(history: EGITransformationHistory) -> str:
        """
        Render a transformation history as a human-readable proof listing.

        Format::

            === Proof ===
            Step 0 — Initial state
              (EGIF)

            Step 1 — IT+ (Iteration)
              (EGIF)
            ...
        """
        lines: List[str] = ["=== Proof ==="]

        # Walk the main linear path from root to current state
        path = ProofSerializer._linear_path(history)

        for i, state_id in enumerate(path):
            state = history.states[state_id]

            # Rule label: first step has no incoming rule
            rule_label = "Initial state"
            if i > 0:
                prev_state_id = path[i - 1]
                step_id = history._find_step_between_states(prev_state_id, state_id)
                if step_id and step_id in history.transformations:
                    rule_label = history.transformations[step_id].rule_name

            try:
                egif = generate_egif(state.egi)
            except Exception as exc:
                egif = f"<EGIF generation failed: {exc}>"

            lines.append(f"\nStep {i} — {rule_label}")
            if state.description and state.description not in (
                "Initial state",
                f"After {rule_label}",
            ):
                lines.append(f"  [{state.description}]")
            lines.append(f"  {egif}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    @staticmethod
    def from_json(json_str: str) -> EGITransformationHistory:
        """
        Reconstruct an EGITransformationHistory from a JSON proof string.

        The EGIF strings in the JSON are re-parsed to EGI objects.  All
        transformation metadata (rule names, timestamps, etc.) is restored;
        TransformationContext / TransformationResult objects are stubs
        (full context data is not stored in the serialized form).
        """
        data: Dict[str, Any] = json.loads(json_str)

        # Re-parse all EGI states
        state_egis: Dict[str, RelationalGraphWithCuts] = {}
        for sid, sdata in data["states"].items():
            egif_str = sdata.get("egif", "")
            if egif_str:
                try:
                    state_egis[sid] = parse_egif(egif_str)
                except Exception as exc:
                    raise ValueError(
                        f"Cannot parse EGIF for state {sid!r}: {exc}"
                    ) from exc
            else:
                raise ValueError(f"State {sid!r} missing 'egif' field in JSON")

        # Identify the root state
        root_state_id: str = data.get(
            "root_state_id", data["state_sequence"][0] if data.get("state_sequence") else ""
        )
        if not root_state_id:
            raise ValueError("Cannot determine root state from JSON")

        # Reconstruct history
        history = EGITransformationHistory(
            initial_egi=state_egis[root_state_id],
            description=data["states"][root_state_id].get("description", "Initial state"),
        )

        # The constructor already created an initial state with a fresh ID.
        # We need to map original IDs → reconstructed IDs.  For the root state
        # this is already done.  Walk the state_sequence in order and replay
        # each transformation as a stub.
        orig_root_id: str = root_state_id
        new_root_id: str = history.current_state_id
        id_map: Dict[str, str] = {orig_root_id: new_root_id}

        state_seq: List[str] = data.get("state_sequence", [])
        for i in range(1, len(state_seq)):
            orig_from = state_seq[i - 1]
            orig_to = state_seq[i]
            step_id_orig = ProofSerializer._find_orig_step(
                data, orig_from, orig_to
            )

            rule_name = "unknown"
            description = data["states"][orig_to].get("description", "")
            if step_id_orig and step_id_orig in data["transformations"]:
                rule_name = data["transformations"][step_id_orig].get("rule_name", "unknown")

            # Build a stub result for this state
            new_egi = state_egis[orig_to]
            stub_context = TransformationContext(
                source_egi=state_egis[orig_from],
                target_area=new_egi.sheet,
                selected_subgraph=frozenset(),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0,
            )
            stub_result = TransformationResult(
                success=True,
                result_egi=new_egi,
                error_message=None,
                changes_made={"restored_from_json": True},
            )
            user_annotation: Optional[str] = None
            if step_id_orig and step_id_orig in data["transformations"]:
                user_annotation = data["transformations"][step_id_orig].get(
                    "user_annotation"
                )
            new_step_id = history.add_transformation(
                rule_name=rule_name,
                context=stub_context,
                result=stub_result,
                user_annotation=user_annotation,
            )
            id_map[orig_to] = history.current_state_id

        return history

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_export_dict(history: EGITransformationHistory) -> Dict[str, Any]:
        """Build a serializable dict from the history."""
        states_out: Dict[str, Any] = {}
        for sid, state in history.states.items():
            try:
                egif = generate_egif(state.egi)
            except Exception as exc:
                egif = f"<error: {exc}>"
            states_out[sid] = {
                "state_id": state.state_id,
                "step_number": state.step_number,
                "description": state.description,
                "timestamp": state.timestamp.isoformat(),
                "egif": egif,
                "metadata": dict(state.metadata),
            }

        steps_out: Dict[str, Any] = {}
        for tid, t in history.transformations.items():
            steps_out[tid] = {
                "step_id": t.step_id,
                "rule_name": t.rule_name,
                "from_state_id": t.from_state_id,
                "to_state_id": t.to_state_id,
                "timestamp": t.timestamp.isoformat(),
                "status": t.status.value,
                "user_annotation": t.user_annotation,
                "metadata": dict(t.metadata),
            }

        return {
            "schema_version": "1.0",
            "history_id": history.history_id,
            "created_timestamp": history.created_timestamp.isoformat(),
            "current_state_id": history.current_state_id,
            "root_state_id": history.root_state_id,
            "state_sequence": list(history.state_sequence),
            "branch_points": list(history.branch_points),
            "states": states_out,
            "transformations": steps_out,
        }

    @staticmethod
    def _linear_path(history: EGITransformationHistory) -> List[str]:
        """Return the main linear path from root to current state."""
        if not history.root_state_id:
            return list(history.states.keys())

        seq = history.get_transformation_sequence(
            history.root_state_id, history.current_state_id
        )
        if seq.is_valid_path and seq.steps:
            path = [seq.from_state_id]
            for step in seq.steps:
                path.append(step.to_state_id)
            return path

        # Fallback: use stored state_sequence
        return list(history.state_sequence)

    @staticmethod
    def _find_orig_step(
        data: Dict[str, Any], from_state: str, to_state: str
    ) -> Optional[str]:
        """Find the transformation step ID connecting two states in exported data."""
        for tid, tdata in data.get("transformations", {}).items():
            if (
                tdata.get("from_state_id") == from_state
                and tdata.get("to_state_id") == to_state
                and tdata.get("status") == TransformationStatus.APPLIED.value
            ):
                return tid
        return None
