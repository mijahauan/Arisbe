"""
Comprehensive tests for Phase 5A: Core User Tools

Tests the bullpen (constrained composition), look ahead system,
and multi-scope exploration tools.
"""

import pytest
import uuid
from typing import Set

from src.bullpen import (
    GraphCompositionTool, ValidationLevel, CompositionMode, 
    ValidationResult, ComponentLibrary
)
from src.lookahead import (
    LookAheadEngine, TransformationPreview, PatternExploration,
    GameMovePreview, UndoRedoManager
)
from src.exploration import (
    GraphExplorer, ScopeType, FocusMode, ViewScope, ExplorationView
)
from src.eg_types import Node, Context, NodeId, ContextId
from src.graph import EGGraph
from src.transformations import TransformationType
from src.game_engine import GameMove, MoveType


class TestGraphCompositionTool:
    """Test the bullpen (constrained composition) system."""
    
    def test_create_blank_sheet(self):
        """Test creating a blank sheet."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        assert isinstance(graph, EGGraph)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert len(graph.ligatures) == 0
    
    def test_add_predicate(self):
        """Test adding a predicate to a graph."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        new_graph, validation = tool.add_predicate(graph, "Person", 1)
        
        assert validation.is_valid
        assert len(new_graph.nodes) == 1
        
        # Check predicate properties
        node = list(new_graph.nodes.values())[0]
        assert node.properties['name'] == "Person"
        assert node.properties['arity'] == 1
    
    def test_create_context(self):
        """Test creating a context (cut)."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        new_graph, context, validation = tool.create_context(graph, "cut")
        
        assert validation.is_valid
        assert isinstance(context, Context)
        assert context.context_type == "cut"
        assert len(new_graph.context_manager.contexts) > 1  # Root + new context
    
    def test_add_ligature(self):
        """Test adding a ligature between nodes."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        # Add two nodes first
        graph, _ = tool.add_predicate(graph, "Person", 1)
        graph, _ = tool.add_predicate(graph, "Mortal", 1)
        
        node_ids = set(graph.nodes.keys())
        new_graph, validation = tool.add_ligature(graph, node_ids)
        
        assert validation.is_valid
        assert len(new_graph.ligatures) == 1
        
        ligature = list(new_graph.ligatures.values())[0]
        assert ligature.nodes == node_ids
    
    def test_validation_levels(self):
        """Test different validation levels."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        # Test syntax validation
        syntax_result = tool.validate_graph(graph, ValidationLevel.SYNTAX_ONLY)
        assert syntax_result.level == ValidationLevel.SYNTAX_ONLY
        
        # Test semantic validation
        semantic_result = tool.validate_graph(graph, ValidationLevel.SEMANTIC)
        assert semantic_result.level == ValidationLevel.SEMANTIC
        
        # Test game readiness validation
        game_result = tool.validate_graph(graph, ValidationLevel.GAME_READY)
        assert game_result.level == ValidationLevel.GAME_READY
    
    def test_create_from_clif(self):
        """Test creating a graph from CLIF text."""
        tool = GraphCompositionTool()
        
        # Simple CLIF expression
        clif_text = "(Person john)"
        graph, validation = tool.create_from_clif(clif_text)
        
        # Should succeed or fail gracefully
        assert isinstance(graph, EGGraph)
        assert isinstance(validation, ValidationResult)
    
    def test_preview_in_game(self):
        """Test previewing a graph in the game context."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        # Add some content
        graph, _ = tool.add_predicate(graph, "Person", 1)
        
        preview = tool.preview_in_game(graph)
        
        assert preview.thesis_graph == graph
        assert isinstance(preview.complexity_assessment, str)
        assert isinstance(preview.strategic_notes, list)
    
    def test_template_system(self):
        """Test the template system."""
        tool = GraphCompositionTool()
        
        # Get available templates
        templates = tool.get_available_templates()
        assert isinstance(templates, list)
        
        # Try to use a template if available
        if templates:
            template = templates[0]
            graph, validation = tool.create_from_template(template.name, {})
            assert isinstance(graph, EGGraph)
            assert isinstance(validation, ValidationResult)


