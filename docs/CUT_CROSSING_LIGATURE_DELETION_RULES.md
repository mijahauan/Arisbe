# Cut-Crossing Ligature Deletion Rules

## Overview

This document defines the canonical behavior for handling ligatures that cross cut boundaries during vertex and predicate deletion operations, based on Dau's formalism where ligatures represent identity relationships that transcend logical contexts.

## Fundamental Principles

### 1. Identity Transcendence
- **Ligatures represent identity**: A ligature crossing cuts maintains the identity of an individual across different logical contexts
- **Cut boundaries are permeable to identity**: Identity relationships can span multiple nested contexts
- **Deletion preserves logical coherence**: Removing elements must maintain valid EGI structure

### 2. Canonical Deletion Rules

#### Vertex Deletion with Cut-Crossing Ligatures

When deleting a vertex that has ligatures crossing cut boundaries:

1. **Impact Analysis Phase**
   - Identify all ligatures connected to the vertex
   - Determine which ligatures cross cut boundaries
   - Identify predicates that will become disconnected
   - Check for predicates that will become completely orphaned

2. **Ligature Removal Phase**
   - Remove all ligatures connected to the deleted vertex
   - Preserve remaining ligature structure for other vertices
   - Maintain identity relationships not involving the deleted vertex

3. **Predicate Orphan Handling**
   - **Completely Orphaned Predicates**: If a predicate loses ALL connections, it becomes a 0-ary predicate (proposition)
   - **Partially Connected Predicates**: If a predicate retains some connections, it continues with reduced arity
   - **Cross-Cut Predicates**: Predicates in different contexts from deleted vertex maintain their logical position

4. **Logical Validation**
   - Ensure no invalid EGI states are created
   - Verify all remaining predicates have valid arity
   - Maintain cut nesting and containment rules

#### Predicate Deletion with Cut-Crossing Ligatures

When deleting a predicate that has ligatures crossing cut boundaries:

1. **Impact Analysis Phase**
   - Identify all vertices connected to the predicate
   - Determine which connections cross cut boundaries
   - Identify vertices that will become completely disconnected
   - Check for vertices that will lose all predicate connections

2. **Ligature Removal Phase**
   - Remove all ligatures connected to the deleted predicate
   - Preserve ligature connections between remaining predicates and vertices
   - Maintain identity relationships not involving the deleted predicate

3. **Vertex Orphan Handling**
   - **Completely Orphaned Vertices**: Vertices that lose ALL predicate connections become free-standing identity lines
   - **Partially Connected Vertices**: Vertices that retain connections to other predicates continue normally
   - **Cross-Cut Vertices**: Vertices in different contexts from deleted predicate maintain their logical position

4. **Identity Line Preservation**
   - Orphaned vertices retain their identity line representation
   - Free-standing identity lines are valid EGI elements (unpredicated individuals)
   - Cross-cut identity relationships remain intact for non-deleted elements

## Implementation Guidelines

### Selection System Integration

```python
# When selecting an element for deletion, highlight:
selection_highlight = selector.get_selection_highlight(element_id, selection_type)

# Show user the impact:
- Primary element (to be deleted)
- Connected elements (will lose connections)
- Crossing cuts (ligatures that span boundaries)
- Orphaned elements (will become disconnected)
```

### Deletion Validation

```python
# Before deletion, validate the operation:
deletion_impact = analyzer.analyze_vertex_deletion(vertex_id)

# Check for invalid states:
- Predicates with invalid arity after deletion
- Broken ligature chains
- Context containment violations
```

### Operation Sequencing

1. **Pre-Deletion Analysis**
   - Calculate full impact of deletion
   - Identify all affected elements
   - Validate resulting EGI state will be legal

2. **User Confirmation**
   - Show highlighted selection with impact preview
   - Allow user to confirm or cancel operation
   - Provide clear indication of what will be removed/orphaned

3. **Atomic Deletion**
   - Remove element and all connected ligatures simultaneously
   - Update EGI model atomically
   - Refresh GUI rendering with new state

4. **Post-Deletion Validation**
   - Verify EGI model integrity
   - Ensure all remaining elements have valid relationships
   - Update spatial layout for remaining elements

## Special Cases

### Cross-Cut Identity Chains

When a vertex is part of an identity chain that crosses multiple cuts:

```
Sheet: [Cut1: [vertex_a] ligature_crosses_boundary [Cut2: [predicate_p vertex_b]]]
```

Deleting `vertex_a`:
- Removes ligature from `vertex_a` to `predicate_p`
- Preserves ligature from `vertex_b` to `predicate_p`
- `predicate_p` reduces from binary to unary
- Cut boundaries remain intact

### Branching Ligatures Across Cuts

When ligatures branch across cut boundaries:

```
Sheet: [vertex_shared] branches to [Cut1: [predicate_p1]] and [Cut2: [predicate_p2]]
```

Deleting `vertex_shared`:
- Removes both cross-cut ligatures
- `predicate_p1` and `predicate_p2` become orphaned (0-ary)
- Both predicates become propositions in their respective contexts

### Nested Cut Traversal

When ligatures traverse multiple nested cuts:

```
Sheet: [Cut1: [Cut2: [vertex_inner]] ligature_traverses [predicate_outer]]
```

Deleting `vertex_inner`:
- Removes ligature that crosses both Cut2 and Cut1 boundaries
- `predicate_outer` becomes orphaned proposition
- Nested cut structure remains unchanged

## Dau Compliance Notes

1. **Identity Preservation**: Deletion operations preserve the identity relationships of non-deleted elements
2. **Context Respect**: Cut boundaries continue to define logical contexts even when ligatures are removed
3. **Logical Validity**: All deletion operations result in valid EGI structures
4. **Minimal Impact**: Only directly connected elements are affected; indirect relationships are preserved

## GUI Feedback Requirements

### Visual Indicators
- **Red highlighting**: Elements that will be deleted
- **Orange highlighting**: Elements that will lose connections
- **Yellow highlighting**: Elements that will become orphaned
- **Blue highlighting**: Cut boundaries that ligatures currently cross

### User Confirmation
- Clear description of deletion impact
- List of elements that will be affected
- Option to cancel operation before execution
- Undo capability for completed deletions

## Error Handling

### Invalid Deletion Attempts
- Prevent deletion that would create invalid EGI states
- Show error message explaining why deletion is not allowed
- Suggest alternative operations that would achieve user's goal

### Recovery Mechanisms
- Undo/redo support for all deletion operations
- Automatic validation after each deletion
- Rollback capability if invalid state is detected

This specification ensures that vertex and predicate deletion operations maintain the mathematical rigor of Dau's formalism while providing clear, predictable behavior for GUI users.
