# EGRF Integration Guide

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
python -m pytest tests/test_egrf_generator.py -v
```

### Basic Usage
```python
from src.graph import EGGraph
from src.eg_types import Entity, Predicate
from src.egrf import EGRFGenerator, EGRFSerializer

# Create a simple existential graph
eg_graph = EGGraph.create_empty()

# Add entity
socrates = Entity.create(name="Socrates", entity_type="constant")
eg_graph = eg_graph.add_entity(socrates)

# Add predicate
person_pred = Predicate.create(name="Person", entities=[socrates.id])
eg_graph = eg_graph.add_predicate(person_pred)

# Generate EGRF
generator = EGRFGenerator()
egrf_doc = generator.generate(eg_graph)

# Save to file
EGRFSerializer.save_to_file(egrf_doc, "socrates_person.egrf")

# View in browser
# Open tools/egrf_viewer/index.html and load the file
```

## Integration Patterns

### 1. Visualization Pipeline
```python
# EG-CL-Manus2 → EGRF → Visual Display

def visualize_graph(eg_graph):
    """Convert EG-CL-Manus2 graph to visual representation."""
    
    # Step 1: Generate EGRF
    generator = EGRFGenerator()
    egrf_doc = generator.generate(eg_graph)
    
    # Step 2: Customize layout (optional)
    egrf_doc = customize_layout(egrf_doc)
    
    # Step 3: Export for visualization
    return EGRFSerializer.to_json(egrf_doc)

def customize_layout(egrf_doc):
    """Adjust visual properties while preserving logic."""
    
    # Adjust predicate positions
    for predicate in egrf_doc.predicates:
        # Move predicates but maintain connections
        predicate.visual.position.x += 50
        
        # Update connection points accordingly
        for connection in predicate.connections:
            connection.connection_point.x += 50
    
    return egrf_doc
```

### 2. Interactive Editing
```python
# EGRF ↔ User Interface ↔ EG-CL-Manus2

class EGRFEditor:
    """Interactive editor for existential graphs."""
    
    def __init__(self, eg_graph):
        self.eg_graph = eg_graph
        self.egrf_doc = EGRFGenerator().generate(eg_graph)
    
    def move_predicate(self, predicate_id, new_position):
        """Move predicate while maintaining logical constraints."""
        
        # Find predicate in EGRF
        predicate = self.find_predicate(predicate_id)
        
        # Update position
        predicate.visual.position = new_position
        
        # Update connection points to maintain ligature integrity
        self.update_connections(predicate)
        
        # Validate constraints
        if not self.validate_constraints():
            raise ValueError("Move violates logical constraints")
    
    def validate_constraints(self):
        """Ensure all logical constraints are satisfied."""
        
        # Check hierarchical consistency
        if not self.check_hierarchy():
            return False
            
        # Check cut containment
        if not self.check_containment():
            return False
            
        # Check ligature connections
        if not self.check_connections():
            return False
            
        return True
```

### 3. Educational Applications
```python
# Step-by-step graph construction

class EGTutorial:
    """Interactive tutorial for existential graphs."""
    
    def __init__(self):
        self.eg_graph = EGGraph.create_empty()
        self.steps = []
    
    def add_entity_step(self, name, entity_type="variable"):
        """Add entity with explanation."""
        
        entity = Entity.create(name=name, entity_type=entity_type)
        self.eg_graph = self.eg_graph.add_entity(entity)
        
        step = {
            "action": "add_entity",
            "entity": entity,
            "explanation": f"Added {entity_type} '{name}' to the graph",
            "egrf": self.generate_current_egrf()
        }
        self.steps.append(step)
        
        return step
    
    def add_predicate_step(self, name, entity_ids):
        """Add predicate with explanation."""
        
        predicate = Predicate.create(name=name, entities=entity_ids)
        self.eg_graph = self.eg_graph.add_predicate(predicate)
        
        step = {
            "action": "add_predicate",
            "predicate": predicate,
            "explanation": f"Added predicate '{name}' connecting entities",
            "egrf": self.generate_current_egrf()
        }
        self.steps.append(step)
        
        return step
    
    def generate_current_egrf(self):
        """Generate EGRF for current state."""
        generator = EGRFGenerator()
        return generator.generate(self.eg_graph)
```

## Advanced Features

### Custom Layout Constraints
```python
from src.egrf import LayoutConstraints

# Define custom layout parameters
constraints = LayoutConstraints(
    canvas_width=1200.0,
    canvas_height=800.0,
    predicate_spacing=120.0,
    entity_spacing=100.0,
    context_padding=30.0,
    predicate_width=80.0,
    predicate_height=40.0
)

# Use with generator
generator = EGRFGenerator(constraints)
egrf_doc = generator.generate(eg_graph)
```

### Schema Validation
```python
from src.egrf.egrf_schema import validate_egrf_file

# Validate EGRF file
is_valid, error_msg = validate_egrf_file("my_graph.egrf")

if not is_valid:
    print(f"Validation error: {error_msg}")
else:
    print("EGRF file is valid")
