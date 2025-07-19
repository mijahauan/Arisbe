"""
Multi-Scope Exploration System

This module provides tools for exploring existential graphs from different
perspectives and scopes. It enables users to examine graphs at various
levels of detail and from different logical and visual viewpoints.

Updated for Entity-Predicate hypergraph architecture where:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

The exploration system supports:
1. Scope-based viewing (area, context, nested content)
2. Level-based navigation (zoom in/out by context levels)
3. Focus management (what's currently in view)
4. Context-aware information display
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, replace
from enum import Enum
import copy

from eg_types import (
    Entity, Predicate, Context, Ligature, 
    EntityId, PredicateId, ContextId, LigatureId, ItemId
)
from graph import EGGraph
from context import ContextManager


class ScopeType(Enum):
    """Types of scope for exploration."""
    AREA_ONLY = "area_only"           # Only objects in the immediate area
    CONTEXT_COMPLETE = "context_complete"  # All nested content (zoom all the way in)
    LEVEL_LIMITED = "level_limited"   # Limited number of levels down
    CONTAINING = "containing"         # Containing contexts (zoom out)


class FocusMode(Enum):
    """Modes for focusing on graph elements."""
    SINGLE_ITEM = "single_item"       # Focus on one specific item
    CONTEXT_AREA = "context_area"     # Focus on a context and its immediate contents
    LIGATURE_PATH = "ligature_path"   # Focus on a ligature and connected elements
    PATTERN_MATCH = "pattern_match"   # Focus on elements matching a pattern
    TRANSFORMATION_TARGET = "transformation_target"  # Focus on transformation targets


@dataclass(frozen=True)
class ViewScope:
    """Defines the scope of a view into the graph."""
    scope_type: ScopeType
    focus_context: ContextId
    max_depth: Optional[int] = None
    include_ligatures: bool = True
    include_containing: bool = False
    filter_types: Optional[Set[str]] = None
    
    def with_depth(self, depth: int) -> 'ViewScope':
        """Create a new scope with specified depth."""
        return replace(self, max_depth=depth)
    
    def with_context(self, context_id: ContextId) -> 'ViewScope':
        """Create a new scope focused on a different context."""
        return replace(self, focus_context=context_id)


@dataclass(frozen=True)
class ExplorationView:
    """A view of the graph from a specific scope and focus."""
    scope: ViewScope
    visible_entities: Set[EntityId]
    visible_predicates: Set[PredicateId]
    visible_contexts: Set[ContextId]
    visible_ligatures: Set[LigatureId]
    focus_items: Set[ItemId]
    context_hierarchy: Dict[ContextId, List[ContextId]]  # parent -> children
    item_locations: Dict[ItemId, ContextId]  # item -> containing context
    scope_boundaries: Set[ContextId]  # contexts at the edge of scope
    navigation_hints: List[str]
    
    @property
    def total_visible_items(self) -> int:
        """Total number of visible items."""
        return (len(self.visible_entities) + len(self.visible_predicates) + 
                len(self.visible_contexts) + len(self.visible_ligatures))
    
    @property
    def is_empty(self) -> bool:
        """Check if the view is empty."""
        return self.total_visible_items == 0


@dataclass(frozen=True)
class NavigationPath:
    """A path through the graph's context hierarchy."""
    contexts: List[ContextId]
    descriptions: List[str]
    depths: List[int]
    
    @property
    def current_context(self) -> ContextId:
        """Get the current (last) context in the path."""
        return self.contexts[-1] if self.contexts else None
    
    @property
    def current_depth(self) -> int:
        """Get the current depth."""
        return self.depths[-1] if self.depths else 0


@dataclass(frozen=True)
class EntityConnection:
    """Represents a connection between entities through predicates."""
    entity1: EntityId
    entity2: EntityId
    connecting_predicates: List[PredicateId]
    connection_type: str  # 'direct', 'shared_predicate', 'ligature'
    path_length: int


@dataclass(frozen=True)
class ExplorationState:
    """Current state of the exploration session."""
    current_view: ExplorationView
    navigation_path: NavigationPath
    focus_history: List[ItemId]
    bookmarks: Dict[str, ViewScope]
    filters: Dict[str, Any]


