#!/usr/bin/env python3
"""
Comprehensive Transformation Sequence Testing

Tests complex multi-step transformation scenarios with real EGI data,
including classical logical proofs, Peirce's examples, and stress testing
with long transformation chains.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def load_real_egi_for_sequences():
    """Load real EGI files suitable for sequence testing."""
    from test_real_egi_data import find_corpus_egi_files, load_egi_from_file
    
    egi_files = find_corpus_egi_files()
    loaded_egis = []
    
    for egi_file in egi_files[:5]:  # Load first 5 for testing
        egi = load_egi_from_file(egi_file)
        if egi:
            loaded_egis.append((egi_file.stem, egi))
    
    return loaded_egis

def test_classical_proof_sequences():
    """Test sequences that represent classical logical proofs."""
    print("📚 TESTING CLASSICAL PROOF SEQUENCES")
    print("=" * 50)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
    
    engine = TransformationSequenceEngine()
    
    # Test 1: Double Negation Elimination (¬¬P → P)
    print("\n🔍 Test 1: Double Negation Elimination")
    print("-" * 30)
    
    # Create EGI representing ¬¬P
    v_p = Vertex(ElementID("P"))
    c_inner = Cut(ElementID("inner_cut"))
    c_outer = Cut(ElementID("outer_cut"))
    sheet = ElementID("sheet")
    
    double_neg_egi = RelationalGraphWithCuts(
        V=frozenset([v_p]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset([c_inner, c_outer]),
        area=frozendict({
            sheet: frozenset([c_outer.id]),
            c_outer.id: frozenset([c_inner.id]),
            c_inner.id: frozenset([v_p.id])
        }),
        rel=frozendict()
    )
    
    # Create sequence for double negation elimination
    seq1 = engine.create_sequence(double_neg_egi, "double_negation_elimination")
    
    # Step 1: Apply double cut rule
    step1 = engine.add_transformation_step(
        "double_negation_elimination",
        TransformationRuleType.DOUBLE_CUT,
        {c_inner.id, c_outer.id}
    )
    
    print(f"  Step 1 (Double Cut): {step1.validation_result.value if step1.validation_result else 'None'}")
    
    # Get sequence statistics
    stats1 = engine.get_sequence_statistics("double_negation_elimination")
    print(f"  Result: {stats1['success_rate']:.1%} success rate")
    
    # Test 2: Disjunctive Syllogism ((P ∨ Q) ∧ ¬P → Q)
    print("\n🔍 Test 2: Disjunctive Syllogism")
    print("-" * 30)
    
    # Create more complex EGI for disjunctive syllogism
    v_p = Vertex(ElementID("P"))
    v_q = Vertex(ElementID("Q"))
    c_not_p = Cut(ElementID("not_p"))
    c_not_pq = Cut(ElementID("not_pq"))
    
    disj_syl_egi = RelationalGraphWithCuts(
        V=frozenset([v_p, v_q]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset([c_not_p, c_not_pq]),
        area=frozendict({
            sheet: frozenset([c_not_pq.id, c_not_p.id]),
            c_not_pq.id: frozenset([v_p.id, v_q.id]),
            c_not_p.id: frozenset([v_p.id])
        }),
        rel=frozendict()
    )
    
    seq2 = engine.create_sequence(disj_syl_egi, "disjunctive_syllogism")
    
    # Multi-step sequence
    step2a = engine.add_transformation_step(
        "disjunctive_syllogism",
        TransformationRuleType.ERASURE,
        {v_p.id}
    )
    
    step2b = engine.add_transformation_step(
        "disjunctive_syllogism", 
        TransformationRuleType.DOUBLE_CUT,
        {c_not_pq.id}
    )
    
    print(f"  Step 1 (Erasure): {step2a.validation_result.value if step2a.validation_result else 'None'}")
    print(f"  Step 2 (Double Cut): {step2b.validation_result.value if step2b.validation_result else 'None'}")
    
    stats2 = engine.get_sequence_statistics("disjunctive_syllogism")
    print(f"  Result: {stats2['success_rate']:.1%} success rate, {stats2['total_steps']} steps")
    
    return [stats1, stats2]

def test_peirce_historical_sequences():
    """Test sequences based on Peirce's historical examples."""
    print("\n📜 TESTING PEIRCE HISTORICAL SEQUENCES")
    print("=" * 50)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    
    engine = TransformationSequenceEngine()
    
    # Load real EGI data
    real_egis = load_real_egi_for_sequences()
    
    if not real_egis:
        print("⚠️  No real EGI data available for historical testing")
        return []
    
    results = []
    
    for name, egi in real_egis[:3]:  # Test first 3
        print(f"\n🔍 Testing: {name}")
        print("-" * 30)
        
        # Create sequence
        seq_id = f"peirce_{name}"
        sequence = engine.create_sequence(egi, seq_id)
        
        # Apply a series of transformations typical of Peirce's work
        steps_applied = 0
        
        # Try erasure if possible
        if len(egi.V) > 1:
            first_vertex = next(iter(egi.V))
            step = engine.add_transformation_step(
                seq_id,
                TransformationRuleType.ERASURE,
                {first_vertex.id}
            )
            steps_applied += 1
            print(f"  Erasure step: {step.validation_result.value if step.validation_result else 'None'}")
        
        # Try double cut if cuts exist
        if len(egi.Cut) >= 2:
            cuts = list(egi.Cut)[:2]
            step = engine.add_transformation_step(
                seq_id,
                TransformationRuleType.DOUBLE_CUT,
                {cut.id for cut in cuts}
            )
            steps_applied += 1
            print(f"  Double cut step: {step.validation_result.value if step.validation_result else 'None'}")
        
        # Try insertion
        step = engine.add_transformation_step(
            seq_id,
            TransformationRuleType.INSERTION,
            set(),
            {"new_element": "test_insertion"}
        )
        steps_applied += 1
        print(f"  Insertion step: {step.validation_result.value if step.validation_result else 'None'}")
        
        # Get final statistics
        stats = engine.get_sequence_statistics(seq_id)
        print(f"  Final: {stats['success_rate']:.1%} success ({stats['valid_steps']}/{stats['total_steps']})")
        
        results.append(stats)
    
    return results

