#!/usr/bin/env python3
"""
Peirce Graphics Adapter

This module converts Peirce rendering instructions to PySide6 graphics items.
It bridges the gap between the layout engine's rendering instructions and
the existing graphics items system.
"""

from typing import Dict, List, Any, Tuple
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QPen, QBrush, QColor, QFont

class PeirceGraphicsAdapter:
    """
    Converts Peirce rendering instructions to PySide6 graphics items.
    """
    
    def __init__(self, scene):
        self.scene = scene
        self.graphics_items = {}
    
    def create_graphics_from_instructions(self, rendering_instructions: Dict[str, Any]) -> Dict[str, QGraphicsItem]:
        """
        Create PySide6 graphics items from Peirce rendering instructions.
        
        Args:
            rendering_instructions: Instructions from PeirceLayoutEngine
            
        Returns:
            Dictionary mapping element IDs to graphics items
        """
        self.graphics_items.clear()
        
        # Process elements (contexts and predicates)
        for element_data in rendering_instructions.get('elements', []):
            item = self._create_element_item(element_data)
            if item:
                element_id = element_data.get('id', 'unknown')
                self.graphics_items[element_id] = item
                self.scene.addItem(item)
        
        # Process ligatures (lines of identity)
        for ligature_data in rendering_instructions.get('ligatures', []):
            item = self._create_ligature_item(ligature_data)
            if item:
                ligature_id = ligature_data.get('id', 'unknown')
                self.graphics_items[ligature_id] = item
                self.scene.addItem(item)
        
        return self.graphics_items
    
    def _create_element_item(self, element_data: Dict[str, Any]) -> QGraphicsItem:
        """Create a graphics item for an element (context or predicate)."""
        element_type = element_data.get('type', 'unknown')
        element_id = element_data.get('id', 'unknown')
        
        if element_type == 'context':
            return self._create_context_item(element_data)
        elif element_type == 'predicate':
            return self._create_predicate_item(element_data)
        else:
            print(f"Warning: Unknown element type {element_type} for {element_id}")
            return None
    
    def _create_context_item(self, element_data: Dict[str, Any]) -> QGraphicsItem:
        """Create a graphics item for a context (cut or sheet)."""
        shape = element_data.get('shape', {})
        style = element_data.get('style', {})
        z_index = element_data.get('z_index', 0)
        
        # Extract shape properties
        shape_type = shape.get('type', 'rectangle')
        x = shape.get('x', 0)
        y = shape.get('y', 0)
        width = shape.get('width', 100)
        height = shape.get('height', 100)
        corner_radius = shape.get('corner_radius', 0)
        
        # Extract style properties
        fill_color = QColor(style.get('fill_color', '#FFFFFF'))
        stroke_color = QColor(style.get('stroke_color', '#000000'))
        line_width = style.get('line_width', 1.0)
        opacity = style.get('opacity', 1.0)
        
        # Create appropriate graphics item
        if shape_type == 'oval' or corner_radius > 0:
            # Create ellipse for cuts
            item = QGraphicsEllipseItem(x, y, width, height)
        else:
            # Create rectangle for sheet
            item = QGraphicsRectItem(x, y, width, height)
        
        # Apply styling
        pen = QPen(stroke_color, line_width)
        brush = QBrush(fill_color)
        item.setPen(pen)
        item.setBrush(brush)
        item.setOpacity(opacity)
        item.setZValue(z_index)
        
        return item
    
    def _create_predicate_item(self, element_data: Dict[str, Any]) -> QGraphicsItem:
        """Create a graphics item for a predicate."""
        position = element_data.get('position', (0, 0))
        size = element_data.get('size', (80, 40))
        text = element_data.get('text', 'P')
        style = element_data.get('style', {})
        text_style = element_data.get('text_style', {})
        z_index = element_data.get('z_index', 0)
        
        x, y = position
        width, height = size
        
        # Create text item
        item = QGraphicsTextItem(text)
        
        # Apply text styling
        font_family = text_style.get('font_family', 'Arial')
        font_size = text_style.get('font_size', 14)
        font_weight = text_style.get('font_weight', 'normal')
        text_color = QColor(style.get('text_color', '#000000'))
        
        font = QFont(font_family, font_size)
        if font_weight == 'bold':
            font.setBold(True)
        
        item.setFont(font)
        item.setDefaultTextColor(text_color)
        
        # Position the text item
        item.setPos(x, y)
        item.setZValue(z_index)
        
        # Center the text within the allocated size
        text_rect = item.boundingRect()
        offset_x = (width - text_rect.width()) / 2
        offset_y = (height - text_rect.height()) / 2
        item.setPos(x + offset_x, y + offset_y)
        
        return item
    
    def _create_ligature_item(self, ligature_data: Dict[str, Any]) -> QGraphicsItem:
        """Create a graphics item for a ligature (line of identity)."""
        start = ligature_data.get('start', (0, 0))
        end = ligature_data.get('end', (0, 0))
        style = ligature_data.get('style', {})
        z_index = ligature_data.get('z_index', 0)
        
        start_x, start_y = start
        end_x, end_y = end
        
        # Create line item
        item = QGraphicsLineItem(start_x, start_y, end_x, end_y)
        
        # Apply styling
        stroke_color = QColor(style.get('stroke_color', '#000000'))
        line_width = style.get('line_width', 3.0)
        line_cap = style.get('line_cap', 'round')
        
        pen = QPen(stroke_color, line_width)
        if line_cap == 'round':
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        item.setPen(pen)
        item.setZValue(z_index)
        
        return item
    
    def update_element_names(self, egrf_doc):
        """Update predicate names from EGRF data."""
        # This method can be used to update predicate text with actual names from EGRF
        for element_data in egrf_doc.logical_elements:
            if element_data.logical_type == "relation":
                element_id = element_data.id
                name = element_data.properties.get('name', 'unnamed')
                
                # Find corresponding graphics item and update text
                if element_id in self.graphics_items:
                    item = self.graphics_items[element_id]
                    if isinstance(item, QGraphicsTextItem):
                        item.setPlainText(name)

def test_peirce_graphics_adapter():
    """Test the Peirce graphics adapter."""
    print("Peirce Graphics Adapter created successfully")
    print("Ready to convert rendering instructions to PySide6 graphics items")

if __name__ == "__main__":
    test_peirce_graphics_adapter()