class GraphExplorer:
    """
    Main tool for exploring existential graphs with Entity-Predicate architecture.
    
    Provides multi-scope viewing, navigation, and analysis capabilities
    for understanding graph structure and logical content.
    """
    
    def __init__(self):
        """Initialize the graph explorer."""
        self.current_state: Optional[ExplorationState] = None
        self.graph: Optional[EGGraph] = None
    
    def set_graph(self, graph: EGGraph) -> None:
        """Set the graph to explore."""
        self.graph = graph
        # Initialize exploration state
        root_scope = ViewScope(
            scope_type=ScopeType.AREA_ONLY,
            focus_context=graph.root_context_id
        )
        initial_view = self.create_view(root_scope)
        initial_path = NavigationPath(
            contexts=[graph.root_context_id],
            descriptions=["Root Context"],
            depths=[0]
        )
        
        self.current_state = ExplorationState(
            current_view=initial_view,
            navigation_path=initial_path,
            focus_history=[],
            bookmarks={},
            filters={}
        )
    
    def create_view(self, scope: ViewScope) -> ExplorationView:
        """Create a view of the graph based on the given scope."""
        if not self.graph:
            raise ValueError("No graph set for exploration")
        
        visible_entities = set()
        visible_predicates = set()
        visible_contexts = set()
        visible_ligatures = set()
        item_locations = {}
        context_hierarchy = {}
        scope_boundaries = set()
        
        # Get the focus context
        focus_context = self.graph.context_manager.get_context(scope.focus_context)
        if not focus_context:
            raise ValueError(f"Focus context {scope.focus_context} not found")
        
        # Build context hierarchy
        for context_id, context in self.graph.context_manager.contexts.items():
            if context.parent_context:
                if context.parent_context not in context_hierarchy:
                    context_hierarchy[context.parent_context] = []
                context_hierarchy[context.parent_context].append(context_id)
        
        # Determine visible items based on scope type
        if scope.scope_type == ScopeType.AREA_ONLY:
            # Only items directly in the focus context
            items_in_context = self.graph.context_manager.get_items_in_context(scope.focus_context)
            self._categorize_items(items_in_context, visible_entities, visible_predicates, visible_ligatures)
            visible_contexts.add(scope.focus_context)
            
        elif scope.scope_type == ScopeType.CONTEXT_COMPLETE:
            # All items in focus context and all nested contexts
            contexts_to_include = self._get_all_nested_contexts(scope.focus_context)
            visible_contexts.update(contexts_to_include)
            
            for context_id in contexts_to_include:
                items_in_context = self.graph.context_manager.get_items_in_context(context_id)
                self._categorize_items(items_in_context, visible_entities, visible_predicates, visible_ligatures)
                
        elif scope.scope_type == ScopeType.LEVEL_LIMITED:
            # Limited depth from focus context
            max_depth = scope.max_depth or 2
            contexts_to_include = self._get_contexts_within_depth(scope.focus_context, max_depth)
            visible_contexts.update(contexts_to_include)
            
            for context_id in contexts_to_include:
                items_in_context = self.graph.context_manager.get_items_in_context(context_id)
                self._categorize_items(items_in_context, visible_entities, visible_predicates, visible_ligatures)
                
            # Mark boundary contexts
            scope_boundaries = self._find_boundary_contexts(contexts_to_include)
            
        elif scope.scope_type == ScopeType.CONTAINING:
            # Focus context and its containing contexts
            current_context = focus_context
            while current_context:
                visible_contexts.add(current_context.id)
                items_in_context = self.graph.context_manager.get_items_in_context(current_context.id)
                self._categorize_items(items_in_context, visible_entities, visible_predicates, visible_ligatures)
                
                if current_context.parent_context:
                    current_context = self.graph.context_manager.get_context(current_context.parent_context)
                else:
                    break
        
        # Build item locations
        for entity_id in visible_entities:
            context_id = self.graph.context_manager.find_item_context(entity_id)
            if context_id:
                item_locations[entity_id] = context_id
        
        for predicate_id in visible_predicates:
            context_id = self.graph.context_manager.find_item_context(predicate_id)
            if context_id:
                item_locations[predicate_id] = context_id
        
        # Apply filters
        if scope.filter_types:
            visible_entities, visible_predicates = self._apply_type_filters(
                visible_entities, visible_predicates, scope.filter_types
            )
        
        # Generate navigation hints
        navigation_hints = self._generate_navigation_hints(scope, visible_contexts)
        
        return ExplorationView(
            scope=scope,
            visible_entities=visible_entities,
            visible_predicates=visible_predicates,
            visible_contexts=visible_contexts,
            visible_ligatures=visible_ligatures,
            focus_items=set(),  # Will be set by focus operations
            context_hierarchy=context_hierarchy,
            item_locations=item_locations,
            scope_boundaries=scope_boundaries,
            navigation_hints=navigation_hints
        )
    
    def focus_on_item(self, item_id: ItemId, focus_mode: FocusMode = FocusMode.SINGLE_ITEM) -> ExplorationView:
        """Focus the view on a specific item."""
        if not self.current_state:
            raise ValueError("No exploration state initialized")
        
        focus_items = set()
        
        if focus_mode == FocusMode.SINGLE_ITEM:
            focus_items.add(item_id)
            
        elif focus_mode == FocusMode.CONTEXT_AREA:
            # Focus on the item and everything in its context
            item_context = self.graph.context_manager.find_item_context(item_id)
            if item_context:
                items_in_context = self.graph.context_manager.get_items_in_context(item_context)
                focus_items.update(items_in_context)
                
        elif focus_mode == FocusMode.LIGATURE_PATH:
            # Focus on ligature connections
            if item_id in self.graph.entities:
                connected_items = self._find_connected_items(item_id)
                focus_items.update(connected_items)
                focus_items.add(item_id)
                
        elif focus_mode == FocusMode.PATTERN_MATCH:
            # Focus on items matching the same pattern as the target item
            pattern_items = self._find_pattern_matches(item_id)
            focus_items.update(pattern_items)
        
        # Update the current view with focus
        updated_view = replace(self.current_state.current_view, focus_items=focus_items)
        
        # Update exploration state
        updated_history = self.current_state.focus_history + [item_id]
        self.current_state = replace(
            self.current_state,
            current_view=updated_view,
            focus_history=updated_history
        )
        
        return updated_view
    
    def navigate_to_context(self, context_id: ContextId, scope_type: ScopeType = ScopeType.AREA_ONLY) -> ExplorationView:
        """Navigate to a different context."""
        if not self.current_state:
            raise ValueError("No exploration state initialized")
        
        # Create new scope for the target context
        new_scope = ViewScope(
            scope_type=scope_type,
            focus_context=context_id,
            include_ligatures=self.current_state.current_view.scope.include_ligatures
        )
        
        # Create new view
        new_view = self.create_view(new_scope)
        
        # Update navigation path
        context = self.graph.context_manager.get_context(context_id)
        context_description = f"Context {context.depth}" if context else "Unknown Context"
        
        updated_path = NavigationPath(
            contexts=self.current_state.navigation_path.contexts + [context_id],
            descriptions=self.current_state.navigation_path.descriptions + [context_description],
            depths=self.current_state.navigation_path.depths + [context.depth if context else 0]
        )
        
        # Update exploration state
        self.current_state = replace(
            self.current_state,
            current_view=new_view,
            navigation_path=updated_path
        )
        
        return new_view
    
    def zoom_in(self, levels: int = 1) -> ExplorationView:
        """Zoom in by including more nested contexts."""
        if not self.current_state:
            raise ValueError("No exploration state initialized")
        
        current_scope = self.current_state.current_view.scope
        
        if current_scope.scope_type == ScopeType.AREA_ONLY:
            # Switch to level limited with specified depth
            new_scope = replace(current_scope, scope_type=ScopeType.LEVEL_LIMITED, max_depth=levels)
        elif current_scope.scope_type == ScopeType.LEVEL_LIMITED:
            # Increase the depth limit
            current_depth = current_scope.max_depth or 1
            new_scope = replace(current_scope, max_depth=current_depth + levels)
        else:
            # For other scope types, switch to level limited
            new_scope = replace(current_scope, scope_type=ScopeType.LEVEL_LIMITED, max_depth=levels)
        
        new_view = self.create_view(new_scope)
        self.current_state = replace(self.current_state, current_view=new_view)
        
        return new_view
    
    def zoom_out(self, levels: int = 1) -> ExplorationView:
        """Zoom out by reducing scope or moving to containing contexts."""
        if not self.current_state:
            raise ValueError("No exploration state initialized")
        
        current_scope = self.current_state.current_view.scope
        
        if current_scope.scope_type == ScopeType.LEVEL_LIMITED:
            # Reduce the depth limit
            current_depth = current_scope.max_depth or 1
            new_depth = max(0, current_depth - levels)
            if new_depth == 0:
                new_scope = replace(current_scope, scope_type=ScopeType.AREA_ONLY, max_depth=None)
            else:
                new_scope = replace(current_scope, max_depth=new_depth)
        else:
            # Move to parent context
            current_context = self.graph.context_manager.get_context(current_scope.focus_context)
            if current_context and current_context.parent_context:
                new_scope = replace(current_scope, focus_context=current_context.parent_context)
            else:
                # Already at root, switch to containing view
                new_scope = replace(current_scope, scope_type=ScopeType.CONTAINING)
        
        new_view = self.create_view(new_scope)
        self.current_state = replace(self.current_state, current_view=new_view)
        
        return new_view
    
    def get_item_details(self, item_id: ItemId) -> Dict[str, Any]:
        """Get detailed information about a specific item."""
        if not self.graph:
            return {"error": "No graph set"}
        
        details = {"id": str(item_id), "type": "unknown"}
        
        if item_id in self.graph.entities:
            entity = self.graph.entities[item_id]
            details.update({
                "type": "entity",
                "name": entity.name,
                "entity_type": entity.entity_type,
                "properties": dict(entity.properties),
                "connected_predicates": self._get_connected_predicates(item_id),
                "context": self.graph.context_manager.find_item_context(item_id)
            })
            
        elif item_id in self.graph.predicates:
            predicate = self.graph.predicates[item_id]
            details.update({
                "type": "predicate",
                "name": predicate.name,
                "arity": predicate.arity,
                "entities": [str(eid) for eid in predicate.entities],
                "properties": dict(predicate.properties),
                "context": self.graph.context_manager.find_item_context(item_id)
            })
            
        elif item_id in self.graph.context_manager.contexts:
            context = self.graph.context_manager.get_context(item_id)
            if context:
                details.update({
                    "type": "context",
                    "context_type": context.context_type,
                    "depth": context.depth,
                    "parent": str(context.parent_context) if context.parent_context else None,
                    "children": [str(cid) for cid in self._get_child_contexts(item_id)],
                    "items": [str(iid) for iid in self.graph.context_manager.get_items_in_context(item_id)],
                    "properties": dict(context.properties)
                })
        
        return details
    
    def find_entity_connections(self, entity_id: EntityId) -> List[EntityConnection]:
        """Find all connections between an entity and other entities."""
        if not self.graph or entity_id not in self.graph.entities:
            return []
        
        connections = []
        
        # Find predicates that include this entity
        connected_predicates = self._get_connected_predicates(entity_id)
        
        # For each predicate, find other entities it connects to
        for predicate_id in connected_predicates:
            predicate = self.graph.predicates[predicate_id]
            for other_entity_id in predicate.entities:
                if other_entity_id != entity_id:
                    connection = EntityConnection(
                        entity1=entity_id,
                        entity2=other_entity_id,
                        connecting_predicates=[predicate_id],
                        connection_type='direct',
                        path_length=1
                    )
                    connections.append(connection)
        
        # Find ligature connections
        for ligature in self.graph.ligatures.values():
            if entity_id in ligature.connected_items:
                for other_item_id in ligature.connected_items:
                    if other_item_id != entity_id and other_item_id in self.graph.entities:
                        connection = EntityConnection(
                            entity1=entity_id,
                            entity2=other_item_id,
                            connecting_predicates=[],
                            connection_type='ligature',
                            path_length=1
                        )
                        connections.append(connection)
        
        return connections
    
    def get_context_summary(self, context_id: ContextId) -> Dict[str, Any]:
        """Get a summary of a context's contents and structure."""
        if not self.graph:
            return {"error": "No graph set"}
        
        context = self.graph.context_manager.get_context(context_id)
        if not context:
            return {"error": f"Context {context_id} not found"}
        
        items_in_context = self.graph.context_manager.get_items_in_context(context_id)
        
        entities_in_context = [item for item in items_in_context if item in self.graph.entities]
        predicates_in_context = [item for item in items_in_context if item in self.graph.predicates]
        
        child_contexts = self._get_child_contexts(context_id)
        
        return {
            "context_id": str(context_id),
            "type": context.context_type,
            "depth": context.depth,
            "polarity": "positive" if context.depth % 2 == 0 else "negative",
            "parent": str(context.parent_context) if context.parent_context else None,
            "entity_count": len(entities_in_context),
            "predicate_count": len(predicates_in_context),
            "child_context_count": len(child_contexts),
            "total_items": len(items_in_context),
            "properties": dict(context.properties)
        }
    
    def bookmark_current_view(self, name: str) -> None:
        """Bookmark the current view scope."""
        if not self.current_state:
            raise ValueError("No exploration state initialized")
        
        bookmarks = dict(self.current_state.bookmarks)
        bookmarks[name] = self.current_state.current_view.scope
        
        self.current_state = replace(self.current_state, bookmarks=bookmarks)
    
    def navigate_to_bookmark(self, name: str) -> ExplorationView:
        """Navigate to a bookmarked view."""
        if not self.current_state or name not in self.current_state.bookmarks:
            raise ValueError(f"Bookmark '{name}' not found")
        
        bookmarked_scope = self.current_state.bookmarks[name]
        new_view = self.create_view(bookmarked_scope)
        
        self.current_state = replace(self.current_state, current_view=new_view)
        return new_view
    
    # Helper methods
    
    def _categorize_items(self, items: Set[ItemId], entities: Set[EntityId], 
                         predicates: Set[PredicateId], ligatures: Set[LigatureId]) -> None:
        """Categorize items into entities, predicates, and ligatures."""
        for item_id in items:
            if item_id in self.graph.entities:
                entities.add(item_id)
            elif item_id in self.graph.predicates:
                predicates.add(item_id)
            elif item_id in self.graph.ligatures:
                ligatures.add(item_id)
    
    def _get_all_nested_contexts(self, context_id: ContextId) -> Set[ContextId]:
        """Get all contexts nested within the given context."""
        contexts = {context_id}
        
        def add_children(ctx_id):
            for child_id in self._get_child_contexts(ctx_id):
                if child_id not in contexts:
                    contexts.add(child_id)
                    add_children(child_id)
        
        add_children(context_id)
        return contexts
    
    def _get_contexts_within_depth(self, context_id: ContextId, max_depth: int) -> Set[ContextId]:
        """Get contexts within a specified depth from the given context."""
        contexts = {context_id}
        current_depth = 0
        
        def add_children_with_depth(ctx_id, depth):
            if depth >= max_depth:
                return
            for child_id in self._get_child_contexts(ctx_id):
                if child_id not in contexts:
                    contexts.add(child_id)
                    add_children_with_depth(child_id, depth + 1)
        
        add_children_with_depth(context_id, 0)
        return contexts
    
    def _get_child_contexts(self, context_id: ContextId) -> List[ContextId]:
        """Get direct child contexts of the given context."""
        children = []
        for ctx_id, context in self.graph.context_manager.contexts.items():
            if context.parent_context == context_id:
                children.append(ctx_id)
        return children
    
    def _find_boundary_contexts(self, included_contexts: Set[ContextId]) -> Set[ContextId]:
        """Find contexts at the boundary of the included set."""
        boundaries = set()
        
        for context_id in included_contexts:
            children = self._get_child_contexts(context_id)
            for child_id in children:
                if child_id not in included_contexts:
                    boundaries.add(context_id)
                    break
        
        return boundaries
    
    def _apply_type_filters(self, entities: Set[EntityId], predicates: Set[PredicateId], 
                          filter_types: Set[str]) -> Tuple[Set[EntityId], Set[PredicateId]]:
        """Apply type filters to visible items."""
        filtered_entities = set()
        filtered_predicates = set()
        
        if 'entities' in filter_types or 'variables' in filter_types or 'constants' in filter_types:
            for entity_id in entities:
                entity = self.graph.entities[entity_id]
                if ('entities' in filter_types or 
                    (entity.entity_type == 'variable' and 'variables' in filter_types) or
                    (entity.entity_type == 'constant' and 'constants' in filter_types)):
                    filtered_entities.add(entity_id)
        
        if 'predicates' in filter_types:
            filtered_predicates = predicates
        
        return filtered_entities, filtered_predicates
    
    def _generate_navigation_hints(self, scope: ViewScope, visible_contexts: Set[ContextId]) -> List[str]:
        """Generate navigation hints for the current view."""
        hints = []
        
        if scope.scope_type == ScopeType.AREA_ONLY:
            child_contexts = self._get_child_contexts(scope.focus_context)
            if child_contexts:
                hints.append(f"Zoom in to see {len(child_contexts)} nested contexts")
        
        if scope.scope_type == ScopeType.LEVEL_LIMITED:
            boundary_contexts = self._find_boundary_contexts(visible_contexts)
            if boundary_contexts:
                hints.append(f"Zoom in further to explore {len(boundary_contexts)} boundary contexts")
        
        focus_context = self.graph.context_manager.get_context(scope.focus_context)
        if focus_context and focus_context.parent_context:
            hints.append("Zoom out to see containing context")
        
        return hints
    
    def _get_connected_predicates(self, entity_id: EntityId) -> List[PredicateId]:
        """Get all predicates connected to an entity."""
        connected = []
        for predicate_id, predicate in self.graph.predicates.items():
            if entity_id in predicate.entities:
                connected.append(predicate_id)
        return connected
    
    def _find_connected_items(self, item_id: ItemId) -> Set[ItemId]:
        """Find all items connected to the given item."""
        connected = set()
        
        if item_id in self.graph.entities:
            # Find predicates connected to this entity
            for predicate_id, predicate in self.graph.predicates.items():
                if item_id in predicate.entities:
                    connected.add(predicate_id)
                    # Add other entities in the same predicate
                    connected.update(predicate.entities)
        
        elif item_id in self.graph.predicates:
            # Add all entities in this predicate
            predicate = self.graph.predicates[item_id]
            connected.update(predicate.entities)
        
        # Find ligature connections
        for ligature in self.graph.ligatures.values():
            if item_id in ligature.connected_items:
                connected.update(ligature.connected_items)
        
        # Remove the original item
        connected.discard(item_id)
        return connected
    
    def _find_pattern_matches(self, item_id: ItemId) -> Set[ItemId]:
        """Find items that match the same pattern as the given item."""
        matches = set()
        
        if item_id in self.graph.entities:
            entity = self.graph.entities[item_id]
            # Find entities of the same type
            for other_id, other_entity in self.graph.entities.items():
                if (other_id != item_id and 
                    other_entity.entity_type == entity.entity_type):
                    matches.add(other_id)
        
        elif item_id in self.graph.predicates:
            predicate = self.graph.predicates[item_id]
            # Find predicates with the same name or arity
            for other_id, other_predicate in self.graph.predicates.items():
                if (other_id != item_id and 
                    (other_predicate.name == predicate.name or 
                     other_predicate.arity == predicate.arity)):
                    matches.add(other_id)
        
        return matches


