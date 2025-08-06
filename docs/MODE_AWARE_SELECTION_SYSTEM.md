# Mode-Aware Selection System Specification

**Version:** 1.0  
**Date:** 2025-08-06  
**Purpose:** Define the selection system that adapts behavior based on Warmup vs Practice mode constraints.

## Core Design Principle

**The selection system behavior is determined by the relationship to the EGI:**
- **Warmup Mode**: Building/composing the EGI (structure can change)
- **Practice Mode**: Transforming a fixed EGI (structure must be preserved)

## Mode-Specific Selection Behaviors

### **Warmup Mode: EGI Construction**

#### Selection Constraints
- **Syntactic Validity Only**: No cut overlap, valid EGI structure, proper containment
- **No Context Polarity Restrictions**: Can add/remove elements from any context
- **No Logical Completeness Requirements**: Can select partial structures for building
- **Compositional Freedom**: Support structure-building operations

#### Available Actions
- **Add Elements**: Insert vertices, predicates, cuts anywhere syntactically valid
- **Remove Elements**: Delete any element (with cascade deletion of dependent elements)
- **Connect/Disconnect**: Modify ν mapping freely to build connections
- **Structural Changes**: Operations that change the logical meaning of the graph
- **Move**: Reposition elements within or across contexts (with validation)

#### Visual Indicators
- **Context Backgrounds**: All contexts use clear/white background (no polarity distinction needed)
- **Selection Overlays**: Blue highlights for compositional selections
- **Action Affordances**: Show connection points, insertion areas, resize handles

### **Practice Mode: EGI Preservation**

#### Selection Constraints
- **Full Rule Validation**: All Dau transformation rule constraints
- **Context Polarity Enforcement**: Positive contexts (erasure), negative contexts (insertion)
- **Logical Completeness Required**: Subgraph selections must be logically complete
- **Meaning Preservation**: Only operations that preserve logical equivalence

#### Available Actions
- **Transformation Rules**: Only Dau's 8 canonical transformation rules
- **Visual Rearrangement**: Layout-only changes that preserve EGI structure
- **Rule-Based Operations**: Erasure, insertion, iteration, double-cut operations
- **Proof Construction**: Step-by-step logical transformations with history

#### Visual Indicators
- **Context Backgrounds**: Clear/white for positive, light gray for negative contexts
- **Selection Overlays**: Green highlights for valid transformations, red for invalid
- **Rule Indicators**: Visual cues showing which transformation rules apply

## Selection Types & Mode Behavior

### 1. **Individual Element Selection**

#### Warmup Mode
```python
# Vertex selection
- Actions: Delete, Move, Connect to new predicates, Change label, Disconnect
- Validation: Syntactic only (ensure valid EGI structure after changes)

# Predicate selection  
- Actions: Delete, Move, Edit relation name/arity, Connect/disconnect vertices
- Validation: Ensure ν mapping remains valid

# Cut selection
- Actions: Delete, Resize, Move (with contents), Add elements inside
- Validation: No overlap with other cuts, proper containment
```

#### Practice Mode
```python
# Vertex selection
- Actions: Apply erasure (positive contexts), Apply iteration, Move (layout only)
- Validation: Context polarity, transformation rule constraints

# Predicate selection
- Actions: Apply erasure (positive contexts), Apply iteration, Edit (limited)
- Validation: Context polarity, logical completeness, rule constraints

# Cut selection
- Actions: Double-cut operations, Resize (layout only), Apply erasure/insertion
- Validation: Double-cut patterns, context polarity, rule constraints
```

### 2. **Multi-Element Selection**

#### Warmup Mode
- **Purpose**: Build complex structures, connect multiple elements
- **Validation**: Syntactic validity of resulting structure
- **Actions**: Group operations, bulk connect/disconnect, structural composition

#### Practice Mode
- **Purpose**: Apply transformation rules to subgraphs
- **Validation**: Logical completeness, rule applicability, context constraints
- **Actions**: Subgraph iteration, bulk erasure, double-cut enclosure

### 3. **Area Selection**

#### Warmup Mode
- **Purpose**: Insert new elements anywhere syntactically valid
- **Validation**: No cut overlap, proper containment after insertion
- **Actions**: Insert any element type, paste subgraphs, create new structures

#### Practice Mode
- **Purpose**: Apply context-specific transformation rules
- **Validation**: Context polarity (positive for erasure, negative for insertion)
- **Actions**: Rule-based insertion/erasure, isolated vertex operations

## Mode Transition Behavior

### **Warmup → Practice Transition**
1. **Clear all selections** (force re-selection under new constraints)
2. **Lock current EGI** as reference for all future transformations
3. **Enable context polarity indicators** (background colors)
4. **Switch to transformation rule validation**
5. **Initialize proof step history**

### **Practice → Warmup Transition**
1. **Clear all selections** (release from rule constraints)
2. **Release EGI lock** (current state becomes new composition base)
3. **Disable context polarity indicators** (uniform background)
4. **Switch to compositional validation**
5. **Reset to compositional history tracking**

## Visual Design Specifications

### **Context Background Colors (Peircean Convention)**
- **Positive Contexts**: Clear/white background
- **Negative Contexts**: Light gray background (#F5F5F5)
- **Applied**: Only in Practice mode, uniform white in Warmup mode

### **Selection Overlays**
- **Warmup Mode**: Blue highlights (#007AFF with 20% opacity)
- **Practice Mode**: Green for valid selections (#28A745 with 20% opacity), red for invalid (#DC3545 with 20% opacity)

### **Mode Indicators**
- **Tab-based mode switching** reinforces constraint changes
- **Mode badge** in corner showing current mode
- **Action menu headers** indicate mode-specific constraints

## Implementation Architecture

### **Core Classes**
```python
class ModeAwareSelectionSystem:
    def __init__(self, mode: Mode):
        self.mode = mode
        self.validator = self._create_validator(mode)
        self.action_provider = self._create_action_provider(mode)
    
    def switch_mode(self, new_mode: Mode):
        self.clear_selections()
        self.mode = new_mode
        self.validator = self._create_validator(new_mode)
        self.action_provider = self._create_action_provider(new_mode)

class WarmupSelectionValidator:
    def validate_action(self, action: Action, selection: Selection) -> ValidationResult:
        # Syntactic validation only
        
class PracticeSelectionValidator:
    def validate_action(self, action: Action, selection: Selection) -> ValidationResult:
        # Full transformation rule validation
```

### **Integration Points**
- **DiagramController**: Mode-aware action dispatch
- **Canvas Rendering**: Context background colors, selection overlays
- **Action Menus**: Mode-specific action availability
- **History System**: Mode-appropriate undo/redo behavior

This specification provides the foundation for implementing a robust, mode-aware selection system that maintains mathematical rigor while supporting both compositional and transformational workflows.
