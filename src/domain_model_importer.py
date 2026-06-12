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
from cl_import_resolver import (
    ImportResolver,
    extract_imports,
    resolve_from_text,
)
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
    resolved_modules: List[str] = field(default_factory=list)
    unresolved_imports: List[str] = field(default_factory=list)

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
    """Extract cl-imports URIs from CLIF text without parsing (shared with the
    closure resolver, ``cl_import_resolver.extract_imports``)."""
    return extract_imports(clif_text)


def _clif_tokenize(s: str) -> List[str]:
    """Tokens of a CLIF document: parens, ``"…"`` / ``'…'`` string literals, bare
    atoms (names, variables, ``=``, and ``http://`` IRIs — all space-free).

    Single-quoted strings (``'…'``) are Common Logic enclosed-name/quoted text;
    COLORE uses them for ``cl-comment`` bodies that contain spaces and parens
    (e.g. ``'Annihilation by zero (entailed for rings)'``).  Keeping the whole
    literal as one token is what lets ``_strip_cl_comments`` drop those forms
    cleanly instead of the parens inside them derailing the reader."""
    toks: List[str] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c in "()":
            toks.append(c); i += 1
        elif c in "\"'":
            quote = c
            j = i + 1
            while j < n and s[j] != quote:
                j += 2 if s[j] == "\\" else 1
            toks.append(s[i:j + 1]); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()"':
                j += 1
            toks.append(s[i:j]); i = j
    return toks


def _clif_read_all(toks: List[str]) -> List[Any]:
    """Parse CLIF tokens into nested lists (Lisp-style ``(head …)`` forms)."""
    pos = [0]

    def read() -> Any:
        t = toks[pos[0]]; pos[0] += 1
        if t == "(":
            items: List[Any] = []
            while pos[0] < len(toks) and toks[pos[0]] != ")":
                items.append(read())
            if pos[0] < len(toks):
                pos[0] += 1  # past ')'
            return items
        return t

    forms: List[Any] = []
    while pos[0] < len(toks):
        if toks[pos[0]] == ")":
            pos[0] += 1; continue
        forms.append(read())
    return forms


def _alpha_rename(node, env: Dict[str, str], counter: List[int]):
    """Alpha-rename every ``forall``/``exists``-bound variable to a globally unique
    name, so independent quantified sentences never accidentally share one.

    Without this, ``parse_clif`` unifies same-named bound variables *across*
    sentences into a single line of identity — turning two independent universals
    ``(∀x A→B) ∧ (∀x C→D)`` into the weaker ``∃x (A→B)∧(C→D)`` (a **correctness**
    bug, and a layout catastrophe: one vertex threaded through every scroll).  Real
    ontologies (COLORE, hand-written CLIF) reuse ``x``/``y``/``z`` constantly.
    """
    if isinstance(node, str):
        return env.get(node, node)
    if not node:
        return node
    head = node[0]
    if head in ("forall", "exists") and len(node) >= 2 and isinstance(node[1], list):
        new_env = dict(env)
        new_binders = []
        for v in node[1]:
            if isinstance(v, str):
                counter[0] += 1
                nv = f"{v}_{counter[0]}"
                new_env[v] = nv
                new_binders.append(nv)
            else:                       # a typed/structured binder — recurse as-is
                new_binders.append(_alpha_rename(v, env, counter))
        return [head, new_binders] + [_alpha_rename(c, new_env, counter)
                                      for c in node[2:]]
    return [_alpha_rename(c, env, counter) for c in node]


def _clif_serialize(node) -> str:
    if isinstance(node, str):
        return node
    return "(" + " ".join(_clif_serialize(c) for c in node) + ")"


def _disambiguate_variables(text: str) -> str:
    """Rename all quantified variables to globally-unique names (see
    ``_alpha_rename``).  ``;;`` line comments are dropped first (the structural
    reader does not model them; block ``/* */`` comments are already stripped)."""
    import re
    text = re.sub(r";;[^\n]*", "", text)
    counter = [0]
    forms = [_alpha_rename(f, {}, counter) for f in _clif_read_all(_clif_tokenize(text))]
    return "\n".join(_clif_serialize(f) for f in forms)


