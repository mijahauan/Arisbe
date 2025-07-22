"""
Existential Graph Rendering Format (EGRF) Implementation

This module provides Python data structures and validation for the EGRF format,
which serves as a GUI-agnostic intermediate representation for 2D existential graphs.
"""

import json
import jsonschema
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class Point:
    """2D coordinate point."""
    x: float
    y: float


@dataclass
class Size:
    """2D size specification."""
    width: float
    height: float


@dataclass
class Bounds:
    """2D rectangular bounds."""
    x: float
    y: float
    width: float
    height: float


@dataclass
class Stroke:
    """Stroke style specification."""
    color: str = "#000000"
    width: float = 1.0
    style: str = "solid"  # solid, dashed, dotted


@dataclass
class Fill:
    """Fill style specification."""
    color: str = "#ffffff"
    opacity: float = 1.0


@dataclass
class Font:
    """Font specification."""
    family: str = "Arial"
    size: float = 12.0
    weight: str = "normal"  # normal, bold
    color: str = "#000000"


@dataclass
class Label:
    """Text label with position and styling."""
    text: str
    position: Point
    font: Font = field(default_factory=Font)
    alignment: str = "center"  # left, center, right


@dataclass
class Marker:
    """Marker specification for line endpoints."""
    type: str = "none"  # none, circle, square, arrow
    size: float = 3.0


@dataclass
class EntityVisual:
    """Visual representation of an entity (line of identity)."""
    style: str = "line"  # line, curve, polyline
    path: List[Point] = field(default_factory=list)
    stroke: Stroke = field(default_factory=Stroke)


@dataclass
class PredicateVisual:
    """Visual representation of a predicate."""
    style: str = "oval"  # oval, rectangle, diamond, circle
    position: Point = field(default_factory=lambda: Point(0, 0))
    size: Size = field(default_factory=lambda: Size(60, 30))
    fill: Fill = field(default_factory=Fill)
    stroke: Stroke = field(default_factory=Stroke)


@dataclass
class ContextVisual:
    """Visual representation of a context (cut)."""
    style: str = "oval"  # oval, rectangle, circle
    bounds: Bounds = field(default_factory=lambda: Bounds(0, 0, 100, 100))
    fill: Fill = field(default_factory=lambda: Fill("#f0f0f0", 0.3))
    stroke: Stroke = field(default_factory=lambda: Stroke("#666666", 2.0, "dashed"))


@dataclass
class LigatureVisual:
    """Visual representation of a ligature (identity connection)."""
    style: str = "dashed_line"  # dashed_line, dotted_line, curved_line
    path: List[Point] = field(default_factory=list)
    stroke: Stroke = field(default_factory=lambda: Stroke("#0066cc", 1.0, "dashed"))
    markers: Dict[str, Marker] = field(default_factory=lambda: {
        "start": Marker("circle", 3.0),
        "end": Marker("circle", 3.0)
    })


@dataclass
class Connection:
    """Connection between predicate and entity."""
    entity_id: str
    connection_point: Point
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """Entity in the existential graph (line of identity)."""
    id: str
    name: str
    type: str  # constant, variable, individual
    visual: EntityVisual = field(default_factory=EntityVisual)
    labels: List[Label] = field(default_factory=list)


@dataclass
class Predicate:
    """Predicate in the existential graph."""
    id: str
    name: str
    type: str  # relation, function
    arity: int
    connected_entities: List[str] = field(default_factory=list)
    visual: PredicateVisual = field(default_factory=PredicateVisual)
    labels: List[Label] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)


@dataclass
class Context:
    """Context in the existential graph (cut or sheet of assertion)."""
    id: str
    type: str  # root, cut, sheet_of_assertion
    parent_context: Optional[str] = None
    visual: ContextVisual = field(default_factory=ContextVisual)
    contained_items: List[str] = field(default_factory=list)
    nesting_level: int = 0


@dataclass
class Ligature:
    """Ligature connecting entities (identity relationship)."""
    id: str
    connected_entities: List[str]
    type: str  # identity, coreference
    visual: LigatureVisual = field(default_factory=LigatureVisual)


@dataclass
class Canvas:
    """Canvas specification for the graph."""
    width: float = 800.0
    height: float = 600.0
    background: str = "#ffffff"
    grid: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "size": 20,
        "color": "#f0f0f0"
    })


@dataclass
class Metadata:
    """Metadata for the EGRF document."""
    title: str = "Existential Graph"
    author: str = "System"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""


@dataclass
class Semantics:
    """Semantic information for validation and consistency."""
    logical_form: Dict[str, str] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EGRFDocument:
    """Complete EGRF document."""
    format: str = "EGRF"
    version: str = "1.0"
    entities: List[Entity] = field(default_factory=list)
    predicates: List[Predicate] = field(default_factory=list)
    contexts: List[Context] = field(default_factory=list)
    ligatures: List[Ligature] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    canvas: Canvas = field(default_factory=Canvas)
    semantics: Semantics = field(default_factory=Semantics)


