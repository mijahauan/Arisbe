#!/usr/bin/env python3
"""
Constraint-Aware Renderer - Maintains EGI-EGDF Concordance During Rendering

This renderer wraps existing renderers (Qt, LaTeX, etc.) and ensures that any
styling or positioning changes maintain logical concordance with the EGI structure.
"""

from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod

from src.spatial_constraint_system import SpatialConstraintSystem, ConstraintViolation
from src.egi_core_dau import RelationalGraphWithCuts
from src.rendering_styles import DauStyle

class ConstraintAwareRenderer(ABC):
    """
    Base class for renderers that maintain EGI-EGDF concordance.
    
    All output formats (Qt, LaTeX, storage, printing) should inherit from this
    to ensure spatial constraints are enforced during rendering.
    """
    
    def __init__(self):
        self.constraint_system = SpatialConstraintSystem()
        self.egi_reference: Optional[RelationalGraphWithCuts] = None
        self.style: Optional[DauStyle] = None
        
    def set_egi_reference(self, egi: RelationalGraphWithCuts):
        """Set the EGI reference for constraint validation."""
        self.egi_reference = egi
        self.constraint_system.set_egi_reference(egi)
        
    def set_style(self, style: DauStyle):
        """Set the rendering style."""
        self.style = style
        
    def render_with_constraints(self, layout_data: Dict[str, Any], **kwargs) -> Any:
        """
        Render while enforcing spatial constraints.
        
        This is the main entry point that ensures constraint compliance.
        """
        # Validate layout against constraints
        violations = self.constraint_system.validate_layout(layout_data)
        
        if violations:
            # Apply constraint fixes
            fixed_layout = self.constraint_system.apply_constraint_fixes(violations, layout_data)
            
            # Log constraint violations and fixes
            self._log_constraint_actions(violations, layout_data, fixed_layout)
            
            layout_data = fixed_layout
            
        # Perform the actual rendering with constraint-compliant layout
        return self._render_implementation(layout_data, **kwargs)
    
    @abstractmethod
    def _render_implementation(self, layout_data: Dict[str, Any], **kwargs) -> Any:
        """Implement the actual rendering logic in subclasses."""
        pass
    
    def _log_constraint_actions(self, violations: List[ConstraintViolation], 
                               original_layout: Dict[str, Any], 
                               fixed_layout: Dict[str, Any]):
        """Log constraint violations and fixes applied."""
        print(f"Applied {len(violations)} constraint fixes:")
        for violation in violations:
            print(f"  - {violation.description}")
            
    def handle_interactive_edit(self, element_id: str, new_position: tuple, 
                              current_layout: Dict[str, Any]) -> tuple:
        """
        Handle interactive editing with constraint enforcement.
        
        Returns the constraint-adjusted position.
        """
        adjusted_position, warnings = self.constraint_system.enforce_constraints_during_edit(
            element_id, new_position, current_layout
        )
        
        for warning in warnings:
            print(f"Constraint warning: {warning}")
            
        return adjusted_position


