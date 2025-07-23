"""
EGRF v3.0 Corpus Validator

Validates EGRF files against the corpus schema and logical constraints.
"""

import os
import json
import yaml
from typing import Dict, Any, List, Tuple, Optional

from .logical_types import (
    LogicalElement, LogicalPredicate, LogicalEntity, LogicalContext,
    ContainmentRelationship, create_logical_context, create_logical_predicate,
    create_logical_entity
)
from .containment_hierarchy import (
    ContainmentHierarchyManager, HierarchyValidator, ValidationResult
)


def load_corpus_index(corpus_dir: str) -> Dict[str, Any]:
    """
    Load the corpus index file.
    
    Args:
        corpus_dir: Path to the corpus directory
        
    Returns:
        Dictionary containing corpus index data
    """
    index_path = os.path.join(corpus_dir, "corpus_index.json")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Corpus index file not found at {index_path}")
    
    with open(index_path, "r") as f:
        return json.load(f)


def load_example(example_id: str, corpus_dir: str) -> Dict[str, Any]:
    """
    Load a corpus example.
    
    Args:
        example_id: ID of the example to load
        corpus_dir: Path to the corpus directory
        
    Returns:
        Dictionary containing example data
    """
    # Find example in index
    index = load_corpus_index(corpus_dir)
    example_info = None
    
    for example in index["examples"]:
        if example["id"] == example_id:
            example_info = example
            break
    
    if not example_info:
        raise ValueError(f"Example {example_id} not found in corpus index")
    
    category = example_info["category"]
    
    # Load EGRF file
    egrf_path = os.path.join(corpus_dir, category, f"{example_id}.egrf")
    
    if not os.path.exists(egrf_path):
        raise FileNotFoundError(f"EGRF file not found at {egrf_path}")
    
    with open(egrf_path, "r") as f:
        egrf_data = json.load(f)
    
    # Load CLIF file
    clif_path = os.path.join(corpus_dir, category, f"{example_id}.clif")
    
    if not os.path.exists(clif_path):
        raise FileNotFoundError(f"CLIF file not found at {clif_path}")
    
    with open(clif_path, "r") as f:
        clif_data = f.read()
    
    # Load EG-HG file
    eg_hg_path = os.path.join(corpus_dir, category, f"{example_id}.eg-hg")
    
    if not os.path.exists(eg_hg_path):
        raise FileNotFoundError(f"EG-HG file not found at {eg_hg_path}")
    
    with open(eg_hg_path, "r") as f:
        eg_hg_data = f.read()
    
    # Load metadata
    metadata_path = os.path.join(corpus_dir, category, f"{example_id}.json")
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    return {
        "id": example_id,
        "category": category,
        "egrf": egrf_data,
        "clif": clif_data,
        "eg_hg": eg_hg_data,
        "metadata": metadata
    }


