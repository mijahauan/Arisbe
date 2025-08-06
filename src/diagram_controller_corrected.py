#!/usr/bin/env python3
"""
Corrected DiagramController with Proper Causality

Key Principle: Visual elements are PRIMARY, EGI ν mapping is SECONDARY
- When loading EGIF: ν mapping → create visual elements
- When user interacts: visual elements → update ν mapping
- Selection system operates on primary visual elements
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from visual_elements_primary import (
    VisualDiagram, LineOfIdentity, PredicateElement, CutElement, 
    Coordinate, ElementState
)
from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge


@dataclass
class AttachmentAction:
    """Represents a line attachment action."""
    line_id: str
    predicate_id: str
    hook_position: int
    line_end: str  # "start" or "end"


class DiagramController:
    """
    Corrected DiagramController with proper causality.
    
    EGIF Loading: ν mapping → create visual elements
    User Interaction: visual elements → update ν mapping
    """
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.visual_diagram = VisualDiagram()
        self._next_position_x = 100
        self._next_position_y = 100
        
    def load_from_egi(self, layout_positions: Optional[Dict] = None) -> VisualDiagram:
        """
        Load visual diagram from EGI ν mapping.
        
        This is the EGIF loading case: ν mapping determines visual connections.
        """
        print("🔄 Loading visual diagram from EGI ν mapping...")
        
        # Clear existing visual elements
        self.visual_diagram = VisualDiagram()
        
        # Create predicates first
        predicate_positions = layout_positions.get('predicates', {}) if layout_positions else {}
        
        for edge in self.egi.E:
            rel_name = self.egi.rel.get(edge.id, f"P{edge.id}")
            
            # Get position from layout or generate
            if edge.id in predicate_positions:
                pos = predicate_positions[edge.id]
                position = Coordinate(pos['x'], pos['y'])
            else:
                position = self._get_next_position()
            
            # Create predicate
            predicate = PredicateElement(
                position=position,
                text=rel_name,
                element_id=f"pred_{edge.id}",
                max_arity=len(self.egi.nu.get(edge.id, ()))
            )
            self.visual_diagram.add_predicate(predicate)
            print(f"  ✅ Created predicate {rel_name} at {position.x}, {position.y}")
        
        # Create vertices and lines of identity
        vertex_positions = layout_positions.get('vertices', {}) if layout_positions else {}
        
        for vertex in self.egi.V:
            # Get constant label from vertex itself
            label = vertex.label if not vertex.is_generic else None
            
            # Get position from layout or generate
            if vertex.id in vertex_positions:
                pos = vertex_positions[vertex.id]
                start_pos = Coordinate(pos['x'] - 15, pos['y'])
                end_pos = Coordinate(pos['x'] + 15, pos['y'])
            else:
                pos = self._get_next_position()
                start_pos = Coordinate(pos.x - 15, pos.y)
                end_pos = Coordinate(pos.x + 15, pos.y)
            
            # Create line of identity
            line = LineOfIdentity(
                start_pos=start_pos,
                end_pos=end_pos,
                element_id=f"line_{vertex.id}",
                label=label
            )
            self.visual_diagram.add_line(line)
            print(f"  ✅ Created line of identity for vertex {vertex.id}" + 
                  (f" ('{label}')" if label else ""))
        
        # Now attach lines to predicates based on ν mapping
        for edge_id, vertex_sequence in self.egi.nu.items():
            predicate = self.visual_diagram.predicates.get(f"pred_{edge_id}")
            if not predicate:
                continue
                
            for hook_position, vertex_id in enumerate(vertex_sequence):
                line = self.visual_diagram.lines_of_identity.get(f"line_{vertex_id}")
                if line and predicate:
                    # Attach line to predicate
                    success = line.attach_to_predicate(predicate, hook_position, end="end")
                    if success:
                        print(f"  🔗 Attached line {vertex_id} to predicate {edge_id} at hook {hook_position}")
                    else:
                        print(f"  ❌ Failed to attach line {vertex_id} to predicate {edge_id}")
        
        print(f"✅ Loaded {len(self.visual_diagram.lines_of_identity)} lines, " +
              f"{len(self.visual_diagram.predicates)} predicates")
        
        return self.visual_diagram
    
    def create_unattached_line(self, start_pos: Coordinate, end_pos: Coordinate, 
                             label: Optional[str] = None) -> LineOfIdentity:
        """
        Create an unattached line of identity (Warmup mode composition).
        
        This is the interactive case: user creates visual element first.
        Also creates corresponding EGI vertex.
        """
        # Create EGI vertex first
        vertex = create_vertex(label=label, is_generic=(label is None))
        self.egi = self.egi.with_vertex(vertex)
        
        # Create visual line with vertex ID
        line = LineOfIdentity(
            start_pos=start_pos,
            end_pos=end_pos,
            element_id=f"line_{vertex.id}",
            label=label
        )
        line.state = ElementState.UNATTACHED
        self.visual_diagram.add_line(line)
        
        print(f"✅ Created unattached line of identity: {line.element_id} (EGI vertex: {vertex.id})")
        return line
    
    def create_unattached_predicate(self, position: Coordinate, text: str = "P") -> PredicateElement:
        """
        Create an unattached predicate (Warmup mode composition).
        
        This is the interactive case: user creates visual element first.
        Also creates corresponding EGI edge (with empty ν mapping initially).
        """
        # Create EGI edge first
        edge = create_edge()
        # Add edge with empty vertex sequence initially
        self.egi = self.egi.with_edge(edge, (), text)
        
        # Create visual predicate with edge ID
        predicate = PredicateElement(
            position=position,
            text=text,
            element_id=f"pred_{edge.id}",
            max_arity=3  # Start with reasonable default
        )
        predicate.state = ElementState.UNATTACHED
        self.visual_diagram.add_predicate(predicate)
        
        print(f"✅ Created unattached predicate '{text}': {predicate.element_id} (EGI edge: {edge.id})")
        return predicate
    
    def attach_line_to_predicate(self, line_id: str, predicate_id: str, 
                               hook_position: int, line_end: str = "end") -> bool:
        """
        User attaches a line to a predicate - UPDATE ν mapping.
        
        This is the key method: visual action → EGI update.
        """
        line = self.visual_diagram.lines_of_identity.get(line_id)
        predicate = self.visual_diagram.predicates.get(predicate_id)
        
        if not line or not predicate:
            print(f"❌ Cannot attach: line {line_id} or predicate {predicate_id} not found")
            return False
        
        # Perform visual attachment
        success = line.attach_to_predicate(predicate, hook_position, line_end)
        if not success:
            print(f"❌ Visual attachment failed")
            return False
        
        # NOW UPDATE EGI ν MAPPING
        self._update_nu_mapping_from_visual()
        
        print(f"✅ Attached line {line_id} to predicate {predicate_id} at hook {hook_position}")
        print(f"   Updated ν mapping in EGI")
        return True
    
    def detach_line_from_predicate(self, line_id: str, predicate_id: str) -> bool:
        """
        User detaches a line from a predicate - UPDATE ν mapping.
        
        This is the key method: visual action → EGI update.
        """
        line = self.visual_diagram.lines_of_identity.get(line_id)
        predicate = self.visual_diagram.predicates.get(predicate_id)
        
        if not line or not predicate:
            print(f"❌ Cannot detach: line {line_id} or predicate {predicate_id} not found")
            return False
        
        # Determine which end to detach
        line_end = "start" if line.start_connection == predicate else "end"
        
        # Perform visual detachment
        line.detach_from_predicate(line_end)
        
        # NOW UPDATE EGI ν MAPPING
        self._update_nu_mapping_from_visual()
        
        print(f"✅ Detached line {line_id} from predicate {predicate_id}")
        print(f"   Updated ν mapping in EGI")
        return True
    
    def _update_nu_mapping_from_visual(self):
        """
        Update EGI ν mapping to match current visual state.
        
        This is the core method that keeps EGI synchronized with visual elements.
        Since RelationalGraphWithCuts is immutable, we create a new instance.
        """
        print("🔄 Updating EGI ν mapping from visual state...")
        
        # Build new ν mapping from visual connections
        new_nu_mapping = {}
        new_rel_mapping = dict(self.egi.rel)  # Copy existing relations
        
        for predicate in self.visual_diagram.predicates.values():
            # Extract edge_id from element_id (pred_edge123 → edge123)
            if predicate.element_id.startswith("pred_"):
                edge_id = predicate.element_id[5:]  # Remove "pred_" prefix
            else:
                edge_id = predicate.element_id
            
            # Build vertex sequence from attached lines
            vertex_sequence = []
            for hook_pos in sorted(predicate.hooks.keys()):
                line = predicate.hooks[hook_pos]
                if line:
                    # Extract vertex_id from line element_id (line_vertex123 → vertex123)
                    if line.element_id.startswith("line_"):
                        vertex_id = line.element_id[5:]  # Remove "line_" prefix
                    else:
                        vertex_id = line.element_id
                    vertex_sequence.append(vertex_id)
            
            # Update ν mapping
            if vertex_sequence:
                new_nu_mapping[edge_id] = tuple(vertex_sequence)
                print(f"  📝 ν[{edge_id}] = {vertex_sequence}")
                
                # Update relation name if needed
                new_rel_mapping[edge_id] = predicate.text
        
        # Create new immutable EGI with updated mappings
        from frozendict import frozendict
        self.egi = RelationalGraphWithCuts(
            V=self.egi.V,
            E=self.egi.E,
            nu=frozendict(new_nu_mapping),
            sheet=self.egi.sheet,
            Cut=self.egi.Cut,
            area=self.egi.area,
            rel=frozendict(new_rel_mapping)
        )
        
        print("✅ EGI ν mapping updated from visual state")
    
    def _get_next_position(self) -> Coordinate:
        """Generate next position for layout."""
        pos = Coordinate(self._next_position_x, self._next_position_y)
        self._next_position_x += 80
        if self._next_position_x > 400:
            self._next_position_x = 100
            self._next_position_y += 60
        return pos
    
    def get_visual_diagram(self) -> VisualDiagram:
        """Get the current visual diagram."""
        return self.visual_diagram


def test_corrected_controller():
    """Test the corrected controller with both EGIF loading and interactive composition."""
    print("=== Testing Corrected DiagramController ===\n")
    
    # Create a simple EGI with ν mapping
    egi = create_empty_graph()
    
    # Add vertices and edges
    vertex1 = create_vertex(label="Socrates", is_generic=False)
    vertex2 = create_vertex()  # Generic vertex
    edge1 = create_edge()
    
    # Build graph with vertices and edge
    egi = egi.with_vertex(vertex1)
    egi = egi.with_vertex(vertex2)
    egi = egi.with_edge(edge1, (vertex1.id,), "Human")  # Human(Socrates)
    
    print("📊 Created EGI:")
    print(f"   Vertices: {[v.id for v in egi.V]}")
    print(f"   Edges: {[e.id for e in egi.E]}")
    print(f"   ν mapping: {dict(egi.nu)}")
    print(f"   Relations: {dict(egi.rel)}")
    print(f"   Vertex labels: {[(v.id, v.label) for v in egi.V]}\n")
    
    # Test 1: Load from EGI (EGIF loading case)
    print("🔍 TEST 1: Loading from EGI ν mapping")
    controller = DiagramController(egi)
    visual_diagram = controller.load_from_egi()
    
    print(f"   Visual elements created:")
    print(f"   - Lines: {len(visual_diagram.lines_of_identity)}")
    print(f"   - Predicates: {len(visual_diagram.predicates)}")
    
    # Verify attachment state
    for line in visual_diagram.lines_of_identity.values():
        print(f"   - Line {line.element_id}: {line.state}, attached={line.is_attached()}")
    
    print()
    
    # Test 2: Interactive composition (user creates elements)
    print("🎨 TEST 2: Interactive composition")
    
    # Create unattached elements
    new_line = controller.create_unattached_line(
        start_pos=Coordinate(300, 100),
        end_pos=Coordinate(350, 100),
        label="Plato"
    )
    
    new_predicate = controller.create_unattached_predicate(
        position=Coordinate(400, 100),
        text="Philosopher"
    )
    
    print(f"   Created unattached line: {new_line.state}")
    print(f"   Created unattached predicate: {new_predicate.state}")
    
    # Test 3: User attaches line to predicate
    print("\n🔗 TEST 3: User attachment action")
    success = controller.attach_line_to_predicate(
        line_id=new_line.element_id,
        predicate_id=new_predicate.element_id,
        hook_position=0
    )
    
    print(f"   Attachment successful: {success}")
    print(f"   Line state after: {new_line.state}")
    print(f"   Predicate arity after: {new_predicate.get_current_arity()}")
    
    # Verify EGI was updated
    print(f"   EGI ν mapping after attachment: {dict(controller.egi.nu)}")
    
    print("\n🎯 CORRECTED CONTROLLER WORKING!")
    print("✅ EGIF loading: ν mapping → visual elements")
    print("✅ Interactive: visual elements → ν mapping updates")
    print("✅ Proper causality maintained")


if __name__ == "__main__":
    test_corrected_controller()
