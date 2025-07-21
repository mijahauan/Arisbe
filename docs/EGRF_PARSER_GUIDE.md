# EGRF Parser Implementation Guide

## Overview

The EGRF Parser is a critical component of the EG-CL-Manus2 system that converts EGRF (Existential Graph Rendering Format) documents back to EG-CL-Manus2 data structures. This enables complete round-trip conversion: **EG-CL-Manus2 → EGRF → EG-CL-Manus2**, preserving logical integrity while supporting visual representation.

## Architecture

### Core Components

```
EGRFParser
├── Validation Layer      # Schema and structural validation
├── Entity Parser         # EGRF entities → EG-CL-Manus2 entities
├── Predicate Parser      # EGRF predicates → EG-CL-Manus2 predicates
├── Context Parser        # EGRF contexts → EG-CL-Manus2 contexts
├── Connection Reconstructor # Visual connections → logical relationships
└── Graph Assembler       # Final EGGraph construction
```

### Data Flow

```
EGRF Document → Validation → Component Parsing → Connection Reconstruction → Graph Assembly → EGGraph
```

## Usage

### Basic Usage

```python
from egrf import EGRFParser, EGRFSerializer

# Create parser
parser = EGRFParser(validation_enabled=True)

# Parse from EGRF document
result = parser.parse(egrf_doc)

if result.is_successful:
    reconstructed_graph = result.graph
    print(f"Successfully parsed {len(result.graph.entities)} entities")
else:
    print(f"Parsing failed: {result.errors}")
```

### Parse from JSON

```python
# Parse directly from JSON string
json_str = '{"format": "EGRF", "version": "1.0", ...}'
result = parser.parse_from_json(json_str)

# Parse from file
result = parser.parse_from_file("graph.egrf")
```

### Round-trip Conversion

```python
from egrf import EGRFGenerator, EGRFParser

# Original graph
original_graph = create_your_graph()

# Generate EGRF
generator = EGRFGenerator()
egrf_doc = generator.generate(original_graph)

# Parse back
parser = EGRFParser()
result = parser.parse(egrf_doc)

if result.is_successful:
    reconstructed_graph = result.graph
    # Verify logical equivalence
    assert_graphs_equivalent(original_graph, reconstructed_graph)
```

## Configuration Options

### Parser Settings

```python
parser = EGRFParser(
    validation_enabled=True,    # Enable EGRF schema validation
    strict_mode=False          # Continue on warnings vs fail
)
```

### Validation Modes

- **`validation_enabled=True`**: Full schema validation (recommended for production)
- **`validation_enabled=False`**: Skip validation (faster, for trusted input)
- **`strict_mode=True`**: Fail on any warnings
- **`strict_mode=False`**: Continue with best-effort parsing

## Error Handling

### Result Structure

```python
class ParseResult:
    graph: Optional[EGGraph]    # Parsed graph (None if failed)
    errors: List[str]           # Critical errors
    warnings: List[str]         # Non-critical issues
    
    @property
    def is_successful(self) -> bool:
        return self.graph is not None and len(self.errors) == 0
```

### Common Error Types

#### Validation Errors
- Invalid EGRF schema
- Missing required fields
- Malformed JSON

#### Parsing Errors
- Invalid entity references
- Broken connection points
- Circular context dependencies

#### Recovery Strategies
- **Graceful degradation**: Continue parsing when possible
- **Detailed reporting**: Specific error locations and descriptions
- **Warning vs Error**: Distinguish critical failures from recoverable issues

### Example Error Handling

```python
result = parser.parse_from_file("graph.egrf")

if not result.is_successful:
    print("Parsing failed:")
    for error in result.errors:
        print(f"  ERROR: {error}")
    
    for warning in result.warnings:
        print(f"  WARNING: {warning}")
else:
    if result.warnings:
        print("Parsing succeeded with warnings:")
        for warning in result.warnings:
            print(f"  WARNING: {warning}")
    
    # Use the parsed graph
    graph = result.graph
```