def validate_egrf_structure(egrf_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate EGRF structure.
    
    Args:
        egrf_data: EGRF data to validate
        
    Returns:
        Tuple of (valid, messages)
    """
    messages = []
    
    # Check required sections
    required_sections = ["elements", "containment", "connections"]
    for section in required_sections:
        if section not in egrf_data:
            messages.append(f"Missing required section: {section}")
            return False, messages
    
    # Check elements
    elements = egrf_data["elements"]
    if not elements:
        messages.append("No elements found")
        return False, messages
    
    for element_id, element in elements.items():
        # Check element type
        if "element_type" not in element:
            messages.append(f"Element {element_id} missing element_type")
            return False, messages
        
        element_type = element["element_type"]
        if element_type not in ["context", "predicate", "entity"]:
            messages.append(f"Invalid element_type for {element_id}: {element_type}")
            return False, messages
        
        # Check logical properties
        if "logical_properties" not in element:
            messages.append(f"Element {element_id} missing logical_properties")
            return False, messages
        
        logical_properties = element["logical_properties"]
        
        # Type-specific checks
        if element_type == "context":
            if "context_type" not in logical_properties:
                messages.append(f"Context {element_id} missing context_type")
                return False, messages
            
            context_type = logical_properties["context_type"]
            if context_type not in ["sheet", "cut", "sheet_of_assertion"]:
                messages.append(f"Invalid context_type for {element_id}: {context_type}")
                return False, messages
        
        elif element_type == "predicate":
            if "arity" not in logical_properties:
                messages.append(f"Predicate {element_id} missing arity")
                return False, messages
        
        elif element_type == "entity":
            if "entity_type" not in logical_properties:
                messages.append(f"Entity {element_id} missing entity_type")
                return False, messages
    
    # Check containment
    containment = egrf_data["containment"]
    for element_id, container_id in containment.items():
        if element_id not in elements:
            messages.append(f"Containment references non-existent element: {element_id}")
            return False, messages
        
        if container_id != "none" and container_id != "viewport" and container_id not in elements:
            messages.append(f"Containment references non-existent container: {container_id}")
            return False, messages
    
    # Check connections
    connections = egrf_data["connections"]
    for connection in connections:
        if "entity_id" not in connection:
            messages.append("Connection missing entity_id")
            return False, messages
        
        if "predicate_id" not in connection:
            messages.append("Connection missing predicate_id")
            return False, messages
        
        entity_id = connection["entity_id"]
        predicate_id = connection["predicate_id"]
        
        if entity_id not in elements:
            messages.append(f"Connection references non-existent entity: {entity_id}")
            return False, messages
        
        if predicate_id not in elements:
            messages.append(f"Connection references non-existent predicate: {predicate_id}")
            return False, messages
        
        if elements[entity_id]["element_type"] != "entity":
            messages.append(f"Connection entity_id {entity_id} is not an entity")
            return False, messages
        
        if elements[predicate_id]["element_type"] != "predicate":
            messages.append(f"Connection predicate_id {predicate_id} is not a predicate")
            return False, messages
    
    # Check ligatures if present
    if "ligatures" in egrf_data:
        ligatures = egrf_data["ligatures"]
        for ligature in ligatures:
            if "entity1_id" not in ligature:
                messages.append("Ligature missing entity1_id")
                return False, messages
            
            if "entity2_id" not in ligature:
                messages.append("Ligature missing entity2_id")
                return False, messages
            
            entity1_id = ligature["entity1_id"]
            entity2_id = ligature["entity2_id"]
            
            if entity1_id not in elements:
                messages.append(f"Ligature references non-existent entity: {entity1_id}")
                return False, messages
            
            if entity2_id not in elements:
                messages.append(f"Ligature references non-existent entity: {entity2_id}")
                return False, messages
            
            if elements[entity1_id]["element_type"] != "entity":
                messages.append(f"Ligature entity1_id {entity1_id} is not an entity")
                return False, messages
            
            if elements[entity2_id]["element_type"] != "entity":
                messages.append(f"Ligature entity2_id {entity2_id} is not an entity")
                return False, messages
    
    messages.append("EGRF structure is valid")
    return True, messages


def validate_logical_consistency(egrf_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate logical consistency in EGRF data.
    
    Args:
        egrf_data: EGRF data to validate
        
    Returns:
        Tuple of (valid, messages)
    """
    messages = []
    
    # Extract elements and connections
    elements = egrf_data["elements"]
    connections = egrf_data["connections"]
    
    # Check predicate arity matches connections
    predicate_connections = {}
    for connection in connections:
        predicate_id = connection["predicate_id"]
        if predicate_id not in predicate_connections:
            predicate_connections[predicate_id] = []
        predicate_connections[predicate_id].append(connection)
    
    for predicate_id, predicate_data in elements.items():
        if predicate_data["element_type"] != "predicate":
            continue
        
        arity = predicate_data["logical_properties"].get("arity", 0)
        actual_connections = len(predicate_connections.get(predicate_id, []))
        
        if arity != actual_connections:
            messages.append(f"Predicate {predicate_id} has arity {arity} but {actual_connections} connections")
            return False, messages
    
    # Check for double-cut implications
    contexts = {
        element_id: element
        for element_id, element in elements.items()
        if element["element_type"] == "context"
    }
    
    # Find all cuts
    cuts = {
        element_id: element
        for element_id, element in contexts.items()
        if element["logical_properties"]["context_type"] == "cut"
    }
    
    # Check nesting levels
    for cut_id, cut in cuts.items():
        nesting_level = cut["logical_properties"].get("nesting_level", 0)
        
        # For implications, we should have pairs of cuts with consecutive nesting levels
        if nesting_level > 0:
            # Find cuts with nesting_level - 1
            outer_cuts = [
                other_id
                for other_id, other in cuts.items()
                if other["logical_properties"].get("nesting_level", 0) == nesting_level - 1
            ]
            
            if not outer_cuts:
                messages.append(f"Cut {cut_id} has nesting level {nesting_level} but no outer cut found")
                # This is a warning, not an error
    
    messages.append("Logical consistency is valid")
    return True, messages


def validate_containment_hierarchy(egrf_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate containment hierarchy in EGRF data.
    
    Args:
        egrf_data: EGRF data to validate
        
    Returns:
        Tuple of (valid, messages)
    """
    messages = []
    
    try:
        # Create hierarchy manager
        hierarchy_manager = ContainmentHierarchyManager()
        
        # Extract elements and containment
        elements = egrf_data["elements"]
        containment = egrf_data["containment"]
        
        # Add elements to hierarchy manager
        for element_id, element in elements.items():
            element_type = element["element_type"]
            logical_properties = element["logical_properties"]
            
            if element_type == "context":
                context_type = logical_properties["context_type"]
                is_root = logical_properties.get("is_root", False)
                nesting_level = logical_properties.get("nesting_level", 0)
                
                context = create_logical_context(
                    id=element_id,
                    name=logical_properties.get("name", f"Context {element_id}"),
                    container=containment.get(element_id, "none"),
                    context_type=context_type,
                    is_root=is_root,
                    nesting_level=nesting_level
                )
                
                hierarchy_manager.add_element(context)
            
            elif element_type == "predicate":
                arity = logical_properties.get("arity", 0)
                
                predicate = create_logical_predicate(
                    id=element_id,
                    name=logical_properties.get("name", f"Predicate {element_id}"),
                    container=containment.get(element_id, "none"),
                    arity=arity
                )
                
                hierarchy_manager.add_element(predicate)
            
            elif element_type == "entity":
                entity_type = logical_properties.get("entity_type", "constant")
                connected_predicates = logical_properties.get("connected_predicates", [])
                
                entity = create_logical_entity(
                    id=element_id,
                    name=logical_properties.get("name", f"Entity {element_id}"),
                    connected_predicates=connected_predicates,
                    entity_type=entity_type
                )
                
                # Set container after creation since create_logical_entity uses "auto"
                entity.layout_constraints.container = containment.get(element_id, "none")
                
                hierarchy_manager.add_element(entity)
        
        # Add containment relationships
        for element_id, container_id in containment.items():
            if container_id != "none" and container_id in hierarchy_manager.elements:
                # Add element to container's relationship
                if container_id not in hierarchy_manager.relationships:
                    relationship = ContainmentRelationship(
                        container=container_id,
                        contained_elements=[element_id]
                    )
                    hierarchy_manager.add_relationship(relationship)
                else:
                    if element_id not in hierarchy_manager.relationships[container_id].contained_elements:
                        hierarchy_manager.relationships[container_id].contained_elements.append(element_id)
        
        # Create validator
        validator = HierarchyValidator(hierarchy_manager)
        
        # Validate hierarchy
        validation_report = validator.validate()
        
        # Check for circular references
        circular_refs = []
        for error in validation_report.errors:
            if error.error_type == ValidationResult.CIRCULAR_REFERENCE:
                circular_refs.append(error.message)
        
        if circular_refs:
            messages.append(f"Circular references detected: {', '.join(circular_refs)}")
        
        # Check for orphaned elements
        orphaned = []
        for error in validation_report.errors:
            if error.error_type == ValidationResult.ORPHANED_ELEMENT:
                orphaned.append(error.message)
        
        if orphaned:
            messages.append(f"Orphaned elements detected: {', '.join(orphaned)}")
        
        # Check for constraint violations
        violations = []
        for error in validation_report.errors:
            if error.error_type == ValidationResult.CONSTRAINT_VIOLATION:
                violations.append(error.message)
        
        if violations:
            messages.append(f"Constraint violations detected: {', '.join(violations)}")
        
        # Check for nesting level inconsistencies
        nesting_issues = []
        for error in validation_report.errors:
            if error.error_type == ValidationResult.INVALID_NESTING:
                nesting_issues.append(error.message)
        
        if nesting_issues:
            messages.append(f"Nesting level inconsistencies detected: {', '.join(nesting_issues)}")
        
        # Overall validation result
        if validation_report.is_valid:
            messages.append("Containment hierarchy is valid")
            return True, messages
        else:
            messages.append(f"Containment hierarchy validation failed with {len(validation_report.errors)} errors")
            return False, messages
    
    except Exception as e:
        messages.append(f"Error validating containment hierarchy: {str(e)}")
        return False, messages

