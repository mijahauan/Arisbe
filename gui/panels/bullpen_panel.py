"""
EG-HG Bullpen Panel

Comprehensive tool panel for graph composition with CLIF integration,
baseline graph generation, and interactive editing capabilities.
"""

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QTextEdit, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QComboBox, QSpinBox, QLineEdit, QGroupBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter

# Import CLIF corpus
from gui.data.clif_corpus import get_all_examples, get_examples_by_difficulty, get_rhema_templates

# Import existing EG system
try:
    from bullpen import GraphCompositionTool
    from clif_parser import CLIFParser
    from clif_generator import CLIFGenerator
    from graph import EGGraph
    EG_SYSTEM_AVAILABLE = True
except ImportError:
    EG_SYSTEM_AVAILABLE = False


class CLIFSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for CLIF text"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()
        
    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules for CLIF"""
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.blue)
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = ["forall", "exists", "and", "or", "not", "if", "iff", "=", "<=", ">=", "<", ">"]
        self.keyword_rules = [(f"\\b{keyword}\\b", keyword_format) for keyword in keywords]
        
        # Parentheses
        paren_format = QTextCharFormat()
        paren_format.setForeground(Qt.darkMagenta)
        paren_format.setFontWeight(QFont.Bold)
        self.paren_rules = [("\\(", paren_format), ("\\)", paren_format)]
        
        # Variables (single letters)
        var_format = QTextCharFormat()
        var_format.setForeground(Qt.darkGreen)
        var_format.setFontItalic(True)
        self.var_rules = [("\\b[a-z]\\b", var_format)]
        
        # Predicates (capitalized words)
        pred_format = QTextCharFormat()
        pred_format.setForeground(Qt.darkRed)
        pred_format.setFontWeight(QFont.Bold)
        self.pred_rules = [("\\b[A-Z][a-zA-Z]*\\b", pred_format)]
        
    def highlightBlock(self, text):
        """Apply highlighting to a block of text"""
        import re
        
        # Apply all rules
        for pattern, format_obj in (self.keyword_rules + self.paren_rules + 
                                   self.var_rules + self.pred_rules):
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)


class CLIFParsingThread(QThread):
    """Background thread for CLIF parsing"""
    
    parsing_complete = Signal(object)  # EGGraph
    parsing_error = Signal(str)
    
    def __init__(self, clif_text):
        super().__init__()
        self.clif_text = clif_text
        
    def run(self):
        """Parse CLIF in background thread"""
        try:
            if EG_SYSTEM_AVAILABLE:
                parser = CLIFParser()
                graph = parser.parse(self.clif_text)
                self.parsing_complete.emit(graph)
            else:
                # Mock parsing for development - create realistic graph structure
                import time
                time.sleep(1)  # Simulate parsing time
                
                # Create mock graph based on CLIF content
                mock_graph = self.create_mock_graph_from_clif(self.clif_text)
                self.parsing_complete.emit(mock_graph)
        except Exception as e:
            self.parsing_error.emit(str(e))
            
    def create_mock_graph_from_clif(self, clif_text):
        """Create a realistic mock graph structure from CLIF text"""
        import re
        
        clif_lower = clif_text.lower().strip()
        
        # Create mock graph object with proper structure
        mock_graph = type('MockGraph', (), {
            'contexts': [],
            'nodes': [],
            'ligatures': [],
            'variables': set(),
            'constants': set()
        })()
        
        # Parse simple predicate expressions like (Person Socrates)
        simple_pred_pattern = r'\(\s*(\w+)\s+(\w+)\s*\)'
        simple_matches = re.findall(simple_pred_pattern, clif_text)
        
        if simple_matches:
            # Handle simple predicates - no cuts needed
            for i, (predicate, constant) in enumerate(simple_matches):
                # Create two nodes: predicate and constant
                pred_node = {
                    'name': predicate,
                    'type': 'predicate',
                    'args': [constant],
                    'position': {'x': -80, 'y': -20 + i * 60},
                    'id': f'pred_{i}'
                }
                
                const_node = {
                    'name': constant,
                    'type': 'constant',
                    'args': [],
                    'position': {'x': 80, 'y': -20 + i * 60},
                    'id': f'const_{i}'
                }
                
                mock_graph.nodes.extend([pred_node, const_node])
                mock_graph.constants.add(constant)
                
                # Create ligature connecting them
                ligature = {
                    'id': f'lig_{i}',
                    'type': 'identity',
                    'connects': [f'pred_{i}', f'const_{i}'],
                    'variable': constant.lower(),  # For internal tracking
                    'start': {'x': -40, 'y': 0 + i * 60},
                    'end': {'x': 40, 'y': 0 + i * 60},
                    'path': 'straight'  # Can be 'curved', 'angled', 'bridge'
                }
                
                mock_graph.ligatures.append(ligature)
                
            return mock_graph
        
        # Handle existential quantification
        if 'exists' in clif_lower:
            # Extract variables from exists clause
            exists_pattern = r'exists\s*\(\s*([^)]+)\s*\)'
            exists_match = re.search(exists_pattern, clif_lower)
            
            if exists_match:
                variables = [v.strip() for v in exists_match.group(1).split()]
                mock_graph.variables.update(variables)
                
                # Only add context if there are multiple predicates or complex structure
                if 'and' in clif_lower or len(variables) > 1:
                    mock_graph.contexts.append({
                        'type': 'existential',
                        'variables': variables,
                        'bounds': {'x': -200, 'y': -100, 'width': 400, 'height': 150}
                    })
        
        # Detect predicates in complex expressions
        predicates = []
        pred_positions = [(-120, -20), (40, -20), (-80, 20), (80, 20)]  # Multiple positions
        
        predicate_patterns = [
            (r'person\s*\(\s*(\w+)\s*\)', 'Person'),
            (r'mortal\s*\(\s*(\w+)\s*\)', 'Mortal'),
            (r'human\s*\(\s*(\w+)\s*\)', 'Human'),
            (r'rational\s*\(\s*(\w+)\s*\)', 'Rational'),
            (r'loves\s*\(\s*(\w+)\s+(\w+)\s*\)', 'Loves'),
            (r'gives\s*\(\s*(\w+)\s+(\w+)\s+(\w+)\s*\)', 'Gives')
        ]
        
        for i, (pattern, name) in enumerate(predicate_patterns):
            matches = re.findall(pattern, clif_lower)
            for j, match in enumerate(matches):
                if isinstance(match, tuple):
                    args = list(match)
                else:
                    args = [match]
                    
                pos_index = (i + j) % len(pred_positions)
                x, y = pred_positions[pos_index]
                
                predicates.append({
                    'name': name,
                    'type': 'predicate',
                    'args': args,
                    'position': {'x': x, 'y': y},
                    'id': f'pred_{len(predicates)}'
                })
                
                mock_graph.variables.update(args)
        
        mock_graph.nodes = predicates
        
        # Create ligatures for shared variables (only for complex expressions)
        if len(predicates) > 1:
            ligatures = []
            variables_used = set()
            
            for pred in predicates:
                variables_used.update(pred['args'])
            
            for var in variables_used:
                # Find predicates that share this variable
                pred_with_var = []
                for pred in predicates:
                    if var in pred['args']:
                        pred_with_var.append(pred)
                
                # Create ligatures between predicates sharing variables
                if len(pred_with_var) > 1:
                    for k in range(len(pred_with_var) - 1):
                        pred1 = pred_with_var[k]
                        pred2 = pred_with_var[k + 1]
                        
                        # Calculate connection points
                        start_x = pred1['position']['x'] + 40
                        start_y = pred1['position']['y'] + 15
                        end_x = pred2['position']['x'] + 40
                        end_y = pred2['position']['y'] + 15
                        
                        ligature = {
                            'id': f'lig_{len(ligatures)}',
                            'type': 'identity',
                            'connects': [pred1['id'], pred2['id']],
                            'variable': var,
                            'start': {'x': start_x, 'y': start_y},
                            'end': {'x': end_x, 'y': end_y},
                            'path': 'straight'
                        }
                        
                        ligatures.append(ligature)
            
            mock_graph.ligatures = ligatures
        
        return mock_graph


class BullpenPanel(QDockWidget):
    """Main Bullpen tool panel for graph composition"""
    
    # Signals
    graph_created = Signal(object)  # EGGraph
    status_message = Signal(str)
    clif_parsed = Signal(object)  # Parsed graph
    
    def __init__(self):
        super().__init__("Bullpen Tools")
        
        # Initialize EG system components
        if EG_SYSTEM_AVAILABLE:
            self.bullpen = GraphCompositionTool()
            self.clif_parser = CLIFParser()
            self.clif_generator = CLIFGenerator()
        else:
            self.bullpen = None
            self.clif_parser = None
            self.clif_generator = None
            
        # Current state
        self.current_clif = ""
        self.current_graph = None
        self.parsing_thread = None
        
        # Setup UI
        self.setup_ui()
        self.load_clif_corpus()
        
    def setup_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget for different tools
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # CLIF Corpus Tab
        self.create_clif_corpus_tab()
        
        # CLIF Editor Tab
        self.create_clif_editor_tab()
        
        # Graph Builder Tab
        self.create_graph_builder_tab()
        
        # Rhema Constructor Tab
        self.create_rhema_constructor_tab()
        
        # Status and controls
        self.create_status_controls(layout)
        
    def create_clif_corpus_tab(self):
        """Create the CLIF corpus browser tab"""
        corpus_widget = QWidget()
        layout = QVBoxLayout(corpus_widget)
        
        # Difficulty filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Difficulty:"))
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["All", "Beginner", "Intermediate", "Advanced"])
        self.difficulty_combo.currentTextChanged.connect(self.filter_corpus)
        filter_layout.addWidget(self.difficulty_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Corpus tree
        self.corpus_tree = QTreeWidget()
        self.corpus_tree.setHeaderLabels(["CLIF Examples", "Description"])
        self.corpus_tree.itemDoubleClicked.connect(self.load_corpus_example)
        layout.addWidget(self.corpus_tree)
        
        # Load button
        load_btn = QPushButton("Load Selected Example")
        load_btn.clicked.connect(self.load_selected_example)
        layout.addWidget(load_btn)
        
        self.tab_widget.addTab(corpus_widget, "CLIF Corpus")
        
    def create_clif_editor_tab(self):
        """Create the CLIF editor tab"""
        editor_widget = QWidget()
        layout = QVBoxLayout(editor_widget)
        
        # CLIF text editor
        editor_label = QLabel("CLIF Expression:")
        editor_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(editor_label)
        
        self.clif_editor = QTextEdit()
        self.clif_editor.setFont(QFont("Consolas", 11))
        self.clif_editor.setPlaceholderText("Enter CLIF expression here...\nExample: (forall (x) (if (Person x) (Mortal x)))")
        
        # Add syntax highlighting
        self.highlighter = CLIFSyntaxHighlighter(self.clif_editor.document())
        
        layout.addWidget(self.clif_editor)
        
        # Editor controls
        editor_controls = QHBoxLayout()
        
        parse_btn = QPushButton("Parse to Graph")
        parse_btn.clicked.connect(self.parse_clif)
        editor_controls.addWidget(parse_btn)
        
        validate_btn = QPushButton("Validate CLIF")
        validate_btn.clicked.connect(self.validate_clif)
        editor_controls.addWidget(validate_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clif_editor.clear)
        editor_controls.addWidget(clear_btn)
        
        layout.addLayout(editor_controls)
        
        # Parsing progress
        self.parse_progress = QProgressBar()
        self.parse_progress.setVisible(False)
        layout.addWidget(self.parse_progress)
        
        self.tab_widget.addTab(editor_widget, "CLIF Editor")
        
    def create_graph_builder_tab(self):
        """Create the interactive graph builder tab"""
        builder_widget = QWidget()
        layout = QVBoxLayout(builder_widget)
        
        # Quick start section
        quick_group = QGroupBox("Quick Start")
        quick_layout = QGridLayout(quick_group)
        
        blank_btn = QPushButton("Blank Sheet")
        blank_btn.clicked.connect(self.create_blank_sheet)
        quick_layout.addWidget(blank_btn, 0, 0)
        
        template_btn = QPushButton("From Template")
        template_btn.clicked.connect(self.show_template_dialog)
        quick_layout.addWidget(template_btn, 0, 1)
        
        layout.addWidget(quick_group)
        
        # Manual construction section with palette
        manual_group = QGroupBox("Graph Elements Palette")
        manual_layout = QVBoxLayout(manual_group)
        
        # Import and add the palette
        try:
            from gui.widgets.graph_builder_palette import GraphBuilderPalette
            self.graph_palette = GraphBuilderPalette()
            self.graph_palette.element_requested.connect(self.handle_element_request)
            self.graph_palette.clif_translation_requested.connect(self.translate_to_clif)
            manual_layout.addWidget(self.graph_palette)
        except ImportError:
            # Fallback if palette not available
            manual_layout.addWidget(QLabel("Graph Builder Palette not available"))
            
        layout.addWidget(manual_group)
        
        self.tab_widget.addTab(builder_widget, "Graph Builder")
        
    def create_rhema_constructor_tab(self):
        """Create the Peirce rhema constructor tab"""
        rhema_widget = QWidget()
        layout = QVBoxLayout(rhema_widget)
        
        # Rhema selection
        rhema_group = QGroupBox("Peirce's Rhemas")
        rhema_layout = QVBoxLayout(rhema_group)
        
        # Rhema list
        self.rhema_list = QListWidget()
        self.load_rhema_templates()
        rhema_layout.addWidget(self.rhema_list)
        
        # Rhema details
        self.rhema_details = QLabel("Select a rhema to see its structure")
        self.rhema_details.setWordWrap(True)
        self.rhema_details.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        rhema_layout.addWidget(self.rhema_details)
        
        # Connect selection
        self.rhema_list.itemSelectionChanged.connect(self.show_rhema_details)
        
        layout.addWidget(rhema_group)
        
        # Argument binding
        binding_group = QGroupBox("Argument Binding")
        binding_layout = QGridLayout(binding_group)
        
        self.arg_edits = []
        for i in range(4):  # Support up to 4 arguments
            binding_layout.addWidget(QLabel(f"Arg {i+1}:"), i, 0)
            edit = QLineEdit()
            edit.setPlaceholderText(f"Variable or constant")
            self.arg_edits.append(edit)
            binding_layout.addWidget(edit, i, 1)
            
        layout.addWidget(binding_group)
        
        # Create rhema button
        create_rhema_btn = QPushButton("Create Rhema Graph")
        create_rhema_btn.clicked.connect(self.create_rhema_graph)
        layout.addWidget(create_rhema_btn)
        
        self.tab_widget.addTab(rhema_widget, "Rhema Constructor")
        
    def create_status_controls(self, layout):
        """Create status and control section"""
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.status_label)
        
        # Generate CLIF button
        generate_layout = QHBoxLayout()
        generate_clif_btn = QPushButton("Generate CLIF from Graph")
        generate_clif_btn.clicked.connect(self.generate_clif_from_graph)
        generate_layout.addWidget(generate_clif_btn)
        
        export_btn = QPushButton("Export Graph")
        export_btn.clicked.connect(self.export_graph)
        generate_layout.addWidget(export_btn)
        
        layout.addLayout(generate_layout)
        
    def load_clif_corpus(self):
        """Load the CLIF corpus into the tree widget"""
        self.corpus_tree.clear()
        
        if self.difficulty_combo.currentText() == "All":
            examples = get_all_examples()
        else:
            level = self.difficulty_combo.currentText().lower()
            examples = get_examples_by_difficulty(level)
            
        for category, subcategories in examples.items():
            category_item = QTreeWidgetItem([category, ""])
            category_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            
            if isinstance(subcategories, dict):
                for subcat, items in subcategories.items():
                    subcat_item = QTreeWidgetItem([subcat, ""])
                    subcat_item.setFont(0, QFont("Arial", 9, QFont.Bold))
                    
                    for item_data in items:
                        if len(item_data) == 2:
                            # Standard (clif, description) format
                            clif, description = item_data
                            item = QTreeWidgetItem([clif, description])
                            item.setData(0, Qt.UserRole, clif)
                        elif len(item_data) == 3:
                            # Rhema (name, pattern, args) format
                            name, pattern, args = item_data
                            clif = f"{name}({', '.join(args)})"
                            item = QTreeWidgetItem([clif, pattern])
                            item.setData(0, Qt.UserRole, clif)
                        else:
                            # Skip malformed items
                            continue
                            
                        subcat_item.addChild(item)
                        
                    category_item.addChild(subcat_item)
            else:
                # Direct list of items
                for item_data in subcategories:
                    if len(item_data) == 2:
                        clif, description = item_data
                        item = QTreeWidgetItem([clif, description])
                        item.setData(0, Qt.UserRole, clif)
                        category_item.addChild(item)
                    elif len(item_data) == 3:
                        # Rhema format
                        name, pattern, args = item_data
                        clif = f"{name}({', '.join(args)})"
                        item = QTreeWidgetItem([clif, pattern])
                        item.setData(0, Qt.UserRole, clif)
                        category_item.addChild(item)
                    
            self.corpus_tree.addTopLevelItem(category_item)
            
        self.corpus_tree.expandAll()
        
    def load_rhema_templates(self):
        """Load Peirce's rhema templates"""
        templates = get_rhema_templates()
        
        for category, rhemas in templates.items():
            for name, pattern, args in rhemas:
                item = QListWidgetItem(f"{name}: {pattern}")
                item.setData(Qt.UserRole, (name, pattern, args))
                self.rhema_list.addItem(item)
                
    def filter_corpus(self):
        """Filter corpus by difficulty level"""
        self.load_clif_corpus()
        
    def load_corpus_example(self, item):
        """Load selected corpus example into editor"""
        clif_text = item.data(0, Qt.UserRole)
        if clif_text:
            self.clif_editor.setPlainText(clif_text)
            self.tab_widget.setCurrentIndex(1)  # Switch to editor tab
            self.status_message.emit(f"Loaded example: {clif_text[:50]}...")
            
    def load_selected_example(self):
        """Load the currently selected example"""
        current = self.corpus_tree.currentItem()
        if current:
            self.load_corpus_example(current)
            
    def show_rhema_details(self):
        """Show details of selected rhema"""
        current = self.rhema_list.currentItem()
        if current:
            name, pattern, args = current.data(Qt.UserRole)
            details = f"<b>{name}</b><br>"
            details += f"Pattern: {pattern}<br>"
            details += f"Arguments: {', '.join(args)}<br><br>"
            details += f"Example: {name}({', '.join(args)})"
            self.rhema_details.setText(details)
            
            # Update argument labels
            for i, edit in enumerate(self.arg_edits):
                if i < len(args):
                    edit.setPlaceholderText(args[i])
                    edit.setVisible(True)
                else:
                    edit.setVisible(False)
                    
    def parse_clif(self):
        """Parse CLIF text to create graph"""
        clif_text = self.clif_editor.toPlainText().strip()
        if not clif_text:
            QMessageBox.warning(self, "Warning", "Please enter CLIF text to parse")
            return
            
        self.current_clif = clif_text
        self.status_label.setText("Parsing CLIF...")
        self.parse_progress.setVisible(True)
        self.parse_progress.setRange(0, 0)  # Indeterminate progress
        
        # Start parsing in background thread
        self.parsing_thread = CLIFParsingThread(clif_text)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.parsing_error.connect(self.on_parsing_error)
        self.parsing_thread.start()
        
    def on_parsing_complete(self, graph):
        """Handle successful CLIF parsing"""
        self.parse_progress.setVisible(False)
        self.current_graph = graph
        self.graph_created.emit(graph)
        self.clif_parsed.emit(graph)
        self.status_label.setText("CLIF parsed successfully")
        self.status_message.emit("Graph created from CLIF expression")
        
    def on_parsing_error(self, error):
        """Handle CLIF parsing error"""
        self.parse_progress.setVisible(False)
        self.status_label.setText("Parsing failed")
        QMessageBox.critical(self, "Parsing Error", f"Failed to parse CLIF:\n{error}")
        
    def validate_clif(self):
        """Validate CLIF syntax"""
        clif_text = self.clif_editor.toPlainText().strip()
        if not clif_text:
            QMessageBox.information(self, "Validation", "No CLIF text to validate")
            return
            
        # TODO: Implement actual CLIF validation
        # For now, just check basic syntax
        if clif_text.count('(') != clif_text.count(')'):
            QMessageBox.warning(self, "Validation", "Unmatched parentheses")
        else:
            QMessageBox.information(self, "Validation", "CLIF syntax appears valid")
            
    def create_blank_sheet(self):
        """Create a blank sheet of assertion"""
        try:
            if EG_SYSTEM_AVAILABLE and self.bullpen:
                graph = self.bullpen.create_blank_sheet()
            else:
                # Mock blank sheet
                graph = type('BlankGraph', (), {
                    'contexts': [],
                    'nodes': [],
                    'ligatures': []
                })()
                
            self.current_graph = graph
            self.graph_created.emit(graph)
            self.status_message.emit("Created blank sheet of assertion")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create blank sheet:\n{e}")
            
    def show_template_dialog(self):
        """Show template selection dialog"""
        # TODO: Implement template dialog
        QMessageBox.information(self, "Templates", "Template selection coming soon!")
        
    def add_predicate(self):
        """Add a predicate to the current graph"""
        name = self.pred_name_edit.text().strip()
        arity = self.pred_arity_spin.value()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a predicate name")
            return
            
        # TODO: Add predicate to current graph
        self.status_message.emit(f"Added predicate: {name}/{arity}")
        self.pred_name_edit.clear()
        
    def add_context(self):
        """Add a context (cut) to the graph"""
        # TODO: Add context to current graph
        self.status_message.emit("Added context (cut)")
        
    def add_ligature(self):
        """Add a line of identity to the graph"""
        # TODO: Add ligature to current graph
        self.status_message.emit("Added line of identity")
        
    def create_rhema_graph(self):
        """Create graph from selected rhema"""
        current = self.rhema_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Please select a rhema")
            return
            
        name, pattern, args = current.data(Qt.UserRole)
        
        # Get argument bindings
        bindings = []
        for i, edit in enumerate(self.arg_edits):
            if i < len(args) and edit.text().strip():
                bindings.append(edit.text().strip())
            elif i < len(args):
                bindings.append(f"var{i+1}")  # Default variable
                
        # TODO: Create graph from rhema
        self.status_message.emit(f"Created rhema graph: {name}")
        
    def generate_clif_from_graph(self):
        """Generate CLIF text from current graph"""
        if not self.current_graph:
            QMessageBox.information(self, "Info", "No graph to generate CLIF from")
            return
            
        try:
            if EG_SYSTEM_AVAILABLE and self.clif_generator:
                clif_text = self.clif_generator.generate(self.current_graph)
            else:
                # Mock CLIF generation
                clif_text = "(exists (x) (Person x))"
                
            self.clif_editor.setPlainText(clif_text)
            self.tab_widget.setCurrentIndex(1)  # Switch to editor
            self.status_message.emit("Generated CLIF from graph")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate CLIF:\n{e}")
            
    def export_graph(self):
        """Export the current graph"""
        if not self.current_graph:
            QMessageBox.information(self, "Info", "No graph to export")
            return
            
        # TODO: Implement graph export
        QMessageBox.information(self, "Export", "Graph export coming soon!")
        
    def closeEvent(self, event):
        """Handle panel close event"""
        if self.parsing_thread and self.parsing_thread.isRunning():
            self.parsing_thread.quit()
            self.parsing_thread.wait()
        event.accept()


    def handle_element_request(self, element_type, properties):
        """Handle element creation request from palette"""
        try:
            if element_type == "predicate":
                self.add_predicate_with_properties(properties)
            elif element_type == "cut":
                self.add_context()
            elif element_type == "ligature":
                self.add_ligature()
            elif element_type == "constant":
                self.add_constant_with_properties(properties)
                
            self.status_message.emit(f"Added {element_type} to graph")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add {element_type}:\n{e}")
            
    def add_predicate_with_properties(self, properties):
        """Add a predicate with specific properties"""
        # Create mock predicate node
        predicate_data = {
            'name': properties.get('name', 'Predicate'),
            'type': 'predicate',
            'arity': properties.get('arity', 1),
            'args': [f'x{i}' for i in range(properties.get('arity', 1))],
            'position': {'x': 0, 'y': 0},  # Will be positioned by user
            'id': f'pred_{len(getattr(self, "created_elements", []))}'
        }
        
        # Signal to add to graph
        self.element_created.emit("predicate", predicate_data)
        
    def add_constant_with_properties(self, properties):
        """Add a constant with specific properties"""
        constant_data = {
            'name': properties.get('name', 'Constant'),
            'type': 'constant',
            'args': [],
            'position': {'x': 0, 'y': 0},
            'id': f'const_{len(getattr(self, "created_elements", []))}'
        }
        
        # Signal to add to graph
        self.element_created.emit("constant", constant_data)
        
    def translate_to_clif(self):
        """Translate current graph to CLIF"""
        try:
            if hasattr(self, 'current_graph') and self.current_graph:
                # Mock CLIF translation for now
                clif_text = self.generate_clif_from_graph(self.current_graph)
                
                # Show in a dialog
                dialog = QDialog(self)
                dialog.setWindowTitle("CLIF Translation")
                dialog.setModal(True)
                
                layout = QVBoxLayout()
                
                label = QLabel("Current graph translates to:")
                layout.addWidget(label)
                
                text_edit = QTextEdit()
                text_edit.setPlainText(clif_text)
                text_edit.setReadOnly(True)
                text_edit.setFont(QFont("Consolas", 11))
                layout.addWidget(text_edit)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok)
                buttons.accepted.connect(dialog.accept)
                layout.addWidget(buttons)
                
                dialog.setLayout(layout)
                dialog.resize(400, 300)
                dialog.exec()
            else:
                QMessageBox.information(self, "Translation", "No graph to translate")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Translation failed:\n{e}")
            
    def generate_clif_from_graph(self, graph):
        """Generate CLIF from graph structure"""
        if not graph:
            return "()"
            
        # Simple mock translation
        if hasattr(graph, 'nodes') and graph.nodes:
            if len(graph.nodes) == 1:
                node = graph.nodes[0]
                if node.get('type') == 'predicate':
                    name = node.get('name', 'Predicate')
                    args = node.get('args', ['x'])
                    if len(args) == 1:
                        return f"({name} {args[0]})"
                    else:
                        return f"({name} {' '.join(args)})"
                        
            elif len(graph.nodes) == 2:
                # Check if it's a simple predicate-constant pair
                pred_node = None
                const_node = None
                
                for node in graph.nodes:
                    if node.get('type') == 'predicate':
                        pred_node = node
                    elif node.get('type') == 'constant':
                        const_node = node
                        
                if pred_node and const_node:
                    pred_name = pred_node.get('name', 'Predicate')
                    const_name = const_node.get('name', 'Constant')
                    return f"({pred_name} {const_name})"
                    
            # Multiple predicates with variables
            if hasattr(graph, 'variables') and graph.variables:
                variables = list(graph.variables)
                predicates = []
                
                for node in graph.nodes:
                    if node.get('type') == 'predicate':
                        name = node.get('name', 'Predicate')
                        args = node.get('args', ['x'])
                        pred_str = f"({name} {' '.join(args)})"
                        predicates.append(pred_str)
                        
                if len(predicates) > 1:
                    pred_conjunction = f"(and {' '.join(predicates)})"
                    if variables:
                        var_list = ' '.join(variables)
                        return f"(exists ({var_list}) {pred_conjunction})"
                    else:
                        return pred_conjunction
                elif len(predicates) == 1:
                    return predicates[0]
                    
        return "()"  # Empty graph

