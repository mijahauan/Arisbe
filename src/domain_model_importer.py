"""
Domain Model Importer — build M (the Grapheus) from external sources.

Two import pathways:

1. **CLIF ontology files** — Single files or directories of .clif files
   (e.g., COLORE repository).  Uses the existing CLIF parser, composes
   multiple files into a single EGI by conjuncting all sentences on the
   sheet.

2. **JSON type lattice** — A lightweight JSON/YAML format for hand-authored
   domain models.  Defines concept types, relation types, subsumption
   (SubClassOf), individuals, and basic axioms.  Converted to EGI via
   the standard EG encoding.

Both pathways produce a ``RelationalGraphWithCuts`` that can serve as M
in the Endoporeutic Game or be stored as a UoD in the tomos.

Usage::

    from domain_model_importer import DomainModelImporter

    importer = DomainModelImporter()

    # From CLIF file(s)
    egi = importer.from_clif_file("path/to/ontology.clif")
    egi = importer.from_clif_directory("path/to/colore/ontology/")

    # From JSON type lattice
    egi = importer.from_type_lattice("path/to/domain.json")
    egi = importer.from_type_lattice_dict(lattice_dict)

    # Wrap as UoD for tomos storage
    uod = importer.as_uod(egi, name="My Domain Model", source="colore/mereology")
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from frozendict import frozendict

from clif_parser_dau import parse_clif
from egi_core_dau import (
    AlphabetDAU,
    Cut,
    Edge,
    ElementID,
    RelationalGraphWithCuts,
    Vertex,
    create_cut,
    create_edge,
    create_empty_graph,
    create_vertex,
)
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ImportResult:
    """Result of a domain model import operation."""

    egi: RelationalGraphWithCuts
    source_path: Optional[str] = None
    source_format: str = "unknown"
    source_clif: str = ""  # Original or generated CLIF text for composition
    num_axioms: int = 0
    num_types: int = 0
    num_relations: int = 0
    num_individuals: int = 0
    warnings: List[str] = field(default_factory=list)
    cl_imports: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        parts = [
            f"Source: {self.source_path or '(in-memory)'}",
            f"Format: {self.source_format}",
            f"Types: {self.num_types}, Relations: {self.num_relations}, "
            f"Individuals: {self.num_individuals}, Axioms: {self.num_axioms}",
        ]
        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLIF import
# ---------------------------------------------------------------------------

def _extract_cl_imports(clif_text: str) -> List[str]:
    """Extract cl-imports URIs from CLIF text without parsing."""
    imports = []
    import re
    for match in re.finditer(r'\(cl-imports\s+([^\s)]+)\s*\)', clif_text):
        imports.append(match.group(1))
    return imports


def from_clif_text(clif_text: str) -> ImportResult:
    """Import a domain model from a CLIF text string.

    Handles single sentences, multiple sentences, cl-text wrappers,
    and comments.
    """
    cl_imports = _extract_cl_imports(clif_text)
    egi = parse_clif(clif_text)

    # Count elements
    num_types = len({name for name in egi.rel.values()})
    num_relations = num_types  # in CLIF, relation = type
    num_individuals = sum(
        1 for v in egi.V if not getattr(v, "is_generic", True)
    )
    num_axioms = len(egi.Cut)  # rough proxy: each cut structure ~ 1 axiom

    return ImportResult(
        egi=egi,
        source_format="clif",
        source_clif=clif_text,
        num_axioms=num_axioms,
        num_types=num_types,
        num_relations=num_relations,
        num_individuals=num_individuals,
        cl_imports=cl_imports,
    )


def from_clif_file(path: Union[str, Path]) -> ImportResult:
    """Import a domain model from a single CLIF file."""
    path = Path(path)
    clif_text = path.read_text(encoding="utf-8")
    result = from_clif_text(clif_text)
    result.source_path = str(path)
    return result


def from_clif_directory(
    directory: Union[str, Path],
    recursive: bool = True,
) -> ImportResult:
    """Import and compose all .clif files in a directory into a single M.

    All sentences from all files are conjuncted on a single sheet,
    producing one unified domain model.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Not a directory: {directory}")

    pattern = "**/*.clif" if recursive else "*.clif"
    clif_files = sorted(directory.glob(pattern))

    if not clif_files:
        raise FileNotFoundError(f"No .clif files found in {directory}")

    # Concatenate all files (each file's sentences get conjuncted)
    combined_text_parts = []
    all_imports: List[str] = []
    warnings: List[str] = []

    for clif_file in clif_files:
        try:
            text = clif_file.read_text(encoding="utf-8")
            combined_text_parts.append(f";; Source: {clif_file.name}\n{text}")
            all_imports.extend(_extract_cl_imports(text))
        except Exception as e:
            warnings.append(f"Skipped {clif_file.name}: {e}")

    combined_text = "\n\n".join(combined_text_parts)
    result = from_clif_text(combined_text)
    result.source_path = str(directory)
    result.warnings = warnings
    result.cl_imports = all_imports
    return result


