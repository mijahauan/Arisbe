#!/usr/bin/env python3
"""
EG-HG to EGRF v3.0 Converter

This module provides functionality to convert EG-HG (Existential Graph Hypergraph)
data to EGRF v3.0 (Existential Graph Rendering Format) with logical containment.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import json
import yaml
from pathlib import Path

from ..logical_types import (
    create_logical_context, create_logical_predicate, create_logical_entity,
    LogicalElement, LogicalContext, LogicalPredicate, LogicalEntity,
    ContainmentRelationship
)
from ..containment_hierarchy import ContainmentHierarchyManager


class EgHgToEgrfConverter:
    """
    Converter for EG-HG to EGRF v3.0 format.
    
    This class handles the conversion of EG-HG data to EGRF v3.0 format,
    including the creation of logical elements, containment relationships,
    and layout constraints.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self._eg_hg_data = {}
        self._egrf_data = {
            "metadata": {
                "version": "3.0.0",
                "format": "egrf",
                "id": "",
                "description": ""
            },
            "elements": {},
            "containment": {},
            "connections": [],
            "ligatures": [],
            "layout_constraints": []
        }
        self._context_map = {}  # Maps EG-HG context IDs to EGRF IDs
        self._predicate_map = {}  # Maps EG-HG predicate IDs to EGRF IDs
        self._entity_map = {}  # Maps EG-HG entity IDs to EGRF IDs
        self._hierarchy_manager = ContainmentHierarchyManager()
    
    def convert(self, eg_hg_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert EG-HG data to EGRF v3.0 format.
        
        Args:
            eg_hg_data: Dictionary containing EG-HG data
            
        Returns:
            Dictionary containing EGRF v3.0 data
        """
        self._eg_hg_data = eg_hg_data
        
        # Set metadata
        self._egrf_data["metadata"]["id"] = eg_hg_data.get("id", "")
        self._egrf_data["metadata"]["description"] = eg_hg_data.get("description", "")
        
        # Process contexts (sheet and cuts)
        self._process_contexts()
        
        # Process predicates
        self._process_predicates()
        
        # Process entities and connections
        self._process_entities()
        
        # Generate layout constraints
        self._generate_layout_constraints()
        
        return self._egrf_data
    
    def _process_contexts(self) -> None:
        """Process contexts (sheet and cuts) from EG-HG data."""
        if "graph" not in self._eg_hg_data or "contexts" not in self._eg_hg_data["graph"]:
            # Create default sheet if no contexts defined
            sheet_id = "sheet"
            sheet = create_logical_context(
                id=sheet_id,
                name="Sheet of Assertion",
                container="none",
                context_type="sheet_of_assertion",
                is_root=True,
                nesting_level=0
            )
            self._egrf_data["elements"][sheet_id] = sheet.to_dict()
            
            # Add to hierarchy manager
            self._hierarchy_manager.add_element(sheet)
            return
        
        # Process each context from EG-HG
        contexts = self._eg_hg_data["graph"]["contexts"]
        
        # First pass: create all contexts
        for context in contexts:
            context_id = context["id"]
            
            # Generate EGRF ID
            egrf_id = "sheet" if context["type"] == "sheet" else f"context_{context_id}"
            self._context_map[context_id] = egrf_id
            
            # Determine context type and nesting level
            context_type = "sheet_of_assertion" if context["type"] == "sheet" else "cut"
            is_root = context["parent"] is None
            
            # Create logical context
            logical_context = create_logical_context(
                id=egrf_id,
                name=f"{context_type.capitalize()} {context_id}",
                container="none" if is_root else "placeholder",  # Will be updated in second pass
                context_type=context_type,
                is_root=is_root,
                nesting_level=0  # Will be updated in second pass
            )
            
            # Add to EGRF data
            self._egrf_data["elements"][egrf_id] = logical_context.to_dict()
            
            # Add to hierarchy manager
            self._hierarchy_manager.add_element(logical_context)
        
        # Second pass: establish containment relationships and update nesting levels
        for context in contexts:
            context_id = context["id"]
            egrf_id = self._context_map[context_id]
            parent_id = context["parent"]
            
            if parent_id is not None:
                # Get parent EGRF ID
                parent_egrf_id = self._context_map.get(parent_id, "sheet")
                
                # Update container in element data
                self._egrf_data["elements"][egrf_id]["logical_properties"]["container"] = parent_egrf_id
                self._egrf_data["containment"][egrf_id] = parent_egrf_id
                
                # Add to hierarchy manager
                # Use add_relationship instead of add_containment
                from ..logical_types import ContainmentRelationship
                relationship = ContainmentRelationship(
                    container=parent_egrf_id,
                    contained_elements=[egrf_id]
                )
                self._hierarchy_manager.add_relationship(relationship)
        
        # Update nesting levels based on hierarchy
        for context_id, egrf_id in self._context_map.items():
            # Calculate nesting level manually
            level = 0
            current = context_id
            visited = set()
            
            while current and current not in visited:
                visited.add(current)
                # Find parent in original EG-HG data
                for ctx in self._eg_hg_data["graph"]["contexts"]:
                    if ctx["id"] == current and ctx["parent"] is not None:
                        level += 1
                        current = ctx["parent"]
                        break
                else:
                    break
            
            # Update nesting level in EGRF data
            self._egrf_data["elements"][egrf_id]["logical_properties"]["nesting_level"] = level
    
    def _process_predicates(self) -> None:
        """Process predicates from EG-HG data."""
        if "graph" not in self._eg_hg_data or "predicates" not in self._eg_hg_data["graph"]:
            return
        
        predicates = self._eg_hg_data["graph"]["predicates"]
        
        for predicate in predicates:
            predicate_id = predicate["id"]
            
            # Generate EGRF ID
            egrf_id = f"predicate_{predicate_id}"
            self._predicate_map[predicate_id] = egrf_id
            
            # Get containing context
            context_id = predicate["context"]
            containing_context = self._context_map.get(context_id, "sheet")
            
            # Create logical predicate
            logical_predicate = create_logical_predicate(
                id=egrf_id,
                name=predicate["label"],
                container=containing_context,
                arity=predicate["arity"]
            )
            
            # Add to EGRF data
            self._egrf_data["elements"][egrf_id] = logical_predicate.to_dict()
            self._egrf_data["containment"][egrf_id] = containing_context
            
            # Add to hierarchy manager
            self._hierarchy_manager.add_element(logical_predicate)
            
            # Add to hierarchy manager
            # Use add_relationship instead of add_containment
            from ..logical_types import ContainmentRelationship
            relationship = ContainmentRelationship(
                container=containing_context,
                contained_elements=[egrf_id]
            )
            self._hierarchy_manager.add_relationship(relationship)
    
    def _process_entities(self) -> None:
        """Process entities and connections from EG-HG data."""
        if "graph" not in self._eg_hg_data:
            return
        
        # Process entities
        if "entities" in self._eg_hg_data["graph"]:
            entities = self._eg_hg_data["graph"]["entities"]
            
            for entity in entities:
                entity_id = entity["id"]
                
                # Generate EGRF ID
                egrf_id = f"entity_{entity_id}"
                self._entity_map[entity_id] = egrf_id
                
                # Get connected predicates (will be updated later)
                connected_predicates = []
                
                # Create logical entity
                logical_entity = create_logical_entity(
                    id=egrf_id,
                    name=entity.get("label", f"Entity {entity_id}"),
                    connected_predicates=connected_predicates,
                    entity_type=entity.get("type", "constant")
                )
                
                # Add to EGRF data
                self._egrf_data["elements"][egrf_id] = logical_entity.to_dict()
                
                # Default containment to sheet (will be updated based on connections)
                self._egrf_data["containment"][egrf_id] = "sheet"
                
                # Add to hierarchy manager
                # Use add_element and add_relationship instead of add_containment
                self._hierarchy_manager.add_element(logical_entity)
                
                from ..logical_types import ContainmentRelationship
                relationship = ContainmentRelationship(
                    container="sheet",
                    contained_elements=[egrf_id]
                )
                self._hierarchy_manager.add_relationship(relationship)
        
        # Process connections
        if "connections" in self._eg_hg_data["graph"]:
            connections = self._eg_hg_data["graph"]["connections"]
            
            for connection in connections:
                # Check if this is a predicate-entity connection
                if "predicate" in connection:
                    predicate_id = connection["predicate"]
                    entity_ids = connection["entities"]
                    roles = connection.get("roles", [])
                    
                    # Map IDs to EGRF IDs
                    egrf_predicate_id = self._predicate_map.get(predicate_id)
                    
                    if not egrf_predicate_id:
                        continue
                    
                    for i, entity_id in enumerate(entity_ids):
                        egrf_entity_id = self._entity_map.get(entity_id)
                        
                        if not egrf_entity_id:
                            continue
                        
                        # Determine role
                        role = roles[i] if i < len(roles) else f"arg{i+1}"
                        
                        # Add connection to EGRF data
                        self._egrf_data["connections"].append({
                            "entity_id": egrf_entity_id,
                            "predicate_id": egrf_predicate_id,
                            "role": role
                        })
                        
                        # Update entity containment to match predicate's container
                        predicate_container = self._egrf_data["containment"][egrf_predicate_id]
                        entity_container = self._egrf_data["containment"][egrf_entity_id]
                        
                        # If entity is in sheet but predicate is in a cut, move entity to sheet
                        # This ensures entities are properly contained for ligatures
                        if entity_container != predicate_container:
                            # Find common ancestor
                            # Implement find_common_ancestor since it's not in ContainmentHierarchyManager
                            def find_common_ancestor(self, element1_id, element2_id):
                                """Find the common ancestor of two elements."""
                                ancestors1 = self._hierarchy_manager.get_ancestors(element1_id)
                                ancestors2 = self._hierarchy_manager.get_ancestors(element2_id)
                                
                                # Add the elements themselves to check if one contains the other
                                ancestors1.insert(0, element1_id)
                                ancestors2.insert(0, element2_id)
                                
                                # Find common ancestors
                                common_ancestors = [a for a in ancestors1 if a in ancestors2]
                                
                                # Return the closest common ancestor (first in the list)
                                return common_ancestors[0] if common_ancestors else None
                            
                            common_ancestor = find_common_ancestor(self, entity_container, predicate_container)
                            
                            if common_ancestor:
                                self._egrf_data["containment"][egrf_entity_id] = common_ancestor
                                
                                # Update hierarchy manager
                                # First remove old relationship
                                old_container = self._hierarchy_manager.get_container(egrf_entity_id)
                                if old_container:
                                    # Find the relationship containing this entity
                                    for rel_container, rel in self._hierarchy_manager.relationships.items():
                                        if egrf_entity_id in rel.contained_elements and rel_container == old_container:
                                            # Remove entity from this relationship
                                            rel.contained_elements.remove(egrf_entity_id)
                                            break
                                
                                # Add to new container
                                entity = self._hierarchy_manager.elements.get(egrf_entity_id)
                                if entity:
                                    entity.layout_constraints.container = common_ancestor
                                
                                # Add to new relationship or create one
                                rel = self._hierarchy_manager.relationships.get(common_ancestor)
                                if rel:
                                    if egrf_entity_id not in rel.contained_elements:
                                        rel.contained_elements.append(egrf_entity_id)
                                else:
                                    from ..logical_types import ContainmentRelationship
                                    new_rel = ContainmentRelationship(
                                        container=common_ancestor,
                                        contained_elements=[egrf_entity_id]
                                    )
                                    self._hierarchy_manager.add_relationship(new_rel)
                # Check if this is an entity-entity connection (ligature)
                elif "entity1" in connection and "entity2" in connection:
                    entity1_id = connection["entity1"]
                    entity2_id = connection["entity2"]
                    connection_type = connection.get("type", "identity")
                    
                    # Get EGRF IDs
                    egrf_entity1_id = self._entity_map.get(entity1_id)
                    egrf_entity2_id = self._entity_map.get(entity2_id)
                    
                    if egrf_entity1_id and egrf_entity2_id:
                        # Add ligature to EGRF data
                        self._egrf_data["ligatures"].append({
                            "entity1_id": egrf_entity1_id,
                            "entity2_id": egrf_entity2_id,
                            "type": connection_type
                        })
    
    def _generate_layout_constraints(self) -> None:
        """Generate layout constraints for EGRF v3.0."""
        constraints = []
        
        # Add size constraints for all elements
        for element_id, element in self._egrf_data["elements"].items():
            element_type = element["element_type"]
            
            if element_type == "context":
                context_type = element["logical_properties"]["context_type"]
                if context_type == "sheet_of_assertion":
                    # Sheet of assertion is the root and has fixed size
                    constraints.append({
                        "element_id": element_id,
                        "constraint_type": "size",
                        "width": 800,
                        "height": 600,
                        "min_width": 800,
                        "min_height": 600,
                        "max_width": 800,
                        "max_height": 600
                    })
                else:
                    # Cuts auto-size based on content
                    constraints.append({
                        "element_id": element_id,
                        "constraint_type": "size",
                        "width": 300,
                        "height": 200,
                        "min_width": 100,
                        "min_height": 100,
                        "max_width": 1000,
                        "max_height": 1000,
                        "auto_size": True
                    })
            elif element_type == "predicate":
                # Predicates have fixed size based on arity
                arity = element["logical_properties"]["arity"]
                width = 100 + (arity * 20)
                height = 50
                
                constraints.append({
                    "element_id": element_id,
                    "constraint_type": "size",
                    "width": width,
                    "height": height,
                    "min_width": width * 0.8,
                    "min_height": height * 0.8,
                    "max_width": width * 1.2,
                    "max_height": height * 1.2
                })
            elif element_type == "entity":
                # Entities are small points
                constraints.append({
                    "element_id": element_id,
                    "constraint_type": "size",
                    "width": 10,
                    "height": 10,
                    "min_width": 5,
                    "min_height": 5,
                    "max_width": 15,
                    "max_height": 15
                })
        
        # Add position constraints
        for element_id, element in self._egrf_data["elements"].items():
            # Skip sheet of assertion (it's the root)
            if element_id == "sheet":
                continue
            
            # Get container
            container = self._egrf_data["containment"].get(element_id, "sheet")
            
            # Add position constraint
            constraints.append({
                "element_id": element_id,
                "constraint_type": "position",
                "container": container,
                "x": 0.5,  # Center horizontally
                "y": 0.5,  # Center vertically
                "x_unit": "relative",
                "y_unit": "relative"
            })
        
        # Add spacing constraints
        for element_id, element in self._egrf_data["elements"].items():
            # Add spacing constraint
            constraints.append({
                "element_id": element_id,
                "constraint_type": "spacing",
                "min_spacing": 10,
                "preferred_spacing": 20
            })
        
        self._egrf_data["layout_constraints"] = constraints


def convert_eg_hg_to_egrf(eg_hg_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert EG-HG data to EGRF v3.0 format.
    
    Args:
        eg_hg_data: Dictionary containing EG-HG data
        
    Returns:
        Dictionary containing EGRF v3.0 data
    """
    converter = EgHgToEgrfConverter()
    return converter.convert(eg_hg_data)


def parse_eg_hg_content(content: str) -> Dict[str, Any]:
    """
    Parse EG-HG content in YAML-like format.
    
    Args:
        content: String containing EG-HG content
        
    Returns:
        Dictionary containing parsed EG-HG data
    """
    # Simple parser for the YAML-like format used in EG-HG files
    # This is a basic implementation and may need to be enhanced
    # for more complex EG-HG files
    
    result = {}
    current_section = None
    current_dict = None
    current_list = None
    current_list_key = None
    indent_level = 0
    
    lines = content.split('\n')
    
    for line in lines:
        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Calculate indent level
        current_indent = len(line) - len(line.lstrip())
        
        # Check if this is a new section
        if ':' in line and current_indent == 0:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if value:
                result[key] = value
            else:
                current_section = key
                result[current_section] = {}
                current_dict = result[current_section]
                current_list = None
                current_list_key = None
        
        # Check if this is a list item
        elif line.strip().startswith('-'):
            item_content = line.strip()[1:].strip()
            
            # If we're not in a list yet, create one
            if current_list is None:
                # Find the parent key based on indentation
                if current_indent > 0 and current_dict is not None:
                    # We're in a nested structure, find the key from previous line
                    for prev_line in reversed(lines[:lines.index(line)]):
                        if prev_line.strip() and not prev_line.strip().startswith('#') and not prev_line.strip().startswith('-'):
                            if ':' in prev_line and len(prev_line) - len(prev_line.lstrip()) < current_indent:
                                list_key = prev_line.split(':', 1)[0].strip()
                                if list_key not in current_dict:
                                    current_dict[list_key] = []
                                current_list = current_dict[list_key]
                                current_list_key = list_key
                                break
            
            # Parse the list item
            if ':' in item_content:
                # This is a dictionary item
                item_dict = {}
                key, value = item_content.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value:
                    item_dict[key] = value
                
                if current_list is not None:
                    current_list.append(item_dict)
                    current_dict = item_dict
            else:
                # This is a simple item
                if current_list is not None:
                    current_list.append(item_content)
        
        # Check if this is a key-value pair in a dictionary
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if current_dict is not None:
                if value:
                    if value.lower() == 'null':
                        current_dict[key] = None
                    else:
                        current_dict[key] = value
                else:
                    # This is a nested dictionary or list
                    if line.strip().endswith(':'):
                        # Check if next line is a list item
                        next_line_idx = lines.index(line) + 1
                        while next_line_idx < len(lines) and (not lines[next_line_idx].strip() or lines[next_line_idx].strip().startswith('#')):
                            next_line_idx += 1
                        
                        if next_line_idx < len(lines) and lines[next_line_idx].strip().startswith('-'):
                            # Next line is a list item, create a list
                            current_dict[key] = []
                            current_list = current_dict[key]
                            current_list_key = key
                        else:
                            # Create a nested dictionary
                            current_dict[key] = {}
                            current_dict = current_dict[key]
                            current_list = None
                            current_list_key = None
    
    return result


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python eg_hg_to_egrf.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Read input file
    with open(input_file, "r") as f:
        content = f.read()
    
    # Parse EG-HG content
    eg_hg_data = parse_eg_hg_content(content)
    
    # Convert to EGRF v3.0
    egrf_data = convert_eg_hg_to_egrf(eg_hg_data)
    
    # Write output file
    with open(output_file, "w") as f:
        json.dump(egrf_data, f, indent=2)
    
    print(f"Converted {input_file} to {output_file}")

