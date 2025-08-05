"""
PySide6 Contract Integration

Integrates the contract system with existing PySide6 canvas implementation
to ensure proper API handoffs and Dau convention compliance.
"""

import sys
sys.path.append('.')

from typing import List, Tuple, Optional
from pyside6_rendering_contracts import (
    PySide6RenderingRequest, PySide6DrawingCommand, PySide6RenderingStyle,
    PySide6CanvasContract, ContractEnforcedPySide6Renderer,
    create_dau_compliant_style, validate_pyside6_handoff
)
from pyside6_canvas import PySide6Canvas
from diagram_renderer_clean import RenderingTheme
from graphviz_layout_engine_v2 import LayoutResult

class ContractCompliantPySide6Canvas(PySide6CanvasContract):
    """PySide6Canvas implementation with contract compliance."""
    
    def __init__(self):
        self.canvas = None
        self.initialized = False
    
    def initialize_canvas(self, width: int, height: int, title: str) -> bool:
        """Initialize canvas with contract validation."""
        try:
            self.canvas = PySide6Canvas(width, height, title)
            self.initialized = True
            return True
        except Exception as e:
            print(f"❌ Canvas initialization failed: {e}")
            return False
    
    def execute_drawing_command(self, command: PySide6DrawingCommand) -> bool:
        """Execute single drawing command with validation."""
        if not self.initialized:
            raise RuntimeError("Canvas not initialized")
        
        try:
            command.validate()
            
            # Convert contract command to canvas API
            if command.command_type == "line":
                start = command.coordinates[0]
                end = command.coordinates[1]
                style = {
                    'width': command.style.line_width,
                    'fill': f'rgb{command.style.line_color}'
                }
                self.canvas.draw_line(start, end, style)
                
            elif command.command_type == "circle":
                center = command.coordinates[0]
                style = {
                    'width': command.style.line_width,
                    'outline': f'rgb{command.style.line_color}',
                    'fill': f'rgb{command.style.fill_color}' if command.style.fill_color else ''
                }
                self.canvas.draw_circle(center, command.style.radius, style)
                
            elif command.command_type == "oval":
                x1, y1 = command.coordinates[0]
                if len(command.coordinates) > 1:
                    x2, y2 = command.coordinates[1]
                else:
                    # Use radius-based oval
                    x2, y2 = x1 + command.style.radius * 2, y1 + command.style.radius * 2
                    x1, y1 = x1 - command.style.radius, y1 - command.style.radius
                
                style = {
                    'width': command.style.line_width,
                    'outline': f'rgb{command.style.line_color}',
                    'fill': f'rgb{command.style.fill_color}' if command.style.fill_color else ''
                }
                self.canvas.draw_oval(x1, y1, x2, y2, style)
                
            elif command.command_type == "text":
                x, y = command.coordinates[0]
                style = {
                    'font': (command.style.font_family, command.style.font_size, command.style.font_weight),
                    'fill': f'rgb{command.style.text_color}'
                }
                self.canvas.draw_text(x, y, command.text, style)
            
            return True
            
        except Exception as e:
            print(f"❌ Drawing command failed: {e}")
            return False
    
    def render_complete_request(self, request: PySide6RenderingRequest) -> bool:
        """Render complete request with full validation."""
        try:
            request.validate()
            
            # Initialize canvas if needed
            if not self.initialized:
                self.initialize_canvas(request.canvas_width, request.canvas_height, request.title)
            
            # Clear canvas
            self.canvas.clear()
            
            # Execute all drawing commands
            success_count = 0
            for command in request.drawing_commands:
                if self.execute_drawing_command(command):
                    success_count += 1
            
            success_rate = success_count / len(request.drawing_commands)
            return success_rate >= 0.95  # Allow for minor failures
            
        except Exception as e:
            print(f"❌ Complete request rendering failed: {e}")
            return False
    
    def save_to_file(self, filepath: str, format: str = "PNG") -> bool:
        """Save canvas to file with validation."""
        if not self.initialized:
            return False
        
        try:
            self.canvas.save_to_file(filepath)
            return True
        except Exception as e:
            print(f"❌ Save to file failed: {e}")
            return False
    
    def show_interactive(self) -> None:
        """Show interactive canvas."""
        if self.initialized:
            self.canvas.show()