# ---------------------------------------------------------------------------
# JSON Type Lattice import
# ---------------------------------------------------------------------------

"""
Type Lattice JSON Schema:

{
  "name": "My Domain Model",
  "description": "A simple domain model for ...",

  "types": [
    {"name": "Animal", "supertypes": []},
    {"name": "Cat", "supertypes": ["Animal"]},
    {"name": "Dog", "supertypes": ["Animal"]},
    {"name": "Person", "supertypes": ["Animal"]}
  ],

  "relations": [
    {"name": "Owns", "signature": ["Person", "Animal"]},
    {"name": "Likes", "signature": ["Person", "Animal"]},
    {"name": "ParentOf", "signature": ["Animal", "Animal"]}
  ],

  "individuals": [
    {"name": "Socrates", "types": ["Person"]},
    {"name": "Biscuit", "types": ["Cat"]}
  ],

  "axioms": [
    "(forall (x) (if (Cat x) (not (Dog x))))",
    "(forall (x) (if (Person x) (exists (y) (Owns x y))))"
  ],

  "disjoint": [
    ["Cat", "Dog"]
  ]
}
"""


def _type_lattice_to_clif(lattice: Dict[str, Any]) -> str:
    """Convert a type lattice dictionary to CLIF text.

    The mapping:
    - types with supertypes → (forall (x) (if (Sub x) (Super x)))
    - individuals with types → (Type Individual)
    - relations → (for documentation; no axiom unless constrained)
    - disjoint pairs → (forall (x) (not (and (A x) (B x))))
    - axioms → passed through verbatim (already CLIF)
    """
    lines: List[str] = []
    name = lattice.get("name", "unnamed")
    lines.append(f";; Domain model: {name}")

    # Type subsumption axioms
    for type_def in lattice.get("types", []):
        type_name = type_def["name"]
        for supertype in type_def.get("supertypes", []):
            lines.append(
                f"(forall (x) (if ({type_name} x) ({supertype} x)))"
            )

    # Individual type assertions
    for individual in lattice.get("individuals", []):
        ind_name = individual["name"]
        for type_name in individual.get("types", []):
            lines.append(f"({type_name} {ind_name})")

    # Disjointness axioms
    for group in lattice.get("disjoint", []):
        if len(group) == 2:
            a, b = group
            lines.append(
                f"(forall (x) (not (and ({a} x) ({b} x))))"
            )
        elif len(group) > 2:
            # Pairwise disjointness
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    lines.append(
                        f"(forall (x) (not (and ({a} x) ({b} x))))"
                    )

    # Verbatim CLIF axioms
    for axiom in lattice.get("axioms", []):
        lines.append(axiom)

    return "\n".join(lines)


def from_type_lattice_dict(lattice: Dict[str, Any]) -> ImportResult:
    """Import a domain model from a type lattice dictionary."""
    clif_text = _type_lattice_to_clif(lattice)
    result = from_clif_text(clif_text)
    result.source_format = "type_lattice"
    result.source_clif = clif_text  # preserve for composition

    # More accurate counts from the lattice itself
    result.num_types = len(lattice.get("types", []))
    result.num_relations = len(lattice.get("relations", []))
    result.num_individuals = len(lattice.get("individuals", []))
    result.num_axioms = (
        sum(len(t.get("supertypes", [])) for t in lattice.get("types", []))
        + len(lattice.get("axioms", []))
        + sum(
            len(g) * (len(g) - 1) // 2 for g in lattice.get("disjoint", [])
        )
    )
    return result