class EGRFValidator:
    """Validator for EGRF documents."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """Initialize validator with JSON schema."""
        if schema_path is None:
            schema_path = "egrf_schema.json"
        
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def validate_json(self, egrf_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate EGRF dictionary against JSON schema."""
        errors = []
        try:
            jsonschema.validate(egrf_dict, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"JSON Schema validation error: {e.message}")
            return False, errors
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def validate_document(self, doc: EGRFDocument) -> Tuple[bool, List[str]]:
        """Validate EGRF document structure and consistency."""
        errors = []
        
        # Convert to dict for JSON schema validation
        doc_dict = asdict(doc)
        json_valid, json_errors = self.validate_json(doc_dict)
        errors.extend(json_errors)
        
        # Additional semantic validation
        semantic_valid, semantic_errors = self._validate_semantics(doc)
        errors.extend(semantic_errors)
        
        return len(errors) == 0, errors
    
    def _validate_semantics(self, doc: EGRFDocument) -> Tuple[bool, List[str]]:
        """Validate semantic consistency of the document."""
        errors = []
        
        # Check ID uniqueness
        all_ids = []
        for entity in doc.entities:
            all_ids.append(entity.id)
        for predicate in doc.predicates:
            all_ids.append(predicate.id)
        for context in doc.contexts:
            all_ids.append(context.id)
        for ligature in doc.ligatures:
            all_ids.append(ligature.id)
        
        if len(all_ids) != len(set(all_ids)):
            errors.append("Duplicate IDs found in document")
        
        # Check reference integrity
        entity_ids = {e.id for e in doc.entities}
        context_ids = {c.id for c in doc.contexts}
        
        # Validate predicate entity references
        for predicate in doc.predicates:
            for entity_id in predicate.connected_entities:
                if entity_id not in entity_ids:
                    errors.append(f"Predicate {predicate.id} references unknown entity {entity_id}")
        
        # Validate ligature entity references
        for ligature in doc.ligatures:
            for entity_id in ligature.connected_entities:
                if entity_id not in entity_ids:
                    errors.append(f"Ligature {ligature.id} references unknown entity {entity_id}")
        
        # Validate context parent references
        for context in doc.contexts:
            if context.parent_context and context.parent_context not in context_ids:
                errors.append(f"Context {context.id} references unknown parent {context.parent_context}")
        
        return len(errors) == 0, errors


class EGRFSerializer:
    """Serializer for EGRF documents."""
    
    @staticmethod
    def to_json(doc: EGRFDocument, indent: int = 2) -> str:
        """Convert EGRF document to JSON string."""
        return json.dumps(asdict(doc), indent=indent, default=str)
    
    @staticmethod
    def from_json(json_str: str) -> EGRFDocument:
        """Create EGRF document from JSON string."""
        data = json.loads(json_str)
        return EGRFSerializer.from_dict(data)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> EGRFDocument:
        """Create EGRF document from dictionary."""
        # This is a simplified implementation
        # In practice, we'd need more sophisticated deserialization
        doc = EGRFDocument()
        
        if 'format' in data:
            doc.format = data['format']
        if 'version' in data:
            doc.version = data['version']
        
        # Handle entities
        if 'entities' in data:
            for entity_data in data['entities']:
                entity = Entity(
                    id=entity_data['id'],
                    name=entity_data['name'],
                    type=entity_data['type']
                )
                doc.entities.append(entity)
        
        # Handle predicates
        if 'predicates' in data:
            for pred_data in data['predicates']:
                predicate = Predicate(
                    id=pred_data['id'],
                    name=pred_data['name'],
                    type=pred_data['type'],
                    arity=pred_data['arity'],
                    connected_entities=pred_data.get('connected_entities', [])
                )
                doc.predicates.append(predicate)
        
        # Handle contexts
        if 'contexts' in data:
            for ctx_data in data['contexts']:
                context = Context(
                    id=ctx_data['id'],
                    type=ctx_data['type'],
                    parent_context=ctx_data.get('parent_context'),
                    contained_items=ctx_data.get('contained_items', []),
                    nesting_level=ctx_data.get('nesting_level', 0)
                )
                doc.contexts.append(context)
        
        return doc


def create_simple_example() -> EGRFDocument:
    """Create a simple EGRF example: 'Socrates is mortal'."""
    doc = EGRFDocument()
    doc.metadata.title = "Socrates is Mortal"
    doc.metadata.description = "Simple existential graph example"
    
    # Create entity for Socrates
    socrates = Entity(
        id="socrates",
        name="Socrates",
        type="constant"
    )
    socrates.visual.path = [Point(100, 150), Point(200, 150)]
    socrates.labels = [Label("Socrates", Point(150, 140))]
    doc.entities.append(socrates)
    
    # Create predicate for Mortal
    mortal = Predicate(
        id="mortal",
        name="Mortal",
        type="relation",
        arity=1,
        connected_entities=["socrates"]
    )
    mortal.visual.position = Point(150, 180)
    mortal.labels = [Label("Mortal", Point(150, 180))]
    doc.predicates.append(mortal)
    
    # Create root context
    root = Context(
        id="root",
        type="sheet_of_assertion",
        contained_items=["socrates", "mortal"]
    )
    doc.contexts.append(root)
    
    # Add semantic information
    doc.semantics.logical_form = {
        "clif_equivalent": "(and (Person Socrates) (Mortal Socrates))",
        "egif_equivalent": "[Person: Socrates] (Mortal Socrates)"
    }
    doc.semantics.validation = {"is_valid": True}
    
    return doc


if __name__ == "__main__":
    # Test the implementation
    print("Creating simple EGRF example...")
    doc = create_simple_example()
    
    print("Validating document...")
    validator = EGRFValidator()
    is_valid, errors = validator.validate_document(doc)
    
    if is_valid:
        print("✓ Document is valid!")
    else:
        print("✗ Document validation failed:")
        for error in errors:
            print(f"  - {error}")
    
    print("\nSerializing to JSON...")
    json_output = EGRFSerializer.to_json(doc)
    print("JSON output length:", len(json_output), "characters")
    
    print("\nTesting round-trip serialization...")
    doc2 = EGRFSerializer.from_json(json_output)
    print("Round-trip successful:", doc.entities[0].name == doc2.entities[0].name)

