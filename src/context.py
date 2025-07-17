"""
Context management for the EG-HG rebuild project.

This module provides the ContextManager class for managing contexts (cuts)
in existential graphs, including hierarchy management and item containment.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, replace, field
import uuid

try:
    from .eg_types import (
        Context, ContextId, ItemId,
        new_context_id, ContextError,
        pmap, pset
    )
except ImportError:
    # For standalone testing
    from eg_types import (
        Context, ContextId, ItemId,
        new_context_id, ContextError,
        pmap, pset
    )


@dataclass(frozen=True)
class ContextManager:
    """Manages contexts and their hierarchical relationships in an existential graph."""
    
    contexts: pmap = field(default_factory=pmap)  # Dict[ContextId, Context]
    root_context: Context = field(default=None)
    
    def __post_init__(self):
        """Initialize the context manager after dataclass initialization."""
        if self.root_context is None:
            root_context = Context.create(
                context_type='sheet_of_assertion',
                parent_context=None,
                depth=0
            )
            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, 'root_context', root_context)
            object.__setattr__(self, 'contexts', pmap({root_context.id: root_context}))
        elif not self.contexts:
            # If root_context is provided but contexts is empty, initialize contexts
            object.__setattr__(self, 'contexts', pmap({self.root_context.id: self.root_context}))
    
    @classmethod
    def create_empty(cls) -> 'ContextManager':
        """Create an empty context manager with default root context."""
        return cls()
    
    @classmethod
    def create_with_root(cls, root_context: Context) -> 'ContextManager':
        """Create a context manager with a specific root context."""
        return cls(
            contexts=pmap({root_context.id: root_context}),
            root_context=root_context
        )
    
    def get_context(self, context_id: ContextId) -> Optional[Context]:
        """Get a context by its ID."""
        return self.contexts.get(context_id)
    
    def has_context(self, context_id: ContextId) -> bool:
        """Check if a context exists."""
        return context_id in self.contexts
    
    def create_context(self, context_type: str, parent_id: Optional[ContextId] = None,
                      name: Optional[str] = None) -> Tuple['ContextManager', Context]:
        """Create a new context.
        
        Args:
            context_type: The type of context to create
            parent_id: The ID of the parent context. If None, uses root context.
            name: Optional name for the context
            
        Returns:
            A tuple of (new_context_manager, new_context)
            
        Raises:
            ContextError: If the parent context doesn't exist.
        """
        if parent_id is None:
            parent_id = self.root_context.id
        
        if parent_id not in self.contexts:
            raise ContextError(f"Parent context {parent_id} not found")
        
        parent_context = self.contexts[parent_id]
        new_context = Context.create(
            context_type=context_type,
            parent_context=parent_id,
            depth=parent_context.depth + 1
        )
        
        if name:
            new_context = new_context.set_property("name", name)
        
        new_contexts = self.contexts.set(new_context.id, new_context)
        new_manager = replace(self, contexts=new_contexts)
        
        return new_manager, new_context
    
    def add_context(self, context: Context) -> 'ContextManager':
        """Add an existing context to the manager."""
        new_contexts = self.contexts.set(context.id, context)
        return replace(self, contexts=new_contexts)
    
    def remove_context(self, context_id: ContextId) -> 'ContextManager':
        """Remove a context and all its children."""
        if context_id == self.root_context.id:
            raise ContextError("Cannot remove root context")
        
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        # Find all child contexts
        children = self._get_child_contexts(context_id)
        
        # Remove all children and the context itself
        new_contexts = self.contexts
        for child_id in children:
            new_contexts = new_contexts.remove(child_id)
        new_contexts = new_contexts.remove(context_id)
        
        return replace(self, contexts=new_contexts)
    
    def add_item_to_context(self, context_id: ContextId, item_id: ItemId) -> 'ContextManager':
        """Add an item to a context."""
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        context = self.contexts[context_id]
        updated_context = context.add_item(item_id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        return replace(self, contexts=new_contexts)
    
    def remove_item_from_context(self, context_id: ContextId, item_id: ItemId) -> 'ContextManager':
        """Remove an item from a context."""
        if context_id not in self.contexts:
            raise ContextError(f"Context {context_id} not found")
        
        context = self.contexts[context_id]
        updated_context = context.remove_item(item_id)
        new_contexts = self.contexts.set(context_id, updated_context)
        
        return replace(self, contexts=new_contexts)
    
    def get_items_in_context(self, context_id: ContextId) -> Set[ItemId]:
        """Get all items directly contained in a context."""
        if context_id not in self.contexts:
            return set()
        
        context = self.contexts[context_id]
        return set(context.contained_items)
    
    def find_item_context(self, item_id: ItemId) -> Optional[ContextId]:
        """Find which context contains an item."""
        for context_id, context in self.contexts.items():
            if item_id in context.contained_items:
                return context_id
        return None
    
    def get_context_path(self, context_id: ContextId) -> List[ContextId]:
        """Get the path from root to the specified context."""
        if context_id not in self.contexts:
            return []
        
        path = []
        current_id = context_id
        
        while current_id is not None:
            path.append(current_id)
            context = self.contexts[current_id]
            current_id = context.parent_context
        
        return list(reversed(path))
    
    def get_context_depth(self, context_id: ContextId) -> int:
        """Get the depth of a context."""
        if context_id not in self.contexts:
            return -1
        
        return self.contexts[context_id].depth
    
    def _get_child_contexts(self, parent_id: ContextId) -> List[ContextId]:
        """Get all direct and indirect children of a context."""
        children = []
        
        for context_id, context in self.contexts.items():
            if context.parent_context == parent_id:
                children.append(context_id)
                children.extend(self._get_child_contexts(context_id))
        
        return children
    
    def validate_integrity(self) -> List[str]:
        """Validate the integrity of the context hierarchy."""
        errors = []
        
        # Check that all parent contexts exist
        for context_id, context in self.contexts.items():
            if context.parent_context is not None:
                if context.parent_context not in self.contexts:
                    errors.append(f"Context {context_id} has non-existent parent {context.parent_context}")
        
        # Check depth consistency
        for context_id, context in self.contexts.items():
            if context.parent_context is not None:
                parent = self.contexts.get(context.parent_context)
                if parent and context.depth != parent.depth + 1:
                    errors.append(f"Context {context_id} has inconsistent depth")
        
        # Check for cycles
        for context_id in self.contexts:
            visited = set()
            current = context_id
            while current is not None:
                if current in visited:
                    errors.append(f"Cycle detected involving context {context_id}")
                    break
                visited.add(current)
                context = self.contexts.get(current)
                current = context.parent_context if context else None
        
        return errors

