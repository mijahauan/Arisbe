"""
PySide6 Rendering API Contracts

Defines and enforces API contracts for the handoff between the layout engine,
diagram renderer, and PySide6 canvas for professional EG diagram rendering.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import functools

# Type aliases for PySide6 rendering
CanvasCoordinate = Tuple[float, float]
CanvasBounds = Tuple[float, float, float, float]  # x1, y1, x2, y2
RGBColor = Tuple[int, int, int]
DrawingCommand = Dict[str, Any]

@dataclass
class PySide6RenderingStyle:
    """Standardized rendering style for PySide6 canvas operations."""
    
    # Line properties
    line_width: float = 1.0
    line_color: RGBColor = (0, 0, 0)  # Black
    line_style: str = "solid"  # solid, dashed, dotted
    
    # Fill properties
    fill_color: Optional[RGBColor] = None
    fill_opacity: float = 1.0
    
    # Text properties
    font_family: str = "Arial"
    font_size: int = 12
    font_weight: str = "normal"  # normal, bold
    text_color: RGBColor = (0, 0, 0)
    
    # Shape properties
    radius: float = 5.0
    
    def validate(self) -> bool:
        """Validate style parameters are within acceptable ranges."""
        if self.line_width <= 0:
            raise ValueError(f"Invalid line_width: {self.line_width} (must be > 0)")
        if not (0 <= self.fill_opacity <= 1):
            raise ValueError(f"Invalid fill_opacity: {self.fill_opacity} (must be 0-1)")
        if self.font_size <= 0:
            raise ValueError(f"Invalid font_size: {self.font_size} (must be > 0)")
        if self.radius < 0:
            raise ValueError(f"Invalid radius: {self.radius} (must be >= 0)")
        return True

@dataclass
class PySide6DrawingCommand:
    """Standardized drawing command for PySide6 canvas."""
    
    command_type: str  # line, oval, rectangle, text, polygon
    coordinates: List[CanvasCoordinate]
    style: PySide6RenderingStyle
    text: Optional[str] = None
    element_id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate drawing command structure and parameters."""
        valid_commands = {"line", "oval", "rectangle", "text", "polygon", "circle"}
        if self.command_type not in valid_commands:
            raise ValueError(f"Invalid command_type: {self.command_type}")
        
        if not self.coordinates:
            raise ValueError("Drawing command must have at least one coordinate")
        
        if self.command_type == "text" and not self.text:
            raise ValueError("Text command must have text content")
        
        if self.command_type == "line" and len(self.coordinates) < 2:
            raise ValueError("Line command must have at least 2 coordinates")
        
        if self.command_type in ["oval", "rectangle", "circle"] and len(self.coordinates) < 1:
            raise ValueError(f"{self.command_type} command must have at least 1 coordinate")
        
        self.style.validate()
        return True

@dataclass
class PySide6RenderingRequest:
    """Complete rendering request for PySide6 canvas."""
    
    canvas_width: int
    canvas_height: int
    canvas_bounds: CanvasBounds
    drawing_commands: List[PySide6DrawingCommand]
    background_color: RGBColor = (255, 255, 255)  # White
    title: str = "EG Diagram"
    
    def validate(self) -> bool:
        """Validate complete rendering request."""
        if self.canvas_width <= 0 or self.canvas_height <= 0:
            raise ValueError(f"Invalid canvas dimensions: {self.canvas_width}x{self.canvas_height}")
        
        x1, y1, x2, y2 = self.canvas_bounds
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid canvas bounds: {self.canvas_bounds}")
        
        if not self.drawing_commands:
            raise ValueError("Rendering request must have at least one drawing command")
        
        for cmd in self.drawing_commands:
            cmd.validate()
        
        return True

class PySide6CanvasContract(ABC):
    """Abstract contract for PySide6 canvas implementations."""
    
    @abstractmethod
    def initialize_canvas(self, width: int, height: int, title: str) -> bool:
        """Initialize canvas with specified dimensions and title."""
        pass
    
    @abstractmethod
    def execute_drawing_command(self, command: PySide6DrawingCommand) -> bool:
        """Execute a single drawing command on the canvas."""
        pass
    
    @abstractmethod
    def render_complete_request(self, request: PySide6RenderingRequest) -> bool:
        """Render a complete drawing request to the canvas."""
        pass
    
    @abstractmethod
    def save_to_file(self, filepath: str, format: str = "PNG") -> bool:
        """Save canvas contents to file."""
        pass
    
    @abstractmethod
    def show_interactive(self) -> None:
        """Display canvas in interactive window."""
        pass

