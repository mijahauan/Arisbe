"""
Interactive EGIF Transformation Interface
Provides step-by-step guided transformation of existential graphs.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from egif_transformation_interface import EGIFTransformationInterface, TransformationRequest
from egi_core_dau import RelationalGraphWithCuts, ElementID


@dataclass
class GraphAnalysis:
    """Analysis of an EGI structure for interactive display."""
    egif: str
    vertex_count: int
    edge_count: int
    cut_count: int
    areas: Dict[str, Dict[str, Any]]
    elements: Dict[str, Dict[str, Any]]
    suggested_operations: List[Dict[str, str]]


class InteractiveEGIFTransformer:
    """Interactive interface for EGIF transformations with user guidance."""
    
    def __init__(self):
        self.interface = EGIFTransformationInterface()
        self.current_egif = None
        self.current_egi = None
        self.analysis = None
        self.corpus_files = self._discover_corpus_files()
    
    def _discover_corpus_files(self) -> List[Dict[str, str]]:
        """Discover available corpus EGIF files."""
        corpus_dir = Path("/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs")
        files = []
        
        if corpus_dir.exists():
            for graph_dir in corpus_dir.iterdir():
                if graph_dir.is_dir():
                    json_file = graph_dir / f"{graph_dir.name}.json"
                    if json_file.exists():
                        try:
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                            
                            egif_content = data.get("linear_forms", {}).get("egif", {}).get("content", "")
                            if egif_content:
                                files.append({
                                    "path": str(json_file),
                                    "id": data.get("id", graph_dir.name),
                                    "title": data.get("title", graph_dir.name),
                                    "description": data.get("description", "No description"),
                                    "egif": egif_content,
                                    "category": data.get("category", "unknown") or "unknown"
                                })
                        except Exception:
                            continue
        
        return sorted(files, key=lambda x: x["category"] + "_" + x["title"])
    
    def analyze_graph(self, egif: str) -> GraphAnalysis:
        """Analyze an EGIF and extract structural information."""
        try:
            egi = self.interface.parse_egif_to_egi(egif)
            # Store the EGI instance for later use
            self.current_egi = egi
            
            # Analyze areas and their properties
            areas = {}
            
            # Sheet area
            sheet_contents = egi.area.get(egi.sheet, frozenset())
            polarity, depth = self.interface._calculate_area_polarity(egi, egi.sheet)
            areas["sheet"] = {
                "id": str(egi.sheet),
                "type": "sheet",
                "polarity": polarity,
                "depth": depth,
                "element_count": len(sheet_contents),
                "description": "Main sheet of assertion (positive area)"
            }
            
            # Cut areas - sort by depth for consistent labeling
            cuts_with_depth = []
            for cut in egi.Cut:
                cut_contents = egi.area.get(cut.id, frozenset())
                polarity, depth = self.interface._calculate_area_polarity(egi, cut.id)
                cuts_with_depth.append((cut, polarity, depth, len(cut_contents)))
            
            # Sort by depth to ensure consistent ordering
            cuts_with_depth.sort(key=lambda x: x[2])  # Sort by depth
            
            for i, (cut, polarity, depth, element_count) in enumerate(cuts_with_depth):
                areas[f"cut_{i}"] = {
                    "id": str(cut.id),
                    "type": "cut",
                    "polarity": polarity,
                    "depth": depth,
                    "element_count": element_count,
                    "description": f"Cut area (depth {depth}, {polarity} polarity)"
                }
            
            # Analyze elements
            elements = {}
            
            # Vertices
            for i, vertex in enumerate(egi.V):
                elements[f"vertex_{i}"] = {
                    "id": str(vertex.id),
                    "type": "vertex",
                    "label": getattr(vertex, 'label', None),
                    "is_constant": hasattr(egi, 'rho') and vertex.id in egi.rho and egi.rho[vertex.id] is not None,
                    "constant_name": getattr(egi, 'rho', {}).get(vertex.id, None)
                }
            
            # Edges
            for i, edge in enumerate(egi.E):
                relation_name = egi.rel.get(edge.id, "unknown")
                vertex_sequence = egi.nu.get(edge.id, ())
                elements[f"edge_{i}"] = {
                    "id": str(edge.id),
                    "type": "edge",
                    "relation": relation_name,
                    "vertices": [str(vid) for vid in vertex_sequence],
                    "arity": len(vertex_sequence)
                }
            
            # Cuts (as erasable elements)
            for i, cut in enumerate(egi.Cut):
                cut_contents = egi.area.get(cut.id, frozenset())
                elements[f"cut_{i}"] = {
                    "id": str(cut.id),
                    "type": "cut",
                    "contents": list(cut_contents),
                    "content_count": len(cut_contents)
                }
            
            # Suggest possible operations
            suggestions = []
            
            # INS suggestions for negative areas
            negative_areas = [area for area in areas.values() if area["polarity"] == "negative"]
            if negative_areas:
                suggestions.append({
                    "rule": "INS",
                    "description": f"Insert content into {len(negative_areas)} negative area(s)",
                    "example": "Add new relations or vertices"
                })
            
            # ERA suggestions for positive areas with content
            positive_areas = [area for area in areas.values() if area["polarity"] == "positive" and area["element_count"] > 0]
            if positive_areas:
                suggestions.append({
                    "rule": "ERA",
                    "description": f"Erase content from {len(positive_areas)} positive area(s)",
                    "example": "Remove existing relations or vertices"
                })
            
            # DC+ always possible
            suggestions.append({
                "rule": "DC+",
                "description": "Insert double cut around any content",
                "example": "Add logical structure for negation"
            })
            
            # DC- if empty double cuts exist
            empty_cuts = [area for area in areas.values() if area["type"] == "cut" and area["element_count"] == 0]
            if len(empty_cuts) >= 2:
                suggestions.append({
                    "rule": "DC-",
                    "description": "Remove empty double cut patterns",
                    "example": "Simplify logical structure"
                })
            
            # IT+ if elements exist
            if len(elements) > 0:
                suggestions.append({
                    "rule": "IT+",
                    "description": "Iterate (copy) existing elements",
                    "example": "Duplicate vertices or relations"
                })
            
            return GraphAnalysis(
                egif=egif,
                vertex_count=len(egi.V),
                edge_count=len(egi.E),
                cut_count=len(egi.Cut),
                areas=areas,
                elements=elements,
                suggested_operations=suggestions
            )
            
        except Exception as e:
            raise ValueError(f"Could not analyze EGIF '{egif}': {e}")
    
    def display_graph_selection(self) -> None:
        """Display available graphs for selection."""
        print("🎯 Available Existential Graphs")
        print("=" * 40)
        
        categories = {}
        for file_info in self.corpus_files:
            category = file_info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(file_info)
        
        index = 1
        file_map = {}
        
        for category, files in categories.items():
            print(f"\n📂 {category.upper()}")
            print("-" * 20)
            
            for file_info in files:
                print(f"{index:2d}. {file_info['title']}")
                print(f"    {file_info['description']}")
                print(f"    EGIF: {file_info['egif']}")
                file_map[index] = file_info
                index += 1
        
        print(f"\n{index}. Enter custom EGIF")
        file_map[index] = {"custom": True}
        
        return file_map
    
    def display_analysis(self, analysis: GraphAnalysis) -> None:
        """Display comprehensive graph analysis."""
        print(f"\n📊 Graph Analysis")
        print("=" * 30)
        print(f"EGIF: {analysis.egif}")
        print(f"Structure: {analysis.vertex_count}V, {analysis.edge_count}E, {analysis.cut_count}C")
        
        # Display areas
        print(f"\n🏗️  Areas ({len(analysis.areas)}):")
        for area_name, area_info in analysis.areas.items():
            polarity_icon = "➕" if area_info["polarity"] == "positive" else "➖"
            print(f"   {polarity_icon} {area_name}: {area_info['description']} ({area_info['element_count']} elements)")
        
        # Display elements
        if analysis.elements:
            print(f"\n🔗 Elements ({len(analysis.elements)}):")
            for elem_name, elem_info in analysis.elements.items():
                if elem_info["type"] == "vertex":
                    if elem_info["is_constant"]:
                        print(f"   🔸 {elem_name}: Constant \"{elem_info['constant_name']}\"")
                    else:
                        print(f"   🔹 {elem_name}: Generic variable")
                elif elem_info["type"] == "edge":
                    print(f"   🔗 {elem_name}: {elem_info['relation']} (arity {elem_info['arity']})")
        
        # Display suggestions
        if analysis.suggested_operations:
            print(f"\n💡 Suggested Operations:")
            for i, suggestion in enumerate(analysis.suggested_operations, 1):
                print(f"   {i}. {suggestion['rule']}: {suggestion['description']}")
                print(f"      Example: {suggestion['example']}")
    
    def display_yaml_structure(self, analysis: GraphAnalysis) -> None:
        """Display graph structure in YAML format."""
        structure = {
            "egif": analysis.egif,
            "structure": {
                "vertices": analysis.vertex_count,
                "edges": analysis.edge_count,
                "cuts": analysis.cut_count
            },
            "areas": {},
            "elements": {}
        }
        
        # Add areas with user-friendly names
        for area_name, area_info in analysis.areas.items():
            friendly_name = area_name
            if area_info["type"] == "sheet":
                friendly_name = "sheet"
            elif area_info["type"] == "cut":
                if area_info["depth"] == 1:
                    friendly_name = f"first_negation"
                elif area_info["depth"] == 2:
                    friendly_name = f"second_negation"
                else:
                    friendly_name = f"cut_depth_{area_info['depth']}"
            
            structure["areas"][friendly_name] = {
                "id": area_info["id"],
                "polarity": area_info["polarity"],
                "depth": area_info["depth"],
                "elements": area_info["element_count"]
            }
        
        # Add elements
        for elem_name, elem_info in analysis.elements.items():
            structure["elements"][elem_name] = {
                "id": elem_info["id"],
                "type": elem_info["type"]
            }
            
            if elem_info["type"] == "vertex" and elem_info["is_constant"]:
                structure["elements"][elem_name]["constant"] = elem_info["constant_name"]
            elif elem_info["type"] == "edge":
                structure["elements"][elem_name]["relation"] = elem_info["relation"]
        
        print(f"\n📋 YAML Structure:")
        print(yaml.dump(structure, default_flow_style=False, sort_keys=False))
    
    def get_user_choice(self, prompt: str, options: Dict[int, Any], allow_custom: bool = False) -> Tuple[int, Any]:
        """Get user choice from numbered options."""
        while True:
            try:
                print(f"\n{prompt}")
                if allow_custom:
                    print("(Enter number or 'c' for custom)")
                
                choice = input("Choice: ").strip()
                
                if allow_custom and choice.lower() == 'c':
                    return -1, None
                
                choice_num = int(choice)
                if choice_num in options:
                    return choice_num, options[choice_num]
                else:
                    print(f"❌ Invalid choice. Please enter a number between {min(options.keys())} and {max(options.keys())}")
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                exit(0)
    
    def select_transformation_rule(self) -> str:
        """Let user select transformation rule."""
        rules = {
            1: ("DC+", "Double Cut Insertion - Add logical structure"),
            2: ("DC-", "Double Cut Erasure - Remove empty double cuts"),
            3: ("INS", "Insertion - Add content to negative areas"),
            4: ("ERA", "Erasure - Remove content from positive areas"),
            5: ("IT+", "Iteration - Copy/duplicate elements"),
            6: ("IT-", "Deiteration - Remove duplicate elements")
        }
        
        print(f"\n🔧 Select Transformation Rule:")
        for num, (rule, desc) in rules.items():
            print(f"   {num}. {rule}: {desc}")
        
        choice, (rule, _) = self.get_user_choice("Select rule:", rules)
        return rule
    
    def select_target_area(self, analysis: GraphAnalysis, rule: str) -> str:
        """Let user select target area based on rule requirements."""
        print(f"\n🎯 Select Target Area for {rule}:")
        
        # Filter areas based on rule requirements
        if rule == "INS":
            valid_areas = {name: info for name, info in analysis.areas.items() 
                          if info["polarity"] == "negative"}
            print("   (INS requires negative areas only)")
        elif rule == "ERA":
            valid_areas = {name: info for name, info in analysis.areas.items() 
                          if info["polarity"] == "positive" and info["element_count"] > 0}
            print("   (ERA requires positive areas with content)")
        else:
            valid_areas = analysis.areas
        
        if not valid_areas:
            if rule == "INS":
                raise ValueError("No negative areas available for insertion")
            elif rule == "ERA":
                raise ValueError("No positive areas with content available for erasure")
        
        area_options = {}
        for i, (area_name, area_info) in enumerate(valid_areas.items(), 1):
            polarity_icon = "➕" if area_info["polarity"] == "positive" else "➖"
            print(f"   {i}. {area_name}: {area_info['description']} {polarity_icon}")
            area_options[i] = area_name
        
        choice, area_name = self.get_user_choice("Select area:", area_options)
        return area_name
    
    def get_subgraph_specification(self, rule: str, analysis: GraphAnalysis, target_area: str = None) -> Dict[str, Any]:
        """Get subgraph specification from user based on rule."""
        if rule == "INS":
            print(f"\n📝 Specify content to insert:")
            print("   Examples:")
            print('   - (Teacher "Socrates")  # Add relation with constant')
            print('   - (Wise *x)            # Add relation with variable')
            print('   - "Plato"              # Add isolated constant')
            print('   - *y                   # Add isolated variable')
            
            content = input("Enter content to insert: ").strip()
            if not content:
                raise ValueError("Content cannot be empty")
            
            return {"insert_content": content}
        
        elif rule in ["ERA", "IT-"]:
            print(f"\n🎯 Select elements for {rule}:")
            
            if not analysis.elements:
                raise ValueError("No elements available for selection")
            
            # Filter elements by target area if specified
            available_elements = {}
            if target_area and target_area in analysis.areas:
                # Get the area ID to check element containment
                target_area_id = analysis.areas[target_area]["id"]
                
                # Use the same EGI instance that was used for analysis
                egi = self.current_egi
                area_contents = egi.area.get(target_area_id, frozenset())
                
                # Filter elements that are in the target area
                for elem_name, elem_info in analysis.elements.items():
                    elem_id = elem_info["id"]
                    if elem_id in area_contents:
                        available_elements[elem_name] = elem_info
            else:
                # No area filtering - show all elements
                available_elements = analysis.elements
            
            if not available_elements:
                print(f"   No elements found in the selected area.")
                return {"selected_elements": []}
            
            element_options = {}
            for i, (elem_name, elem_info) in enumerate(available_elements.items(), 1):
                if elem_info["type"] == "vertex":
                    if elem_info["is_constant"]:
                        desc = f"Constant \"{elem_info['constant_name']}\""
                    else:
                        desc = "Generic variable"
                    print(f"   {i}. {elem_name}: {desc}")
                elif elem_info["type"] == "edge":
                    print(f"   {i}. {elem_name}: {elem_info['relation']} relation")
                elif elem_info["type"] == "cut":
                    content_desc = f"({elem_info['content_count']} elements)" if elem_info['content_count'] > 0 else "(empty)"
                    print(f"   {i}. {elem_name}: Cut {content_desc}")
                
                element_options[i] = elem_info["id"]
            
            print("   (Enter comma-separated numbers for multiple elements)")
            selection = input("Select elements: ").strip()
            
            if not selection:
                return {"selected_elements": []}
            
            try:
                selected_nums = [int(x.strip()) for x in selection.split(",")]
                selected_elements = []
                
                for num in selected_nums:
                    if num in element_options:
                        elem_id = element_options[num]
                        selected_elements.append(elem_id)
                        
                        # For cuts, the transformation engine handles removing contents automatically
                
                return {"selected_elements": selected_elements}
            except ValueError:
                raise ValueError("Invalid element selection")
        
        elif rule == "IT+":
            # IT+ requires selecting elements from source area, then selecting destination area
            print(f"\n🎯 Select elements for {rule} (from source area):")
            
            if not analysis.elements:
                raise ValueError("No elements available for selection")
            
            # Filter elements by target area if specified
            available_elements = {}
            if target_area and target_area in analysis.areas:
                # Get the area ID to check element containment
                target_area_id = analysis.areas[target_area]["id"]
                
                # Use the same EGI instance that was used for analysis
                egi = self.current_egi
                area_contents = egi.area.get(target_area_id, frozenset())
                
                # Filter elements that are in the target area
                for elem_name, elem_info in analysis.elements.items():
                    elem_id = elem_info["id"]
                    if elem_id in area_contents:
                        available_elements[elem_name] = elem_info
            else:
                # No area filtering - show all elements
                available_elements = analysis.elements
            
            if not available_elements:
                print(f"   No elements found in the selected area.")
                return {"selected_elements": []}
            
            element_options = {}
            for i, (elem_name, elem_info) in enumerate(available_elements.items(), 1):
                if elem_info["type"] == "vertex":
                    if elem_info["is_constant"]:
                        desc = f"Constant \"{elem_info['constant_name']}\""
                    else:
                        desc = "Generic variable"
                    print(f"   {i}. {elem_name}: {desc}")
                elif elem_info["type"] == "edge":
                    print(f"   {i}. {elem_name}: {elem_info['relation']} relation")
                elif elem_info["type"] == "cut":
                    content_desc = f"({elem_info['content_count']} elements)" if elem_info['content_count'] > 0 else "(empty)"
                    print(f"   {i}. {elem_name}: Cut {content_desc}")
                
                element_options[i] = elem_info["id"]
            
            print("   (Enter comma-separated numbers for multiple elements)")
            selection = input("Select elements: ").strip()
            
            if not selection:
                return {"selected_elements": []}
            
            try:
                selected_nums = [int(x.strip()) for x in selection.split(",")]
                selected_elements = []
                
                for num in selected_nums:
                    if num in element_options:
                        elem_id = element_options[num]
                        selected_elements.append(elem_id)
                        
                        # For cuts, the transformation engine handles removing contents automatically
            except ValueError:
                raise ValueError("Invalid element selection")
            
            # Now select destination area for IT+
            print(f"\n🎯 Select destination area for iteration:")
            print("   (Must be the same area or an area nested within the source area)")
            
            # Get valid destination areas (same area or nested within source area)
            valid_destinations = self.get_valid_iteration_destinations(analysis, target_area)
            
            if not valid_destinations:
                print("   No valid destination areas available.")
                return {"selected_elements": selected_elements}
            
            dest_options = {}
            for i, (area_name, area_info) in enumerate(valid_destinations.items(), 1):
                polarity_symbol = "➕" if area_info["polarity"] == "positive" else "➖"
                print(f"   {i}. {area_name}: {area_info['description']} {polarity_symbol}")
                dest_options[i] = area_name
            
            dest_choice = input("Select destination area: ").strip()
            
            try:
                dest_num = int(dest_choice)
                if dest_num in dest_options:
                    destination_area = dest_options[dest_num]
                    destination_area_id = analysis.areas[destination_area]["id"]
                    return {
                        "selected_elements": selected_elements,
                        "destination_area": destination_area_id
                    }
                else:
                    raise ValueError("Invalid destination area selection")
            except ValueError:
                raise ValueError("Invalid destination area selection")
        
        elif rule == "DC+":
            print(f"\n🎯 Select elements to enclose in double cut:")
            print("   (Select elements to enclose, or leave empty for empty double cut)")
            
            if not analysis.elements:
                print("   No elements available - will create empty double cut")
                return {"selected_elements": []}
            
            # Filter elements by target area if specified
            available_elements = {}
            if target_area and target_area in analysis.areas:
                # Get the area ID to check element containment
                target_area_id = analysis.areas[target_area]["id"]
                
                # Use the same EGI instance that was used for analysis
                egi = self.current_egi
                area_contents = egi.area.get(target_area_id, frozenset())
                
                # Filter elements that are in the target area
                for elem_name, elem_info in analysis.elements.items():
                    elem_id = elem_info["id"]
                    if elem_id in area_contents:
                        available_elements[elem_name] = elem_info
            else:
                # No area filtering - show all elements
                available_elements = analysis.elements
            
            if not available_elements:
                print(f"   No elements found in the selected area - will create empty double cut")
                return {"selected_elements": []}
            
            element_options = {}
            for i, (elem_name, elem_info) in enumerate(available_elements.items(), 1):
                if elem_info["type"] == "vertex":
                    if elem_info["is_constant"]:
                        desc = f"Constant \"{elem_info['constant_name']}\""
                    else:
                        desc = "Generic variable"
                    print(f"   {i}. {elem_name}: {desc}")
                elif elem_info["type"] == "edge":
                    print(f"   {i}. {elem_name}: {elem_info['relation']} relation")
                elif elem_info["type"] == "cut":
                    content_desc = f"({elem_info['content_count']} elements)" if elem_info['content_count'] > 0 else "(empty)"
                    print(f"   {i}. {elem_name}: Cut {content_desc}")
                
                element_options[i] = elem_info["id"]
            
            print("   (Enter comma-separated numbers for multiple elements, or press Enter for empty double cut)")
            selection = input("Select elements to enclose: ").strip()
            
            if not selection:
                return {"selected_elements": []}
            
            try:
                selected_nums = [int(x.strip()) for x in selection.split(",")]
                selected_elements = []
                
                for num in selected_nums:
                    if num in element_options:
                        elem_id = element_options[num]
                        selected_elements.append(elem_id)
                        
                        # For cuts, the transformation engine handles removing contents automatically
                
                return {"selected_elements": selected_elements}
            except ValueError:
                raise ValueError("Invalid element selection")
        
        else:  # DC-
            # For DC-, identify potential double cuts in the target area
            target_area_id = analysis.areas[target_area]["id"]
            egi = self.current_egi
            area_contents = egi.area.get(target_area_id, frozenset())
            
            # Find cuts in this area that could be outer cuts of double cut patterns
            potential_double_cuts = []
            element_options = {}
            
            for i, elem_id in enumerate(area_contents, 1):
                if elem_id in egi._cut_map:
                    # Check if this cut contains only another cut
                    cut_contents = egi.area.get(elem_id, frozenset())
                    if len(cut_contents) == 1:
                        inner_elem = next(iter(cut_contents))
                        if inner_elem in egi._cut_map:
                            potential_double_cuts.append((i, elem_id))
                            element_options[i] = elem_id
                            print(f"   {i}. Double cut pattern (outer cut {elem_id})")
            
            if not potential_double_cuts:
                return {"selected_elements": [], "error": "No double cut patterns found in selected area"}
            
            if len(potential_double_cuts) == 1:
                # Only one double cut pattern, select it automatically
                selected_cut = element_options[potential_double_cuts[0][0]]
                print(f"✅ Automatically selected double cut: {selected_cut}")
                return {"selected_elements": [selected_cut]}
            else:
                # Multiple double cut patterns, let user choose
                print("🎯 Select double cut pattern to remove:")
                selection = input("Select double cut: ").strip()
                
                try:
                    selected_num = int(selection)
                    if selected_num in element_options:
                        return {"selected_elements": [element_options[selected_num]]}
                    else:
                        raise ValueError("Invalid selection")
                except ValueError:
                    raise ValueError("Invalid double cut selection")
    
    def get_valid_iteration_destinations(self, analysis: GraphAnalysis, source_area: str) -> Dict[str, Any]:
        """Get valid destination areas for IT+ operation."""
        valid_destinations = {}
        
        # Source area is always valid
        if source_area in analysis.areas:
            valid_destinations[source_area] = analysis.areas[source_area]
        
        # Find areas nested within the source area
        source_area_id = analysis.areas[source_area]["id"]
        egi = self.current_egi
        
        # Check each area to see if it's nested within the source area
        for area_name, area_info in analysis.areas.items():
            if area_name == source_area:
                continue  # Already added
                
            area_id = area_info["id"]
            
            # Check if this area is nested within the source area
            if self.is_area_nested_within(egi, area_id, source_area_id):
                valid_destinations[area_name] = area_info
        
        return valid_destinations
    
    def is_area_nested_within(self, egi: RelationalGraphWithCuts, child_area_id: ElementID, parent_area_id: ElementID) -> bool:
        """Check if child_area is nested within parent_area."""
        current_area = child_area_id
        
        while True:
            # Find the area that contains the current area
            containing_area = None
            for area_candidate, contents in egi.area.items():
                if current_area in contents:
                    containing_area = area_candidate
                    break
            
            if containing_area is None:
                return False
            
            if containing_area == parent_area_id:
                return True
            
            if containing_area == egi.sheet:
                return False
            
            current_area = containing_area
    
    def run_interactive_session(self) -> None:
        """Run the main interactive transformation session."""
        print("🎮 Interactive EGIF Transformer")
        print("=" * 35)
        print("Transform existential graphs step-by-step with guided assistance.")
        
        try:
            # Step 1: Select starting graph
            file_map = self.display_graph_selection()
            choice, selected = self.get_user_choice("Select starting graph:", file_map)
            
            if selected.get("custom"):
                egif = input("\nEnter custom EGIF: ").strip()
                if not egif:
                    print("❌ EGIF cannot be empty")
                    return
            else:
                egif = selected["egif"]
                print(f"\n✅ Selected: {selected['title']}")
            
            # Step 2: Analyze and display graph
            self.current_egif = egif
            self.analysis = self.analyze_graph(egif)
            self.display_analysis(self.analysis)
            self.display_yaml_structure(self.analysis)
            
            # Step 3: Select transformation rule
            rule = self.select_transformation_rule()
            print(f"\n✅ Selected rule: {rule}")
            
            # Step 4: Select target area
            target_area = self.select_target_area(self.analysis, rule)
            print(f"✅ Selected area: {target_area}")
            
            # Step 5: Specify subgraph
            operation_details = self.get_subgraph_specification(rule, self.analysis, target_area)
            print(f"✅ Operation details: {operation_details}")
            
            # Step 6: Perform transformation
            print(f"\n🔄 Applying {rule} transformation...")
            
            # Convert area name to actual area ID from the same EGI instance
            target_area_id = self.analysis.areas[target_area]["id"]
            
            # Create a custom transformation interface that uses our existing EGI
            request = TransformationRequest(
                source_egif=self.current_egif,
                rule_name=rule,
                target_area_description=target_area_id,
                operation_details=operation_details,
                description=f"Interactive {rule} operation"
            )
            
            # Pass the current EGI instance to maintain consistent area IDs
            response = self.interface.apply_transformation(request, existing_egi=self.current_egi)
            
            if response.success:
                print("✓ Transformation applied successfully!")
                print(f"Result EGIF:\n{response.result_egif}")
                
                # Optionally save result
                save = input("\nSave result to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("Enter filename (without extension): ").strip()
                    if filename:
                        filepath = f"transformed_{filename}.egif"
                        with open(filepath, 'w') as f:
                            f.write(response.result_egif)
                        print(f"✓ Saved to {filepath}")
                
                # Option to continue transforming the result
                continue_choice = input("\nContinue transforming this result? (y/n): ").strip().lower()
                if continue_choice == 'y':
                    # Update current EGI to the transformed result and continue
                    self.current_egi = response.result_egi
                    self.current_egif = response.result_egif
                    print(f"\n🔄 Continuing with transformed graph...")
                    self.continue_transformation_session()
            else:
                print(f"✗ Transformation failed: {response.error_message}")
                
                retry_choice = input("\nTry again? (y/n): ").strip().lower()
                if retry_choice == 'y':
                    self.continue_transformation_session()
        
        except KeyboardInterrupt:
            print("\n👋 Session ended by user")
        except Exception as e:
            print(f"\n💥 Error: {e}")
            retry_choice = input("\nTry again? (y/n): ").strip().lower()
            if retry_choice == 'y':
                self.run_interactive_session()
    
    def continue_transformation_session(self) -> None:
        """Continue transformation session with the current EGIF."""
        try:
            # Step 1: Analyze and display current graph
            self.analysis = self.analyze_graph(self.current_egif)
            self.display_analysis(self.analysis)
            self.display_yaml_structure(self.analysis)
            
            # Step 2: Select transformation rule
            rule = self.select_transformation_rule()
            print(f"\n✅ Selected rule: {rule}")
            
            # Step 3: Select target area
            target_area = self.select_target_area(self.analysis, rule)
            print(f"✅ Selected area: {target_area}")
            
            # Step 4: Specify subgraph
            operation_details = self.get_subgraph_specification(rule, self.analysis, target_area)
            print(f"✅ Operation details: {operation_details}")
            
            # Step 5: Perform transformation
            print(f"\n🔄 Applying {rule} transformation...")
            
            # Convert area name to actual area ID from the same EGI instance
            target_area_id = self.analysis.areas[target_area]["id"]
            
            # Create a custom transformation interface that uses our existing EGI
            request = TransformationRequest(
                source_egif=self.current_egif,
                rule_name=rule,
                target_area_description=target_area_id,
                operation_details=operation_details,
                description=f"Apply {rule} transformation"
            )
            
            response = self.interface.apply_transformation(request, existing_egi=self.current_egi)
            
            if response.success:
                print("✓ Transformation applied successfully!")
                print(f"Result EGIF:\n{response.result_egif}")
                
                # Optionally save result
                save = input("\nSave result to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("Enter filename (without extension): ").strip()
                    if filename:
                        filepath = f"transformed_{filename}.egif"
                        with open(filepath, 'w') as f:
                            f.write(response.result_egif)
                        print(f"✓ Saved to {filepath}")
                
                # Option to continue transforming the result
                continue_choice = input("\nContinue transforming this result? (y/n): ").strip().lower()
                if continue_choice == 'y':
                    # Update current EGI to the transformed result and continue
                    self.current_egi = response.result_egi
                    self.current_egif = response.result_egif
                    print(f"\n🔄 Continuing with transformed graph...")
                    self.continue_transformation_session()
            else:
                print(f"✗ Transformation failed: {response.error_message}")
                
                retry_choice = input("\nTry again? (y/n): ").strip().lower()
                if retry_choice == 'y':
                    self.continue_transformation_session()
        
        except KeyboardInterrupt:
            print("\n👋 Session ended by user")
        except Exception as e:
            print(f"\n💥 Error: {e}")
            retry_choice = input("\nTry again? (y/n): ").strip().lower()
            if retry_choice == 'y':
                self.continue_transformation_session()


def main():
    """Main entry point for interactive EGIF transformer."""
    transformer = InteractiveEGIFTransformer()
    transformer.run_interactive_session()


if __name__ == "__main__":
    main()
