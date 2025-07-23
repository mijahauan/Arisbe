# EGRF v3.0 Architecture Guide

## Overview

The Existential Graph Rendering Format (EGRF) v3.0 represents a significant architectural shift from previous versions, moving from an absolute coordinate-based approach to a logical containment model. This guide provides a comprehensive overview of the EGRF v3.0 architecture, its components, and how they work together to provide a platform-independent rendering format for Peirce's Existential Graphs.

## Core Principles

EGRF v3.0 is built on several core principles:

1. **Logical Containment**: Elements are defined by their logical relationships rather than absolute positions.
2. **Platform Independence**: The format is designed to work across any GUI platform.
3. **Peirce Compliance**: The architecture enforces Peirce's rules for Existential Graphs.
4. **User Freedom**: Users can freely move elements within their logical constraints.
5. **Auto-Sizing**: Containers size themselves based on their contents.

## Architecture Components

### 1. Logical Types

The foundation of EGRF v3.0 is the logical types system, which defines the core data structures:

- **LogicalElement**: Base class for all elements in the graph.
- **LogicalContext**: Represents cuts and sheets with containment properties.
- **LogicalPredicate**: Represents predicates with arity and connection points.
- **LogicalEntity**: Represents lines of identity with path constraints.
- **LogicalLigature**: Represents connections between entities across contexts.

### 2. Containment Hierarchy

The containment hierarchy manages the nesting relationships between elements:

- **ContainmentHierarchyManager**: Manages the overall hierarchy.
- **ContainmentRelationship**: Defines the relationship between a container and its contained elements.
- **HierarchyValidator**: Validates the logical structure of the hierarchy.
- **HierarchyValidationReport**: Reports validation results.

### 3. Layout Constraints

The layout constraints system provides platform-independent positioning:

- **LayoutConstraint**: Base class for all constraints.
- **SizeConstraint**: Controls element dimensions.
- **PositionConstraint**: Positions elements relative to others.
- **SpacingConstraint**: Maintains spacing between elements.
- **AlignmentConstraint**: Aligns elements with each other.
- **ContainmentConstraint**: Ensures elements stay within containers.

### 4. EG-HG to EGRF Converter

The converter transforms EG-HG (Existential Graph Hypergraph) data to EGRF v3.0:

- **EgHgToEgrfConverter**: Handles the conversion process.
- **parse_eg_hg_content**: Parses EG-HG content from files.
- **convert**: Transforms parsed data to EGRF v3.0 format.

### 5. Corpus Validation

The corpus validation system ensures the correctness of EGRF v3.0 implementations:

- **CorpusValidator**: Validates EGRF v3.0 against corpus examples.
- **load_corpus_index**: Loads the corpus index.
- **load_example**: Loads a specific example from the corpus.
- **validate_egrf_structure**: Validates the structure of an EGRF v3.0 document.

## Data Flow

The EGRF v3.0 system follows a clear data flow:

1. **Input**: EG-HG data (from files or memory).
2. **Parsing**: The EG-HG data is parsed into a structured format.
3. **Conversion**: The parsed data is converted to EGRF v3.0 format.
4. **Validation**: The converted data is validated against the EGRF v3.0 schema.
5. **Rendering**: The validated data can be rendered by any GUI platform.

## Logical Containment Model

The logical containment model is the core innovation of EGRF v3.0. Instead of specifying absolute coordinates, elements are defined by their logical relationships:

- **Contexts**: Define the logical boundaries of the graph.
- **Nesting Levels**: Determine the depth of nesting for each context.
- **Containment Relationships**: Specify which elements are contained within which contexts.
- **Movement Constraints**: Ensure elements stay within their logical containers.

## Platform Independence

EGRF v3.0 achieves platform independence through:

- **Relative Positioning**: Elements are positioned relative to their containers.
- **Layout Constraints**: Constraints are defined in a platform-independent way.
- **Auto-Sizing**: Containers size themselves based on their contents.
- **Platform Adapters**: Adapters translate EGRF v3.0 to platform-specific layouts.

## Peirce Compliance

EGRF v3.0 enforces Peirce's rules for Existential Graphs:

- **Double-Cut Implication**: Properly represents implication with double cuts.
- **Proper Nesting**: Ensures correct nesting of contexts.
- **Line of Identity**: Correctly represents lines of identity and ligatures.
- **Predicate Placement**: Ensures predicates are placed within their containing cuts.

## Conclusion

EGRF v3.0 represents a significant advancement in the representation of Existential Graphs. By moving from absolute coordinates to logical containment, it provides a more flexible, platform-independent, and Peirce-compliant rendering format. This architecture guide provides a foundation for understanding and working with EGRF v3.0.