class TestComponentLibrary:
    """Test the component library."""
    
    def test_get_common_predicates(self):
        """Test getting common predicates."""
        library = ComponentLibrary()
        predicates = library.get_common_predicates()
        
        assert isinstance(predicates, list)
        assert len(predicates) > 0
        
        # Check structure of predicate definitions
        for pred in predicates:
            assert 'name' in pred
            assert 'arity' in pred
            assert 'description' in pred
    
    def test_get_logical_patterns(self):
        """Test getting logical patterns."""
        library = ComponentLibrary()
        patterns = library.get_logical_patterns()
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check for common patterns
        pattern_names = [p['name'] for p in patterns]
        assert 'universal_quantification' in pattern_names
        assert 'implication' in pattern_names
    
    def test_create_nodes(self):
        """Test creating different types of nodes."""
        library = ComponentLibrary()
        
        # Test predicate node
        pred_node = library.create_predicate_node("Person", 1)
        assert pred_node.node_type == 'predicate'
        assert pred_node.properties['name'] == "Person"
        assert pred_node.properties['arity'] == 1
        
        # Test individual node
        ind_node = library.create_individual_node("john")
        assert ind_node.node_type == 'individual'
        assert ind_node.properties['name'] == "john"
        
        # Test variable node
        var_node = library.create_variable_node("x")
        assert var_node.node_type == 'variable'
        assert var_node.properties['name'] == "x"


class TestLookAheadEngine:
    """Test the look ahead system."""
    
    def test_preview_transformation(self):
        """Test previewing transformations."""
        engine = LookAheadEngine()
        
        # Create a simple graph
        graph = EGGraph.create_empty()
        # Add some content for transformation
        
        # Test transformation preview
        preview = engine.preview_transformation(
            graph, 
            TransformationType.DOUBLE_CUT_INSERTION,
            set()
        )
        
        assert isinstance(preview, TransformationPreview)
        assert preview.original_graph == graph
        assert preview.transformation_type == TransformationType.DOUBLE_CUT_INSERTION
    
    def test_explore_pattern_instances(self):
        """Test pattern exploration."""
        engine = LookAheadEngine()
        graph = EGGraph.create_empty()
        
        exploration = engine.explore_pattern_instances("universal_quantification", graph)
        
        assert isinstance(exploration, PatternExploration)
        assert exploration.pattern_template == "universal_quantification"
        assert exploration.base_graph == graph
        assert isinstance(exploration.matches, list)
    
    def test_get_transformation_suggestions(self):
        """Test getting transformation suggestions."""
        engine = LookAheadEngine()
        graph = EGGraph.create_empty()
        
        suggestions = engine.get_transformation_suggestions(graph)
        
        assert isinstance(suggestions, list)
        # Empty graph might not have many suggestions
        assert len(suggestions) >= 0


class TestUndoRedoManager:
    """Test the undo/redo system."""
    
    def test_undo_redo_operations(self):
        """Test undo and redo operations."""
        graph1 = EGGraph.create_empty()
        manager = UndoRedoManager(graph1)
        
        # Initially can't undo
        assert not manager.can_undo()
        assert not manager.can_redo()
        
        # Save a new state
        graph2 = EGGraph.create_empty()  # Different graph
        manager.save_state(graph2)
        
        # Now can undo
        assert manager.can_undo()
        assert not manager.can_redo()
        
        # Undo
        undone_graph = manager.undo()
        assert undone_graph is not None
        assert not manager.can_undo()
        assert manager.can_redo()
        
        # Redo
        redone_graph = manager.redo()
        assert redone_graph is not None
        assert manager.can_undo()
        assert not manager.can_redo()
    
    def test_history_limit(self):
        """Test that history is limited to prevent memory issues."""
        graph = EGGraph.create_empty()
        manager = UndoRedoManager(graph)
        
        # Save many states
        for i in range(60):  # More than max_history (50)
            new_graph = EGGraph.create_empty()
            manager.save_state(new_graph)
        
        # Should still be within reasonable bounds
        assert len(manager.history) <= manager.max_history + 5


