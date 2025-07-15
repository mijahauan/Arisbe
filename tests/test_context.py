"""
Tests for the context management system.
"""

import pytest
from hypothesis import given, strategies as st

from src.context import ContextManager
from src.eg_types import (
    Context, ContextId, ItemId, ContextError, ValidationError,
    new_context_id, new_node_id, pmap
)


class TestContext:
    """Test the Context class."""
    
    def test_context_creation_with_defaults(self):
        """Test creating a context with default values."""
        context = Context.create(context_type="sheet")
        assert context.context_type == "sheet"
        assert context.parent_context is None
        assert context.depth == 0
        assert len(context.contained_items) == 0
        assert len(context.properties) == 0
    
    def test_context_with_properties(self):
        """Test creating a context with properties."""
        properties = {"name": "Test Context", "color": "blue"}
        context = Context.create(
            context_type="cut",
            properties=properties
        )
        assert context.properties == pmap(properties)


class TestContextManager:
    """Test the ContextManager class."""
    
    def test_context_manager_initialization_default(self):
        """Test creating a context manager with default root context."""
        manager = ContextManager()
        assert manager.root_context.context_type == 'sheet'
        assert manager.root_context.depth == 0
        assert 'name' in manager.root_context.properties
        assert manager.root_context.properties['name'] == 'Sheet of Assertion'
    
    def test_context_manager_initialization_custom_root(self):
        """Test creating a context manager with custom root context."""
        custom_root = Context.create(
            context_type='sheet',
            depth=0,
            properties={'name': 'Custom Sheet'}
        )
        manager = ContextManager(custom_root)
        assert manager.root_context == custom_root
        assert manager.root_context.properties['name'] == 'Custom Sheet'
    
    def test_get_context_existing(self):
        """Test getting an existing context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        context = manager.get_context(root_id)
        assert context == manager.root_context
    
    def test_get_context_nonexistent(self):
        """Test getting a non-existent context."""
        manager = ContextManager()
        fake_id = new_context_id()
        context = manager.get_context(fake_id)
        assert context is None
    
    def test_has_context(self):
        """Test checking if a context exists."""
        manager = ContextManager()
        root_id = manager.root_context.id
        fake_id = new_context_id()
        
        assert manager.has_context(root_id)
        assert not manager.has_context(fake_id)
    
    def test_create_context_in_root(self):
        """Test creating a context in the root context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        new_manager, new_context = manager.create_context('cut', parent_id=root_id)
        
        assert new_context.context_type == 'cut'
        assert new_context.parent_context == root_id
        assert new_context.depth == 1
        assert new_manager.has_context(new_context.id)
    
    def test_create_context_default_parent(self):
        """Test creating a context with default parent (root)."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        new_manager, new_context = manager.create_context('cut')
        
        assert new_context.parent_context == root_id
        assert new_context.depth == 1
    
    def test_create_context_nonexistent_parent(self):
        """Test creating a context with non-existent parent."""
        manager = ContextManager()
        fake_parent_id = new_context_id()
        
        with pytest.raises(ContextError):
            manager.create_context('cut', parent_id=fake_parent_id)
    
    def test_add_item_to_context(self):
        """Test adding an item to a context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        item_id = new_node_id()
        
        new_manager = manager.add_item_to_context(root_id, item_id)
        
        updated_context = new_manager.get_context(root_id)
        assert item_id in updated_context.contained_items
    
    def test_add_item_to_nonexistent_context(self):
        """Test adding an item to a non-existent context."""
        manager = ContextManager()
        fake_context_id = new_context_id()
        item_id = new_node_id()
        
        with pytest.raises(ContextError):
            manager.add_item_to_context(fake_context_id, item_id)
    
    def test_remove_item_from_context(self):
        """Test removing an item from a context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        item_id = new_node_id()
        
        # Add item first
        manager = manager.add_item_to_context(root_id, item_id)
        
        # Remove item
        new_manager = manager.remove_item_from_context(root_id, item_id)
        
        updated_context = new_manager.get_context(root_id)
        assert item_id not in updated_context.contained_items
    
    def test_move_item(self):
        """Test moving an item between contexts."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create a second context
        manager, context2 = manager.create_context('cut', parent_id=root_id)
        context2_id = context2.id
        
        # Add item to root
        item_id = new_node_id()
        manager = manager.add_item_to_context(root_id, item_id)
        
        # Move item to context2
        new_manager = manager.move_item(item_id, root_id, context2_id)
        
        # Check item was moved
        root_context = new_manager.get_context(root_id)
        context2_updated = new_manager.get_context(context2_id)
        
        assert item_id not in root_context.contained_items
        assert item_id in context2_updated.contained_items
    
    def test_get_context_path(self):
        """Test getting the path to a context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create nested contexts
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        
        path = manager.get_context_path(context2.id)
        expected_path = [root_id, context1.id, context2.id]
        
        assert path == expected_path
    
    def test_get_context_path_nonexistent(self):
        """Test getting path for non-existent context."""
        manager = ContextManager()
        fake_id = new_context_id()
        
        path = manager.get_context_path(fake_id)
        assert path is None
    
    def test_get_ancestors(self):
        """Test getting ancestors of a context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create nested contexts
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        
        ancestors = manager.get_ancestors(context2.id)
        expected_ancestors = [context1.id, root_id]
        
        assert ancestors == expected_ancestors
    
    def test_get_descendants(self):
        """Test getting descendants of a context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create nested contexts
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        manager, context3 = manager.create_context('cut', parent_id=root_id)
        
        descendants = manager.get_descendants(root_id)
        
        assert context1.id in descendants
        assert context2.id in descendants
        assert context3.id in descendants
        assert len(descendants) == 3
    
    def test_is_ancestor(self):
        """Test checking ancestor relationships."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create nested contexts
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        
        assert manager.is_ancestor(root_id, context1.id)
        assert manager.is_ancestor(root_id, context2.id)
        assert manager.is_ancestor(context1.id, context2.id)
        assert not manager.is_ancestor(context1.id, root_id)
        assert not manager.is_ancestor(context2.id, context1.id)
    
    def test_find_common_ancestor(self):
        """Test finding common ancestor of two contexts."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create branching structure
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        manager, context3 = manager.create_context('cut', parent_id=context1.id)
        
        common = manager.find_common_ancestor(context2.id, context3.id)
        assert common == context1.id
        
        common = manager.find_common_ancestor(context1.id, context2.id)
        assert common == root_id
    
    def test_get_items_in_context(self):
        """Test getting items in a specific context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        item1 = new_node_id()
        item2 = new_node_id()
        
        manager = manager.add_item_to_context(root_id, item1)
        manager = manager.add_item_to_context(root_id, item2)
        
        items = manager.get_items_in_context(root_id)
        assert item1 in items
        assert item2 in items
        assert len(items) == 2
    
    def test_get_all_items_in_subtree(self):
        """Test getting all items in a context subtree."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create nested contexts with items
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        
        item1 = new_node_id()
        item2 = new_node_id()
        
        manager = manager.add_item_to_context(root_id, item1)
        manager = manager.add_item_to_context(context1.id, item2)
        
        all_items = manager.get_all_items_in_subtree(root_id)
        assert item1 in all_items
        assert item2 in all_items
        assert len(all_items) == 2
    
    def test_find_item_context(self):
        """Test finding which context contains an item."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        
        item_id = new_node_id()
        manager = manager.add_item_to_context(context1.id, item_id)
        
        found_context = manager.find_item_context(item_id)
        assert found_context == context1.id
    
    def test_validate_context_hierarchy_valid(self):
        """Test validation of a valid context hierarchy."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create valid nested structure
        manager, cut1 = manager.create_context('cut', parent_id=root_id)
        manager, cut2 = manager.create_context('cut', parent_id=cut1.id)
        
        errors = manager.validate_context_hierarchy()
        assert errors == []
    
    def test_validate_context_hierarchy_invalid_depth(self):
        """Test validation catches invalid depth relationships."""
        manager = ContextManager()
        
        # Manually create context with wrong depth
        invalid_context = Context.create(
            context_type='cut',
            parent_context=manager.root_context.id,
            depth=5  # Should be 1
        )
        
        # Manually add to contexts (bypassing normal creation)
        new_contexts = manager.contexts.set(invalid_context.id, invalid_context)
        manager.contexts = new_contexts
        
        errors = manager.validate_context_hierarchy()
        assert len(errors) > 0
        assert any("depth" in error for error in errors)


class TestContextManagerImmutability:
    """Test immutability of ContextManager operations."""
    
    def test_create_context_immutability(self):
        """Test that creating a context doesn't modify the original manager."""
        manager = ContextManager()
        original_contexts = manager.contexts
        
        new_manager, _ = manager.create_context('cut')
        
        assert manager.contexts == original_contexts
        assert new_manager.contexts != original_contexts
    
    def test_add_item_immutability(self):
        """Test that adding an item doesn't modify the original manager."""
        manager = ContextManager()
        root_id = manager.root_context.id
        item_id = new_node_id()
        
        original_contexts = manager.contexts
        new_manager = manager.add_item_to_context(root_id, item_id)
        
        assert manager.contexts == original_contexts
        assert new_manager.contexts != original_contexts
    
    def test_remove_item_immutability(self):
        """Test that removing an item doesn't modify the original manager."""
        manager = ContextManager()
        root_id = manager.root_context.id
        item_id = new_node_id()
        
        # Add item first
        manager = manager.add_item_to_context(root_id, item_id)
        original_contexts = manager.contexts
        
        new_manager = manager.remove_item_from_context(root_id, item_id)
        
        assert manager.contexts == original_contexts
        assert new_manager.contexts != original_contexts


