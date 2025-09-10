"""
GUI Visualization of Cut Correspondence to Sheet and Negation

This visualization demonstrates:
1. Canvas representing the sheet of assertion (unbounded space)
2. Cuts as rectangles representing negation contexts
3. Sibling cuts (beside each other in same area)
4. Nested cuts (cuts within cuts creating sub-areas)
5. R-tree spatial indexing and area containment
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import our R-tree cut tracking system
from rtree_cut_tracker import (
    RTreeCutTracker, SpatialBounds, CutPlacementType, 
    CutSpatialInfo
)
from egi_core_dau import RelationalGraphWithCuts, Cut, ElementID
from frozendict import frozendict


@dataclass
class VisualStyle:
    """Visual styling for cuts and areas."""
    cut_border_color: str = "#2E3440"
    cut_fill_color: str = "#D8DEE9"
    nested_cut_color: str = "#88C0D0"
    selected_cut_color: str = "#5E81AC"
    sheet_color: str = "#ECEFF4"
    text_color: str = "#2E3440"
    highlight_color: str = "#BF616A"


class CutVisualizationCanvas(tk.Canvas):
    """Canvas widget for visualizing cuts and their spatial relationships."""
    
    def __init__(self, parent, width=800, height=600, **kwargs):
        super().__init__(parent, width=width, height=height, bg=VisualStyle.sheet_color, **kwargs)
        
        self.cut_tracker = RTreeCutTracker()
        self.style = VisualStyle()
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.selected_cut = None
        
        # Visual elements tracking
        self.cut_rectangles: Dict[ElementID, int] = {}  # cut_id -> canvas item id
        self.cut_labels: Dict[ElementID, int] = {}      # cut_id -> canvas text id
        
        # Bind mouse events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<MouseWheel>", self.on_zoom)
        
        # Track dragging state
        self.dragging_cut = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
    def load_test_egi(self) -> RelationalGraphWithCuts:
        """Create test EGI with sibling and nested cuts."""
        # Initialize EGI components
        vertices = set()
        edges = set()
        cuts = set()
        nu_mapping = {}
        area_mapping = {"sheet": set()}
        rel_mapping = {}
        
        # Create test cuts
        cut_ids = ["cut_A", "cut_B", "cut_C", "cut_D", "cut_E", "cut_F"]
        
        for cut_id in cut_ids:
            cut = Cut(cut_id)
            cuts.add(cut)
        
        # Set up area relationships
        # Root level: cut_A, cut_B are siblings in sheet
        area_mapping["sheet"] = {"cut_A", "cut_B"}
        
        # cut_A contains cut_C and cut_D (siblings)
        area_mapping["cut_A"] = {"cut_C", "cut_D"}
        
        # cut_B contains cut_E
        area_mapping["cut_B"] = {"cut_E"}
        
        # cut_C contains cut_F (deeply nested)
        area_mapping["cut_C"] = {"cut_F"}
        
        # Initialize empty areas for cuts that don't contain others
        for cut_id in ["cut_D", "cut_E", "cut_F"]:
            area_mapping[cut_id] = set()
        
        # Convert to frozen structures
        frozen_area_mapping = {}
        for area_id, contained_elements in area_mapping.items():
            frozen_area_mapping[area_id] = frozenset(contained_elements)
        
        # Create EGI
        egi = RelationalGraphWithCuts(
            V=frozenset(vertices),
            E=frozenset(edges),
            nu=frozendict(nu_mapping),
            sheet="sheet",
            Cut=frozenset(cuts),
            area=frozendict(frozen_area_mapping),
            rel=frozendict(rel_mapping)
        )
        
        return egi
    
    def setup_test_cuts(self):
        """Set up test cuts with spatial positions."""
        egi = self.load_test_egi()
        
        # Define spatial bounds for test cuts
        cut_bounds = {
            "cut_A": SpatialBounds(50, 50, 300, 200),    # Large cut on left
            "cut_B": SpatialBounds(400, 50, 250, 150),   # Medium cut on right
            "cut_C": SpatialBounds(70, 70, 120, 80),     # Nested in cut_A
            "cut_D": SpatialBounds(210, 70, 120, 80),    # Sibling to cut_C in cut_A
            "cut_E": SpatialBounds(420, 80, 100, 60),    # Nested in cut_B
            "cut_F": SpatialBounds(80, 90, 60, 40),      # Deeply nested in cut_C
        }
        
        # Add cuts to tracker
        for cut_id, bounds in cut_bounds.items():
            success = self.cut_tracker.add_cut(egi, cut_id, bounds, CutPlacementType.BESIDE)
            if not success:
                print(f"Warning: Failed to add cut {cut_id}")
        
        # Store EGI reference
        self.egi = egi
        
        # Draw all cuts
        self.redraw_all()
    
    def redraw_all(self):
        """Redraw all cuts and labels."""
        self.delete("all")
        self.cut_rectangles.clear()
        self.cut_labels.clear()
        
        # Draw sheet background (already set as canvas background)
        
        # Draw cuts in order of nesting level (deepest first, so they appear behind)
        cut_infos = list(self.cut_tracker.cut_spatial_info.values())
        cut_infos.sort(key=lambda c: -c.nesting_level)  # Deepest first
        
        for cut_info in cut_infos:
            self.draw_cut(cut_info)
        
        # Draw area information
        self.draw_area_info()
    
    def draw_cut(self, cut_info: CutSpatialInfo):
        """Draw a single cut with appropriate styling."""
        bounds = cut_info.bounds
        cut_id = cut_info.cut_id
        
        # Choose color based on nesting level
        if cut_info.nesting_level == 0:
            fill_color = self.style.cut_fill_color
        elif cut_info.nesting_level == 1:
            fill_color = self.style.nested_cut_color
        else:
            # Deeper nesting gets progressively darker
            fill_color = "#4C566A"
        
        # Highlight selected cut
        if cut_id == self.selected_cut:
            fill_color = self.style.selected_cut_color
        
        # Draw rectangle
        rect_id = self.create_rectangle(
            bounds.x, bounds.y,
            bounds.x + bounds.width, bounds.y + bounds.height,
            outline=self.style.cut_border_color,
            fill=fill_color,
            width=2,
            tags=f"cut_{cut_id}"
        )
        self.cut_rectangles[cut_id] = rect_id
        
        # Draw label
        center_x = bounds.x + bounds.width / 2
        center_y = bounds.y + bounds.height / 2
        
        label_text = f"{cut_id}\n(Level {cut_info.nesting_level})"
        if cut_info.parent_area_id != "sheet":
            label_text += f"\nin {cut_info.parent_area_id}"
        
        text_id = self.create_text(
            center_x, center_y,
            text=label_text,
            fill=self.style.text_color,
            font=("Arial", 10, "bold"),
            tags=f"label_{cut_id}"
        )
        self.cut_labels[cut_id] = text_id
    
    def draw_area_info(self):
        """Draw area containment information."""
        y_pos = 10
        
        # Sheet information
        sheet_cuts = self.cut_tracker.get_directly_enclosed_cuts("sheet")
        self.create_text(
            10, y_pos,
            text=f"Sheet contains: {', '.join(sheet_cuts)}",
            anchor="nw",
            fill=self.style.text_color,
            font=("Arial", 10)
        )
        y_pos += 20
        
        # Area information for each cut
        for cut_id in self.cut_tracker.cut_spatial_info.keys():
            direct_cuts = self.cut_tracker.get_directly_enclosed_cuts(cut_id)
            if direct_cuts:
                self.create_text(
                    10, y_pos,
                    text=f"{cut_id} contains: {', '.join(direct_cuts)}",
                    anchor="nw",
                    fill=self.style.text_color,
                    font=("Arial", 10)
                )
                y_pos += 20
    
    def on_click(self, event):
        """Handle mouse click events."""
        x, y = event.x, event.y
        
        # Find cut at click position
        clicked_cut = self.cut_tracker.get_cut_at_point(x, y)
        
        if clicked_cut:
            self.selected_cut = clicked_cut
            self.dragging_cut = clicked_cut
            self.drag_start_x = x
            self.drag_start_y = y
            self.redraw_all()
            
            # Show cut information
            self.show_cut_info(clicked_cut)
        else:
            self.selected_cut = None
            self.redraw_all()
    
    def on_drag(self, event):
        """Handle mouse drag events."""
        if not self.dragging_cut:
            return
        
        x, y = event.x, event.y
        dx = x - self.drag_start_x
        dy = y - self.drag_start_y
        
        # Get current cut bounds
        cut_info = self.cut_tracker.cut_spatial_info[self.dragging_cut]
        current_bounds = cut_info.bounds
        
        # Calculate new bounds
        new_bounds = SpatialBounds(
            current_bounds.x + dx,
            current_bounds.y + dy,
            current_bounds.width,
            current_bounds.height
        )
        
        # Try to move the cut
        if self.cut_tracker.move_cut(self.dragging_cut, new_bounds):
            self.drag_start_x = x
            self.drag_start_y = y
            self.redraw_all()
        # If move failed, don't update drag position (provides resistance feedback)
    
    def on_release(self, event):
        """Handle mouse release events."""
        self.dragging_cut = None
    
    def on_zoom(self, event):
        """Handle mouse wheel zoom events."""
        # Simple zoom implementation
        if event.delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1
        
        # Note: Full zoom implementation would require coordinate transformation
        # For now, just provide visual feedback
        print(f"Zoom: {self.scale_factor:.2f}")
    
    def show_cut_info(self, cut_id: ElementID):
        """Show detailed information about a cut."""
        cut_info = self.cut_tracker.cut_spatial_info[cut_id]
        
        # Get containment information
        direct_cuts = self.cut_tracker.get_directly_enclosed_cuts(cut_id)
        nested_cuts = self.cut_tracker.get_nested_cuts(cut_id, self.egi)
        area_extent = self.cut_tracker.get_area_spatial_extent(cut_id)
        
        info_text = f"""Cut Information: {cut_id}
        
