"""
Enhanced CLIF generator with pattern-aware output and full ISO 24707 support.

This module provides sophisticated CLIF generation that leverages pattern
recognition to produce clean, readable CLIF output that preserves the
logical structure and intent of existential graphs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId, ItemId,
    ValidationError, pmap, pset
)
from .graph import EGGraph
from .pattern_recognizer import PatternRecognitionEngine, PatternMatch


@dataclass
class CLIFGenerationOptions:
    """Options for CLIF generation."""
    use_pattern_recognition: bool = True
    preserve_comments: bool = True
    include_metadata: bool = False
    format_output: bool = True
    fallback_to_canonical: bool = True
    variable_naming_strategy: str = 'alphabetic'  # 'alphabetic', 'descriptive', 'original'


@dataclass
class CLIFGenerationResult:
    """Result of CLIF generation."""
    clif_text: str
    patterns_used: List[PatternMatch]
    warnings: List[str]
    metadata: Dict[str, Any]


class CLIFGenerator:
    """Enhanced CLIF generator with pattern recognition."""
    
    def __init__(self, options: Optional[CLIFGenerationOptions] = None):
        """Initialize the CLIF generator.
        
        Args:
            options: Generation options. Uses defaults if None.
        """
        self.options = options or CLIFGenerationOptions()
        self.pattern_engine = PatternRecognitionEngine()
        self.variable_counter = 0
        self.variable_mapping = {}
        
    def generate(self, graph: EGGraph, comments: List[str] = None, 
                imports: List[str] = None) -> CLIFGenerationResult:
        """Generate CLIF representation of an existential graph.
        
        Args:
            graph: The existential graph to convert.
            comments: Optional comments to include.
            imports: Optional import statements.
            
        Returns:
            CLIFGenerationResult with the generated CLIF and metadata.
        """
        # Reset state
        self.variable_counter = 0
        self.variable_mapping = {}
        warnings = []
        
        # Recognize patterns if enabled
        patterns = []
        if self.options.use_pattern_recognition:
            try:
                patterns = self.pattern_engine.recognize_patterns(graph)
            except Exception as e:
                warnings.append(f"Pattern recognition failed: {str(e)}")
        
        # Generate CLIF text
        clif_parts = []
        
        # Add comments if requested
        if self.options.preserve_comments and comments:
            for comment in comments:
                clif_parts.append(f"/* {comment} */")
        
        # Add imports if present
        if imports:
            for import_uri in imports:
                clif_parts.append(f"(cl:imports \"{import_uri}\")")
        
        # Generate main content
        if patterns and self.options.use_pattern_recognition:
            main_content = self.pattern_engine.generate_clif_from_patterns(graph, patterns)
        else:
            if self.options.fallback_to_canonical:
                main_content = self._generate_canonical_clif(graph)
            else:
                warnings.append("No patterns recognized and fallback disabled")
                main_content = "(and)"
        
        if main_content and main_content != "(and)":
            clif_parts.append(main_content)
        
        # Combine and format
        clif_text = "\n".join(clif_parts)
        
        if self.options.format_output:
            clif_text = self._format_clif(clif_text)
        
        # Prepare metadata
        metadata = {
            'pattern_count': len(patterns),
            'variable_count': self.variable_counter,
            'context_count': len(graph.context_manager.contexts),
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
            'ligature_count': len(graph.ligatures)
        }
        
        if self.options.include_metadata:
            metadata.update({
                'patterns_by_type': self._group_patterns_by_type(patterns),
                'context_hierarchy': self._analyze_context_hierarchy(graph),
                'variable_mapping': dict(self.variable_mapping)
            })
        
        return CLIFGenerationResult(
            clif_text=clif_text,
            patterns_used=patterns,
            warnings=warnings,
            metadata=metadata
        )
    
    def _generate_canonical_clif(self, graph: EGGraph) -> str:
        """Generate canonical CLIF representation without pattern recognition."""
        # Start from root context and traverse
        root_content = self._generate_context_content(graph, graph.root_context_id)
        
        if not root_content:
            return "(and)"
        
        return root_content
    
    def _generate_context_content(self, graph: EGGraph, context_id: ContextId) -> str:
        """Generate CLIF content for a specific context."""
        context = graph.context_manager.get_context(context_id)
        if not context:
            return ""
        
        # Get items directly in this context (not in child contexts)
        direct_items = self._get_direct_items(graph, context_id)
        
        # Get child contexts
        child_contexts = []
        for ctx_id in graph.context_manager.get_descendants(context_id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context_id:
                child_contexts.append(child_ctx)
        
        content_parts = []
        
        # Process direct items (predicates, etc.)
        for item_id in direct_items:
            if item_id in graph.nodes:
                node = graph.nodes[item_id]
                if node.node_type == 'predicate':
                    pred_clif = self._node_to_clif(graph, node)
                    if pred_clif:
                        content_parts.append(pred_clif)
        
        # Process child contexts
        for child_context in child_contexts:
            child_content = self._generate_context_content(graph, child_context.id)
            
            if child_content:
                if child_context.is_positive:
                    content_parts.append(child_content)
                else:
                    # Negative context = negation
                    content_parts.append(f"(not {child_content})")
        
        # Combine content
        if len(content_parts) == 0:
            return ""
        elif len(content_parts) == 1:
            return content_parts[0]
        else:
            return f"(and {' '.join(content_parts)})"
    
    def _get_direct_items(self, graph: EGGraph, context_id: ContextId) -> Set[ItemId]:
        """Get items directly in a context (not in child contexts)."""
        all_items = graph.get_items_in_context(context_id)
        direct_items = set(all_items)
        
        # Remove items that are in child contexts
        for ctx_id in graph.context_manager.get_descendants(context_id):
            child_ctx = graph.context_manager.get_context(ctx_id)
            if child_ctx and child_ctx.parent_context == context_id:
                child_items = graph.get_items_in_context(child_ctx.id)
                direct_items -= child_items
        
        return direct_items
    
    def _node_to_clif(self, graph: EGGraph, node: Node) -> Optional[str]:
        """Convert a node to CLIF representation."""
        if node.node_type == 'predicate':
            pred_name = node.properties.get('name', '')
            
            # Find arguments through edges
            incident_edges = graph.find_incident_edges(node.id)
            arguments = []
            
            for edge in incident_edges:
                if edge.edge_type == 'predication':
                    for arg_id in edge.nodes:
                        if arg_id != node.id and arg_id in graph.nodes:
                            arg_node = graph.nodes[arg_id]
                            arg_value = self._get_term_value(arg_node)
                            if arg_value:
                                arguments.append(arg_value)
            
            # Check for ligatures (equality)
            ligatures = self._find_node_ligatures(graph, node.id)
            for ligature in ligatures:
                if ligature.properties.get('type') == 'equality':
                    # Handle equality specially
                    other_nodes = ligature.nodes - {node.id}
                    for other_id in other_nodes:
                        if other_id in graph.nodes:
                            other_node = graph.nodes[other_id]
                            other_value = self._get_term_value(other_node)
                            if other_value:
                                return f"(= {pred_name} {other_value})"
            
            if pred_name:
                if arguments:
                    return f"({pred_name} {' '.join(arguments)})"
                else:
                    return f"({pred_name})"
        
        elif node.node_type == 'term':
            # Terms are handled as part of predicates
            return None
        
        return None
    
    def _get_term_value(self, node: Node) -> Optional[str]:
        """Get the value of a term node."""
        if node.node_type in ['term', 'variable']:
            value = node.properties.get('value') or node.properties.get('name')
            
            # Apply variable naming strategy
            if (node.node_type == 'variable' and 
                self.options.variable_naming_strategy == 'alphabetic'):
                return self._get_alphabetic_variable_name(value)
            
            return value
        
        return None
    
    def _get_alphabetic_variable_name(self, original_name: Optional[str]) -> str:
        """Get alphabetic variable name (x, y, z, x1, y1, ...)."""
        if original_name and original_name in self.variable_mapping:
            return self.variable_mapping[original_name]
        
        # Generate new alphabetic name
        alphabet = 'xyzuvwabcdefghijklmnopqrst'
        base_index = self.variable_counter % len(alphabet)
        suffix = self.variable_counter // len(alphabet)
        
        if suffix == 0:
            var_name = alphabet[base_index]
        else:
            var_name = f"{alphabet[base_index]}{suffix}"
        
        if original_name:
            self.variable_mapping[original_name] = var_name
        
        self.variable_counter += 1
        return var_name
    
    def _find_node_ligatures(self, graph: EGGraph, node_id: NodeId) -> List[Ligature]:
        """Find all ligatures containing a specific node."""
        ligatures = []
        
        for ligature in graph.ligatures.values():
            if node_id in ligature.nodes:
                ligatures.append(ligature)
        
        return ligatures
    
    def _format_clif(self, clif_text: str) -> str:
        """Format CLIF text for readability."""
        if not clif_text:
            return clif_text
        
        # Simple formatting: add newlines and indentation
        lines = []
        current_line = ""
        indent_level = 0
        
        i = 0
        while i < len(clif_text):
            char = clif_text[i]
            
            if char == '(':
                if current_line.strip():
                    lines.append("  " * indent_level + current_line.strip())
                    current_line = ""
                
                current_line += char
                
                # Look ahead to see if this is a simple predicate
                j = i + 1
                paren_count = 1
                is_simple = True
                
                while j < len(clif_text) and paren_count > 0:
                    if clif_text[j] == '(':
                        paren_count += 1
                        if paren_count > 1:
                            is_simple = False
                    elif clif_text[j] == ')':
                        paren_count -= 1
                    j += 1
                
                if not is_simple:
                    lines.append("  " * indent_level + current_line.strip())
                    current_line = ""
                    indent_level += 1
                
            elif char == ')':
                current_line += char
                
                # Check if this closes a complex expression
                if current_line.count('(') != current_line.count(')'):
                    indent_level = max(0, indent_level - 1)
                    lines.append("  " * indent_level + current_line.strip())
                    current_line = ""
                
            elif char == ' ' and current_line.strip():
                current_line += char
                
            elif char not in [' ', '\n', '\t']:
                current_line += char
            
            i += 1
        
        if current_line.strip():
            lines.append("  " * indent_level + current_line.strip())
        
        return "\n".join(lines)
    
    def _group_patterns_by_type(self, patterns: List[PatternMatch]) -> Dict[str, int]:
        """Group patterns by type for metadata."""
        pattern_counts = {}
        
        for pattern in patterns:
            pattern_type = pattern.pattern_type
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        return pattern_counts
    
    def _analyze_context_hierarchy(self, graph: EGGraph) -> Dict[str, Any]:
        """Analyze the context hierarchy for metadata."""
        contexts = graph.context_manager.contexts
        
        max_depth = 0
        positive_count = 0
        negative_count = 0
        
        for context in contexts.values():
            max_depth = max(max_depth, context.depth)
            
            if context.is_positive:
                positive_count += 1
            else:
                negative_count += 1
        
        return {
            'max_depth': max_depth,
            'positive_contexts': positive_count,
            'negative_contexts': negative_count,
            'total_contexts': len(contexts)
        }


class CLIFRoundTripValidator:
    """Validates CLIF round-trip conversion (EG -> CLIF -> EG)."""
    
    def __init__(self):
        """Initialize the validator."""
        self.generator = CLIFGenerator()
    
    def validate_round_trip(self, original_graph: EGGraph) -> Dict[str, Any]:
        """Validate that EG -> CLIF -> EG preserves semantic equivalence.
        
        Args:
            original_graph: The original existential graph.
            
        Returns:
            Validation results with equivalence check and differences.
        """
        from .clif_parser import CLIFParser
        
        # Generate CLIF
        generation_result = self.generator.generate(original_graph)
        clif_text = generation_result.clif_text
        
        # Parse back to EG
        parser = CLIFParser()
        parse_result = parser.parse(clif_text)
        
        if parse_result.graph is None:
            return {
                'round_trip_successful': False,
                'error': 'Failed to parse generated CLIF',
                'parse_errors': parse_result.errors,
                'original_clif': clif_text
            }
        
        reconstructed_graph = parse_result.graph
        
        # Compare graphs for semantic equivalence
        equivalence_result = self._check_semantic_equivalence(
            original_graph, reconstructed_graph
        )
        
        return {
            'round_trip_successful': equivalence_result['equivalent'],
            'semantic_equivalence': equivalence_result,
            'original_clif': clif_text,
            'generation_metadata': generation_result.metadata,
            'parse_warnings': parse_result.warnings,
            'patterns_preserved': len(generation_result.patterns_used)
        }
    
    def _check_semantic_equivalence(self, graph1: EGGraph, graph2: EGGraph) -> Dict[str, Any]:
        """Check if two graphs are semantically equivalent."""
        # This is a simplified equivalence check
        # A full implementation would use graph isomorphism
        
        differences = []
        
        # Compare basic statistics
        stats1 = self._get_graph_stats(graph1)
        stats2 = self._get_graph_stats(graph2)
        
        for key in stats1:
            if stats1[key] != stats2[key]:
                differences.append(f"{key}: {stats1[key]} vs {stats2[key]}")
        
        # Compare context structure
        context_diff = self._compare_context_structures(graph1, graph2)
        if context_diff:
            differences.extend(context_diff)
        
        equivalent = len(differences) == 0
        
        return {
            'equivalent': equivalent,
            'differences': differences,
            'original_stats': stats1,
            'reconstructed_stats': stats2
        }
    
    def _get_graph_stats(self, graph: EGGraph) -> Dict[str, int]:
        """Get basic statistics about a graph."""
        return {
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
            'ligature_count': len(graph.ligatures),
            'context_count': len(graph.context_manager.contexts),
            'predicate_count': sum(1 for node in graph.nodes.values() 
                                 if node.node_type == 'predicate'),
            'term_count': sum(1 for node in graph.nodes.values() 
                            if node.node_type == 'term')
        }
    
    def _compare_context_structures(self, graph1: EGGraph, graph2: EGGraph) -> List[str]:
        """Compare the context structures of two graphs."""
        differences = []
        
        # Compare context counts by depth
        depth_counts1 = {}
        depth_counts2 = {}
        
        for context in graph1.context_manager.contexts.values():
            depth = context.depth
            depth_counts1[depth] = depth_counts1.get(depth, 0) + 1
        
        for context in graph2.context_manager.contexts.values():
            depth = context.depth
            depth_counts2[depth] = depth_counts2.get(depth, 0) + 1
        
        all_depths = set(depth_counts1.keys()) | set(depth_counts2.keys())
        
        for depth in all_depths:
            count1 = depth_counts1.get(depth, 0)
            count2 = depth_counts2.get(depth, 0)
            
            if count1 != count2:
                differences.append(f"Depth {depth}: {count1} vs {count2} contexts")
        
        return differences

