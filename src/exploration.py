"""
Multi-Scope Exploration System

This module provides tools for exploring existential graphs from different
perspectives and scopes. It enables users to examine graphs at various
levels of detail and from different logical and visual viewpoints.

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

from .eg_types import (
    Node, Edge, Context, Ligature, NodeId, EdgeId, ContextId, 
    LigatureId, ItemId
)
from .graph import EGGraph
from .context import ContextManager


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
    visible_nodes: Set[NodeId]
    visible_edges: Set[EdgeId]
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
        return (len(self.visible_nodes) + len(self.visible_edges) + 
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
    def depth(self) -> int:
        """Get the current depth."""
        return len(self.contexts) - 1


@dataclass(frozen=True)
class ExplorationState:
    """Current state of exploration."""
    current_view: ExplorationView
    navigation_path: NavigationPath
    focus_mode: FocusMode
    focus_target: Optional[ItemId]
    bookmarks: Dict[str, ViewScope]
    history: List[ViewScope]
    
    def can_go_back(self) -> bool:
        """Check if we can navigate back."""
        return len(self.history) > 1
    
    def can_zoom_in(self) -> bool:
        """Check if we can zoom in further."""
        return bool(self.current_view.scope_boundaries)
    
    def can_zoom_out(self) -> bool:
        """Check if we can zoom out."""
        return self.navigation_path.depth > 0


class GraphExplorer:
    """
    Main tool for exploring existential graphs at different scopes.
    
    Provides navigation, focusing, and scope management capabilities
    for understanding complex graph structures.
    """
    
    def __init__(self, graph: EGGraph):
        self.graph = graph
        self.current_state: Optional[ExplorationState] = None
        self._initialize_exploration()
    
    def get_overview(self) -> ExplorationView:
        """Get a high-level overview of the entire graph."""
        scope = ViewScope(
            scope_type=ScopeType.LEVEL_LIMITED,
            focus_context=self.graph.root_context_id,
            max_depth=2,
            include_ligatures=True,
            include_containing=False
        )
        return self._create_view(scope)
    
    def focus_on_context(self, context_id: ContextId, 
                        scope_type: ScopeType = ScopeType.CONTEXT_COMPLETE) -> ExplorationView:
        """Focus exploration on a specific context."""
        scope = ViewScope(
            scope_type=scope_type,
            focus_context=context_id,
            include_ligatures=True
        )
        view = self._create_view(scope)
        self._update_exploration_state(view, scope, FocusMode.CONTEXT_AREA, context_id)
        return view
    
    def focus_on_item(self, item_id: ItemId, 
                     context_radius: int = 1) -> ExplorationView:
        """Focus exploration on a specific item and its immediate context."""
        # Find the context containing this item
        containing_context = self._find_containing_context(item_id)
        
        scope = ViewScope(
            scope_type=ScopeType.LEVEL_LIMITED,
            focus_context=containing_context,
            max_depth=context_radius,
            include_ligatures=True
        )
        view = self._create_view(scope)
        view = replace(view, focus_items={item_id})
        self._update_exploration_state(view, scope, FocusMode.SINGLE_ITEM, item_id)
        return view
    
    def focus_on_ligature(self, ligature_id: LigatureId) -> ExplorationView:
        """Focus exploration on a ligature and all connected elements."""
        if ligature_id not in self.graph.ligatures:
            return self._create_empty_view("Ligature not found")
        
        ligature = self.graph.ligatures[ligature_id]
        connected_nodes = ligature.nodes
        
        # Find all contexts containing connected nodes
        contexts = set()
        for node_id in connected_nodes:
            context = self._find_containing_context(node_id)
            contexts.add(context)
        
        # Find a common ancestor context to focus on
        if contexts:
            focus_context = self._find_common_ancestor_context(list(contexts))
        else:
            focus_context = self.graph.root_context_id
        
        scope = ViewScope(
            scope_type=ScopeType.CONTEXT_COMPLETE,
            focus_context=focus_context,
            include_ligatures=True
        )
        view = self._create_view(scope)
        view = replace(view, focus_items=connected_nodes | {ligature_id})
        self._update_exploration_state(view, scope, FocusMode.LIGATURE_PATH, ligature_id)
        return view
    
    def zoom_in(self, target_context: Optional[ContextId] = None) -> ExplorationView:
        """Zoom in to show more detail."""
        if not self.current_state:
            return self.get_overview()
        
        current_scope = self.current_state.current_view.scope
        
        if target_context:
            new_focus = target_context
        else:
            # Find a child context to zoom into
            children = self.graph.context_manager.get_child_contexts(current_scope.focus_context)
            if children:
                new_focus = children[0]  # Choose first child
            else:
                return self.current_state.current_view  # Can't zoom in further
        
        new_scope = ViewScope(
            scope_type=current_scope.scope_type,
            focus_context=new_focus,
            max_depth=current_scope.max_depth,
            include_ligatures=current_scope.include_ligatures
        )
        
        view = self._create_view(new_scope)
        self._update_exploration_state(view, new_scope, self.current_state.focus_mode)
        return view
    
    def zoom_out(self) -> ExplorationView:
        """Zoom out to show broader context."""
        if not self.current_state:
            return self.get_overview()
        
        current_scope = self.current_state.current_view.scope
        current_context = current_scope.focus_context
        
        # Find parent context
        parent_context = self.graph.context_manager.get_parent_context(current_context)
        if parent_context is None:
            return self.current_state.current_view  # Already at root
        
        new_scope = ViewScope(
            scope_type=current_scope.scope_type,
            focus_context=parent_context,
            max_depth=current_scope.max_depth,
            include_ligatures=current_scope.include_ligatures,
            include_containing=True
        )
        
        view = self._create_view(new_scope)
        self._update_exploration_state(view, new_scope, self.current_state.focus_mode)
        return view
    
    def adjust_depth(self, new_depth: int) -> ExplorationView:
        """Adjust the depth of exploration."""
        if not self.current_state:
            return self.get_overview()
        
        current_scope = self.current_state.current_view.scope
        new_scope = current_scope.with_depth(new_depth)
        
        view = self._create_view(new_scope)
        self._update_exploration_state(view, new_scope, self.current_state.focus_mode)
        return view
    
    def navigate_to_context(self, context_id: ContextId) -> ExplorationView:
        """Navigate directly to a specific context."""
        return self.focus_on_context(context_id)
    
    def follow_ligature_path(self, start_node: NodeId, 
                           max_hops: int = 3) -> List[ExplorationView]:
        """Follow ligature connections from a starting node."""
        views = []
        visited = set()
        current_nodes = {start_node}
        
        for hop in range(max_hops):
            if not current_nodes or current_nodes.issubset(visited):
                break
            
            # Find ligatures connecting to current nodes
            connected_ligatures = set()
            for ligature_id, ligature in self.graph.ligatures.items():
                if ligature.nodes & current_nodes:
                    connected_ligatures.add(ligature_id)
            
            if not connected_ligatures:
                break
            
            # Create view for this hop
            view = self.focus_on_ligature(list(connected_ligatures)[0])
            views.append(view)
            
            # Find next nodes
            next_nodes = set()
            for ligature_id in connected_ligatures:
                ligature = self.graph.ligatures[ligature_id]
                next_nodes.update(ligature.nodes)
            
            visited.update(current_nodes)
            current_nodes = next_nodes - visited
        
        return views
    
    def search_for_pattern(self, pattern_description: str) -> List[ExplorationView]:
        """Search for elements matching a pattern description."""
        # This would implement pattern searching
        # For now, return empty list
        return []
    
    def bookmark_current_view(self, name: str) -> bool:
        """Bookmark the current view for later return."""
        if not self.current_state:
            return False
        
        try:
            bookmarks = dict(self.current_state.bookmarks)
            bookmarks[name] = self.current_state.current_view.scope
            
            new_state = replace(self.current_state, bookmarks=bookmarks)
            self.current_state = new_state
            return True
        except Exception:
            return False
    
    def go_to_bookmark(self, name: str) -> Optional[ExplorationView]:
        """Navigate to a bookmarked view."""
        if not self.current_state or name not in self.current_state.bookmarks:
            return None
        
        scope = self.current_state.bookmarks[name]
        view = self._create_view(scope)
        self._update_exploration_state(view, scope, FocusMode.CONTEXT_AREA)
        return view
    
    def get_navigation_options(self) -> Dict[str, List[str]]:
        """Get available navigation options from current position."""
        if not self.current_state:
            return {}
        
        options = {}
        current_context = self.current_state.current_view.scope.focus_context
        
        # Child contexts (zoom in options)
        children = self.graph.context_manager.get_child_contexts(current_context)
        if children:
            options["zoom_in"] = [f"Context {ctx}" for ctx in children]
        
        # Parent context (zoom out option)
        parent = self.graph.context_manager.get_parent_context(current_context)
        if parent:
            options["zoom_out"] = [f"Context {parent}"]
        
        # Sibling contexts (lateral navigation)
        if parent:
            siblings = self.graph.context_manager.get_child_contexts(parent)
            siblings = [ctx for ctx in siblings if ctx != current_context]
            if siblings:
                options["siblings"] = [f"Context {ctx}" for ctx in siblings]
        
        # Connected elements via ligatures
        connected = self._find_ligature_connected_contexts(current_context)
        if connected:
            options["ligature_paths"] = [f"Context {ctx}" for ctx in connected]
        
        return options
    
    def get_context_summary(self, context_id: ContextId) -> Dict[str, Any]:
        """Get a summary of a context's contents."""
        if context_id not in self.graph.context_manager.contexts:
            return {"error": "Context not found"}
        
        context = self.graph.context_manager.contexts[context_id]
        items = self.graph.get_items_in_context(context_id)
        
        # Count different types of items
        nodes = [item for item in items if item in self.graph.nodes]
        edges = [item for item in items if item in self.graph.edges]
        
        # Find ligatures that connect to items in this context
        relevant_ligatures = []
        for ligature_id, ligature in self.graph.ligatures.items():
            if ligature.nodes & set(nodes):
                relevant_ligatures.append(ligature_id)
        
        # Get child contexts
        children = self.graph.context_manager.get_child_contexts(context_id)
        
        return {
            "context_id": context_id,
            "context_type": context.context_type,
            "depth": context.depth,
            "is_positive": context.is_positive,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "ligature_count": len(relevant_ligatures),
            "child_context_count": len(children),
            "total_items": len(items)
        }
    
    def _create_view(self, scope: ViewScope) -> ExplorationView:
        """Create an exploration view based on the given scope."""
        visible_nodes = set()
        visible_edges = set()
        visible_contexts = set()
        visible_ligatures = set()
        context_hierarchy = {}
        item_locations = {}
        scope_boundaries = set()
        
        # Start with the focus context
        contexts_to_process = [(scope.focus_context, 0)]
        processed_contexts = set()
        
        while contexts_to_process:
            context_id, depth = contexts_to_process.pop(0)
            
            if context_id in processed_contexts:
                continue
            processed_contexts.add(context_id)
            
            # Add this context to visible contexts
            visible_contexts.add(context_id)
            
            # Get items in this context
            items = self.graph.get_items_in_context(context_id)
            
            for item_id in items:
                item_locations[item_id] = context_id
                
                if item_id in self.graph.nodes:
                    visible_nodes.add(item_id)
                elif item_id in self.graph.edges:
                    visible_edges.add(item_id)
            
            # Handle child contexts based on scope type
            children = self.graph.context_manager.get_child_contexts(context_id)
            context_hierarchy[context_id] = children
            
            if scope.scope_type == ScopeType.AREA_ONLY:
                # Don't descend into child contexts
                scope_boundaries.update(children)
            elif scope.scope_type == ScopeType.CONTEXT_COMPLETE:
                # Include all nested content
                for child in children:
                    contexts_to_process.append((child, depth + 1))
            elif scope.scope_type == ScopeType.LEVEL_LIMITED:
                # Include children up to max depth
                if scope.max_depth is None or depth < scope.max_depth:
                    for child in children:
                        contexts_to_process.append((child, depth + 1))
                else:
                    scope_boundaries.update(children)
        
        # Handle ligatures
        if scope.include_ligatures:
            for ligature_id, ligature in self.graph.ligatures.items():
                # Include ligature if any of its nodes are visible
                if ligature.nodes & visible_nodes:
                    visible_ligatures.add(ligature_id)
        
        # Generate navigation hints
        navigation_hints = self._generate_navigation_hints(scope, scope_boundaries)
        
        return ExplorationView(
            scope=scope,
            visible_nodes=visible_nodes,
            visible_edges=visible_edges,
            visible_contexts=visible_contexts,
            visible_ligatures=visible_ligatures,
            focus_items=set(),
            context_hierarchy=context_hierarchy,
            item_locations=item_locations,
            scope_boundaries=scope_boundaries,
            navigation_hints=navigation_hints
        )
    
    def _create_empty_view(self, message: str) -> ExplorationView:
        """Create an empty view with a message."""
        return ExplorationView(
            scope=ViewScope(ScopeType.AREA_ONLY, self.graph.root_context_id),
            visible_nodes=set(),
            visible_edges=set(),
            visible_contexts=set(),
            visible_ligatures=set(),
            focus_items=set(),
            context_hierarchy={},
            item_locations={},
            scope_boundaries=set(),
            navigation_hints=[message]
        )
    
    def _update_exploration_state(self, view: ExplorationView, scope: ViewScope,
                                focus_mode: FocusMode, focus_target: Optional[ItemId] = None):
        """Update the current exploration state."""
        if self.current_state:
            # Add current scope to history
            history = list(self.current_state.history)
            history.append(self.current_state.current_view.scope)
            
            # Limit history size
            if len(history) > 20:
                history.pop(0)
            
            bookmarks = self.current_state.bookmarks
        else:
            history = []
            bookmarks = {}
        
        # Create navigation path
        path_contexts = []
        path_descriptions = []
        path_depths = []
        
        current = scope.focus_context
        while current is not None:
            path_contexts.insert(0, current)
            context = self.graph.context_manager.contexts[current]
            path_descriptions.insert(0, f"{context.context_type} (depth {context.depth})")
            path_depths.insert(0, context.depth)
            current = self.graph.context_manager.get_parent_context(current)
        
        navigation_path = NavigationPath(path_contexts, path_descriptions, path_depths)
        
        self.current_state = ExplorationState(
            current_view=view,
            navigation_path=navigation_path,
            focus_mode=focus_mode,
            focus_target=focus_target,
            bookmarks=bookmarks,
            history=history
        )
    
    def _find_containing_context(self, item_id: ItemId) -> ContextId:
        """Find the context that contains a specific item."""
        for context_id in self.graph.context_manager.contexts:
            items = self.graph.get_items_in_context(context_id)
            if item_id in items:
                return context_id
        return self.graph.root_context_id
    
    def _find_common_ancestor_context(self, contexts: List[ContextId]) -> ContextId:
        """Find the common ancestor of multiple contexts."""
        if not contexts:
            return self.graph.root_context_id
        
        if len(contexts) == 1:
            return contexts[0]
        
        # Get paths to root for each context
        paths = []
        for context_id in contexts:
            path = []
            current = context_id
            while current is not None:
                path.insert(0, current)
                current = self.graph.context_manager.get_parent_context(current)
            paths.append(path)
        
        # Find common prefix
        common_ancestor = self.graph.root_context_id
        min_length = min(len(path) for path in paths)
        
        for i in range(min_length):
            if all(path[i] == paths[0][i] for path in paths):
                common_ancestor = paths[0][i]
            else:
                break
        
        return common_ancestor
    
    def _find_ligature_connected_contexts(self, context_id: ContextId) -> Set[ContextId]:
        """Find contexts connected via ligatures."""
        connected = set()
        
        # Get items in this context
        items = self.graph.get_items_in_context(context_id)
        nodes_in_context = [item for item in items if item in self.graph.nodes]
        
        # Find ligatures connecting to these nodes
        for ligature_id, ligature in self.graph.ligatures.items():
            if ligature.nodes & set(nodes_in_context):
                # Find contexts containing other nodes in this ligature
                for node_id in ligature.nodes:
                    if node_id not in nodes_in_context:
                        other_context = self._find_containing_context(node_id)
                        if other_context != context_id:
                            connected.add(other_context)
        
        return connected
    
    def _generate_navigation_hints(self, scope: ViewScope, 
                                 boundaries: Set[ContextId]) -> List[str]:
        """Generate helpful navigation hints."""
        hints = []
        
        if boundaries:
            hints.append(f"Can zoom into {len(boundaries)} child contexts")
        
        if scope.focus_context != self.graph.root_context_id:
            hints.append("Can zoom out to parent context")
        
        if scope.scope_type == ScopeType.LEVEL_LIMITED and scope.max_depth:
            hints.append(f"Currently showing {scope.max_depth} levels deep")
        
        return hints
    
    def _initialize_exploration(self):
        """Initialize exploration with overview."""
        overview = self.get_overview()
        self._update_exploration_state(overview, overview.scope, FocusMode.CONTEXT_AREA)

