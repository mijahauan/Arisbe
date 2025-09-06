#!/usr/bin/env python3
"""
Arisbe Home - Central doorway interface to Organon, Ergasterion, and Agon

Provides a unified entry point with visual doorways to each component,
descriptions, and integrated help system.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QSplitter, QStackedWidget
)

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from organon.main_window import OrganonMainWindow
from organon_ergasterion_protocol import GraphHandoffPackage, OrganonErgasterionBridge


class WorkingRoom(QFrame):
    """Visual representation of a working room within the Arisbe home."""
    
    room_entered = Signal(str)  # Emits room name
    
    def __init__(self, room_name: str, title: str, description: str, 
                 help_text: str, room_type: str = "study"):
        super().__init__()
        self.room_name = room_name
        self.room_type = room_type
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setMinimumSize(320, 420)
        self.setMaximumSize(380, 480)
        
        # Room-specific styling based on function
        room_colors = {
            "library": "#8B4513",    # Brown - Organon (library/study)
            "workshop": "#228B22",   # Forest Green - Ergasterion (workshop)
            "gameroom": "#B22222"    # Fire Brick - Agon (game room)
        }
        
        color = room_colors.get(room_type, "#696969")
        
        # Set room styling with warm, homey feel
        self.setStyleSheet(f"""
            WorkingRoom {{
                border: 2px solid {color};
                border-radius: 12px;
                background-color: #faf8f5;
                margin: 15px;
                background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><rect width="20" height="20" fill="%23faf8f5"/><rect width="1" height="1" x="10" y="10" fill="%23f0f0f0"/></svg>');
            }}
            WorkingRoom:hover {{
                background-color: #f5f2ed;
                border-color: {self._darken_color(color)};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
        
        self._setup_room_ui(title, description, help_text, color)
    
    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color for hover effect."""
        color = QColor(hex_color)
        return color.darker(120).name()
    
    def _setup_room_ui(self, title: str, description: str, help_text: str, color: str):
        """Set up the room UI with homey styling."""
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Room title with icon
        title_layout = QHBoxLayout()
        
        # Room-specific icon
        icon_label = QLabel()
        icon_pixmap = self._create_room_icon(color)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel(title)
        title_font = QFont("Georgia", 20)  # More homey serif font
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet(f"color: {color}; margin-left: 10px;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Room description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignTop)
        desc_font = QFont("Arial", 11)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: #4a4a4a; line-height: 1.5; margin: 10px 0;")
        
        # Usage notes
        help_label = QLabel(f"💡 {help_text}")
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignTop)
        help_font = QFont("Arial", 10)
        help_label.setFont(help_font)
        help_label.setStyleSheet("color: #666; font-style: italic; background-color: #f9f9f9; padding: 8px; border-radius: 4px;")
        
        # Enter room button
        enter_btn = QPushButton(f"🚪 Enter {title}")
        enter_btn.setMinimumHeight(45)
        enter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 12px;
                font-family: Arial;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(self._darken_color(color))};
                transform: translateY(1px);
            }}
        """)
        enter_btn.clicked.connect(lambda: self.room_entered.emit(self.room_name))
        
        # Add to layout
        layout.addLayout(title_layout)
        layout.addWidget(desc_label)
        layout.addWidget(help_label)
        layout.addStretch()
        layout.addWidget(enter_btn)
    
    def _create_room_icon(self, color: str) -> QPixmap:
        """Create a room-specific icon."""
        pixmap = QPixmap(52, 52)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Room-specific icons based on type
        if self.room_type == "library":
            # Book icon for Organon
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(color).darker(120), 2))
            painter.drawRect(12, 8, 28, 36)  # Book spine
            painter.drawLine(16, 12, 16, 40)  # Book detail
            painter.drawLine(20, 12, 20, 40)
        elif self.room_type == "workshop":
            # Hammer icon for Ergasterion
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(color).darker(120), 2))
            painter.drawRect(20, 10, 6, 20)   # Handle
            painter.drawRect(14, 8, 18, 8)    # Head
        elif self.room_type == "gameroom":
            # Trophy icon for Agon
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(color).darker(120), 2))
            painter.drawEllipse(16, 8, 20, 16)  # Cup
            painter.drawRect(24, 24, 4, 12)     # Stem
            painter.drawRect(18, 36, 16, 4)     # Base
        else:
            # Default circle
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(color).darker(120), 2))
            painter.drawEllipse(6, 6, 40, 40)
        
        painter.end()
        return pixmap


