#!/usr/bin/env python3
"""
Demo: ProofSerializer — EGI Transformation History Serialization

Demonstrates four representative use cases:

  1. Linear proof  — build a multi-step proof, print as text, save/reload as JSON
  2. Syllogism     — serialize a classical syllogism proof sequence
  3. Annotations   — attach rule citations to transformation steps
  4. Branching DAG — serialize a history that has an alternative branch

Run:
    conda run -n CGIF python tools/demo_proof_serializer.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from egi_transformation_history import EGITransformationHistory
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    AreaPolarity,
    DoubleCutInsertionRule,
    TransformationContext,
)
from proof_serializer import ProofSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(egi, polarity=AreaPolarity.POSITIVE):
    return TransformationContext(
        source_egi=egi,
        target_area=egi.sheet,
        selected_subgraph=frozenset(),
        area_polarity=polarity,
        nesting_depth=0,
    )


def _apply(history, rule, annotation=None):
    egi = history.get_current_state().egi
    ctx = _ctx(egi)
    result = rule.apply_transformation(ctx)
    if result.success:
        history.add_transformation(rule.get_rule_name(), ctx, result, user_annotation=annotation)
    else:
        print(f"  [!] Rule {rule.get_rule_name()} failed: {result.error_message}")
    return result.success


def _hr(title=""):
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * (width - pad - len(title) - 2))
    else:
        print("─" * width)


# ---------------------------------------------------------------------------
# Demo 1: Linear proof with DC+, save/reload
# ---------------------------------------------------------------------------


def demo_linear_proof():
    _hr("Demo 1: Linear proof — save, reload, verify")

    egi = parse_egif("*x (Human x)")
    h = EGITransformationHistory(egi, "Premise: ∃x.Human(x)")

    print("Building 3-step DC+ proof...")
    for _ in range(3):
        _apply(h, DoubleCutInsertionRule())

    print("\n── Text proof ──")
    print(ProofSerializer.to_text(h))

    print("\n── JSON (excerpt) ──")
    data = json.loads(ProofSerializer.to_json(h))
    print(f"  schema_version : {data['schema_version']}")
    print(f"  states         : {len(data['states'])}")
    print(f"  transformations: {len(data['transformations'])}")
    print("  EGIFs per state:")
    for sid in data["state_sequence"]:
        s = data["states"][sid]
        print(f"    step {s['step_number']}: {s['egif']}")

    print("\n── Round-trip reload ──")
    json_str = ProofSerializer.to_json(h)
    restored = ProofSerializer.from_json(json_str)
    print(f"  Original  states : {len(h.states)}")
    print(f"  Restored  states : {len(restored.states)}")
    final_egif = generate_egif(restored.get_current_state().egi)
    print(f"  Final EGIF       : {final_egif}")
    print("  ✅ Round-trip OK" if len(restored.states) == len(h.states) else "  ❌ Mismatch!")


# ---------------------------------------------------------------------------
# Demo 2: Classical syllogism proof
# ---------------------------------------------------------------------------


def demo_syllogism():
    _hr("Demo 2: Syllogism proof sequence")

    print("Building syllogism: All humans are mortal; Socrates is human")
    print("→ DC+ is used to wrap sub-areas (simplified transformation stand-in)")

    # Represent the premise as an EGI and apply formal steps
    # In a full proof, ERA/IT+/IT- would be used with real subgraphs;
    # here we apply DC+ steps as placeholders to demonstrate serialization.
    egi = parse_egif("*x (Human x) ~[(Mortal x)]")
    h = EGITransformationHistory(egi, "Premise: ∀x.Human(x) → Mortal(x)")

    _apply(h, DoubleCutInsertionRule(), annotation="Dau Theorem 12.3.1 — DC+ in positive context")
    _apply(h, DoubleCutInsertionRule(), annotation="Prepare for deiteration step")
    _apply(h, DoubleCutInsertionRule(), annotation="Wrap for subsequent IT+ application")

    print(ProofSerializer.to_text(h))

    # Save to file
    out_path = os.path.join(os.path.dirname(__file__), "..", "test_outputs", "syllogism_proof.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ProofSerializer.to_json(h))
    print(f"  Saved to: {os.path.relpath(out_path)}")


# ---------------------------------------------------------------------------
# Demo 3: Step annotations for academic citation
# ---------------------------------------------------------------------------


def demo_annotations():
    _hr("Demo 3: Annotated steps with rule citations")

    egi = parse_egif("*x (Human x)")
    h = EGITransformationHistory(egi, "Initial graph")

    _apply(h, DoubleCutInsertionRule(),
           annotation="Dau §12.3.1 — double cut insertion (positive area)")
    _apply(h, DoubleCutInsertionRule(),
           annotation="Iteration pre-condition: wrap before IT+")
    _apply(h, DoubleCutInsertionRule(),
           annotation="Dau §12.3.1 again — third wrap for demonstration")

    data = json.loads(ProofSerializer.to_json(h))

    print("  Transformation steps with annotations:")
    for seq_idx in range(1, len(data["state_sequence"])):
        from_id = data["state_sequence"][seq_idx - 1]
        to_id   = data["state_sequence"][seq_idx]
        # Find the step connecting these two states
        for tid, t in data["transformations"].items():
            if t["from_state_id"] == from_id and t["to_state_id"] == to_id:
                ann = t.get("user_annotation") or "(no annotation)"
                print(f"    [{t['rule_name']:4s}]  {ann}")
                break

    # Verify annotations survive round-trip
    restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
    restored_data = json.loads(ProofSerializer.to_json(restored))
    annotations = [
        t.get("user_annotation")
        for t in restored_data["transformations"].values()
        if t.get("user_annotation")
    ]
    print(f"\n  Annotations preserved after round-trip: {len(annotations)}/3")
    assert len(annotations) == 3, "Annotation round-trip failed"
    print("  ✅ All annotations round-trip correctly")


# ---------------------------------------------------------------------------
# Demo 4: Branching DAG serialization
# ---------------------------------------------------------------------------


def demo_branching():
    _hr("Demo 4: Branching DAG — two paths from a single state")

    egi = parse_egif("*x (Human x)")
    h = EGITransformationHistory(egi, "Root")

    # S0 → S1 (main path continues)
    _apply(h, DoubleCutInsertionRule(), annotation="Main path step 1")
    branch_point_id = h.current_state_id
    print(f"  Branch point: step {h.get_current_state().step_number}")

    # S1 → S2 (main)
    _apply(h, DoubleCutInsertionRule(), annotation="Main path step 2")
    main_end = h.current_state_id

    # Create alternative branch from S1 → S3
    h.create_branch_from_state(branch_point_id, description="Alternative exploration")
    _apply(h, DoubleCutInsertionRule(), annotation="Alt branch step")
    alt_end = h.current_state_id

    data = json.loads(ProofSerializer.to_json(h))
    print(f"  Total states       : {len(data['states'])}")
    print(f"  Total steps        : {len(data['transformations'])}")
    print(f"  Branch points      : {data['branch_points']}")
    print(f"  Main path length   : {len(data['state_sequence'])} states")

    # to_text follows current_state_id path
    text = ProofSerializer.to_text(h)
    print("\n── Text proof (follows current path) ──")
    print(text)

    # Round-trip
    restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
    print(f"\n  Restored states: {len(restored.states)} (expected {len(h.states)})")
    assert len(restored.states) == len(h.states)
    print("  ✅ Branching DAG round-trip OK")


# ---------------------------------------------------------------------------
# Demo 5: Sharing a proof (write + reload as a collaborator would)
# ---------------------------------------------------------------------------


def demo_sharing():
    _hr("Demo 5: Sharing a proof between sessions")

    egi = parse_egif("*x *y (R x y)")
    h = EGITransformationHistory(egi, "Relational graph R(x,y)")
    _apply(h, DoubleCutInsertionRule(), annotation="Wrap for iteration")
    _apply(h, DoubleCutInsertionRule())

    # Researcher A saves
    json_str = ProofSerializer.to_json(h)
    out_path = os.path.join(os.path.dirname(__file__), "..", "test_outputs", "shared_proof.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    print(f"  Researcher A saved proof → {os.path.relpath(out_path)}")

    # Researcher B loads
    with open(out_path, encoding="utf-8") as f:
        received = ProofSerializer.from_json(f.read())

    final = generate_egif(received.get_current_state().egi)
    steps = received.get_current_state().step_number
    print(f"  Researcher B loaded: {len(received.states)} states, {steps} steps applied")
    print(f"  Final graph: {final}")
    print("  ✅ Sharing demo complete")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 60)
    print("  ProofSerializer Demo")
    print("=" * 60)

    demo_linear_proof()
    demo_syllogism()
    demo_annotations()
    demo_branching()
    demo_sharing()

    print("\n" + "=" * 60)
    print("  All demos complete")
    print("=" * 60)
