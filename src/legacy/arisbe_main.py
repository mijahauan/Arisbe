#!/usr/bin/env python3
"""
Arisbe Main Application - Unified EGI System
Integrates Organon (exploration), Ergasterion (editing), and Agon (reasoning) modules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from typing import Optional

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

# Import modules
from organon.corpus_navigator import CorpusNavigator
from gui.enhanced_diagram_editor import EnhancedDiagramEditor
from agon.endoporeutic_game import EndoporeuticGameEngine


class ArisbeMainApplication:
    """Main Arisbe application integrating all three modules."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arisbe - Existential Graphs of Ideas")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Module windows
        self.organon_window: Optional[tk.Toplevel] = None
        self.ergasterion_window: Optional[tk.Toplevel] = None
        self.agon_window: Optional[tk.Toplevel] = None
        
        # Module instances
        self.organon_app: Optional[CorpusNavigator] = None
        self.ergasterion_app: Optional[EnhancedDiagramEditor] = None
        self.agon_app: Optional[EndoporeuticGameEngine] = None
        
        self.setup_main_interface()
        
    def setup_main_interface(self):
        """Setup the main application interface."""
        # Title and description
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="ARISBE",
            font=("Arial", 24, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Existential Graphs of Ideas - Dau-Compliant System",
            font=("Arial", 12, "italic")
        )
        subtitle_label.pack(pady=5)
        
        # Module selection frame
        modules_frame = ttk.LabelFrame(self.root, text="Logical Inquiry Modules")
        modules_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # Create three columns for modules
        for i in range(3):
            modules_frame.columnconfigure(i, weight=1)
        
        # Organon module
        self.create_module_panel(
            modules_frame,
            "ORGANON",
            "Corpus Navigator & Explorer",
            "Explore and manage collections of EGI diagrams.\n"
            "• Browse thematic universes of discourse\n"
            "• Search and filter diagram collections\n"
            "• Import/export corpus data\n"
            "• Metadata management",
            self.launch_organon,
            0, 0
        )
        
        # Ergasterion module
        self.create_module_panel(
            modules_frame,
            "ERGASTERION",
            "Diagram Editor & Constructor",
            "Create and edit EGI diagrams with full validation.\n"
            "• Visual diagram construction\n"
            "• Dau-compliant constraint enforcement\n"
            "• Complete transformation rule support\n"
            "• Advanced editing capabilities",
            self.launch_ergasterion,
            0, 1
        )
        
        # Agon module
        self.create_module_panel(
            modules_frame,
            "AGON",
            "Reasoning Game & Umpire",
            "Engage in deductive reasoning games.\n"
            "• Endoporeutic game mechanics\n"
            "• Competing hypothesis management\n"
            "• Automated logical outcome analysis\n"
            "• Meta-level umpire functions",
            self.launch_agon,
            0, 2
        )
        
        # Status and info frame
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.status_var = tk.StringVar(value="Ready - Select a module to begin")
        status_label = ttk.Label(info_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=10)
        
        # About button
        about_btn = ttk.Button(info_frame, text="About", command=self.show_about)
        about_btn.pack(side=tk.RIGHT, padx=10)
        
    def create_module_panel(self, parent, title, subtitle, description, command, row, col):
        """Create a module selection panel."""
        panel = ttk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        panel.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Title
        title_label = ttk.Label(panel, text=title, font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Subtitle
        subtitle_label = ttk.Label(panel, text=subtitle, font=("Arial", 10, "italic"))
        subtitle_label.pack()
        
        # Description
        desc_label = ttk.Label(
            panel,
            text=description,
            font=("Arial", 9),
            justify=tk.LEFT,
            wraplength=250
        )
        desc_label.pack(pady=10, padx=10)
        
        # Launch button
        launch_btn = ttk.Button(
            panel,
            text=f"Launch {title}",
            command=command,
            style="Accent.TButton"
        )
        launch_btn.pack(pady=10)
        
    def launch_organon(self):
        """Launch the Organon corpus navigator."""
        if self.organon_window and self.organon_window.winfo_exists():
            self.organon_window.lift()
            return
            
        self.organon_window = tk.Toplevel(self.root)
        self.organon_app = CorpusNavigator(self.organon_window)
        self.status_var.set("Organon (Corpus Navigator) launched")
        
        # Handle window closing
        def on_organon_close():
            self.organon_window = None
            self.organon_app = None
            self.status_var.set("Organon closed")
            
        self.organon_window.protocol("WM_DELETE_WINDOW", on_organon_close)
        
    def launch_ergasterion(self):
        """Launch the Ergasterion diagram editor."""
        if self.ergasterion_window and self.ergasterion_window.winfo_exists():
            self.ergasterion_window.lift()
            return
            
        self.ergasterion_window = tk.Toplevel(self.root)
        self.ergasterion_app = EnhancedDiagramEditor(self.ergasterion_window)
        self.status_var.set("Ergasterion (Diagram Editor) launched")
        
        # Handle window closing
        def on_ergasterion_close():
            self.ergasterion_window = None
            self.ergasterion_app = None
            self.status_var.set("Ergasterion closed")
            
        self.ergasterion_window.protocol("WM_DELETE_WINDOW", on_ergasterion_close)
        
    def launch_agon(self):
        """Launch the Agon reasoning game."""
        if self.agon_window and self.agon_window.winfo_exists():
            self.agon_window.lift()
            return
            
        self.agon_window = tk.Toplevel(self.root)
        self.agon_app = EndoporeuticGameEngine(self.agon_window)
        self.status_var.set("Agon (Reasoning Game) launched")
        
        # Handle window closing
        def on_agon_close():
            self.agon_window = None
            self.agon_app = None
            self.status_var.set("Agon closed")
            
        self.agon_window.protocol("WM_DELETE_WINDOW", on_agon_close)
        
    def show_about(self):
        """Show about dialog."""
        about_text = """
ARISBE - Existential Graphs of Ideas

A mathematically rigorous system for working with Peirce's 
Existential Graphs based on Dau's formalism.

Modules:
• ORGANON: Corpus navigation and exploration
• ERGASTERION: Diagram editing and construction  
• AGON: Deductive reasoning games

Features:
• Dau-compliant constraint enforcement
• Complete transformation rule support (IT+, IT-, DC+, DC-, INS, ERA)
• Bidirectional diagram-EGI correspondence
• Visual validation feedback
• Professional editing capabilities

Built with mathematical rigor and logical precision.
        """
        
        messagebox.showinfo("About Arisbe", about_text.strip())
        
    def run(self):
        """Run the main application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    app = ArisbeMainApplication()
    app.run()


if __name__ == "__main__":
    main()
