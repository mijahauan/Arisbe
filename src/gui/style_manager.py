"""
Abstract Style Manager for Existential Graph Diagram Rendering

Supports multiple visual styles while maintaining logical independence:
- Dau-compliant (mathematical precision, rounded rectangles)
- Peirce-authentic (historical fidelity, traditional appearance) 
- Sowa-compliant (conceptual graph conventions)
- User-defined (custom styling)

The style system is completely orthogonal to the logical structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QBrush, QFont


class StyleType(Enum):
    """Available diagram style types."""
    DAU_COMPLIANT = "dau-compliant"
    PEIRCE_AUTHENTIC = "peirce-authentic" 
    SOWA_COMPLIANT = "sowa-compliant"
    USER_DEFINED = "user-defined"


@dataclass
class ElementStyle:
    """Base styling parameters for diagram elements."""
    line_width: float
    color: QColor
    fill_color: Optional[QColor] = None
    line_style: Qt.PenStyle = Qt.SolidLine
    
    def get_pen(self) -> QPen:
        """Get QPen for this element style."""
        pen = QPen(self.color)
        pen.setWidthF(self.line_width)
        pen.setStyle(self.line_style)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen
    
    def get_brush(self) -> QBrush:
        """Get QBrush for this element style."""
        if self.fill_color:
            # Check if it's a QColor or a tuple
            if isinstance(self.fill_color, QColor):
                return QBrush(self.fill_color)
            else:
                return QBrush(QColor(*self.fill_color))
        return QBrush(Qt.NoBrush)


@dataclass
class CutStyle(ElementStyle):
    """Styling parameters specific to cuts."""
    corner_radius: float = 8.0
    padding: float = 10.0
    nesting_margin: float = 15.0
    shape_type: str = "rounded_rectangle"  # "rectangle", "rounded_rectangle", "oval"


@dataclass
class LigatureStyle(ElementStyle):
    """Styling parameters specific to ligatures."""
    connection_type: str = "straight"  # "straight", "curved", "orthogonal"
    arrow_style: str = "none"  # "none", "arrow", "double_arrow"
    routing_algorithm: str = "direct"  # "direct", "orthogonal", "bezier"


@dataclass
class VertexStyle(ElementStyle):
    """Styling parameters specific to vertices."""
    radius: float = 8.0
    shape_type: str = "circle"  # "circle", "square", "diamond"
    label_offset: float = 15.0


@dataclass
class PredicateStyle(ElementStyle):
    """Styling parameters specific to predicates."""
    length: float = 40.0
    shape_type: str = "line"  # "line", "rectangle", "oval"


@dataclass
class LabelStyle:
    """Styling parameters for text labels."""
    font_family: str = "Arial"
    font_size: int = 12
    font_weight: str = "normal"  # "normal", "bold", "light"
    color: tuple = (0, 0, 0)  # RGB tuple instead of QColor
    
    def get_font(self) -> QFont:
        """Get QFont for labels."""
        font = QFont(self.font_family, self.font_size)
        if self.font_weight == "normal":
            font.setWeight(QFont.Weight.Normal)
        elif self.font_weight == "bold":
            font.setWeight(QFont.Weight.Bold)
        elif self.font_weight == "light":
            font.setWeight(QFont.Weight.Light)
        return font


@dataclass
class LayoutStyle:
    """Styling parameters for overall layout."""
    element_spacing: float = 40.0
    diagram_margin: float = 30.0
    sheet_color: tuple = (255, 255, 255)  # RGB tuple instead of QColor
    grid_visible: bool = False
    grid_spacing: float = 20.0
    grid_color: tuple = (240, 240, 240)  # RGB tuple instead of QColor


class DiagramStyle(ABC):
    """Abstract base class for diagram visual styles."""
    
    def __init__(self, style_id: str, name: str, description: str):
        self.style_id = style_id
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_cut_style(self, nesting_level: int = 0) -> CutStyle:
        """Get cut styling parameters."""
        pass
    
    @abstractmethod
    def get_ligature_style(self, context: str = "default") -> LigatureStyle:
        """Get ligature styling parameters."""
        pass
    
    @abstractmethod
    def get_vertex_style(self, vertex_type: str = "generic") -> VertexStyle:
        """Get vertex styling parameters."""
        pass
    
    @abstractmethod
    def get_predicate_style(self, relation_name: str = "default") -> PredicateStyle:
        """Get predicate styling parameters."""
        pass
    
    @abstractmethod
    def get_label_style(self, label_type: str = "default") -> LabelStyle:
        """Get label styling parameters."""
        pass
    
    @abstractmethod
    def get_layout_style(self) -> LayoutStyle:
        """Get layout styling parameters."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Export style to dictionary for serialization."""
        return {
            "style_id": self.style_id,
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiagramStyle':
        """Import style from dictionary."""
        raise NotImplementedError("Subclasses must implement from_dict")


class StyleManager:
    """Manages multiple diagram styles and provides style selection."""
    
    def __init__(self):
        self._styles: Dict[str, DiagramStyle] = {}
        self._current_style_id: Optional[str] = None
        self._style_search_paths: List[Path] = [
            Path(__file__).parent / "styles",
            Path.home() / ".arisbe" / "styles"
        ]
    
    def register_style(self, style: DiagramStyle):
        """Register a new diagram style."""
        self._styles[style.style_id] = style
        if self._current_style_id is None:
            self._current_style_id = style.style_id
    
    def get_style(self, style_id: str) -> Optional[DiagramStyle]:
        """Get a registered style by ID."""
        return self._styles.get(style_id)
    
    def get_current_style(self) -> Optional[DiagramStyle]:
        """Get the currently active style."""
        if self._current_style_id:
            return self._styles.get(self._current_style_id)
        return None
    
    def set_current_style(self, style_id: str) -> bool:
        """Set the current active style."""
        if style_id in self._styles:
            self._current_style_id = style_id
            return True
        return False
    
    def list_styles(self) -> List[Tuple[str, str, str]]:
        """List all registered styles as (id, name, description) tuples."""
        return [
            (style.style_id, style.name, style.description)
            for style in self._styles.values()
        ]
    
    def load_style_from_file(self, file_path: Path) -> bool:
        """Load a style from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            style_type = data.get('type', 'UserDefinedStyle')
            
            # Import appropriate style class
            if style_type == 'DauCompliantStyle':
                from gui.styles.dau_compliant_style import DauCompliantStyle
                style = DauCompliantStyle.from_dict(data)
            elif style_type == 'PeirceAuthenticStyle':
                from gui.styles.peirce_authentic_style import PeirceAuthenticStyle
                style = PeirceAuthenticStyle.from_dict(data)
            elif style_type == 'PeirceLatexInspiredStyle':
                from gui.styles.peirce_latex_inspired_style import PeirceLatexInspiredStyle
                style = PeirceLatexInspiredStyle.from_dict(data)
            elif style_type == 'PeirceHandwrittenStyle':
                from gui.styles.peirce_handwritten_style import PeirceHandwrittenStyle
                style = PeirceHandwrittenStyle.from_dict(data)
            elif style_type == 'SowaCompliantStyle':
                # TODO: Implement SowaCompliantStyle
                from gui.styles.user_defined_style import UserDefinedStyle
                style = UserDefinedStyle.from_dict(data)
            else:
                from gui.styles.user_defined_style import UserDefinedStyle
                style = UserDefinedStyle.from_dict(data)
            
            self.register_style(style)
            return True
            
        except Exception as e:
            print(f"Failed to load style from {file_path}: {e}")
            return False
    
    def save_style_to_file(self, style_id: str, file_path: Path) -> bool:
        """Save a style to JSON file."""
        style = self.get_style(style_id)
        if not style:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(style.to_dict(), f, indent=2, default=self._json_serializer)
            return True
            
        except Exception as e:
            print(f"Failed to save style to {file_path}: {e}")
            return False
    
    def discover_styles(self):
        """Discover and load styles from search paths."""
        for search_path in self._style_search_paths:
            if search_path.exists():
                for style_file in search_path.glob("*.json"):
                    self.load_style_from_file(style_file)
    
    def create_user_style(self, base_style_id: str, new_style_id: str, 
                         name: str, description: str) -> bool:
        """Create a new user-defined style based on an existing style."""
        base_style = self.get_style(base_style_id)
        if not base_style:
            return False
        
        try:
            from gui.styles.user_defined_style import UserDefinedStyle
            
            # Create new style by copying base style parameters
            user_style = UserDefinedStyle(new_style_id, name, description)
            user_style.copy_from_style(base_style)
            
            self.register_style(user_style)
            return True
            
        except Exception as e:
            print(f"Failed to create user style: {e}")
            return False
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for Qt objects."""
        if isinstance(obj, QColor):
            return {"r": obj.red(), "g": obj.green(), "b": obj.blue(), "a": obj.alpha()}
        elif isinstance(obj, Qt.PenStyle):
            return int(obj)
        elif isinstance(obj, QFont.Weight):
            return int(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Global style manager instance
STYLE_MANAGER = StyleManager()

# Initialize with default styles
def _initialize_default_styles():
    """Initialize the style manager with default styles."""
    try:
        # Register simple style as fallback
        from gui.simple_style_system import get_simple_style
        
        # Create a basic style wrapper for the simple style
        class SimpleStyleWrapper:
            def __init__(self, style_id, name, description, simple_style):
                self.style_id = style_id
                self.name = name
                self.description = description
                self._simple_style = simple_style
                
            def get_cut_style(self):
                return self._simple_style.cut_style
                
            def get_ligature_style(self):
                return self._simple_style.ligature_style
                
            def get_vertex_style(self):
                return self._simple_style.vertex_style
                
            def get_predicate_style(self):
                return self._simple_style.predicate_style
                
            def get_label_style(self):
                return self._simple_style.label_style
                
            def get_layout_style(self):
                return self._simple_style.layout_style
        
        # Register default style
        default_style = SimpleStyleWrapper(
            "dau_compliant", 
            "Dau Compliant", 
            "Default Dau-compliant style",
            get_simple_style("default")
        )
        STYLE_MANAGER.register_style(default_style)
        STYLE_MANAGER.set_current_style("dau_compliant")
        
    except Exception as e:
        print(f"Warning: Failed to initialize default styles: {e}")

# Initialize styles on import
_initialize_default_styles()


def get_current_style() -> Optional[DiagramStyle]:
    """Convenience function to get current active style."""
    return STYLE_MANAGER.get_current_style()


def set_style(style_id: str) -> bool:
    """Convenience function to set active style."""
    return STYLE_MANAGER.set_current_style(style_id)