class LayoutToPySide6Converter:
    """Converts layout results to PySide6 rendering requests."""
    
    def __init__(self, theme: Optional[RenderingTheme] = None):
        self.theme = theme or RenderingTheme()
    
    def convert_layout_to_request(self, layout_result: LayoutResult, graph, 
                                canvas_width: int, canvas_height: int,
                                title: str = "EG Diagram") -> PySide6RenderingRequest:
        """Convert layout result to PySide6 rendering request."""
        
        drawing_commands = []
        
        # Convert each spatial primitive to drawing command
        for primitive_id, primitive in layout_result.primitives.items():
            element_type = primitive.element_type
            element_id = primitive.element_id
            
            if element_type == 'vertex':
                # Vertex as filled circle (identity spot)
                x, y = primitive.position
                style = create_dau_compliant_style("vertex_spot")
                
                command = PySide6DrawingCommand(
                    command_type="circle",
                    coordinates=[(x, y)],
                    style=style,
                    element_id=element_id
                )
                drawing_commands.append(command)
                
            elif element_type == 'edge':
                # Edge as line (identity line or hook)
                if hasattr(primitive, 'coordinates') and primitive.coordinates:
                    coords = primitive.coordinates
                elif hasattr(primitive, 'position'):
                    # Fallback: create short line from position
                    x, y = primitive.position
                    coords = [(x-10, y), (x+10, y)]
                else:
                    continue
                    
                # Determine if this is an identity line or hook
                if 'identity' in element_id.lower():
                    style = create_dau_compliant_style("identity_line")
                else:
                    style = create_dau_compliant_style("hook_line")
                
                command = PySide6DrawingCommand(
                    command_type="line",
                    coordinates=coords,
                    style=style,
                    element_id=element_id
                )
                drawing_commands.append(command)
                    
            elif element_type == 'cut':
                # Cut as oval boundary
                if hasattr(primitive, 'bounds'):
                    x1, y1, x2, y2 = primitive.bounds
                else:
                    # Fallback: create bounds from position
                    x, y = primitive.position
                    x1, y1, x2, y2 = x-50, y-30, x+50, y+30
                    
                style = create_dau_compliant_style("cut_boundary")
                
                command = PySide6DrawingCommand(
                    command_type="oval",
                    coordinates=[(x1, y1), (x2, y2)],
                    style=style,
                    element_id=element_id
                )
                drawing_commands.append(command)
                
            elif element_type == 'predicate':
                # Predicate text - this is the missing case!
                x, y = primitive.position
                # Get predicate name from graph relations
                predicate_name = 'P'  # Default
                if hasattr(graph, 'rel') and element_id in graph.rel:
                    predicate_name = graph.rel[element_id]
                elif hasattr(graph, 'E'):
                    # Find edge with this ID and get its relation name
                    for edge in graph.E:
                        if edge.id == element_id and hasattr(graph, 'rel') and edge.id in graph.rel:
                            predicate_name = graph.rel[edge.id]
                            break
                
                style = create_dau_compliant_style("predicate_text")
                
                command = PySide6DrawingCommand(
                    command_type="text",
                    coordinates=[(x, y)],
                    style=style,
                    text=predicate_name,
                    element_id=element_id
                )
                drawing_commands.append(command)
                
            elif element_type == 'text':
                # Generic text
                x, y = primitive.position
                text = getattr(primitive, 'text', 'P')
                style = create_dau_compliant_style("predicate_text")
                
                command = PySide6DrawingCommand(
                    command_type="text",
                    coordinates=[(x, y)],
                    style=style,
                    text=text,
                    element_id=element_id
                )
                drawing_commands.append(command)
        
        # Create rendering request
        request = PySide6RenderingRequest(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            canvas_bounds=layout_result.canvas_bounds,
            drawing_commands=drawing_commands,
            title=title
        )
        
        return request

@validate_pyside6_handoff
def render_egif_with_contracts(egif: str, output_path: str, 
                             canvas_width: int = 800, canvas_height: int = 600) -> bool:
    """Render EGIF with full contract validation and enforcement."""
    
    try:
        # Import required modules
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        print(f"🔒 Contract-Enforced EGIF Rendering")
        print(f"   EGIF: {egif}")
        print(f"   Output: {output_path}")
        
        # Parse EGIF
        graph = parse_egif(egif)
        print(f"   ✅ Parsed: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Generate layout
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(graph)
        print(f"   ✅ Layout: {len(layout_result.primitives)} spatial primitives")
        
        # Convert to PySide6 request
        converter = LayoutToPySide6Converter()
        request = converter.convert_layout_to_request(
            layout_result, graph, canvas_width, canvas_height, f"EG: {egif}"
        )
        print(f"   ✅ Converted: {len(request.drawing_commands)} drawing commands")
        
        # Create contract-enforced renderer
        canvas_impl = ContractCompliantPySide6Canvas()
        renderer = ContractEnforcedPySide6Renderer(canvas_impl)
        
        # Render with contracts
        success = renderer.render_with_contracts(request)
        print(f"   ✅ Rendered: {success}")
        
        if success:
            # Save to file
            save_success = canvas_impl.save_to_file(output_path)
            print(f"   ✅ Saved: {save_success}")
            return save_success
        
        return False
        
    except Exception as e:
        print(f"   ❌ Contract-enforced rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔒 PySide6 Contract Integration Test")
    print("=" * 40)
    
    # Test contract integration
    test_cases = [
        '(Human "Socrates")',
        '*x (Human x)',
        '~[ (Mortal "Socrates") ]',
        '*x ~[ (P x) ] ~[ (Q x) ]'
    ]
    
    for i, egif in enumerate(test_cases):
        output_path = f"contract_test_{i+1}.png"
        print(f"\n🧪 Test Case {i+1}:")
        success = render_egif_with_contracts(egif, output_path)
        if success:
            print(f"   ✅ SUCCESS: {output_path}")
        else:
            print(f"   ❌ FAILED: {output_path}")
    
    print(f"\n🎯 Contract integration testing complete!")