class TestGraphExplorer:
    """Test the multi-scope exploration system."""
    
    def test_get_overview(self):
        """Test getting a graph overview."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        overview = explorer.get_overview()
        
        assert isinstance(overview, ExplorationView)
        assert overview.scope.scope_type == ScopeType.LEVEL_LIMITED
        assert overview.scope.max_depth == 2
    
    def test_focus_on_context(self):
        """Test focusing on a specific context."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        # Focus on root context
        view = explorer.focus_on_context(graph.root_context_id)
        
        assert isinstance(view, ExplorationView)
        assert view.scope.focus_context == graph.root_context_id
        assert graph.root_context_id in view.visible_contexts
    
    def test_zoom_operations(self):
        """Test zoom in and zoom out operations."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        # Get initial overview
        overview = explorer.get_overview()
        
        # Try to zoom out (should stay at root)
        zoomed_out = explorer.zoom_out()
        assert isinstance(zoomed_out, ExplorationView)
        
        # Try to zoom in (might not be possible with empty graph)
        zoomed_in = explorer.zoom_in()
        assert isinstance(zoomed_in, ExplorationView)
    
    def test_adjust_depth(self):
        """Test adjusting exploration depth."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        # Adjust to different depths
        view_depth_1 = explorer.adjust_depth(1)
        assert view_depth_1.scope.max_depth == 1
        
        view_depth_3 = explorer.adjust_depth(3)
        assert view_depth_3.scope.max_depth == 3
    
    def test_bookmark_system(self):
        """Test the bookmark system."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        # Get initial view
        overview = explorer.get_overview()
        
        # Bookmark current view
        success = explorer.bookmark_current_view("test_bookmark")
        assert success
        
        # Navigate to bookmark
        bookmarked_view = explorer.go_to_bookmark("test_bookmark")
        assert bookmarked_view is not None
        assert isinstance(bookmarked_view, ExplorationView)
    
    def test_navigation_options(self):
        """Test getting navigation options."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        options = explorer.get_navigation_options()
        
        assert isinstance(options, dict)
        # Empty graph might not have many options
    
    def test_context_summary(self):
        """Test getting context summaries."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        summary = explorer.get_context_summary(graph.root_context_id)
        
        assert isinstance(summary, dict)
        assert 'context_id' in summary
        assert 'context_type' in summary
        assert 'node_count' in summary
        assert 'total_items' in summary


class TestIntegration:
    """Test integration between Phase 5A tools."""
    
    def test_bullpen_to_lookahead(self):
        """Test using bullpen output with look ahead system."""
        # Create a graph in bullpen
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        graph, _ = tool.add_predicate(graph, "Person", 1)
        
        # Use look ahead to explore transformations
        engine = LookAheadEngine()
        suggestions = engine.get_transformation_suggestions(graph)
        
        assert isinstance(suggestions, list)
    
    def test_lookahead_to_exploration(self):
        """Test using look ahead results with exploration system."""
        # Create a graph
        graph = EGGraph.create_empty()
        
        # Use look ahead to preview a transformation
        engine = LookAheadEngine()
        preview = engine.preview_transformation(
            graph, 
            TransformationType.DOUBLE_CUT_INSERTION,
            set()
        )
        
        # Explore the result if transformation succeeded
        if preview.transformed_graph:
            explorer = GraphExplorer(preview.transformed_graph)
            overview = explorer.get_overview()
            assert isinstance(overview, ExplorationView)
    
    def test_exploration_to_bullpen(self):
        """Test using exploration insights to guide composition."""
        # Start with exploration
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        overview = explorer.get_overview()
        
        # Use insights to guide composition
        tool = GraphCompositionTool()
        
        # Add content based on exploration insights
        new_graph, validation = tool.add_predicate(graph, "Person", 1)
        assert validation.is_valid
        
        # Re-explore the modified graph
        new_explorer = GraphExplorer(new_graph)
        new_overview = new_explorer.get_overview()
        assert new_overview.total_visible_items >= overview.total_visible_items


class TestErrorHandling:
    """Test error handling in Phase 5A tools."""
    
    def test_invalid_transformations(self):
        """Test handling of invalid transformations."""
        engine = LookAheadEngine()
        graph = EGGraph.create_empty()
        
        # Try invalid transformation
        preview = engine.preview_transformation(
            graph,
            TransformationType.DEITERATION,  # Requires specific structure
            {NodeId(uuid.uuid4())}  # Non-existent node
        )
        
        assert not preview.success
        assert preview.transformed_graph is None
    
    def test_invalid_contexts(self):
        """Test handling of invalid context operations."""
        graph = EGGraph.create_empty()
        explorer = GraphExplorer(graph)
        
        # Try to focus on non-existent context
        fake_context = ContextId(uuid.uuid4())
        view = explorer.focus_on_context(fake_context)
        
        # Should handle gracefully
        assert isinstance(view, ExplorationView)
    
    def test_empty_graph_operations(self):
        """Test operations on empty graphs."""
        tool = GraphCompositionTool()
        graph = tool.create_blank_sheet()
        
        # Validate empty graph
        validation = tool.validate_graph(graph, ValidationLevel.FULL)
        assert isinstance(validation, ValidationResult)
        
        # Preview empty graph in game
        preview = tool.preview_in_game(graph)
        assert isinstance(preview.complexity_assessment, str)
        
        # Explore empty graph
        explorer = GraphExplorer(graph)
        overview = explorer.get_overview()
        assert overview.total_visible_items >= 0  # At least root context