## Data Mapping

### Entity Mapping

| EGRF Entity | EG-CL-Manus2 Entity | Notes |
|-------------|---------------------|-------|
| `id` | `EntityId` | UUID preservation or generation |
| `name` | `name` | Direct mapping |
| `entity_type` | `entity_type` | constant/variable/anonymous |
| `visual.path` | Reconstructed as ligatures | Visual → logical conversion |

### Predicate Mapping

| EGRF Predicate | EG-CL-Manus2 Predicate | Notes |
|----------------|------------------------|-------|
| `id` | `PredicateId` | UUID preservation or generation |
| `name` | `name` | Direct mapping |
| `connections` | `entities` | Connection points → entity relationships |
| `visual` | Ignored | Visual data not preserved in logical structure |

### Context Mapping

| EGRF Context | EG-CL-Manus2 Context | Notes |
|--------------|----------------------|-------|
| `id` | `ContextId` | UUID preservation or generation |
| `context_type` | `context_type` | cut/sheet_of_assertion |
| `visual.bounds` | Hierarchy reconstruction | Containment → parent-child relationships |

## Connection Reconstruction

The most complex aspect of parsing is reconstructing logical entity-predicate connections from visual EGRF data.

### Algorithm

1. **Extract Connections**: Parse connection points from EGRF predicates
2. **Validate Entities**: Ensure referenced entities exist
3. **Reconstruct Relationships**: Map visual connections to logical entity lists
4. **Verify Integrity**: Check connection consistency

### Example

```python
# EGRF predicate with connections
egrf_predicate = {
    "id": "pred_1",
    "name": "On",
    "connections": [
        {"entity_id": "entity_x", "connection_point": {"x": 100, "y": 150}},
        {"entity_id": "entity_y", "connection_point": {"x": 200, "y": 150}}
    ]
}

# Reconstructed EG-CL-Manus2 predicate
predicate = Predicate.create(
    name="On",
    entities=[entity_x_id, entity_y_id]  # Mapped from connection entity_ids
)
```

## Performance Characteristics

### Benchmarks

Based on performance testing:

| Graph Size | Generation Time | Parsing Time | Total Time |
|------------|----------------|--------------|------------|
| 10 entities, 10 predicates | 0.001s | 0.001s | 0.003s |
| 100 entities, 100 predicates | 0.006s | 0.008s | 0.019s |
| 500 entities, 100 predicates | 0.024s | 0.018s | 0.056s |

### Performance Notes

- **Linear scaling**: Performance scales linearly with graph size
- **Parsing efficiency**: Parsing is slightly faster than generation
- **Memory usage**: Immutable data structures ensure memory safety
- **Large graphs**: Successfully handles 500+ entities with sub-second performance

## Integration with EG-CL-Manus2

### Workflow Integration

```python
# Typical workflow
def process_visual_graph(egrf_file: str) -> EGGraph:
    """Process visual EGRF file into logical EG-CL-Manus2 graph."""
    
    # Parse EGRF
    parser = EGRFParser()
    result = parser.parse_from_file(egrf_file)
    
    if not result.is_successful:
        raise ValueError(f"EGRF parsing failed: {result.errors}")
    
    # Validate logical structure
    graph = result.graph
    validation_result = graph.validate()
    
    if not validation_result.is_valid:
        raise ValueError(f"Invalid graph structure: {validation_result.errors}")
    
    return graph
```

### CLIF Integration

```python
from clif_generator import CLIFGenerator

# Round-trip with CLIF verification
def verify_round_trip_with_clif(original_graph: EGGraph) -> bool:
    """Verify round-trip conversion preserves CLIF semantics."""
    
    # Generate original CLIF
    clif_gen = CLIFGenerator()
    original_clif = clif_gen.generate(original_graph)
    
    # Round-trip through EGRF
    generator = EGRFGenerator()
    parser = EGRFParser()
    
    egrf_doc = generator.generate(original_graph)
    result = parser.parse(egrf_doc)
    
    if not result.is_successful:
        return False
    
    # Generate reconstructed CLIF
    reconstructed_clif = clif_gen.generate(result.graph)
    
    # Compare CLIF expressions for semantic equivalence
    return clif_equivalent(original_clif, reconstructed_clif)
```

