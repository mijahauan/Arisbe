#!/usr/bin/env python3
"""
Primary Visual Elements for Existential Graph Diagrams

These are the first-class visual objects that users see and select.
They drive EGI updates through DiagramController, not the other way around.

Key Principle: Visual elements are PRIMARY, EGI ν mapping is SECONDARY
- User actions create/modify visual elements
- DiagramController updates EGI ν mapping to match visual state
- Selection system operates on these primary visual elements
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
import uuid


class ElementState(Enum):
    """State of a visual element."""
    UNATTACHED = "unattached"  # Not connected to anything (Warmup mode)
    ATTACHED = "attached"      # Connected to other elements
    SELECTED = "selected"      # Currently selected by user


@dataclass
class VisualStyle:
    """Visual styling for elements."""
    line_width: float = 1.0
    line_color: Tuple[int, int, int] = (0, 0, 0)  # RGB
    fill_color: Optional[Tuple[int, int, int]] = None
    font_size: int = 12
    font_family: str = "Arial"


@dataclass
class Coordinate:
    """2D coordinate."""
    x: float
    y: float
    
    def __iter__(self):
        return iter((self.x, self.y))
    
    def __getitem__(self, index):
        return (self.x, self.y)[index]


class VisualElement:
    """Base class for all primary visual elements."""
    
    def __init__(self, element_id: Optional[str] = None):
        self.element_id = element_id or f"elem_{uuid.uuid4().hex[:8]}"
        self.state = ElementState.UNATTACHED
        self.selected = False
        self.area_id = "sheet"  # Which cut/area this element belongs to
        
    def select(self):
        """Mark this element as selected."""
        self.selected = True
        self.state = ElementState.SELECTED
        
    def deselect(self):
        """Mark this element as not selected."""
        self.selected = False
        if self.state == ElementState.SELECTED:
            self.state = ElementState.ATTACHED if self.is_attached() else ElementState.UNATTACHED
    
    def is_attached(self) -> bool:
        """Override in subclasses to determine attachment state."""
        return False


class LineOfIdentity(VisualElement):
    """
    Primary visual element: Heavy line of identity.
    
    This is what users see and select. It can be:
    - Unattached (free-floating in Warmup mode)
    - Attached to predicates at one or both ends
    - Part of a ligature (connected to other lines)
    """
    
    def __init__(self, start_pos: Coordinate, end_pos: Coordinate, 
                 element_id: Optional[str] = None, label: Optional[str] = None):
        super().__init__(element_id)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.label = label  # Constant name like "Socrates"
        self.label_position = 0.5  # Position along line (0.0 = start, 1.0 = end)
        
        # Connection state
        self.start_connection: Optional['PredicateElement'] = None
        self.end_connection: Optional['PredicateElement'] = None
        self.start_hook_position: Optional[int] = None  # Which hook on predicate
        self.end_hook_position: Optional[int] = None
        
        # Visual properties
        self.style = VisualStyle(
            line_width=4.0,  # Heavy line per Dau
            line_color=(0, 0, 0)
        )
    
    def is_attached(self) -> bool:
        """Line is attached if either end connects to a predicate."""
        return self.start_connection is not None or self.end_connection is not None
    
    def attach_to_predicate(self, predicate: 'PredicateElement', hook_position: int, 
                          end: str = "start") -> bool:
        """Attach this line to a predicate at specified hook position."""
        if end == "start":
            if predicate.can_attach_at_hook(hook_position):
                self.start_connection = predicate
                self.start_hook_position = hook_position
                predicate.attach_line(self, hook_position)
                self.state = ElementState.ATTACHED
                return True
        elif end == "end":
            if predicate.can_attach_at_hook(hook_position):
                self.end_connection = predicate
                self.end_hook_position = hook_position
                predicate.attach_line(self, hook_position)
                self.state = ElementState.ATTACHED
                return True
        return False
    
    def detach_from_predicate(self, end: str = "start"):
        """Detach this line from a predicate."""
        if end == "start" and self.start_connection:
            self.start_connection.detach_line(self, self.start_hook_position)
            self.start_connection = None
            self.start_hook_position = None
        elif end == "end" and self.end_connection:
            self.end_connection.detach_line(self, self.end_hook_position)
            self.end_connection = None
            self.end_hook_position = None
        
        # Update state
        if not self.is_attached():
            self.state = ElementState.UNATTACHED
    
    def get_label_coordinate(self) -> Coordinate:
        """Calculate where to place the label along the line."""
        x = self.start_pos.x + self.label_position * (self.end_pos.x - self.start_pos.x)
        y = self.start_pos.y + self.label_position * (self.end_pos.y - self.start_pos.y)
        return Coordinate(x, y)
    
    def move(self, new_start: Coordinate, new_end: Coordinate):
        """Move this line to new positions."""
        self.start_pos = new_start
        self.end_pos = new_end


class PredicateElement(VisualElement):
    """
    Primary visual element: Predicate with text and invisible hook boundary.
    
    This is what users see and select. It has:
    - Text (relation name)
    - Invisible boundary with hook positions
    - Can start as arity 0 (unattached) in Warmup mode
    """
    
    def __init__(self, position: Coordinate, text: str = "P", 
                 element_id: Optional[str] = None, max_arity: int = 3):
        super().__init__(element_id)
        self.position = position
        self.text = text
        self.max_arity = max_arity
        
        # Hook management
        self.hooks: Dict[int, Optional[LineOfIdentity]] = {}  # hook_position -> line
        for i in range(max_arity):
            self.hooks[i] = None
        
        # Visual properties
        self.style = VisualStyle(
            font_size=12,
            font_family="Arial",
            line_color=(0, 0, 0)
        )
        
        # Boundary for hook positions (invisible)
        self.boundary_radius = 20.0  # Distance from center to hook positions
    
    def get_current_arity(self) -> int:
        """Get current arity based on attached lines."""
        return sum(1 for line in self.hooks.values() if line is not None)
    
    def can_attach_at_hook(self, hook_position: int) -> bool:
        """Check if a line can attach at the specified hook position."""
        return (0 <= hook_position < self.max_arity and 
                self.hooks[hook_position] is None)
    
    def attach_line(self, line: LineOfIdentity, hook_position: int) -> bool:
        """Attach a line to this predicate at specified hook."""
        if self.can_attach_at_hook(hook_position):
            self.hooks[hook_position] = line
            self.state = ElementState.ATTACHED
            return True
        return False
    
    def detach_line(self, line: LineOfIdentity, hook_position: Optional[int] = None):
        """Detach a line from this predicate."""
        if hook_position is not None:
            if self.hooks.get(hook_position) == line:
                self.hooks[hook_position] = None
        else:
            # Find and remove the line
            for pos, attached_line in self.hooks.items():
                if attached_line == line:
                    self.hooks[pos] = None
                    break
        
        # Update state
        if self.get_current_arity() == 0:
            self.state = ElementState.UNATTACHED
    
    def get_hook_coordinate(self, hook_position: int) -> Coordinate:
        """Calculate the coordinate for a hook position on the boundary."""
        if hook_position >= self.max_arity:
            hook_position = 0
        
        # Distribute hooks evenly around the boundary
        angle = (2 * 3.14159 * hook_position) / self.max_arity
        x = self.position.x + self.boundary_radius * (0.8 * (angle / 3.14159))  # Simplified
        y = self.position.y + self.boundary_radius * 0.3 * (1 if hook_position % 2 == 0 else -1)
        return Coordinate(x, y)
    
    def is_attached(self) -> bool:
        """Predicate is attached if any lines are connected."""
        return self.get_current_arity() > 0
    
    def move(self, new_position: Coordinate):
        """Move this predicate to a new position."""
        self.position = new_position


class CutElement(VisualElement):
    """
    Primary visual element: Cut boundary (fine-drawn closed curve).
    """
    
    def __init__(self, bounds: Tuple[float, float, float, float], 
                 element_id: Optional[str] = None):
        super().__init__(element_id)
        self.bounds = bounds  # (x1, y1, x2, y2)
        self.style = VisualStyle(
            line_width=1.0,  # Fine line per Dau
            line_color=(0, 0, 0)
        )
    
    def contains_point(self, point: Coordinate) -> bool:
        """Check if a point is inside this cut."""
        x1, y1, x2, y2 = self.bounds
        return x1 <= point.x <= x2 and y1 <= point.y <= y2
    
    def move(self, new_bounds: Tuple[float, float, float, float]):
        """Move/resize this cut."""
        self.bounds = new_bounds


class VisualDiagram:
    """
    Container for all primary visual elements.
    
    This is what the Selection system operates on.
    DiagramController keeps EGI ν mapping synchronized with this visual state.
    """
    
    def __init__(self):
        self.lines_of_identity: Dict[str, LineOfIdentity] = {}
        self.predicates: Dict[str, PredicateElement] = {}
        self.cuts: Dict[str, CutElement] = {}
        
    def add_line(self, line: LineOfIdentity):
        """Add a line of identity to the diagram."""
        self.lines_of_identity[line.element_id] = line
    
    def add_predicate(self, predicate: PredicateElement):
        """Add a predicate to the diagram."""
        self.predicates[predicate.element_id] = predicate
    
    def add_cut(self, cut: CutElement):
        """Add a cut to the diagram."""
        self.cuts[cut.element_id] = cut
    
    def remove_element(self, element_id: str):
        """Remove an element from the diagram."""
        if element_id in self.lines_of_identity:
            line = self.lines_of_identity[element_id]
            # Detach from any connected predicates
            line.detach_from_predicate("start")
            line.detach_from_predicate("end")
            del self.lines_of_identity[element_id]
        elif element_id in self.predicates:
            predicate = self.predicates[element_id]
            # Detach all connected lines
            for hook_pos, line in predicate.hooks.items():
                if line:
                    line.detach_from_predicate("start" if line.start_connection == predicate else "end")
            del self.predicates[element_id]
        elif element_id in self.cuts:
            del self.cuts[element_id]
    
    def get_element(self, element_id: str) -> Optional[VisualElement]:
        """Get any element by ID."""
        if element_id in self.lines_of_identity:
            return self.lines_of_identity[element_id]
        elif element_id in self.predicates:
            return self.predicates[element_id]
        elif element_id in self.cuts:
            return self.cuts[element_id]
        return None
    
    def get_all_elements(self) -> List[VisualElement]:
        """Get all elements in the diagram."""
        elements = []
        elements.extend(self.lines_of_identity.values())
        elements.extend(self.predicates.values())
        elements.extend(self.cuts.values())
        return elements
    
    def get_selected_elements(self) -> List[VisualElement]:
        """Get all currently selected elements."""
        return [elem for elem in self.get_all_elements() if elem.selected]


if __name__ == "__main__":
    print("=== Testing Primary Visual Elements ===")
    
    # Create a simple diagram
    diagram = VisualDiagram()
    
    # Create a line of identity
    line = LineOfIdentity(
        start_pos=Coordinate(100, 200),
        end_pos=Coordinate(200, 200),
        label="Socrates"
    )
    diagram.add_line(line)
    print(f"✅ Created line of identity: {line.element_id}")
    print(f"   Label position: {line.get_label_coordinate().x}, {line.get_label_coordinate().y}")
    
    # Create a predicate
    predicate = PredicateElement(
        position=Coordinate(250, 200),
        text="Human"
    )
    diagram.add_predicate(predicate)
    print(f"✅ Created predicate: {predicate.element_id}")
    print(f"   Current arity: {predicate.get_current_arity()}")
    
    # Attach line to predicate
    success = line.attach_to_predicate(predicate, hook_position=0, end="end")
    print(f"✅ Attached line to predicate: {success}")
    print(f"   Line state: {line.state}")
    print(f"   Predicate arity: {predicate.get_current_arity()}")
    
    # Test selection
    line.select()
    selected = diagram.get_selected_elements()
    print(f"✅ Selected elements: {len(selected)}")
    
    print("\n🎯 PRIMARY VISUAL ELEMENTS WORKING!")
    print("✅ Lines of identity are primary selectable objects")
    print("✅ Predicates have invisible hook boundaries")
    print("✅ Attachment updates both line and predicate state")
    print("✅ Selection system can operate on visual elements")