# ---------------------------------------------------------------------------
# Function-term relationalization (CLIF → CLIF, at the importer boundary)
# ---------------------------------------------------------------------------
#
# The protected CLIF parser (``_parse_atomic_formula``) accepts only *names* in
# argument position — a nested function application ``(f t₁ … tₙ)`` there is a
# parse error.  But functions are EG-expressible by **relationalization**: a
# function is a relation whose last argument is uniquely determined by the rest
# (its graph).  ``(density (dmv v m))`` ↦ ``(exists (z) (and (dmv v m z) (density
# z)))``.  Dau gives the direct extension (*Constants and Functions in Peirce's
# Existential Graphs*, ICCS 2007); EGIF has a ``(Type … | output)`` form.  We do
# the meaning-preserving reduction here, leaving the protected lexer untouched —
# exactly as ``_strip_block_comments`` / ``_disambiguate_variables`` already do.
#
# The ∃-form is sound in *any* polarity given totality+functionality (the value
# exists in every context), so a lifted atom inside a ``not`` stays correct.

# Logical connectives whose direct children are sentences (recurse, never lift).
_CLIF_CONNECTIVES = {"and", "or", "not", "if", "iff"}
# Quantifiers: child[1] is the binder list, child[2:] are sentences.
_CLIF_QUANTIFIERS = {"forall", "exists"}
# Common Logic wrappers whose *list* children are sentences (names left alone).
_CLIF_META = {
    "cl-text", "cl:text", "cl-module", "cl:module",
    "cl-comment", "cl:comment", "cl-imports", "cl:imports",
}


def _lift_function_terms(term, graph_atoms, fresh, sigs, counter):
    """Replace a function term in argument position with a fresh variable, recording
    its relational graph atom.  Recurses so nested ``(f (g x))`` lifts inside-out.

    ``term`` is a name (returned as-is) or a function application ``(f t₁ … tₙ)``
    (a list).  For the latter: lift the inner arguments first, mint a fresh output
    variable ``z``, append the graph atom ``(f …inner… z)``, and return ``z``.
    """
    if isinstance(term, str) or not term:
        return term
    f = term[0]
    inner = [_lift_function_terms(a, graph_atoms, fresh, sigs, counter)
             for a in term[1:]]
    counter[0] += 1
    z = f"_fnz{counter[0]}"
    fresh.append(z)
    graph_atoms.append([f] + inner + [z])
    if isinstance(f, str):
        # f used as an n-ary function ⇒ an (n+1)-ary relation (its graph).
        sigs.add((f, len(inner)))
    return z


def _relationalize_node(node, sigs, counter):
    """Walk a CLIF s-expression, lifting every function term out of predication
    (and equality) argument positions.  Logical structure is recursed through
    untouched; only atoms carrying a ``(… )`` argument are rewritten."""
    if isinstance(node, str) or not node:
        return node
    head = node[0]
    if not isinstance(head, str):
        return [_relationalize_node(c, sigs, counter) for c in node]
    if head in _CLIF_QUANTIFIERS and len(node) >= 2 and isinstance(node[1], list):
        return [head, node[1]] + [_relationalize_node(c, sigs, counter)
                                  for c in node[2:]]
    if head in _CLIF_CONNECTIVES:
        return [head] + [_relationalize_node(c, sigs, counter) for c in node[1:]]
    if head in _CLIF_META:
        return [head] + [_relationalize_node(c, sigs, counter)
                         if isinstance(c, list) else c for c in node[1:]]
    # Otherwise a predication ``(P t₁ … tₙ)`` — including ``(= t₁ t₂)``, since the
    # parser reads ``=`` as an ordinary relation.  Lift function-term arguments.
    graph_atoms: List[Any] = []
    fresh: List[str] = []
    new_args = [_lift_function_terms(a, graph_atoms, fresh, sigs, counter)
                for a in node[1:]]
    atom = [head] + new_args
    if not fresh:
        return atom
    return ["exists", fresh, ["and"] + graph_atoms + [atom]]


