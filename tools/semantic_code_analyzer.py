#!/usr/bin/env python3
"""
Semantic Code Analyzer - Layer 1 of Layered Strategy

Builds semantic relationships between code entities beyond simple indexing.
Maps function calls, class inheritance, module dependencies, and data flow.
"""

import ast
import json
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx


@dataclass
class CodeEntity:
    """Represents a code entity with semantic information."""

    name: str
    type: str  # 'function', 'class', 'module', 'variable'
    file_path: str
    line_number: int
    docstring: Optional[str]
    semantic_tags: Set[str]


@dataclass
class CodeRelationship:
    """Represents a relationship between code entities."""

    source: str
    target: str
    relationship_type: str  # 'calls', 'inherits', 'imports', 'uses', 'defines'
    context: Optional[str]


class SemanticAnalyzer(ast.NodeVisitor):
    """AST visitor that builds semantic relationships."""

    def __init__(self, file_path: str, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.entities: List[CodeEntity] = []
        self.relationships: List[CodeRelationship] = []
        self.current_class = None
        self.current_function = None
        self.imports = {}  # alias -> full_name

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            self.imports[import_name] = alias.name

            # Create import relationship
            self.relationships.append(
                CodeRelationship(
                    source=self.module_name,
                    target=alias.name,
                    relationship_type="imports",
                    context=f"line {node.lineno}",
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        module = node.module or ""
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports[import_name] = full_name

            self.relationships.append(
                CodeRelationship(
                    source=self.module_name,
                    target=full_name,
                    relationship_type="imports",
                    context=f"line {node.lineno}",
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Analyze class definitions and inheritance."""
        class_name = f"{self.module_name}.{node.name}"

        # Extract semantic tags from class
        semantic_tags = self._extract_semantic_tags(node.name, ast.get_docstring(node))

        entity = CodeEntity(
            name=class_name,
            type="class",
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            semantic_tags=semantic_tags,
        )
        self.entities.append(entity)

        # Track inheritance relationships
        for base in node.bases:
            base_name = self._resolve_name(base)
            if base_name:
                self.relationships.append(
                    CodeRelationship(
                        source=class_name,
                        target=base_name,
                        relationship_type="inherits",
                        context=f"line {node.lineno}",
                    )
                )

        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Analyze function definitions."""
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = f"{self.module_name}.{node.name}"

        semantic_tags = self._extract_semantic_tags(node.name, ast.get_docstring(node))

        entity = CodeEntity(
            name=func_name,
            type="function",
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            semantic_tags=semantic_tags,
        )
        self.entities.append(entity)

        self.current_function = func_name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        """Track function calls."""
        if self.current_function:
            called_name = self._resolve_name(node.func)
            if called_name:
                self.relationships.append(
                    CodeRelationship(
                        source=self.current_function,
                        target=called_name,
                        relationship_type="calls",
                        context=f"line {node.lineno}",
                    )
                )
        self.generic_visit(node)

    def _resolve_name(self, node) -> Optional[str]:
        """Resolve a name node to its full qualified name."""
        if isinstance(node, ast.Name):
            # Check if it's an imported name
            return self.imports.get(node.id, f"{self.module_name}.{node.id}")
        elif isinstance(node, ast.Attribute):
            base = self._resolve_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return None

    def _extract_semantic_tags(self, name: str, docstring: Optional[str]) -> Set[str]:
        """Extract semantic tags from name and docstring."""
        tags = set()

        # Domain-specific semantic tags
        domain_concepts = {
            "polarity": ["polarity", "positive", "negative"],
            "hierarchy": ["hierarchy", "nesting", "depth", "level", "containment"],
            "spatial": ["spatial", "bounds", "area", "region", "coordinate"],
            "transformation": ["transform", "rule", "apply", "change"],
            "index": ["index", "lookup", "search", "find"],
            "validation": ["validate", "check", "verify", "ensure"],
            "egi": ["egi", "graph", "vertex", "edge", "cut"],
            "performance": ["o(1)", "efficient", "fast", "optimize"],
        }

        text = (name + " " + (docstring or "")).lower()

        for concept, keywords in domain_concepts.items():
            if any(keyword in text for keyword in keywords):
                tags.add(concept)

        return tags


class SemanticCodeAnalyzer:
    """Main analyzer that builds semantic knowledge graph."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.entities: Dict[str, CodeEntity] = {}
        self.relationships: List[CodeRelationship] = []
        self.knowledge_graph = nx.DiGraph()

    def analyze_codebase(self):
        """Analyze entire codebase and build knowledge graph."""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                self._analyze_file(py_file)
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")

        self._build_knowledge_graph()

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["__pycache__", ".git", "test_", "debug_", ".backup"]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
                module_name = self._get_module_name(file_path)
                analyzer = SemanticAnalyzer(str(file_path), module_name)
                analyzer.visit(tree)

                # Store entities and relationships
                for entity in analyzer.entities:
                    self.entities[entity.name] = entity

                self.relationships.extend(analyzer.relationships)

            except SyntaxError:
                print(f"Syntax error in {file_path}, skipping")

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        rel_path = file_path.relative_to(self.root_path)
        module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        return ".".join(module_parts)

    def _build_knowledge_graph(self):
        """Build NetworkX knowledge graph from entities and relationships."""
        # Add nodes
        for entity in self.entities.values():
            self.knowledge_graph.add_node(
                entity.name,
                type=entity.type,
                file_path=entity.file_path,
                line_number=entity.line_number,
                semantic_tags=list(entity.semantic_tags),
            )

        # Add edges
        for rel in self.relationships:
            if rel.source in self.entities and rel.target in self.entities:
                self.knowledge_graph.add_edge(
                    rel.source,
                    rel.target,
                    relationship=rel.relationship_type,
                    context=rel.context,
                )

    def find_related_functions(self, concept: str) -> List[CodeEntity]:
        """Find functions related to a concept."""
        related = []
        for entity in self.entities.values():
            if entity.type == "function" and concept in entity.semantic_tags:
                related.append(entity)
        return related

    def find_call_chain(self, start_function: str, target_function: str) -> List[str]:
        """Find call chain from start to target function."""
        try:
            return nx.shortest_path(
                self.knowledge_graph, start_function, target_function
            )
        except nx.NetworkXNoPath:
            return []

    def find_impact_of_change(self, entity_name: str) -> Set[str]:
        """Find all entities that would be impacted by changing the given entity."""
        if entity_name not in self.knowledge_graph:
            return set()

        # Find all entities that depend on this one
        impacted = set()

        # Direct dependencies (things that call/use this entity)
        for predecessor in self.knowledge_graph.predecessors(entity_name):
            impacted.add(predecessor)

        # Transitive dependencies (things that depend on direct dependencies)
        for direct_dep in list(impacted):
            impacted.update(nx.ancestors(self.knowledge_graph, direct_dep))

        return impacted

    def get_concept_cluster(self, concept: str) -> Dict[str, List[str]]:
        """Get all entities related to a concept, grouped by type."""
        cluster = defaultdict(list)

        for entity in self.entities.values():
            if concept in entity.semantic_tags:
                cluster[entity.type].append(entity.name)

        return dict(cluster)

    def export_knowledge_graph(self, output_path: str):
        """Export knowledge graph to JSON."""
        graph_data = {
            "entities": {
                name: asdict(entity) for name, entity in self.entities.items()
            },
            "relationships": [asdict(rel) for rel in self.relationships],
            "metadata": {
                "total_entities": len(self.entities),
                "total_relationships": len(self.relationships),
            },
        }

        # Convert sets to lists for JSON serialization
        for entity_data in graph_data["entities"].values():
            entity_data["semantic_tags"] = list(entity_data["semantic_tags"])

        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)


def main():
    """Analyze Arisbe codebase and build semantic knowledge graph."""
    analyzer = SemanticCodeAnalyzer("/Users/mjh/Sync/GitHub/Arisbe/src")

    print("Building semantic knowledge graph...")
    analyzer.analyze_codebase()

    print(
        f"Found {len(analyzer.entities)} entities and {len(analyzer.relationships)} relationships"
    )

    # Export knowledge graph
    analyzer.export_knowledge_graph(
        "/Users/mjh/Sync/GitHub/Arisbe/semantic_knowledge_graph.json"
    )

    # Show polarity concept cluster
    polarity_cluster = analyzer.get_concept_cluster("polarity")
    print(f"\nPolarity concept cluster:")
    for entity_type, entities in polarity_cluster.items():
        print(f"  {entity_type}: {len(entities)} entities")
        for entity in entities[:3]:  # Show first 3
            print(f"    - {entity}")

    # Show hierarchy concept cluster
    hierarchy_cluster = analyzer.get_concept_cluster("hierarchy")
    print(f"\nHierarchy concept cluster:")
    for entity_type, entities in hierarchy_cluster.items():
        print(f"  {entity_type}: {len(entities)} entities")


if __name__ == "__main__":
    main()
