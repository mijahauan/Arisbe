"""
Graph Builder Palette

Provides drag-and-drop palette for composing existential graphs.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem,
                               QDialog, QLineEdit, QSpinBox, QFormLayout,
                               QDialogButtonBox, QTextEdit, QGroupBox)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QFont, QColor


class PredicatePropertiesDialog(QDialog):
    """Dialog for setting predicate properties"""
    
    def __init__(self, parent=None, predicate_name="", arity=1):
        super().__init__(parent)
        self.setWindowTitle("Predicate Properties")
        self.setModal(True)
        
        layout = QFormLayout()
        
        # Predicate name
        self.name_edit = QLineEdit(predicate_name)
        layout.addRow("Name:", self.name_edit)
        
        # Arity (number of arguments)
        self.arity_spin = QSpinBox()
        self.arity_spin.setMinimum(0)
        self.arity_spin.setMaximum(10)
        self.arity_spin.setValue(arity)
        layout.addRow("Arity:", self.arity_spin)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        
    def get_properties(self):
        """Get the predicate properties"""
        return {
            'name': self.name_edit.text(),
            'arity': self.arity_spin.value()
        }


class DraggableListItem(QListWidgetItem):
    """List item that can be dragged to create graph elements"""
    
    def __init__(self, text, element_type, data=None):
        super().__init__(text)
        self.element_type = element_type
        self.element_data = data or {}
        
        # Set item properties
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)


class GraphBuilderPalette(QWidget):
    """Palette for building existential graphs with drag-and-drop"""
    
    # Signals
    element_requested = Signal(str, dict)  # element_type, properties
    clif_translation_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the palette UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Graph Builder Palette")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Basic Elements Group
        basic_group = QGroupBox("Basic Elements")
        basic_layout = QVBoxLayout()
        
        # Element list
        self.element_list = QListWidget()
        self.element_list.setDragDropMode(QListWidget.DragOnly)
        self.element_list.setDefaultDropAction(Qt.CopyAction)
        
        # Add basic elements
        self.add_palette_items()
        
        basic_layout.addWidget(self.element_list)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Tools Group
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()
        
        # Custom predicate button
        custom_pred_btn = QPushButton("Create Custom Predicate")
        custom_pred_btn.clicked.connect(self.create_custom_predicate)
        tools_layout.addWidget(custom_pred_btn)
        
        # CLIF translation button
        clif_btn = QPushButton("Show CLIF Translation")
        clif_btn.clicked.connect(self.clif_translation_requested.emit)
        tools_layout.addWidget(clif_btn)
        
        # Validate graph button
        validate_btn = QPushButton("Validate Graph")
        validate_btn.clicked.connect(self.validate_current_graph)
        tools_layout.addWidget(validate_btn)
        
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        # Instructions
        instructions = QLabel(
            "Drag elements to the canvas to build your graph.\n"
            "Double-click predicates to edit properties.\n"
            "Connect ligatures to predicates for identity."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(instructions)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def add_palette_items(self):
        """Add items to the palette"""
        # Basic elements
        elements = [
            ("Cut (Context)", "cut", {"type": "cut"}),
            ("Predicate", "predicate", {"name": "Predicate", "arity": 1}),
            ("Line of Identity", "ligature", {"type": "identity"}),
            ("Constant", "constant", {"name": "Constant"}),
        ]
        
        for text, element_type, data in elements:
            item = DraggableListItem(text, element_type, data)
            self.element_list.addItem(item)
            
        # Common predicates
        common_predicates = [
            ("Person", 1),
            ("Mortal", 1),
            ("Human", 1),
            ("Loves", 2),
            ("Gives", 3),
            ("Between", 3),
        ]
        
        for name, arity in common_predicates:
            data = {"name": name, "arity": arity, "type": "predicate"}
            item = DraggableListItem(f"{name}({arity})", "predicate", data)
            self.element_list.addItem(item)
            
    def create_custom_predicate(self):
        """Create a custom predicate"""
        dialog = PredicatePropertiesDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            props = dialog.get_properties()
            
            # Add to palette
            data = {
                "name": props['name'],
                "arity": props['arity'],
                "type": "predicate"
            }
            
            text = f"{props['name']}({props['arity']})"
            item = DraggableListItem(text, "predicate", data)
            self.element_list.addItem(item)
            
            # Signal that element was created
            self.element_requested.emit("predicate", data)
            
    def validate_current_graph(self):
        """Validate the current graph structure"""
        # This would connect to the main graph validation system
        # For now, just emit a signal
        self.clif_translation_requested.emit()
        
    def startDrag(self, supportedActions):
        """Handle drag start from palette"""
        current_item = self.element_list.currentItem()
        
        if not isinstance(current_item, DraggableListItem):
            return
            
        # Create drag data
        mime_data = QMimeData()
        mime_data.setText(f"{current_item.element_type}:{current_item.text()}")
        
        # Store element data
        mime_data.setData("application/x-eg-element", 
                         str(current_item.element_data).encode())
        
        # Create drag pixmap
        pixmap = self.create_drag_pixmap(current_item)
        
        # Start drag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        # Execute drag
        drag.exec(Qt.CopyAction)
        
    def create_drag_pixmap(self, item):
        """Create a pixmap for dragging"""
        # Create a simple pixmap representation
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw based on element type
        if item.element_type == "cut":
            painter.setPen(QColor(150, 100, 150))
            painter.setBrush(QColor(200, 150, 200, 100))
            painter.drawEllipse(5, 5, 90, 20)
            
        elif item.element_type == "predicate":
            painter.setPen(QColor(100, 150, 200))
            painter.setBrush(QColor(150, 200, 255))
            painter.drawRoundedRect(5, 5, 90, 20, 5, 5)
            
        elif item.element_type == "ligature":
            painter.setPen(QColor(50, 50, 50))
            painter.drawLine(10, 15, 90, 15)
            
        elif item.element_type == "constant":
            painter.setPen(QColor(200, 100, 100))
            painter.setBrush(QColor(255, 150, 150))
            painter.drawRect(5, 5, 90, 20)
            
        # Draw text
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, item.text())
        
        painter.end()
        return pixmap

