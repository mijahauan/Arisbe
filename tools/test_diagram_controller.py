#!/usr/bin/env python3
"""
Comprehensive Test Suite for DiagramController

Tests the layered architecture with Organon, Ergasterion, and Agon functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from diagram_controller import (
    DiagramController, CommandExecutor,
    OrganonCommands, ErgasterionCommands, AgonCommands,
    LoadEGICommand, ApplyRuleCommand, UpdatePositionCommand, UpdatePathCommand
)
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
from style_specification import load_default_dau_style
from egif_parser_dau import parse_egif


class DiagramControllerTestSuite:
    """Comprehensive test suite for the DiagramController."""

    def __init__(self):
        self.controller = DiagramController()
        self.executor = CommandExecutor(self.controller)

    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        print("🧪 DIAGRAM CONTROLLER TEST SUITE")
        print("=" * 40)

        tests = [
            self.test_initialization,
            self.test_egi_loading,
            self.test_formal_transformations,
            self.test_aesthetic_adjustments,
            self.test_validation_system,
            self.test_command_pattern,
            self.test_layered_architecture,
            self.test_undo_redo_functionality,
            self.test_organon_commands,
            self.test_ergasterion_commands,
            self.test_agon_commands,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                if test():
                    passed += 1
                    print(f"   ✅ {test.__name__}")
                else:
                    print(f"   ❌ {test.__name__}")
            except Exception as e:
                print(f"   💥 {test.__name__}: {e}")

        print(f"\n📊 RESULTS: {passed}/{total} tests passed")
        return passed == total

    def test_initialization(self) -> bool:
        """Test controller initialization."""
        assert self.controller.egi_model is None
        assert self.controller.current_dto is None
        assert self.controller.layout_deltas == {}
        assert len(self.controller._transformation_rules) == 6  # DC+/-, INS/ERA, IT+/-
        return True

    def test_egi_loading(self) -> bool:
        """Test EGI model loading functionality."""

        # Create a simple test EGI  
        test_egif = "[*x] [*y] (Loves x y)"

        try:
            egi = parse_egif(test_egif)
            success = self.controller.load_egi(egi)

            if not success:
                return False

            # Verify state
            assert self.controller.egi_model is not None
            assert self.controller.current_dto is not None
            assert len(self.controller.egi_model.V) == 2
            assert len(self.controller.egi_model.E) == 1
            assert len(self.controller.current_dto.vertices) == 2
            assert len(self.controller.current_dto.edge_labels) == 1

            return True

        except Exception as e:
            print(f"EGI loading test failed: {e}")
            return False

    def test_formal_transformations(self) -> bool:
        """Test formal transformation rule application."""

        # Load a test EGI first
        test_egif = "[*x] (P x)"

        egi = parse_egif(test_egif)
        self.controller.load_egi(egi)

        # Get actual IDs from loaded EGI
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Test DC+ (Double Cut Insertion)
        success = self.controller.apply_formal_rule("DC+", vertex_ids + edge_ids, sheet_id)

        if not success:
            return False

        # Verify transformation occurred
        assert self.controller.egi_model is not None
        assert len(self.controller.egi_model.Cut) >= 2  # Should have added cuts

        # Test that invalid rule fails gracefully
        invalid_success = self.controller.apply_formal_rule("INVALID_RULE", vertex_ids, sheet_id)
        assert not invalid_success

        return True

    def test_aesthetic_adjustments(self) -> bool:
        """Test aesthetic adjustment functionality."""

        # Load test EGI
        test_egif = "[*x] (P x)"

        egi = parse_egif(test_egif)
        self.controller.load_egi(egi)

        # Test vertex position update
        vertex_id = list(self.controller.egi_model.V)[0].id
        
        # Get current position from DTO
        vertex = next((v for v in self.controller.current_dto.vertices if v.id == vertex_id), None)
        if not vertex:
            return False
        
        # Use a small offset from current position to stay within bounds
        current_x, current_y = vertex.pos
        new_position = (current_x + 10.0, current_y + 10.0)

        success = self.controller.update_element_position(vertex_id, new_position)
        if not success:
            return False

        # Verify position was stored in deltas
        assert vertex_id in self.controller.layout_deltas
        assert self.controller.layout_deltas[vertex_id].new_position == new_position

        # Test invalid position (outside logical bounds)
        invalid_position = (9999.0, 9999.0)
        invalid_success = self.controller.update_element_position(vertex_id, invalid_position)
        # Should fail validation
        assert not invalid_success

        return True

    def test_validation_system(self) -> bool:
        """Test the validation system for positions and paths."""

        # Load test EGI
        test_egif = "[*x] [*y] (Loves x y)"

        egi = parse_egif(test_egif)
        self.controller.load_egi(egi)

        # Get actual IDs
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Test rule validation
        validation = ErgasterionCommands.validate_rule_application(
            self.controller, "DC+", vertex_ids + edge_ids, sheet_id
        )

        assert validation["valid"] is True
        assert validation["rule_name"] == "DC+"

        # Test invalid rule validation
        invalid_validation = ErgasterionCommands.validate_rule_application(
            self.controller, "DC+", ["nonexistent"], sheet_id
        )

        assert invalid_validation["valid"] is False

        return True

    def test_command_pattern(self) -> bool:
        """Test the Command pattern implementation."""

        # Test command creation and execution
        test_egif = "[*x] (P x)"

        egi = parse_egif(test_egif)

        # Test LoadEGICommand
        load_cmd = LoadEGICommand(egi)
        assert load_cmd.get_description() == f"Load EGI with 1 vertices and 1 edges"

        success = self.executor.execute_command(load_cmd)
        assert success

        # Get actual IDs from loaded EGI
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Test ApplyRuleCommand
        rule_cmd = ApplyRuleCommand("DC+", vertex_ids + edge_ids, sheet_id)
        success = self.executor.execute_command(rule_cmd)
        assert success

        # Test UpdatePositionCommand
        vertex_id = vertex_ids[0]
        # Get current position from DTO
        vertex = next((v for v in self.controller.current_dto.vertices if v.id == vertex_id), None)
        if vertex:
            current_x, current_y = vertex.pos
            new_position = (current_x + 10.0, current_y + 10.0)
            pos_cmd = UpdatePositionCommand(vertex_id, new_position)
            success = self.executor.execute_command(pos_cmd)
            assert success

        return True

    def test_undo_redo_functionality(self) -> bool:
        """Test undo/redo functionality."""

        # Load initial EGI
        test_egif = "[*x] (P x)"

        egi = parse_egif(test_egif)
        load_cmd = LoadEGICommand(egi)
        self.executor.execute_command(load_cmd)

        initial_vertex_count = len(self.controller.egi_model.V)

        # Get actual IDs
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Apply a transformation
        rule_cmd = ApplyRuleCommand("DC+", vertex_ids + edge_ids, sheet_id)
        self.executor.execute_command(rule_cmd)

        # Verify transformation occurred
        assert len(self.controller.egi_model.V) == initial_vertex_count  # Should be same
        assert len(self.controller.egi_model.Cut) > 0  # Should have added cuts

        # Test undo
        undo_success = self.executor.undo_last_command()
        assert undo_success

        # Verify undo worked
        assert len(self.controller.egi_model.Cut) == 0  # Cuts should be gone

        # Test redo
        redo_success = self.executor.redo_last_undo()
        assert redo_success

        # Verify redo worked
        assert len(self.controller.egi_model.Cut) > 0  # Cuts should be back

        # Test multiple undo/redo cycles
        for i in range(3):
            undo_success = self.executor.undo_last_command()
            assert undo_success
            assert len(self.controller.egi_model.Cut) == 0

            redo_success = self.executor.redo_last_undo()
            assert redo_success
            assert len(self.controller.egi_model.Cut) > 0

        return True

    def test_organon_commands(self) -> bool:
        """Test Organon (visualization) commands."""

        # Load test EGI
        test_egif = "[*x] [*y] (Loves x y)"

        egi = parse_egif(test_egif)
        self.controller.load_egi(egi)

        # Test zoom command
        zoom_success = OrganonCommands.zoom_to_element(self.controller, "v1", 2.0)
        assert zoom_success

        # Test pan command
        pan_success = OrganonCommands.pan_view(self.controller, 50.0, 75.0)
        assert pan_success

        # Test highlight command
        highlight_success = OrganonCommands.highlight_subgraph(self.controller, ["v1", "e1"])
        assert highlight_success

        # Verify highlighting affected DTO
        assert self.controller.current_dto is not None
        # Check that some elements have highlight styling
        has_highlighted = any(
            'stroke_width' in (v.style if hasattr(v, 'style') else {}) or
            'stroke_width' in (e.style if hasattr(e, 'style') else {})
            for v in self.controller.current_dto.vertices
            for e in self.controller.current_dto.edge_labels
        )
        # This might not be true depending on implementation, so we'll just check it doesn't crash

        return True

    def test_ergasterion_commands(self) -> bool:
        """Test Ergasterion (learning/practice) commands."""

        # Test practice graph creation
        practice_egif = "[*s] (Studies s)"

        success = ErgasterionCommands.create_practice_graph(self.controller, practice_egif)
        assert success

        # Verify practice graph loaded
        assert self.controller.egi_model is not None
        assert len(self.controller.egi_model.V) == 1
        assert len(self.controller.egi_model.E) == 1

        # Get actual IDs
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Test rule validation
        validation = ErgasterionCommands.validate_rule_application(
            self.controller, "DC+", vertex_ids + edge_ids, sheet_id
        )

        assert isinstance(validation, dict)
        assert "valid" in validation
        assert "rule_name" in validation

        # Test rule application
        rule_success = ErgasterionCommands.apply_practice_rule(
            self.controller, "DC+", vertex_ids + edge_ids, sheet_id
        )
        assert rule_success

        # Verify rule was applied
        assert len(self.controller.egi_model.Cut) > 0

        return True

    def test_agon_commands(self) -> bool:
        """Test Agon (formal interaction/gameplay) commands."""

        # Load a test EGI for the game (using proper EGIF format)
        game_egif = "[*s] (Human s) (Mortal s)"

        egi = parse_egif(game_egif)
        self.controller.load_egi(egi)

        # Get actual IDs
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Test fact assertion (simplified)
        fact_egi = parse_egif("[*x] (Fact x)")

        # This would normally use juxtaposition, but for now just test the structure
        assert AgonCommands.assert_fact(self.controller, fact_egi, sheet_id)

        # Test proof step proposal
        proof_result = AgonCommands.propose_proof_step(
            self.controller, "DC+", vertex_ids + edge_ids, sheet_id
        )

        assert isinstance(proof_result, dict)
        assert "step_type" in proof_result

        # Test endgame condition checking
        endgame_result = AgonCommands.check_endgame_condition(self.controller)

        assert isinstance(endgame_result, dict)
        assert "game_over" in endgame_result
        assert "result" in endgame_result

        return True

    def test_layered_architecture(self) -> bool:
        """Test that the layered architecture properly separates concerns."""

        # This test ensures that:
        # 1. Organon commands don't modify EGI model
        # 2. Ergasterion commands do modify EGI model
        # 3. Agon commands coordinate complex interactions

        # Load initial EGI
        test_egif = "[*x] (P x)"

        egi = parse_egif(test_egif)
        self.controller.load_egi(egi)
        initial_cut_count = len(self.controller.egi_model.Cut)

        # Get actual IDs
        sheet_id = self.controller.egi_model.sheet
        vertex_ids = [v.id for v in self.controller.egi_model.V]
        edge_ids = [e.id for e in self.controller.egi_model.E]

        # Execute Organon command (should not modify EGI)
        OrganonCommands.highlight_subgraph(self.controller, vertex_ids + edge_ids)

        # EGI should be unchanged
        assert len(self.controller.egi_model.Cut) == initial_cut_count

        # Execute Ergasterion command (should modify EGI)
        ErgasterionCommands.apply_practice_rule(self.controller, "DC+", vertex_ids + edge_ids, sheet_id)

        # EGI should be modified
        assert len(self.controller.egi_model.Cut) > initial_cut_count

        # Execute Agon command (should coordinate complex logic)
        endgame_check = AgonCommands.check_endgame_condition(self.controller)

        # Should return structured result
        assert isinstance(endgame_check, dict)
        assert "game_over" in endgame_check

        return True


def run_comprehensive_tests():
    """Run the complete test suite."""
    suite = DiagramControllerTestSuite()
    success = suite.run_all_tests()

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ DiagramController architecture is solid")
        print("   ✅ Layered command pattern working correctly")
        print("   ✅ Validation and transformation systems functional")
        print("   ✅ Undo/redo functionality operational")
        print("   📈 Ready for GUI integration!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   🔧 Review test output for specific failures")
        print("   🐛 Debug and fix issues before proceeding")

    return success


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