class TestContextManagerProperties:
    """Property-based tests for ContextManager."""
    
    @given(st.integers(min_value=1, max_value=10))
    def test_context_depth_consistency(self, num_contexts):
        """Test that context depths are always consistent."""
        manager = ContextManager()
        current_parent = manager.root_context.id
        
        for i in range(num_contexts):
            manager, new_context = manager.create_context('cut', parent_id=current_parent)
            
            # Check depth consistency
            parent = manager.get_context(current_parent)
            assert new_context.depth == parent.depth + 1
            
            current_parent = new_context.id
        
        # Validate the entire hierarchy
        errors = manager.validate_context_hierarchy()
        assert errors == []
    
    @given(st.integers(min_value=1, max_value=20))
    def test_item_context_consistency(self, num_items):
        """Test that items are always found in the correct context."""
        manager = ContextManager()
        root_id = manager.root_context.id
        
        # Create some contexts
        manager, context1 = manager.create_context('cut', parent_id=root_id)
        manager, context2 = manager.create_context('cut', parent_id=context1.id)
        
        contexts = [root_id, context1.id, context2.id]
        items_to_contexts = {}
        
        for i in range(num_items):
            item_id = new_node_id()
            context_id = contexts[i % len(contexts)]
            
            manager = manager.add_item_to_context(context_id, item_id)
            items_to_contexts[item_id] = context_id
        
        # Verify all items are in their expected contexts
        for item_id, expected_context in items_to_contexts.items():
            found_context = manager.find_item_context(item_id)
            assert found_context == expected_context

