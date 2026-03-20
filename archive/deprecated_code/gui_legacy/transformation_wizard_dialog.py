"""
Interactive transformation wizard dialog for step-by-step EGI transformations.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chapter21_transformation_wizards import TransformationRuleType, WizardStep


class TransformationWizardDialog(QDialog):
    """Interactive dialog for step-by-step transformation guidance."""

    def __init__(self, wizard, rule_name, source_egi, parent=None):
        super().__init__(parent)
        self.wizard = wizard
        self.rule_name = rule_name
        self.source_egi = source_egi
        self.result = None

        self.setWindowTitle(f"Transformation Wizard - {rule_name}")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.update_step_display()

    def setup_ui(self):
        """Set up the wizard dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"🧙‍♂️ {self.rule_name} Transformation Wizard")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(len(WizardStep))
        layout.addWidget(self.progress)

        # Main content area
        content_layout = QHBoxLayout()

        # Left: Steps list
        steps_group = QGroupBox("Wizard Steps")
        steps_layout = QVBoxLayout(steps_group)

        self.steps_list = QListWidget()
        self.populate_steps_list()
        steps_layout.addWidget(self.steps_list)

        content_layout.addWidget(steps_group, 1)

        # Right: Current step details
        details_group = QGroupBox("Current Step")
        details_layout = QVBoxLayout(details_group)

        self.step_description = QLabel()
        self.step_description.setWordWrap(True)
        details_layout.addWidget(self.step_description)

        self.step_content = QTextEdit()
        self.step_content.setReadOnly(True)
        details_layout.addWidget(self.step_content)

        # Interactive controls area
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        details_layout.addWidget(self.controls_widget)

        content_layout.addWidget(details_group, 2)

        layout.addLayout(content_layout)

        # Button bar
        button_layout = QHBoxLayout()

        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_btn)

        button_layout.addStretch()

        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_btn)

        self.execute_btn = QPushButton("🚀 Execute Transformation")
        self.execute_btn.clicked.connect(self.execute_transformation)
        self.execute_btn.setVisible(False)
        button_layout.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def populate_steps_list(self):
        """Populate the steps list widget."""
        step_names = {
            WizardStep.RULE_SELECTION: "1. Rule Selection",
            WizardStep.AREA_SELECTION: "2. Area Selection",
            WizardStep.ELEMENT_SELECTION: "3. Element Selection",
            WizardStep.POSITION_SELECTION: "4. Position Selection",
            WizardStep.PREVIEW: "5. Preview Changes",
            WizardStep.EXECUTE: "6. Execute Transformation",
        }

        for step in WizardStep:
            if step in step_names:
                item = QListWidgetItem(step_names[step])
                item.setData(Qt.UserRole, step)
                self.steps_list.addItem(item)

    def update_step_display(self):
        """Update the display for the current wizard step."""
        current_step = self.wizard.state.current_step

        # Update progress
        step_index = list(WizardStep).index(current_step)
        self.progress.setValue(step_index + 1)

        # Highlight current step in list
        for i in range(self.steps_list.count()):
            item = self.steps_list.item(i)
            step = item.data(Qt.UserRole)
            if step == current_step:
                item.setSelected(True)
                self.steps_list.setCurrentItem(item)
                break

        # Update step description and content
        self.update_step_content(current_step)

        # Update button states
        self.update_buttons()

    def update_step_content(self, step):
        """Update content for the current step."""
        # Clear previous controls
        for i in reversed(range(self.controls_layout.count())):
            self.controls_layout.itemAt(i).widget().setParent(None)

        if step == WizardStep.RULE_SELECTION:
            self.step_description.setText(
                f"Selected transformation rule: {self.rule_name}"
            )
            content = f"Rule: {self.rule_name}\n"
            content += f"Type: {self.wizard.state.rule_type.value if self.wizard.state.rule_type else 'Unknown'}\n\n"
            content += self.get_rule_description()

        elif step == WizardStep.AREA_SELECTION:
            self.step_description.setText("Select the target area for transformation")
            content = "Choose where to apply the transformation:\n\n"

            # Add area selection controls
            area_label = QLabel("Target Area:")
            self.controls_layout.addWidget(area_label)

            self.area_combo = QComboBox()
            self.area_combo.addItem("Sheet (main area)", "sheet")
            for cut in self.source_egi.Cut:
                self.area_combo.addItem(f"Cut area: {cut.id}", str(cut.id))
            self.area_combo.currentTextChanged.connect(self.on_area_selected)
            self.controls_layout.addWidget(self.area_combo)

            content += f"Available areas:\n"
            content += f"• Sheet (main area) - {len(self.source_egi.area.get(self.source_egi.sheet, set()))} elements\n"
            for cut in self.source_egi.Cut:
                cut_contents = len(self.source_egi.area.get(cut.id, set()))
                content += f"• {cut.id} - {cut_contents} elements\n"

        elif step == WizardStep.ELEMENT_SELECTION:
            self.step_description.setText("Select elements to transform (if any)")
            content = "Choose which elements to include in the transformation:\n\n"

            # Add element selection controls
            if self.rule_name == "DC+":
                selection_label = QLabel("Elements to enclose:")
                self.controls_layout.addWidget(selection_label)

                self.element_group = QButtonGroup()

                # Option for empty double cut
                empty_radio = QRadioButton("Create empty double cut")
                empty_radio.setChecked(True)
                self.element_group.addButton(empty_radio, 0)
                self.controls_layout.addWidget(empty_radio)

                # Option for all elements
                all_radio = QRadioButton("Enclose all elements in area")
                self.element_group.addButton(all_radio, 1)
                self.controls_layout.addWidget(all_radio)

                # Individual element checkboxes
                if self.source_egi.V or self.source_egi.E:
                    individual_radio = QRadioButton("Select specific elements:")
                    self.element_group.addButton(individual_radio, 2)
                    self.controls_layout.addWidget(individual_radio)

                    self.element_checkboxes = []
                    for vertex in self.source_egi.V:
                        cb = QCheckBox(f"Vertex: {vertex.id}")
                        cb.setEnabled(False)
                        self.element_checkboxes.append(cb)
                        self.controls_layout.addWidget(cb)

                    for edge in self.source_egi.E:
                        cb = QCheckBox(f"Edge: {edge.id}")
                        cb.setEnabled(False)
                        self.element_checkboxes.append(cb)
                        self.controls_layout.addWidget(cb)

                    individual_radio.toggled.connect(
                        self.on_individual_selection_toggled
                    )

                self.element_group.buttonClicked.connect(
                    self.on_element_selection_changed
                )

            elif self.rule_name == "INS":
                # INS insertion type selection
                insertion_label = QLabel("What to insert:")
                self.controls_layout.addWidget(insertion_label)

                self.insertion_group = QButtonGroup()

                # Subgraph insertion
                subgraph_radio = QRadioButton("Subgraph (closed graph structure)")
                subgraph_radio.setChecked(True)
                self.insertion_group.addButton(subgraph_radio, 0)
                self.controls_layout.addWidget(subgraph_radio)

                # Edge insertion
                edge_radio = QRadioButton(
                    "Edge (with relation name and vertex connections)"
                )
                self.insertion_group.addButton(edge_radio, 1)
                self.controls_layout.addWidget(edge_radio)

                # Vertex insertion
                vertex_radio = QRadioButton("Vertex (single vertex in area)")
                self.insertion_group.addButton(vertex_radio, 2)
                self.controls_layout.addWidget(vertex_radio)

                # Cut insertion
                cut_radio = QRadioButton("Cut (positive or negative enclosure)")
                self.insertion_group.addButton(cut_radio, 3)
                self.controls_layout.addWidget(cut_radio)

                self.insertion_group.buttonClicked.connect(
                    self.on_insertion_type_changed
                )

                # Add details section for insertion specifications
                self.insertion_details = QWidget()
                self.insertion_details_layout = QVBoxLayout(self.insertion_details)
                self.controls_layout.addWidget(self.insertion_details)

                # Initially show subgraph details
                self.update_insertion_details(0)

            content += f"Current EGI elements:\n"
            content += f"Vertices: {len(self.source_egi.V)}\n"
            content += f"Edges: {len(self.source_egi.E)}\n"
            content += f"Cuts: {len(self.source_egi.Cut)}\n\n"
            if self.rule_name == "DC+":
                content += "DC+ can enclose any subset of elements or create an empty double cut."
            elif self.rule_name == "INS":
                content += "INS can insert subgraphs, edges, vertices, or cuts into negatively-enclosed areas."

        elif step == WizardStep.POSITION_SELECTION:
            self.step_description.setText("Specify position for the transformation")
            content = "Choose how to position the transformation:\n\n"

            # Add position controls
            pos_label = QLabel("Position type:")
            self.controls_layout.addWidget(pos_label)

            self.position_combo = QComboBox()
            self.position_combo.addItem(
                "Whole area - Apply to entire selected area", "whole_area"
            )
            self.position_combo.addItem(
                "Selected elements - Apply to specific elements", "selected_elements"
            )
            self.position_combo.addItem(
                "Empty spot - Create new structure", "empty_spot"
            )
            self.position_combo.currentTextChanged.connect(self.on_position_selected)
            self.controls_layout.addWidget(self.position_combo)

            content += "Position options:\n"
            content += "• Whole area - Apply to entire selected area\n"
            content += "• Selected elements - Apply to specific elements\n"
            content += "• Empty spot - Create new structure\n"

        elif step == WizardStep.PREVIEW:
            self.step_description.setText("Preview the transformation result")
            content = "Transformation preview:\n\n"
            if self.rule_name == "DC+":
                content += "Will create:\n"
                content += "• Outer cut (dc_outer)\n"
                content += "• Inner cut (dc_inner) inside outer cut\n"

                # Show what will be enclosed based on selections
                if (
                    hasattr(self, "element_group")
                    and self.element_group.checkedId() == 0
                ):
                    content += "• Empty double cut (no elements enclosed)\n"
                elif (
                    hasattr(self, "element_group")
                    and self.element_group.checkedId() == 1
                ):
                    content += "• All elements in selected area will be enclosed\n"
                else:
                    content += "• Selected elements will be enclosed\n"

        elif step == WizardStep.EXECUTE:
            self.step_description.setText("Ready to execute transformation")
            content = "All steps completed. Ready to apply the transformation.\n\n"
            content += f"Rule: {self.rule_name}\n"

            # Show selected configuration
            if hasattr(self, "area_combo"):
                content += f"Target: {self.area_combo.currentText()}\n"
            else:
                content += f"Target: Sheet area\n"

            if hasattr(self, "element_group"):
                if self.element_group.checkedId() == 0:
                    content += f"Elements: Empty double cut\n"
                elif self.element_group.checkedId() == 1:
                    content += f"Elements: All elements in area\n"
                else:
                    content += f"Elements: Selected elements\n"

        self.step_content.setPlainText(content)

    def get_rule_description(self):
        """Get description for the selected rule."""
        descriptions = {
            "DC+": "Double Cut Insertion - Creates nested cuts around selected elements",
            "DC-": "Double Cut Erasure - Removes nested double cut patterns",
            "IT+": "Iteration - Copies subgraph to same context",
            "IT-": "Deiteration - Removes duplicate subgraph",
            "ERA": "Erasure - Removes elements from negative areas",
            "INS": "Insertion - Adds elements to positive areas",
        }
        return descriptions.get(self.rule_name, "Transformation rule")

    def update_buttons(self):
        """Update button states based on current step."""
        current_step = self.wizard.state.current_step
        step_list = list(WizardStep)
        current_index = step_list.index(current_step)

        # Back button
        self.back_btn.setEnabled(current_index > 0)

        # Next/Execute buttons
        if current_step == WizardStep.EXECUTE:
            self.next_btn.setVisible(False)
            self.execute_btn.setVisible(True)
        else:
            self.next_btn.setVisible(True)
            self.execute_btn.setVisible(False)
            self.next_btn.setEnabled(self.wizard.state.can_proceed)

    def go_back(self):
        """Go to previous wizard step."""
        step_list = list(WizardStep)
        current_index = step_list.index(self.wizard.state.current_step)
        if current_index > 0:
            self.wizard.state.current_step = step_list[current_index - 1]
            self.wizard.state.can_proceed = True
            self.update_step_display()

    def go_next(self):
        """Go to next wizard step."""
        if self.wizard.advance_step():
            self.wizard.state.can_proceed = True  # Allow proceeding for demo
            self.update_step_display()

    def execute_transformation(self):
        """Execute the transformation."""
        try:
            # Fix the area mapping issue first
            if not self.source_egi.area:
                # Create minimal area mapping with sheet
                from dataclasses import replace

                from frozendict import frozendict

                self.source_egi = replace(
                    self.source_egi,
                    area=frozendict({self.source_egi.sheet: frozenset()}),
                )
                self.wizard.source_egi = self.source_egi

            self.result = self.wizard.execute_transformation()

            if self.result.success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Transformation {self.rule_name} completed successfully!",
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Transformation Failed", f"Error: {self.result.error_message}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transformation error: {str(e)}")

    def on_area_selected(self):
        """Handle area selection change."""
        self.wizard.state.can_proceed = True
        self.update_buttons()

    def on_element_selection_changed(self):
        """Handle element selection change."""
        self.wizard.state.can_proceed = True
        self.update_buttons()

    def on_individual_selection_toggled(self, checked):
        """Enable/disable individual element checkboxes."""
        if hasattr(self, "element_checkboxes"):
            for cb in self.element_checkboxes:
                cb.setEnabled(checked)
        self.wizard.state.can_proceed = True
        self.update_buttons()

    def on_position_selected(self):
        """Handle position selection change."""
        self.wizard.state.can_proceed = True
        self.update_buttons()

    def on_insertion_type_changed(self):
        """Handle insertion type selection change."""
        if hasattr(self, "insertion_group"):
            selected_id = self.insertion_group.checkedId()
            self.update_insertion_details(selected_id)
        self.wizard.state.can_proceed = True
        self.update_buttons()

    def update_insertion_details(self, insertion_type_id):
        """Update the insertion details section based on selected type."""
        # Clear previous details
        for i in reversed(range(self.insertion_details_layout.count())):
            self.insertion_details_layout.itemAt(i).widget().setParent(None)

        if insertion_type_id == 0:  # Subgraph
            details_label = QLabel("Subgraph Details:")
            self.insertion_details_layout.addWidget(details_label)

            subgraph_combo = QComboBox()
            subgraph_combo.addItem("Simple vertex-edge structure", "simple")
            subgraph_combo.addItem("Predefined subgraph pattern", "pattern")
            subgraph_combo.addItem("Copy from existing area", "copy")
            self.insertion_details_layout.addWidget(subgraph_combo)

        elif insertion_type_id == 1:  # Edge
            details_label = QLabel("Edge Details:")
            self.insertion_details_layout.addWidget(details_label)

            from PySide6.QtWidgets import QLineEdit

            relation_label = QLabel("Relation name:")
            self.insertion_details_layout.addWidget(relation_label)

            self.relation_input = QLineEdit()
            self.relation_input.setPlaceholderText(
                "e.g., 'loves', 'is', 'connected_to'"
            )
            self.insertion_details_layout.addWidget(self.relation_input)

            vertices_label = QLabel("Connect to vertices (comma-separated IDs):")
            self.insertion_details_layout.addWidget(vertices_label)

            self.vertices_input = QLineEdit()
            self.vertices_input.setPlaceholderText(
                "e.g., 'v1,v2' or 'new_vertex_1,new_vertex_2'"
            )
            self.insertion_details_layout.addWidget(self.vertices_input)

        elif insertion_type_id == 2:  # Vertex
            details_label = QLabel("Vertex Details:")
            self.insertion_details_layout.addWidget(details_label)

            from PySide6.QtWidgets import QLineEdit

            label_input = QLineEdit()
            label_input.setPlaceholderText("Optional vertex label")
            self.insertion_details_layout.addWidget(label_input)

        elif insertion_type_id == 3:  # Cut
            details_label = QLabel("Cut Details:")
            self.insertion_details_layout.addWidget(details_label)

            cut_type_combo = QComboBox()
            cut_type_combo.addItem("Positive cut (even nesting)", "positive")
            cut_type_combo.addItem("Negative cut (odd nesting)", "negative")
            self.insertion_details_layout.addWidget(cut_type_combo)

    def get_result(self):
        """Get the transformation result."""
        return self.result
