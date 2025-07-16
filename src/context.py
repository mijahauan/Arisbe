"""
Context management for the EG-HG rebuild project.

This module provides the ContextManager class for managing hierarchical
contexts in existential graphs, including creation, validation, and
manipulation of context relationships.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from pyrsistent import pmap, pset

from .eg_types import (
    Context, ContextId, ItemId, ContextError, ValidationError,
    new_context_id
)


class ContextManager:
    """Manages hierarchical contexts in an existential graph.
    
    This class provides immutable operations for creating, managing, and
    validating context hierarchies. All operations return new instances
    to maintain immutability.
    """
    
    def __init__(self, root_context: Optional[Context] = None):
        """Initialize a new context manager.
        
        Args:
            root_context: Optional root context. If None, creates a default
                         'sheet' context.
        """
        if root_context is None:
            root_context = Context.create(
                context_type='sheet',
                depth=0,
                properties={'name': 'Sheet of Assertion'}
            )
        
        self.root_context = root_context
        self.contexts = pmap({root_context.id: root_context})
    
    def get_context(self, context_id: ContextId) -> Optional[Context]:
        """Get a context by its ID.
        
        Args:
            context_id: The ID of the context to retrieve.
            
        Returns:
            The context if found, None otherwise.
        """
        return self.contexts.get(context_id)
    
    def has_context(self, context_id: ContextId) -> bool:
        """Check if a context exists.
        
        Args:
            context_id: The ID of the context to check.
            
        Returns:
            True if the context exists, False otherwise.
        """
        return context_id in self.contexts
    
    def create_context(self, context_type: str, parent_id: Optional[ContextId] = None,
                      name: Optional[str] = None) -> Tuple['ContextManager', Context]:
        """Create a new context.
        
        Args:
            context_type: The type of context to create.
            parent_id: The ID of the parent context. If None, uses root context.
            name: Optional name for the context.
            
        Returns:
            A tuple of (new_manager, new_context).
            
        Raises:
            ContextError: If the parent context doesn't exist.
        """
        if parent_id is None:
            parent_id = self.root_context.id
        
        parent_context = self.get_context(parent_id)
        if parent_context is None:
            raise ContextError(f"Parent context {parent_id} not found")
        
        # Create properties dict
        properties = {}
        if name is not None:
            properties['name'] = name
        
        # Create new context with proper depth
        new_context = Context.create(
            context_type=context_type,
            parent_context=parent_id,
            depth=parent_context.depth + 1,
            properties=properties
        )
        
        # Create new manager with updated contexts
        new_contexts = self.contexts.set(new_context.id, new_context)
        new_manager = ContextManager.__new__(ContextManager)
        new_manager.root_context = self.root_context
        new_manager.contexts = new_contexts
        
        return new_manager, new_context
    
    def add_item_to_context(self, context_id: ContextId, item_id: ItemId) -> 'ContextManager':
        """Add an item to a context.
        
        Args:
            context_id: The ID of the context to add the item to.
            item_id: The ID of the item to add.
            
        Returns:
            A new ContextManager with the item added.
            
        Raises:
            ContextError: If the context doesn't exist.
        """
        context = self.get_context(context_id)
        if context is None:
            raise ContextError(f"Context {context_id} not found")
        
        updated_context = context.add_item(item_id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        new_manager = ContextManager.__new__(ContextManager)
        new_manager.root_context = self.root_context
        new_manager.contexts = new_contexts
        
        return new_manager
    
    def remove_item_from_context(self, context_id: ContextId, item_id: ItemId) -> 'ContextManager':
        """Remove an item from a context.
        
        Args:
            context_id: The ID of the context to remove the item from.
            item_id: The ID of the item to remove.
            
        Returns:
            A new ContextManager with the item removed.
            
        Raises:
            ContextError: If the context doesn't exist.
        """
        context = self.get_context(context_id)
        if context is None:
            raise ContextError(f"Context {context_id} not found")
        
        updated_context = context.remove_item(item_id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        new_manager = ContextManager.__new__(ContextManager)
        new_manager.root_context = self.root_context
        new_manager.contexts = new_contexts
        
        return new_manager
    
    def move_item(self, item_id: ItemId, from_context_id: ContextId, 
                  to_context_id: ContextId) -> 'ContextManager':
        """Move an item from one context to another.
        
        Args:
            item_id: The ID of the item to move.
            from_context_id: The ID of the source context.
            to_context_id: The ID of the destination context.
            
        Returns:
            A new ContextManager with the item moved.
            
        Raises:
            ContextError: If either context doesn't exist.
        """
        # Remove from source context
        manager = self.remove_item_from_context(from_context_id, item_id)
        # Add to destination context
        return manager.add_item_to_context(to_context_id, item_id)
    
    def get_context_path(self, context_id: ContextId) -> Optional[List[ContextId]]:
        """Get the path from root to the specified context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A list of context IDs from root to the specified context,
            or None if the context doesn't exist.
        """
        context = self.get_context(context_id)
        if context is None:
            return None
        
        path = []
        current = context
        
        while current is not None:
            path.append(current.id)
            if current.parent_context is None:
                break
            current = self.get_context(current.parent_context)
        
        return list(reversed(path))
    
    def get_ancestors(self, context_id: ContextId) -> List[ContextId]:
        """Get all ancestor contexts of the specified context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A list of ancestor context IDs, from immediate parent to root.
        """
        ancestors = []
        context = self.get_context(context_id)
        
        while context is not None and context.parent_context is not None:
            ancestors.append(context.parent_context)
            context = self.get_context(context.parent_context)
        
        return ancestors
    
    def get_descendants(self, context_id: ContextId) -> List[ContextId]:
        """Get all descendant contexts of the specified context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A list of descendant context IDs.
        """
        descendants = []
        
        for ctx_id, ctx in self.contexts.items():
            if ctx.parent_context == context_id:
                descendants.append(ctx_id)
                # Recursively get descendants of this child
                descendants.extend(self.get_descendants(ctx_id))
        
        return descendants
    
    def get_child_contexts(self, context_id: ContextId) -> List[ContextId]:
        """
        Get the immediate child contexts of a given context.
        
        Args:
            context_id: The ID of the parent context.
            
        Returns:
            A list of immediate child context IDs.
        """
        children = []
        for ctx_id, ctx in self.contexts.items():
            if ctx.parent_context == context_id:
                children.append(ctx_id)
        return children
    
    def get_parent_context(self, context_id: ContextId) -> Optional[ContextId]:
        """
        Get the parent context of a given context.
        
        Args:
            context_id: The ID of the child context.
            
        Returns:
            The parent context ID, or None if this is the root context.
        """
        context = self.get_context(context_id)
        return context.parent_context if context else None
    
    def is_ancestor(self, ancestor_id: ContextId, descendant_id: ContextId) -> bool:
        """Check if one context is an ancestor of another.
        
        Args:
            ancestor_id: The ID of the potential ancestor context.
            descendant_id: The ID of the potential descendant context.
            
        Returns:
            True if ancestor_id is an ancestor of descendant_id.
        """
        ancestors = self.get_ancestors(descendant_id)
        return ancestor_id in ancestors
    
    def find_common_ancestor(self, context1_id: ContextId, 
                           context2_id: ContextId) -> Optional[ContextId]:
        """Find the lowest common ancestor of two contexts.
        
        Args:
            context1_id: The ID of the first context.
            context2_id: The ID of the second context.
            
        Returns:
            The ID of the lowest common ancestor, or None if not found.
        """
        # Special case: if one context is an ancestor of the other,
        # the common ancestor is the parent of the deeper one
        if self.is_ancestor(context1_id, context2_id):
            # context1 is ancestor of context2, so common ancestor is context1's parent
            context1 = self.get_context(context1_id)
            return context1.parent_context if context1 else None
        elif self.is_ancestor(context2_id, context1_id):
            # context2 is ancestor of context1, so common ancestor is context2's parent
            context2 = self.get_context(context2_id)
            return context2.parent_context if context2 else None
        
        # General case: find paths and compare
        path1 = self.get_context_path(context1_id)
        path2 = self.get_context_path(context2_id)
        
        if path1 is None or path2 is None:
            return None
        
        # Find the last common element in the paths
        common_ancestor = None
        for i in range(min(len(path1), len(path2))):
            if path1[i] == path2[i]:
                common_ancestor = path1[i]
            else:
                break
        
        return common_ancestor
    
    def get_items_in_context(self, context_id: ContextId) -> Set[ItemId]:
        """Get all items directly contained in a context.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A set of item IDs in the context.
        """
        context = self.get_context(context_id)
        if context is None:
            return set()
        
        return set(context.contained_items)
    
    def get_all_items_in_subtree(self, context_id: ContextId) -> Set[ItemId]:
        """Get all items in a context and all its descendants.
        
        Args:
            context_id: The ID of the context.
            
        Returns:
            A set of all item IDs in the subtree.
        """
        items = self.get_items_in_context(context_id)
        
        # Add items from all descendant contexts
        for descendant_id in self.get_descendants(context_id):
            items.update(self.get_items_in_context(descendant_id))
        
        return items
    
    def find_item_context(self, item_id: ItemId) -> Optional[ContextId]:
        """Find which context contains a specific item.
        
        Args:
            item_id: The ID of the item to find.
            
        Returns:
            The ID of the context containing the item, or None if not found.
        """
        for ctx_id, ctx in self.contexts.items():
            if item_id in ctx.contained_items:
                return ctx_id
        
        return None
    
    def validate_context_hierarchy(self) -> List[str]:
        """Validate the context hierarchy for consistency.
        
        Returns:
            A list of error messages. Empty list means no errors.
        """
        errors = []
        
        # Check that all contexts have valid parent relationships
        for ctx_id, ctx in self.contexts.items():
            if ctx.parent_context is not None:
                parent = self.get_context(ctx.parent_context)
                if parent is None:
                    errors.append(f"Context {ctx_id} has non-existent parent {ctx.parent_context}")
                else:
                    # Check depth consistency
                    expected_depth = parent.depth + 1
                    if ctx.depth != expected_depth:
                        errors.append(f"Context {ctx_id} has depth {ctx.depth}, expected {expected_depth}")
        
        # Check for cycles
        visited = set()
        for ctx_id in self.contexts:
            if ctx_id not in visited:
                path = []
                current = ctx_id
                
                while current is not None and current not in visited:
                    if current in path:
                        errors.append(f"Cycle detected in context hierarchy: {path}")
                        break
                    
                    path.append(current)
                    context = self.get_context(current)
                    current = context.parent_context if context else None
                
                visited.update(path)
        
        return errors
    
    def remove_context(self, context_id: ContextId) -> 'ContextManager':
        """Remove a context and update parent references.
        
        Args:
            context_id: The ID of the context to remove.
            
        Returns:
            A new ContextManager with the context removed.
        """
        if context_id not in self.contexts:
            return self  # Context doesn't exist, return unchanged
        
        # Get the context to remove
        context_to_remove = self.contexts[context_id]
        
        # Update children to point to the removed context's parent
        new_contexts = self.contexts.remove(context_id)
        
        for ctx_id, ctx in new_contexts.items():
            if ctx.parent_context == context_id:
                # Update child to point to removed context's parent
                updated_ctx = ctx.create(parent_context=context_to_remove.parent_context)
                new_contexts = new_contexts.set(ctx_id, updated_ctx)
        
        # Remove items that were in this context
        new_context_items = self.context_items
        if context_id in new_context_items:
            new_context_items = new_context_items.remove(context_id)
        
        return ContextManager(
            contexts=new_contexts,
            context_items=new_context_items
        )