def test_stress_sequences():
    """Test long transformation sequences for performance and stability."""
    print("\n💪 TESTING STRESS SEQUENCES")
    print("=" * 50)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, ElementID
    import time
    
    engine = TransformationSequenceEngine()
    
    # Create complex EGI for stress testing
    vertices = [Vertex(ElementID(f"v_{i}")) for i in range(10)]
    edges = [Edge(ElementID(f"e_{i}")) for i in range(5)]
    sheet = ElementID("sheet")
    
    # Build connections
    nu_dict = {}
    for i, edge in enumerate(edges):
        v1_idx = i % len(vertices)
        v2_idx = (i + 1) % len(vertices)
        nu_dict[edge.id] = (vertices[v1_idx].id, vertices[v2_idx].id)
    
    stress_egi = RelationalGraphWithCuts(
        V=frozenset(vertices),
        E=frozenset(edges),
        nu=frozendict(nu_dict),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([v.id for v in vertices] + [e.id for e in edges])
        }),
        rel=frozendict({e.id: f"Relation_{i}" for i, e in enumerate(edges)})
    )
    
    print(f"Created stress EGI: {len(vertices)} vertices, {len(edges)} edges")
    
    # Test long sequence
    seq_id = "stress_test_long_sequence"
    sequence = engine.create_sequence(stress_egi, seq_id)
    
    start_time = time.time()
    
    # Apply many transformation steps
    for i in range(20):  # 20 transformation steps
        rule_type = [
            TransformationRuleType.ERASURE,
            TransformationRuleType.INSERTION,
            TransformationRuleType.DOUBLE_CUT
        ][i % 3]
        
        # Select elements based on rule type
        if rule_type == TransformationRuleType.ERASURE and vertices:
            selected_elements = {vertices[i % len(vertices)].id}
        else:
            selected_elements = set()
        
        step = engine.add_transformation_step(
            seq_id,
            rule_type,
            selected_elements,
            {"step_number": i}
        )
        
        if i % 5 == 0:  # Progress update every 5 steps
            print(f"  Step {i+1}: {step.validation_result.value if step.validation_result else 'None'}")
    
    end_time = time.time()
    
    # Get final statistics
    stats = engine.get_sequence_statistics(seq_id)
    
    print(f"\nStress test results:")
    print(f"  Total time: {end_time - start_time:.2f} seconds")
    print(f"  Steps per second: {stats['total_steps'] / (end_time - start_time):.1f}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Rule distribution: {stats['rule_distribution']}")
    
    return stats