def from_type_lattice(path: Union[str, Path]) -> ImportResult:
    """Import a domain model from a JSON type lattice file."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        lattice = json.load(f)
    result = from_type_lattice_dict(lattice)
    result.source_path = str(path)
    return result


# ---------------------------------------------------------------------------
# Composition: merge multiple domain models
# ---------------------------------------------------------------------------

def compose_models(*results: ImportResult) -> ImportResult:
    """Compose multiple imported domain models into a single M.

    All axioms from all models are conjuncted on a single sheet.
    This produces the union of all domain knowledge.
    """
    if not results:
        return ImportResult(egi=create_empty_graph())

    total_warnings: List[str] = []
    total_imports: List[str] = []
    total_types = 0
    total_relations = 0
    total_individuals = 0
    total_axioms = 0

    # Compose at the CLIF level: concatenate source CLIF texts and
    # re-parse.  This avoids ID collisions that occur when trying to
    # merge EGI structures directly, and avoids EGIF round-trip issues
    # with special characters in predicate names.
    clif_parts: List[str] = []

    for r in results:
        total_warnings.extend(r.warnings)
        total_imports.extend(r.cl_imports)
        total_types += r.num_types
        total_relations += r.num_relations
        total_individuals += r.num_individuals
        total_axioms += r.num_axioms
        if r.source_clif.strip():
            clif_parts.append(r.source_clif)

    combined_clif = "\n\n".join(clif_parts)
    egi = parse_clif(combined_clif) if combined_clif.strip() else create_empty_graph()

    sources = [r.source_path or "(in-memory)" for r in results]

    return ImportResult(
        egi=egi,
        source_path=" + ".join(sources),
        source_format="composed",
        source_clif=combined_clif,
        num_types=total_types,
        num_relations=total_relations,
        num_individuals=total_individuals,
        num_axioms=total_axioms,
        warnings=total_warnings,
        cl_imports=total_imports,
    )


# ---------------------------------------------------------------------------
# UoD wrapping
# ---------------------------------------------------------------------------

def as_uod(
    result: ImportResult,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> UniverseOfDiscourse:
    """Wrap an import result as a Universe of Discourse for tomos storage."""
    if name is None:
        name = Path(result.source_path).stem if result.source_path else "Imported Domain Model"

    if description is None:
        description = result.summary

    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    metadata = UoDMetadata(
        uod_id=str(uuid.uuid4()),
        name=name,
        description=description,
        uod_type=UoDType.STANDALONE,
        category=UoDCategory.DOMAIN_MODEL,
        created=now,
        last_modified=now,
        tags={f"source:{result.source_format}"},
    )

    return UniverseOfDiscourse(
        metadata=metadata,
        current_egi=result.egi,
    )


# ---------------------------------------------------------------------------
# Convenience class
# ---------------------------------------------------------------------------

class DomainModelImporter:
    """Convenience wrapper for all import operations."""

    def from_clif_text(self, clif_text: str) -> ImportResult:
        return from_clif_text(clif_text)

    def from_clif_file(self, path: Union[str, Path]) -> ImportResult:
        return from_clif_file(path)

    def from_clif_directory(
        self, directory: Union[str, Path], recursive: bool = True
    ) -> ImportResult:
        return from_clif_directory(directory, recursive)

    def from_type_lattice(self, path: Union[str, Path]) -> ImportResult:
        return from_type_lattice(path)

    def from_type_lattice_dict(self, lattice: Dict[str, Any]) -> ImportResult:
        return from_type_lattice_dict(lattice)

    def compose(self, *results: ImportResult) -> ImportResult:
        return compose_models(*results)

    def as_uod(
        self, result: ImportResult, name: str = None, description: str = None
    ) -> UniverseOfDiscourse:
        return as_uod(result, name, description)