class ArisbeHomeWidget(QWidget):
    """Central home foyer with access to the three working rooms."""
    
    room_requested = Signal(str, dict)  # room_name, options
    
    def __init__(self):
        super().__init__()
        self.current_component = None
        self.component_widgets = {}
        
        self._setup_ui()
        self._create_rooms()
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with house image
        header_layout = QVBoxLayout()
        
        # House image and title section
        house_title_layout = QHBoxLayout()
        
        # House image
        house_image_label = QLabel()
        house_image_path = Path(__file__).parent.parent / "assets" / "arisbe_house.jpg"
        
        if house_image_path.exists():
            house_pixmap = QPixmap(str(house_image_path))
            # Scale image to reasonable size while maintaining aspect ratio
            scaled_pixmap = house_pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            house_image_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to text if image not found
            house_image_label.setText("🏠")
            house_image_label.setStyleSheet("font-size: 48px; color: #8B4513;")
        
        house_image_label.setAlignment(Qt.AlignCenter)
        
        # Title and subtitle
        title_section = QVBoxLayout()
        
        title_label = QLabel("Arisbe")
        title_font = QFont("Georgia", 36)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #8B4513; margin-bottom: 5px;")
        
        subtitle_label = QLabel("Home for Existential Graph Inquiry")
        subtitle_font = QFont("Georgia", 18)
        subtitle_font.setItalic(True)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #A0522D; margin-bottom: 15px;")
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        
        # Add house image and title to horizontal layout
        house_title_layout.addStretch()
        house_title_layout.addWidget(house_image_label)
        house_title_layout.addSpacing(20)
        house_title_layout.addLayout(title_section)
        house_title_layout.addStretch()
        
        # Introduction text
        intro_text = QLabel(
            "Welcome to your intellectual home. Named after Charles Sanders Peirce's residence "
            "in northeast New Jersey, this house contains three specialized working rooms "
            "for your Existential Graph inquiry. Choose which room to enter:"
        )
        intro_text.setWordWrap(True)
        intro_text.setAlignment(Qt.AlignCenter)
        intro_text.setStyleSheet("color: #495057; font-size: 12px; margin: 20px 0 30px 0;")
        
        header_layout.addLayout(house_title_layout)
        header_layout.addWidget(intro_text)
        
        # Rooms container
        rooms_scroll = QScrollArea()
        rooms_scroll.setWidgetResizable(True)
        rooms_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        rooms_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        rooms_scroll.setStyleSheet("background-color: #f5f2ed; border: none;")  # Warm background
        
        rooms_widget = QWidget()
        self.rooms_layout = QHBoxLayout(rooms_widget)
        self.rooms_layout.setAlignment(Qt.AlignCenter)
        self.rooms_layout.setSpacing(25)
        
        rooms_scroll.setWidget(rooms_widget)
        
        # Add to main layout
        layout.addLayout(header_layout)
        layout.addWidget(rooms_scroll, 1)
    
    def _create_rooms(self):
        """Create the three working rooms."""
        
        # Organon - Library/Study Room
        organon_room = WorkingRoom(
            room_name="organon",
            title="Organon",
            description="Your personal library and study for browsing the corpus of existential graphs. "
                       "Explore your collection, view existing diagrams, and select items for deeper work.",
            help_text="Start here to browse your knowledge corpus. Use the three-panel interface to "
                     "navigate folders, preview graphs, and launch editing or practice sessions.",
            room_type="library"
        )
        
        # Ergasterion - Workshop Room  
        ergasterion_room = WorkingRoom(
            room_name="ergasterion",
            title="Ergasterion",
            description="Your creative workshop for hands-on diagram work. Create new existential graphs, "
                       "edit existing ones, and practice transformation rules with full constraint validation.",
            help_text="The interactive workspace where you compose and manipulate existential graphs. "
                     "Features spatial layout tools, constraint validation, and transformation rule enforcement.",
            room_type="workshop"
        )
        
        # Agon - Game Room
        agon_room = WorkingRoom(
            room_name="agon",
            title="Agon",
            description="Your competition space for logical challenges and endoporeutic games. "
                       "Test your understanding through structured exercises and friendly competition.",
            help_text="Coming soon: Interactive games and challenges to test your mastery of existential "
                     "graph logic and transformation rules. Compete with others or challenge yourself.",
            room_type="gameroom"
        )
        
        # Connect signals
        organon_room.room_entered.connect(self._handle_room_selection)
        ergasterion_room.room_entered.connect(self._handle_room_selection)
        agon_room.room_entered.connect(self._handle_room_selection)
        
        # Add to layout
        self.rooms_layout.addWidget(organon_room)
        self.rooms_layout.addWidget(ergasterion_room)
        self.rooms_layout.addWidget(agon_room)
    
    def _handle_room_selection(self, room_name: str):
        """Handle selection of a working room."""
        options = {}
        
        if room_name == "agon":
            # Agon is not yet implemented
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Agon Under Construction",
                "The Agon (competition arena) is being prepared for a future release. "
                "For now, visit the Organon to browse graphs or the Ergasterion to create and edit them."
            )
            return
        
        self.room_requested.emit(room_name, options)