def _functionality_axioms(sigs: Set[Tuple[str, int]]) -> List[str]:
    """Optional totality + uniqueness axioms that make each relationalized ``R_f``
    a genuine *function* rather than a mere relation.  Both are non-Horn / use
    equality, so they land in the contest residue (materialization won't use
    them) — emitted only when explicitly requested."""
    lines: List[str] = []
    for f, n in sorted(sigs):
        xs = [f"_fa_x{i}" for i in range(n)]
        graph_z = f"({f} {' '.join(xs + ['_fa_z'])})"
        graph_z2 = f"({f} {' '.join(xs + ['_fa_z2'])})"
        binder = " ".join(xs)
        # Totality: ∀x⃗ ∃z R_f(x⃗, z)
        lines.append(f"(forall ({binder}) (exists (_fa_z) {graph_z}))"
                     if n else f"(exists (_fa_z) {graph_z})")
        # Uniqueness: ∀x⃗ ∀z ∀z′ (R_f(x⃗,z) ∧ R_f(x⃗,z′) → z = z′)
        ub = " ".join(xs + ["_fa_z", "_fa_z2"])
        lines.append(f"(forall ({ub}) (if (and {graph_z} {graph_z2}) "
                     f"(= _fa_z _fa_z2)))")
    return lines


_CL_COMMENT_HEADS = {"cl-comment", "cl:comment"}


def _strip_cl_comments(node):
    """Drop ``(cl-comment <string> …)`` annotations, recursively.

    The protected CLIF parser has no ``cl-comment`` form, so a comment string
    that contains parens (COLORE: ``(cl-comment 'Annihilation by zero (entailed
    for rings)')``) would derail it.  Common Logic's ``cl-comment`` carries no
    logical content — it annotates an optional trailing phrase — so we remove the
    comment node, keeping any annotated phrase (``(cl-comment "note" φ)`` → ``φ``)
    and dropping a bare comment entirely.  Done here at the importer boundary,
    like ``_strip_block_comments``."""
    if isinstance(node, str) or not node:
        return node
    out = []
    for c in node:
        if isinstance(c, list) and c and c[0] in _CL_COMMENT_HEADS:
            # keep the annotated phrase (child[2:]), drop the comment string
            out.extend(_strip_cl_comments(g) for g in c[2:])
        else:
            out.append(_strip_cl_comments(c))
    return out


def _relationalize_functions(
    text: str,
    *,
    assert_functionality: bool = False,
    sigs_out: Optional[Set[Tuple[str, int]]] = None,
) -> str:
    """Relationalize every nested function term in ``text`` (CLIF → CLIF).

    ``;;`` line comments are dropped first (the structural reader does not model
    them; block ``/* */`` comments are stripped upstream).  When
    ``assert_functionality`` is set, totality + uniqueness axioms for every lifted
    function symbol are appended.
    """
    import re
    text = re.sub(r";;[^\n]*", "", text)
    counter = [0]
    sigs: Set[Tuple[str, int]] = set()
    # Strip cl-comment forms first (a synthetic root carries the top level so a
    # comment that *is* a top-level form is dropped too), then relationalize.
    forms = _strip_cl_comments(["__root__"] + _clif_read_all(_clif_tokenize(text)))[1:]
    forms = [_relationalize_node(f, sigs, counter) for f in forms]
    out = [_clif_serialize(f) for f in forms]
    if sigs_out is not None:
        sigs_out.update(sigs)
    if assert_functionality and sigs:
        out.extend(_functionality_axioms(sigs))
    return "\n".join(out)