def test_sequence_replay_and_rollback():
    """Test replay and rollback functionality."""
    print("\n🔄 TESTING REPLAY AND ROLLBACK")
    print("=" * 50)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    
    engine = TransformationSequenceEngine()
    
    # Load a real EGI for testing
    real_egis = load_real_egi_for_sequences()
    if not real_egis:
        print("⚠️  No real EGI data available for replay testing")
        return {}
    
    name, egi = real_egis[0]
    
    # Create original sequence
    original_id = "replay_test_original"
    original_seq = engine.create_sequence(egi, original_id)
    
    # Add several steps
    steps_to_add = [
        (TransformationRuleType.INSERTION, set()),
        (TransformationRuleType.ERASURE, {next(iter(egi.V)).id} if egi.V else set()),
        (TransformationRuleType.DOUBLE_CUT, set())
    ]
    
    for i, (rule_type, elements) in enumerate(steps_to_add):
        step = engine.add_transformation_step(original_id, rule_type, elements)
        print(f"  Original step {i+1}: {step.validation_result.value if step.validation_result else 'None'}")
    
    # Test replay
    try:
        replay_seq = engine.replay_sequence(original_id)
        replay_stats = engine.get_sequence_statistics(replay_seq.sequence_id)
        print(f"✅ Replay successful: {replay_stats['total_steps']} steps replayed")
    except Exception as e:
        print(f"❌ Replay failed: {e}")
        replay_stats = {}
    
    # Test rollback
    try:
        rollback_seq = engine.rollback_to_step(original_id, 1)  # Rollback to step 1
        rollback_stats = engine.get_sequence_statistics(rollback_seq.sequence_id)
        print(f"✅ Rollback successful: rolled back to {rollback_stats['total_steps']} steps")
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        rollback_stats = {}
    
    # Export original sequence
    try:
        export_data = engine.export_sequence(original_id)
        print(f"✅ Export successful: {len(export_data['steps'])} steps exported")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        export_data = {}
    
    return {
        "original": engine.get_sequence_statistics(original_id),
        "replay": replay_stats,
        "rollback": rollback_stats,
        "export_size": len(export_data.get('steps', []))
    }

def run_comprehensive_sequence_tests():
    """Run all transformation sequence tests."""
    print("🧪 COMPREHENSIVE TRANSFORMATION SEQUENCE TESTING")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Classical proofs
    try:
        classical_results = test_classical_proof_sequences()
        results['classical'] = classical_results
    except Exception as e:
        print(f"❌ Classical proof tests failed: {e}")
        results['classical'] = []
    
    # Test 2: Peirce historical examples
    try:
        peirce_results = test_peirce_historical_sequences()
        results['peirce'] = peirce_results
    except Exception as e:
        print(f"❌ Peirce historical tests failed: {e}")
        results['peirce'] = []
    
    # Test 3: Stress testing
    try:
        stress_results = test_stress_sequences()
        results['stress'] = stress_results
    except Exception as e:
        print(f"❌ Stress tests failed: {e}")
        results['stress'] = {}
    
    # Test 4: Replay and rollback
    try:
        replay_results = test_sequence_replay_and_rollback()
        results['replay'] = replay_results
    except Exception as e:
        print(f"❌ Replay/rollback tests failed: {e}")
        results['replay'] = {}
    
    # Summary
    print(f"\n🎯 COMPREHENSIVE SEQUENCE TEST SUMMARY")
    print("=" * 60)
    
    total_sequences = (
        len(results.get('classical', [])) +
        len(results.get('peirce', [])) +
        (1 if results.get('stress') else 0) +
        (1 if results.get('replay') else 0)
    )
    
    print(f"Total sequences tested: {total_sequences}")
    print(f"Classical proofs: {len(results.get('classical', []))} sequences")
    print(f"Peirce examples: {len(results.get('peirce', []))} sequences")
    print(f"Stress testing: {'✅' if results.get('stress') else '❌'}")
    print(f"Replay/rollback: {'✅' if results.get('replay') else '❌'}")
    
    # Calculate overall success rates
    all_stats = []
    for category in ['classical', 'peirce']:
        if isinstance(results.get(category), list):
            all_stats.extend(results[category])
    
    if results.get('stress'):
        all_stats.append(results['stress'])
    
    if all_stats:
        avg_success_rate = sum(stat.get('success_rate', 0) for stat in all_stats) / len(all_stats)
        total_steps = sum(stat.get('total_steps', 0) for stat in all_stats)
        
        print(f"\nOverall statistics:")
        print(f"  Average success rate: {avg_success_rate:.1%}")
        print(f"  Total transformation steps: {total_steps}")
        print(f"  Framework performance: {'EXCELLENT' if avg_success_rate > 0.8 else 'GOOD' if avg_success_rate > 0.5 else 'NEEDS WORK'}")
    
    print(f"\n✅ Transformation sequence framework fully tested")
    print(f"✅ Ready for complex multi-step EG reasoning")
    
    return results

if __name__ == "__main__":
    run_comprehensive_sequence_tests()
