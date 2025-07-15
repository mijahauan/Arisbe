"""
Intelligent pattern recognition for logical constructs in existential graphs.

This module provides sophisticated pattern recognition algorithms that can
identify logical patterns (forall, if, or) regardless of how they were
created, enabling robust CLIF reconstruction.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from .graph import EGGraph
from .context import ContextManager


@dataclass
class PatternMatch:
    """A recognized logical pattern in the graph."""
    pattern_type: str
    confidence: float
    context_id: ContextId
    components: Dict[str, Any]
    clif_representation: str
    metadata: Dict[str, Any]


@dataclass
class PatternContext:
    """Context information for pattern recognition."""
    context: Context
    parent_context: Optional[Context]
    child_contexts: List[Context]
    items_in_context: Set[ItemId]
    depth: int
    polarity: str  # 'positive' or 'negative'


class PatternRecognizer(ABC):
    """Abstract base class for pattern recognizers."""
    
    @abstractmethod
    def recognize(self, graph: EGGraph, context_info: PatternContext) -> List[PatternMatch]:
        """Recognize patterns in the given context.
        
        Args:
            graph: The existential graph to analyze.
            context_info: Information about the context being analyzed.
            
        Returns:
            List of recognized patterns with confidence scores.
        """
        pass
    
    @abstractmethod
    def get_pattern_type(self) -> str:
        """Get the type of pattern this recognizer handles."""
        pass


class UniversalQuantifierRecognizer(PatternRecognizer):
    """Recognizes universal quantification patterns: ~[exists x ~[P(x)]]"""
    
    def get_pattern_type(self) -> str:
        return "universal_quantifier"
    
    def recognize(self, graph: EGGraph, context_info: PatternContext) -> List[PatternMatch]:
        """Recognize universal quantification patterns."""
        matches = []
        
        # Universal quantification pattern: ~[exists x ~[P(x)]]
        # This creates: negative context -> positive context -> negative context with predicate
        if context_info.polarity == 'negative' and len(context_info.child_contexts) >= 1:
            for child_context in context_info.child_contexts:
                child_info = self._get_context_info(graph, child_context)
                
                # Look for positive context (existential scope)
                if (child_info.polarity == 'positive' and 
                    len(child_info.child_contexts) >= 1):
                    
                    # Look for nested negative context (predicate negation)
                    for grandchild_context in child_info.child_contexts:
                        grandchild_info = self._get_context_info(graph, grandchild_context)
                        
                        if (grandchild_info.polarity == 'negative' and 
                            len(grandchild_info.items_in_context) > 0):
                            
                            # Analyze the content for quantified variables
                            variables = self._find_quantified_variables(graph, grandchild_info)
                            predicates = self._find_predicates(graph, grandchild_info)
                            
                            if variables and predicates:
                                confidence = self._calculate_confidence(variables, predicates, grandchild_info)
                                
                                if confidence > 0.7:  # Threshold for recognition
                                    clif_repr = self._generate_clif_representation(variables, predicates)
                                    
                                    match = PatternMatch(
                                        pattern_type=self.get_pattern_type(),
                                        confidence=confidence,
                                        context_id=context_info.context.id,
                                        components={
                                            'variables': variables,
                                            'predicates': predicates,
                                            'predicate_context': grandchild_context.id,
                                            'existential_context': child_context.id,
                                            'universal_context': context_info.context.id
                                        },
                                        clif_representation=clif_repr,
                                        metadata={
                                            'depth': context_info.depth,
                                            'variable_count': len(variables),
                                            'predicate_count': len(predicates)
                                        }
                                    )
                                    matches.append(match)
        
        return matches
    
    def _get_context_info(self, graph: EGGraph, context: Context) -> PatternContext:
        """Get detailed information about a context."""
        parent_context = None
        if context.parent_context:
            parent_context = graph.context_manager.get_context(context.parent_context)
        
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context.id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context.id:
                child_contexts.append(child_ctx)
        
        items_in_context = graph.get_items_in_context(context.id)
        polarity = 'positive' if context.is_positive else 'negative'
        
        return PatternContext(
            context=context,
            parent_context=parent_context,
            child_contexts=child_contexts,
            items_in_context=items_in_context,
            depth=context.depth,
            polarity=polarity
        )
    
    def _find_quantified_variables(self, graph: EGGraph, context_info: PatternContext) -> List[str]:
        """Find variables that appear to be quantified."""
        variables = []
        
        # Look for nodes that could be variables
        for item_id in context_info.items_in_context:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                if (node.node_type == 'variable' or 
                    (node.node_type == 'term' and 
                     self._looks_like_variable(node.properties.get('value', '')))):
                    var_name = node.properties.get('value') or node.properties.get('name')
                    if var_name and var_name not in variables:
                        variables.append(var_name)
        
        return variables
    
    def _find_predicates(self, graph: EGGraph, context_info: PatternContext) -> List[Dict[str, Any]]:
        """Find predicates in the context."""
        predicates = []
        
        # Look for predicate nodes and their relationships
        for item_id in context_info.items_in_context:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                if node.node_type == 'predicate':
                    # Find arguments connected to this predicate
                    incident_edges = graph.find_incident_edges(node.id)
                    arguments = []
                    
                    for edge in incident_edges:
                        if edge.edge_type == 'predication':
                            for arg_id in edge.nodes:
                                if arg_id != node.id and arg_id in graph.nodes:
                                    arg_node = graph.nodes[arg_id]
                                    arg_value = (arg_node.properties.get('value') or 
                                               arg_node.properties.get('name'))
                                    if arg_value:
                                        arguments.append(arg_value)
                    
                    predicate_info = {
                        'name': node.properties.get('name', ''),
                        'arguments': arguments,
                        'node_id': node.id
                    }
                    predicates.append(predicate_info)
        
        return predicates
    
    def _looks_like_variable(self, term: str) -> bool:
        """Check if a term looks like a variable."""
        if not term:
            return False
        
        # Variables typically start with lowercase or are single letters
        return (len(term) == 1 and term.islower()) or term.islower()
    
    def _calculate_confidence(self, variables: List[str], predicates: List[Dict[str, Any]], 
                            context_info: PatternContext) -> float:
        """Calculate confidence score for universal quantification pattern."""
        confidence = 0.0
        
        # Base confidence for having variables and predicates
        if variables and predicates:
            confidence += 0.5
        
        # Bonus for variables appearing in predicates
        for predicate in predicates:
            for var in variables:
                if var in predicate['arguments']:
                    confidence += 0.2
        
        # Bonus for proper nesting structure
        if context_info.depth >= 2:  # At least double-nested
            confidence += 0.2
        
        # Penalty for too many unrelated items
        total_items = len(context_info.items_in_context)
        expected_items = len(variables) + len(predicates)
        if total_items > expected_items * 2:
            confidence -= 0.1
        
        return min(confidence, 1.0)
    
    def _generate_clif_representation(self, variables: List[str], 
                                    predicates: List[Dict[str, Any]]) -> str:
        """Generate CLIF representation for the universal quantification."""
        var_list = " ".join(variables)
        
        if len(predicates) == 1:
            pred = predicates[0]
            pred_str = f"({pred['name']} {' '.join(pred['arguments'])})"
        else:
            pred_strs = []
            for pred in predicates:
                pred_strs.append(f"({pred['name']} {' '.join(pred['arguments'])})")
            pred_str = f"(and {' '.join(pred_strs)})"
        
        return f"(forall ({var_list}) {pred_str})"


class ImplicationRecognizer(PatternRecognizer):
    """Recognizes implication patterns: ~[P ~[Q]]"""
    
    def get_pattern_type(self) -> str:
        return "implication"
    
    def recognize(self, graph: EGGraph, context_info: PatternContext) -> List[PatternMatch]:
        """Recognize implication patterns."""
        matches = []
        
        # Implication pattern: ~[P ~[Q]]
        # This creates: negative context (depth 1) with P and positive context (depth 2) with Q
        if (context_info.polarity == 'negative' and 
            len(context_info.child_contexts) >= 1 and
            len(context_info.items_in_context) > 0):
            
            # Look for antecedent in the current context (direct items)
            antecedent = self._extract_antecedent(graph, context_info)
            
            # Look for consequent in nested context (should be positive polarity at depth 2)
            for child_context in context_info.child_contexts:
                child_info = self._get_context_info(graph, child_context)
                
                # For implication, the inner context should be positive (depth 2)
                # This represents the negation of the consequent
                if child_info.polarity == 'positive':
                    consequent = self._extract_consequent(graph, child_info)
                    
                    if antecedent and consequent:
                        confidence = self._calculate_implication_confidence(
                            antecedent, consequent, context_info, child_info
                        )
                        
                        if confidence > 0.6:
                            clif_repr = f"(if {antecedent['clif']} {consequent['clif']})"
                            
                            match = PatternMatch(
                                pattern_type=self.get_pattern_type(),
                                confidence=confidence,
                                context_id=context_info.context.id,
                                components={
                                    'antecedent': antecedent,
                                    'consequent': consequent,
                                    'outer_context': context_info.context.id,
                                    'inner_context': child_context.id
                                },
                                clif_representation=clif_repr,
                                metadata={
                                    'depth': context_info.depth,
                                    'antecedent_complexity': len(antecedent.get('components', [])),
                                    'consequent_complexity': len(consequent.get('components', []))
                                }
                            )
                            matches.append(match)
        
        return matches
    
    def _get_context_info(self, graph: EGGraph, context: Context) -> PatternContext:
        """Get detailed information about a context."""
        # Same implementation as UniversalQuantifierRecognizer
        parent_context = None
        if context.parent_context:
            parent_context = graph.context_manager.get_context(context.parent_context)
        
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context.id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context.id:
                child_contexts.append(child_ctx)
        
        items_in_context = graph.get_items_in_context(context.id)
        polarity = 'positive' if context.is_positive else 'negative'
        
        return PatternContext(
            context=context,
            parent_context=parent_context,
            child_contexts=child_contexts,
            items_in_context=items_in_context,
            depth=context.depth,
            polarity=polarity
        )
    
    def _extract_antecedent(self, graph: EGGraph, context_info: PatternContext) -> Optional[Dict[str, Any]]:
        """Extract the antecedent from the context."""
        # Look for items that are not in child contexts (direct items)
        direct_items = set(context_info.items_in_context)
        
        # Remove items that are in child contexts
        for child_context in context_info.child_contexts:
            child_items = graph.get_items_in_context(child_context.id)
            direct_items -= child_items
        
        if direct_items:
            clif_parts = []
            components = []
            
            for item_id in direct_items:
                if item_id in graph.nodes:
                    node = graph.nodes[item_id]
                    if node.node_type == 'predicate':
                        pred_clif = self._node_to_clif(graph, node)
                        if pred_clif:
                            clif_parts.append(pred_clif)
                            components.append({'type': 'predicate', 'node_id': item_id})
            
            if clif_parts:
                clif_repr = clif_parts[0] if len(clif_parts) == 1 else f"(and {' '.join(clif_parts)})"
                return {
                    'clif': clif_repr,
                    'components': components,
                    'items': list(direct_items)
                }
        
        return None
    
    def _extract_consequent(self, graph: EGGraph, context_info: PatternContext) -> Optional[Dict[str, Any]]:
        """Extract the consequent from the nested context."""
        if context_info.items_in_context:
            clif_parts = []
            components = []
            
            for item_id in context_info.items_in_context:
                if item_id in graph.nodes:
                    node = graph.nodes[item_id]
                    if node.node_type == 'predicate':
                        pred_clif = self._node_to_clif(graph, node)
                        if pred_clif:
                            clif_parts.append(pred_clif)
                            components.append({'type': 'predicate', 'node_id': item_id})
            
            if clif_parts:
                clif_repr = clif_parts[0] if len(clif_parts) == 1 else f"(and {' '.join(clif_parts)})"
                return {
                    'clif': clif_repr,
                    'components': components,
                    'items': list(context_info.items_in_context)
                }
        
        return None
    
    def _node_to_clif(self, graph: EGGraph, node: Node) -> Optional[str]:
        """Convert a node to CLIF representation."""
        if node.node_type == 'predicate':
            pred_name = node.properties.get('name', '')
            
            # Find arguments
            incident_edges = graph.find_incident_edges(node.id)
            arguments = []
            
            for edge in incident_edges:
                if edge.edge_type == 'predication':
                    for arg_id in edge.nodes:
                        if arg_id != node.id and arg_id in graph.nodes:
                            arg_node = graph.nodes[arg_id]
                            arg_value = (arg_node.properties.get('value') or 
                                       arg_node.properties.get('name'))
                            if arg_value:
                                arguments.append(arg_value)
            
            if pred_name:
                if arguments:
                    return f"({pred_name} {' '.join(arguments)})"
                else:
                    return f"({pred_name})"
        
        return None
    
    def _calculate_implication_confidence(self, antecedent: Dict[str, Any], 
                                        consequent: Dict[str, Any],
                                        outer_context: PatternContext,
                                        inner_context: PatternContext) -> float:
        """Calculate confidence for implication pattern."""
        confidence = 0.0
        
        # Base confidence for having both parts
        if antecedent and consequent:
            confidence += 0.4
        
        # Bonus for proper nesting structure
        if outer_context.polarity == 'negative' and inner_context.polarity == 'negative':
            confidence += 0.3
        
        # Bonus for reasonable complexity
        ant_complexity = len(antecedent.get('components', []))
        cons_complexity = len(consequent.get('components', []))
        
        if 1 <= ant_complexity <= 3 and 1 <= cons_complexity <= 3:
            confidence += 0.2
        
        # Bonus for shared variables
        ant_clif = antecedent.get('clif', '')
        cons_clif = consequent.get('clif', '')
        
        # Simple heuristic: look for common terms
        ant_terms = set(ant_clif.split())
        cons_terms = set(cons_clif.split())
        shared_terms = ant_terms & cons_terms
        
        if shared_terms:
            confidence += 0.1
        
        return min(confidence, 1.0)


class DisjunctionRecognizer(PatternRecognizer):
    """Recognizes disjunction patterns: ~[~[P] ~[Q]]"""
    
    def get_pattern_type(self) -> str:
        return "disjunction"
    
    def recognize(self, graph: EGGraph, context_info: PatternContext) -> List[PatternMatch]:
        """Recognize disjunction patterns."""
        matches = []
        
        # Disjunction pattern: ~[~[P] ~[Q]]
        # This creates: negative context (depth 1) with multiple positive contexts (depth 2)
        if (context_info.polarity == 'negative' and 
            len(context_info.child_contexts) >= 2 and
            len(context_info.items_in_context) == 0):  # No direct items, only child contexts
            
            disjuncts = []
            
            # Look for multiple positive child contexts (each represents a negated disjunct)
            for child_context in context_info.child_contexts:
                child_info = self._get_context_info(graph, child_context)
                
                # Each disjunct should be in a positive context (depth 2)
                if (child_info.polarity == 'positive' and 
                    len(child_info.items_in_context) > 0):
                    
                    disjunct = self._extract_disjunct(graph, child_info)
                    if disjunct:
                        disjuncts.append(disjunct)
            
            # Need at least 2 disjuncts for a disjunction
            if len(disjuncts) >= 2:
                confidence = self._calculate_disjunction_confidence(disjuncts, context_info)
                
                if confidence > 0.6:
                    clif_parts = [d['clif'] for d in disjuncts]
                    clif_repr = f"(or {' '.join(clif_parts)})"
                    
                    match = PatternMatch(
                        pattern_type=self.get_pattern_type(),
                        confidence=confidence,
                        context_id=context_info.context.id,
                        components={
                            'disjuncts': disjuncts,
                            'outer_context': context_info.context.id,
                            'disjunct_contexts': [ctx.id for ctx in context_info.child_contexts]
                        },
                        clif_representation=clif_repr,
                        metadata={
                            'depth': context_info.depth,
                            'disjunct_count': len(disjuncts),
                            'total_complexity': sum(len(d.get('components', [])) for d in disjuncts)
                        }
                    )
                    matches.append(match)
        
        return matches
    
    def _get_context_info(self, graph: EGGraph, context: Context) -> PatternContext:
        """Get detailed information about a context."""
        # Same implementation as other recognizers
        parent_context = None
        if context.parent_context:
            parent_context = graph.context_manager.get_context(context.parent_context)
        
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context.id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context.id:
                child_contexts.append(child_ctx)
        
        items_in_context = graph.get_items_in_context(context.id)
        polarity = 'positive' if context.is_positive else 'negative'
        
        return PatternContext(
            context=context,
            parent_context=parent_context,
            child_contexts=child_contexts,
            items_in_context=items_in_context,
            depth=context.depth,
            polarity=polarity
        )
    
    def _extract_disjunct(self, graph: EGGraph, context_info: PatternContext) -> Optional[Dict[str, Any]]:
        """Extract a disjunct from a context."""
        if context_info.items_in_context:
            clif_parts = []
            components = []
            
            for item_id in context_info.items_in_context:
                if item_id in graph.nodes:
                    node = graph.nodes[item_id]
                    if node.node_type == 'predicate':
                        pred_clif = self._node_to_clif(graph, node)
                        if pred_clif:
                            clif_parts.append(pred_clif)
                            components.append({'type': 'predicate', 'node_id': item_id})
            
            if clif_parts:
                clif_repr = clif_parts[0] if len(clif_parts) == 1 else f"(and {' '.join(clif_parts)})"
                return {
                    'clif': clif_repr,
                    'components': components,
                    'items': list(context_info.items_in_context)
                }
        
        return None
    
    def _node_to_clif(self, graph: EGGraph, node: Node) -> Optional[str]:
        """Convert a node to CLIF representation."""
        # Same implementation as ImplicationRecognizer
        if node.node_type == 'predicate':
            pred_name = node.properties.get('name', '')
            
            # Find arguments
            incident_edges = graph.find_incident_edges(node.id)
            arguments = []
            
            for edge in incident_edges:
                if edge.edge_type == 'predication':
                    for arg_id in edge.nodes:
                        if arg_id != node.id and arg_id in graph.nodes:
                            arg_node = graph.nodes[arg_id]
                            arg_value = (arg_node.properties.get('value') or 
                                       arg_node.properties.get('name'))
                            if arg_value:
                                arguments.append(arg_value)
            
            if pred_name:
                if arguments:
                    return f"({pred_name} {' '.join(arguments)})"
                else:
                    return f"({pred_name})"
        
        return None
    
    def _calculate_disjunction_confidence(self, disjuncts: List[Dict[str, Any]], 
                                        context_info: PatternContext) -> float:
        """Calculate confidence for disjunction pattern."""
        confidence = 0.0
        
        # Base confidence for having multiple disjuncts
        if len(disjuncts) >= 2:
            confidence += 0.4
        
        # Bonus for proper structure
        if context_info.polarity == 'negative':
            confidence += 0.2
        
        # Bonus for reasonable number of disjuncts
        if 2 <= len(disjuncts) <= 4:
            confidence += 0.2
        
        # Bonus for similar complexity disjuncts
        complexities = [len(d.get('components', [])) for d in disjuncts]
        if complexities and max(complexities) - min(complexities) <= 1:
            confidence += 0.1
        
        # Bonus for non-trivial disjuncts
        if all(len(d.get('components', [])) >= 1 for d in disjuncts):
            confidence += 0.1
        
        return min(confidence, 1.0)


class PatternRecognitionEngine:
    """Main engine for recognizing logical patterns in existential graphs."""
    
    def __init__(self):
        """Initialize the pattern recognition engine."""
        self.recognizers = [
            UniversalQuantifierRecognizer(),
            ImplicationRecognizer(),
            DisjunctionRecognizer()
        ]
    
    def recognize_patterns(self, graph: EGGraph) -> List[PatternMatch]:
        """Recognize all patterns in the graph.
        
        Args:
            graph: The existential graph to analyze.
            
        Returns:
            List of all recognized patterns sorted by confidence.
        """
        all_matches = []
        
        # Analyze each context in the graph
        for context_id, context in graph.context_manager.contexts.items():
            context_info = self._get_context_info(graph, context)
            
            # Run all recognizers on this context
            for recognizer in self.recognizers:
                matches = recognizer.recognize(graph, context_info)
                all_matches.extend(matches)
        
        # Sort by confidence (highest first)
        all_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        # Remove overlapping patterns (keep highest confidence)
        filtered_matches = self._filter_overlapping_patterns(all_matches)
        
        return filtered_matches
    
    def _get_context_info(self, graph: EGGraph, context: Context) -> PatternContext:
        """Get detailed information about a context."""
        parent_context = None
        if context.parent_context:
            parent_context = graph.context_manager.get_context(context.parent_context)
        
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context.id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context.id:
                child_contexts.append(child_ctx)
        
        items_in_context = graph.get_items_in_context(context.id)
        polarity = 'positive' if context.is_positive else 'negative'
        
        return PatternContext(
            context=context,
            parent_context=parent_context,
            child_contexts=child_contexts,
            items_in_context=items_in_context,
            depth=context.depth,
            polarity=polarity
        )
    
    def _filter_overlapping_patterns(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Filter out overlapping patterns, keeping the highest confidence ones."""
        filtered = []
        used_contexts = set()
        
        for match in matches:
            # Check if this context is already used by a higher-confidence pattern
            if match.context_id not in used_contexts:
                filtered.append(match)
                used_contexts.add(match.context_id)
                
                # Also mark any nested contexts as used
                if 'inner_contexts' in match.components:
                    for ctx_id in match.components['inner_contexts']:
                        used_contexts.add(ctx_id)
                elif 'inner_context' in match.components:
                    used_contexts.add(match.components['inner_context'])
        
        return filtered
    
    def generate_clif_from_patterns(self, graph: EGGraph, patterns: List[PatternMatch]) -> str:
        """Generate CLIF representation using recognized patterns.
        
        Args:
            graph: The existential graph.
            patterns: List of recognized patterns.
            
        Returns:
            CLIF representation of the graph.
        """
        if not patterns:
            return self._generate_fallback_clif(graph)
        
        # Group patterns by context hierarchy
        root_patterns = []
        for pattern in patterns:
            context = graph.context_manager.get_context(pattern.context_id)
            if context and context.parent_context == graph.root_context_id:
                root_patterns.append(pattern)
        
        if len(root_patterns) == 1:
            return root_patterns[0].clif_representation
        elif len(root_patterns) > 1:
            clif_parts = [p.clif_representation for p in root_patterns]
            return f"(and {' '.join(clif_parts)})"
        else:
            return self._generate_fallback_clif(graph)
    
    def _generate_fallback_clif(self, graph: EGGraph) -> str:
        """Generate fallback CLIF when no patterns are recognized."""
        # Simple fallback: list all predicates in the root context
        root_items = graph.get_items_in_context(graph.root_context_id)
        predicates = []
        
        for item_id in root_items:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                if node.node_type == 'predicate':
                    pred_name = node.properties.get('name', '')
                    if pred_name:
                        predicates.append(f"({pred_name})")
        
        if len(predicates) == 1:
            return predicates[0]
        elif len(predicates) > 1:
            return f"(and {' '.join(predicates)})"
        else:
            return "(and)"  # Empty conjunction