def _strip_block_comments(text: str) -> str:
    """Remove C-style ``/* … */`` block comments before parsing.

    Every COLORE file carries a ``/* Copyright … */`` header, and the protected
    CLIF lexer only strips ``;;`` line comments — so words inside the header (e.g.
    "Toronto **and** others") would tokenise as keywords and break the parse.  We
    strip ``/* */`` here (the importer boundary) rather than touch the lexer.  Only
    block comments are removed: ``//`` is left alone because it occurs inside
    ``http://`` IRIs in ``cl-text`` / ``cl-imports`` forms.
    """
    import re
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def from_clif_text(
    clif_text: str,
    *,
    assert_functionality: bool = False,
    resolver: Optional[ImportResolver] = None,
    root_iri: Optional[str] = None,
) -> ImportResult:
    """Import a domain model from a CLIF text string.

    Handles single sentences, multiple sentences, cl-text wrappers,
    ``;;`` comments and (COLORE-style) ``/* … */`` block comments.  Nested
    function terms ``(f t₁ … tₙ)`` in argument position are **relationalized**
    (lifted to their graph relation ``R_f``) so function-bearing ontologies
    (most of COLORE) import; pass ``assert_functionality`` to also emit the
    (non-Horn) totality + uniqueness axioms.

    When ``resolver`` is given, the module's ``(cl-imports <iri>)`` closure is
    resolved first (``cl_import_resolver``): every transitively-imported module is
    fetched/located, deduped, and conjuncted on the sheet before parsing, so an
    ontology that *imports* its dependencies (most of COLORE) imports complete.
    Unresolved IRIs are recorded on the result, never silently dropped.
    """
    resolved_modules: List[str] = []
    unresolved_imports: List[str] = []
    if resolver is not None:
        closure = resolve_from_text(
            clif_text, resolver, root_iri=root_iri or "(root)")
        clif_text = closure.combined_clif
        resolved_modules = closure.resolved_iris
        unresolved_imports = list(closure.unresolved)

    clif_text = _strip_block_comments(clif_text)
    cl_imports = _extract_cl_imports(clif_text)
    clif_text = _relationalize_functions(
        clif_text, assert_functionality=assert_functionality)
    egi = parse_clif(_disambiguate_variables(clif_text))

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
        resolved_modules=resolved_modules,
        unresolved_imports=unresolved_imports,
    )


def from_clif_file(
    path: Union[str, Path],
    *,
    resolver: Optional[ImportResolver] = None,
    root_iri: Optional[str] = None,
) -> ImportResult:
    """Import a domain model from a single CLIF file.

    Pass ``resolver`` to auto-resolve the file's ``cl-imports`` closure (see
    ``from_clif_text``); ``root_iri`` names the file's own IRI for the closure
    headers (defaults to the path)."""
    path = Path(path)
    clif_text = path.read_text(encoding="utf-8")
    result = from_clif_text(
        clif_text, resolver=resolver, root_iri=root_iri or str(path))
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
# OWL import (OWL 2 Functional-Style Syntax → CLIF → EGI)
# ---------------------------------------------------------------------------

def from_owl_text(owl_text: str) -> ImportResult:
    """Import a domain model from OWL 2 functional-syntax text.

    Translates the EG-expressible axioms to CLIF (``tools/owl_to_clif``) and parses
    that — the OWL→CLIF→EGI pipeline.  Untranslatable constructs (cardinality, union,
    complement, datatypes, annotations) are recorded as warnings, never silently
    dropped (the manifest floor).  The generated CLIF is kept on the result so the
    model composes with CLIF imports.
    """
    import sys as _sys
    _tools = str(Path(__file__).resolve().parent.parent / "tools")
    if _tools not in _sys.path:
        _sys.path.insert(0, _tools)
    from owl_to_clif import translate as _owl_translate

    clif_text, report = _owl_translate(owl_text)
    egi = parse_clif(clif_text) if clif_text.strip() else parse_clif("(true)")

    warnings = [f"skipped {n}× {construct}"
                for construct, n in sorted(report.skipped.items())]
    result = from_clif_text(clif_text) if clif_text.strip() else ImportResult(
        egi=egi, source_clif=clif_text)
    result.egi = egi
    result.source_format = "owl-functional"
    result.source_clif = clif_text
    result.num_axioms = report.n_axioms
    result.num_types = len(report.classes)
    result.num_relations = len(report.properties)
    result.num_individuals = len(report.individuals)
    result.warnings = warnings
    return result


def from_owl_file(path: Union[str, Path]) -> ImportResult:
    """Import a domain model from a single OWL functional-syntax file (.ofn/.owl)."""
    path = Path(path)
    result = from_owl_text(path.read_text(encoding="utf-8"))
    result.source_path = str(path)
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
    # Re-disambiguate the *combined* text: each part was numbered from zero, so two
    # parts could still share a variable name across the join (re-collapsing).
    egi = (parse_clif(_disambiguate_variables(combined_clif))
           if combined_clif.strip() else create_empty_graph())

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

    def from_owl_text(self, owl_text: str) -> ImportResult:
        return from_owl_text(owl_text)

    def from_owl_file(self, path: Union[str, Path]) -> ImportResult:
        return from_owl_file(path)

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