class ConstraintAwareQtRenderer(ConstraintAwareRenderer):
    """Qt renderer with spatial constraint enforcement."""
    
    def __init__(self, base_renderer):
        super().__init__()
        self.base_renderer = base_renderer
        
    def create_canvas(self):
        """Create a Qt canvas widget with constraint enforcement."""
        return self.base_renderer.create_canvas()
        
    def render(self, styled_primitives: Dict[str, Any], **kwargs) -> Any:
        """Render with constraint enforcement."""
        return self.render_with_constraints(styled_primitives, **kwargs)
        
    def _render_implementation(self, layout_data: Dict[str, Any], **kwargs) -> Any:
        """Render using the base Qt renderer with constraint-compliant layout."""
        # Apply style to primitives with constraint-adjusted positions
        styled_primitives = self._apply_style_with_constraints(layout_data)
        
        # Use base renderer with styled primitives
        return self.base_renderer.render(styled_primitives, **kwargs)
    
    def _apply_style_with_constraints(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply styling while respecting spatial constraints."""
        styled_primitives = {}
        
        if not self.style:
            return layout_data
            
        # Apply style to each primitive type while maintaining constraints
        for element_id, primitive_data in layout_data.items():
            styled_primitive = self.style.apply_to_primitive(primitive_data)
            
            # Validate that styling doesn't violate constraints
            # (e.g., font size doesn't make text overflow cut boundaries)
            styled_primitive = self._validate_styled_primitive(styled_primitive, layout_data)
            
            styled_primitives[element_id] = styled_primitive
            
        return styled_primitives
    
    def _validate_styled_primitive(self, styled_primitive: Any, layout_data: Dict[str, Any]) -> Any:
        """Validate that styled primitive doesn't violate spatial constraints."""
        # Check if text size fits within bounds, vertex size doesn't exceed cut, etc.
        # For now, return as-is but this would implement size constraint validation
        return styled_primitive


class ConstraintAwareLaTeXRenderer(ConstraintAwareRenderer):
    """LaTeX renderer with spatial constraint enforcement."""
    
    def _render_implementation(self, layout_data: Dict[str, Any], **kwargs) -> str:
        """Generate LaTeX with constraint-compliant positioning."""
        latex_output = []
        
        # Generate LaTeX commands with constraint-validated positions
        latex_output.append("\\begin{tikzpicture}")
        
        # Render cuts first
        for element_id, primitive in layout_data.items():
            if getattr(primitive, 'element_type', None) == 'cut':
                latex_output.append(self._generate_cut_latex(primitive))
                
        # Render predicates
        for element_id, primitive in layout_data.items():
            if getattr(primitive, 'element_type', None) == 'predicate':
                latex_output.append(self._generate_predicate_latex(primitive))
                
        # Render vertices
        for element_id, primitive in layout_data.items():
            if getattr(primitive, 'element_type', None) == 'vertex':
                latex_output.append(self._generate_vertex_latex(primitive))
                
        # Render ligatures
        for element_id, primitive in layout_data.items():
            if getattr(primitive, 'element_type', None) == 'ligature':
                latex_output.append(self._generate_ligature_latex(primitive))
                
        latex_output.append("\\end{tikzpicture}")
        
        return "\n".join(latex_output)
    
    def _generate_cut_latex(self, primitive: Any) -> str:
        """Generate LaTeX for a cut with constraint-validated bounds."""
        if hasattr(primitive, 'bounds'):
            x1, y1, x2, y2 = primitive.bounds
            width = x2 - x1
            height = y2 - y1
            return f"\\draw ({x1},{y1}) rectangle ({x2},{y2});"
        return ""
    
    def _generate_predicate_latex(self, primitive: Any) -> str:
        """Generate LaTeX for a predicate with constraint-validated position."""
        if hasattr(primitive, 'position') and hasattr(primitive, 'label'):
            x, y = primitive.position
            label = primitive.label
            return f"\\node at ({x},{y}) {{{label}}};"
        return ""
    
    def _generate_vertex_latex(self, primitive: Any) -> str:
        """Generate LaTeX for a vertex with constraint-validated position."""
        if hasattr(primitive, 'position'):
            x, y = primitive.position
            vertex_cmd = f"\\filldraw ({x},{y}) circle (2pt);"
            if hasattr(primitive, 'label') and primitive.label:
                vertex_cmd += f"\n\\node at ({x+5},{y}) {{{primitive.label}}};"
            return vertex_cmd
        return ""
    
    def _generate_ligature_latex(self, primitive: Any) -> str:
        """Generate LaTeX for a ligature with constraint-validated path."""
        if hasattr(primitive, 'start_pos') and hasattr(primitive, 'end_pos'):
            x1, y1 = primitive.start_pos
            x2, y2 = primitive.end_pos
            # Generate rectilinear path
            if abs(x2 - x1) > abs(y2 - y1):
                return f"\\draw ({x1},{y1}) -- ({x2},{y1}) -- ({x2},{y2});"
            else:
                return f"\\draw ({x1},{y1}) -- ({x1},{y2}) -- ({x2},{y2});"
        return ""


class ConstraintAwareStorageRenderer(ConstraintAwareRenderer):
    """Storage renderer that maintains constraint compliance in serialized data."""
    
    def _render_implementation(self, layout_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate constraint-compliant storage format."""
        storage_data = {
            'egi_reference': self._serialize_egi(),
            'layout_data': layout_data,
            'constraints': self._serialize_constraints(),
            'metadata': {
                'constraint_system_version': '1.0',
                'validation_timestamp': self._get_timestamp()
            }
        }
        
        return storage_data
    
    def _serialize_egi(self) -> Dict[str, Any]:
        """Serialize EGI reference for storage."""
        if not self.egi_reference:
            return {}
            
        # Serialize EGI structure
        return {
            'vertices': [{'id': v.id, 'label': getattr(v, 'label', '')} for v in self.egi_reference.V],
            'edges': [{'id': e.id, 'label': getattr(e, 'label', '')} for e in self.egi_reference.E],
            'cuts': [{'id': c.id, 'label': getattr(c, 'label', '')} for c in self.egi_reference.Cut],
            'nu_mapping': dict(self.egi_reference.nu) if hasattr(self.egi_reference, 'nu') else {},
            'rel_mapping': dict(self.egi_reference.rel) if hasattr(self.egi_reference, 'rel') else {}
        }
    
    def _serialize_constraints(self) -> List[Dict[str, Any]]:
        """Serialize spatial constraints for storage."""
        return [
            {
                'constraint_id': c.constraint_id,
                'constraint_type': c.constraint_type,
                'source_element': c.source_element,
                'target_element': c.target_element,
                'parameters': c.parameters
            }
            for c in self.constraint_system.constraints.values()
        ]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        import datetime
        return datetime.datetime.now().isoformat()
