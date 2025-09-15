#!/usr/bin/env python3
"""
Corpus Navigator for the Organon module.
Provides exploration and navigation of EGI collections and universes of discourse.
"""

import json
import os

# Import core components
import sys
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional, Set

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from egi_core_dau import RelationalGraphWithCuts

# from enhanced_transformation_history import TransformationHistory
# from history_persistence import HistoryPersistenceManager


@dataclass
class CorpusEntry:
    """Entry in the corpus index."""

    entry_id: str
    title: str
    description: str
    file_path: str
    universe_of_discourse: str
    creation_date: datetime
    last_modified: datetime
    tags: Set[str]
    metadata: Dict[str, Any]


@dataclass
class UniverseOfDiscourse:
    """A thematic collection of related EGIs."""

    universe_id: str
    name: str
    description: str
    domain_model: Optional[str]
    entries: List[str]  # Entry IDs
    ontology_links: Dict[str, str]


class CorpusNavigator:
    """Navigator for exploring EGI corpus and universes of discourse."""

    def __init__(self, master, corpus_root: str = "corpus"):
        self.master = master
        self.corpus_root = Path(corpus_root)

        # Data structures
        self.entries: Dict[str, CorpusEntry] = {}
        self.universes: Dict[str, UniverseOfDiscourse] = {}
        self.current_selection: Optional[str] = None

        # UI components
        self.tree = None
        self.details_panel = None
        self.search_var = None

        self.setup_ui()
        self.load_corpus_index()

    def setup_ui(self):
        """Create the corpus navigator interface."""
        # Main container
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        # Search
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_changed)
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Actions
        ttk.Button(toolbar, text="Refresh", command=self.refresh_corpus).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="New Universe", command=self.create_universe).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Import EGI", command=self.import_egi).pack(
            side=tk.LEFT, padx=5
        )

        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Tree view
        tree_frame = ttk.LabelFrame(content_frame, text="Corpus Structure")
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Tree with scrollbars
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            tree_container, columns=("type", "modified"), show="tree headings"
        )
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("modified", text="Modified")

        self.tree.column("#0", width=200)
        self.tree.column("type", width=80)
        self.tree.column("modified", width=120)

        # Scrollbars for tree
        tree_v_scroll = ttk.Scrollbar(
            tree_container, orient=tk.VERTICAL, command=self.tree.yview
        )
        tree_h_scroll = ttk.Scrollbar(
            tree_container, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=tree_v_scroll.set, xscrollcommand=tree_h_scroll.set
        )

        tree_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind tree selection
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_selection)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Right panel - Details
        self.details_panel = ttk.LabelFrame(content_frame, text="Details")
        self.details_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        self.setup_details_panel()

    def setup_details_panel(self):
        """Setup the details panel for selected items."""
        # Scrollable text area for details
        details_frame = ttk.Frame(self.details_panel)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.details_text = tk.Text(details_frame, wrap=tk.WORD, width=40, height=20)
        details_scroll = ttk.Scrollbar(
            details_frame, orient=tk.VERTICAL, command=self.details_text.yview
        )
        self.details_text.configure(yscrollcommand=details_scroll.set)

        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = ttk.Frame(self.details_panel)
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="Open", command=self.open_selected).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Export", command=self.export_selected).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Delete", command=self.delete_selected).pack(
            side=tk.LEFT, padx=2
        )

    def load_corpus_index(self):
        """Load the corpus index from disk."""
        try:
            # Load universes
            universes_file = self.corpus_root / "universes.json"
            if universes_file.exists():
                with open(universes_file, "r") as f:
                    universes_data = json.load(f)
                    for universe_data in universes_data:
                        universe = UniverseOfDiscourse(**universe_data)
                        self.universes[universe.universe_id] = universe

            # Load entries index
            index_file = self.corpus_root / "index.json"
            if index_file.exists():
                with open(index_file, "r") as f:
                    entries_data = json.load(f)
                    for entry_data in entries_data:
                        # Convert datetime strings back to datetime objects
                        entry_data["creation_date"] = datetime.fromisoformat(
                            entry_data["creation_date"]
                        )
                        entry_data["last_modified"] = datetime.fromisoformat(
                            entry_data["last_modified"]
                        )
                        entry_data["tags"] = set(entry_data["tags"])

                        entry = CorpusEntry(**entry_data)
                        self.entries[entry.entry_id] = entry

            self.populate_tree()

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load corpus index: {e}")

    def save_corpus_index(self):
        """Save the corpus index to disk."""
        try:
            # Ensure corpus directory exists
            self.corpus_root.mkdir(parents=True, exist_ok=True)

            # Save universes
            universes_data = []
            for universe in self.universes.values():
                universe_dict = {
                    "universe_id": universe.universe_id,
                    "name": universe.name,
                    "description": universe.description,
                    "domain_model": universe.domain_model,
                    "entries": universe.entries,
                    "ontology_links": universe.ontology_links,
                }
                universes_data.append(universe_dict)

            with open(self.corpus_root / "universes.json", "w") as f:
                json.dump(universes_data, f, indent=2)

            # Save entries index
            entries_data = []
            for entry in self.entries.values():
                entry_dict = {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "description": entry.description,
                    "file_path": entry.file_path,
                    "universe_of_discourse": entry.universe_of_discourse,
                    "creation_date": entry.creation_date.isoformat(),
                    "last_modified": entry.last_modified.isoformat(),
                    "tags": list(entry.tags),
                    "metadata": entry.metadata,
                }
                entries_data.append(entry_dict)

            with open(self.corpus_root / "index.json", "w") as f:
                json.dump(entries_data, f, indent=2)

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save corpus index: {e}")

    def populate_tree(self):
        """Populate the tree view with corpus structure."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add universes as top-level items
        for universe in self.universes.values():
            universe_item = self.tree.insert(
                "",
                "end",
                text=universe.name,
                values=("Universe", ""),
                tags=("universe",),
            )

            # Add entries under each universe
            for entry_id in universe.entries:
                if entry_id in self.entries:
                    entry = self.entries[entry_id]
                    modified_str = entry.last_modified.strftime("%Y-%m-%d")
                    self.tree.insert(
                        universe_item,
                        "end",
                        text=entry.title,
                        values=("EGI", modified_str),
                        tags=("entry", entry_id),
                    )

        # Add orphaned entries (not in any universe)
        orphaned_entries = []
        for entry in self.entries.values():
            if not any(
                entry.entry_id in universe.entries
                for universe in self.universes.values()
            ):
                orphaned_entries.append(entry)

        if orphaned_entries:
            orphaned_item = self.tree.insert(
                "", "end", text="Uncategorized", values=("Folder", ""), tags=("folder",)
            )

            for entry in orphaned_entries:
                modified_str = entry.last_modified.strftime("%Y-%m-%d")
                self.tree.insert(
                    orphaned_item,
                    "end",
                    text=entry.title,
                    values=("EGI", modified_str),
                    tags=("entry", entry.entry_id),
                )

        # Expand all items
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def on_tree_selection(self, event):
        """Handle tree selection changes."""
        selection = self.tree.selection()
        if not selection:
            self.current_selection = None
            self.update_details_panel(None)
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")

        if "entry" in tags and len(tags) > 1:
            # Entry selected
            entry_id = tags[1]  # Second tag is the entry ID
            self.current_selection = entry_id
            self.update_details_panel(self.entries[entry_id])
        elif "universe" in tags:
            # Universe selected
            universe_name = self.tree.item(item, "text")
            universe = next(
                (u for u in self.universes.values() if u.name == universe_name), None
            )
            self.current_selection = None
            self.update_details_panel(universe)
        else:
            self.current_selection = None
            self.update_details_panel(None)

    def update_details_panel(self, item):
        """Update the details panel with information about the selected item."""
        self.details_text.delete(1.0, tk.END)

        if isinstance(item, CorpusEntry):
            # Display entry details
            details = f"Title: {item.title}\n\n"
            details += f"Description:\n{item.description}\n\n"
            details += f"Universe: {item.universe_of_discourse}\n"
            details += f"File: {item.file_path}\n"
            details += f"Created: {item.creation_date.strftime('%Y-%m-%d %H:%M')}\n"
            details += f"Modified: {item.last_modified.strftime('%Y-%m-%d %H:%M')}\n\n"

            if item.tags:
                details += f"Tags: {', '.join(sorted(item.tags))}\n\n"

            if item.metadata:
                details += "Metadata:\n"
                for key, value in item.metadata.items():
                    details += f"  {key}: {value}\n"

            self.details_text.insert(1.0, details)

        elif isinstance(item, UniverseOfDiscourse):
            # Display universe details
            details = f"Universe: {item.name}\n\n"
            details += f"Description:\n{item.description}\n\n"
            details += f"Entries: {len(item.entries)}\n"

            if item.domain_model:
                details += f"Domain Model: {item.domain_model}\n"

            if item.ontology_links:
                details += "\nOntology Links:\n"
                for concept, link in item.ontology_links.items():
                    details += f"  {concept}: {link}\n"

            self.details_text.insert(1.0, details)

        else:
            self.details_text.insert(1.0, "No item selected")

    def on_tree_double_click(self, event):
        """Handle double-click on tree items."""
        self.open_selected()

    def on_search_changed(self, *args):
        """Handle search text changes."""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.populate_tree()
            return

        # Filter entries based on search term
        # TODO: Implement search filtering
        pass

    def refresh_corpus(self):
        """Refresh the corpus from disk."""
        self.load_corpus_index()

    def create_universe(self):
        """Create a new universe of discourse."""
        dialog = UniverseDialog(self.master, "Create Universe")
        if dialog.result:
            universe_data = dialog.result
            universe = UniverseOfDiscourse(
                universe_id=universe_data["universe_id"],
                name=universe_data["name"],
                description=universe_data["description"],
                domain_model=universe_data.get("domain_model"),
                entries=[],
                ontology_links={},
            )

            self.universes[universe.universe_id] = universe
            self.save_corpus_index()
            self.populate_tree()

    def import_egi(self):
        """Import an EGI file into the corpus."""
        file_path = filedialog.askopenfilename(
            title="Import EGI",
            filetypes=[
                ("JSON files", "*.json"),
                ("YAML files", "*.yaml"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            # TODO: Implement EGI import
            messagebox.showinfo(
                "Import", f"Import functionality not yet implemented for {file_path}"
            )

    def open_selected(self):
        """Open the selected entry."""
        if self.current_selection:
            entry = self.entries[self.current_selection]
            # TODO: Open in appropriate editor (Ergasterion or Agon)
            messagebox.showinfo(
                "Open", f"Opening {entry.title} - functionality not yet implemented"
            )

    def export_selected(self):
        """Export the selected entry."""
        if self.current_selection:
            entry = self.entries[self.current_selection]
            # TODO: Implement export functionality
            messagebox.showinfo(
                "Export", f"Export functionality not yet implemented for {entry.title}"
            )

    def delete_selected(self):
        """Delete the selected entry."""
        if self.current_selection:
            entry = self.entries[self.current_selection]
            if messagebox.askyesno("Delete", f"Delete '{entry.title}'?"):
                # Remove from universes
                for universe in self.universes.values():
                    if self.current_selection in universe.entries:
                        universe.entries.remove(self.current_selection)

                # Remove from entries
                del self.entries[self.current_selection]

                # TODO: Delete actual file

                self.save_corpus_index()
                self.populate_tree()
                self.current_selection = None
                self.update_details_panel(None)


class UniverseDialog:
    """Dialog for creating/editing universes of discourse."""

    def __init__(self, parent, title="Universe"):
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.geometry(
            "+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50)
        )

        self.setup_ui()

        # Wait for dialog to close
        self.dialog.wait_window()

    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Universe ID
        ttk.Label(main_frame, text="Universe ID:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.id_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.id_var, width=40).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        # Name
        ttk.Label(main_frame, text="Name:").grid(row=1, column=0, sticky="w", pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(
            row=1, column=1, sticky="ew", pady=2
        )

        # Description
        ttk.Label(main_frame, text="Description:").grid(
            row=2, column=0, sticky="nw", pady=2
        )
        self.description_text = tk.Text(main_frame, width=40, height=8)
        self.description_text.grid(row=2, column=1, sticky="ew", pady=2)

        # Domain Model
        ttk.Label(main_frame, text="Domain Model:").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.domain_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.domain_var, width=40).grid(
            row=3, column=1, sticky="ew", pady=2
        )

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)

    def ok(self):
        """Handle OK button."""
        universe_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        description = self.description_text.get(1.0, tk.END).strip()

        if not universe_id or not name:
            messagebox.showerror("Error", "Universe ID and Name are required")
            return

        self.result = {
            "universe_id": universe_id,
            "name": name,
            "description": description,
            "domain_model": self.domain_var.get().strip() or None,
        }

        self.dialog.destroy()

    def cancel(self):
        """Handle Cancel button."""
        self.dialog.destroy()


def main():
    """Run the corpus navigator."""
    root = tk.Tk()
    root.title("Arisbe - Corpus Navigator (Organon)")
    root.geometry("1000x700")

    app = CorpusNavigator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