# Convenience functions for common exploration patterns

def explore_quantification_structure(graph: EGGraph) -> Dict[str, Any]:
    """Analyze the quantification structure of the graph."""
    explorer = GraphExplorer()
    explorer.set_graph(graph)
    
    quantification_info = {
        "existential_contexts": [],
        "universal_patterns": [],
        "nested_depth": 0,
        "variable_scoping": {}
    }
    
    # Find contexts that represent quantification
    for context_id, context in graph.context_manager.contexts.items():
        if context.depth > 0:  # Non-root contexts
            items_in_context = graph.context_manager.get_items_in_context(context_id)
            entities_in_context = [item for item in items_in_context if item in graph.entities]
            
            if entities_in_context:
                context_info = {
                    "context_id": str(context_id),
                    "depth": context.depth,
                    "polarity": "positive" if context.depth % 2 == 0 else "negative",
                    "entities": len(entities_in_context),
                    "type": "existential" if context.depth % 2 == 0 else "negation"
                }
                
                if context.depth % 2 == 0:
                    quantification_info["existential_contexts"].append(context_info)
                
                quantification_info["nested_depth"] = max(quantification_info["nested_depth"], context.depth)
    
    return quantification_info


def find_logical_patterns(graph: EGGraph) -> List[Dict[str, Any]]:
    """Find common logical patterns in the graph."""
    explorer = GraphExplorer()
    explorer.set_graph(graph)
    
    patterns = []
    
    # Look for universal quantification pattern: ~[exists x ~[P(x)]]
    for context_id, context in graph.context_manager.contexts.items():
        if context.depth == 1 and context.depth % 2 == 1:  # Negative context at depth 1
            child_contexts = explorer._get_child_contexts(context_id)
            for child_id in child_contexts:
                child_context = graph.context_manager.get_context(child_id)
                if child_context and child_context.depth == 2:  # Positive context at depth 2
                    grandchild_contexts = explorer._get_child_contexts(child_id)
                    for grandchild_id in grandchild_contexts:
                        grandchild_context = graph.context_manager.get_context(grandchild_id)
                        if grandchild_context and grandchild_context.depth == 3:  # Negative context at depth 3
                            patterns.append({
                                "type": "universal_quantification",
                                "outer_cut": str(context_id),
                                "existential_scope": str(child_id),
                                "inner_cut": str(grandchild_id),
                                "confidence": 0.9
                            })
    
    return patterns

