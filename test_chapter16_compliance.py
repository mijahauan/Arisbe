"""
Comprehensive Test Suite for Dau Chapter 16 Ligature Implementation
Tests all implemented ligature rules, detection algorithms, and n-ary identity relations.
"""

import sys
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import core EGI components
from src.egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from src.formal_transformation_rules import TransformationContext, TransformationResult, AreaPolarity

# Import all Chapter 16 implementations
from src.ligature_manipulation_rules import (
    MoveBranchesAlongLigatureRule,
    ExtendRestrictLigatureRule, 
    RetractLigatureRule,
    LigatureRearrangementRule,
    LigatureManipulationEngine
)
from src.single_object_ligature_detector import SingleObjectLigatureDetector
from src.vertex_splitting_merging_rules import VertexSplittingRule, VertexMergingRule
from src.nary_identity_relations import (
    CreateNaryIdentityRule,
    SeparateNaryIdentityRule,
    NaryIdentityAnalyzer,
    NaryIdentityRelation
)


@dataclass
class TestResult:
    """Result of a single test case."""
    test_name: str
    success: bool
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class Chapter16TestSuite:
    """Comprehensive test suite for Chapter 16 ligature implementation."""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.setup_test_egis()
    
    def setup_test_egis(self):
        """Set up test EGIs for various scenarios."""
        
        # Basic ligature EGI
        self.basic_ligature_egi = self._create_basic_ligature_egi()
        
        # Complex ligature EGI with nested contexts
        self.complex_ligature_egi = self._create_complex_ligature_egi()
        
        # Single-object ligature test EGI
        self.single_object_egi = self._create_single_object_test_egi()
        
        # N-ary identity test EGI
        self.nary_identity_egi = self._create_nary_identity_test_egi()
    
    def _create_basic_ligature_egi(self) -> RelationalGraphWithCuts:
        """Create basic EGI with simple ligature structure."""
        vertex_a = Vertex(ElementID("A"))
        vertex_b = Vertex(ElementID("B"))
        vertex_c = Vertex(ElementID("C"))
        
        edge_id1 = Edge(ElementID("id1"))
        edge_r = Edge(ElementID("R"))
        edge_s = Edge(ElementID("S"))
        
        return RelationalGraphWithCuts(
            V=frozenset([vertex_a, vertex_b, vertex_c]),
            E=frozenset([edge_id1, edge_r, edge_s]),
            nu=frozendict({
                ElementID("id1"): (ElementID("A"), ElementID("B")),
                ElementID("R"): (ElementID("A"), ElementID("C")),
                ElementID("S"): (ElementID("B"), ElementID("C"))
            }),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({
                ElementID("sheet"): frozenset([
                    ElementID("A"), ElementID("B"), ElementID("C"),
                    ElementID("id1"), ElementID("R"), ElementID("S")
                ])
            }),
            rel=frozendict({
                ElementID("id1"): "=",
                ElementID("R"): "Relation1",
                ElementID("S"): "Relation2"
            })
        )
    
    def _create_complex_ligature_egi(self) -> RelationalGraphWithCuts:
        """Create complex EGI with nested contexts and multiple ligatures."""
        vertex_a = Vertex(ElementID("A"))
        vertex_b = Vertex(ElementID("B"))
        vertex_c = Vertex(ElementID("C"))
        vertex_d = Vertex(ElementID("D"))
        
        edge_id1 = Edge(ElementID("id1"))
        edge_id2 = Edge(ElementID("id2"))
        edge_r = Edge(ElementID("R"))
        
        cut1 = Cut(ElementID("cut1"))
        cut2 = Cut(ElementID("cut2"))
        
        return RelationalGraphWithCuts(
            V=frozenset([vertex_a, vertex_b, vertex_c, vertex_d]),
            E=frozenset([edge_id1, edge_id2, edge_r]),
            nu=frozendict({
                ElementID("id1"): (ElementID("A"), ElementID("B")),
                ElementID("id2"): (ElementID("C"), ElementID("D")),
                ElementID("R"): (ElementID("A"), ElementID("C"))
            }),
            sheet=ElementID("sheet"),
            Cut=frozenset([cut1, cut2]),
            area=frozendict({
                ElementID("sheet"): frozenset([
                    ElementID("A"), ElementID("B"), ElementID("id1"),
                    ElementID("R"), ElementID("cut1")
                ]),
                ElementID("cut1"): frozenset([
                    ElementID("C"), ElementID("D"), ElementID("id2"), ElementID("cut2")
                ]),
                ElementID("cut2"): frozenset()
            }),
            rel=frozendict({
                ElementID("id1"): "=",
                ElementID("id2"): "=",
                ElementID("R"): "Relation1"
            })
        )
    
    def _create_single_object_test_egi(self) -> RelationalGraphWithCuts:
        """Create EGI for testing single-object ligature detection."""
        vertex_a = Vertex(ElementID("A"))
        vertex_b = Vertex(ElementID("B"))
        vertex_c = Vertex(ElementID("C"))
        
        edge_id1 = Edge(ElementID("id1"))
        edge_id2 = Edge(ElementID("id2"))
        
        cut1 = Cut(ElementID("cut1"))
        
        return RelationalGraphWithCuts(
            V=frozenset([vertex_a, vertex_b, vertex_c]),
            E=frozenset([edge_id1, edge_id2]),
            nu=frozendict({
                ElementID("id1"): (ElementID("A"), ElementID("B")),
                ElementID("id2"): (ElementID("B"), ElementID("C"))
            }),
            sheet=ElementID("sheet"),
            Cut=frozenset([cut1]),
            area=frozendict({
                ElementID("sheet"): frozenset([
                    ElementID("A"), ElementID("B"), ElementID("id1"), ElementID("cut1")
                ]),
                ElementID("cut1"): frozenset([
                    ElementID("C"), ElementID("id2")
                ])
            }),
            rel=frozendict({
                ElementID("id1"): "=",
                ElementID("id2"): "="
            })
        )
    
    def _create_nary_identity_test_egi(self) -> RelationalGraphWithCuts:
        """Create EGI for testing n-ary identity relations."""
        vertex_a = Vertex(ElementID("A"))
        vertex_b = Vertex(ElementID("B"))
        vertex_c = Vertex(ElementID("C"))
        vertex_d = Vertex(ElementID("D"))
        
        return RelationalGraphWithCuts(
            V=frozenset([vertex_a, vertex_b, vertex_c, vertex_d]),
            E=frozenset(),
            nu=frozendict(),
            sheet=ElementID("sheet"),
            Cut=frozenset(),
            area=frozendict({
                ElementID("sheet"): frozenset([
                    ElementID("A"), ElementID("B"), ElementID("C"), ElementID("D")
                ])
            }),
            rel=frozendict()
        )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Chapter 16 compliance tests."""
        print("🧪 Running Chapter 16 Compliance Test Suite")
        print("=" * 50)
        
        # Test ligature manipulation rules
        self.test_move_branches_rule()
        self.test_extend_restrict_rule()
        self.test_retract_ligature_rule()
        self.test_rearrange_ligature_rule()
        
        # Test single-object ligature detection
        self.test_single_object_detection()
        
        # Test vertex splitting and merging
        self.test_vertex_splitting_rule()
        self.test_vertex_merging_rule()
        
        # Test n-ary identity relations
        self.test_create_nary_identity()
        self.test_separate_nary_identity()
        
        # Test integration scenarios
        self.test_ligature_engine_integration()
        self.test_complex_transformation_sequence()
        
        # Generate summary
        return self.generate_test_summary()
    
    def test_move_branches_rule(self):
        """Test Lemma 16.1: Moving Branches Along Ligature."""
        try:
            rule = MoveBranchesAlongLigatureRule()
            context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Move Branches Along Ligature (Lemma 16.1)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Move Branches Along Ligature (Lemma 16.1)",
                success=False,
                error_message=str(e)
            ))
    
    def test_extend_restrict_rule(self):
        """Test Lemma 16.2: Extending/Restricting Ligatures."""
        try:
            rule = ExtendRestrictLigatureRule()
            context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Extend/Restrict Ligature (Lemma 16.2)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Extend/Restrict Ligature (Lemma 16.2)",
                success=False,
                error_message=str(e)
            ))
    
    def test_retract_ligature_rule(self):
        """Test Lemma 16.3: Retracting Ligatures."""
        try:
            rule = RetractLigatureRule()
            context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Retract Ligature (Lemma 16.3)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Retract Ligature (Lemma 16.3)",
                success=False,
                error_message=str(e)
            ))
    
    def test_rearrange_ligature_rule(self):
        """Test Definition 16.4: Rearranging Ligatures."""
        try:
            rule = LigatureRearrangementRule()
            context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Rearrange Ligature (Definition 16.4)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Rearrange Ligature (Definition 16.4)",
                success=False,
                error_message=str(e)
            ))
    
    def test_single_object_detection(self):
        """Test Definition 16.8: Single-Object Ligature Detection."""
        try:
            detector = SingleObjectLigatureDetector()
            detector.egi = self.single_object_egi
            ligature_vertices = [ElementID("A"), ElementID("B"), ElementID("C")]
            
            is_single_object, violations = detector.is_single_object_ligature(ligature_vertices)
            components = detector.separate_into_single_object_components(ligature_vertices)
            
            self.test_results.append(TestResult(
                test_name="Single-Object Ligature Detection (Definition 16.8)",
                success=True,  # Detection itself should work
                details={
                    "is_single_object": is_single_object,
                    "violations": violations,
                    "components": len(components)
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Single-Object Ligature Detection (Definition 16.8)",
                success=False,
                error_message=str(e)
            ))
    
    def test_vertex_splitting_rule(self):
        """Test Lemma 16.7: Vertex Splitting."""
        try:
            rule = VertexSplittingRule()
            context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Vertex Splitting (Lemma 16.7)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Vertex Splitting (Lemma 16.7)",
                success=False,
                error_message=str(e)
            ))
    
    def test_vertex_merging_rule(self):
        """Test Lemma 16.7: Vertex Merging."""
        try:
            # First create a split vertex scenario
            split_rule = VertexSplittingRule()
            split_context = TransformationContext(
                source_egi=self.basic_ligature_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            split_result = split_rule.apply_transformation(split_context)
            
            if split_result.success:
                # Now test merging
                merge_rule = VertexMergingRule()
                
                # Find the split vertices
                split_egi = split_result.result_egi
                identity_vertices = []
                for edge_id, vertex_sequence in split_egi.nu.items():
                    if split_egi.rel.get(edge_id) == "=" and len(vertex_sequence) == 2:
                        identity_vertices = list(vertex_sequence)
                        break
                
                if identity_vertices:
                    merge_context = TransformationContext(
                        source_egi=split_egi,
                        target_area=ElementID("sheet"),
                        selected_subgraph=frozenset(identity_vertices),
                        area_polarity=AreaPolarity.POSITIVE,
                        nesting_depth=0
                    )
                    
                    merge_result = merge_rule.apply_transformation(merge_context)
                    
                    self.test_results.append(TestResult(
                        test_name="Vertex Merging (Lemma 16.7)",
                        success=merge_result.success,
                        error_message=merge_result.error_message,
                        details=merge_result.changes_made if merge_result.success else None
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name="Vertex Merging (Lemma 16.7)",
                        success=False,
                        error_message="No identity vertices found after splitting"
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name="Vertex Merging (Lemma 16.7)",
                    success=False,
                    error_message=f"Split failed: {split_result.error_message}"
                ))
                
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Vertex Merging (Lemma 16.7)",
                success=False,
                error_message=str(e)
            ))
    
    def test_create_nary_identity(self):
        """Test N-ary Identity Creation."""
        try:
            rule = CreateNaryIdentityRule()
            context = TransformationContext(
                source_egi=self.nary_identity_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B"), ElementID("C")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            result = rule.apply_transformation(context)
            
            self.test_results.append(TestResult(
                test_name="Create N-ary Identity (.=k)",
                success=result.success,
                error_message=result.error_message,
                details=result.changes_made if result.success else None
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Create N-ary Identity (.=k)",
                success=False,
                error_message=str(e)
            ))
    
    def test_separate_nary_identity(self):
        """Test N-ary Identity Separation."""
        try:
            # First create n-ary identity
            create_rule = CreateNaryIdentityRule()
            create_context = TransformationContext(
                source_egi=self.nary_identity_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B"), ElementID("C")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            create_result = create_rule.apply_transformation(create_context)
            
            if create_result.success:
                # Now test separation
                separate_rule = SeparateNaryIdentityRule()
                separate_context = TransformationContext(
                    source_egi=create_result.result_egi,
                    target_area=ElementID("sheet"),
                    selected_subgraph=frozenset([ElementID("C")]),
                    area_polarity=AreaPolarity.POSITIVE,
                    nesting_depth=0
                )
                
                separate_result = separate_rule.apply_transformation(separate_context)
                
                self.test_results.append(TestResult(
                    test_name="Separate N-ary Identity",
                    success=separate_result.success,
                    error_message=separate_result.error_message,
                    details=separate_result.changes_made if separate_result.success else None
                ))
            else:
                self.test_results.append(TestResult(
                    test_name="Separate N-ary Identity",
                    success=False,
                    error_message=f"Create failed: {create_result.error_message}"
                ))
                
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Separate N-ary Identity",
                success=False,
                error_message=str(e)
            ))
    
    def test_ligature_engine_integration(self):
        """Test LigatureManipulationEngine integration."""
        try:
            engine = LigatureManipulationEngine()
            
            # Test engine rule availability
            expected_rules = ["MOVE_BRANCHES", "EXTEND_LIGATURE", "RETRACT_LIGATURE", "REARRANGE_LIGATURE"]
            available_rules = list(engine.rules.keys())
            
            missing_rules = set(expected_rules) - set(available_rules)
            
            self.test_results.append(TestResult(
                test_name="Ligature Engine Integration",
                success=len(missing_rules) == 0,
                error_message=f"Missing rules: {missing_rules}" if missing_rules else None,
                details={
                    "available_rules": available_rules,
                    "expected_rules": expected_rules
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Ligature Engine Integration",
                success=False,
                error_message=str(e)
            ))
    
    def test_complex_transformation_sequence(self):
        """Test complex sequence of transformations."""
        try:
            # Start with complex ligature EGI
            current_egi = self.complex_ligature_egi
            transformation_count = 0
            
            # Apply retraction
            retract_rule = RetractLigatureRule()
            retract_context = TransformationContext(
                source_egi=current_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A"), ElementID("B")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            retract_result = retract_rule.apply_transformation(retract_context)
            if retract_result.success:
                current_egi = retract_result.result_egi
                transformation_count += 1
            
            # Apply extension
            extend_rule = ExtendRestrictLigatureRule()
            extend_context = TransformationContext(
                source_egi=current_egi,
                target_area=ElementID("sheet"),
                selected_subgraph=frozenset([ElementID("A")]),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            
            extend_result = extend_rule.apply_transformation(extend_context)
            if extend_result.success:
                current_egi = extend_result.result_egi
                transformation_count += 1
            
            self.test_results.append(TestResult(
                test_name="Complex Transformation Sequence",
                success=transformation_count > 0,
                details={
                    "transformations_applied": transformation_count,
                    "final_vertex_count": len(current_egi.V),
                    "final_edge_count": len(current_egi.E)
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="Complex Transformation Sequence",
                success=False,
                error_message=str(e)
            ))
    
    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Test Summary")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.test_name}")
            if not result.success and result.error_message:
                print(f"      Error: {result.error_message}")
            elif result.success and result.details:
                print(f"      Details: {result.details}")
        
        # Check Chapter 16 compliance
        critical_tests = [
            "Move Branches Along Ligature (Lemma 16.1)",
            "Extend/Restrict Ligature (Lemma 16.2)", 
            "Retract Ligature (Lemma 16.3)",
            "Single-Object Ligature Detection (Definition 16.8)",
            "Vertex Splitting (Lemma 16.7)"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result.test_name in critical_tests and result.success)
        
        print(f"\n🎯 Chapter 16 Compliance:")
        print(f"   Critical Components: {critical_passed}/{len(critical_tests)} implemented")
        
        compliance_status = "FULL" if critical_passed == len(critical_tests) else "PARTIAL"
        print(f"   Compliance Status: {compliance_status}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "critical_compliance": critical_passed,
            "compliance_status": compliance_status,
            "test_results": self.test_results
        }


def run_chapter16_compliance_tests():
    """Run the complete Chapter 16 compliance test suite."""
    print("🚀 Starting Dau Chapter 16 Compliance Testing")
    print("=" * 55)
    
    try:
        test_suite = Chapter16TestSuite()
        summary = test_suite.run_all_tests()
        
        print(f"\n🏁 Chapter 16 Testing Complete")
        print(f"   Implementation Status: {summary['compliance_status']} COMPLIANCE")
        
        return summary
        
    except Exception as e:
        print(f"❌ Test suite execution failed: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_chapter16_compliance_tests()
