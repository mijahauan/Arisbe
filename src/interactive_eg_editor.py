"""
Correct Existential Graph GUI - Proper EG Semantics

This module implements existential graphs with the correct semantics:

1. Lines of Identity ARE the entities (not connections between entities)
2. Predicates have invisible oval boundaries with hook attachment points
3. Lines of identity attach to hooks on predicate boundaries
4. Movement is constrained by logical containment structure
5. Visual adjustments are enabled and constrained by underlying logic

Key Corrections:
- Line of Identity = Entity (corresponds to Node in EG-HG)
- Predicates = Text with oval boundary and hooks
- Attachment = Line connects to hook on predicate boundary
- Movement = Constrained by containment, lines move with predicates

Author: Manus AI
Date: January 2025
Phase: 4B - Correct EG Implementation
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
import uuid
import math

@dataclass
class Point:
    """2D point for geometric calculations."""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def add(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def subtract(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)


@dataclass
class Bounds:
    """Rectangular bounds for elements."""
    x: float
    y: float
    width: float
    height: float
    
    def contains_point(self, point: Point) -> bool:
        return (self.x <= point.x <= self.x + self.width and 
                self.y <= point.y <= self.y + self.height)
    
    def center(self) -> Point:
        return Point(self.x + self.width/2, self.y + self.height/2)
    
    def overlaps(self, other: 'Bounds') -> bool:
        return not (self.x + self.width < other.x or 
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or 
                   other.y + other.height < self.y)


@dataclass
class Hook:
    """Attachment point on a predicate boundary."""
    predicate_id: str
    angle: float  # Angle around the oval (0-2π)
    position: Point  # Calculated position on boundary
    
    def calculate_position(self, predicate_center: Point, width: float, height: float):
        """Calculate hook position on oval boundary."""
        # Parametric equation for ellipse
        a = width / 2  # Semi-major axis
        b = height / 2  # Semi-minor axis
        
        x = predicate_center.x + a * math.cos(self.angle)
        y = predicate_center.y + b * math.sin(self.angle)
        
        self.position = Point(x, y)


@dataclass
class LineOfIdentity:
    """
    Line of Identity - This IS the entity in EG notation.
    Corresponds to a Node in the EG-HG model.
    """
    id: str
    name: str
    points: List[Point] = None  # Path of the line
    attached_hooks: List[Hook] = None  # Hooks this line attaches to
    line_type: str = "variable"  # variable, constant
    
    def __post_init__(self):
        if self.points is None:
            self.points = []
        if self.attached_hooks is None:
            self.attached_hooks = []
    
    def add_point(self, point: Point):
        """Add a point to extend the line."""
        self.points.append(point)
    
    def attach_to_hook(self, hook: Hook):
        """Attach this line to a predicate hook."""
        self.attached_hooks.append(hook)
        # Extend line to hook position
        if hook.position:
            self.points.append(hook.position)
    
    def detach_from_hook(self, predicate_id: str):
        """Detach from all hooks of a specific predicate."""
        self.attached_hooks = [h for h in self.attached_hooks if h.predicate_id != predicate_id]
    
    def update_hook_positions(self, predicates: Dict[str, 'EGPredicate']):
        """Update positions of attached hooks when predicates move."""
        for hook in self.attached_hooks:
            if hook.predicate_id in predicates:
                predicate = predicates[hook.predicate_id]
                hook.calculate_position(predicate.position, predicate.size[0], predicate.size[1])
        
        # Update line points to match hook positions
        if self.attached_hooks:
            # Simple case: line connects hooks
            self.points = [hook.position for hook in self.attached_hooks if hook.position]


@dataclass
class EGPredicate:
    """
    EG Predicate - Text with invisible oval boundary and hooks.
    The oval boundary defines the 2D extent and attachment points.
    """
    id: str
    name: str
    position: Point  # Center of the predicate
    arity: int
    size: Tuple[float, float] = (100, 50)  # Width, height of oval boundary
    hooks: List[Hook] = None  # Available attachment points
    
    def __post_init__(self):
        if self.hooks is None:
            self.hooks = []
    
    def bounds(self) -> Bounds:
        """Get the oval boundary bounds."""
        return Bounds(
            self.position.x - self.size[0]/2, 
            self.position.y - self.size[1]/2,
            self.size[0], 
            self.size[1]
        )
    
    def add_hook(self, angle: float) -> Hook:
        """Add a hook at the specified angle on the boundary."""
        hook = Hook(
            predicate_id=self.id,
            angle=angle,
            position=Point(0, 0)  # Will be calculated
        )
        hook.calculate_position(self.position, self.size[0], self.size[1])
        self.hooks.append(hook)
        return hook
    
    def find_nearest_hook_angle(self, point: Point) -> float:
        """Find the angle for the nearest point on the boundary."""
        # Vector from center to point
        dx = point.x - self.position.x
        dy = point.y - self.position.y
        
        # Angle to the point
        angle = math.atan2(dy, dx)
        return angle
    
    def move_to(self, new_position: Point):
        """Move predicate and update all hook positions."""
        self.position = new_position
        for hook in self.hooks:
            hook.calculate_position(self.position, self.size[0], self.size[1])
    
    def can_move_to(self, new_position: Point, container_bounds: Bounds, nested_cuts: List[Bounds]) -> bool:
        """Check if predicate can move to new position based on containment rules."""
        new_bounds = Bounds(
            new_position.x - self.size[0]/2,
            new_position.y - self.size[1]/2,
            self.size[0],
            self.size[1]
        )
        
        # Must stay within container
        if not container_bounds.contains_point(new_position):
            return False
        
        # Cannot overlap with nested cuts
        for cut_bounds in nested_cuts:
            if new_bounds.overlaps(cut_bounds):
                return False
        
        return True


@dataclass
class EGCut:
    """EG Cut - Oval context that contains other elements."""
    id: str
    name: str
    bounds: Bounds
    nesting_level: int
    parent_cut: Optional[str] = None
    contained_elements: List[str] = None
    
    def __post_init__(self):
        if self.contained_elements is None:
            self.contained_elements = []


class CorrectEGGraph:
    """Existential graph with correct semantics and visual behavior."""
    
    def __init__(self):
        self.lines_of_identity: Dict[str, LineOfIdentity] = {}  # These ARE the entities
        self.predicates: Dict[str, EGPredicate] = {}
        self.cuts: Dict[str, EGCut] = {}
        self.containment: Dict[str, str] = {}  # element_id -> container_id
        self.canvas_size = (800, 600)
        
        # Create root sheet of assertion
        self.sheet_id = "sheet"
        self.cuts[self.sheet_id] = EGCut(
            id=self.sheet_id,
            name="Sheet of Assertion",
            bounds=Bounds(0, 0, self.canvas_size[0], self.canvas_size[1]),
            nesting_level=0
        )
    
    def add_line_of_identity(self, name: str, start_point: Point) -> str:
        """Add a line of identity (entity) starting at the given point."""
        line_id = f"line_{len(self.lines_of_identity)}"
        line = LineOfIdentity(
            id=line_id,
            name=name,
            points=[start_point]
        )
        self.lines_of_identity[line_id] = line
        
        # Find containing cut
        container = self._find_containing_cut(start_point)
        self.containment[line_id] = container
        self.cuts[container].contained_elements.append(line_id)
        
        return line_id
    
    def add_predicate(self, name: str, position: Point, arity: int = 1) -> str:
        """Add a predicate at the specified position."""
        predicate_id = f"predicate_{len(self.predicates)}"
        predicate = EGPredicate(
            id=predicate_id,
            name=name,
            position=position,
            arity=arity
        )
        self.predicates[predicate_id] = predicate
        
        # Find containing cut
        container = self._find_containing_cut(position)
        self.containment[predicate_id] = container
        self.cuts[container].contained_elements.append(predicate_id)
        
        return predicate_id
    
    def attach_line_to_predicate(self, line_id: str, predicate_id: str, attachment_point: Point) -> bool:
        """Attach a line of identity to a predicate at the nearest hook point."""
        if line_id not in self.lines_of_identity or predicate_id not in self.predicates:
            return False
        
        line = self.lines_of_identity[line_id]
        predicate = self.predicates[predicate_id]
        
        # Find nearest point on predicate boundary
        angle = predicate.find_nearest_hook_angle(attachment_point)
        hook = predicate.add_hook(angle)
        
        # Attach line to hook
        line.attach_to_hook(hook)
        
        return True
    
    def move_predicate(self, predicate_id: str, new_position: Point) -> bool:
        """Move a predicate, updating attached lines and checking constraints."""
        if predicate_id not in self.predicates:
            return False
        
        predicate = self.predicates[predicate_id]
        
        # Check movement constraints
        container_id = self.containment.get(predicate_id)
        if not container_id or container_id not in self.cuts:
            return False
        
        container_bounds = self.cuts[container_id].bounds
        
        # Get nested cuts in the same container
        nested_cuts = []
        for element_id in self.cuts[container_id].contained_elements:
            if element_id in self.cuts and element_id != predicate_id:
                nested_cuts.append(self.cuts[element_id].bounds)
        
        # Check if movement is allowed
        if not predicate.can_move_to(new_position, container_bounds, nested_cuts):
            return False
        
        # Move predicate
        predicate.move_to(new_position)
        
        # Update all attached lines
        for line in self.lines_of_identity.values():
            line.update_hook_positions(self.predicates)
        
        return True
    
    def add_cut(self, position: Point, size: Tuple[float, float] = (200, 150)) -> str:
        """Add a cut at the specified position."""
        cut_id = f"cut_{len(self.cuts) - 1}"  # -1 for sheet
        
        # Find parent cut and nesting level
        parent_container = self._find_containing_cut(position)
        nesting_level = self.cuts[parent_container].nesting_level + 1
        
        cut = EGCut(
            id=cut_id,
            name=f"Cut {nesting_level}",
            bounds=Bounds(position.x - size[0]/2, position.y - size[1]/2, size[0], size[1]),
            nesting_level=nesting_level,
            parent_cut=parent_container
        )
        
        # Validate no overlapping with sibling cuts
        if self._cut_overlaps_with_siblings(cut, parent_container):
            raise ValueError("Cuts cannot overlap - this violates EG syntax")
        
        self.cuts[cut_id] = cut
        self.containment[cut_id] = parent_container
        self.cuts[parent_container].contained_elements.append(cut_id)
        
        return cut_id
    
    def _find_containing_cut(self, position: Point) -> str:
        """Find the innermost cut containing the given position."""
        best_container = self.sheet_id
        best_nesting_level = -1
        
        for cut_id, cut in self.cuts.items():
            if cut.bounds.contains_point(position) and cut.nesting_level > best_nesting_level:
                best_container = cut_id
                best_nesting_level = cut.nesting_level
        
        return best_container
    
    def _cut_overlaps_with_siblings(self, new_cut: EGCut, parent_id: str) -> bool:
        """Check if a new cut overlaps with sibling cuts."""
        parent = self.cuts[parent_id]
        for element_id in parent.contained_elements:
            if element_id in self.cuts:
                sibling_cut = self.cuts[element_id]
                if new_cut.bounds.overlaps(sibling_cut.bounds):
                    return True
        return False
    
    def validate_graph(self) -> Dict[str, Any]:
        """Validate the graph for logical and syntactic correctness."""
        issues = []
        
        # Check for overlapping cuts
        for cut_id, cut in self.cuts.items():
            if cut_id == self.sheet_id:
                continue
            parent_id = cut.parent_cut
            if parent_id and self._cut_overlaps_with_siblings(cut, parent_id):
                issues.append(f"Cut {cut_id} overlaps with sibling cuts")
        
        # Check line-predicate attachments
        for line_id, line in self.lines_of_identity.items():
            for hook in line.attached_hooks:
                if hook.predicate_id not in self.predicates:
                    issues.append(f"Line {line_id} attached to non-existent predicate {hook.predicate_id}")
        
        # Check containment consistency
        for element_id, container_id in self.containment.items():
            if container_id not in self.cuts:
                issues.append(f"Element {element_id} contained in non-existent cut {container_id}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "line_count": len(self.lines_of_identity),
            "predicate_count": len(self.predicates),
            "cut_count": len(self.cuts) - 1,  # Exclude sheet
            "attachment_count": sum(len(line.attached_hooks) for line in self.lines_of_identity.values())
        }
    
    def to_dict(self) -> Dict:
        """Convert graph to dictionary for JSON serialization."""
        return {
            "lines_of_identity": {lid: asdict(line) for lid, line in self.lines_of_identity.items()},
            "predicates": {pid: asdict(pred) for pid, pred in self.predicates.items()},
            "cuts": {cid: asdict(cut) for cid, cut in self.cuts.items()},
            "containment": self.containment,
            "canvas_size": self.canvas_size
        }


class CorrectEGGUI:
    """Correct Existential Graph GUI with proper semantics."""
    
    def __init__(self):
        self.graph = CorrectEGGraph()
        self.app = Flask(__name__)
        self._setup_routes()
        self._create_simple_example()
    
    def _create_simple_example(self):
        """Create a simple example showing correct EG semantics."""
        # Add a line of identity (entity)
        line_id = self.graph.add_line_of_identity("x", Point(200, 200))
        
        # Add predicates
        man_id = self.graph.add_predicate("Man", Point(150, 250))
        mortal_id = self.graph.add_predicate("Mortal", Point(250, 250))
        
        # Attach line to predicates (line connects to hooks on predicate boundaries)
        self.graph.attach_line_to_predicate(line_id, man_id, Point(150, 230))
        self.graph.attach_line_to_predicate(line_id, mortal_id, Point(250, 230))
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            return render_template('correct_eg_editor.html')
        
        @self.app.route('/api/graph')
        def get_graph():
            """Get the current graph state."""
            return jsonify(self.graph.to_dict())
        
        @self.app.route('/api/validate')
        def validate_graph():
            """Validate the current graph."""
            return jsonify(self.graph.validate_graph())
        
        @self.app.route('/api/add_line', methods=['POST'])
        def add_line():
            """Add a line of identity (entity)."""
            data = request.json
            name = data.get('name', 'x')
            x, y = data.get('x', 0), data.get('y', 0)
            
            line_id = self.graph.add_line_of_identity(name, Point(x, y))
            return jsonify({"success": True, "id": line_id})
        
        @self.app.route('/api/add_predicate', methods=['POST'])
        def add_predicate():
            """Add a predicate."""
            data = request.json
            name = data.get('name', 'P')
            x, y = data.get('x', 0), data.get('y', 0)
            arity = data.get('arity', 1)
            
            predicate_id = self.graph.add_predicate(name, Point(x, y), arity)
            return jsonify({"success": True, "id": predicate_id})
        
        @self.app.route('/api/attach', methods=['POST'])
        def attach_line():
            """Attach a line to a predicate."""
            data = request.json
            line_id = data.get('line_id')
            predicate_id = data.get('predicate_id')
            x, y = data.get('x', 0), data.get('y', 0)
            
            success = self.graph.attach_line_to_predicate(line_id, predicate_id, Point(x, y))
            return jsonify({"success": success})
        
        @self.app.route('/api/move_predicate', methods=['POST'])
        def move_predicate():
            """Move a predicate (with constraint checking)."""
            data = request.json
            predicate_id = data.get('predicate_id')
            x, y = data.get('x', 0), data.get('y', 0)
            
            success = self.graph.move_predicate(predicate_id, Point(x, y))
            return jsonify({"success": success})
        
        @self.app.route('/api/add_cut', methods=['POST'])
        def add_cut():
            """Add a cut."""
            data = request.json
            x, y = data.get('x', 0), data.get('y', 0)
            width = data.get('width', 200)
            height = data.get('height', 150)
            
            try:
                cut_id = self.graph.add_cut(Point(x, y), (width, height))
                return jsonify({"success": True, "id": cut_id})
            except ValueError as e:
                return jsonify({"success": False, "error": str(e)})
    
    def run(self, debug=True, port=5002):
        """Run the correct EG GUI."""
        # Create templates and static directories
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        
        self._create_html_template()
        self._create_css_styles()
        self._create_javascript()
        
        print("Starting Correct Existential Graph GUI")
        print("=" * 60)
        print("Correct EG Semantics:")
        print("• Lines of Identity ARE the entities")
        print("• Predicates have hook attachment points")
        print("• Movement constrained by logical structure")
        print("• Visual adjustments enabled/constrained by logic")
        print("=" * 60)
        print(f"Access at: http://localhost:{port}")
        
        self.app.run(debug=debug, port=port, host='0.0.0.0')
    
    def _create_html_template(self):
        """Create HTML template for correct EG editor."""
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Correct Existential Graph Editor</title>
    <link rel="stylesheet" href="/static/correct_eg.css">
</head>
<body>
    <div class="container">
        <header class="toolbar">
            <div class="tool-group">
                <label>Tool:</label>
                <input type="radio" id="select" name="tool" value="select" checked>
                <label for="select">Select</label>
                
                <input type="radio" id="line" name="tool" value="line">
                <label for="line">Line of Identity</label>
                
                <input type="radio" id="predicate" name="tool" value="predicate">
                <label for="predicate">Predicate</label>
                
                <input type="radio" id="attach" name="tool" value="attach">
                <label for="attach">Attach</label>
                
                <input type="radio" id="cut" name="tool" value="cut">
                <label for="cut">Cut</label>
            </div>
            
            <div class="action-group">
                <button id="validate-btn">Validate</button>
                <button id="clear-btn">Clear</button>
                <button id="help-btn">Help</button>
            </div>
        </header>
        
        <main class="editor-area">
            <canvas id="eg-canvas" width="800" height="600"></canvas>
        </main>
        
        <aside class="info-panel">
            <h3>Graph Information</h3>
            <div id="graph-info">
                <p>Lines of Identity: <span id="line-count">0</span></p>
                <p>Predicates: <span id="predicate-count">0</span></p>
                <p>Cuts: <span id="cut-count">0</span></p>
                <p>Attachments: <span id="attachment-count">0</span></p>
            </div>
            
            <h3>Validation</h3>
            <div id="validation-info">
                <p id="validation-status">Valid</p>
                <ul id="validation-issues"></ul>
            </div>
            
            <h3>Instructions</h3>
            <div id="instructions">
                <p><strong>Line of Identity:</strong> Click to create entity line</p>
                <p><strong>Predicate:</strong> Click to create predicate with hooks</p>
                <p><strong>Attach:</strong> Click line, then predicate to attach</p>
                <p><strong>Select:</strong> Drag predicates (lines move with them)</p>
            </div>
        </aside>
        
        <footer class="status-bar">
            <span id="status-text">Ready - Correct EG semantics: Lines ARE entities</span>
        </footer>
    </div>
    
    <script src="/static/correct_eg.js"></script>
</body>
</html>'''
        
        with open('templates/correct_eg_editor.html', 'w') as f:
            f.write(html_content)
    
    def _create_css_styles(self):
        """Create CSS for correct EG visual conventions."""
        css_content = '''/* Correct Existential Graph Editor Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Times New Roman', serif;
    background-color: #fefefe;
    color: #333;
}

.container {
    display: grid;
    grid-template-rows: auto 1fr auto;
    grid-template-columns: 1fr 280px;
    grid-template-areas: 
        "toolbar toolbar"
        "editor info"
        "status status";
    height: 100vh;
    gap: 5px;
    padding: 5px;
}

.toolbar {
    grid-area: toolbar;
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 10px;
    background-color: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.tool-group, .action-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.editor-area {
    grid-area: editor;
    border: 2px solid #333;
    background-color: #ffffff;
    overflow: hidden;
    position: relative;
}

#eg-canvas {
    display: block;
    cursor: crosshair;
    background-color: #ffffff;
}

.info-panel {
    grid-area: info;
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    padding: 10px;
    overflow-y: auto;
}

.info-panel h3 {
    margin-bottom: 8px;
    font-size: 14px;
    color: #555;
    border-bottom: 1px solid #ddd;
    padding-bottom: 4px;
}

#instructions p {
    font-size: 12px;
    margin-bottom: 4px;
    color: #666;
}

.status-bar {
    grid-area: status;
    padding: 6px 10px;
    background-color: #f0f0f0;
    border: 1px solid #ddd;
    font-size: 12px;
    color: #555;
}

button, select {
    padding: 6px 12px;
    border: 1px solid #ccc;
    background-color: #fff;
    border-radius: 3px;
    cursor: pointer;
    font-family: inherit;
}

button:hover, select:hover {
    background-color: #f0f0f0;
}

#validation-issues {
    list-style: none;
    padding: 0;
}

#validation-issues li {
    padding: 2px 0;
    font-size: 12px;
    color: #d00;
}

.valid {
    color: #0a0;
}

.invalid {
    color: #d00;
}'''
        
        with open('static/correct_eg.css', 'w') as f:
            f.write(css_content)
    
    def _create_javascript(self):
        """Create JavaScript for correct EG interaction."""
        js_content = '''// Correct Existential Graph Editor

class CorrectEGEditor {
    constructor() {
        this.canvas = document.getElementById('eg-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentTool = 'select';
        this.graph = null;
        this.selectedElement = null;
        this.attachmentStart = null;
        this.isDragging = false;
        this.dragStart = null;
        
        this.setupEventListeners();
        this.loadGraph();
        this.startUpdateLoop();
    }
    
    setupEventListeners() {
        // Tool selection
        document.querySelectorAll('input[name="tool"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentTool = e.target.value;
                this.updateStatus(`${this.currentTool} mode selected`);
                this.attachmentStart = null; // Reset attachment
            });
        });
        
        // Canvas events
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Buttons
        document.getElementById('validate-btn').addEventListener('click', () => this.validateGraph());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearGraph());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
    }
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    handleClick(e) {
        const pos = this.getMousePos(e);
        
        if (this.currentTool === 'line') {
            this.addLineOfIdentity(pos.x, pos.y);
        } else if (this.currentTool === 'predicate') {
            this.addPredicate(pos.x, pos.y);
        } else if (this.currentTool === 'cut') {
            this.addCut(pos.x, pos.y);
        } else if (this.currentTool === 'attach') {
            this.handleAttachClick(pos.x, pos.y);
        }
    }
    
    handleMouseDown(e) {
        if (this.currentTool === 'select') {
            const pos = this.getMousePos(e);
            const predicate = this.findPredicateAt(pos.x, pos.y);
            
            if (predicate) {
                this.selectedElement = predicate;
                this.isDragging = true;
                this.dragStart = pos;
                this.updateStatus(`Dragging predicate "${predicate.name}"`);
            }
        }
    }
    
    handleMouseMove(e) {
        if (this.isDragging && this.selectedElement && this.currentTool === 'select') {
            const pos = this.getMousePos(e);
            this.movePredicate(this.selectedElement.id, pos.x, pos.y);
        }
    }
    
    handleMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.dragStart = null;
            this.updateStatus('Predicate moved - lines updated automatically');
        }
    }
    
    async addLineOfIdentity(x, y) {
        const name = prompt('Line of Identity name (entity):', 'x');
        if (!name) return;
        
        try {
            const response = await fetch('/api/add_line', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added line of identity "${name}" (this IS the entity)`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding line:', error);
        }
    }
    
    async addPredicate(x, y) {
        const name = prompt('Predicate name:', 'P');
        if (!name) return;
        
        const arity = parseInt(prompt('Arity (number of arguments):', '1') || '1');
        
        try {
            const response = await fetch('/api/add_predicate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    x: x,
                    y: y,
                    arity: arity
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus(`Added predicate "${name}" with hook attachment points`);
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding predicate:', error);
        }
    }
    
    handleAttachClick(x, y) {
        if (!this.attachmentStart) {
            // First click - select line
            const line = this.findLineAt(x, y);
            if (line) {
                this.attachmentStart = line.id;
                this.updateStatus(`Selected line "${line.name}" - click predicate to attach`);
            } else {
                this.updateStatus('Click on a line of identity first');
            }
        } else {
            // Second click - select predicate
            const predicate = this.findPredicateAt(x, y);
            if (predicate) {
                this.attachLineToPredicate(this.attachmentStart, predicate.id, x, y);
                this.attachmentStart = null;
            } else {
                this.updateStatus('Click on a predicate to attach the line');
            }
        }
    }
    
    async attachLineToPredicate(lineId, predicateId, x, y) {
        try {
            const response = await fetch('/api/attach', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    line_id: lineId,
                    predicate_id: predicateId,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Line attached to predicate hook');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error attaching line:', error);
        }
    }
    
    async movePredicate(predicateId, x, y) {
        try {
            const response = await fetch('/api/move_predicate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    predicate_id: predicateId,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
            } else {
                this.updateStatus('Cannot move predicate there (containment constraint)');
            }
        } catch (error) {
            console.error('Error moving predicate:', error);
        }
    }
    
    async addCut(x, y) {
        try {
            const response = await fetch('/api/add_cut', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    x: x,
                    y: y,
                    width: 200,
                    height: 150
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadGraph();
                this.updateStatus('Added cut (no overlapping allowed)');
            } else {
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Error adding cut:', error);
        }
    }
    
    findLineAt(x, y) {
        if (!this.graph || !this.graph.lines_of_identity) return null;
        
        for (const [id, line] of Object.entries(this.graph.lines_of_identity)) {
            // Check if click is near any point on the line
            for (const point of line.points) {
                const dx = x - point.x;
                const dy = y - point.y;
                if (Math.sqrt(dx*dx + dy*dy) <= 10) {
                    return {id, ...line};
                }
            }
        }
        return null;
    }
    
    findPredicateAt(x, y) {
        if (!this.graph || !this.graph.predicates) return null;
        
        for (const [id, predicate] of Object.entries(this.graph.predicates)) {
            const bounds = this.getPredicateBounds(predicate);
            if (x >= bounds.x && x <= bounds.x + bounds.width &&
                y >= bounds.y && y <= bounds.y + bounds.height) {
                return {id, ...predicate};
            }
        }
        return null;
    }
    
    getPredicateBounds(predicate) {
        const width = predicate.size ? predicate.size[0] : 100;
        const height = predicate.size ? predicate.size[1] : 50;
        return {
            x: predicate.position.x - width/2,
            y: predicate.position.y - height/2,
            width: width,
            height: height
        };
    }
    
    async loadGraph() {
        try {
            const response = await fetch('/api/graph');
            this.graph = await response.json();
            this.render();
            this.updateInfo();
        } catch (error) {
            console.error('Error loading graph:', error);
        }
    }
    
    render() {
        if (!this.graph) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render cuts
        this.renderCuts();
        
        // Render predicates (with invisible boundaries)
        this.renderPredicates();
        
        // Render lines of identity (these ARE the entities)
        this.renderLinesOfIdentity();
        
        // Render hooks (for debugging)
        this.renderHooks();
    }
    
    renderCuts() {
        if (!this.graph.cuts) return;
        
        // Sort by nesting level to render outer cuts first
        const cuts = Object.entries(this.graph.cuts)
            .filter(([id, cut]) => id !== 'sheet')
            .sort(([,a], [,b]) => a.nesting_level - b.nesting_level);
        
        cuts.forEach(([id, cut]) => {
            this.ctx.save();
            this.ctx.strokeStyle = '#333';
            this.ctx.lineWidth = 2;
            this.ctx.fillStyle = 'rgba(240, 240, 240, 0.1)';
            
            // Draw oval
            this.ctx.beginPath();
            this.ctx.ellipse(
                cut.bounds.x + cut.bounds.width/2,
                cut.bounds.y + cut.bounds.height/2,
                cut.bounds.width/2,
                cut.bounds.height/2,
                0, 0, 2 * Math.PI
            );
            this.ctx.fill();
            this.ctx.stroke();
            
            // Label
            this.ctx.fillStyle = '#666';
            this.ctx.font = '12px Times New Roman';
            this.ctx.fillText(cut.name, cut.bounds.x + 5, cut.bounds.y + 15);
            
            this.ctx.restore();
        });
    }
    
    renderPredicates() {
        if (!this.graph.predicates) return;
        
        Object.values(this.graph.predicates).forEach(predicate => {
            this.ctx.save();
            
            // Draw invisible boundary (for debugging - light gray)
            const bounds = this.getPredicateBounds(predicate);
            this.ctx.strokeStyle = '#ddd';
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([2, 2]);
            
            this.ctx.beginPath();
            this.ctx.ellipse(
                predicate.position.x,
                predicate.position.y,
                bounds.width/2,
                bounds.height/2,
                0, 0, 2 * Math.PI
            );
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            
            // Draw predicate text
            this.ctx.fillStyle = '#000';
            this.ctx.font = '16px Times New Roman';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(predicate.name, predicate.position.x, predicate.position.y + 5);
            
            this.ctx.restore();
        });
    }
    
    renderLinesOfIdentity() {
        if (!this.graph.lines_of_identity) return;
        
        Object.values(this.graph.lines_of_identity).forEach(line => {
            if (line.points && line.points.length > 0) {
                this.ctx.save();
                this.ctx.strokeStyle = '#000';
                this.ctx.lineWidth = 3;
                
                // Draw the line path
                this.ctx.beginPath();
                this.ctx.moveTo(line.points[0].x, line.points[0].y);
                
                for (let i = 1; i < line.points.length; i++) {
                    this.ctx.lineTo(line.points[i].x, line.points[i].y);
                }
                
                this.ctx.stroke();
                
                // Label the line
                if (line.points.length > 0) {
                    const firstPoint = line.points[0];
                    this.ctx.fillStyle = '#000';
                    this.ctx.font = '14px Times New Roman';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(line.name, firstPoint.x, firstPoint.y - 10);
                }
                
                this.ctx.restore();
            }
        });
    }
    
    renderHooks() {
        if (!this.graph.predicates) return;
        
        // Render hook points for debugging
        Object.values(this.graph.predicates).forEach(predicate => {
            if (predicate.hooks) {
                predicate.hooks.forEach(hook => {
                    if (hook.position) {
                        this.ctx.save();
                        this.ctx.fillStyle = '#f00';
                        this.ctx.beginPath();
                        this.ctx.arc(hook.position.x, hook.position.y, 3, 0, 2 * Math.PI);
                        this.ctx.fill();
                        this.ctx.restore();
                    }
                });
            }
        });
    }
    
    updateInfo() {
        if (!this.graph) return;
        
        document.getElementById('line-count').textContent = 
            Object.keys(this.graph.lines_of_identity || {}).length;
        document.getElementById('predicate-count').textContent = 
            Object.keys(this.graph.predicates || {}).length;
        document.getElementById('cut-count').textContent = 
            Object.keys(this.graph.cuts || {}).length - 1; // Exclude sheet
        
        // Count total attachments
        let attachmentCount = 0;
        if (this.graph.lines_of_identity) {
            Object.values(this.graph.lines_of_identity).forEach(line => {
                if (line.attached_hooks) {
                    attachmentCount += line.attached_hooks.length;
                }
            });
        }
        document.getElementById('attachment-count').textContent = attachmentCount;
    }
    
    async validateGraph() {
        try {
            const response = await fetch('/api/validate');
            const validation = await response.json();
            
            const statusEl = document.getElementById('validation-status');
            const issuesEl = document.getElementById('validation-issues');
            
            statusEl.textContent = validation.is_valid ? 'Valid' : 'Invalid';
            statusEl.className = validation.is_valid ? 'valid' : 'invalid';
            
            issuesEl.innerHTML = '';
            validation.issues.forEach(issue => {
                const li = document.createElement('li');
                li.textContent = issue;
                issuesEl.appendChild(li);
            });
            
            this.updateStatus(`Validation: ${validation.is_valid ? 'Valid' : 'Invalid'}`);
        } catch (error) {
            console.error('Error validating graph:', error);
        }
    }
    
    clearGraph() {
        if (confirm('Clear the entire graph?')) {
            // Implement clear functionality
            this.updateStatus('Graph cleared');
        }
    }
    
    showHelp() {
        alert(`Correct Existential Graph Editor

Key Concepts:
• Line of Identity = Entity (not a connection!)
• Predicates have invisible oval boundaries with hooks
• Lines attach to hooks on predicate boundaries
• Movement is constrained by logical containment

Tools:
• Line of Identity: Create entity lines (these ARE the entities)
• Predicate: Create predicates with hook attachment points
• Attach: Connect lines to predicate hooks
• Select: Drag predicates (lines move automatically)
• Cut: Create nested contexts (no overlapping allowed)

Correct Semantics:
• Lines of identity represent entities in the domain
• Predicates are relations with attachment hooks
• Movement preserves logical relationships
• Visual layout constrained by logical structure`);
    }
    
    updateStatus(message) {
        document.getElementById('status-text').textContent = message;
    }
    
    startUpdateLoop() {
        setInterval(() => {
            this.render();
        }, 100); // 10 FPS for smooth updates
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.egEditor = new CorrectEGEditor();
    console.log('Correct EG Editor initialized');
    console.log('Lines of identity ARE the entities!');
});'''
        
        with open('static/correct_eg.js', 'w') as f:
            f.write(js_content)


if __name__ == "__main__":
    print("Correct Existential Graph GUI - Starting...")
    print("=" * 60)
    print("CORRECTED EG Semantics:")
    print("• Lines of Identity ARE the entities (not connections)")
    print("• Predicates have hook attachment points on boundaries")
    print("• Lines attach to hooks, not to other lines")
    print("• Movement constrained by logical containment")
    print("• Visual adjustments enabled/constrained by logic")
    print("=" * 60)
    
    try:
        gui = CorrectEGGUI()
        gui.run(debug=True, port=5002)
    except Exception as e:
        print(f"Error starting correct EG GUI: {e}")
        import traceback
        traceback.print_exc()

