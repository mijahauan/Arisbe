# UNIFIED SINGLE-SIMULATION LAYOUT ARCHITECTURE

**Status**: Production (As of 2025-10-12)  
**Replaces**: `BOTTOM_UP_D3_ARCHITECTURE.md` (Recursive Shell-and-Core Model)

---

## 🎯 Architectural Goal: Radical Simplification and Robustness

This architecture solves the critical flaws of the previous recursive, multi-simulation model. The primary goal is to **eliminate fragile, manual coordinate transformations** in Python by delegating all layout intelligence to a single, unified D3.js physics simulation.

This model is fundamentally more stable, simpler to debug, and correctly leverages the D3 physics engine.

---

## 🏗️ The Unified Simulation Workflow

Instead of a separate simulation for each cut, we now run **one single, unified simulation** for the entire EGI. This is the standard and most robust way to solve complex containment and collision problems with d3-force.

### **1. Python's Role: The Simple Assembler** (`unified_d3_engine.py`)

Python's responsibility is drastically simplified. It no longer performs any recursive calculations or complex coordinate transformations. Its sole job is to **assemble a single, comprehensive JSON payload** for the D3 worker.

```python
# Simplified Python Logic
def _build_unified_payload(egi, style):
    # 1. Create a FLAT list of ALL nodes (vertices, predicates, AND cuts)
    nodes = []
    for element in egi.iter_elements():
        nodes.append({
            "id": element.id,
            "type": "vertex" | "predicate" | "cut",
            # ... other properties
        })

    # 2. Create a FLAT list of all links
    links = [] # All ligature connections

    # 3. Define the hierarchy map
    hierarchy = {element_id: area_id for ...}

    # 4. Send ONE payload to the D3 worker
    return {"nodes": nodes, "links": links, "hierarchy": hierarchy}
```

**Key takeaway**: Python is now dumb. It just gathers data. All layout intelligence is delegated.

### **2. D3 Worker's Role: The Intelligent Simulator** (`unified_d3_worker.js`)

The D3 worker receives the single payload and performs all layout logic within one unified simulation.

#### **A. The Single Simulation**
```javascript
// One simulation for all nodes
const simulation = d3.forceSimulation(nodes)
    .force('link', ...)
    .force('collide', ...) // The ONLY collision force
    .force('hierarchy', ...); // The NEW custom force
```

#### **B. The `forceHierarchy`: The Brains of the Operation**
This is a powerful custom force that runs on **every tick** of the simulation. It has two critical responsibilities:

1.  **Dynamic Sizing**: It finds all children belonging to a `cut` node, calculates their collective bounding box, and **updates the `width` and `height` properties of the parent `cut` node in real-time**. This ensures cuts are always precisely large enough to contain their contents.

2.  **Containment (Gentle Pull)**: It applies a gentle, continuous force that pulls each child node towards the center of its parent's (now correctly sized) bounding box. This is a stable, physics-based approach to containment that works *with* the simulation, not against it.

#### **C. `forceCollide`: The Muscle**
- `d3.forceCollide` is now the **single, authoritative force** for all repulsion.
- It uses the dynamically updated `width` and `height` of the `cut` nodes (from `forceHierarchy`) to correctly push apart not just small nodes, but entire cuts.
- This creates a clean, cooperative system: `forceHierarchy` defines the sizes, and `forceCollide` arranges them without overlap.

---

## ✅ How This Solves the Critical Flaws

### **1. Eliminates "Coordinate System Hell"**
- **Problem**: The old engine used fragile, manual coordinate transformations (`_translate_cut_and_descendants`) as the recursion unwound.
- **Solution**: There is only **one global coordinate system** inside the D3 simulation. The need for manual translation is completely gone. This removes the #1 source of bugs and fragility.

### **2. Creates a Cooperative Force Model**
- **Problem**: The old engine had conflicting forces (`forceObstacleAvoidance` vs. `forceCollide`), causing instability and nodes "tunneling" through obstacles.
- **Solution**: `forceHierarchy` and `forceCollide` now have distinct, cooperative roles. One sizes and contains, the other repels. They work together to find a stable equilibrium.

### **3. Provides True, Robust Containment**
- **Problem**: The old `forceWalls` only handled the outermost boundary, and strong link forces could pull nodes out of their cuts.
- **Solution**: The `forceHierarchy` containment pull is always active, gently ensuring nodes stay within their parent's boundaries without the violent instability of a hard wall ejection.

---

## 🏆 Conclusion

By moving all layout intelligence into a **single, unified D3 simulation**, we eliminate the fragile and error-prone Python-based coordinate management. This new architecture leverages the physics engine for what it does best: finding a stable equilibrium for a complex system of interconnected and contained objects.

This model is simpler, more robust, and less vulnerable to the subtle bugs that plagued the previous recursive implementation.