## Best Practices

### Development

1. **Always check `ParseResult.is_successful`** before using the graph
2. **Handle warnings appropriately** - they indicate potential issues
3. **Use validation in production** - disable only for trusted input
4. **Test round-trip conversion** for your specific use cases

### Error Recovery

1. **Graceful degradation**: Continue processing when possible
2. **Detailed logging**: Capture all errors and warnings
3. **User feedback**: Provide clear error messages for UI applications

### Performance

1. **Disable validation** for trusted, high-volume processing
2. **Batch processing**: Parse multiple documents efficiently
3. **Memory management**: Parser uses immutable structures for safety

## Testing

### Unit Tests

```bash
# Run parser-specific tests
cd EG-CL-Manus2
PYTHONPATH=src python3 -m pytest tests/test_egrf_parser.py -v
```

### Round-trip Tests

```bash
# Run comprehensive round-trip tests
python3 test_round_trip.py
```

### Performance Tests

```bash
# Run performance benchmarks
python3 test_performance.py
```

## Troubleshooting

### Common Issues

#### "Parsing failed: 'dict' object has no attribute 'id'"
- **Cause**: EGRF serializer returned dictionary instead of object
- **Solution**: Parser handles both formats automatically (fixed in current version)

#### "Context.create() got an unexpected keyword argument 'name'"
- **Cause**: Incorrect Context.create() parameters
- **Solution**: Use proper parameter names (context_type, parent_context, depth, id)

#### "Connection references unknown entity"
- **Cause**: EGRF contains connection to non-existent entity
- **Solution**: Check EGRF generation or validate entity references

### Debug Mode

```python
# Enable detailed debugging
import logging
logging.basicConfig(level=logging.DEBUG)

parser = EGRFParser(validation_enabled=True, strict_mode=True)
result = parser.parse(egrf_doc)

# Examine detailed results
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
```

## Future Enhancements

### Planned Features

1. **Advanced Context Support**: Full context hierarchy reconstruction
2. **Visual Validation**: Verify visual consistency during parsing
3. **Incremental Parsing**: Support for streaming large documents
4. **Schema Evolution**: Handle multiple EGRF format versions

### Extension Points

1. **Custom Validators**: Add domain-specific validation rules
2. **Connection Algorithms**: Implement alternative connection reconstruction methods
3. **Performance Optimizations**: Lazy loading and caching strategies

## API Reference

### EGRFParser Class

```python
class EGRFParser:
    def __init__(self, validation_enabled: bool = True, strict_mode: bool = False)
    def parse(self, egrf_doc: EGRFDocument) -> ParseResult
    def parse_from_json(self, json_str: str) -> ParseResult
    def parse_from_file(self, file_path: str) -> ParseResult
```

### ParseResult Class

```python
class ParseResult:
    graph: Optional[EGGraph]
    errors: List[str]
    warnings: List[str]
    
    @property
    def is_successful(self) -> bool
```

### Convenience Functions

```python
def parse_egrf(egrf_doc: EGRFDocument, validation_enabled: bool = True) -> ParseResult
def parse_egrf_from_json(json_str: str, validation_enabled: bool = True) -> ParseResult
def parse_egrf_from_file(file_path: str, validation_enabled: bool = True) -> ParseResult
```

## Conclusion

The EGRF Parser completes the round-trip conversion capability of the EG-CL-Manus2 system, enabling seamless integration between logical graph structures and visual representations. With comprehensive error handling, performance optimization, and extensive testing, it provides a robust foundation for GUI applications and the Endoporeutic Game implementation.

The parser maintains the academic rigor of the EG-CL-Manus2 system while enabling practical visual applications, ensuring that logical consistency is preserved throughout the conversion process.

