"""
Style Loader for Arisbe EG Style System

Loads and validates JSON-based style definitions for use with the layout engine.
Provides platform-independent style management with schema validation.
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class StyleSpecification:
    """Platform-independent style specification for layout engine integration"""
    
    # Metadata
    style_name: str
    version: str
    description: str
    
    # Layout parameters (affect spatial calculations)
    element_spacing: float
    cut_padding: float
    sibling_spacing: float
    diagram_margin: float
    text_margin: float
    ligature_clearance: float
    
    # Typography
    font_family: str
    font_size: float
    font_weight: str
    background_color: str
    
    # Element sizing
    vertex_radius: float
    predicate_char_width: float
    predicate_height: float
    
    # Visual properties
    vertex_fill_color: str
    vertex_rendering_mode: str
    cut_shape: str
    cut_corner_radius: float
    cut_line_width: float
    ligature_line_width: float
    
    # Polarity-based fills
    even_polarity_fill: str
    odd_polarity_fill: str
    
    # Optional features
    alternating_shading_enabled: bool
    arity_numbers_enabled: bool
    variable_labels_enabled: bool
    
    # Transformation support
    double_cut_highlight_enabled: bool
    isomorphic_highlight_enabled: bool
    collapsed_context_enabled: bool
    
    # Raw style data for renderer access
    raw_style_data: Dict[str, Any]

    # Layout flow direction — the reading axis the layered layout develops along
    # (ELK's elk.direction).  "RIGHT" = left-to-right (default, the scan order
    # of left-to-right scripts); "DOWN"/"LEFT"/"UP" are the other axes.  An
    # honored projection convention sourced from the style's layout.direction.
    layout_direction: str = "RIGHT"

    # How a relation's argument ORDER (its ν sequence) is shown in the drawing —
    # a projection convention faithful to the style's namesake:
    #   "numbered"  — small numeric labels 1..n on the lines (Dau §11.2; also
    #                 Sowa CGs).  Always unambiguous, independent of placement.
    #   "clockwise" — the hooks are read in clockwise order around the spot
    #                 (Peirce, CP 4.470 / Convention 13).
    # The reader (eg_reader) recovers the order by whichever the active style
    # draws, so the drawn form carries the full ν — argument order included.
    argument_order_convention: str = "numbered"

    def get_element_bounds(self, element_type: str, content: str = "") -> Tuple[float, float]:
        """Calculate spatial bounds required for an element with this style"""
        if element_type == "vertex":
            return (self.vertex_radius * 2, self.vertex_radius * 2)
        elif element_type == "predicate":
            # Text-based sizing
            text_width = len(content) * self.predicate_char_width * 0.6  # Approximate
            width = max(self.predicate_char_width * 8, text_width + 2 * self.text_margin)
            return (width, self.predicate_height)
        elif element_type == "cut":
            return (self.cut_padding * 2, self.cut_padding * 2)  # Minimum
        else:
            return (20.0, 20.0)  # Default
    
    @classmethod
    def from_json_data(cls, data: Dict[str, Any]) -> 'StyleSpecification':
        """Create StyleSpecification from validated JSON data"""
        
        return cls(
            # Metadata
            style_name=data['style_name'],
            version=data['version'],
            description=data.get('description', ''),
            
            # Layout parameters
            element_spacing=data['layout']['element_spacing'],
            cut_padding=data['layout']['cut_padding'],
            sibling_spacing=data['layout']['sibling_spacing'],
            diagram_margin=data['layout'].get('diagram_margin', 25.0),
            text_margin=data['layout'].get('text_margin', 5.0),
            ligature_clearance=data['layout'].get('ligature_clearance', 10.0),
            
            # Typography
            font_family=data['global']['font_family'],
            font_size=data['global']['font_size'],
            font_weight=data['global'].get('font_weight', 'normal'),
            background_color=data['global']['background_color'],
            
            # Element sizing
            vertex_radius=data['vertex']['radius'],
            predicate_char_width=data['predicate'].get('char_width_estimate', 6.0),
            predicate_height=data['predicate'].get('height_estimate', 14.0),
            
            # Visual properties
            vertex_fill_color=data['vertex']['fill_color'],
            vertex_rendering_mode=data['vertex'].get('rendering_mode', 'dot_and_label'),
            cut_shape=data['cut']['shape'],
            cut_corner_radius=data['cut'].get('corner_radius', 0),
            cut_line_width=data['cut']['line_width'],
            ligature_line_width=data['ligature']['line_width'],
            
            # Polarity-based fills
            even_polarity_fill=data['cut'].get('even_polarity_fill', 'transparent'),
            odd_polarity_fill=data['cut'].get('odd_polarity_fill', 'rgba(0,0,0,0.08)'),
            
            # Optional features
            alternating_shading_enabled=data.get('alternating_shading', {}).get('enabled', False),
            arity_numbers_enabled=data.get('arity_numbers', {}).get('enabled', False),
            variable_labels_enabled=data.get('variable_labels', {}).get('enabled', False),
            
            # Transformation support
            double_cut_highlight_enabled=data.get('double_cut_highlight', {}).get('enabled', False),
            isomorphic_highlight_enabled=data.get('isomorphic_highlight', {}).get('enabled', False),
            collapsed_context_enabled=data.get('collapsed_context', {}).get('enabled', False),
            
            # Raw data for renderer access
            raw_style_data=data,

            # Layout flow direction (honored; default left-to-right)
            layout_direction=data['layout'].get('direction', 'RIGHT'),

            # Argument-order convention (how ν's order is drawn): default the
            # unambiguous numbered form (Dau); a style may set "clockwise" (Peirce).
            argument_order_convention=data.get('argument_order', {}).get(
                'convention', 'numbered'),
        )


class StyleLoader:
    """Loads and validates EG style definitions"""
    
    def __init__(self, styles_dir: Optional[Path] = None):
        """Initialize style loader
        
        Args:
            styles_dir: Directory containing style files (defaults to project styles/)
        """
        if styles_dir is None:
            # Default to project styles directory
            project_root = Path(__file__).parent.parent
            styles_dir = project_root / 'styles'
        
        self.styles_dir = Path(styles_dir)
        self.schema_path = self.styles_dir / 'style_schema.json'
        self._schema = None
        self._loaded_styles = {}
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Load and cache the style schema"""
        if self._schema is None:
            if self.schema_path.exists():
                with open(self.schema_path, 'r') as f:
                    self._schema = json.load(f)
            else:
                raise FileNotFoundError(f"Style schema not found: {self.schema_path}")
        return self._schema
    
    def list_available_styles(self) -> List[str]:
        """List all available style files"""
        if not self.styles_dir.exists():
            return []
        
        style_files = []
        for file_path in self.styles_dir.glob('*.json'):
            if file_path.name != 'style_schema.json':
                # Extract style name from filename (remove .json extension)
                style_name = file_path.stem
                style_files.append(style_name)
        
        return sorted(style_files)
    
    def load_style(self, style_name: str) -> StyleSpecification:
        """Load and validate a style definition
        
        Args:
            style_name: Name of style file (with or without .json extension)
            
        Returns:
            StyleSpecification object
            
        Raises:
            FileNotFoundError: If style file doesn't exist
            jsonschema.ValidationError: If style doesn't match schema
            json.JSONDecodeError: If style file has invalid JSON
        """
        
        # Check cache first
        if style_name in self._loaded_styles:
            return self._loaded_styles[style_name]
        
        # Ensure .json extension
        if not style_name.endswith('.json'):
            style_name += '.json'
        
        style_path = self.styles_dir / style_name
        
        if not style_path.exists():
            raise FileNotFoundError(f"Style file not found: {style_path}")
        
        # Load JSON data
        with open(style_path, 'r') as f:
            style_data = json.load(f)
        
        # Validate against schema
        try:
            jsonschema.validate(style_data, self.schema)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(
                f"Style validation failed for {style_name}: {e.message}"
            )
        
        # Create StyleSpecification
        style_spec = StyleSpecification.from_json_data(style_data)
        
        # Cache and return
        cache_key = style_name.replace('.json', '')
        self._loaded_styles[cache_key] = style_spec
        
        return style_spec
    
    def load_default_style(self) -> StyleSpecification:
        """Load the default DAU-compliant style"""
        return self.load_style('dau-compliant@1.0')
    
    def validate_style_file(self, style_path: Path) -> bool:
        """Validate a style file against the schema
        
        Args:
            style_path: Path to style file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            with open(style_path, 'r') as f:
                style_data = json.load(f)
            
            jsonschema.validate(style_data, self.schema)
            return True
            
        except (json.JSONDecodeError, jsonschema.ValidationError, FileNotFoundError):
            return False
    
    def get_style_info(self, style_name: str) -> Dict[str, Any]:
        """Get metadata about a style without fully loading it
        
        Args:
            style_name: Name of style file
            
        Returns:
            Dictionary with style metadata
        """
        if not style_name.endswith('.json'):
            style_name += '.json'
        
        style_path = self.styles_dir / style_name
        
        if not style_path.exists():
            raise FileNotFoundError(f"Style file not found: {style_path}")
        
        with open(style_path, 'r') as f:
            style_data = json.load(f)
        
        return {
            'style_name': style_data.get('style_name', 'Unknown'),
            'version': style_data.get('version', '0.0.0'),
            'description': style_data.get('description', 'No description'),
            'file_path': str(style_path),
            'file_size': style_path.stat().st_size
        }
    
    def create_style_template(self, output_path: Path, base_style: str = 'dau-compliant@1.0') -> None:
        """Create a new style template based on an existing style
        
        Args:
            output_path: Where to save the new style template
            base_style: Base style to copy from
        """
        base_spec = self.load_style(base_style)
        
        # Create template with modified metadata
        template_data = base_spec.raw_style_data.copy()
        template_data['style_name'] = output_path.stem
        template_data['version'] = '1.0.0'
        template_data['description'] = f'Custom style based on {base_style}'
        
        # Save template
        with open(output_path, 'w') as f:
            json.dump(template_data, f, indent=2)


# Convenience functions for common operations
def load_style(style_name: str) -> StyleSpecification:
    """Load a style using the default loader"""
    loader = StyleLoader()
    return loader.load_style(style_name)


def load_default_style() -> StyleSpecification:
    """Load the default DAU-compliant style"""
    loader = StyleLoader()
    return loader.load_default_style()


def list_available_styles() -> List[str]:
    """List all available styles"""
    loader = StyleLoader()
    return loader.list_available_styles()


if __name__ == '__main__':
    # Demo usage
    loader = StyleLoader()
    
    print("Available styles:")
    for style in loader.list_available_styles():
        info = loader.get_style_info(style)
        print(f"  {info['style_name']} v{info['version']} - {info['description']}")
    
    print("\nLoading default style...")
    default_style = loader.load_default_style()
    print(f"Loaded: {default_style.style_name} v{default_style.version}")
    print(f"Element spacing: {default_style.element_spacing}")
    print(f"Cut shape: {default_style.cut_shape}")
