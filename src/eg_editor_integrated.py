#!/usr/bin/env python3
"""
Integrated EG Editor - Main Workflow with Validation & Transformation

Combines all Phase 1-3 components into a functional EG editor:
- Phase 1: Robust EGIF↔EG↔Diagram round-trip
- Phase 2: Selection-driven interaction architecture  
- Phase 3: Background validation and transformation logic

This is the main application that users will interact with.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Set, Dict, List, Optional, Tuple
import json

# Core EG components
from egi_core_dau import RelationalGraphWithCuts, ElementID
from egif_parser_dau import EGIFParser
from layout_engine_clean import CleanLayoutEngine
from content_driven_layout import ContentDrivenLayoutEngine
from diagram_renderer_clean import CleanDiagramRenderer
from tkinter_backend import TkinterCanvas

# Phase 3 validation and transformation
from eg_transformation_rules import EGTransformationEngine, TransformationRule
from background_validation_system import create_validation_system, ValidationLevel
from corpus_loader import CorpusLoader

class IntegratedEGEditor:
    """
    Main Arisbe application with three sub-applications:
    - Bullpen: Graph editor with Warmup/Practice modes
    - Browser: Graph collection viewer (placeholder)
    - Endoporeutic Game: Formal game implementation (placeholder)
    
    Features:
    - Tab-based navigation between applications
    - Mode switching within Bullpen
    - Professional interaction patterns
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arisbe - Existential Graphs Platform")
        self.root.geometry("1400x900")
        
        # Core systems
        self.layout_engine = ContentDrivenLayoutEngine()
        self.transformation_engine = EGTransformationEngine()
        self.validation_system = create_validation_system(ValidationLevel.STANDARD)
        self.corpus_loader = CorpusLoader()
        
        # Application state
        self.current_graph: Optional[RelationalGraphWithCuts] = None
        self.current_file: Optional[str] = None
        self.selected_elements: Set[ElementID] = set()
        self.undo_stack: List[RelationalGraphWithCuts] = []
        self.redo_stack: List[RelationalGraphWithCuts] = []
        
        # UI components
        self.canvas: Optional[TkinterCanvas] = None
        self.renderer: Optional[CleanDiagramRenderer] = None
        self.status_var = tk.StringVar(value="Ready")
        self.validation_text: Optional[tk.Text] = None
        
        # Create UI
        self._create_ui()
        
        # Load example
        self._load_example()
    
    def _create_ui(self):
        """Create the main application UI with hierarchical tabs."""
        
        # Menu bar
        self._create_menu()
        
        # Main application tabs (top level)
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === BULLPEN TAB ===
        self.bullpen_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.bullpen_frame, text="Bullpen")
        
        # Bullpen sub-tabs (Warmup/Practice modes)
        self.bullpen_notebook = ttk.Notebook(self.bullpen_frame)
        self.bullpen_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Warmup mode tab
        self.warmup_frame = ttk.Frame(self.bullpen_notebook)
        self.bullpen_notebook.add(self.warmup_frame, text="Warmup")
        
        # Practice mode tab
        self.practice_frame = ttk.Frame(self.bullpen_notebook)
        self.bullpen_notebook.add(self.practice_frame, text="Practice")
        
        # Create Warmup mode content (current editor)
        self._create_warmup_mode(self.warmup_frame)
        
        # Create Practice mode content (placeholder for now)
        self._create_practice_mode(self.practice_frame)
        
        # === BROWSER TAB (Placeholder) ===
        self.browser_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.browser_frame, text="Browser", state="disabled")
        
        placeholder_browser = ttk.Label(self.browser_frame, 
                                       text="Graph Browser\n(Coming Soon)", 
                                       font=('TkDefaultFont', 16),
                                       foreground='gray')
        placeholder_browser.pack(expand=True)
        
        # === ENDOPOREUTIC GAME TAB (Placeholder) ===
        self.game_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.game_frame, text="Endoporeutic Game", state="disabled")
        
        placeholder_game = ttk.Label(self.game_frame, 
                                    text="Endoporeutic Game\n(Coming Soon)", 
                                    font=('TkDefaultFont', 16),
                                    foreground='gray')
        placeholder_game.pack(expand=True)
        
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Mode indicator
        self.mode_var = tk.StringVar(value="Warmup Mode")
        ttk.Label(status_frame, textvariable=self.mode_var, foreground='blue').pack(side=tk.RIGHT, padx=5)
        
        # Bind tab change events
        self.bullpen_notebook.bind("<<NotebookTabChanged>>", self._on_mode_change)

    def _create_warmup_mode(self, parent):
        """Create Warmup mode interface (current editor functionality)."""
        
        # Main layout for warmup mode
        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Tools and validation
        left_frame = ttk.Frame(main_paned, width=350)
        main_paned.add(left_frame, weight=0)
        
        # Right panel: Canvas
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Create left panel (tools, validation)
        self._create_left_panel(left_frame)
        
        # Create right panel (canvas)
        self._create_right_panel(right_frame)
    
    def _create_practice_mode(self, parent):
        """Create Practice mode interface (rule-based editing)."""
        
        # Placeholder for Practice mode
        practice_label = ttk.Label(parent, 
                                  text="Practice Mode\n\nRule-based EG editing with formal validation\n(Implementation in progress)", 
                                  font=('TkDefaultFont', 14),
                                  foreground='darkblue',
                                  justify='center')
        practice_label.pack(expand=True)
        
        # Add some placeholder controls
        controls_frame = ttk.LabelFrame(parent, text="Formal Rules", padding=10)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(controls_frame, text="Iteration", state="disabled").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Deiteration", state="disabled").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Erasure", state="disabled").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Insertion", state="disabled").pack(side=tk.LEFT, padx=5)
    
    def _on_mode_change(self, event):
        """Handle mode switching between Warmup and Practice."""
        
        selected_tab = self.bullpen_notebook.tab(self.bullpen_notebook.select(), "text")
        
        if selected_tab == "Warmup":
            self.mode_var.set("Warmup Mode")
            self._update_status("Switched to Warmup mode - Creative composition and exploration")
        elif selected_tab == "Practice":
            self.mode_var.set("Practice Mode")
            self._update_status("Switched to Practice mode - Formal rule-based editing")
            
            # TODO: Validate current graph against formal rules when switching to Practice
            # TODO: Initialize Practice mode with current graph state

    
    def _create_menu(self):
        """Create application menu bar."""
        
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file, accelerator="Cmd+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Cmd+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Cmd+S")
        file_menu.add_command(label="Save As...", command=self._save_file_as, accelerator="Cmd+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export PNG...", command=self._export_png)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Cmd+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Cmd+Shift+Z")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self._select_all, accelerator="Cmd+A")
        edit_menu.add_command(label="Clear Selection", command=self._clear_selection)
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete Selected", command=self._delete_selected, accelerator="Delete")
        
        # Transform menu
        transform_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transform", menu=transform_menu)
        transform_menu.add_command(label="Insert Double Cut", command=lambda: self._apply_rule(TransformationRule.DOUBLE_CUT_INSERT))
        transform_menu.add_command(label="Delete Double Cut", command=lambda: self._apply_rule(TransformationRule.DOUBLE_CUT_DELETE))
        transform_menu.add_command(label="Insert Cut Around Selection", command=lambda: self._apply_rule(TransformationRule.CUT_INSERT))
        transform_menu.add_command(label="Delete Cut", command=lambda: self._apply_rule(TransformationRule.CUT_DELETE))
        transform_menu.add_separator()
        transform_menu.add_command(label="Erase Selection", command=lambda: self._apply_rule(TransformationRule.ERASURE))
        
        # Bind keyboard shortcuts
        self.root.bind('<Command-n>', lambda e: self._new_file())
        self.root.bind('<Command-o>', lambda e: self._open_file())
        self.root.bind('<Command-s>', lambda e: self._save_file())
        self.root.bind('<Command-z>', lambda e: self._undo())
        self.root.bind('<Command-y>', lambda e: self._redo())
        self.root.bind('<Command-a>', lambda e: self._select_all())
        self.root.bind('<Delete>', lambda e: self._delete_selected())
    
    def _create_left_panel(self, parent):
        """Create left panel with tools and validation."""
        
        # EGIF Input/Output (moved to top for prominence)
        egif_frame = ttk.LabelFrame(parent, text="EGIF Input/Output", padding=10)
        egif_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.egif_text = tk.Text(egif_frame, height=4, width=40)
        self.egif_text.pack(fill=tk.X)
        
        egif_buttons = ttk.Frame(egif_frame)
        egif_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(egif_buttons, text="Parse", command=self._parse_egif).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(egif_buttons, text="Generate", command=self._generate_egif).pack(side=tk.LEFT)
        
        # Corpus Examples (compact layout)
        corpus_frame = ttk.LabelFrame(parent, text="Load Examples", padding=10)
        corpus_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Category selection (more compact)
        category_frame = ttk.Frame(corpus_frame)
        category_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(category_frame, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="All")
        categories = ["All"] + self.corpus_loader.get_categories()
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly", width=12)
        category_combo.pack(side=tk.LEFT, padx=(5, 0))
        category_combo.bind('<<ComboboxSelected>>', self._on_category_change)
        
        # Load button (more prominent)
        ttk.Button(category_frame, text="Load", 
                  command=self._load_corpus_example).pack(side=tk.RIGHT)
        
        # Example selection (smaller height)
        self.example_listbox = tk.Listbox(corpus_frame, height=3)
        self.example_listbox.pack(fill=tk.X, pady=(5, 0))
        self.example_listbox.bind('<Double-Button-1>', self._load_corpus_example)
        
        # Populate initial examples
        self._update_corpus_examples()
        
        # Selection info
        selection_frame = ttk.LabelFrame(parent, text="Selection", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.selection_listbox = tk.Listbox(selection_frame, height=3)
        self.selection_listbox.pack(fill=tk.X)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        actions = [
            ("Add Predicate", self._add_predicate),
            ("Add Line of Identity", self._add_loi),
            ("Add Cut", self._add_cut),
            ("Delete Selected", self._delete_selected)
        ]
        
        for text, command in actions:
            ttk.Button(actions_frame, text=text, command=command).pack(fill=tk.X, pady=2)
        
        # Validation feedback
        validation_frame = ttk.LabelFrame(parent, text="Validation", padding=10)
        validation_frame.pack(fill=tk.BOTH, expand=True)
        
        self.validation_text = tk.Text(validation_frame, wrap=tk.WORD)
        validation_scroll = ttk.Scrollbar(validation_frame, orient=tk.VERTICAL, command=self.validation_text.yview)
        self.validation_text.configure(yscrollcommand=validation_scroll.set)
        
        self.validation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        validation_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_right_panel(self, parent):
        """Create right panel with canvas."""
        
        canvas_frame = ttk.LabelFrame(parent, text="Diagram", padding=10)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = TkinterCanvas(800, 600, title="EG Diagram", master=canvas_frame)
        self.canvas.tk_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create renderer
        self.renderer = CleanDiagramRenderer(self.canvas)
        
        # Bind canvas events
        self.canvas.tk_canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.tk_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.tk_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.tk_canvas.bind("<Control-Button-1>", self._on_canvas_ctrl_click)
    
    # File operations
    def _new_file(self):
        """Create new empty graph."""
        
        if self._check_unsaved_changes():
            from egi_core_dau import create_empty_graph
            self.current_graph = create_empty_graph()
            self.current_file = None
            self.selected_elements.clear()
            self._clear_undo_redo()
            self._update_display()
            self._update_status("New file created")
    
    def _open_file(self):
        """Open EGIF file."""
        
        if not self._check_unsaved_changes():
            return
        
        filename = filedialog.askopenfilename(
            title="Open EGIF File",
            filetypes=[("EGIF files", "*.egif"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    egif_content = f.read().strip()
                
                parser = EGIFParser(egif_content)
                self.current_graph = parser.parse()
                self.current_file = filename
                self.selected_elements.clear()
                self._clear_undo_redo()
                
                # Update EGIF text
                self.egif_text.delete(1.0, tk.END)
                self.egif_text.insert(1.0, egif_content)
                
                self._update_display()
                self._update_status(f"Opened: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    
    def _save_file(self):
        """Save current graph to file."""
        
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._save_file_as()
    
    def _save_file_as(self):
        """Save current graph to new file."""
        
        filename = filedialog.asksaveasfilename(
            title="Save EGIF File",
            defaultextension=".egif",
            filetypes=[("EGIF files", "*.egif"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            self._save_to_file(filename)
    
    def _save_to_file(self, filename: str):
        """Save graph to specified file."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph to save")
            return
        
        try:
            # Generate EGIF
            from egif_generator_dau import generate_egif
            egif_content = generate_egif(self.current_graph)
            
            # Save to file
            with open(filename, 'w') as f:
                f.write(egif_content)
            
            self.current_file = filename
            self._update_status(f"Saved: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def _export_png(self):
        """Export diagram as PNG."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export PNG",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.canvas.save_to_file(filename, "png")
                self._update_status(f"Exported: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PNG: {str(e)}")
    
    # Core operations
    def _parse_egif(self):
        """Parse EGIF from text input."""
        
        egif_content = self.egif_text.get(1.0, tk.END).strip()
        if not egif_content:
            messagebox.showwarning("Warning", "No EGIF content to parse")
            return
        
        try:
            parser = EGIFParser(egif_content)
            new_graph = parser.parse()
            
            self._save_state()  # For undo
            self.current_graph = new_graph
            self.selected_elements.clear()
            
            self._update_display()
            self._update_status("EGIF parsed successfully")
            
        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse EGIF: {str(e)}")
    
    def _generate_egif(self):
        """Generate EGIF from current graph."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph to generate EGIF from")
            return
        
        try:
            from egif_generator_dau import generate_egif
            egif_content = generate_egif(self.current_graph)
            
            self.egif_text.delete(1.0, tk.END)
            self.egif_text.insert(1.0, egif_content)
            
            self._update_status("EGIF generated")
            
        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate EGIF: {str(e)}")
    
    def _update_display(self):
        """Update the visual display."""
        
        if not self.current_graph:
            self.canvas.clear()
            return
        
        try:
            # Generate layout
            layout = self.layout_engine.layout_graph(self.current_graph)
            
            # Render diagram
            self.canvas.clear()
            self.renderer.render_diagram(layout, self.current_graph)
            
            # Update selection display
            self._update_selection_display()
            
            # Update validation
            self._update_validation()
            
        except Exception as e:
            self._update_status(f"Display error: {str(e)}")
    
    def _update_selection_display(self):
        """Update selection listbox."""
        
        self.selection_listbox.delete(0, tk.END)
        
        for element_id in self.selected_elements:
            desc = self._get_element_description(element_id)
            self.selection_listbox.insert(tk.END, desc)
    
    def _update_validation(self):
        """Update validation feedback."""
        
        if not self.current_graph:
            self.validation_text.delete(1.0, tk.END)
            self.validation_text.insert(1.0, "No graph loaded")
            return
        
        # Validate graph integrity before running validation system
        integrity_issues = self._check_graph_integrity(self.current_graph)
        if integrity_issues:
            # If graph is corrupted, try to reload from EGIF
            try:
                current_egif = self.egif_text.get(1.0, tk.END).strip()
                if current_egif:
                    from egif_parser_dau import EGIFParser
                    parser = EGIFParser(current_egif)
                    self.current_graph = parser.parse()
                    self._update_status("Graph integrity restored from EGIF")
                else:
                    self._update_status("Graph corruption detected - please reload")
                    return
            except Exception as e:
                self._update_status(f"Cannot restore graph integrity: {str(e)}")
                return
        
        # Get validation results
        validation_results = self.validation_system.validator.background_validator.validate_graph_structure(
            self.current_graph
        )
        
        # Display results
        feedback_text = "=== VALIDATION RESULTS ===\n\n"
        
        if validation_results['is_valid']:
            feedback_text += "✓ Graph structure is valid\n\n"
        else:
            feedback_text += "✗ Graph has structural issues\n\n"
        
        if validation_results['errors']:
            feedback_text += "ERRORS:\n"
            for error in validation_results['errors']:
                feedback_text += f"  • {error}\n"
            feedback_text += "\n"
        
        if validation_results['warnings']:
            feedback_text += "WARNINGS:\n"
            for warning in validation_results['warnings']:
                feedback_text += f"  • {warning}\n"
            feedback_text += "\n"
        
        if validation_results['suggestions']:
            feedback_text += "SUGGESTIONS:\n"
            for suggestion in validation_results['suggestions']:
                feedback_text += f"  • {suggestion}\n"
            feedback_text += "\n"
        
        # Show available transformations
        transformations = self.validation_system.get_transformation_opportunities(self.current_graph)
        if transformations:
            feedback_text += "AVAILABLE TRANSFORMATIONS:\n"
            for transform in transformations[:5]:
                feedback_text += f"  • {transform['description']}\n"
        
        self.validation_text.delete(1.0, tk.END)
        self.validation_text.insert(1.0, feedback_text)
    
    def _get_element_description(self, element_id: ElementID) -> str:
        """Get human-readable element description."""
        
        if not self.current_graph:
            return f"Element {element_id[-8:]}"
        
        if element_id in self.current_graph.V:
            return f"Vertex {element_id[-8:]}"
        elif element_id in self.current_graph.E:
            predicate_name = self.current_graph.rel.get(element_id, "Unknown")
            return f"Predicate '{predicate_name}' ({element_id[-8:]})"
        elif element_id in self.current_graph.Cut:
            return f"Cut {element_id[-8:]}"
        else:
            return f"Unknown {element_id[-8:]}"
    
    # Canvas event handlers
    def _on_canvas_click(self, event):
        """Handle canvas click."""
        
        # For now, just clear selection on empty click
        # Real implementation would use spatial layout for element selection
        if not self.selected_elements:
            self._update_status("Click and drag to select elements")
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag."""
        pass
    
    def _on_canvas_release(self, event):
        """Handle canvas release."""
        pass
    
    def _on_canvas_ctrl_click(self, event):
        """Handle Ctrl+click for multi-selection."""
        pass
    
    # Action handlers
    def _add_predicate(self):
        """Add new predicate."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph loaded")
            return
        
        # Simple dialog for predicate name
        name = tk.simpledialog.askstring("Add Predicate", "Predicate name:")
        if name:
            self._save_state()
            # Implementation would add predicate to graph
            self._update_status(f"Added predicate: {name}")
    
    def _add_loi(self):
        """Add Line of Identity."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph loaded")
            return
        
        self._save_state()
        # Implementation would add LoI to graph
        self._update_status("Added Line of Identity")
    
    def _add_cut(self):
        """Add cut around selection."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph loaded")
            return
        
        result = self.transformation_engine.apply_transformation(
            self.current_graph, TransformationRule.CUT_INSERT,
            target_area=self.current_graph.sheet,
            enclosed_elements=self.selected_elements
        )
        
        if result.success:
            self._save_state()
            self.current_graph = result.new_graph
            self.selected_elements.clear()
            self._update_display()
            self._update_status(f"Added cut: {result.description}")
        else:
            messagebox.showerror("Error", f"Failed to add cut: {result.error_message}")
    
    def _delete_selected(self):
        """Delete selected elements."""
        
        if not self.current_graph or not self.selected_elements:
            return
        
        result = self.transformation_engine.apply_transformation(
            self.current_graph, TransformationRule.ERASURE,
            elements_to_erase=self.selected_elements
        )
        
        if result.success:
            self._save_state()
            self.current_graph = result.new_graph
            self.selected_elements.clear()
            self._update_display()
            self._update_status(f"Deleted elements: {result.description}")
        else:
            messagebox.showerror("Error", f"Failed to delete: {result.error_message}")
    
    def _apply_rule(self, rule: TransformationRule):
        """Apply transformation rule."""
        
        if not self.current_graph:
            messagebox.showwarning("Warning", "No graph loaded")
            return
        
        # Get appropriate parameters based on rule
        params = {}
        
        if rule == TransformationRule.DOUBLE_CUT_INSERT:
            params['target_area'] = self.current_graph.sheet
        elif rule == TransformationRule.DOUBLE_CUT_DELETE:
            cuts = list(self.current_graph.Cut)
            if not cuts:
                messagebox.showwarning("Warning", "No cuts available for double cut deletion")
                return
            params['outer_cut_id'] = cuts[0]
        elif rule == TransformationRule.ERASURE:
            if not self.selected_elements:
                messagebox.showwarning("Warning", "No elements selected for erasure")
                return
            params['elements_to_erase'] = self.selected_elements
        elif rule == TransformationRule.CUT_INSERT:
            params['target_area'] = self.current_graph.sheet
            params['enclosed_elements'] = self.selected_elements
        elif rule == TransformationRule.CUT_DELETE:
            cuts = list(self.current_graph.Cut)
            if not cuts:
                messagebox.showwarning("Warning", "No cuts available for deletion")
                return
            params['cut_id'] = cuts[0]
        
        # Apply transformation
        result = self.transformation_engine.apply_transformation(self.current_graph, rule, **params)
        
        if result.success:
            self._save_state()
            self.current_graph = result.new_graph
            self.selected_elements.clear()
            self._update_display()
            self._update_status(f"Applied {rule.value}: {result.description}")
        else:
            messagebox.showerror("Error", f"Transformation failed: {result.error_message}")
    
    # Undo/Redo
    def _save_state(self):
        """Save current state for undo."""
        
        if self.current_graph:
            self.undo_stack.append(self.current_graph)
            self.redo_stack.clear()
            
            # Limit undo stack size
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
    
    def _undo(self):
        """Undo last operation."""
        
        if self.undo_stack:
            self.redo_stack.append(self.current_graph)
            self.current_graph = self.undo_stack.pop()
            self.selected_elements.clear()
            self._update_display()
            self._update_status("Undone")
    
    def _redo(self):
        """Redo last undone operation."""
        
        if self.redo_stack:
            self.undo_stack.append(self.current_graph)
            self.current_graph = self.redo_stack.pop()
            self.selected_elements.clear()
            self._update_display()
            self._update_status("Redone")
    
    def _clear_undo_redo(self):
        """Clear undo/redo stacks."""
        
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    # Selection operations
    def _select_all(self):
        """Select all elements."""
        
        if self.current_graph:
            self.selected_elements = self.current_graph.V | self.current_graph.E | self.current_graph.Cut
            self._update_selection_display()
            self._update_validation()
            self._update_status(f"Selected {len(self.selected_elements)} elements")
    
    def _clear_selection(self):
        """Clear selection."""
        
        self.selected_elements.clear()
        self._update_selection_display()
        self._update_validation()
        self._update_status("Selection cleared")
    
    # Utility methods
    def _check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user."""
        
        # For now, always return True
        # Real implementation would track dirty state
        return True
    
    def _update_status(self, message: str):
        """Update status bar."""
        
        self.status_var.set(message)
    
    def _check_graph_integrity(self, graph):
        """Check if graph has structural integrity issues.
        
        Returns list of integrity issues found, empty if graph is sound.
        """
        issues = []
        
        try:
            # Check 1: All elements should be in some area (FIXED: compare IDs, not objects)
            all_element_ids = {elem.id for elem in (graph.V | graph.E | graph.Cut)}
            elements_in_areas = set()
            for elements in graph.area.values():
                elements_in_areas.update(elements)
            
            orphaned = all_element_ids - elements_in_areas
            if orphaned:
                issues.append(f"Orphaned elements not in any area: {orphaned}")
            
            # Check 2: Nu mapping should only reference existing elements
            for edge_id, vertices in graph.nu.items():
                if edge_id not in graph.E:
                    issues.append(f"Nu mapping references non-existent edge: {edge_id}")
                for vertex_id in vertices:
                    if vertex_id not in graph.V:
                        issues.append(f"Nu mapping references non-existent vertex: {vertex_id}")
            
            # Check 3: Area mapping should only reference existing elements
            for area_id, elements in graph.area.items():
                for element_id in elements:
                    if (element_id not in graph.V and 
                        element_id not in graph.E and 
                        element_id not in graph.Cut):
                        issues.append(f"Area mapping references non-existent element: {element_id}")
            
            # Check 4: Relation mapping should only reference existing edges
            for edge_id in graph.rel.keys():
                if edge_id not in graph.E:
                    issues.append(f"Relation mapping references non-existent edge: {edge_id}")
                    
        except Exception as e:
            issues.append(f"Exception during integrity check: {str(e)}")
        
        return issues
    
    def _on_category_change(self, event=None):
        """Handle category selection change."""
        self._update_corpus_examples()
    
    def _update_corpus_examples(self):
        """Update the corpus examples listbox based on selected category."""
        category = self.category_var.get()
        
        # Clear current list
        self.example_listbox.delete(0, tk.END)
        
        # Get examples for category
        if category == "All":
            examples = self.corpus_loader.list_examples()
        else:
            examples = self.corpus_loader.list_examples(category)
        
        # Populate listbox
        for example in examples:
            display_text = f"{example.title} ({example.category})"
            self.example_listbox.insert(tk.END, display_text)
            # Store the example ID for retrieval
            self.example_listbox.insert(tk.END, example.id)
            self.example_listbox.delete(tk.END)  # Remove the ID, keep it in memory
        
        # Store examples for easy access
        self._current_examples = examples
    
    def _load_corpus_example(self, event=None):
        """Load selected corpus example into the editor."""
        selection = self.example_listbox.curselection()
        if not selection:
            self._update_status("Please select an example to load")
            return
        
        try:
            # Get selected example
            idx = selection[0]
            if idx >= len(self._current_examples):
                self._update_status("Invalid selection")
                return
            
            example = self._current_examples[idx]
            
            # Try to load EGIF content
            if example.egif_content:
                egif_text = example.egif_content
            else:
                # Generate a simple EGIF from the logical form if available
                if example.logical_form:
                    # This is a placeholder - you might want to implement
                    # a more sophisticated conversion from logical form to EGIF
                    egif_text = f"# {example.title}\n# {example.description}\n# Logical form: {example.logical_form}\n# TODO: Convert to EGIF"
                else:
                    egif_text = f"# {example.title}\n# {example.description}\n# No EGIF content available"
            
            # Load into EGIF text area
            self.egif_text.delete(1.0, tk.END)
            self.egif_text.insert(1.0, egif_text)
            
            # If it's actual EGIF (not a comment), try to parse it
            if not egif_text.strip().startswith('#'):
                self._parse_egif()
            
            self._update_status(f"Loaded example: {example.title}")
            
        except Exception as e:
            self._update_status(f"Error loading example: {e}")
    
    def _load_example(self):
        """Load example graph."""
        
        # Simple example for testing
        egif_text = "(Human \"Socrates\") ~[ (Mortal \"Socrates\") ]"
        
        try:
            parser = EGIFParser()
            graph = parser.parse(egif_text)
            
            self.current_graph = graph
            self.egif_text.delete(1.0, tk.END)
            self.egif_text.insert(1.0, egif_text)
            
            self._update_display()
            self._update_status("Example loaded successfully")
            
        except Exception as e:
            self._update_status(f"Error loading example: {e}")
    
    def run(self):
        """Run the application."""
        
        self.root.mainloop()


def main():
    """Main entry point."""
    
    print("Starting Arisbe - Existential Graphs Editor...")
    
    try:
        app = IntegratedEGEditor()
        app.run()
    except Exception as e:
        print(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
