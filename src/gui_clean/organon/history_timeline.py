"""
History Timeline - Visual display of transformation sequence.

Shows the diachronic aspect of historical entities with:
- Linear sequence of states
- Transformation steps between states
- Current position indicator
- Clickable navigation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from universe_of_discourse import UniverseOfDiscourse
from egi_transformation_history import TransformationStep


class TimelineItem(QWidget):
    """
    Single state in the timeline.
    
    Visual representation:
    ┌─────────────────┐
    │  [STATE 5]      │  ← Bold if current
    │  DC+ on vertex  │  ← Description
    │  2025-10-09     │  ← Timestamp
    └─────────────────┘
    """
    
    clicked = Signal(str)  # Emits state_id
    
    def __init__(
        self,
        state_id: str,
        state_number: int,
        description: str,
        timestamp_str: str,
        is_current: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.state_id = state_id
        self.is_current = is_current
        
        self._setup_ui(state_number, description, timestamp_str)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_ui(self, state_number: int, description: str, timestamp_str: str):
        """Create the timeline item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(2)
        
        # State number
        state_label = QLabel(f"State {state_number}")
        if self.is_current:
            state_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        else:
            state_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(state_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Timestamp
        time_label = QLabel(timestamp_str)
        time_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(time_label)
        
        # Style the widget
        if self.is_current:
            self.setStyleSheet("""
                TimelineItem {
                    background-color: #e6f2ff;
                    border: 2px solid #0066cc;
                    border-radius: 4px;
                }
                TimelineItem:hover {
                    background-color: #d0e8ff;
                }
            """)
        else:
            self.setStyleSheet("""
                TimelineItem {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                TimelineItem:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                }
            """)
        
        self.setMinimumWidth(120)
        self.setMaximumWidth(200)
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.state_id)
        super().mousePressEvent(event)


class TransformationArrow(QWidget):
    """
    Arrow showing transformation between states.
    
    Visual:
    ──[DC+]──>
    
    Shows rule name and direction.
    """
    
    def __init__(
        self,
        step_id: str,
        rule_name: str,
        description: str,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.step_id = step_id
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Arrow with rule name
        arrow_text = f"─[{rule_name}]─>"
        arrow_label = QLabel(arrow_text)
        arrow_label.setStyleSheet("color: #666; font-family: monospace;")
        arrow_label.setToolTip(description)
        layout.addWidget(arrow_label)
        
        self.setMinimumWidth(80)
        self.setMaximumWidth(120)


class HistoryTimeline(QWidget):
    """
    Timeline view of transformation history.
    
    Shows:
    - Linear sequence of states
    - Transformation steps between states
    - Current position indicator
    - Clickable states for navigation
    
    Emits:
    - state_selected(state_id) when user clicks a state
    """
    
    state_selected = Signal(str)  # Emits state_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._current_uod: Optional[UniverseOfDiscourse] = None
        self._timeline_items = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the timeline UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Title
        title = QLabel("📜 Transformation History")
        title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 3px;")
        main_layout.addWidget(title)
        
        # Scrollable timeline area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(150)
        scroll.setMinimumHeight(120)
        
        # Timeline container (horizontal layout)
        self.timeline_container = QWidget()
        self.timeline_layout = QHBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(5, 5, 5, 5)
        self.timeline_layout.setSpacing(2)
        self.timeline_layout.addStretch()  # Start with stretch for empty state
        
        scroll.setWidget(self.timeline_container)
        main_layout.addWidget(scroll)
        
        # Initially hidden (shown when historical entity loaded)
        self.hide()
    
    def update_history(self, uod: UniverseOfDiscourse):
        """
        Update timeline with UoD history.
        
        Args:
            uod: The Universe of Discourse with history to display
        """
        self._current_uod = uod
        
        # Clear existing timeline
        self.clear()
        
        # Only show for historical UoDs
        if not uod.is_historical:
            self.hide()
            return
        
        self.show()
        
        history = uod.history
        if not history or not history.state_sequence:
            self.hide()
            return
        
        # Build timeline
        for i, state_id in enumerate(history.state_sequence):
            state = history.states.get(state_id)
            if not state:
                continue
            
            # Create state item
            timestamp_str = state.timestamp.strftime("%Y-%m-%d %H:%M")
            is_current = (state_id == history.current_state_id)
            
            item = TimelineItem(
                state_id=state_id,
                state_number=i + 1,
                description=state.description,
                timestamp_str=timestamp_str,
                is_current=is_current
            )
            item.clicked.connect(self._on_state_clicked)
            
            self.timeline_layout.addWidget(item)
            self._timeline_items.append(item)
            
            # Add transformation arrow if not last state
            if i < len(history.state_sequence) - 1:
                next_state_id = history.state_sequence[i + 1]
                step = self._find_step(state_id, next_state_id, history)
                
                if step:
                    arrow = TransformationArrow(
                        step_id=step.step_id,
                        rule_name=step.rule_name,
                        description=step.description
                    )
                    self.timeline_layout.addWidget(arrow)
        
        # Add stretch at end
        self.timeline_layout.addStretch()
    
    def _find_step(self, from_id: str, to_id: str, history) -> Optional[TransformationStep]:
        """
        Find transformation step between two states.
        
        Args:
            from_id: Source state ID
            to_id: Target state ID
            history: The transformation history
            
        Returns:
            TransformationStep if found, None otherwise
        """
        for step in history.transformations.values():
            if step.from_state_id == from_id and step.to_state_id == to_id:
                return step
        return None
    
    def _on_state_clicked(self, state_id: str):
        """Handle state click - emit signal for navigation."""
        self.state_selected.emit(state_id)
    
    def clear(self):
        """Clear all timeline items."""
        # Remove all widgets from layout
        while self.timeline_layout.count() > 0:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._timeline_items.clear()
        
        # Add initial stretch
        self.timeline_layout.addStretch()
    
    def get_current_state_id(self) -> Optional[str]:
        """Get currently selected state ID."""
        if self._current_entity and self._current_entity.history:
            return self._current_entity.history.current_state_id
        return None