```

### Batch Processing
```python
def process_graph_collection(eg_graphs, output_dir):
    """Convert multiple graphs to EGRF format."""
    
    generator = EGRFGenerator()
    
    for i, eg_graph in enumerate(eg_graphs):
        # Generate EGRF
        egrf_doc = generator.generate(eg_graph)
        
        # Add metadata
        egrf_doc.metadata.title = f"Graph {i+1}"
        egrf_doc.metadata.description = f"Generated from collection item {i+1}"
        
        # Save to file
        filename = f"{output_dir}/graph_{i+1:03d}.egrf"
        EGRFSerializer.save_to_file(egrf_doc, filename)
        
        print(f"Generated {filename}")
```

## Web Interface Integration

### EGRF Viewer Setup
```bash
# Navigate to viewer directory
cd tools/egrf_viewer

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

### Custom Web Integration
```javascript
// Load and display EGRF in web application

async function loadEGRF(file) {
    const response = await fetch(file);
    const egrfData = await response.json();
    
    // Validate format
    if (egrfData.format !== "EGRF") {
        throw new Error("Invalid EGRF format");
    }
    
    // Render graph
    renderEGRF(egrfData);
}

function renderEGRF(egrfData) {
    // Create SVG canvas
    const svg = d3.select("#graph-container")
        .append("svg")
        .attr("width", egrfData.canvas.width)
        .attr("height", egrfData.canvas.height);
    
    // Render entities (lines of identity)
    egrfData.entities.forEach(entity => {
        const line = svg.append("path")
            .attr("d", createPathFromPoints(entity.visual.path))
            .attr("stroke", entity.visual.stroke.color)
            .attr("stroke-width", entity.visual.stroke.width);
    });
    
    // Render predicates
    egrfData.predicates.forEach(predicate => {
        const oval = svg.append("ellipse")
            .attr("cx", predicate.visual.position.x)
            .attr("cy", predicate.visual.position.y)
            .attr("rx", predicate.visual.size.width / 2)
            .attr("ry", predicate.visual.size.height / 2);
    });
}
```

## Testing Integration

### Unit Tests
```python
# tests/test_my_egrf_integration.py

import unittest
from src.egrf import EGRFGenerator, EGRFSerializer
from src.graph import EGGraph
from src.eg_types import Entity, Predicate

class TestMyEGRFIntegration(unittest.TestCase):
    
    def test_custom_workflow(self):
        """Test my specific EGRF workflow."""
        
        # Create test graph
        eg_graph = self.create_test_graph()
        
        # Generate EGRF
        generator = EGRFGenerator()
        egrf_doc = generator.generate(eg_graph)
        
        # Validate results
        self.assertEqual(len(egrf_doc.entities), 2)
        self.assertEqual(len(egrf_doc.predicates), 1)
        
        # Test serialization
        json_str = EGRFSerializer.to_json(egrf_doc)
        egrf_restored = EGRFSerializer.from_json(json_str)
        
        # Validate round-trip
        self.assertEqual(len(egrf_restored.entities), 2)
        self.assertEqual(len(egrf_restored.predicates), 1)
```

### Integration Tests
```python
def test_full_pipeline():
    """Test complete EG-CL-Manus2 → EGRF → Visualization pipeline."""
    
    # Start with EG-CL-Manus2 graph
    eg_graph = create_complex_test_graph()
    
    # Generate EGRF
    egrf_doc = EGRFGenerator().generate(eg_graph)
    
    # Validate logical consistency
    assert_logical_consistency(eg_graph, egrf_doc)
    
    # Test visualization rendering
    svg_output = render_to_svg(egrf_doc)
    assert len(svg_output) > 0
    
    # Test round-trip conversion (when parser is implemented)
    # eg_graph_restored = EGRFParser().parse(egrf_doc)
    # assert_graphs_equivalent(eg_graph, eg_graph_restored)
```

## Best Practices

### 1. Logical Integrity
- **Always validate** EGRF documents after generation
- **Preserve constraints** when modifying visual properties
- **Test round-trips** to ensure semantic preservation

### 2. Performance
- **Cache EGRF documents** for frequently accessed graphs
- **Use lazy loading** for large graph collections
- **Optimize layouts** for specific use cases

### 3. User Experience
- **Provide visual feedback** during constraint violations
- **Enable undo/redo** for interactive editing
- **Offer layout templates** for common patterns

### 4. Maintenance
- **Version EGRF files** for compatibility tracking
- **Document customizations** for future reference
- **Test with real data** from your domain

## Troubleshooting

### Common Issues

#### Import Errors
```python
# Ensure proper path setup
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

#### Validation Failures
```python
# Check schema compliance
from src.egrf.egrf_schema import validate_egrf

is_valid, error = validate_egrf(egrf_data)
if not is_valid:
    print(f"Validation error: {error}")
```

#### Layout Issues
```python
# Verify constraint satisfaction
def check_layout_constraints(egrf_doc):
    for predicate in egrf_doc.predicates:
        for connection in predicate.connections:
            # Ensure connection points are within predicate bounds
            assert is_point_in_predicate(connection.connection_point, predicate)
```

### Getting Help
- **Documentation**: See `docs/EGRF_SPECIFICATION.md` for detailed format information
- **Examples**: Check `examples/egrf/` for sample files
- **Tests**: Review `tests/test_egrf_generator.py` for usage patterns
- **Issues**: Report problems via GitHub issues with minimal reproduction cases

This guide provides the foundation for integrating EGRF visualization into your existential graph applications while maintaining the academic rigor and logical precision of the EG-CL-Manus2 system.

