"""
EGIF Transformation Interface - Parse corpus EGIFs, apply transformations, generate new EGIFs.
Uses existing egif_parser_dau.py and formal_transformation_rules.py.
"""

import json
from typing import Dict, List, Optional, Any, Set, Tuple, FrozenSet
import dataclasses
from frozendict import frozendict
from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from egif_parser_dau import parse_egif
from egif_generator_dau import EGIFGenerator
from formal_transformation_rules import FormalTransformationEngine, TransformationResult


@dataclasses.dataclass
class TransformationRequest:
    """Request for applying a transformation to an EGIF."""
    source_egif: str
    rule_name: str
    target_area_description: str
    operation_details: Dict[str, Any]
    description: str


@dataclasses.dataclass
class TransformationResponse:
    """Response from applying a transformation."""
    success: bool
    original_egif: str
    result_egif: Optional[str]
    original_egi: RelationalGraphWithCuts
    result_egi: Optional[RelationalGraphWithCuts]
    transformation_details: TransformationResult
    error_message: Optional[str]


class EGIFTransformationInterface:
    """Interface for parsing EGIFs, applying transformations, and generating new EGIFs."""
    
    def __init__(self):
        self.engine = FormalTransformationEngine()
        self.egif_generator = EGIFGenerator()
    
    def load_corpus_egif(self, corpus_path: str) -> Tuple[str, Dict[str, Any]]:
        """Load EGIF from corpus JSON file."""
        with open(corpus_path, 'r') as f:
            corpus_data = json.load(f)
        
        egif_content = corpus_data.get("linear_forms", {}).get("egif", {}).get("content")
        if not egif_content:
            raise ValueError(f"No EGIF content found in {corpus_path}")
        
        return egif_content, corpus_data
    
    def parse_egif_to_egi(self, egif: str) -> RelationalGraphWithCuts:
        """Parse EGIF string into EGI using existing parser."""
        return parse_egif(egif)
    
    def generate_egif_from_egi(self, egi: RelationalGraphWithCuts) -> str:
        """Generate EGIF string from EGI using existing generator."""
        return self.egif_generator.generate_egif(egi)
    
    def identify_target_area(self, egi: RelationalGraphWithCuts, area_description: str) -> ElementID:
        """
        Identify target area for transformation based on description.
        Supports descriptions like:
        - "sheet" - the main sheet
        - "first_cut" - first cut encountered
        - "second_negation" - second negatively-enclosed area (innermost cut)
        - "inner_cut" - innermost cut
        """
        if area_description == "sheet":
            return egi.sheet
        
        if area_description == "first_cut":
            if egi.Cut:
                return next(iter(egi.Cut)).id
            raise ValueError("No cuts found in EGI")
        
        if area_description == "second_negation" or area_description == "inner_cut":
            # Find the innermost cut (not containing other cuts)
            innermost_cut = None
            for cut in egi.Cut:
                cut_contents = egi.area.get(cut.id, frozenset())
                has_nested_cuts = any(other_cut.id in cut_contents for other_cut in egi.Cut if other_cut.id != cut.id)
                if not has_nested_cuts:
                    innermost_cut = cut.id
                    break
            if innermost_cut:
                return innermost_cut
        
        # Try to find by ElementID directly - handle both string and ElementID types
        try:
            if isinstance(area_description, str):
                # Try to find an area with this ID in the current EGI
                for area_id in egi.area.keys():
                    if str(area_id) == area_description:
                        return area_id
                # If not found, try to create ElementID
                return ElementID(area_description)
            else:
                return area_description
        except:
            raise ValueError(f"Could not identify target area: {area_description}")
    
    def _calculate_area_polarity(self, egi: RelationalGraphWithCuts, area_id: str) -> Tuple[str, int]:
        """Calculate polarity and nesting depth for an area."""
        # Check if this is a cut area or the sheet
        is_cut_area = any(cut.id == area_id for cut in egi.Cut)
        
        if is_cut_area:
            # Count the number of cuts that enclose this cut
            enclosing_cuts = 0
            current_area = area_id
            
            # Traverse up the containment hierarchy
            while True:
                # Find which area contains the current area
                containing_area = None
                for area_candidate, contents in egi.area.items():
                    if current_area in contents:
                        containing_area = area_candidate
                        break
                
                if containing_area is None or containing_area == egi.sheet:
                    # Reached the sheet - we're done
                    break
                
                # If the containing area is a cut, increment enclosing cuts count
                if any(cut.id == containing_area for cut in egi.Cut):
                    enclosing_cuts += 1
                    current_area = containing_area
                else:
                    # Containing area is the sheet
                    break
            
            # Depth = number of enclosing cuts (the cut area itself doesn't add to depth)
            nesting_depth = enclosing_cuts
        else:
            # Sheet area has depth 0
            nesting_depth = 0
        
        polarity = "positive" if nesting_depth % 2 == 0 else "negative"
        return polarity, nesting_depth
    
    def create_insertion_subgraph(self, relation_spec: str) -> FrozenSet[ElementID]:
        """
        Create a subgraph for insertion based on specification.
        Examples:
        - '(Teacher "Socrates")' -> creates edge with constant vertex
        - '"Plato"' -> creates isolated constant vertex
        - '*x' -> creates isolated generic vertex
        """
        # For now, create a simple approach - parse the relation spec as mini-EGIF
        try:
            temp_egi = parse_egif(relation_spec)
            # Return all elements from the parsed EGI
            all_elements = set()
            for vertex in temp_egi.V:
                all_elements.add(vertex.id)
            for edge in temp_egi.E:
                all_elements.add(edge.id)
            return frozenset(all_elements)
        except Exception as e:
            raise ValueError(f"Could not parse insertion specification '{relation_spec}': {e}")
    
    def apply_transformation(self, request: TransformationRequest, existing_egi: RelationalGraphWithCuts = None) -> TransformationResponse:
        """Apply transformation to EGIF and return result."""
        
        try:
            # Use existing EGI if provided, otherwise parse EGIF
            if existing_egi is not None:
                original_egi = existing_egi
            else:
                original_egi = self.parse_egif_to_egi(request.source_egif)
            
            # Identify target area
            target_area = self.identify_target_area(original_egi, request.target_area_description)
            
            # Prepare transformation parameters
            if request.rule_name == "INS":
                # For insertion, create elements to insert based on the specification
                insertion_spec = request.operation_details.get("insert_content", "")
                if not insertion_spec:
                    raise ValueError("INS operation requires 'insert_content' specification")
                
                # Parse the insertion content to understand what to create
                # For INS operations, we need to handle variable references to existing variables
                import re
                
                # Extract variable names from the original EGIF
                var_pattern = r'\*([a-zA-Z][a-zA-Z0-9_]*)'
                logical_vars = re.findall(var_pattern, request.source_egif)
                
                # Parse insertion content to extract relation structure
                import re
                
                # Parse relation pattern: (RelationName arg1 arg2 ...)
                relation_match = re.match(r'\(\s*(\w+)\s+(.*?)\s*\)', insertion_spec.strip())
                if not relation_match:
                    raise ValueError(f"Invalid relation format: {insertion_spec}")
                
                relation_name = relation_match.group(1)
                args_str = relation_match.group(2)
                
                # Parse arguments
                arg_tokens = re.findall(r'(\*?\w+|"[^"]*")', args_str)
                
                # Create variable name to vertex ID mapping from original EGIF
                original_var_to_vertex = {}
                
                # Parse the original EGIF to extract variable-to-vertex mapping
                # based on how variables appear in relations
                import re
                
                # Find all relations in the original EGIF
                relation_matches = re.findall(r'\((\w+)\s+([^)]+)\)', request.source_egif)
                
                for orig_relation_name, orig_args_str in relation_matches:
                    # Parse arguments
                    orig_arg_tokens = re.findall(r'(\*?\w+|"[^"]*")', orig_args_str)
                    
                    # Find the corresponding edge in the original EGI
                    for edge_id in original_egi._edge_map.keys():
                        if original_egi.rel[edge_id] == orig_relation_name:
                            vertex_sequence = original_egi.nu[edge_id]
                            
                            # Map each argument to its corresponding vertex
                            for i, arg in enumerate(orig_arg_tokens):
                                if not (arg.startswith('"') and arg.endswith('"')):  # Not a constant
                                    var_name = arg.lstrip('*')  # Remove * if present
                                    if i < len(vertex_sequence):
                                        original_var_to_vertex[var_name] = vertex_sequence[i]
                            break
                
                # Store for later use in EGIF generation
                self._original_var_to_vertex = original_var_to_vertex
                
                # Map insertion arguments to existing vertex IDs
                mapped_vertex_sequence = []
                for arg in arg_tokens:
                    if arg.startswith('"') and arg.endswith('"'):
                        # Constant - create or reuse constant vertex
                        constant_name = arg[1:-1]  # Remove quotes
                        # Find existing constant vertex or create new one
                        constant_vertex_id = None
                        for vertex in original_egi.V:
                            vertex_obj = original_egi.get_vertex(vertex.id)
                            if not vertex_obj.is_generic and vertex_obj.label == constant_name:
                                constant_vertex_id = vertex.id
                                break
                        
                        if not constant_vertex_id:
                            constant_vertex_id = ElementID(f"const_{constant_name}")
                        
                        mapped_vertex_sequence.append(constant_vertex_id)
                    else:
                        # Variable - map to existing vertex ID
                        var_name = arg.lstrip('*')  # Remove * if present
                        if var_name in original_var_to_vertex:
                            mapped_vertex_sequence.append(original_var_to_vertex[var_name])
                        else:
                            raise ValueError(f"Variable {var_name} not found in original graph")
                
                # Create new edge for the insertion
                new_edge_id = ElementID(f"ins_{relation_name.lower()}")
                elements_to_insert = {new_edge_id}
                
                # Create a modified transformation context with the graph to insert
                from formal_transformation_rules import TransformationContext, AreaPolarity
                
                # Calculate area polarity
                polarity, depth = self._calculate_area_polarity(original_egi, target_area)
                area_polarity = AreaPolarity.POSITIVE if depth % 2 == 0 else AreaPolarity.NEGATIVE
                
                # Create context with insertion details
                context = TransformationContext(
                    source_egi=original_egi,
                    target_area=target_area,
                    selected_subgraph=frozenset(),
                    area_polarity=area_polarity,
                    nesting_depth=depth
                )
                
                # Add insertion details as attributes
                context.insertion_edge_id = new_edge_id
                context.insertion_relation_name = relation_name
                context.insertion_vertex_sequence = tuple(mapped_vertex_sequence)
                
                # Apply insertion using the rule directly
                ins_rule = self.engine.rules["INS"]
                result = ins_rule.apply_transformation(context)
            
            elif request.rule_name in ["DC+", "DC-"]:
                # For double cut operations
                selected_elements = request.operation_details.get("selected_elements", [])
                selected_subgraph = frozenset(ElementID(elem) for elem in selected_elements)
                
                result = self.engine.apply_rule(
                    request.rule_name,
                    original_egi,
                    target_area,
                    selected_subgraph
                )
            
            elif request.rule_name in ["ERA", "IT-"]:
                # For erasure and deiteration operations
                selected_elements = request.operation_details.get("selected_elements", [])
                selected_subgraph = frozenset(ElementID(elem) for elem in selected_elements)
                
                result = self.engine.apply_rule(
                    request.rule_name,
                    original_egi,
                    target_area,
                    selected_subgraph
                )
            
            elif request.rule_name == "IT+":
                # For iteration operations with destination area
                selected_elements = request.operation_details.get("selected_elements", [])
                selected_subgraph = frozenset(ElementID(elem) for elem in selected_elements)
                destination_area = request.operation_details.get("destination_area")
                
                if destination_area:
                    # Use destination area as target for iteration
                    destination_area_id = ElementID(destination_area) if isinstance(destination_area, str) else destination_area
                    result = self.engine.apply_rule(
                        request.rule_name,
                        original_egi,
                        destination_area_id,
                        selected_subgraph
                    )
                else:
                    # Fallback to original target area
                    result = self.engine.apply_rule(
                        request.rule_name,
                        original_egi,
                        target_area,
                        selected_subgraph
                    )
            
            else:
                raise ValueError(f"Unknown rule: {request.rule_name}")
            
            # Generate result EGIF with preserved variable mapping for INS
            from egif_generator_dau import EGIFGenerator, generate_egif
            
            # Debug logging for IT- transformation
            if request.rule_name == 'IT-':
                print(f"DEBUG: IT- transformation result.success = {result.success}")
                print(f"DEBUG: IT- transformation result.result_egi = {result.result_egi}")
                if result.result_egi is None:
                    print(f"DEBUG: IT- transformation error_message = {result.error_message}")
            
            # Check if transformation succeeded and has result EGI
            if not result.success or result.result_egi is None:
                raise ValueError(f"Transformation {request.rule_name} failed: {result.error_message if result else 'Unknown error'}")
            
            if request.rule_name == 'INS' and hasattr(self, '_original_var_to_vertex'):
                # Create a custom generator that preserves original variable assignments
                generator = EGIFGenerator(result.result_egi)
                
                # Pre-assign variable labels based on original mapping
                for var_name, vertex_id in self._original_var_to_vertex.items():
                    if vertex_id in result.result_egi._vertex_map:
                        generator.vertex_labels[vertex_id] = var_name
                        generator.used_labels.add(var_name)
                
                result_egif = generator.generate()
            else:
                result_egif = generate_egif(result.result_egi)
            
            return TransformationResponse(
                success=result.success,
                original_egif=request.source_egif,
                result_egif=result_egif,
                original_egi=original_egi,
                result_egi=result.result_egi,
                transformation_details=result,
                error_message=result.error_message if not result.success else None
            )
            
        except Exception as e:
            return TransformationResponse(
                success=False,
                original_egif=request.source_egif,
                result_egif=None,
                original_egi=None,
                result_egi=None,
                transformation_details=None,
                error_message=str(e)
            )
    
    def demonstrate_transformation(self, corpus_path: str, rule_name: str, 
                                 target_area_description: str, operation_details: Dict[str, Any],
                                 description: str = "") -> TransformationResponse:
        """Demonstrate transformation on a corpus EGIF."""
        
        print(f"🔄 EGIF Transformation Demonstration")
        print("=" * 40)
        
        # Load corpus EGIF
        try:
            egif_content, corpus_data = self.load_corpus_egif(corpus_path)
            print(f"📁 Loaded: {corpus_data.get('title', 'Unknown')}")
            print(f"📝 Description: {corpus_data.get('description', 'No description')}")
            print(f"🧮 Original EGIF: {egif_content}")
            
        except Exception as e:
            print(f"❌ Error loading corpus: {e}")
            return TransformationResponse(False, "", None, None, None, None, str(e))
        
        # Create transformation request
        request = TransformationRequest(
            source_egif=egif_content,
            rule_name=rule_name,
            target_area_description=target_area_description,
            operation_details=operation_details,
            description=description
        )
        
        # Apply transformation
        print(f"\n🎯 Applying {rule_name} transformation...")
        print(f"📍 Target area: {target_area_description}")
        print(f"⚙️  Operation: {description}")
        
        response = self.apply_transformation(request)
        
        # Display results
        if response.success:
            print(f"\n✅ Transformation successful!")
            print(f"🧮 Result EGIF: {response.result_egif}")
            
            if response.original_egi and response.result_egi:
                print(f"\n📊 EGI Changes:")
                print(f"   Vertices: {len(response.original_egi.V)} → {len(response.result_egi.V)}")
                print(f"   Edges: {len(response.original_egi.E)} → {len(response.result_egi.E)}")
                print(f"   Cuts: {len(response.original_egi.Cut)} → {len(response.result_egi.Cut)}")
                
                if response.transformation_details and response.transformation_details.changes_made:
                    print(f"   Changes: {response.transformation_details.changes_made}")
        else:
            print(f"\n❌ Transformation failed!")
            print(f"💥 Error: {response.error_message}")
        
        return response


def demonstrate_socrates_example():
    """Demonstrate the specific Socrates example from the user request."""
    
    interface = EGIFTransformationInterface()
    
    # The example from the user
    corpus_path = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.json"
    
    response = interface.demonstrate_transformation(
        corpus_path=corpus_path,
        rule_name="INS",
        target_area_description="second_negation",
        operation_details={
            "insert_content": '(Teacher "Socrates")'
        },
        description='Insert (Teacher "Socrates") inside the second negation'
    )
    
    return response


if __name__ == "__main__":
    print("🚀 EGIF Transformation Interface Demo")
    print("=" * 50)
    
    # Run the Socrates example
    result = demonstrate_socrates_example()
    
    if result.success:
        print(f"\n🎉 Demo completed successfully!")
        print(f"Original: {result.original_egif}")
        print(f"Result:   {result.result_egif}")
    else:
        print(f"\n⚠️  Demo encountered issues: {result.error_message}")