class IntegratedArisbeWindow(QWidget):
    """Main window that integrates home, Organon, and Ergasterion."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe - Home for Existential Graph Inquiry")
        self.setGeometry(100, 100, 1400, 900)
        
        self.organon_widget = None
        self.ergasterion_instances = []
        
        self._setup_ui()
        self._setup_navigation()
    
    def _setup_ui(self):
        """Set up the integrated UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation bar
        self.nav_bar = QFrame()
        self.nav_bar.setFixedHeight(50)
        self.nav_bar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 2px solid #34495e;
            }
        """)
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(20, 10, 20, 10)
        
        # Home button
        self.home_btn = QPushButton("🏠 Return Home")
        self.home_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B4513;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: Georgia;
            }
            QPushButton:hover {
                background-color: #A0522D;
            }
        """)
        self.home_btn.clicked.connect(self._show_home)
        
        # Room indicators
        self.current_room_label = QLabel("Foyer")
        self.current_room_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; font-family: Georgia;")
        
        nav_layout.addWidget(self.home_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.current_room_label)
        
        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Home widget
        self.home_widget = ArisbeHomeWidget()
        self.home_widget.room_requested.connect(self._handle_room_request)
        
        self.stacked_widget.addWidget(self.home_widget)
        
        # Add to main layout
        layout.addWidget(self.nav_bar)
        layout.addWidget(self.stacked_widget, 1)
    
    def _setup_navigation(self):
        """Set up navigation between components."""
        # Start with home view
        self._show_home()
    
    def _show_home(self):
        """Show the home foyer interface."""
        self.stacked_widget.setCurrentWidget(self.home_widget)
        self.current_room_label.setText("Foyer")
    
    def _handle_room_request(self, room_name: str, options: dict):
        """Handle request to enter a room."""
        if room_name == "organon":
            self._enter_library(options)
        elif room_name == "ergasterion":
            self._enter_workshop(options)
    
    def _enter_library(self, options: dict):
        """Enter the Library (Organon)."""
        if not hasattr(self, 'organon_widget') or self.organon_widget is None:
            from src.organon.main_window import OrganonMainWindow
            self.organon_widget = OrganonMainWindow()
            
            # Connect handoff signal
            self.organon_widget.edit_in_ergasterion.connect(self._handle_library_to_workshop_handoff)
            
            self.stacked_widget.addWidget(self.organon_widget)
        
        # Check if we should refresh the current graph (e.g., after returning from Ergasterion)
        refresh_needed = options.get("refresh_graph", False)
        if refresh_needed and hasattr(self.organon_widget, 'refresh_current_graph'):
            self.organon_widget.refresh_current_graph()
        
        self.stacked_widget.setCurrentWidget(self.organon_widget)
        self.current_room_label.setText("📚 Organon")
    
    def _enter_workshop(self, options: dict):
        """Enter the Workshop (Ergasterion)."""
        if not hasattr(self, 'ergasterion_widget') or self.ergasterion_widget is None:
            from tools.drawing_editor_refactored import RefactoredDrawingEditor
            self.ergasterion_widget = RefactoredDrawingEditor()
            
            # Handle any handoff payload
            handoff_payload = options.get("handoff_payload")
            if handoff_payload:
                # Process handoff data if provided
                graph_dir = handoff_payload.get("graph_dir")
                if graph_dir:
                    self.ergasterion_widget.set_current_graph_dir(graph_dir)
                
                # Load EGI and EGDF data if available
                egi_data = handoff_payload.get("egi")
                egdf_data = handoff_payload.get("egdf")
                
                if egi_data or egdf_data:
                    self.ergasterion_widget.load_handoff_data(egi_data, egdf_data)
            
            self.stacked_widget.addWidget(self.ergasterion_widget)
        
        self.stacked_widget.setCurrentWidget(self.ergasterion_widget)
        self.current_room_label.setText("🔨 Ergasterion")
    
    def _handle_library_to_workshop_handoff(self, payload: dict):
        """Handle handoff from Library to Workshop."""
        # Launch Workshop with handoff data
        self._enter_workshop({"handoff_payload": payload})
