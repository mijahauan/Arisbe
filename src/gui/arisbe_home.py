#!/usr/bin/env python3
"""
Arisbe Home - Clean entry point to Organon, Ergasterion, and Agon

Provides a unified entry point with visual doorways to each component,
using only clean architecture without legacy code references.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Add src directory to path for clean imports
sys.path.append(str(Path(__file__).parent.parent))

from gui.organon.main_window import OrganonMainWindow


class WorkingRoom(QFrame):
    """Visual representation of a working room within the Arisbe home."""

    room_entered = Signal(str)  # Emits room name

    def __init__(
        self,
        room_name: str,
        title: str,
        description: str,
        help_text: str,
        room_type: str = "study",
    ):
        super().__init__()
        self.room_name = room_name
        self.room_type = room_type
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setMinimumSize(320, 420)
        self.setMaximumSize(380, 480)

        # Room-specific styling based on function
        room_colors = {
            "library": "#8B4513",  # Brown - Organon (library/study)
            "workshop": "#228B22",  # Forest Green - Ergasterion (workshop)
            "gameroom": "#B22222",  # Fire Brick - Agon (game room)
        }

        color = room_colors.get(room_type, "#696969")
        self.setStyleSheet(
            f"""
            WorkingRoom {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: #f5f5f5;
            }}
            WorkingRoom:hover {{
                background-color: #e8e8e8;
                border-color: {color};
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Room title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Room description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 11))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        desc_label.setStyleSheet("color: #333; margin-bottom: 15px;")
        layout.addWidget(desc_label)

        # Enter button
        enter_btn = QPushButton(f"Enter {room_name}")
        enter_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        enter_btn.setMinimumHeight(40)
        enter_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """
        )
        enter_btn.clicked.connect(lambda: self.room_entered.emit(room_name))
        layout.addWidget(enter_btn)

        # Help text
        help_area = QTextEdit()
        help_area.setPlainText(help_text)
        help_area.setFont(QFont("Arial", 9))
        help_area.setReadOnly(True)
        help_area.setMaximumHeight(120)
        help_area.setStyleSheet(
            """
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )
        layout.addWidget(help_area)


class ArisbeHome(QMainWindow):
    """Main Arisbe home interface with doorways to three components."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe - Existential Graph Research Environment")
        self.setMinimumSize(1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_label = QLabel("Arisbe")
        header_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(header_label)

        subtitle_label = QLabel("Existential Graph Research Environment")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        main_layout.addWidget(subtitle_label)

        # Three working rooms
        rooms_layout = QHBoxLayout()
        rooms_layout.setSpacing(30)

        # Organon - Exploration and viewing
        organon_room = WorkingRoom(
            "Organon",
            "📚 Organon",
            "Explore and examine existential graphs. View synchronic diagrams, "
            "diachronic histories, and corpus materials.",
            "The Organon provides read-only exploration of EG diagrams and their "
            "transformation histories. Browse the corpus, examine metadata, "
            "export to various formats, and study the logical structure.",
            "library",
        )
        organon_room.room_entered.connect(self.enter_organon)
        rooms_layout.addWidget(organon_room)

        # Ergasterion - Composition and practice
        ergasterion_room = WorkingRoom(
            "Ergasterion",
            "🔨 Ergasterion",
            "Compose and edit existential graphs. Practice transformations "
            "and build new graph utterances.",
            "The Ergasterion provides interactive graph editing and transformation "
            "practice. Create new graphs, apply formal rules (DC+/DC-, INS/ERA, IT+/IT-), "
            "and build graph utterances following Peirce-Dau formalism.",
            "workshop",
        )
        ergasterion_room.room_entered.connect(self.enter_ergasterion)
        rooms_layout.addWidget(ergasterion_room)

        # Agon - Reasoning and games
        agon_room = WorkingRoom(
            "Agon",
            "⚔️ Agon",
            "Engage in logical reasoning through the Endoporeutic Game. "
            "Test hypotheses and explore logical consequences.",
            "The Agon provides the Endoporeutic Game framework where Proposer "
            "and Skeptic engage in logical dialogue. Test domain models, "
            "explore competing hypotheses, and validate logical arguments.",
            "gameroom",
        )
        agon_room.room_entered.connect(self.enter_agon)
        rooms_layout.addWidget(agon_room)

        main_layout.addLayout(rooms_layout)

        # Footer
        footer_label = QLabel(
            "Select a working room to begin your exploration of existential graphs"
        )
        footer_label.setFont(QFont("Arial", 10))
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: #95a5a6; margin-top: 20px;")
        main_layout.addWidget(footer_label)

        # Initialize component windows (but don't show them)
        self.organon_window = None
        self.ergasterion_window = None
        self.agon_window = None

    def enter_organon(self):
        """Launch Organon for exploration and viewing."""
        if self.organon_window is None:
            self.organon_window = OrganonMainWindow()

        self.organon_window.show()
        self.organon_window.raise_()
        self.organon_window.activateWindow()

    def enter_ergasterion(self):
        """Launch Ergasterion for composition and practice."""
        # TODO: Implement clean Ergasterion using gui components
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Ergasterion",
            "Ergasterion (composition/practice) will be implemented using clean GUI components.\n\n"
            "This will provide interactive graph editing and transformation practice.",
        )

    def enter_agon(self):
        """Launch Agon for reasoning and games."""
        # TODO: Implement clean Agon using gui components
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Agon",
            "Agon (reasoning/games) will be implemented using clean GUI components.\n\n"
            "This will provide the Endoporeutic Game framework for logical dialogue.",
        )


def main():
    """Main entry point for Arisbe."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Arisbe")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Arisbe Research")

    # Create and show home window
    home = ArisbeHome()
    home.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