def validate_pyside6_handoff(func):
    """Decorator to validate PySide6 rendering handoff contracts."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Pre-execution validation
        if len(args) > 1 and isinstance(args[1], PySide6RenderingRequest):
            request = args[1]
            try:
                request.validate()
            except Exception as e:
                raise ValueError(f"PySide6 handoff contract violation: {e}")
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Post-execution validation
        if not isinstance(result, bool):
            raise ValueError(f"PySide6 handoff must return boolean success status, got {type(result)}")
        
        return result
    
    return wrapper

class PySide6ContractValidator:
    """Utility class for validating PySide6 rendering contracts."""
    
    @staticmethod
    def validate_style_consistency(commands: List[PySide6DrawingCommand]) -> bool:
        """Validate that drawing commands have consistent, appropriate styles."""
        
        # Check for Dau convention compliance
        identity_line_width = None
        cut_line_width = None
        
        for cmd in commands:
            if cmd.element_id and "identity" in cmd.element_id.lower():
                if identity_line_width is None:
                    identity_line_width = cmd.style.line_width
                elif cmd.style.line_width != identity_line_width:
                    raise ValueError("Inconsistent identity line widths detected")
            
            if cmd.element_id and "cut" in cmd.element_id.lower():
                if cut_line_width is None:
                    cut_line_width = cmd.style.line_width
                elif cmd.style.line_width != cut_line_width:
                    raise ValueError("Inconsistent cut line widths detected")
        
        # Validate Dau convention: identity lines should be heavier than cuts
        if identity_line_width and cut_line_width:
            if identity_line_width <= cut_line_width:
                raise ValueError(f"Dau convention violation: identity lines ({identity_line_width}) must be heavier than cuts ({cut_line_width})")
        
        return True
    
    @staticmethod
    def validate_spatial_consistency(commands: List[PySide6DrawingCommand], bounds: CanvasBounds) -> bool:
        """Validate that all drawing commands fit within canvas bounds."""
        
        x1, y1, x2, y2 = bounds
        
        for cmd in commands:
            for coord in cmd.coordinates:
                x, y = coord
                if not (x1 <= x <= x2 and y1 <= y <= y2):
                    raise ValueError(f"Drawing command coordinate {coord} outside canvas bounds {bounds}")
        
        return True
    
    @staticmethod
    def validate_element_coverage(commands: List[PySide6DrawingCommand], expected_elements: List[str]) -> bool:
        """Validate that all expected graph elements have drawing commands."""
        
        command_elements = set()
        for cmd in commands:
            if cmd.element_id:
                command_elements.add(cmd.element_id)
        
        expected_set = set(expected_elements)
        missing_elements = expected_set - command_elements
        
        if missing_elements:
            raise ValueError(f"Missing drawing commands for elements: {missing_elements}")
        
        return True

def create_dau_compliant_style(element_type: str) -> PySide6RenderingStyle:
    """Create Dau-compliant rendering style for specific element types."""
    
    if element_type == "identity_line":
        return PySide6RenderingStyle(
            line_width=4.0,  # Heavy identity lines per Dau
            line_color=(0, 0, 0),
            line_style="solid"
        )
    elif element_type == "cut_boundary":
        return PySide6RenderingStyle(
            line_width=1.0,  # Fine cut boundaries per Dau
            line_color=(0, 0, 0),
            line_style="solid",
            fill_color=None  # No fill for cuts
        )
    elif element_type == "vertex_spot":
        return PySide6RenderingStyle(
            line_width=1.0,
            line_color=(0, 0, 0),
            fill_color=(0, 0, 0),  # Filled spots
            radius=3.5  # Prominent vertex spots
        )
    # NOTE: hook_line removed - hooks are invisible positions per Dau formalism
    # Heavy identity lines connect directly to predicate boundary positions
    elif element_type == "predicate_text":
        return PySide6RenderingStyle(
            font_family="Arial",
            font_size=12,
            font_weight="normal",
            text_color=(0, 0, 0)
        )
    else:
        # Default style
        return PySide6RenderingStyle()

# Contract enforcement integration
class ContractEnforcedPySide6Renderer:
    """Renderer with automatic contract enforcement for PySide6 handoff."""
    
    def __init__(self, canvas_implementation):
        if not isinstance(canvas_implementation, PySide6CanvasContract):
            raise ValueError("Canvas implementation must implement PySide6CanvasContract")
        self.canvas = canvas_implementation
        self.validator = PySide6ContractValidator()
    
    @validate_pyside6_handoff
    def render_with_contracts(self, request: PySide6RenderingRequest) -> bool:
        """Render with full contract validation."""
        
        # Pre-render validation
        self.validator.validate_style_consistency(request.drawing_commands)
        self.validator.validate_spatial_consistency(request.drawing_commands, request.canvas_bounds)
        
        # Execute rendering
        return self.canvas.render_complete_request(request)

if __name__ == "__main__":
    # Test contract validation
    print("🔒 PySide6 Rendering API Contracts")
    print("=" * 40)
    
    # Test style creation
    identity_style = create_dau_compliant_style("identity_line")
    cut_style = create_dau_compliant_style("cut_boundary")
    
    print(f"✅ Identity line style: width={identity_style.line_width}")
    print(f"✅ Cut boundary style: width={cut_style.line_width}")
    print(f"✅ Dau compliance: identity ({identity_style.line_width}) > cut ({cut_style.line_width})")
    
    # Test command validation
    test_command = PySide6DrawingCommand(
        command_type="line",
        coordinates=[(0, 0), (100, 100)],
        style=identity_style,
        element_id="identity_line_1"
    )
    
    print(f"✅ Command validation: {test_command.validate()}")
    
    print("\n🎯 Contract system ready for PySide6 handoff validation!")