Spatial Bounds: ({cut_info.bounds.x:.0f}, {cut_info.bounds.y:.0f}, {cut_info.bounds.width:.0f}, {cut_info.bounds.height:.0f})
Parent Area: {cut_info.parent_area_id}
Nesting Level: {cut_info.nesting_level}

Directly Contains: {', '.join(direct_cuts) if direct_cuts else 'None'}
All Nested Cuts: {', '.join(nested_cuts) if nested_cuts else 'None'}

Area Extent: {area_extent}
"""
        
        messagebox.showinfo(f"Cut {cut_id}", info_text)


class CutVisualizationGUI:
    """Main GUI application for cut visualization."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EGI Cut Visualization - Sheet and Negation Correspondence")
        self.root.geometry("1000x700")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="EGI Cut Visualization: Sheet and Negation Correspondence",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_text = """
Canvas represents the Sheet of Assertion (unbounded logical space)
Cuts represent Negation contexts creating exclusive sub-areas
Click cuts to select and drag to move (with constraint validation)
        """
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.CENTER)
        desc_label.pack(pady=(0, 10))
        
        # Canvas frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Visualization canvas
        self.canvas = CutVisualizationCanvas(canvas_frame, width=800, height=500)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(fill=tk.X)
        self.canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="Load Test Cuts", 
            command=self.load_test_cuts
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Validate Constraints", 
            command=self.validate_constraints
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Show R-tree Info", 
            command=self.show_rtree_info
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Reset View", 
            command=self.reset_view
        ).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Click 'Load Test Cuts' to begin")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(10, 0))
    
    def load_test_cuts(self):
        """Load test cuts into the visualization."""
        try:
            self.canvas.setup_test_cuts()
            self.status_var.set("Test cuts loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load test cuts: {str(e)}")
            self.status_var.set("Error loading test cuts")
    
    def validate_constraints(self):
        """Validate spatial constraints."""
        overlapping_pairs = self.canvas.cut_tracker.validate_non_overlapping_constraint()
        
        if overlapping_pairs:
            overlap_text = "\n".join([f"{c1} overlaps {c2}" for c1, c2 in overlapping_pairs])
            messagebox.showwarning("Constraint Violations", f"Overlapping cuts found:\n{overlap_text}")
            self.status_var.set(f"Found {len(overlapping_pairs)} constraint violations")
        else:
            messagebox.showinfo("Validation", "All spatial constraints satisfied!")
            self.status_var.set("All constraints valid")
    
    def show_rtree_info(self):
        """Show R-tree spatial index information."""
        cut_count = len(self.canvas.cut_tracker.cut_spatial_info)
        area_count = len(self.canvas.cut_tracker.area_bounds)
        
        info_text = f"""R-tree Spatial Index Information:

Total Cuts Tracked: {cut_count}
Total Areas: {area_count}
Minimum Cut Spacing: {self.canvas.cut_tracker.min_cut_spacing}

Area Extents:
"""
        
        for area_id, bounds in self.canvas.cut_tracker.area_bounds.items():
            info_text += f"  {area_id}: ({bounds.x:.0f}, {bounds.y:.0f}) {bounds.width:.0f}×{bounds.height:.0f}\n"
        
        messagebox.showinfo("R-tree Information", info_text)
    
    def reset_view(self):
        """Reset the visualization view."""
        self.canvas.scale_factor = 1.0
        self.canvas.offset_x = 0
        self.canvas.offset_y = 0
        self.canvas.selected_cut = None
        self.canvas.redraw_all()
        self.status_var.set("View reset")
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main function to run the cut visualization GUI."""
    print("Starting EGI Cut Visualization GUI...")
    
    try:
        app = CutVisualizationGUI()
        app.run()
    except Exception as e:
        print(f"Error running GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
